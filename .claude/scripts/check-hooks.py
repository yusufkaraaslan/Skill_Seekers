#!/usr/bin/env python3
"""
Hook Validation System for Claude Code

Comprehensive validation of Claude Code hook configuration, syntax, and functionality.
"""

import json
import os
import sys
import subprocess
import time
import stat
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

class HookValidator:
    """Comprehensive hook validation system."""

    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.settings_file = self.project_dir / ".claude" / "settings.json"
        self.issues = []
        self.fixes_applied = []
        self.test_results = {}

    def validate_all(self, fix: bool = False, test: bool = False, verbose: bool = False,
                    hooks_filter: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive hook validation."""
        print("🔍 Hook Validation Report")
        print("=" * 24)
        print()

        results = {
            'configuration': False,
            'paths': False,
            'permissions': False,
            'environment': False,
            'hooks': {},
            'overall_score': 0,
            'issues': [],
            'fixes_applied': []
        }

        # 1. Configuration Validation
        print("📋 Validating configuration...")
        results['configuration'] = self._validate_configuration()

        # 2. Path Resolution
        print("📍 Checking paths...")
        results['paths'] = self._validate_paths()

        # 3. Permission Validation
        print("🔐 Checking permissions...")
        results['permissions'] = self._validate_permissions()

        # 4. Environment Validation
        print("🐍 Validating environment...")
        results['environment'] = self._validate_environment()

        # 5. Hook-specific validation
        if self.settings_file.exists():
            settings = self._load_settings()
            if settings and 'hooks' in settings:
                hooks_to_check = hooks_filter or ['SessionStart', 'PreToolUse', 'PostToolUse']

                for hook_type in hooks_to_check:
                    if hook_type in settings['hooks']:
                        print(f"🔧 Testing {hook_type} hooks...")
                        results['hooks'][hook_type] = self._validate_hook_type(
                            settings['hooks'][hook_type], hook_type, test
                        )

        # 6. Apply fixes if requested
        if fix and self.issues:
            print("\n🔨 Applying fixes...")
            self._apply_fixes()
            results['fixes_applied'] = self.fixes_applied

        # 7. Calculate overall score
        results['overall_score'] = self._calculate_score(results)
        results['issues'] = self.issues

        # 8. Generate report
        self._generate_report(results, verbose)

        return results

    def _validate_configuration(self) -> bool:
        """Validate JSON configuration syntax."""
        try:
            if not self.settings_file.exists():
                self.issues.append(("❌ Critical", f"Settings file not found: {self.settings_file}"))
                return False

            with open(self.settings_file) as f:
                json.load(f)

            print("✅ Valid JSON syntax")
            return True

        except json.JSONDecodeError as e:
            self.issues.append(("❌ Critical", f"JSON syntax error: {e}"))
            return False
        except Exception as e:
            self.issues.append(("❌ Critical", f"Configuration error: {e}"))
            return False

    def _validate_paths(self) -> bool:
        """Validate that all paths in hooks are accessible."""
        if not self.settings_file.exists():
            return False

        try:
            settings = self._load_settings()
            if not settings or 'hooks' not in settings:
                return False

            all_paths_valid = True

            for hook_type, hook_config in settings['hooks'].items():
                for hook_group in hook_config:
                    if 'hooks' not in hook_group:
                        continue

                    for hook in hook_group['hooks']:
                        if hook.get('type') == 'command':
                            command = hook.get('command', '')
                            if not command:
                                continue

                            # Extract paths from command
                            paths_in_command = self._extract_paths_from_command(command)
                            for path in paths_in_command:
                                path_obj = Path(path)
                                if not path_obj.exists():
                                    self.issues.append(("⚠️ Warning", f"Path not found: {path}"))
                                    all_paths_valid = False
                                else:
                                    if self.is_verbose:
                                        print(f"  ✅ Path valid: {path}")

            if all_paths_valid:
                print("✅ All executable paths resolved")

            return all_paths_valid

        except Exception as e:
            self.issues.append(("❌ Critical", f"Path validation error: {e}"))
            return False

    def _validate_permissions(self) -> bool:
        """Validate executable permissions on hook scripts."""
        if not self.settings_file.exists():
            return False

        try:
            settings = self._load_settings()
            if not settings or 'hooks' not in settings:
                return False

            all_permissions_valid = True

            for hook_type, hook_config in settings['hooks'].items():
                for hook_group in hook_config:
                    if 'hooks' not in hook_group:
                        continue

                    for hook in hook_group['hooks']:
                        if hook.get('type') == 'command':
                            command = hook.get('command', '')
                            if not command:
                                continue

                            # Extract executable paths
                            executable_paths = self._extract_executable_paths(command)
                            for exe_path in executable_paths:
                                path_obj = Path(exe_path)
                                if path_obj.exists() and not os.access(exe_path, os.X_OK):
                                    self.issues.append(("⚠️ Warning", f"Missing execute permission: {exe_path}"))
                                    all_permissions_valid = False
                                elif path_obj.exists() and os.access(exe_path, os.X_OK):
                                    if self.is_verbose:
                                        print(f"  ✅ Executable: {exe_path}")

            if all_permissions_valid:
                print("✅ All scripts have execute permissions")

            return all_permissions_valid

        except Exception as e:
            self.issues.append(("❌ Critical", f"Permission validation error: {e}"))
            return False

    def _validate_environment(self) -> bool:
        """Validate Python virtual environment and dependencies."""
        try:
            # Check common virtual environment locations
            venv_paths = [
                self.project_dir / ".claude" / "skills" / "agent-scaffolding-toolkit" / ".venv",
                self.project_dir / ".venv",
                self.project_dir / "venv"
            ]

            venv_found = False
            for venv_path in venv_paths:
                if venv_path.exists():
                    python_exe = venv_path / "bin" / "python3"
                    if python_exe.exists():
                        if self.is_verbose:
                            print(f"  ✅ Python environment: {venv_path}")
                        venv_found = True
                        break

            if not venv_found:
                self.issues.append(("⚠️ Warning", "No Python virtual environment found"))
                print("⚠️  No Python virtual environment found")
                return False

            print("✅ Python virtual environment healthy")
            return True

        except Exception as e:
            self.issues.append(("❌ Critical", f"Environment validation error: {e}"))
            return False

    def _validate_hook_type(self, hook_config: List[Dict], hook_type: str, test: bool = False) -> Dict:
        """Validate a specific hook type."""
        results = {
            'total_hooks': 0,
            'testable_hooks': 0,
            'working_hooks': 0,
            'untestable_hooks': 0,
            'issues': [],
            'test_results': {}
        }

        for hook_group in hook_config:
            if 'hooks' not in hook_group:
                continue

            for i, hook in enumerate(hook_group['hooks']):
                results['total_hooks'] += 1
                hook_name = f"{hook_type}[{i}]"

                if hook.get('type') == 'command':
                    results['testable_hooks'] += 1
                    success, issue = self._test_hook_command(hook, hook_name, test)
                    if success:
                        results['working_hooks'] += 1
                    else:
                        results['issues'].append(issue)
                elif hook.get('type') == 'prompt':
                    results['untestable_hooks'] += 1
                    # Prompt hooks can't be tested but are counted for reporting

        # Calculate percentage based only on testable hooks
        working_pct = (results['working_hooks'] / results['testable_hooks'] * 100) if results['testable_hooks'] > 0 else 100

        if results['testable_hooks'] > 0:
            status = "✅" if working_pct == 100 else "⚠️" if working_pct >= 50 else "❌"
            testable_part = f"{results['working_hooks']}/{results['testable_hooks']} testable"
        else:
            status = "✅"  # All untestable hooks are considered OK
            testable_part = "0 testable"

        if results['untestable_hooks'] > 0:
            untestable_part = f", {results['untestable_hooks']} untestable"
        else:
            untestable_part = ""

        print(f"  {status} {testable_part}{untestable_part} hooks working")

        return results

    def _test_hook_command(self, hook: Dict, hook_name: str, test: bool = False) -> Tuple[bool, str]:
        """Test a single hook command."""
        command = hook.get('command', '')
        if not command:
            return False, f"{hook_name}: Empty command"

        try:
            # For testing, we need to provide appropriate input
            input_data = '{"tool_input":{"file_path":"/test/path"}}'

            if test:
                # Actually run the command with test input
                result = subprocess.run(
                    command.split(),
                    input=input_data,
                    text=True,
                    capture_output=True,
                    timeout=10
                )

                success = result.returncode == 0
                if not success and result.stderr:
                    return False, f"{hook_name}: {result.stderr.strip()}"

                self.test_results[hook_name] = {
                    'exit_code': result.returncode,
                    'stdout': result.stdout[:200],
                    'stderr': result.stderr[:200]
                }
            else:
                # Just check if command would run (dry run)
                # Extract the executable part
                parts = command.split()
                if parts:
                    exe_path = parts[0]
                    if not Path(exe_path).exists():
                        return False, f"{hook_name}: Executable not found: {exe_path}"

            return True, ""

        except subprocess.TimeoutExpired:
            return False, f"{hook_name}: Timeout (10s)"
        except Exception as e:
            return False, f"{hook_name}: {e}"

    def _extract_paths_from_command(self, command: str) -> List[str]:
        """Extract file paths from a hook command."""
        parts = command.split()
        paths = []

        for part in parts:
            # Skip the command and options
            if part.startswith('-') or '=' in part:
                continue

            # Check if it looks like a file path
            if '/' in part and not part.startswith('$'):
                path_obj = Path(part)
                if path_obj.exists():
                    paths.append(str(path_obj))

        return paths

    def _extract_executable_paths(self, command: str) -> List[str]:
        """Extract executable paths from a hook command."""
        parts = command.split()
        executables = []

        for part in parts:
            # Skip options and environment variables
            if part.startswith('-') or '=' in part or part.startswith('$'):
                continue

            # Check if it exists and is executable
            path_obj = Path(part)
            if path_obj.exists():
                executables.append(str(path_obj))

        return executables

    def _apply_fixes(self):
        """Apply automatic fixes to common issues."""
        for severity, issue in self.issues:
            if "JSON syntax error" in issue:
                # Try to fix common JSON syntax issues
                self._fix_json_syntax()
            elif "Missing execute permission" in issue:
                # Fix executable permissions
                path = issue.split(": ")[1]
                try:
                    os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                    self.fixes_applied.append(f"Fixed permissions: {path}")
                except Exception as e:
                    self.issues.append(("❌ Critical", f"Could not fix permissions: {e}"))
            elif "environment variable" in issue.lower():
                # Fix environment variable issues
                self._fix_environment_variables()

    def _fix_json_syntax(self):
        """Attempt to fix JSON syntax issues."""
        try:
            with open(self.settings_file, 'r') as f:
                content = f.read()

            # Fix common quote escaping issues
            fixed_content = content.replace('\\"', '"')

            with open(self.settings_file, 'w') as f:
                f.write(fixed_content)

            self.fixes_applied.append("Fixed JSON quote escaping")
        except Exception as e:
            self.issues.append(("❌ Critical", f"Could not fix JSON: {e}"))

    def _fix_environment_variables(self):
        """Replace environment variables with absolute paths."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

            modified = False
            for hook_type, hook_config in settings.get('hooks', {}).items():
                for hook_group in hook_config:
                    for hook in hook_group.get('hooks', []):
                        if hook.get('type') == 'command':
                            command = hook.get('command', '')
                            if '$CLAUDE_PROJECT_DIR' in command:
                                # Replace with absolute path
                                abs_command = command.replace('$CLAUDE_PROJECT_DIR', str(self.project_dir))
                                hook['command'] = abs_command
                                modified = True

            if modified:
                with open(self.settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                self.fixes_applied.append("Replaced environment variables with absolute paths")

        except Exception as e:
            self.issues.append(("❌ Critical", f"Could not fix environment variables: {e}"))

    def _calculate_score(self, results: Dict) -> int:
        """Calculate overall hook health score."""
        scores = []

        # Base components (20% each)
        scores.append(20 if results['configuration'] else 0)  # Configuration
        scores.append(20 if results['paths'] else 0)         # Paths
        scores.append(20 if results['permissions'] else 0)   # Permissions
        scores.append(20 if results['environment'] else 0)   # Environment

        # Hook functionality (20%)
        hook_score = self._calculate_hook_score(results['hooks'])
        scores.append(hook_score)

        return sum(scores)

    def _calculate_hook_score(self, hooks_results: Dict) -> int:
        """Calculate hook functionality score."""
        if not hooks_results:
            return 20  # No hooks configured is considered OK

        total_testable = 0
        total_working = 0

        for hook_type, hook_results in hooks_results.items():
            total_testable += hook_results.get('testable_hooks', 0)
            total_working += hook_results.get('working_hooks', 0)

        if total_testable == 0:
            # No testable hooks - all untestable (prompt) hooks, which is fine
            return 20

        # Calculate percentage of testable hooks that are working
        working_pct = (total_working / total_testable) * 100

        # Convert to 20-point scale
        return int((working_pct / 100) * 20)

    def _generate_report(self, results: Dict, verbose: bool = False):
        """Generate a detailed validation report."""
        print()

        # Summary
        config_status = "✅ Valid JSON syntax" if results['configuration'] else "❌ Configuration errors"
        paths_status = "✅ All executable paths resolved" if results['paths'] else "❌ Path issues found"
        perm_status = "✅ All scripts have execute permissions" if results['permissions'] else "❌ Permission issues found"
        env_status = "✅ Python virtual environment healthy" if results['environment'] else "❌ Environment issues found"

        print(f"Configuration: {config_status}")
        print(f"Paths: {paths_status}")
        print(f"Permissions: {perm_status}")
        print(f"Environment: {env_status}")
        print()

        # Hook summary
        for hook_type, hook_results in results['hooks'].items():
            working = hook_results['working_hooks']
            testable = hook_results['testable_hooks']
            untestable = hook_results.get('untestable_hooks', 0)
            total = hook_results['total_hooks']

            if testable > 0:
                status = "✅" if working == testable else "⚠️" if working > 0 else "❌"
                if untestable > 0:
                    print(f"{hook_type}: {status} {working}/{testable} testable, {untestable} untestable hooks")
                else:
                    print(f"{hook_type}: {status} {working}/{testable} hooks working")
            else:
                # All untestable hooks
                print(f"{hook_type}: ✅ {untestable} untestable hooks")

        print()

        # Overall health
        score = results['overall_score']
        if score >= 95:
            health_emoji = "🟢"
            health_status = "Excellent"
        elif score >= 80:
            health_emoji = "🟡"
            health_status = "Good"
        elif score >= 60:
            health_emoji = "🟠"
            health_status = "Fair"
        else:
            health_emoji = "🔴"
            health_status = "Poor"

        print(f"Overall Health: {health_emoji} {health_status} ({score}%)")

        # Issues summary
        if results['issues']:
            print()
            print("🚨 Issues found:")
            for severity, issue in results['issues']:
                print(f"  {severity}: {issue}")

        # Fixes applied
        if results['fixes_applied']:
            print()
            print("🔨 Fixes applied:")
            for fix in results['fixes_applied']:
                print(f"  ✅ {fix}")

        # Test results (if verbose)
        if verbose and self.test_results:
            print()
            print("🧪 Test Results:")
            for hook_name, test_result in self.test_results.items():
                print(f"  {hook_name}: Exit {test_result['exit_code']}")
                if test_result['stderr']:
                    print(f"    STDERR: {test_result['stderr']}")

    def _load_settings(self) -> Dict:
        """Load and parse settings file."""
        try:
            with open(self.settings_file) as f:
                return json.load(f)
        except Exception:
            return None

def main():
    """Main entry point for hook validation."""
    parser = argparse.ArgumentParser(description="Validate Claude Code hooks")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes")
    parser.add_argument("--test", action="store_true", help="Test hooks with sample data")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--hooks", nargs="+", choices=["SessionStart", "PreToolUse", "PostToolUse"],
                       help="Specific hook types to check")
    parser.add_argument("--project-dir", help="Project directory (default: current)")

    args = parser.parse_args()

    validator = HookValidator(args.project_dir)
    validator.is_verbose = args.verbose

    start_time = time.time()
    results = validator.validate_all(
        fix=args.fix,
        test=args.test,
        verbose=args.verbose,
        hooks_filter=args.hooks
    )
    elapsed = time.time() - start_time

    print(f"\n⏱️  Total validation time: {elapsed:.1f}s")

    # Exit with appropriate code
    if results['overall_score'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues found

if __name__ == "__main__":
    main()