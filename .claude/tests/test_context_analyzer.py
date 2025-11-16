"""
Test suite for Repository Context Analyzer using TDD methodology.

These tests define the expected behavior of the context analyzer before implementation.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from context_analyzer import (
    RepositoryContextAnalyzer,
    RepositoryContext,
    TechStack,
    CodePatterns,
    SecurityAssessment,
    QualityMetrics
)


class TestRepositoryContextAnalyzer:
    """Test suite for RepositoryContextAnalyzer class."""

    @pytest.fixture
    def python_project_dir(self, temp_project_dir: Path) -> Path:
        """Create a sample Python project structure."""
        # Create Python project structure
        (temp_project_dir / "src").mkdir(parents=True)
        (temp_project_dir / "tests").mkdir(parents=True)
        (temp_project_dir / "docs").mkdir(parents=True)

        # Create Python files
        (temp_project_dir / "src" / "main.py").write_text("""
import flask
from flask import Flask
import requests
import pandas as pd

app = Flask(__name__)

class UserController:
    def __init__(self):
        self.db_connection = None

    def get_user(self, user_id: int):
        try:
            # Query database for user
            return {"id": user_id, "name": "Test User"}
        except Exception as e:
            raise ValueError(f"User not found: {e}")

    def create_user(self, user_data: dict):
        # Create new user
        pass

@app.route('/users/<int:user_id>')
def get_user_endpoint(user_id: int):
    controller = UserController()
    return controller.get_user(user_id)

if __name__ == '__main__':
    app.run(debug=True)
        """)

        (temp_project_dir / "src" / "utils.py").write_text("""
import logging
import hashlib
import jwt
from typing import Optional

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id: int) -> str:
    return jwt.encode({"user_id": user_id}, "secret", algorithm="HS256")

def validate_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, "secret", algorithms=["HS256"])
    except:
        return None
        """)

        (temp_project_dir / "tests" / "test_main.py").write_text("""
import unittest
from src.main import app

class TestMain(unittest.TestCase):
    def test_user_endpoint(self):
        with app.test_client() as client:
            response = client.get('/users/1')
            self.assertEqual(response.status_code, 200)

    def test_user_not_found(self):
        with app.test_client() as client:
            response = client.get('/users/999')
            self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
        """)

        # Create configuration files
        (temp_project_dir / "requirements.txt").write_text("""
flask==2.0.1
requests==2.25.1
pandas==1.3.0
pytest==6.2.4
        """)

        (temp_project_dir / "README.md").write_text("""
# Python Web Application

A sample Flask application with user management.

## Features

- User authentication
- REST API endpoints
- Database integration

## Installation

```bash
pip install -r requirements.txt
python src/main.py
```
        """)

        # Create security-related files
        (temp_project_dir / "SECURITY.md").write_text("""
# Security Policy

This document outlines our security practices.

## Vulnerability Reporting

Please report security vulnerabilities to security@example.com
        """)

        # Create Docker configuration
        (temp_project_dir / "Dockerfile").write_text("""
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/

CMD ["python", "src/main.py"]
        """)

        # Create GitHub Actions workflow
        github_dir = temp_project_dir / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "ci.yml").write_text("""
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: python -m pytest tests/
        """)

        return temp_project_dir

    @pytest.fixture
    def javascript_project_dir(self, temp_project_dir: Path) -> Path:
        """Create a sample JavaScript/React project structure."""
        # Create React project structure
        (temp_project_dir / "src").mkdir(parents=True)
        (temp_project_dir / "public").mkdir(parents=True)
        (temp_project_dir / "components").mkdir(parents=True)

        # Create React components
        (temp_project_dir / "src" / "App.js").write_text("""
import React, { useState, useEffect } from 'react';
import UserList from './components/UserList';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/users');
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>User Management System</h1>
      </header>
      <main>
        {loading ? (
          <div>Loading...</div>
        ) : (
          <UserList users={users} />
        )}
      </main>
    </div>
  );
}

export default App;
        """)

        (temp_project_dir / "components" / "UserList.js").write_text("""
import React from 'react';

const UserList = ({ users }) => {
  return (
    <div className="user-list">
      <h2>Users</h2>
      {users.map(user => (
        <div key={user.id} className="user-item">
          <h3>{user.name}</h3>
          <p>{user.email}</p>
        </div>
      ))}
    </div>
  );
};

export default UserList;
        """)

        # Create package.json
        (temp_project_dir / "package.json").write_text(json.dumps({
            "name": "react-user-management",
            "version": "1.0.0",
            "dependencies": {
                "react": "^17.0.2",
                "react-dom": "^17.0.2",
                "axios": "^0.21.1"
            },
            "devDependencies": {
                "jest": "^26.6.0",
                "@testing-library/react": "^11.2.0",
                "eslint": "^7.2.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "test": "jest",
                "lint": "eslint src/"
            }
        }, indent=2))

        # Create test files
        (temp_project_dir / "App.test.js").write_text("""
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  expect(screen.getByText(/User Management System/i)).toBeInTheDocument();
});
        """)

        return temp_project_dir

    @pytest.fixture
    def security_focused_project_dir(self, temp_project_dir: Path) -> Path:
        """Create a project with strong security focus."""
        (temp_project_dir / "src").mkdir(parents=True)
        (temp_project_dir / "security").mkdir(parents=True)

        # Create security-focused code
        (temp_project_dir / "src" / "auth.py").write_text("""
import bcrypt
import jwt
import ssl
from cryptography.fernet import Fernet

class SecurityManager:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    def generate_jwt(self, user_id: int, expires_in: int = 3600) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')

    def encrypt_data(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        """)

        # Create security files
        (temp_project_dir / "SECURITY_POLICY.md").write_text("""
# Security Policy

## Authentication and Authorization

- All API endpoints require authentication
- JWT tokens expire after 1 hour
- Password hashing with bcrypt
- Data encryption at rest and in transit

## Compliance

- GDPR compliance for user data
- Regular security audits
- Vulnerability scanning with Snyk
        """)

        (temp_project_dir / ".snyk").write_text("")
        (temp_project_dir / "bandit.yaml").write_text("""
targets:
  - src/**/*.py
exclude_dirs:
  - tests
        """)

        return temp_project_dir

    @pytest.fixture
    def empty_project_dir(self, temp_project_dir: Path) -> Path:
        """Create a minimal project with basic structure."""
        (temp_project_dir / "main.py").write_text("print('Hello, World!')")
        return temp_project_dir

    def test_analyze_python_project(self, python_project_dir: Path):
        """Test analysis of a Python project with Flask."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        # Verify basic repository info
        assert context.name == python_project_dir.name
        assert context.total_files > 0
        assert context.dominant_language == "Python"

        # Verify technology stack detection
        assert "Python" in context.tech_stack.languages
        assert "flask" in context.tech_stack.frameworks
        assert "pip" in context.tech_stack.package_managers

        # Verify testing framework detection
        assert "pytest" in context.tech_stack.testing_frameworks

        # Verify security assessment
        assert context.security_assessment.has_security_files
        assert "SECURITY.md" in str(context.security_assessment.security_files)
        assert context.security_assessment.security_score > 5

    def test_analyze_javascript_project(self, javascript_project_dir: Path):
        """Test analysis of a JavaScript/React project."""
        analyzer = RepositoryContextAnalyzer(str(javascript_project_dir))
        context = analyzer.analyze()

        # Verify basic repository info
        assert context.name == javascript_project_dir.name
        assert context.dominant_language == "JavaScript"

        # Verify technology stack detection
        assert "JavaScript" in context.tech_stack.languages
        assert "react" in context.tech_stack.frameworks
        assert "npm" in context.tech_stack.package_managers
        assert "jest" in context.tech_stack.testing_frameworks

    def test_analyze_security_focused_project(self, security_focused_project_dir: Path):
        """Test analysis of security-focused project."""
        analyzer = RepositoryContextAnalyzer(str(security_focused_project_dir))
        context = analyzer.analyze()

        # Verify security assessment
        assert context.security_assessment.has_security_files
        assert len(context.security_assessment.security_files) >= 2
        assert "Snyk" in context.security_assessment.vulnerability_tools
        assert context.security_assessment.security_score >= 7

    def test_analyze_empty_project(self, empty_project_dir: Path):
        """Test analysis of minimal project."""
        analyzer = RepositoryContextAnalyzer(str(empty_project_dir))
        context = analyzer.analyze()

        # Verify basic detection works for minimal projects
        assert context.total_files == 1
        assert context.dominant_language == "Python"

        # Verify defaults for projects without specific patterns
        assert context.code_patterns.complexity_score == 5  # Default medium
        assert context.security_assessment.security_score == 5  # Default medium
        assert context.quality_metrics.test_coverage_score == 0  # No tests found

    def test_technology_stack_detection(self, python_project_dir: Path):
        """Test comprehensive technology stack detection."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        tech_stack = context.tech_stack

        # Should detect Python ecosystem
        assert "Python" in tech_stack.languages
        assert "flask" in tech_stack.frameworks

        # Should detect development tools
        assert "pip" in tech_stack.package_managers
        assert "pytest" in tech_stack.testing_frameworks

        # Should detect potential databases from imports
        # (This would require more sophisticated analysis)

    def test_code_patterns_analysis(self, python_project_dir: Path):
        """Test code pattern analysis."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        code_patterns = context.code_patterns

        # Should detect basic organization
        assert code_patterns.organization_structure in ["src-based", "lib-based", "app-based", "flat"]

        # Should detect development methodology
        assert code_patterns.development_methodology in ["DevOps", "Agile", "Documentation-First", "Unknown"]

        # Should have complexity score in valid range
        assert 1 <= code_patterns.complexity_score <= 10

        # Should have maintainability index in valid range
        assert 0 <= code_patterns.maintainability_index <= 100

    def test_security_assessment(self, python_project_dir: Path):
        """Test security posture assessment."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        security = context.security_assessment

        # Should detect security files
        if security.has_security_files:
            assert len(security.security_files) > 0
            assert security.security_score > 5

        # Should score in valid range
        assert 1 <= security.security_score <= 10

    def test_quality_metrics_evaluation(self, python_project_dir: Path):
        """Test quality metrics evaluation."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        quality = context.quality_metrics

        # Should have test coverage estimate
        assert 0 <= quality.test_coverage_score <= 10

        # Should have documentation quality estimate
        assert 0 <= quality.documentation_quality <= 10

        # Should have complexity assessment
        assert 1 <= quality.code_complexity <= 10

        # Should have error handling quality
        assert 0 <= quality.error_handling_quality <= 10

    def test_docker_detection(self, python_project_dir: Path):
        """Test Docker and DevOps tool detection."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        # Should detect Dockerfile
        if (python_project_dir / "Dockerfile").exists():
            assert any("docker" in tool.lower() for tool in context.tech_stack.build_tools)

        # Should detect GitHub Actions
        if (python_project_dir / ".github" / "workflows").exists():
            assert "github_actions" in " ".join(context.tech_stack.build_tools).lower()

    def test_framework_pattern_matching(self, python_project_dir: Path):
        """Test framework detection through pattern matching."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        # Should detect Flask patterns
        assert "flask" in context.tech_stack.frameworks
        assert len(context.tech_stack.frameworks) > 0

    def test_error_handling_in_file_reading(self, temp_project_dir: Path):
        """Test graceful handling of unreadable files."""
        # Create a file with invalid encoding
        bad_file = temp_project_dir / "bad_encoding.py"
        bad_file.write_bytes(b'\xff\xfe\x00\x00Invalid encoding')

        analyzer = RepositoryContextAnalyzer(str(temp_project_dir))

        # Should not crash when encountering unreadable files
        context = analyzer.analyze()
        assert context is not None
        assert isinstance(context, RepositoryContext)

    def test_context_analysis_output_format(self, python_project_dir: Path):
        """Test that context analysis returns properly structured data."""
        analyzer = RepositoryContextAnalyzer(str(python_project_dir))
        context = analyzer.analyze()

        # Verify all required attributes exist
        assert hasattr(context, 'path')
        assert hasattr(context, 'name')
        assert hasattr(context, 'tech_stack')
        assert hasattr(context, 'code_patterns')
        assert hasattr(context, 'security_assessment')
        assert hasattr(context, 'quality_metrics')
        assert hasattr(context, 'total_files')
        assert hasattr(context, 'dominant_language')

        # Verify tech_stack structure
        assert isinstance(context.tech_stack.languages, list)
        assert isinstance(context.tech_stack.frameworks, list)
        assert isinstance(context.tech_stack.package_managers, list)

    def test_multiple_language_project(self, temp_project_dir: Path):
        """Test analysis of project with multiple languages."""
        # Create project with Python and JavaScript files
        (temp_project_dir / "app.py").write_text("print('Python code')")
        (temp_project_dir / "script.js").write_text("console.log('JavaScript code')")

        analyzer = RepositoryContextAnalyzer(str(temp_project_dir))
        context = analyzer.analyze()

        # Should detect both languages
        assert "Python" in context.tech_stack.languages
        assert "JavaScript" in context.tech_stack.languages

        # Should have a dominant language
        assert context.dominant_language in ["Python", "JavaScript"]

    def test_large_project_performance(self, temp_project_dir: Path):
        """Test that analysis remains performant with larger projects."""
        # Create many files to simulate larger project
        for i in range(50):
            (temp_project_dir / f"module_{i}.py").write_text(f"# Module {i}\ndef func_{i}():\n    return {i}")

        analyzer = RepositoryContextAnalyzer(str(temp_project_dir))

        # Should complete analysis without issues
        context = analyzer.analyze()
        assert context.total_files >= 50
        assert context.dominant_language == "Python"


class TestTechStackDataclass:
    """Test suite for TechStack dataclass."""

    def test_tech_stack_creation(self):
        """Test TechStack dataclass creation and attributes."""
        tech_stack = TechStack(
            languages=["Python", "JavaScript"],
            frameworks=["Flask", "React"],
            databases=["PostgreSQL", "MongoDB"],
            build_tools=["Docker", "Webpack"],
            testing_frameworks=["pytest", "Jest"],
            package_managers=["pip", "npm"],
            cloud_platforms=["AWS", "GCP"]
        )

        assert tech_stack.languages == ["Python", "JavaScript"]
        assert tech_stack.frameworks == ["Flask", "React"]
        assert len(tech_stack.languages) == 2
        assert "Python" in tech_stack.languages


class TestRepositoryContextDataclass:
    """Test suite for RepositoryContext dataclass."""

    def test_repository_context_creation(self):
        """Test RepositoryContext dataclass creation."""
        tech_stack = TechStack([], [], [], [], [], [], [])
        code_patterns = CodePatterns([], [], "", "", 5, 70)
        security = SecurityAssessment(False, [], [], [], 5)
        quality = QualityMetrics(5, 5, 5, 5, 5)

        context = RepositoryContext(
            path="/test/path",
            name="test-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security,
            quality_metrics=quality,
            total_files=10,
            dominant_language="Python"
        )

        assert context.path == "/test/path"
        assert context.name == "test-project"
        assert context.total_files == 10
        assert context.dominant_language == "Python"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])