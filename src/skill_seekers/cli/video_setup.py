"""GPU auto-detection and video dependency installation.

Detects NVIDIA (CUDA) or AMD (ROCm) GPUs using system tools (without
requiring torch to be installed) and installs the correct PyTorch variant
plus all visual extraction dependencies (easyocr, opencv, etc.).

Also handles:
- Virtual environment creation (if not already in one)
- System dependency checks (tesseract binary)
- ROCm environment variable configuration (MIOPEN_FIND_MODE)

Usage:
    skill-seekers video --setup          # Interactive (all modules)
    skill-seekers video --setup          # Interactive, choose modules
    From MCP: run_setup(interactive=False)
"""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================


class GPUVendor(Enum):
    """Detected GPU hardware vendor."""

    NVIDIA = "nvidia"
    AMD = "amd"
    NONE = "none"


@dataclass
class GPUInfo:
    """Result of GPU auto-detection."""

    vendor: GPUVendor
    name: str = ""
    compute_version: str = ""
    index_url: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class SetupModules:
    """Which modules to install during setup."""

    torch: bool = True
    easyocr: bool = True
    opencv: bool = True
    tesseract: bool = True
    scenedetect: bool = True
    whisper: bool = True


# =============================================================================
# PyTorch Index URL Mapping
# =============================================================================

_PYTORCH_BASE = "https://download.pytorch.org/whl"


def _cuda_version_to_index_url(version: str) -> str:
    """Map a CUDA version string to the correct PyTorch index URL."""
    try:
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        ver = major + minor / 10.0
    except (ValueError, IndexError):
        return f"{_PYTORCH_BASE}/cpu"

    if ver >= 12.4:
        return f"{_PYTORCH_BASE}/cu124"
    if ver >= 12.1:
        return f"{_PYTORCH_BASE}/cu121"
    if ver >= 11.8:
        return f"{_PYTORCH_BASE}/cu118"
    return f"{_PYTORCH_BASE}/cpu"


def _rocm_version_to_index_url(version: str) -> str:
    """Map a ROCm version string to the correct PyTorch index URL."""
    try:
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        ver = major + minor / 10.0
    except (ValueError, IndexError):
        return f"{_PYTORCH_BASE}/cpu"

    if ver >= 6.3:
        return f"{_PYTORCH_BASE}/rocm6.3"
    if ver >= 6.0:
        return f"{_PYTORCH_BASE}/rocm6.2.4"
    return f"{_PYTORCH_BASE}/cpu"


# =============================================================================
# GPU Detection (without torch)
# =============================================================================


def detect_gpu() -> GPUInfo:
    """Detect GPU vendor and compute version using system tools.

    Detection order:
    1. nvidia-smi  -> NVIDIA + CUDA version
    2. rocminfo    -> AMD + ROCm version
    3. lspci       -> AMD GPU present but no ROCm (warn)
    4. Fallback    -> CPU-only
    """
    # 1. Check NVIDIA
    nvidia = _check_nvidia()
    if nvidia is not None:
        return nvidia

    # 2. Check AMD ROCm
    amd = _check_amd_rocm()
    if amd is not None:
        return amd

    # 3. Check if AMD GPU exists but ROCm isn't installed
    amd_no_rocm = _check_amd_lspci()
    if amd_no_rocm is not None:
        return amd_no_rocm

    # 4. CPU fallback
    return GPUInfo(
        vendor=GPUVendor.NONE,
        name="CPU-only",
        index_url=f"{_PYTORCH_BASE}/cpu",
        details=["No GPU detected, will use CPU-only PyTorch"],
    )


def _check_nvidia() -> GPUInfo | None:
    """Detect NVIDIA GPU via nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        output = result.stdout
        # Parse CUDA version from "CUDA Version: X.Y"
        cuda_match = re.search(r"CUDA Version:\s*(\d+\.\d+)", output)
        cuda_ver = cuda_match.group(1) if cuda_match else ""

        # Parse GPU name from the table row (e.g., "NVIDIA GeForce RTX 4090")
        gpu_name = ""
        name_match = re.search(r"\|\s+(NVIDIA[^\|]+?)\s+(?:On|Off)\s+\|", output)
        if name_match:
            gpu_name = name_match.group(1).strip()

        index_url = _cuda_version_to_index_url(cuda_ver) if cuda_ver else f"{_PYTORCH_BASE}/cpu"

        return GPUInfo(
            vendor=GPUVendor.NVIDIA,
            name=gpu_name or "NVIDIA GPU",
            compute_version=cuda_ver,
            index_url=index_url,
            details=[f"CUDA {cuda_ver}" if cuda_ver else "CUDA version unknown"],
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def _check_amd_rocm() -> GPUInfo | None:
    """Detect AMD GPU via rocminfo."""
    if not shutil.which("rocminfo"):
        return None
    try:
        result = subprocess.run(
            ["rocminfo"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        output = result.stdout
        # Parse GPU name from "Name: gfx..." or "Marketing Name: ..."
        gpu_name = ""
        marketing_match = re.search(r"Marketing Name:\s*(.+)", output)
        if marketing_match:
            gpu_name = marketing_match.group(1).strip()

        # Get ROCm version from /opt/rocm/.info/version
        rocm_ver = _read_rocm_version()

        index_url = _rocm_version_to_index_url(rocm_ver) if rocm_ver else f"{_PYTORCH_BASE}/cpu"

        return GPUInfo(
            vendor=GPUVendor.AMD,
            name=gpu_name or "AMD GPU",
            compute_version=rocm_ver,
            index_url=index_url,
            details=[f"ROCm {rocm_ver}" if rocm_ver else "ROCm version unknown"],
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def _read_rocm_version() -> str:
    """Read ROCm version from /opt/rocm/.info/version."""
    try:
        with open("/opt/rocm/.info/version") as f:
            return f.read().strip().split("-")[0]
    except OSError:
        return ""


def _check_amd_lspci() -> GPUInfo | None:
    """Detect AMD GPU via lspci when ROCm isn't installed."""
    if not shutil.which("lspci"):
        return None
    try:
        result = subprocess.run(
            ["lspci"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        # Look for AMD/ATI VGA or Display controllers
        for line in result.stdout.splitlines():
            if ("VGA" in line or "Display" in line) and ("AMD" in line or "ATI" in line):
                return GPUInfo(
                    vendor=GPUVendor.AMD,
                    name=line.split(":")[-1].strip() if ":" in line else "AMD GPU",
                    compute_version="",
                    index_url=f"{_PYTORCH_BASE}/cpu",
                    details=[
                        "AMD GPU detected but ROCm is not installed",
                        "Install ROCm first for GPU acceleration: https://rocm.docs.amd.com/",
                        "Falling back to CPU-only PyTorch",
                    ],
                )
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


# =============================================================================
# Virtual Environment
# =============================================================================


def is_in_venv() -> bool:
    """Check if the current Python process is running inside a venv."""
    return sys.prefix != sys.base_prefix


def create_venv(venv_path: str = ".venv") -> bool:
    """Create a virtual environment and return True on success."""
    path = Path(venv_path).resolve()
    if path.exists():
        logger.info(f"Venv already exists at {path}")
        return True
    try:
        venv.create(str(path), with_pip=True)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to create venv: {exc}")
        return False


def get_venv_python(venv_path: str = ".venv") -> str:
    """Return the python executable path inside a venv."""
    path = Path(venv_path).resolve()
    if platform.system() == "Windows":
        return str(path / "Scripts" / "python.exe")
    return str(path / "bin" / "python")


def get_venv_activate_cmd(venv_path: str = ".venv") -> str:
    """Return the shell command to activate the venv."""
    path = Path(venv_path).resolve()
    if platform.system() == "Windows":
        return str(path / "Scripts" / "activate")
    return f"source {path}/bin/activate"


# =============================================================================
# System Dependency Checks
# =============================================================================


def _detect_distro() -> str:
    """Detect Linux distro family for install command suggestions."""
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        if "arch" in content or "manjaro" in content or "endeavour" in content:
            return "arch"
        if "debian" in content or "ubuntu" in content or "mint" in content or "pop" in content:
            return "debian"
        if "fedora" in content or "rhel" in content or "centos" in content or "rocky" in content:
            return "fedora"
        if "opensuse" in content or "suse" in content:
            return "suse"
    except OSError:
        pass
    return "unknown"


def _get_tesseract_install_cmd() -> str:
    """Return distro-specific command to install tesseract."""
    distro = _detect_distro()
    cmds = {
        "arch": "sudo pacman -S tesseract tesseract-data-eng",
        "debian": "sudo apt install tesseract-ocr tesseract-ocr-eng",
        "fedora": "sudo dnf install tesseract tesseract-langpack-eng",
        "suse": "sudo zypper install tesseract-ocr tesseract-ocr-traineddata-english",
    }
    return cmds.get(distro, "Install tesseract-ocr with your package manager")


def check_tesseract() -> dict[str, bool | str]:
    """Check if tesseract binary is installed and has English data.

    Returns dict with keys: installed, has_eng, install_cmd, version.
    """
    result: dict[str, bool | str] = {
        "installed": False,
        "has_eng": False,
        "install_cmd": _get_tesseract_install_cmd(),
        "version": "",
    }

    tess_bin = shutil.which("tesseract")
    if not tess_bin:
        return result

    result["installed"] = True

    # Get version
    try:
        ver = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        first_line = (ver.stdout or ver.stderr).split("\n")[0]
        result["version"] = first_line.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Check for eng language data
    try:
        langs = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = langs.stdout + langs.stderr
        result["has_eng"] = "eng" in output.split()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return result


# =============================================================================
# ROCm Environment Configuration
# =============================================================================


def configure_rocm_env() -> list[str]:
    """Set environment variables for ROCm/MIOpen to work correctly.

    Returns list of env vars that were set.
    """
    changes: list[str] = []

    # MIOPEN_FIND_MODE=FAST avoids the workspace allocation issue
    # where MIOpen requires huge workspace but allocates 0 bytes
    if "MIOPEN_FIND_MODE" not in os.environ:
        os.environ["MIOPEN_FIND_MODE"] = "FAST"
        changes.append("MIOPEN_FIND_MODE=FAST")

    # Ensure MIOpen user DB has a writable location
    if "MIOPEN_USER_DB_PATH" not in os.environ:
        db_path = os.path.expanduser("~/.config/miopen")
        os.makedirs(db_path, exist_ok=True)
        os.environ["MIOPEN_USER_DB_PATH"] = db_path
        changes.append(f"MIOPEN_USER_DB_PATH={db_path}")

    return changes


# =============================================================================
# Installation
# =============================================================================


_BASE_VIDEO_DEPS = ["yt-dlp", "youtube-transcript-api"]


def _build_visual_deps(modules: SetupModules) -> list[str]:
    """Build the list of pip packages based on selected modules."""
    # Base video deps are always included — setup must leave video fully ready
    deps: list[str] = list(_BASE_VIDEO_DEPS)
    if modules.easyocr:
        deps.append("easyocr")
    if modules.opencv:
        deps.append("opencv-python-headless")
    if modules.tesseract:
        deps.append("pytesseract")
    if modules.scenedetect:
        deps.append("scenedetect[opencv]")
    if modules.whisper:
        deps.append("faster-whisper")
    return deps


def install_torch(gpu_info: GPUInfo, python_exe: str | None = None) -> bool:
    """Install PyTorch with the correct GPU variant.

    Returns True on success, False on failure.
    """
    exe = python_exe or sys.executable
    cmd = [exe, "-m", "pip", "install", "torch", "torchvision", "--index-url", gpu_info.index_url]
    logger.info(f"Installing PyTorch from {gpu_info.index_url}")
    try:
        result = subprocess.run(cmd, timeout=600, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"PyTorch install failed:\n{result.stderr[-500:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("PyTorch installation timed out (10 min)")
        return False
    except OSError as exc:
        logger.error(f"PyTorch installation error: {exc}")
        return False


def install_visual_deps(modules: SetupModules | None = None, python_exe: str | None = None) -> bool:
    """Install visual extraction dependencies.

    Returns True on success, False on failure.
    """
    mods = modules or SetupModules()
    deps = _build_visual_deps(mods)
    if not deps:
        return True

    exe = python_exe or sys.executable
    cmd = [exe, "-m", "pip", "install"] + deps
    logger.info(f"Installing visual deps: {', '.join(deps)}")
    try:
        result = subprocess.run(cmd, timeout=600, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Visual deps install failed:\n{result.stderr[-500:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("Visual deps installation timed out (10 min)")
        return False
    except OSError as exc:
        logger.error(f"Visual deps installation error: {exc}")
        return False


def install_skill_seekers(python_exe: str) -> bool:
    """Install skill-seekers into the target python environment."""
    cmd = [python_exe, "-m", "pip", "install", "skill-seekers"]
    try:
        result = subprocess.run(cmd, timeout=300, capture_output=True, text=True)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


# =============================================================================
# Verification
# =============================================================================


def verify_installation() -> dict[str, bool]:
    """Verify that all video deps are importable.

    Returns a dict mapping package name to import success.
    """
    results: dict[str, bool] = {}

    # Base video deps
    try:
        import yt_dlp  # noqa: F401

        results["yt-dlp"] = True
    except ImportError:
        results["yt-dlp"] = False

    try:
        import youtube_transcript_api  # noqa: F401

        results["youtube-transcript-api"] = True
    except ImportError:
        results["youtube-transcript-api"] = False

    # torch
    try:
        import torch

        results["torch"] = True
        results["torch.cuda"] = torch.cuda.is_available()
        results["torch.rocm"] = hasattr(torch.version, "hip") and torch.version.hip is not None
    except ImportError:
        results["torch"] = False
        results["torch.cuda"] = False
        results["torch.rocm"] = False

    # easyocr
    try:
        import easyocr  # noqa: F401

        results["easyocr"] = True
    except ImportError:
        results["easyocr"] = False

    # opencv
    try:
        import cv2  # noqa: F401

        results["opencv"] = True
    except ImportError:
        results["opencv"] = False

    # pytesseract
    try:
        import pytesseract  # noqa: F401

        results["pytesseract"] = True
    except ImportError:
        results["pytesseract"] = False

    # scenedetect
    try:
        import scenedetect  # noqa: F401

        results["scenedetect"] = True
    except ImportError:
        results["scenedetect"] = False

    # faster-whisper
    try:
        import faster_whisper  # noqa: F401

        results["faster-whisper"] = True
    except ImportError:
        results["faster-whisper"] = False

    return results


# =============================================================================
# Module Selection (Interactive)
# =============================================================================


def _ask_modules(interactive: bool) -> SetupModules:
    """Ask the user which modules to install. Returns all if non-interactive."""
    if not interactive:
        return SetupModules()

    print("Which modules do you want to install?")
    print("  [a] All (default)")
    print("  [c] Choose individually")
    try:
        choice = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return SetupModules()

    if choice not in ("c", "choose"):
        return SetupModules()

    modules = SetupModules()
    _ask = _interactive_yn

    modules.torch = _ask("PyTorch (required for easyocr GPU)", default=True)
    modules.easyocr = _ask("EasyOCR (text extraction from video frames)", default=True)
    modules.opencv = _ask("OpenCV (frame extraction and image processing)", default=True)
    modules.tesseract = _ask("pytesseract (secondary OCR engine)", default=True)
    modules.scenedetect = _ask("scenedetect (scene change detection)", default=True)
    modules.whisper = _ask("faster-whisper (local audio transcription)", default=True)

    return modules


def _interactive_yn(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question, return bool."""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"  {prompt}? {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


# =============================================================================
# Orchestrator
# =============================================================================


def run_setup(interactive: bool = True) -> int:
    """Auto-detect GPU and install all visual extraction dependencies.

    Handles:
    1. Venv creation (if not in one)
    2. GPU detection
    3. Module selection (optional — interactive only)
    4. System dep checks (tesseract binary)
    5. ROCm env var configuration
    6. PyTorch installation (correct GPU variant)
    7. Visual deps installation
    8. Verification

    Args:
        interactive: If True, prompt user for confirmation before installing.

    Returns:
        0 on success, 1 on failure.
    """
    print("=" * 60)
    print("  Video Visual Extraction Setup")
    print("=" * 60)
    print()

    total_steps = 7

    # ── Step 1: Venv check ──
    print(f"[1/{total_steps}] Checking environment...")
    if is_in_venv():
        print(f"  Already in venv: {sys.prefix}")
        python_exe = sys.executable
    else:
        print("  Not in a virtual environment.")
        venv_path = ".venv"
        if interactive:
            try:
                answer = input(f"  Create venv at ./{venv_path}? [Y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup cancelled.")
                return 1
            if answer and answer not in ("y", "yes"):
                print("  Continuing without venv (installing to system Python).")
                python_exe = sys.executable
            else:
                if not create_venv(venv_path):
                    print("  FAILED: Could not create venv.")
                    return 1
                python_exe = get_venv_python(venv_path)
                activate_cmd = get_venv_activate_cmd(venv_path)
                print(f"  Venv created at ./{venv_path}")
                print(f"  Installing skill-seekers into venv...")
                if not install_skill_seekers(python_exe):
                    print("  FAILED: Could not install skill-seekers into venv.")
                    return 1
                print(f"  After setup completes, activate with:")
                print(f"    {activate_cmd}")
        else:
            # Non-interactive: use current python
            python_exe = sys.executable
    print()

    # ── Step 2: GPU detection ──
    print(f"[2/{total_steps}] Detecting GPU...")
    gpu_info = detect_gpu()

    vendor_label = {
        GPUVendor.NVIDIA: "NVIDIA (CUDA)",
        GPUVendor.AMD: "AMD (ROCm)",
        GPUVendor.NONE: "CPU-only",
    }
    print(f"  GPU:    {gpu_info.name}")
    print(f"  Vendor: {vendor_label.get(gpu_info.vendor, gpu_info.vendor.value)}")
    if gpu_info.compute_version:
        print(f"  Version: {gpu_info.compute_version}")
    for detail in gpu_info.details:
        print(f"  {detail}")
    print(f"  PyTorch index: {gpu_info.index_url}")
    print()

    # ── Step 3: Module selection ──
    print(f"[3/{total_steps}] Selecting modules...")
    modules = _ask_modules(interactive)
    deps = _build_visual_deps(modules)
    print(f"  Selected: {', '.join(deps) if deps else '(none)'}")
    if modules.torch:
        print(f"  + PyTorch + torchvision")
    print()

    # ── Step 4: System dependency check ──
    print(f"[4/{total_steps}] Checking system dependencies...")
    if modules.tesseract:
        tess = check_tesseract()
        if not tess["installed"]:
            print(f"  WARNING: tesseract binary not found!")
            print(f"  The pytesseract Python package needs the tesseract binary installed.")
            print(f"  Install it with: {tess['install_cmd']}")
            print()
        elif not tess["has_eng"]:
            print(f"  WARNING: tesseract installed ({tess['version']}) but English data missing!")
            print(f"  Install with: {tess['install_cmd']}")
            print()
        else:
            print(f"  tesseract: {tess['version']} (eng data OK)")
    else:
        print("  tesseract: skipped (not selected)")
    print()

    # ── Step 5: ROCm configuration ──
    print(f"[5/{total_steps}] Configuring GPU environment...")
    if gpu_info.vendor == GPUVendor.AMD:
        changes = configure_rocm_env()
        if changes:
            print("  Set ROCm environment variables:")
            for c in changes:
                print(f"    {c}")
            print("  (These fix MIOpen workspace allocation issues)")
        else:
            print("  ROCm env vars already configured.")
    elif gpu_info.vendor == GPUVendor.NVIDIA:
        print("  NVIDIA: no extra configuration needed.")
    else:
        print("  CPU-only: no GPU configuration needed.")
    print()

    # ── Step 6: Confirm and install ──
    if interactive:
        print("Ready to install. Summary:")
        if modules.torch:
            print(f"  - PyTorch + torchvision (from {gpu_info.index_url})")
        for dep in deps:
            print(f"  - {dep}")
        print()
        try:
            answer = input("Proceed? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if answer and answer not in ("y", "yes"):
            print("Setup cancelled.")
            return 1
        print()

    print(f"[6/{total_steps}] Installing packages...")
    if modules.torch:
        print("  Installing PyTorch...")
        if not install_torch(gpu_info, python_exe):
            print("  FAILED: PyTorch installation failed.")
            print(
                f"  Try: {python_exe} -m pip install torch torchvision --index-url {gpu_info.index_url}"
            )
            return 1
        print("  PyTorch installed.")

    if deps:
        print("  Installing visual packages...")
        if not install_visual_deps(modules, python_exe):
            print("  FAILED: Visual packages installation failed.")
            print(f"  Try: {python_exe} -m pip install {' '.join(deps)}")
            return 1
        print("  Visual packages installed.")
    print()

    # ── Step 7: Verify ──
    print(f"[7/{total_steps}] Verifying installation...")
    results = verify_installation()
    all_ok = True
    for pkg, ok in results.items():
        status = "OK" if ok else "MISSING"
        print(f"  {pkg}: {status}")
        # torch.cuda / torch.rocm are informational, not required
        if not ok and pkg not in ("torch.cuda", "torch.rocm"):
            # Only count as failure if the module was selected
            if pkg == "torch" and modules.torch:
                all_ok = False
            elif pkg == "easyocr" and modules.easyocr:
                all_ok = False
            elif pkg == "opencv" and modules.opencv:
                all_ok = False
            elif pkg == "pytesseract" and modules.tesseract:
                all_ok = False
            elif pkg == "scenedetect" and modules.scenedetect:
                all_ok = False
            elif pkg == "faster-whisper" and modules.whisper:
                all_ok = False

    print()
    if all_ok:
        print("Setup complete! You can now use: skill-seekers video --url <URL> --visual")
        if not is_in_venv() and python_exe != sys.executable:
            activate_cmd = get_venv_activate_cmd()
            print(f"\nDon't forget to activate the venv first:")
            print(f"  {activate_cmd}")
    else:
        print("Some packages failed to install. Check the output above.")
        return 1

    return 0
