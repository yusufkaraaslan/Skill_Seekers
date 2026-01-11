#!/usr/bin/env python3
"""
Configuration Pattern Extraction (C3.4)

Extracts configuration patterns from actual config files in the codebase.
Supports JSON, YAML, TOML, ENV, INI, Python config modules, and more.

This is different from C3.2 which extracts config examples from test code.
C3.4 focuses on documenting the actual project configuration.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Literal
import ast

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.debug("PyYAML not available - YAML parsing will be limited")

try:
    import tomli
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False
        logger.debug("toml/tomli not available - TOML parsing disabled")


@dataclass
class ConfigSetting:
    """Individual configuration setting"""
    key: str
    value: Any
    value_type: str  # 'string', 'integer', 'boolean', 'array', 'object', 'null'
    default_value: Optional[Any] = None
    required: bool = False
    env_var: Optional[str] = None
    description: str = ""
    validation: Dict[str, Any] = field(default_factory=dict)
    nested_path: List[str] = field(default_factory=list)  # For nested configs


@dataclass
class ConfigFile:
    """Represents a configuration file"""
    file_path: str
    relative_path: str
    config_type: Literal["json", "yaml", "toml", "env", "ini", "python", "javascript", "dockerfile", "docker-compose"]
    purpose: str  # Inferred purpose: database, api, logging, etc.
    settings: List[ConfigSetting] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    raw_content: Optional[str] = None
    parse_errors: List[str] = field(default_factory=list)


@dataclass
class ConfigExtractionResult:
    """Result of config extraction"""
    config_files: List[ConfigFile] = field(default_factory=list)
    total_files: int = 0
    total_settings: int = 0
    detected_patterns: Dict[str, List[str]] = field(default_factory=dict)  # pattern -> files
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON output"""
        return {
            'total_files': self.total_files,
            'total_settings': self.total_settings,
            'detected_patterns': self.detected_patterns,
            'config_files': [
                {
                    'file_path': cf.file_path,
                    'relative_path': cf.relative_path,
                    'type': cf.config_type,
                    'purpose': cf.purpose,
                    'patterns': cf.patterns,
                    'settings_count': len(cf.settings),
                    'settings': [
                        {
                            'key': s.key,
                            'value': s.value,
                            'type': s.value_type,
                            'env_var': s.env_var,
                            'description': s.description,
                        }
                        for s in cf.settings
                    ],
                    'parse_errors': cf.parse_errors,
                }
                for cf in self.config_files
            ],
            'errors': self.errors,
        }

    def to_markdown(self) -> str:
        """Generate markdown report of extraction results"""
        md = "# Configuration Extraction Report\n\n"
        md += f"**Total Files:** {self.total_files}\n"
        md += f"**Total Settings:** {self.total_settings}\n"

        # Handle both dict and list formats for detected_patterns
        if self.detected_patterns:
            if isinstance(self.detected_patterns, dict):
                patterns_str = ', '.join(self.detected_patterns.keys())
            else:
                patterns_str = ', '.join(self.detected_patterns)
        else:
            patterns_str = 'None'
        md += f"**Detected Patterns:** {patterns_str}\n\n"

        if self.config_files:
            md += "## Configuration Files\n\n"
            for cf in self.config_files:
                md += f"### {cf.relative_path}\n\n"
                md += f"- **Type:** {cf.config_type}\n"
                md += f"- **Purpose:** {cf.purpose}\n"
                md += f"- **Settings:** {len(cf.settings)}\n"
                if cf.patterns:
                    md += f"- **Patterns:** {', '.join(cf.patterns)}\n"
                if cf.parse_errors:
                    md += f"- **Errors:** {len(cf.parse_errors)}\n"
                md += "\n"

        if self.errors:
            md += "## Errors\n\n"
            for error in self.errors:
                md += f"- {error}\n"

        return md


class ConfigFileDetector:
    """Detect configuration files in codebase"""

    # Config file patterns by type
    CONFIG_PATTERNS = {
        'json': {
            'patterns': ['*.json', 'package.json', 'tsconfig.json', 'jsconfig.json'],
            'names': ['config.json', 'settings.json', 'app.json', '.eslintrc.json', '.prettierrc.json'],
        },
        'yaml': {
            'patterns': ['*.yaml', '*.yml'],
            'names': ['config.yml', 'settings.yml', '.travis.yml', '.gitlab-ci.yml', 'docker-compose.yml'],
        },
        'toml': {
            'patterns': ['*.toml'],
            'names': ['pyproject.toml', 'Cargo.toml', 'config.toml'],
        },
        'env': {
            'patterns': ['.env*', '*.env'],
            'names': ['.env', '.env.example', '.env.local', '.env.production'],
        },
        'ini': {
            'patterns': ['*.ini', '*.cfg'],
            'names': ['config.ini', 'setup.cfg', 'tox.ini'],
        },
        'python': {
            'patterns': [],
            'names': ['settings.py', 'config.py', 'configuration.py', 'constants.py'],
        },
        'javascript': {
            'patterns': ['*.config.js', '*.config.ts'],
            'names': ['config.js', 'next.config.js', 'vue.config.js', 'webpack.config.js'],
        },
        'dockerfile': {
            'patterns': ['Dockerfile*'],
            'names': ['Dockerfile', 'Dockerfile.dev', 'Dockerfile.prod'],
        },
        'docker-compose': {
            'patterns': ['docker-compose*.yml', 'docker-compose*.yaml'],
            'names': ['docker-compose.yml', 'docker-compose.yaml'],
        },
    }

    # Directories to skip
    SKIP_DIRS = {
        'node_modules', 'venv', 'env', '.venv', '__pycache__', '.git',
        'build', 'dist', '.tox', '.mypy_cache', '.pytest_cache',
        'htmlcov', 'coverage', '.eggs', '*.egg-info'
    }

    def find_config_files(self, directory: Path, max_files: int = 100) -> List[ConfigFile]:
        """
        Find all configuration files in directory.

        Args:
            directory: Root directory to search
            max_files: Maximum number of config files to find

        Returns:
            List of ConfigFile objects
        """
        config_files = []
        found_count = 0

        for file_path in self._walk_directory(directory):
            if found_count >= max_files:
                logger.info(f"Reached max_files limit ({max_files})")
                break

            config_type = self._detect_config_type(file_path)
            if config_type:
                relative_path = str(file_path.relative_to(directory))
                config_file = ConfigFile(
                    file_path=str(file_path),
                    relative_path=relative_path,
                    config_type=config_type,
                    purpose=self._infer_purpose(file_path, config_type)
                )
                config_files.append(config_file)
                found_count += 1
                logger.debug(f"Found {config_type} config: {relative_path}")

        logger.info(f"Found {len(config_files)} configuration files")
        return config_files

    def _walk_directory(self, directory: Path):
        """Walk directory, skipping excluded directories"""
        for item in directory.rglob('*'):
            # Skip directories
            if item.is_dir():
                continue

            # Skip if in excluded directory
            if any(skip_dir in item.parts for skip_dir in self.SKIP_DIRS):
                continue

            yield item

    def _detect_config_type(self, file_path: Path) -> Optional[str]:
        """Detect configuration file type"""
        filename = file_path.name.lower()

        # Check each config type
        for config_type, patterns in self.CONFIG_PATTERNS.items():
            # Check exact name matches
            if filename in patterns['names']:
                return config_type

            # Check pattern matches
            for pattern in patterns['patterns']:
                if file_path.match(pattern):
                    return config_type

        return None

    def _infer_purpose(self, file_path: Path, config_type: str) -> str:
        """Infer configuration purpose from file path and name"""
        path_lower = str(file_path).lower()
        filename = file_path.name.lower()

        # Database configs
        if any(word in path_lower for word in ['database', 'db', 'postgres', 'mysql', 'mongo']):
            return 'database_configuration'

        # API configs
        if any(word in path_lower for word in ['api', 'rest', 'graphql', 'endpoint']):
            return 'api_configuration'

        # Logging configs
        if any(word in path_lower for word in ['log', 'logger', 'logging']):
            return 'logging_configuration'

        # Docker configs
        if 'docker' in filename:
            return 'docker_configuration'

        # CI/CD configs
        if any(word in path_lower for word in ['.travis', '.gitlab', '.github', 'ci', 'cd']):
            return 'ci_cd_configuration'

        # Package configs
        if filename in ['package.json', 'pyproject.toml', 'cargo.toml']:
            return 'package_configuration'

        # TypeScript/JavaScript configs
        if filename in ['tsconfig.json', 'jsconfig.json']:
            return 'typescript_configuration'

        # Framework configs
        if 'next.config' in filename or 'vue.config' in filename or 'webpack.config' in filename:
            return 'framework_configuration'

        # Environment configs
        if '.env' in filename:
            return 'environment_configuration'

        # Default
        return 'general_configuration'


class ConfigParser:
    """Parse different configuration file formats"""

    def parse_config_file(self, config_file: ConfigFile) -> ConfigFile:
        """
        Parse configuration file and extract settings.

        Args:
            config_file: ConfigFile object to parse

        Returns:
            Updated ConfigFile with settings populated
        """
        try:
            # Read file content
            with open(config_file.file_path, 'r', encoding='utf-8') as f:
                config_file.raw_content = f.read()

            # Parse based on type
            if config_file.config_type == 'json':
                self._parse_json(config_file)
            elif config_file.config_type == 'yaml':
                self._parse_yaml(config_file)
            elif config_file.config_type == 'toml':
                self._parse_toml(config_file)
            elif config_file.config_type == 'env':
                self._parse_env(config_file)
            elif config_file.config_type == 'ini':
                self._parse_ini(config_file)
            elif config_file.config_type == 'python':
                self._parse_python_config(config_file)
            elif config_file.config_type == 'javascript':
                self._parse_javascript_config(config_file)
            elif config_file.config_type == 'dockerfile':
                self._parse_dockerfile(config_file)
            elif config_file.config_type == 'docker-compose':
                self._parse_yaml(config_file)  # Docker compose is YAML

        except Exception as e:
            error_msg = f"Error parsing {config_file.relative_path}: {str(e)}"
            logger.warning(error_msg)
            config_file.parse_errors.append(error_msg)

        return config_file

    def _parse_json(self, config_file: ConfigFile):
        """Parse JSON configuration"""
        try:
            data = json.loads(config_file.raw_content)
            self._extract_settings_from_dict(data, config_file)
        except json.JSONDecodeError as e:
            config_file.parse_errors.append(f"JSON parse error: {str(e)}")

    def _parse_yaml(self, config_file: ConfigFile):
        """Parse YAML configuration"""
        if not YAML_AVAILABLE:
            config_file.parse_errors.append("PyYAML not installed")
            return

        try:
            data = yaml.safe_load(config_file.raw_content)
            if isinstance(data, dict):
                self._extract_settings_from_dict(data, config_file)
        except yaml.YAMLError as e:
            config_file.parse_errors.append(f"YAML parse error: {str(e)}")

    def _parse_toml(self, config_file: ConfigFile):
        """Parse TOML configuration"""
        if not TOML_AVAILABLE:
            config_file.parse_errors.append("toml/tomli not installed")
            return

        try:
            if 'tomli' in globals():
                data = tomli.loads(config_file.raw_content)
            else:
                import toml
                data = toml.loads(config_file.raw_content)

            self._extract_settings_from_dict(data, config_file)
        except Exception as e:
            config_file.parse_errors.append(f"TOML parse error: {str(e)}")

    def _parse_env(self, config_file: ConfigFile):
        """Parse .env file"""
        lines = config_file.raw_content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            match = re.match(r'([A-Z_][A-Z0-9_]*)\s*=\s*(.+)', line)
            if match:
                key, value = match.groups()
                value = value.strip().strip('"').strip("'")

                setting = ConfigSetting(
                    key=key,
                    value=value,
                    value_type=self._infer_type(value),
                    env_var=key,
                    description=self._extract_env_description(lines, line_num - 1)
                )
                config_file.settings.append(setting)

    def _parse_ini(self, config_file: ConfigFile):
        """Parse INI configuration"""
        import configparser

        try:
            parser = configparser.ConfigParser()
            parser.read_string(config_file.raw_content)

            for section in parser.sections():
                for key, value in parser[section].items():
                    setting = ConfigSetting(
                        key=f"{section}.{key}",
                        value=value,
                        value_type=self._infer_type(value),
                        nested_path=[section, key]
                    )
                    config_file.settings.append(setting)
        except Exception as e:
            config_file.parse_errors.append(f"INI parse error: {str(e)}")

    def _parse_python_config(self, config_file: ConfigFile):
        """Parse Python configuration module"""
        try:
            tree = ast.parse(config_file.raw_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Get variable name
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                        key = node.targets[0].id

                        # Skip private variables
                        if key.startswith('_'):
                            continue

                        # Extract value
                        try:
                            value = ast.literal_eval(node.value)
                            setting = ConfigSetting(
                                key=key,
                                value=value,
                                value_type=self._infer_type(value),
                                description=self._extract_python_docstring(node)
                            )
                            config_file.settings.append(setting)
                        except (ValueError, TypeError):
                            # Can't evaluate complex expressions
                            pass

        except SyntaxError as e:
            config_file.parse_errors.append(f"Python parse error: {str(e)}")

    def _parse_javascript_config(self, config_file: ConfigFile):
        """Parse JavaScript/TypeScript config (basic extraction)"""
        # Simple regex-based extraction for common patterns
        patterns = [
            r'(?:const|let|var)\s+(\w+)\s*[:=]\s*(["\'])(.*?)\2',  # String values
            r'(?:const|let|var)\s+(\w+)\s*[:=]\s*(\d+)',  # Number values
            r'(?:const|let|var)\s+(\w+)\s*[:=]\s*(true|false)',  # Boolean values
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, config_file.raw_content):
                if len(match.groups()) >= 2:
                    key = match.group(1)
                    value = match.group(3) if len(match.groups()) > 2 else match.group(2)

                    setting = ConfigSetting(
                        key=key,
                        value=value,
                        value_type=self._infer_type(value)
                    )
                    config_file.settings.append(setting)

    def _parse_dockerfile(self, config_file: ConfigFile):
        """Parse Dockerfile configuration"""
        lines = config_file.raw_content.split('\n')

        for line in lines:
            line = line.strip()

            # Extract ENV variables
            if line.startswith('ENV '):
                parts = line[4:].split('=', 1)
                if len(parts) == 2:
                    key, value = parts
                    setting = ConfigSetting(
                        key=key.strip(),
                        value=value.strip(),
                        value_type='string',
                        env_var=key.strip()
                    )
                    config_file.settings.append(setting)

            # Extract ARG variables
            elif line.startswith('ARG '):
                parts = line[4:].split('=', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) == 2 else None

                setting = ConfigSetting(
                    key=key,
                    value=value,
                    value_type='string'
                )
                config_file.settings.append(setting)

    def _extract_settings_from_dict(self, data: Dict, config_file: ConfigFile, parent_path: List[str] = None):
        """Recursively extract settings from dictionary"""
        if parent_path is None:
            parent_path = []

        for key, value in data.items():
            if isinstance(value, dict):
                # Recurse into nested dicts
                self._extract_settings_from_dict(value, config_file, parent_path + [key])
            else:
                setting = ConfigSetting(
                    key='.'.join(parent_path + [key]) if parent_path else key,
                    value=value,
                    value_type=self._infer_type(value),
                    nested_path=parent_path + [key]
                )
                config_file.settings.append(setting)

    def _infer_type(self, value: Any) -> str:
        """Infer value type"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, (list, tuple)):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'string'

    def _extract_env_description(self, lines: List[str], line_index: int) -> str:
        """Extract description from comment above env variable"""
        if line_index > 0:
            prev_line = lines[line_index - 1].strip()
            if prev_line.startswith('#'):
                return prev_line[1:].strip()
        return ""

    def _extract_python_docstring(self, node: ast.AST) -> str:
        """Extract docstring/comment for Python node"""
        # This is simplified - real implementation would need more context
        return ""


class ConfigPatternDetector:
    """Detect common configuration patterns"""

    # Known configuration patterns
    KNOWN_PATTERNS = {
        'database_config': {
            'keys': ['host', 'port', 'database', 'user', 'username', 'password', 'db_name'],
            'min_match': 3,
        },
        'api_config': {
            'keys': ['base_url', 'api_key', 'api_secret', 'timeout', 'retry', 'endpoint'],
            'min_match': 2,
        },
        'logging_config': {
            'keys': ['level', 'format', 'handler', 'file', 'console', 'log_level'],
            'min_match': 2,
        },
        'cache_config': {
            'keys': ['backend', 'ttl', 'timeout', 'max_size', 'redis', 'memcached'],
            'min_match': 2,
        },
        'email_config': {
            'keys': ['smtp_host', 'smtp_port', 'email', 'from_email', 'mail_server'],
            'min_match': 2,
        },
        'auth_config': {
            'keys': ['secret_key', 'jwt_secret', 'token', 'oauth', 'authentication'],
            'min_match': 1,
        },
        'server_config': {
            'keys': ['host', 'port', 'bind', 'workers', 'threads'],
            'min_match': 2,
        },
    }

    def detect_patterns(self, config_file: ConfigFile) -> List[str]:
        """
        Detect which patterns this config file matches.

        Args:
            config_file: ConfigFile with settings extracted

        Returns:
            List of detected pattern names
        """
        detected = []

        # Get all keys from settings (lowercase for matching)
        setting_keys = {s.key.lower() for s in config_file.settings}

        # Check against each known pattern
        for pattern_name, pattern_def in self.KNOWN_PATTERNS.items():
            pattern_keys = {k.lower() for k in pattern_def['keys']}
            min_match = pattern_def['min_match']

            # Count matches
            matches = len(setting_keys & pattern_keys)

            if matches >= min_match:
                detected.append(pattern_name)
                logger.debug(f"Detected {pattern_name} in {config_file.relative_path} ({matches} matches)")

        return detected


class ConfigExtractor:
    """Main configuration extraction orchestrator"""

    def __init__(self):
        self.detector = ConfigFileDetector()
        self.parser = ConfigParser()
        self.pattern_detector = ConfigPatternDetector()

    def extract_from_directory(
        self,
        directory: Path,
        max_files: int = 100
    ) -> ConfigExtractionResult:
        """
        Extract configuration patterns from directory.

        Args:
            directory: Root directory to analyze
            max_files: Maximum config files to process

        Returns:
            ConfigExtractionResult with all findings
        """
        result = ConfigExtractionResult()

        logger.info(f"Extracting configuration patterns from: {directory}")

        # Step 1: Find config files
        config_files = self.detector.find_config_files(directory, max_files)
        result.total_files = len(config_files)

        if not config_files:
            logger.warning("No configuration files found")
            return result

        # Step 2: Parse each config file
        for config_file in config_files:
            try:
                parsed = self.parser.parse_config_file(config_file)

                # Step 3: Detect patterns
                patterns = self.pattern_detector.detect_patterns(parsed)
                parsed.patterns = patterns

                # Track patterns
                for pattern in patterns:
                    if pattern not in result.detected_patterns:
                        result.detected_patterns[pattern] = []
                    result.detected_patterns[pattern].append(parsed.relative_path)

                result.config_files.append(parsed)
                result.total_settings += len(parsed.settings)

            except Exception as e:
                error_msg = f"Error processing {config_file.relative_path}: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(f"Extracted {result.total_settings} settings from {result.total_files} config files")
        logger.info(f"Detected patterns: {list(result.detected_patterns.keys())}")

        return result

    def to_dict(self, result: ConfigExtractionResult) -> Dict:
        """Convert result to dictionary for JSON output"""
        return {
            'total_files': result.total_files,
            'total_settings': result.total_settings,
            'detected_patterns': result.detected_patterns,
            'config_files': [
                {
                    'file_path': cf.file_path,
                    'relative_path': cf.relative_path,
                    'type': cf.config_type,
                    'purpose': cf.purpose,
                    'patterns': cf.patterns,
                    'settings_count': len(cf.settings),
                    'settings': [
                        {
                            'key': s.key,
                            'value': s.value,
                            'type': s.value_type,
                            'env_var': s.env_var,
                            'description': s.description,
                        }
                        for s in cf.settings
                    ],
                    'parse_errors': cf.parse_errors,
                }
                for cf in result.config_files
            ],
            'errors': result.errors,
        }


def main():
    """CLI entry point for config extraction"""
    import argparse

    parser = argparse.ArgumentParser(description="Extract configuration patterns from codebase with optional AI enhancement")
    parser.add_argument('directory', type=Path, help='Directory to analyze')
    parser.add_argument('--output', '-o', type=Path, help='Output JSON file')
    parser.add_argument('--max-files', type=int, default=100, help='Maximum config files to process')
    parser.add_argument('--enhance', action='store_true', help='Enhance with AI analysis (API mode, requires ANTHROPIC_API_KEY)')
    parser.add_argument('--enhance-local', action='store_true', help='Enhance with AI analysis (LOCAL mode, uses Claude Code CLI)')
    parser.add_argument('--ai-mode', choices=['auto', 'api', 'local', 'none'], default='none',
                        help='AI enhancement mode: auto (detect), api (Claude API), local (Claude Code CLI), none (disable)')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Extract
    extractor = ConfigExtractor()
    result = extractor.extract_from_directory(args.directory, args.max_files)

    # Convert to dict
    output_dict = extractor.to_dict(result)

    # AI Enhancement (if requested)
    enhance_mode = args.ai_mode
    if args.enhance:
        enhance_mode = 'api'
    elif args.enhance_local:
        enhance_mode = 'local'

    if enhance_mode != 'none':
        try:
            from skill_seekers.cli.config_enhancer import ConfigEnhancer
            logger.info(f"🤖 Starting AI enhancement (mode: {enhance_mode})...")
            enhancer = ConfigEnhancer(mode=enhance_mode)
            output_dict = enhancer.enhance_config_result(output_dict)
            logger.info("✅ AI enhancement complete")
        except ImportError:
            logger.warning("⚠️  ConfigEnhancer not available, skipping enhancement")
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_dict, f, indent=2)
        print(f"✅ Saved config extraction results to: {args.output}")
    else:
        print(json.dumps(output_dict, indent=2))

    # Summary
    print(f"\n📊 Summary:")
    print(f"  Config files found: {result.total_files}")
    print(f"  Total settings: {result.total_settings}")
    print(f"  Detected patterns: {', '.join(result.detected_patterns.keys()) or 'None'}")

    if 'ai_enhancements' in output_dict:
        print(f"  ✨ AI enhancements: Yes ({enhance_mode} mode)")
        insights = output_dict['ai_enhancements'].get('overall_insights', {})
        if insights.get('security_issues_found'):
            print(f"  🔐 Security issues found: {insights['security_issues_found']}")

    if result.errors:
        print(f"\n⚠️  Errors: {len(result.errors)}")


if __name__ == '__main__':
    main()
