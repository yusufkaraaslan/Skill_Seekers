#!/usr/bin/env python3
"""
Repository Context Analyzer for Smart Agent Generation

Phase 1 Implementation: Context-aware repository analysis
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TechnologyType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    MOBILE = "mobile"
    AI_ML = "ai_ml"


@dataclass
class TechStack:
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    build_tools: List[str]
    testing_frameworks: List[str]
    package_managers: List[str]
    cloud_platforms: List[str]


@dataclass
class CodePatterns:
    architectural_patterns: List[str]
    design_patterns: List[str]
    organization_structure: str
    development_methodology: str
    complexity_score: int
    maintainability_index: int


@dataclass
class SecurityAssessment:
    has_security_files: bool
    security_files: List[str]
    compliance_frameworks: List[str]
    vulnerability_tools: List[str]
    security_score: int


@dataclass
class QualityMetrics:
    test_coverage_score: int
    documentation_quality: int
    code_complexity: int
    error_handling_quality: int
    performance_score: int


@dataclass
class UserResponses:
    """User responses to generated questions."""
    responses: Dict[str, List[str]] = field(default_factory=dict)
    mode: str = "smart"
    specialization: Optional[str] = None
    template_preference: Optional[str] = None


@dataclass
class RepositoryContext:
    path: str
    name: str
    tech_stack: TechStack
    code_patterns: CodePatterns
    security_assessment: SecurityAssessment
    quality_metrics: QualityMetrics
    total_files: int
    dominant_language: str


class RepositoryContextAnalyzer:
    """Analyzes repository context for intelligent agent generation"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.context_cache = {}

        # Technology detection patterns
        self.framework_patterns = {
            TechnologyType.FRONTEND: {
                'react': r'react|jsx|tsx|\.react\.|create-react-app',
                'vue': r'vue|vuex|\.vue$|vue\.config',
                'angular': r'angular|@angular|\.component\.|\.service\.',
                'svelte': r'svelte|\.svelte$',
                'nextjs': r'next\.js|next\.config',
                'nuxt': r'nuxt|nuxt\.config',
            },
            TechnologyType.BACKEND: {
                'django': r'django|settings\.py|views\.py|models\.py',
                'flask': r'flask|@flask|app\.route',
                'express': r'express|@express|app\.use|app\.get',
                'fastapi': r'fastapi|@fastapi|app\.get|app\.post',
                'spring': r'spring|@spring|@controller|@service',
                'rails': r'rails|routes\.rb|application_controller',
            },
            TechnologyType.DATABASE: {
                'postgresql': r'postgres|postgresql|psycopg',
                'mysql': r'mysql|pymysql|mysql2',
                'mongodb': r'mongodb|pymongo|mongoose',
                'redis': r'redis|predis|redis-py',
                'sqlite': r'sqlite|sqlite3',
            },
            TechnologyType.DEVOPS: {
                'docker': r'docker|dockerfile|docker\-compose',
                'kubernetes': r'kubernetes|k8s|deployment\.yaml',
                'terraform': r'terraform|\.tf$',
                'github_actions': r'\.github/workflows',
                'jenkins': r'jenkinsfile|jenkins',
            },
            TechnologyType.SECURITY: {
                'oauth': r'oauth|jwt|auth0',
                'ssl': r'ssl|tls|https',
                'encryption': r'encrypt|bcrypt|hashlib',
                'security_headers': r'csp|x-frame|security',
            },
            TechnologyType.TESTING: {
                'jest': r'jest|\.test\.|\.spec\.|describe\(',
                'pytest': r'pytest|test_|conftest\.py',
                'cypress': r'cypress|\.cy\.|describe\(',
                'selenium': r'selenium|webdriver',
                'junit': r'junit|@test|testng',
            }
        }

    def analyze(self) -> RepositoryContext:
        """Perform comprehensive repository context analysis"""
        print(f"🔍 Analyzing repository: {self.repo_path}")

        # Analyze technology stack
        tech_stack = self._analyze_technology_stack()

        # Analyze code patterns
        code_patterns = self._analyze_code_patterns()

        # Assess security posture
        security_assessment = self._assess_security()

        # Evaluate quality metrics
        quality_metrics = self._evaluate_quality()

        # Get repository metadata
        repo_name = self.repo_path.name
        total_files = self._count_files()
        dominant_language = self._get_dominant_language()

        context = RepositoryContext(
            path=str(self.repo_path),
            name=repo_name,
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=total_files,
            dominant_language=dominant_language
        )

        print(f"✅ Analysis complete: {len(tech_stack.frameworks)} frameworks, "
              f"{len(tech_stack.languages)} languages detected")

        return context

    def _analyze_technology_stack(self) -> TechStack:
        """Detect technology stack from repository files"""
        languages = set()
        frameworks = set()
        databases = set()
        build_tools = set()
        testing_frameworks = set()
        package_managers = set()
        cloud_platforms = set()

        # Analyze file extensions and common patterns
        for file_path in self._walk_repository():
            file_ext = file_path.suffix.lower()
            file_name = file_path.name.lower()

            # Language detection
            if file_ext in ['.py', '.pyw']:
                languages.add('Python')
            elif file_ext in ['.js', '.jsx', '.mjs']:
                languages.add('JavaScript')
            elif file_ext in ['.ts', '.tsx']:
                languages.add('TypeScript')
            elif file_ext in ['.java']:
                languages.add('Java')
            elif file_ext in ['.go']:
                languages.add('Go')
            elif file_ext in ['.rs']:
                languages.add('Rust')
            elif file_ext in ['.cpp', '.cc', '.cxx']:
                languages.add('C++')
            elif file_ext in ['.c']:
                languages.add('C')
            elif file_ext in ['.cs']:
                languages.add('C#')
            elif file_ext in ['.rb']:
                languages.add('Ruby')
            elif file_ext in ['.php']:
                languages.add('PHP')
            elif file_ext in ['.swift']:
                languages.add('Swift')
            elif file_ext in ['.kt']:
                languages.add('Kotlin')

            # Framework and tool detection
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()

                    # Detect frameworks
                    for tech_type, patterns in self.framework_patterns.items():
                        for framework, pattern in patterns.items():
                            if re.search(pattern, content, re.IGNORECASE):
                                frameworks.add(framework)

                                # Add to specific categories
                                if tech_type == TechnologyType.FRONTEND:
                                    pass  # Already in frameworks
                                elif tech_type == TechnologyType.BACKEND:
                                    pass
                                elif tech_type == TechnologyType.DATABASE:
                                    databases.add(framework)
                                elif tech_type == TechnologyType.DEVOPS:
                                    build_tools.add(framework)
                                elif tech_type == TechnologyType.SECURITY:
                                    # Security tools tracked separately
                                    pass
                                elif tech_type == TechnologyType.TESTING:
                                    testing_frameworks.add(framework)

                    # Detect package managers
                    if re.search(r'pip install|pipenv|poetry', content):
                        package_managers.add('pip')
                    if re.search(r'npm install|yarn install', content):
                        package_managers.add('npm')
                    if re.search(r'maven|gradle', content):
                        package_managers.add('maven')
                    if re.search(r'go mod', content):
                        package_managers.add('go mod')

                    # Detect cloud platforms
                    if re.search(r'aws|amazon', content):
                        cloud_platforms.add('AWS')
                    if re.search(r'gcp|google cloud', content):
                        cloud_platforms.add('GCP')
                    if re.search(r'azure|microsoft', content):
                        cloud_platforms.add('Azure')

            except Exception as e:
                continue  # Skip files that can't be read

        # Check for configuration files
        config_files = [
            ('package.json', 'npm'),
            ('requirements.txt', 'pip'),
            ('Pipfile', 'pipenv'),
            ('poetry.lock', 'poetry'),
            ('Gemfile', 'bundler'),
            ('pom.xml', 'maven'),
            ('build.gradle', 'gradle'),
            ('go.mod', 'go mod'),
            ('Cargo.toml', 'cargo'),
        ]

        for config_file, manager in config_files:
            if (self.repo_path / config_file).exists():
                package_managers.add(manager)

        # Check for Docker and DevOps files
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore']
        for docker_file in docker_files:
            if (self.repo_path / docker_file).exists():
                build_tools.add('docker')

        # Check for GitHub Actions
        if (self.repo_path / '.github' / 'workflows').exists():
            build_tools.add('github_actions')

        return TechStack(
            languages=list(languages),
            frameworks=list(frameworks),
            databases=list(databases),
            build_tools=list(build_tools),
            testing_frameworks=list(testing_frameworks),
            package_managers=list(package_managers),
            cloud_platforms=list(cloud_platforms)
        )

    def _analyze_code_patterns(self) -> CodePatterns:
        """Analyze code organization and design patterns"""
        architectural_patterns = []
        design_patterns = []
        complexity_score = 5  # Default medium complexity
        maintainability_index = 70  # Default good maintainability

        # Check for architectural patterns
        if (self.repo_path / 'src').exists():
            organization_structure = "src-based"
        elif (self.repo_path / 'lib').exists():
            organization_structure = "lib-based"
        elif (self.repo_path / 'app').exists():
            organization_structure = "app-based"
        else:
            organization_structure = "flat"

        # Look for common patterns in code files
        mvc_pattern = False
        microservices_pattern = False
        repository_pattern = False

        for file_path in self._walk_repository():
            if file_path.suffix in ['.py', '.js', '.ts', '.java']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()

                        # MVC pattern
                        if re.search(r'controller|model|view', content):
                            mvc_pattern = True

                        # Microservices pattern
                        if re.search(r'service|microservice|api.*gateway', content):
                            microservices_pattern = True

                        # Repository pattern
                        if re.search(r'repository.*pattern|repository.*class', content):
                            repository_pattern = True

                        # Design patterns
                        if re.search(r'factory.*method|abstract.*factory', content):
                            design_patterns.append('Factory')
                        if re.search(r'singleton.*pattern|singleton.*class', content):
                            design_patterns.append('Singleton')
                        if re.search(r'observer.*pattern|observer.*class', content):
                            design_patterns.append('Observer')
                        if re.search(r'strategy.*pattern|strategy.*class', content):
                            design_patterns.append('Strategy')

                except Exception:
                    continue

        if mvc_pattern:
            architectural_patterns.append('MVC')
        if microservices_pattern:
            architectural_patterns.append('Microservices')
        if repository_pattern:
            architectural_patterns.append('Repository')

        # Estimate complexity based on file count and directory depth
        total_files = self._count_files()
        max_depth = self._get_max_directory_depth()

        if total_files > 100 or max_depth > 5:
            complexity_score = min(10, complexity_score + 3)
        elif total_files > 50 or (max_depth > 3 and total_files > 1):
            complexity_score = min(10, complexity_score + 1)

        # Adjust maintainability based on patterns
        if len(design_patterns) > 0:
            maintainability_index = min(100, maintainability_index + 5)
        if organization_structure == "flat" and total_files > 20:
            maintainability_index = max(0, maintainability_index - 10)

        # Detect development methodology
        development_methodology = "Unknown"
        if (self.repo_path / '.github' / 'workflows').exists():
            development_methodology = "DevOps"
        elif (self.repo_path / 'tests').exists() or (self.repo_path / 'test').exists():
            development_methodology = "Agile"
        elif (self.repo_path / 'docs').exists():
            development_methodology = "Documentation-First"

        return CodePatterns(
            architectural_patterns=list(set(architectural_patterns)),
            design_patterns=list(set(design_patterns)),
            organization_structure=organization_structure,
            development_methodology=development_methodology,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index
        )

    def _assess_security(self) -> SecurityAssessment:
        """Assess security posture and tools"""
        security_files = []
        compliance_frameworks = []
        vulnerability_tools = []

        # Look for security-related files (case-insensitive)
        security_file_patterns = [
            '*security*.md',
            '*security*.txt',
            '.security',
            '*vulnerabilities*.md',
            '*compliance*.md',
            '*privacy*.md',
            '*security-policy*.md',
            '.snyk',
            'bandit.yaml',
            'bandit.yml',
            '*bandit*.yaml',
            '*bandit*.yml'
        ]

        for pattern in security_file_patterns:
            for file_path in self.repo_path.rglob(pattern):
                if file_path.is_file():
                    security_files.append(str(file_path.relative_to(self.repo_path)))

        # Additional case-insensitive search for security files
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file():
                file_name_lower = file_path.name.lower()
                if any(keyword in file_name_lower for keyword in [
                    'security', 'vulnerability', 'compliance', 'privacy', 'auth', 'ssl', 'encryption'
                ]):
                    if file_name_lower.endswith(('.md', '.txt', '.rst', '.adoc')):
                        security_files.append(str(file_path.relative_to(self.repo_path)))
                        break  # Avoid duplicates

        # Check for common security tools
        security_tool_files = [
            ('.bandit', 'Bandit'),
            ('.snyk', 'Snyk'),
            ('sonar-project.properties', 'SonarQube'),
            ('.trivy.yml', 'Trivy'),
            ('dependabot.yml', 'Dependabot'),
            ('security_scan.yml', 'Custom Security Scan')
        ]

        for file_pattern, tool_name in security_tool_files:
            if (self.repo_path / file_pattern).exists():
                vulnerability_tools.append(tool_name)

        # Look for compliance frameworks in code
        compliance_keywords = ['gdpr', 'hipaa', 'pci', 'sox', 'iso27001']

        for file_path in self._walk_repository():
            if file_path.suffix in ['.md', '.txt', '.py', '.js', '.ts']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for keyword in compliance_keywords:
                            if keyword in content:
                                compliance_frameworks.append(keyword.upper())
                except Exception:
                    continue

        # Calculate security score
        security_score = 5  # Default medium security
        if len(security_files) > 0:
            security_score += 2
        if len(vulnerability_tools) > 0:
            security_score += 2
        if len(compliance_frameworks) > 0:
            security_score += 1

        return SecurityAssessment(
            has_security_files=len(security_files) > 0,
            security_files=security_files,
            compliance_frameworks=list(set(compliance_frameworks)),
            vulnerability_tools=vulnerability_tools,
            security_score=min(10, security_score)
        )

    def _evaluate_quality(self) -> QualityMetrics:
        """Evaluate code quality metrics"""
        test_coverage_score = 0
        documentation_quality = 0
        code_complexity = 5
        error_handling_quality = 5
        performance_score = 5

        # Test coverage estimation
        test_files = list(self.repo_path.rglob('test_*')) + list(self.repo_path.rglob('*_test.*'))
        test_files += list(self.repo_path.rglob('*.test.*')) + list(self.repo_path.rglob('*.spec.*'))

        total_code_files = len([f for f in self._walk_repository()
                              if f.suffix in ['.py', '.js', '.ts', '.java', '.go']])

        if total_code_files > 0:
            test_ratio = len(test_files) / total_code_files
            test_coverage_score = min(10, int(test_ratio * 20))

        # Documentation quality
        doc_files = list(self.repo_path.rglob('*.md')) + list(self.repo_path.rglob('*.rst'))
        doc_files += list(self.repo_path.rglob('docs/**/*'))

        readme_exists = (self.repo_path / 'README.md').exists()
        if readme_exists:
            documentation_quality += 3

        if len(doc_files) > 5:
            documentation_quality += 2
        elif len(doc_files) > 2:
            documentation_quality += 1

        # Code complexity (simplified)
        max_depth = self._get_max_directory_depth()
        total_files = self._count_files()

        if total_files > 200:
            code_complexity = min(10, code_complexity + 3)
        elif total_files > 100:
            code_complexity = min(10, code_complexity + 1)

        if max_depth > 6:
            code_complexity = min(10, code_complexity + 2)
        elif max_depth > 4:
            code_complexity = min(10, code_complexity + 1)

        # Error handling quality
        error_patterns = ['try:', 'catch', 'except', 'throw', 'raise', 'error']
        error_handling_count = 0

        for file_path in self._walk_repository():
            if file_path.suffix in ['.py', '.js', '.ts', '.java']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for pattern in error_patterns:
                            error_handling_count += content.count(pattern)
                except Exception:
                    continue

        if total_code_files > 0:
            error_ratio = error_handling_count / total_code_files
            error_handling_quality = min(10, int(error_ratio * 10))

        return QualityMetrics(
            test_coverage_score=test_coverage_score,
            documentation_quality=min(10, documentation_quality),
            code_complexity=code_complexity,
            error_handling_quality=error_handling_quality,
            performance_score=performance_score
        )

    def _walk_repository(self):
        """Walk through repository files"""
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}

        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and not any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                if file_path.suffix and file_path.name[0] != '.':
                    yield file_path

    def _count_files(self) -> int:
        """Count total code files"""
        return len(list(self._walk_repository()))

    def _get_dominant_language(self) -> str:
        """Get the dominant programming language"""
        language_counts = {}

        for file_path in self._walk_repository():
            ext = file_path.suffix.lower()
            if ext in ['.py']: language_counts['Python'] = language_counts.get('Python', 0) + 1
            elif ext in ['.js', '.jsx']: language_counts['JavaScript'] = language_counts.get('JavaScript', 0) + 1
            elif ext in ['.ts', '.tsx']: language_counts['TypeScript'] = language_counts.get('TypeScript', 0) + 1
            elif ext in ['.java']: language_counts['Java'] = language_counts.get('Java', 0) + 1
            elif ext in ['.go']: language_counts['Go'] = language_counts.get('Go', 0) + 1
            elif ext in ['.rs']: language_counts['Rust'] = language_counts.get('Rust', 0) + 1
            elif ext in ['.cpp', '.cc']: language_counts['C++'] = language_counts.get('C++', 0) + 1
            elif ext in ['.c']: language_counts['C'] = language_counts.get('C', 0) + 1
            elif ext in ['.cs']: language_counts['C#'] = language_counts.get('C#', 0) + 1
            elif ext in ['.rb']: language_counts['Ruby'] = language_counts.get('Ruby', 0) + 1
            elif ext in ['.php']: language_counts['PHP'] = language_counts.get('PHP', 0) + 1

        return max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else 'Unknown'

    def _get_max_directory_depth(self) -> int:
        """Get maximum directory depth"""
        max_depth = 0
        for file_path in self.repo_path.rglob('*'):
            depth = len(file_path.relative_to(self.repo_path).parts)
            max_depth = max(max_depth, depth)
        return max_depth


def main():
    """Command-line interface for context analysis"""
    import sys

    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = "."

    analyzer = RepositoryContextAnalyzer(repo_path)
    context = analyzer.analyze()

    # Output JSON for easy parsing
    print(json.dumps({
        'repository': {
            'name': context.name,
            'path': context.path,
            'total_files': context.total_files,
            'dominant_language': context.dominant_language
        },
        'tech_stack': {
            'languages': context.tech_stack.languages,
            'frameworks': context.tech_stack.frameworks,
            'databases': context.tech_stack.databases,
            'build_tools': context.tech_stack.build_tools,
            'testing_frameworks': context.tech_stack.testing_frameworks,
            'package_managers': context.tech_stack.package_managers,
            'cloud_platforms': context.tech_stack.cloud_platforms
        },
        'code_patterns': {
            'architectural_patterns': context.code_patterns.architectural_patterns,
            'design_patterns': context.code_patterns.design_patterns,
            'organization_structure': context.code_patterns.organization_structure,
            'development_methodology': context.code_patterns.development_methodology,
            'complexity_score': context.code_patterns.complexity_score,
            'maintainability_index': context.code_patterns.maintainability_index
        },
        'security_assessment': {
            'has_security_files': context.security_assessment.has_security_files,
            'security_files': context.security_assessment.security_files,
            'compliance_frameworks': context.security_assessment.compliance_frameworks,
            'vulnerability_tools': context.security_assessment.vulnerability_tools,
            'security_score': context.security_assessment.security_score
        },
        'quality_metrics': {
            'test_coverage_score': context.quality_metrics.test_coverage_score,
            'documentation_quality': context.quality_metrics.documentation_quality,
            'code_complexity': context.quality_metrics.code_complexity,
            'error_handling_quality': context.quality_metrics.error_handling_quality,
            'performance_score': context.quality_metrics.performance_score
        }
    }, indent=2))


if __name__ == "__main__":
    main()