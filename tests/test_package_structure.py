"""Test suite for Python package structure.

Tests that the package structure is correct and imports work properly.
This ensures Phase 0 refactoring is successful.
"""

import pytest
import sys
from pathlib import Path


class TestCliPackage:
    """Test cli package structure and imports."""

    def test_cli_package_exists(self):
        """Test that cli package can be imported."""
        import cli
        assert cli is not None

    def test_cli_has_version(self):
        """Test that cli package has __version__."""
        import cli
        assert hasattr(cli, '__version__')
        assert cli.__version__ == '1.3.0'

    def test_cli_has_all(self):
        """Test that cli package has __all__ export list."""
        import cli
        assert hasattr(cli, '__all__')
        assert isinstance(cli.__all__, list)
        assert len(cli.__all__) > 0

    def test_llms_txt_detector_import(self):
        """Test that LlmsTxtDetector can be imported from cli."""
        from cli import LlmsTxtDetector
        assert LlmsTxtDetector is not None

    def test_llms_txt_downloader_import(self):
        """Test that LlmsTxtDownloader can be imported from cli."""
        from cli import LlmsTxtDownloader
        assert LlmsTxtDownloader is not None

    def test_llms_txt_parser_import(self):
        """Test that LlmsTxtParser can be imported from cli."""
        from cli import LlmsTxtParser
        assert LlmsTxtParser is not None

    def test_open_folder_import(self):
        """Test that open_folder can be imported from cli (if utils exists)."""
        try:
            from cli import open_folder
            # If import succeeds, function should not be None
            assert open_folder is not None
        except ImportError:
            # If utils.py doesn't exist, that's okay for now
            pytest.skip("utils.py not found, skipping open_folder test")

    def test_cli_exports_match_all(self):
        """Test that exported items in __all__ can actually be imported."""
        import cli
        for item_name in cli.__all__:
            if item_name == 'open_folder' and cli.open_folder is None:
                # open_folder might be None if utils doesn't exist
                continue
            assert hasattr(cli, item_name), f"{item_name} not found in cli package"


class TestMcpPackage:
    """Test skill_seeker_mcp package structure and imports."""

    def test_mcp_package_exists(self):
        """Test that skill_seeker_mcp package can be imported."""
        import skill_seeker_mcp
        assert skill_seeker_mcp is not None

    def test_mcp_has_version(self):
        """Test that skill_seeker_mcp package has __version__."""
        import skill_seeker_mcp
        assert hasattr(skill_seeker_mcp, '__version__')
        assert skill_seeker_mcp.__version__ == '1.2.0'

    def test_mcp_has_all(self):
        """Test that skill_seeker_mcp package has __all__ export list."""
        import skill_seeker_mcp
        assert hasattr(skill_seeker_mcp, '__all__')
        assert isinstance(skill_seeker_mcp.__all__, list)

    def test_mcp_tools_package_exists(self):
        """Test that skill_seeker_mcp.tools subpackage can be imported."""
        import skill_seeker_mcp.tools
        assert skill_seeker_mcp.tools is not None

    def test_mcp_tools_has_version(self):
        """Test that skill_seeker_mcp.tools has __version__."""
        import skill_seeker_mcp.tools
        assert hasattr(skill_seeker_mcp.tools, '__version__')
        assert skill_seeker_mcp.tools.__version__ == '1.2.0'


class TestPackageStructure:
    """Test overall package structure integrity."""

    def test_cli_init_file_exists(self):
        """Test that cli/__init__.py exists."""
        init_file = Path(__file__).parent.parent / 'cli' / '__init__.py'
        assert init_file.exists(), "cli/__init__.py not found"

    def test_mcp_init_file_exists(self):
        """Test that skill_seeker_mcp/__init__.py exists."""
        init_file = Path(__file__).parent.parent / 'skill_seeker_mcp' / '__init__.py'
        assert init_file.exists(), "skill_seeker_mcp/__init__.py not found"

    def test_mcp_tools_init_file_exists(self):
        """Test that skill_seeker_mcp/tools/__init__.py exists."""
        init_file = Path(__file__).parent.parent / 'skill_seeker_mcp' / 'tools' / '__init__.py'
        assert init_file.exists(), "skill_seeker_mcp/tools/__init__.py not found"

    def test_cli_init_has_docstring(self):
        """Test that cli/__init__.py has a module docstring."""
        import cli
        assert cli.__doc__ is not None
        assert len(cli.__doc__) > 50  # Should have substantial documentation

    def test_mcp_init_has_docstring(self):
        """Test that skill_seeker_mcp/__init__.py has a module docstring."""
        import skill_seeker_mcp
        assert skill_seeker_mcp.__doc__ is not None
        assert len(skill_seeker_mcp.__doc__) > 50  # Should have substantial documentation


class TestImportPatterns:
    """Test that various import patterns work correctly."""

    def test_direct_module_import(self):
        """Test importing modules directly."""
        from cli import llms_txt_detector
        from cli import llms_txt_downloader
        from cli import llms_txt_parser
        assert llms_txt_detector is not None
        assert llms_txt_downloader is not None
        assert llms_txt_parser is not None

    def test_class_import_from_package(self):
        """Test importing classes from package."""
        from cli import LlmsTxtDetector, LlmsTxtDownloader, LlmsTxtParser
        assert LlmsTxtDetector.__name__ == 'LlmsTxtDetector'
        assert LlmsTxtDownloader.__name__ == 'LlmsTxtDownloader'
        assert LlmsTxtParser.__name__ == 'LlmsTxtParser'

    def test_package_level_import(self):
        """Test importing entire packages."""
        import cli
        import skill_seeker_mcp
        import skill_seeker_mcp.tools
        assert 'cli' in sys.modules
        assert 'skill_seeker_mcp' in sys.modules
        assert 'skill_seeker_mcp.tools' in sys.modules


class TestBackwardsCompatibility:
    """Test that existing code patterns still work."""

    def test_direct_file_import_still_works(self):
        """Test that direct file imports still work (backwards compatible)."""
        # This ensures we didn't break existing code
        from cli.llms_txt_detector import LlmsTxtDetector
        from cli.llms_txt_downloader import LlmsTxtDownloader
        from cli.llms_txt_parser import LlmsTxtParser
        assert LlmsTxtDetector is not None
        assert LlmsTxtDownloader is not None
        assert LlmsTxtParser is not None

    def test_module_path_import_still_works(self):
        """Test that module-level imports still work."""
        import cli.llms_txt_detector as detector
        import cli.llms_txt_downloader as downloader
        import cli.llms_txt_parser as parser
        assert detector is not None
        assert downloader is not None
        assert parser is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
