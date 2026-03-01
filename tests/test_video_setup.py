#!/usr/bin/env python3
"""
Tests for Video Setup (cli/video_setup.py) and video_visual.py resilience.

Tests cover:
- GPU detection (NVIDIA, AMD ROCm, AMD without ROCm, CPU fallback)
- CUDA / ROCm version → index URL mapping
- PyTorch installation (mocked subprocess)
- Visual deps installation (mocked subprocess)
- Installation verification
- run_setup orchestrator
- Venv detection and creation
- System dep checks (tesseract binary)
- ROCm env var configuration
- Module selection (SetupModules)
- Tesseract circuit breaker (video_visual.py)
- --setup flag in VIDEO_ARGUMENTS and early-exit in video_scraper
"""

import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skill_seekers.cli.video_setup import (
    _BASE_VIDEO_DEPS,
    GPUInfo,
    GPUVendor,
    SetupModules,
    _build_visual_deps,
    _cuda_version_to_index_url,
    _detect_distro,
    _PYTORCH_BASE,
    _rocm_version_to_index_url,
    check_tesseract,
    configure_rocm_env,
    create_venv,
    detect_gpu,
    get_venv_activate_cmd,
    get_venv_python,
    install_torch,
    install_visual_deps,
    is_in_venv,
    run_setup,
    verify_installation,
)


# =============================================================================
# GPU Detection Tests
# =============================================================================


class TestGPUDetection(unittest.TestCase):
    """Tests for detect_gpu() and its helpers."""

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_nvidia_detected(self, mock_run, mock_which):
        """nvidia-smi present → GPUVendor.NVIDIA."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nvidia-smi" if cmd == "nvidia-smi" else None
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "+-------------------------+\n"
                "| NVIDIA GeForce RTX 4090  On |\n"
                "| CUDA Version: 12.4      |\n"
                "+-------------------------+\n"
            ),
        )
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.NVIDIA
        assert "12.4" in gpu.compute_version
        assert "cu124" in gpu.index_url

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    @patch("skill_seekers.cli.video_setup._read_rocm_version", return_value="6.3.1")
    def test_amd_rocm_detected(self, mock_rocm_ver, mock_run, mock_which):
        """rocminfo present → GPUVendor.AMD."""

        def which_side(cmd):
            if cmd == "nvidia-smi":
                return None
            if cmd == "rocminfo":
                return "/usr/bin/rocminfo"
            return None

        mock_which.side_effect = which_side
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Marketing Name: AMD Radeon RX 7900 XTX\n",
        )
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.AMD
        assert "rocm6.3" in gpu.index_url

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_amd_no_rocm_fallback(self, mock_run, mock_which):
        """AMD GPU in lspci but no ROCm → AMD vendor, CPU index URL."""

        def which_side(cmd):
            if cmd == "lspci":
                return "/usr/bin/lspci"
            return None

        mock_which.side_effect = which_side

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="06:00.0 VGA compatible controller: AMD/ATI Navi 31 [Radeon RX 7900 XTX]\n",
        )
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.AMD
        assert "cpu" in gpu.index_url
        assert any("ROCm is not installed" in d for d in gpu.details)

    @patch("skill_seekers.cli.video_setup.shutil.which", return_value=None)
    def test_cpu_fallback(self, mock_which):
        """No GPU tools found → GPUVendor.NONE."""
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.NONE
        assert "cpu" in gpu.index_url

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_nvidia_smi_error(self, mock_run, mock_which):
        """nvidia-smi returns non-zero → skip to next check."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nvidia-smi" if cmd == "nvidia-smi" else None
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.NONE

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_nvidia_smi_timeout(self, mock_run, mock_which):
        """nvidia-smi times out → skip to next check."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nvidia-smi" if cmd == "nvidia-smi" else None
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=10)
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.NONE

    @patch("skill_seekers.cli.video_setup.shutil.which")
    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_rocminfo_error(self, mock_run, mock_which):
        """rocminfo returns non-zero → skip to next check."""

        def which_side(cmd):
            if cmd == "nvidia-smi":
                return None
            if cmd == "rocminfo":
                return "/usr/bin/rocminfo"
            return None

        mock_which.side_effect = which_side
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        gpu = detect_gpu()
        assert gpu.vendor == GPUVendor.NONE


# =============================================================================
# Version Mapping Tests
# =============================================================================


class TestVersionMapping(unittest.TestCase):
    """Tests for CUDA/ROCm version → index URL mapping."""

    def test_cuda_124(self):
        assert _cuda_version_to_index_url("12.4") == f"{_PYTORCH_BASE}/cu124"

    def test_cuda_126(self):
        assert _cuda_version_to_index_url("12.6") == f"{_PYTORCH_BASE}/cu124"

    def test_cuda_121(self):
        assert _cuda_version_to_index_url("12.1") == f"{_PYTORCH_BASE}/cu121"

    def test_cuda_118(self):
        assert _cuda_version_to_index_url("11.8") == f"{_PYTORCH_BASE}/cu118"

    def test_cuda_old_falls_to_cpu(self):
        assert _cuda_version_to_index_url("10.2") == f"{_PYTORCH_BASE}/cpu"

    def test_cuda_invalid_string(self):
        assert _cuda_version_to_index_url("garbage") == f"{_PYTORCH_BASE}/cpu"

    def test_rocm_63(self):
        assert _rocm_version_to_index_url("6.3.1") == f"{_PYTORCH_BASE}/rocm6.3"

    def test_rocm_60(self):
        assert _rocm_version_to_index_url("6.0") == f"{_PYTORCH_BASE}/rocm6.2.4"

    def test_rocm_old_falls_to_cpu(self):
        assert _rocm_version_to_index_url("5.4") == f"{_PYTORCH_BASE}/cpu"

    def test_rocm_invalid(self):
        assert _rocm_version_to_index_url("bad") == f"{_PYTORCH_BASE}/cpu"


# =============================================================================
# Venv Tests
# =============================================================================


class TestVenv(unittest.TestCase):
    """Tests for venv detection and creation."""

    def test_is_in_venv_returns_bool(self):
        result = is_in_venv()
        assert isinstance(result, bool)

    def test_is_in_venv_detects_prefix_mismatch(self):
        # If sys.prefix != sys.base_prefix, we're in a venv
        with patch.object(sys, "prefix", "/some/venv"), patch.object(sys, "base_prefix", "/usr"):
            assert is_in_venv() is True

    def test_is_in_venv_detects_no_venv(self):
        with patch.object(sys, "prefix", "/usr"), patch.object(sys, "base_prefix", "/usr"):
            assert is_in_venv() is False

    def test_create_venv_in_tempdir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = os.path.join(tmpdir, "test_venv")
            result = create_venv(venv_path)
            assert result is True
            assert os.path.isdir(venv_path)

    def test_create_venv_already_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create it once
            create_venv(tmpdir)
            # Creating again should succeed (already exists)
            assert create_venv(tmpdir) is True

    def test_get_venv_python_linux(self):
        with patch("skill_seekers.cli.video_setup.platform.system", return_value="Linux"):
            path = get_venv_python("/path/.venv")
            assert path.endswith("bin/python")

    def test_get_venv_activate_cmd_linux(self):
        with patch("skill_seekers.cli.video_setup.platform.system", return_value="Linux"):
            cmd = get_venv_activate_cmd("/path/.venv")
            assert "source" in cmd
            assert "bin/activate" in cmd


# =============================================================================
# System Dep Check Tests
# =============================================================================


class TestSystemDeps(unittest.TestCase):
    """Tests for system dependency checks."""

    @patch("skill_seekers.cli.video_setup.shutil.which", return_value=None)
    def test_tesseract_not_installed(self, mock_which):
        result = check_tesseract()
        assert result["installed"] is False
        assert result["has_eng"] is False
        assert isinstance(result["install_cmd"], str)

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    @patch("skill_seekers.cli.video_setup.shutil.which", return_value="/usr/bin/tesseract")
    def test_tesseract_installed_with_eng(self, mock_which, mock_run):
        mock_run.side_effect = [
            # --version call
            MagicMock(returncode=0, stdout="tesseract 5.3.0\n", stderr=""),
            # --list-langs call
            MagicMock(returncode=0, stdout="List of available languages:\neng\nosd\n", stderr=""),
        ]
        result = check_tesseract()
        assert result["installed"] is True
        assert result["has_eng"] is True

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    @patch("skill_seekers.cli.video_setup.shutil.which", return_value="/usr/bin/tesseract")
    def test_tesseract_installed_no_eng(self, mock_which, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="tesseract 5.3.0\n", stderr=""),
            MagicMock(returncode=0, stdout="List of available languages:\nosd\n", stderr=""),
        ]
        result = check_tesseract()
        assert result["installed"] is True
        assert result["has_eng"] is False

    def test_detect_distro_returns_string(self):
        result = _detect_distro()
        assert isinstance(result, str)

    @patch("builtins.open", side_effect=OSError)
    def test_detect_distro_no_os_release(self, mock_open):
        assert _detect_distro() == "unknown"


# =============================================================================
# ROCm Configuration Tests
# =============================================================================


class TestROCmConfig(unittest.TestCase):
    """Tests for configure_rocm_env()."""

    def test_sets_miopen_find_mode(self):
        env_backup = os.environ.get("MIOPEN_FIND_MODE")
        try:
            os.environ.pop("MIOPEN_FIND_MODE", None)
            changes = configure_rocm_env()
            assert "MIOPEN_FIND_MODE=FAST" in changes
            assert os.environ["MIOPEN_FIND_MODE"] == "FAST"
        finally:
            if env_backup is not None:
                os.environ["MIOPEN_FIND_MODE"] = env_backup

    def test_does_not_override_existing(self):
        env_backup = os.environ.get("MIOPEN_FIND_MODE")
        try:
            os.environ["MIOPEN_FIND_MODE"] = "NORMAL"
            changes = configure_rocm_env()
            miopen_changes = [c for c in changes if "MIOPEN_FIND_MODE" in c]
            assert len(miopen_changes) == 0
            assert os.environ["MIOPEN_FIND_MODE"] == "NORMAL"
        finally:
            if env_backup is not None:
                os.environ["MIOPEN_FIND_MODE"] = env_backup
            else:
                os.environ.pop("MIOPEN_FIND_MODE", None)

    def test_sets_miopen_user_db_path(self):
        env_backup = os.environ.get("MIOPEN_USER_DB_PATH")
        try:
            os.environ.pop("MIOPEN_USER_DB_PATH", None)
            changes = configure_rocm_env()
            db_changes = [c for c in changes if "MIOPEN_USER_DB_PATH" in c]
            assert len(db_changes) == 1
        finally:
            if env_backup is not None:
                os.environ["MIOPEN_USER_DB_PATH"] = env_backup


# =============================================================================
# Module Selection Tests
# =============================================================================


class TestModuleSelection(unittest.TestCase):
    """Tests for SetupModules and _build_visual_deps."""

    def test_default_modules_all_true(self):
        m = SetupModules()
        assert m.torch is True
        assert m.easyocr is True
        assert m.opencv is True
        assert m.tesseract is True
        assert m.scenedetect is True
        assert m.whisper is True

    def test_build_all_deps(self):
        deps = _build_visual_deps(SetupModules())
        assert "yt-dlp" in deps
        assert "youtube-transcript-api" in deps
        assert "easyocr" in deps
        assert "opencv-python-headless" in deps
        assert "pytesseract" in deps
        assert "scenedetect[opencv]" in deps
        assert "faster-whisper" in deps

    def test_build_no_optional_deps(self):
        """Even with all optional modules off, base video deps are included."""
        m = SetupModules(
            torch=False,
            easyocr=False,
            opencv=False,
            tesseract=False,
            scenedetect=False,
            whisper=False,
        )
        deps = _build_visual_deps(m)
        assert deps == list(_BASE_VIDEO_DEPS)

    def test_build_partial_deps(self):
        m = SetupModules(
            easyocr=True, opencv=True, tesseract=False, scenedetect=False, whisper=False
        )
        deps = _build_visual_deps(m)
        assert "yt-dlp" in deps
        assert "youtube-transcript-api" in deps
        assert "easyocr" in deps
        assert "opencv-python-headless" in deps
        assert "pytesseract" not in deps
        assert "faster-whisper" not in deps


# =============================================================================
# Installation Tests
# =============================================================================


class TestInstallation(unittest.TestCase):
    """Tests for install_torch() and install_visual_deps()."""

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_torch_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        gpu = GPUInfo(vendor=GPUVendor.NVIDIA, index_url=f"{_PYTORCH_BASE}/cu124")
        assert install_torch(gpu) is True
        call_args = mock_run.call_args[0][0]
        assert "torch" in call_args
        assert "--index-url" in call_args
        assert f"{_PYTORCH_BASE}/cu124" in call_args

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_torch_cpu(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        gpu = GPUInfo(vendor=GPUVendor.NONE, index_url=f"{_PYTORCH_BASE}/cpu")
        assert install_torch(gpu) is True
        call_args = mock_run.call_args[0][0]
        assert f"{_PYTORCH_BASE}/cpu" in call_args

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_torch_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
        gpu = GPUInfo(vendor=GPUVendor.NVIDIA, index_url=f"{_PYTORCH_BASE}/cu124")
        assert install_torch(gpu) is False

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_torch_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip", timeout=600)
        gpu = GPUInfo(vendor=GPUVendor.NVIDIA, index_url=f"{_PYTORCH_BASE}/cu124")
        assert install_torch(gpu) is False

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_torch_custom_python(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        gpu = GPUInfo(vendor=GPUVendor.NONE, index_url=f"{_PYTORCH_BASE}/cpu")
        install_torch(gpu, python_exe="/custom/python")
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/custom/python"

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_visual_deps_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert install_visual_deps() is True
        call_args = mock_run.call_args[0][0]
        assert "easyocr" in call_args

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_visual_deps_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        assert install_visual_deps() is False

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_visual_deps_partial_modules(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        modules = SetupModules(
            easyocr=True, opencv=False, tesseract=False, scenedetect=False, whisper=False
        )
        install_visual_deps(modules)
        call_args = mock_run.call_args[0][0]
        assert "easyocr" in call_args
        assert "opencv-python-headless" not in call_args

    @patch("skill_seekers.cli.video_setup.subprocess.run")
    def test_install_visual_deps_base_only(self, mock_run):
        """Even with all optional modules off, base video deps get installed."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        modules = SetupModules(
            easyocr=False, opencv=False, tesseract=False, scenedetect=False, whisper=False
        )
        result = install_visual_deps(modules)
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "yt-dlp" in call_args
        assert "youtube-transcript-api" in call_args
        assert "easyocr" not in call_args


# =============================================================================
# Verification Tests
# =============================================================================


class TestVerification(unittest.TestCase):
    """Tests for verify_installation()."""

    @patch.dict("sys.modules", {"torch": None, "easyocr": None, "cv2": None})
    def test_returns_dict(self):
        results = verify_installation()
        assert isinstance(results, dict)

    def test_expected_keys(self):
        results = verify_installation()
        for key in (
            "yt-dlp",
            "youtube-transcript-api",
            "torch",
            "torch.cuda",
            "torch.rocm",
            "easyocr",
            "opencv",
        ):
            assert key in results, f"Missing key: {key}"


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestRunSetup(unittest.TestCase):
    """Tests for run_setup() orchestrator."""

    @patch("skill_seekers.cli.video_setup.verify_installation")
    @patch("skill_seekers.cli.video_setup.install_visual_deps", return_value=True)
    @patch("skill_seekers.cli.video_setup.install_torch", return_value=True)
    @patch("skill_seekers.cli.video_setup.check_tesseract")
    @patch("skill_seekers.cli.video_setup.detect_gpu")
    def test_non_interactive_success(
        self, mock_detect, mock_tess, mock_torch, mock_deps, mock_verify
    ):
        mock_detect.return_value = GPUInfo(
            vendor=GPUVendor.NONE,
            name="CPU-only",
            index_url=f"{_PYTORCH_BASE}/cpu",
        )
        mock_tess.return_value = {
            "installed": True,
            "has_eng": True,
            "install_cmd": "",
            "version": "5.3.0",
        }
        mock_verify.return_value = {
            "torch": True,
            "torch.cuda": False,
            "torch.rocm": False,
            "easyocr": True,
            "opencv": True,
            "pytesseract": True,
            "scenedetect": True,
            "faster-whisper": True,
        }
        rc = run_setup(interactive=False)
        assert rc == 0
        mock_torch.assert_called_once()
        mock_deps.assert_called_once()

    @patch("skill_seekers.cli.video_setup.install_torch", return_value=False)
    @patch("skill_seekers.cli.video_setup.check_tesseract")
    @patch("skill_seekers.cli.video_setup.detect_gpu")
    def test_failure_returns_nonzero(self, mock_detect, mock_tess, mock_torch):
        mock_detect.return_value = GPUInfo(
            vendor=GPUVendor.NONE,
            name="CPU-only",
            index_url=f"{_PYTORCH_BASE}/cpu",
        )
        mock_tess.return_value = {
            "installed": True,
            "has_eng": True,
            "install_cmd": "",
            "version": "5.3.0",
        }
        rc = run_setup(interactive=False)
        assert rc == 1

    @patch("skill_seekers.cli.video_setup.install_torch", return_value=True)
    @patch("skill_seekers.cli.video_setup.install_visual_deps", return_value=False)
    @patch("skill_seekers.cli.video_setup.check_tesseract")
    @patch("skill_seekers.cli.video_setup.detect_gpu")
    def test_visual_deps_failure(self, mock_detect, mock_tess, mock_deps, mock_torch):
        mock_detect.return_value = GPUInfo(
            vendor=GPUVendor.NONE,
            name="CPU-only",
            index_url=f"{_PYTORCH_BASE}/cpu",
        )
        mock_tess.return_value = {
            "installed": True,
            "has_eng": True,
            "install_cmd": "",
            "version": "5.3.0",
        }
        rc = run_setup(interactive=False)
        assert rc == 1

    @patch("skill_seekers.cli.video_setup.verify_installation")
    @patch("skill_seekers.cli.video_setup.install_visual_deps", return_value=True)
    @patch("skill_seekers.cli.video_setup.install_torch", return_value=True)
    @patch("skill_seekers.cli.video_setup.check_tesseract")
    @patch("skill_seekers.cli.video_setup.detect_gpu")
    def test_rocm_configures_env(self, mock_detect, mock_tess, mock_torch, mock_deps, mock_verify):
        """AMD GPU → configure_rocm_env called and env vars set."""
        mock_detect.return_value = GPUInfo(
            vendor=GPUVendor.AMD,
            name="RX 7900",
            index_url=f"{_PYTORCH_BASE}/rocm6.3",
        )
        mock_tess.return_value = {
            "installed": True,
            "has_eng": True,
            "install_cmd": "",
            "version": "5.3.0",
        }
        mock_verify.return_value = {
            "torch": True,
            "torch.cuda": False,
            "torch.rocm": True,
            "easyocr": True,
            "opencv": True,
            "pytesseract": True,
            "scenedetect": True,
            "faster-whisper": True,
        }
        rc = run_setup(interactive=False)
        assert rc == 0
        assert os.environ.get("MIOPEN_FIND_MODE") is not None


# =============================================================================
# Tesseract Circuit Breaker Tests (video_visual.py)
# =============================================================================


class TestTesseractCircuitBreaker(unittest.TestCase):
    """Tests for _tesseract_broken flag in video_visual.py."""

    def test_circuit_breaker_flag_exists(self):
        import skill_seekers.cli.video_visual as vv

        assert hasattr(vv, "_tesseract_broken")

    def test_circuit_breaker_skips_after_failure(self):
        import skill_seekers.cli.video_visual as vv
        from skill_seekers.cli.video_models import FrameType

        # Save and set broken state
        original = vv._tesseract_broken
        try:
            vv._tesseract_broken = True
            result = vv._run_tesseract_ocr("/nonexistent/path.png", FrameType.CODE_EDITOR)
            assert result == []
        finally:
            vv._tesseract_broken = original

    def test_circuit_breaker_allows_when_not_broken(self):
        import skill_seekers.cli.video_visual as vv
        from skill_seekers.cli.video_models import FrameType

        original = vv._tesseract_broken
        try:
            vv._tesseract_broken = False
            if not vv.HAS_PYTESSERACT:
                # pytesseract not installed → returns [] immediately
                result = vv._run_tesseract_ocr("/nonexistent/path.png", FrameType.CODE_EDITOR)
                assert result == []
            # If pytesseract IS installed, it would try to run and potentially fail
            # on our fake path — that's fine, the circuit breaker would trigger
        finally:
            vv._tesseract_broken = original


# =============================================================================
# MIOPEN Env Var Tests (video_visual.py)
# =============================================================================


class TestMIOPENEnvVars(unittest.TestCase):
    """Tests that video_visual.py sets MIOPEN env vars at import time."""

    def test_miopen_find_mode_set(self):
        # video_visual.py sets this at module level before torch import
        assert "MIOPEN_FIND_MODE" in os.environ

    def test_miopen_user_db_path_set(self):
        assert "MIOPEN_USER_DB_PATH" in os.environ


# =============================================================================
# Argument & Early-Exit Tests
# =============================================================================


class TestVideoArgumentSetup(unittest.TestCase):
    """Tests for --setup flag in VIDEO_ARGUMENTS."""

    def test_setup_in_video_arguments(self):
        from skill_seekers.cli.arguments.video import VIDEO_ARGUMENTS

        assert "setup" in VIDEO_ARGUMENTS
        assert VIDEO_ARGUMENTS["setup"]["kwargs"]["action"] == "store_true"

    def test_parser_accepts_setup(self):
        import argparse

        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)
        args = parser.parse_args(["--setup"])
        assert args.setup is True

    def test_parser_default_false(self):
        import argparse

        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)
        args = parser.parse_args(["--url", "https://example.com"])
        assert args.setup is False


class TestVideoScraperSetupEarlyExit(unittest.TestCase):
    """Test that --setup exits before source validation."""

    @patch("skill_seekers.cli.video_setup.run_setup", return_value=0)
    def test_setup_skips_source_validation(self, mock_setup):
        """--setup without --url should NOT error about missing source."""
        from skill_seekers.cli.video_scraper import main

        old_argv = sys.argv
        try:
            sys.argv = ["video_scraper", "--setup"]
            rc = main()
            assert rc == 0
            mock_setup.assert_called_once_with(interactive=True)
        finally:
            sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
