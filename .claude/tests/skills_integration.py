#!/usr/bin/env python3
"""
Skills Integration Layer for /create-agent Command

Hybrid architecture combining TDD implementation with agent-scaffolding-toolkit expertise.
This integration uses multiple mental models for robust design:

Mental Models Applied:
- First Principles: Fundamental combination of systematic TDD + expert skill knowledge
- Systems Thinking: Complete ecosystem with feedback loops and interdependencies
- Second Order Effects: Integration impact on broader agent creation workflow
- Inversion: Failure prevention and graceful degradation
- Interdependencies: Mapping relationships between components

Architecture:
TDD Implementation (Core Logic) + Skill Expertise (Specialized Knowledge) = Enhanced Agent Creation
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Add skill toolkit to path
SKILL_TOOLKIT_PATH = Path(__file__).parent.parent / "skills" / "agent-scaffolding-toolkit"
sys.path.insert(0, str(SKILL_TOOLKIT_PATH))

# Import our TDD implementations
from context_analyzer import (
    RepositoryContext, RepositoryContextAnalyzer, UserResponses
)
from test_question_generator import SmartQuestionGenerator, Question
from test_agent_generator import (
    IntelligentAgentGenerator, AgentSpecification, AgentType, FrameworkType
)


@dataclass
class SkillCapability:
    """Represents a capability from the agent-scaffolding-toolkit skill."""
    name: str
    description: str
    script_path: Optional[Path] = None
    parameters: Dict[str, Any] = None
    success_rate: float = 1.0


@dataclass
class IntegrationResult:
    """Result of a skill integration operation."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    fallback_used: bool = False
    confidence: float = 1.0


class SkillInterfaceBase(ABC):
    """Abstract base class for skill interfaces with graceful degradation."""

    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.venv_path = skill_path / ".venv"
        self.scripts_path = skill_path / "scripts"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if skill interface is available."""
        pass

    @abstractmethod
    def execute_with_fallback(self, fallback_data: Any) -> IntegrationResult:
        """Execute skill with fallback to TDD implementation."""
        pass


class TemplateDiscoverySkill(SkillInterfaceBase):
    """Integration with agent-scaffolding-toolkit template discovery."""

    def is_available(self) -> bool:
        """Check if template discovery is available."""
        return (self.venv_path.exists() and
                (self.scripts_path / "list_templates.py").exists())

    def discover_templates(self, detailed: bool = False) -> IntegrationResult:
        """Discover available templates with fallback to static knowledge."""
        if not self.is_available():
            return self._static_template_fallback()

        try:
            cmd = [
                str(self.venv_path / "bin" / "python"),
                str(self.scripts_path / "list_templates.py"),
                "--detailed" if detailed else "--json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.skill_path,
                timeout=30
            )

            if result.returncode == 0:
                return IntegrationResult(
                    success=True,
                    data=self._parse_template_output(result.stdout),
                    confidence=0.95
                )
            else:
                return self._static_template_fallback()

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Template discovery failed: {e}",
                fallback_used=True,
                data=self._static_template_fallback().data
            )

    def _parse_template_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse template discovery output."""
        # Parse the structured output from list_templates.py
        templates = []
        lines = output.strip().split('\n')

        current_template = {}
        for line in lines:
            if line.startswith('🎯') and current_template:
                templates.append(current_template)
                current_template = {}
            elif 'File:' in line:
                current_template['file'] = line.split('File:')[1].strip()
            elif 'Description:' in line:
                current_template['description'] = line.split('Description:')[1].strip()
            elif 'Default Tools:' in line:
                current_template['tools'] = line.split('Default Tools:')[1].strip().split(', ')
            elif 'Tags:' in line:
                current_template['tags'] = line.split('Tags:')[1].strip().split(', ')

        if current_template:
            templates.append(current_template)

        return templates

    def _static_template_fallback(self) -> IntegrationResult:
        """Fallback to static template knowledge."""
        static_templates = [
            {
                "name": "Orchestrator",
                "description": "Chief-of-staff agent for multi-agent coordination",
                "tools": ["Task", "Bash", "Read", "Grep"],
                "tags": ["orchestration", "multi-agent", "coordination"],
                "use_cases": [
                    "Coordinating parallel code reviews",
                    "Managing large-scale refactoring projects"
                ]
            },
            {
                "name": "Specialist",
                "description": "Domain-specific expert agent",
                "tools": ["Task", "Read", "Write", "Grep"],
                "tags": ["specialist", "domain-expert", "focused"],
                "use_cases": [
                    "Security analysis and vulnerability assessment",
                    "Performance optimization and profiling"
                ]
            },
            {
                "name": "Referee",
                "description": "Autonomous synthesis and selection agent",
                "tools": ["Read", "Bash", "Task", "Grep"],
                "tags": ["synthesis", "deterministic", "evaluation"],
                "use_cases": [
                    "Selecting best implementation from prototypes",
                    "Automated test result evaluation"
                ]
            }
        ]

        return IntegrationResult(
            success=True,
            data=static_templates,
            fallback_used=True,
            confidence=0.8
        )

    def execute_with_fallback(self, fallback_data: Any) -> IntegrationResult:
        """Execute template discovery with fallback."""
        return self.discover_templates()


class AgentValidationSkill(SkillInterfaceBase):
    """Integration with agent-scaffolding-toolkit validation."""

    def is_available(self) -> bool:
        """Check if validation is available."""
        return (self.venv_path.exists() and
                (self.scripts_path / "validate_agent.py").exists())

    def validate_agent(self, agent_spec: AgentSpecification) -> IntegrationResult:
        """Validate agent specification with skill validation."""
        if not self.is_available():
            return self._tdd_validation_fallback(agent_spec)

        try:
            # Create temporary agent file for validation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(agent_spec.yaml_content)
                temp_file = f.name

            try:
                cmd = [
                    str(self.venv_path / "bin" / "python"),
                    str(self.scripts_path / "validate_agent.py"),
                    "--agent", temp_file,
                    "--json"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.skill_path,
                    timeout=30
                )

                if result.returncode == 0:
                    validation_data = json.loads(result.stdout)
                    return IntegrationResult(
                        success=True,
                        data=validation_data,
                        confidence=0.9
                    )
                else:
                    return self._tdd_validation_fallback(agent_spec)

            finally:
                os.unlink(temp_file)

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Skill validation failed: {e}",
                fallback_used=True,
                data=self._tdd_validation_fallback(agent_spec).data
            )

    def _tdd_validation_fallback(self, agent_spec: AgentSpecification) -> IntegrationResult:
        """Fallback to TDD validation."""
        from test_agent_generator import IntelligentAgentGenerator

        generator = IntelligentAgentGenerator()
        errors = generator.validate_agent_specification(agent_spec)

        return IntegrationResult(
            success=len(errors) == 0,
            data={
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": [],
                "source": "tdd_fallback"
            },
            fallback_used=True,
            confidence=0.85
        )

    def execute_with_fallback(self, fallback_data: Any) -> IntegrationResult:
        """Execute validation with fallback."""
        return self.validate_agent(fallback_data)


class SkillExportSkill(SkillInterfaceBase):
    """Integration with agent-scaffolding-toolkit export functionality."""

    def is_available(self) -> bool:
        """Check if export is available."""
        return (self.venv_path.exists() and
                (self.scripts_path / "export_to_skill_seekers.py").exists())

    def export_agent(self, agent_spec: AgentSpecification, output_dir: Path) -> IntegrationResult:
        """Export agent to Skill Seekers format."""
        if not self.is_available():
            return self._manual_export_fallback(agent_spec, output_dir)

        try:
            # Create temporary agent file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(self._format_agent_for_export(agent_spec))
                temp_file = f.name

            try:
                cmd = [
                    str(self.venv_path / "bin" / "python"),
                    str(self.scripts_path / "export_to_skill_seekers.py"),
                    "--agent", temp_file,
                    "--output-dir", str(output_dir),
                    "--format", "both",
                    "--detect-conflicts",
                    "--package"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.skill_path,
                    timeout=60
                )

                if result.returncode == 0:
                    return IntegrationResult(
                        success=True,
                        data={"exported": True, "output_dir": str(output_dir)},
                        confidence=0.9
                    )
                else:
                    return self._manual_export_fallback(agent_spec, output_dir)

            finally:
                os.unlink(temp_file)

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Skill export failed: {e}",
                fallback_used=True,
                data=self._manual_export_fallback(agent_spec, output_dir).data
            )

    def _format_agent_for_export(self, agent_spec: AgentSpecification) -> str:
        """Format agent specification for skill export."""
        return f"""---
name: {agent_spec.name}
description: {agent_spec.description}
type: {agent_spec.type.value}
framework: {agent_spec.framework.value}
specialization: {agent_spec.specialization}
tools:
{self._format_tools_for_export(agent_spec.tools)}
delegation_network: {[f"@{target.value}" for target in agent_spec.delegation_network]}
capabilities: {agent_spec.capabilities}
---

# {agent_spec.name}

{agent_spec.description}

## Framework
{agent_spec.framework.value}: {agent_spec.methodology}

## Specialization
{agent_spec.specialization}

## Capabilities
{chr(10).join(f"- {cap}" for cap in agent_spec.capabilities)}

## Delegation Network
Can delegate to: {', '.join(f"@{target.value}" for target in agent_spec.delegation_network)}
"""

    def _format_tools_for_export(self, tools) -> str:
        """Format tools for export."""
        tool_lines = []
        for tool in tools:
            tool_lines.append(f"  - {tool.name}: {tool.description}")
        return '\n'.join(tool_lines)

    def _manual_export_fallback(self, agent_spec: AgentSpecification, output_dir: Path) -> IntegrationResult:
        """Fallback to manual export."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export as skill
        skill_file = output_dir / f"{agent_spec.name.lstrip('@')}_skill.md"
        skill_file.write_text(self._format_agent_for_export(agent_spec))

        # Export as config
        config_file = output_dir / f"{agent_spec.name.lstrip('@')}_config.json"
        config_data = {
            "name": agent_spec.name,
            "description": agent_spec.description,
            "type": agent_spec.type.value,
            "specialization": agent_spec.specialization,
            "tools": [{"name": t.name, "description": t.description} for t in agent_spec.tools]
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        return IntegrationResult(
            success=True,
            data={
                "exported": True,
                "skill_file": str(skill_file),
                "config_file": str(config_file),
                "source": "manual_fallback"
            },
            fallback_used=True,
            confidence=0.8
        )

    def execute_with_fallback(self, fallback_data: Any) -> IntegrationResult:
        """Execute export with fallback."""
        agent_spec, output_dir = fallback_data
        return self.export_agent(agent_spec, output_dir)


class SkillsIntegrator:
    """Main integration coordinator combining TDD with skill expertise."""

    def __init__(self, skill_toolkit_path: Optional[Path] = None):
        self.skill_toolkit_path = skill_toolkit_path or SKILL_TOOLKIT_PATH
        self.template_discovery = TemplateDiscoverySkill(self.skill_toolkit_path)
        self.agent_validation = AgentValidationSkill(self.skill_toolkit_path)
        self.skill_export = SkillExportSkill(self.skill_toolkit_path)
        self.integration_stats = {
            "skill_calls": 0,
            "fallbacks_used": 0,
            "success_rate": 0.0
        }

    def discover_templates_for_context(self, context: RepositoryContext) -> IntegrationResult:
        """Discover templates optimized for repository context."""
        # Get all available templates
        template_result = self.template_discovery.discover_templates(detailed=True)
        self.integration_stats["skill_calls"] += 1

        if not template_result.success:
            self.integration_stats["fallbacks_used"] += 1
            return template_result

        # Filter and rank templates based on context
        templates = template_result.data
        ranked_templates = self._rank_templates_for_context(templates, context)

        return IntegrationResult(
            success=True,
            data=ranked_templates,
            confidence=template_result.confidence * 0.9  # Slight reduction for ranking
        )

    def _rank_templates_for_context(self, templates: List[Dict], context: RepositoryContext) -> List[Dict]:
        """Rank templates based on repository context using multiple factors."""
        scored_templates = []

        for template in templates:
            score = 0.0

            # Security-focused scoring
            if context.security_assessment.has_security_files:
                if "security" in template.get('tags', []):
                    score += 0.3
                if template.get('name') == 'Specialist':
                    score += 0.2  # Specialists can be security-focused

            # Complexity-based scoring
            if context.code_patterns.complexity_score >= 8:
                if template.get('name') == 'Orchestrator':
                    score += 0.4  # Complex projects need orchestration
                if "multi-agent" in template.get('tags', []):
                    score += 0.2

            # Multi-language project scoring
            if len(context.tech_stack.languages) > 2:
                if template.get('name') == 'Orchestrator':
                    score += 0.3
                if "coordination" in template.get('tags', []):
                    score += 0.2

            # Testing focus scoring
            if context.quality_metrics.test_coverage_score < 5:
                if "test" in str(template.get('use_cases', [])).lower():
                    score += 0.3

            # Documentation quality scoring
            if context.quality_metrics.documentation_quality >= 8:
                if "documentation" in str(template.get('use_cases', [])).lower():
                    score += 0.2

            # Add base score
            score += 0.5

            scored_templates.append({
                **template,
                "context_score": score,
                "ranking_factors": self._get_ranking_factors(template, context)
            })

        # Sort by context score
        scored_templates.sort(key=lambda x: x["context_score"], reverse=True)
        return scored_templates

    def _get_ranking_factors(self, template: Dict, context: RepositoryContext) -> List[str]:
        """Get explanation of ranking factors for template."""
        factors = []

        if context.security_assessment.has_security_files and "security" in template.get('tags', []):
            factors.append("Security-focused project")

        if context.code_patterns.complexity_score >= 8 and template.get('name') == 'Orchestrator':
            factors.append("High complexity needs orchestration")

        if len(context.tech_stack.languages) > 2 and template.get('name') == 'Orchestrator':
            factors.append("Multi-language coordination")

        if context.quality_metrics.test_coverage_score < 5 and "test" in str(template.get('use_cases', [])).lower():
            factors.append("Low test coverage detected")

        return factors

    def validate_agent_with_skill(self, agent_spec: AgentSpecification) -> IntegrationResult:
        """Validate agent using skill validation with TDD fallback."""
        self.integration_stats["skill_calls"] += 1

        result = self.agent_validation.validate_agent(agent_spec)

        if result.fallback_used:
            self.integration_stats["fallbacks_used"] += 1

        return result

    def export_agent_with_skill(self, agent_spec: AgentSpecification, output_dir: Path) -> IntegrationResult:
        """Export agent using skill export with manual fallback."""
        self.integration_stats["skill_calls"] += 1

        result = self.skill_export.export_agent(agent_spec, output_dir)

        if result.fallback_used:
            self.integration_stats["fallbacks_used"] += 1

        return result

    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics for monitoring."""
        success_rate = (
            (self.integration_stats["skill_calls"] - self.integration_stats["fallbacks_used"])
            / max(self.integration_stats["skill_calls"], 1)
        )
        self.integration_stats["success_rate"] = success_rate

        return self.integration_stats.copy()


# Global integrator instance
_skills_integrator = None

def get_skills_integrator() -> SkillsIntegrator:
    """Get or create global skills integrator instance."""
    global _skills_integrator
    if _skills_integrator is None:
        _skills_integrator = SkillsIntegrator()
    return _skills_integrator


# Test the integration
if __name__ == "__main__":
    integrator = get_skills_integrator()

    print("🔧 Testing Skills Integration")
    print("=" * 50)

    # Test template discovery
    print("\n1. Testing Template Discovery:")
    result = integrator.template_discovery.discover_templates()
    print(f"Success: {result.success}")
    print(f"Fallback used: {result.fallback_used}")
    print(f"Confidence: {result.confidence}")
    if result.success:
        print(f"Found {len(result.data)} templates")

    # Test validation with mock agent
    print("\n2. Testing Agent Validation:")
    from test_agent_generator import AgentSpecification, AgentType, FrameworkType, AgentTool

    mock_agent = AgentSpecification(
        name="test-agent",
        description="Test agent for validation",
        type=AgentType.SPECIALIST,
        framework=FrameworkType.COGNITIVE,
        tools=[AgentTool("Read", "Read files", "file_operations")],
        delegation_network=[],
        methodology="Test methodology",
        specialization="Testing",
        capabilities=["Test capability"],
        usage_patterns=["Test pattern"],
        yaml_content="name: test-agent"
    )

    result = integrator.validate_agent_with_skill(mock_agent)
    print(f"Success: {result.success}")
    print(f"Fallback used: {result.fallback_used}")
    print(f"Data: {result.data}")

    # Print integration stats
    print("\n3. Integration Stats:")
    stats = integrator.get_integration_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")