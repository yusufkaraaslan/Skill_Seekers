#!/usr/bin/env python3
"""
Verification script for finance-screener TDD setup.

Mental Model: Systems Thinking
- Verify all components integrate correctly
- Check for missing dependencies, configuration issues

Run: python3 verify_setup.py
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """Run shell command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def check_python_version() -> bool:
    """Check Python version >= 3.10."""
    print("✓ Checking Python version...")
    if sys.version_info >= (3, 10):
        print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
        return True
    else:
        print(f"  ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need >= 3.10)")
        return False


def check_project_structure() -> bool:
    """Check required directories and files exist."""
    print("\n✓ Checking project structure...")
    
    required_paths = [
        "pyproject.toml",
        ".env.example",
        "skill_seeker_mcp/__init__.py",
        "skill_seeker_mcp/finance_tools/__init__.py",
        "skill_seeker_mcp/finance_tools/discovery.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_discovery.py",
    ]
    
    project_root = Path(__file__).parent
    missing = []
    
    for path in required_paths:
        full_path = project_root / path
        if not full_path.exists():
            missing.append(path)
    
    if missing:
        print(f"  ❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print(f"  ✅ All required files present ({len(required_paths)} files)")
        return True


def check_pytest_config() -> bool:
    """Check pytest configuration."""
    print("\n✓ Checking pytest configuration...")
    
    project_root = Path(__file__).parent
    pyproject = project_root / "pyproject.toml"
    
    if not pyproject.exists():
        print("  ❌ pyproject.toml not found")
        return False
    
    content = pyproject.read_text()
    
    required_configs = [
        "[tool.pytest.ini_options]",
        "testpaths",
        "asyncio_mode",
        "--cov",
        "--cov-fail-under=80"
    ]
    
    missing = [cfg for cfg in required_configs if cfg not in content]
    
    if missing:
        print(f"  ❌ Missing pytest configs: {', '.join(missing)}")
        return False
    else:
        print("  ✅ pytest configuration valid")
        return True


def check_test_collection() -> bool:
    """Check if pytest can collect tests."""
    print("\n✓ Checking test collection...")
    
    project_root = Path(__file__).parent
    exit_code, stdout, stderr = run_command(
        ["python3", "-m", "pytest", "--collect-only", "-q"],
        cwd=project_root
    )
    
    if exit_code != 0:
        print(f"  ❌ pytest collection failed")
        print(f"     stderr: {stderr}")
        return False
    
    # Count collected tests
    lines = stdout.split('\n')
    test_count = sum(1 for line in lines if '::test_' in line)
    
    if test_count == 0:
        print("  ❌ No tests collected")
        return False
    else:
        print(f"  ✅ Collected {test_count} tests")
        return True


def check_imports() -> bool:
    """Check if Python can import our modules."""
    print("\n✓ Checking module imports...")
    
    try:
        # Try importing our modules (will fail if dependencies missing)
        import_test = """
import sys
sys.path.insert(0, 'finance-screener')

# Check if modules can be imported
try:
    from skill_seeker_mcp.finance_tools import discovery
    print("discovery_ok")
except ImportError as e:
    print(f"discovery_error: {e}")

try:
    import pytest
    print("pytest_ok")
except ImportError:
    print("pytest_error")
"""
        
        project_root = Path(__file__).parent
        exit_code, stdout, stderr = run_command(
            ["python3", "-c", import_test],
            cwd=project_root.parent
        )
        
        if "discovery_ok" in stdout:
            print("  ✅ Module imports working")
            return True
        else:
            print("  ⚠️  Module imports may require dependencies")
            print("     Run: pip install -e '.[dev]'")
            return False
    
    except Exception as e:
        print(f"  ❌ Import check failed: {e}")
        return False


def check_mental_model_documentation() -> bool:
    """Check if mental models are documented in code."""
    print("\n✓ Checking mental model documentation...")
    
    project_root = Path(__file__).parent
    discovery_file = project_root / "skill_seeker_mcp" / "finance_tools" / "discovery.py"
    test_file = project_root / "tests" / "test_discovery.py"
    
    required_models = [
        "First Principles",
        "Second Order Effects",
        "Systems Thinking",
        "Inversion",
    ]
    
    discovery_content = discovery_file.read_text()
    test_content = test_file.read_text()
    combined = discovery_content + test_content
    
    missing = [model for model in required_models if model not in combined]
    
    if missing:
        print(f"  ⚠️  Mental models not documented: {', '.join(missing)}")
        print("     (Recommended but not required)")
        return True  # Warning only
    else:
        print(f"  ✅ All {len(required_models)} mental models documented")
        return True


def main() -> int:
    """Run all verification checks."""
    print("=" * 60)
    print("Finance Screener TDD Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Pytest Configuration", check_pytest_config),
        ("Test Collection", check_test_collection),
        ("Module Imports", check_imports),
        ("Mental Model Docs", check_mental_model_documentation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nScore: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! TDD setup complete.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -e '.[dev]'")
        print("  2. Run tests: pytest -v")
        print("  3. Check coverage: pytest --cov")
        return 0
    else:
        print("\n⚠️  Some checks failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
