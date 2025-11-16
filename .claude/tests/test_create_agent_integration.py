#!/usr/bin/env python3
"""
TDD Phase 4: Integration Tests for /create-agent Command

This test suite follows Test-Driven Development principles.
Tests are written FIRST, then implementation is created to make them pass.

Integration tests verify the complete end-to-end functionality:
- Context analysis → Question generation → User responses → Agent generation → YAML output
- Different command modes (smart, fast, interactive)
- Error handling and edge cases
- File I/O operations for saving generated agents
"""

import pytest
import os
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Import all our TDD implementations
from context_analyzer import (
    RepositoryContextAnalyzer, RepositoryContext, UserResponses
)
from test_question_generator import SmartQuestionGenerator, Question
from test_agent_generator import (
    IntelligentAgentGenerator, AgentSpecification, AgentType
)


@dataclass
class CreateAgentConfig:
    """Configuration for /create-agent command."""
    mode: str = "smart"  # smart, fast, interactive
    context: str = "."  # Target directory or repository path
    specialization: Optional[str] = None
    template: Optional[AgentType] = None
    output_dir: str = ".claude/agents"
    auto_save: bool = True


class MockAskUserQuestion:
    """Mock implementation of AskUserQuestion for testing."""

    def __init__(self, predefined_responses: Optional[Dict[str, List[str]]] = None):
        self.predefined_responses = predefined_responses or {}
        self.call_history = []

    def __call__(self, questions, answers: Dict[str, str]):
        """Mock the AskUserQuestion tool call."""
        self.call_history.append(questions)

        # Return predefined responses
        responses = {}
        for question in questions:
            # Handle both Question objects and dict objects
            if hasattr(question, 'header'):
                header = question.header
                options = question.options
            else:
                header = question.get("header", "")
                options = question.get("options", [])

            if header in self.predefined_responses:
                responses[header] = self.predefined_responses[header]
            else:
                # Default to first option if no predefined response
                if options:
                    if hasattr(options[0], 'label'):
                        responses[header] = [options[0].label]
                    else:
                        responses[header] = [options[0]["label"]]

        return UserResponses(responses=responses)


class CreateAgentCommand:
    """Implementation of /create-agent command."""

    def __init__(self, config: CreateAgentConfig):
        self.config = config
        self.context_analyzer = RepositoryContextAnalyzer(config.context)
        self.question_generator = SmartQuestionGenerator()
        self.agent_generator = IntelligentAgentGenerator()

    def execute(self, user_question_tool=None) -> AgentSpecification:
        """
        Execute the complete create-agent workflow.

        Args:
            user_question_tool: Mock/real AskUserQuestion tool for testing

        Returns:
            Generated agent specification
        """
        # Phase 1: Repository Context Analysis
        try:
            context = self.context_analyzer.analyze()
        except Exception as e:
            # Fallback for context analysis failures
            context = self._create_fallback_context()

        # Phase 2: Question Generation based on mode
        if self.config.mode == "fast":
            user_responses = UserResponses(
                mode="fast",
                specialization=self.config.specialization,
                template_preference=self.config.template
            )
        elif self.config.mode == "interactive":
            # Would generate comprehensive questions in real implementation
            # For testing, we'll use smart mode with extended questioning
            questions = self.question_generator.generate_contextual_questions(context)
            if user_question_tool:
                user_responses = user_question_tool(questions, {})
            else:
                # Default responses for testing without user interaction
                user_responses = UserResponses(
                    responses=self._generate_default_responses(questions),
                    specialization=self.config.specialization,
                    template_preference=self.config.template
                )
        else:  # smart mode (default)
            questions = self.question_generator.generate_contextual_questions(context)
            if user_question_tool:
                user_responses = user_question_tool(questions, {})
            else:
                # Default responses for testing without user interaction
                user_responses = UserResponses(
                    responses=self._generate_default_responses(questions),
                    specialization=self.config.specialization,
                    template_preference=self.config.template
                )

        # Phase 3: Intelligent Agent Generation
        agent_spec = self.agent_generator.generate_agent_specification(context, user_responses)

        # Phase 4: Validation
        validation_errors = self.agent_generator.validate_agent_specification(agent_spec)
        if validation_errors:
            raise ValueError(f"Generated agent specification failed validation: {validation_errors}")

        # Phase 5: Save if auto_save is enabled
        if self.config.auto_save:
            self._save_agent_specification(agent_spec)

        return agent_spec

    def _create_fallback_context(self) -> RepositoryContext:
        """Create fallback context when analysis fails."""
        from context_analyzer import TechStack, CodePatterns, SecurityAssessment, QualityMetrics

        tech_stack = TechStack([], [], [], [], [], [], [])
        code_patterns = CodePatterns([], [], "flat", "Unknown", 5, 50)
        security_assessment = SecurityAssessment(False, [], [], [], 5)
        quality_metrics = QualityMetrics(0, 0, 5, 5, 5)

        return RepositoryContext(
            path=self.config.context,
            name=Path(self.config.context).name,
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=0,
            dominant_language="Unknown"
        )

    def _generate_default_responses(self, questions: List[Question]) -> Dict[str, List[str]]:
        """Generate default responses for questions when no user interaction available."""
        responses = {}
        for question in questions:
            if question.options:
                # Select first option by default
                responses[question.header] = [question.options[0]["label"]]
        return responses

    def _save_agent_specification(self, agent_spec: AgentSpecification) -> str:
        """Save agent specification to file."""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename from agent name
        filename = f"{agent_spec.name.lstrip('@')}.md"
        filepath = output_path / filename

        # Create full agent file content with YAML frontmatter
        content = f"""---
name: {agent_spec.name}
description: {agent_spec.description}
type: {agent_spec.type.value if hasattr(agent_spec.type, 'value') else str(agent_spec.type)}
framework: {agent_spec.framework.value if hasattr(agent_spec.framework, 'value') else str(agent_spec.framework)}
methodology: {agent_spec.methodology}
specialization: {agent_spec.specialization}
tools:
{self._format_tools_for_yaml(agent_spec.tools)}
delegation_network: {[f"@{target.value}" if hasattr(target, 'value') else f"@{target}" for target in agent_spec.delegation_network]}
capabilities: {agent_spec.capabilities}
usage_patterns: {agent_spec.usage_patterns}
---

# {agent_spec.name}

{agent_spec.description}

## Framework

{agent_spec.framework.value}: {agent_spec.methodology}

## Specialization

{agent_spec.specialization}

## Capabilities

{self._format_capabilities_for_markdown(agent_spec.capabilities)}

## Usage Patterns

{self._format_usage_patterns_for_markdown(agent_spec.usage_patterns)}

## Delegation Network

This agent can delegate to: {', '.join(f'@{target.value}' for target in agent_spec.delegation_network)}

---

*Generated by /create-agent command*
"""

        filepath.write_text(content)
        return str(filepath)

    def _format_tools_for_yaml(self, tools) -> str:
        """Format tools for YAML frontmatter."""
        tool_lines = []
        for tool in tools:
            tool_lines.append(f"  - name: {tool.name}")
            tool_lines.append(f"    description: {tool.description}")
            tool_lines.append(f"    category: {tool.category}")
        return '\n'.join(tool_lines)

    def _format_capabilities_for_markdown(self, capabilities: List[str]) -> str:
        """Format capabilities for markdown."""
        return '\n'.join(f"- {cap}" for cap in capabilities)

    def _format_usage_patterns_for_markdown(self, usage_patterns: List[str]) -> str:
        """Format usage patterns for markdown."""
        return '\n'.join(f"- {pattern}" for pattern in usage_patterns)


class TestCreateAgentIntegration:
    """Integration tests for /create-agent command using TDD methodology."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def python_project_dir(self, temp_project_dir):
        """Create a Python project for testing."""
        # Create project structure
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "tests").mkdir()
        (temp_project_dir / "docs").mkdir()

        # Create Python files
        (temp_project_dir / "src" / "app.py").write_text("""
from flask import Flask, request, jsonify
import bcrypt
import jwt

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'users': []})

@app.route('/api/auth', methods=['POST'])
def authenticate():
    # Security: Hash passwords with bcrypt
    password = request.json.get('password')
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return jsonify({'hashed': hashed.decode()})
""")

        (temp_project_dir / "src" / "utils.py").write_text("""
def utility_function():
    return "utility"
""")

        (temp_project_dir / "tests" / "test_app.py").write_text("""
import pytest
from src.app import app

def test_app_exists():
    assert app is not None
""")

        (temp_project_dir / "requirements.txt").write_text("""
flask==2.0.1
bcrypt==3.2.0
pyjwt==2.1.0
pytest==6.2.0
""")

        (temp_project_dir / "README.md").write_text("""
# Python Flask Project

This is a sample Flask application with authentication.
""")

        (temp_project_dir / "SECURITY.md").write_text("""
# Security Policy

- All passwords must be hashed
- Use JWT for authentication
- Input validation required
""")

        return temp_project_dir

    @pytest.fixture
    def output_dir(self, temp_project_dir):
        """Create output directory for agents."""
        output = temp_project_dir / ".claude" / "agents"
        output.mkdir(parents=True)
        return output

    @pytest.fixture
    def security_focused_responses(self):
        """Predefined responses for security-focused questions."""
        return {
            "Security Focus": ["Vulnerability Detection", "Compliance"],
            "Performance Focus": ["Code Quality"],
            "Documentation": ["API Documentation"]
        }

    @pytest.fixture
    def performance_focused_responses(self):
        """Predefined responses for performance-focused questions."""
        return {
            "Security Focus": ["DevSecOps Integration"],
            "Performance Focus": ["Performance", "Testing"],
            "Technology Focus": ["Framework Optimization"]
        }

    def test_smart_mode_complete_workflow(self, python_project_dir, output_dir, security_focused_responses):
        """Test complete smart mode workflow from start to finish."""
        config = CreateAgentConfig(
            mode="smart",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        mock_ask_user = MockAskUserQuestion(security_focused_responses)
        command = CreateAgentCommand(config)

        # Execute complete workflow
        agent_spec = command.execute(user_question_tool=mock_ask_user)

        # Verify agent specification
        assert isinstance(agent_spec, AgentSpecification)
        assert agent_spec.name
        assert agent_spec.description
        assert agent_spec.type in [AgentType.SECURITY, AgentType.SPECIALIST]

        # Verify YAML content is valid
        parsed_yaml = yaml.safe_load(agent_spec.yaml_content)
        assert isinstance(parsed_yaml, dict)
        assert "name" in parsed_yaml
        assert "tools" in parsed_yaml

        # Verify file was saved
        expected_file = output_dir / f"{agent_spec.name.lstrip('@')}.md"
        assert expected_file.exists()

        # Verify file content
        content = expected_file.read_text()
        assert agent_spec.name in content
        assert agent_spec.description in content
        assert "---" in content  # YAML frontmatter

    def test_fast_mode_workflow(self, python_project_dir, output_dir):
        """Test fast mode workflow with automated decisions."""
        config = CreateAgentConfig(
            mode="fast",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            specialization="Flask Development",
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Execute without user interaction
        agent_spec = command.execute()

        # Should generate valid agent specification
        assert isinstance(agent_spec, AgentSpecification)
        assert agent_spec.specialization == "Flask Development"

        # Should save agent file
        expected_file = output_dir / f"{agent_spec.name.lstrip('@')}.md"
        assert expected_file.exists()

    def test_interactive_mode_workflow(self, python_project_dir, output_dir, performance_focused_responses):
        """Test interactive mode workflow with extended questioning."""
        config = CreateAgentConfig(
            mode="interactive",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        mock_ask_user = MockAskUserQuestion(performance_focused_responses)
        command = CreateAgentCommand(config)

        # Execute with user interaction
        agent_spec = command.execute(user_question_tool=mock_ask_user)

        # Verify agent specification
        assert isinstance(agent_spec, AgentSpecification)
        assert agent_spec.name

        # Verify user questions were asked
        assert len(mock_ask_user.call_history) > 0

    def test_template_override_workflow(self, python_project_dir, output_dir):
        """Test workflow with explicit template preference."""
        config = CreateAgentConfig(
            mode="smart",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            template=AgentType.TEST,
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Execute with template override
        agent_spec = command.execute()

        # Should respect template preference
        assert agent_spec.type == AgentType.TEST

    def test_specialization_parameter_workflow(self, python_project_dir, output_dir):
        """Test workflow with specialization parameter."""
        config = CreateAgentConfig(
            mode="smart",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            specialization="API Security",
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Execute with specialization
        agent_spec = command.execute()

        # Should include specialization in agent
        assert "API Security" in agent_spec.specialization

    def test_error_handling_invalid_context(self, output_dir):
        """Test error handling for invalid context directory."""
        config = CreateAgentConfig(
            mode="smart",
            context="/nonexistent/directory",
            output_dir=str(output_dir),
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Should handle invalid context gracefully
        try:
            agent_spec = command.execute()
            # Should still generate agent with fallback context
            assert isinstance(agent_spec, AgentSpecification)
        except Exception as e:
            # Should not crash with unhandled exception
            assert "context" in str(e).lower() or "directory" in str(e).lower()

    def test_error_handling_validation_failure(self, python_project_dir, output_dir):
        """Test error handling for validation failures."""
        config = CreateAgentConfig(
            mode="smart",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Mock agent generator to return invalid specification
        with patch.object(command.agent_generator, 'generate_agent_specification') as mock_generate:
            invalid_spec = AgentSpecification(
                name="",  # Invalid empty name
                description="",
                type=AgentType.SPECIALIST,
                framework=None,  # Invalid framework
                tools=[],
                delegation_network=[],
                methodology="",
                specialization="",
                capabilities=[],
                usage_patterns=[],
                yaml_content=""
            )
            mock_generate.return_value = invalid_spec

            # Should raise validation error
            with pytest.raises(ValueError) as exc_info:
                command.execute()

            assert "validation" in str(exc_info.value).lower()

    def test_auto_save_disabled(self, python_project_dir, output_dir):
        """Test workflow with auto_save disabled."""
        config = CreateAgentConfig(
            mode="fast",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            auto_save=False  # Disable auto-save
        )

        command = CreateAgentCommand(config)

        # Execute without saving
        agent_spec = command.execute()

        # Should generate specification
        assert isinstance(agent_spec, AgentSpecification)

        # Should NOT save file
        agent_files = list(output_dir.glob("*.md"))
        assert len(agent_files) == 0

    def test_output_directory_creation(self, python_project_dir):
        """Test automatic creation of output directory."""
        nonexistent_output = python_project_dir / "nonexistent" / "output" / "dir"

        config = CreateAgentConfig(
            mode="fast",
            context=str(python_project_dir),
            output_dir=str(nonexistent_output),
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Execute
        agent_spec = command.execute()

        # Should create output directory and save file
        assert nonexistent_output.exists()
        expected_file = nonexistent_output / f"{agent_spec.name.lstrip('@')}.md"
        assert expected_file.exists()

    def test_complex_project_workflow(self, temp_project_dir, output_dir):
        """Test workflow with complex multi-language project."""
        # Create complex project
        (temp_project_dir / "frontend").mkdir()
        (temp_project_dir / "backend").mkdir()
        (temp_project_dir / "infrastructure").mkdir()

        # Multiple language files
        (temp_project_dir / "frontend" / "app.js").write_text("console.log('React app');")
        (temp_project_dir / "backend" / "app.py").write_text("from flask import Flask")
        (temp_project_dir / "infrastructure" / "docker-compose.yml").write_text("""
version: '3.8'
services:
  web:
    build: .
  redis:
    image: redis:alpine
""")
        (temp_project_dir / "package.json").write_text('{"name": "multi-lang-app"}')
        (temp_project_dir / "requirements.txt").write_text("flask==2.0.0")

        config = CreateAgentConfig(
            mode="smart",
            context=str(temp_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Execute for complex project
        agent_spec = command.execute()

        # Should generate appropriate agent
        assert isinstance(agent_spec, AgentSpecification)
        # Complex multi-language projects may need orchestrators, specialists, or test generators
        assert agent_spec.type in [AgentType.ORCHESTRATOR, AgentType.SPECIALIST, AgentType.TEST]

    def test_yaml_frontmatter_structure(self, python_project_dir, output_dir):
        """Test that saved files have proper YAML frontmatter structure."""
        config = CreateAgentConfig(
            mode="fast",
            context=str(python_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        command = CreateAgentCommand(config)
        agent_spec = command.execute()

        # Read saved file
        saved_file = output_dir / f"{agent_spec.name.lstrip('@')}.md"
        content = saved_file.read_text()

        # Parse YAML frontmatter
        frontmatter_start = content.find("---")
        frontmatter_end = content.find("---", frontmatter_start + 3)

        assert frontmatter_start != -1
        assert frontmatter_end != -1

        yaml_content = content[frontmatter_start + 3:frontmatter_end].strip()
        parsed_frontmatter = yaml.safe_load(yaml_content)

        # Verify required fields
        assert "name" in parsed_frontmatter
        assert "description" in parsed_frontmatter
        assert "type" in parsed_frontmatter
        assert "framework" in parsed_frontmatter

    def test_multiple_agent_generation(self, python_project_dir, output_dir):
        """Test generating multiple different agents for same project."""
        configs = [
            CreateAgentConfig(
                mode="fast",
                context=str(python_project_dir),
                output_dir=str(output_dir),
                template=AgentType.SECURITY,
                auto_save=True
            ),
            CreateAgentConfig(
                mode="fast",
                context=str(python_project_dir),
                output_dir=str(output_dir),
                template=AgentType.TEST,
                auto_save=True
            ),
            CreateAgentConfig(
                mode="fast",
                context=str(python_project_dir),
                output_dir=str(output_dir),
                template=AgentType.PERFORMANCE,
                auto_save=True
            )
        ]

        generated_agents = []
        for config in configs:
            command = CreateAgentCommand(config)
            agent_spec = command.execute()
            generated_agents.append(agent_spec)

        # Should generate different agent types
        agent_types = {agent.type for agent in generated_agents}
        assert len(agent_types) == 3  # Security, Test, Performance

        # All files should be saved
        saved_files = list(output_dir.glob("*.md"))
        assert len(saved_files) == 3

    def test_edge_case_empty_project(self, temp_project_dir, output_dir):
        """Test workflow with minimal/empty project."""
        # Create minimal project
        (temp_project_dir / "main.py").write_text("print('hello')")

        config = CreateAgentConfig(
            mode="fast",
            context=str(temp_project_dir),
            output_dir=str(output_dir),
            auto_save=True
        )

        command = CreateAgentCommand(config)

        # Should handle empty project gracefully
        agent_spec = command.execute()
        assert isinstance(agent_spec, AgentSpecification)

        # Should still save file
        expected_file = output_dir / f"{agent_spec.name.lstrip('@')}.md"
        assert expected_file.exists()


class TestCreateAgentConfig:
    """Test suite for CreateAgentConfig dataclass."""

    def test_config_creation_defaults(self):
        """Test config creation with default values."""
        config = CreateAgentConfig()

        assert config.mode == "smart"
        assert config.context == "."
        assert config.specialization is None
        assert config.template is None
        assert config.output_dir == ".claude/agents"
        assert config.auto_save is True

    def test_config_custom_values(self):
        """Test config creation with custom values."""
        config = CreateAgentConfig(
            mode="fast",
            context="/custom/path",
            specialization="Custom Spec",
            template=AgentType.SECURITY,
            output_dir="/output/dir",
            auto_save=False
        )

        assert config.mode == "fast"
        assert config.context == "/custom/path"
        assert config.specialization == "Custom Spec"
        assert config.template == AgentType.SECURITY
        assert config.output_dir == "/output/dir"
        assert config.auto_save is False


class TestMockAskUserQuestion:
    """Test suite for MockAskUserQuestion helper."""

    def test_mock_with_predefined_responses(self):
        """Test mock with predefined responses."""
        predefined = {"Security Focus": ["Vulnerability Detection"]}
        mock = MockAskUserQuestion(predefined)

        questions = [{
            "header": "Security Focus",
            "options": [{"label": "Vulnerability Detection", "description": "Test"}]
        }]

        result = mock(questions, {})

        assert isinstance(result, UserResponses)
        assert "Security Focus" in result.responses
        assert result.responses["Security Focus"] == ["Vulnerability Detection"]
        assert len(mock.call_history) == 1

    def test_mock_default_responses(self):
        """Test mock with default responses when no predefined."""
        mock = MockAskUserQuestion()

        questions = [{
            "header": "Test Question",
            "options": [
                {"label": "Option 1", "description": "First option"},
                {"label": "Option 2", "description": "Second option"}
            ]
        }]

        result = mock(questions, {})

        assert isinstance(result, UserResponses)
        assert "Test Question" in result.responses
        assert result.responses["Test Question"] == ["Option 1"]  # First option default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])