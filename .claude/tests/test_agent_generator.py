#!/usr/bin/env python3
"""
TDD Phase 3: Tests for Intelligent Agent Generator

This test suite follows Test-Driven Development principles.
Tests are written FIRST, then implementation is created to make them pass.

The Intelligent Agent Generator is responsible for:
- Selecting appropriate agent templates based on context and user responses
- Customizing frameworks (M.A.P.S., C.O.G.N.I.T.I.V.E., G.E.N.E. E.D.I.T., P.O.S.S.I.B.I.L.I.T.Y.)
- Configuring tools based on repository context
- Designing delegation networks
- Generating personalized agent specifications in YAML format
- Validating generated agents against requirements
"""

import pytest
import yaml
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from pathlib import Path

# Import from our TDD implementations
from context_analyzer import RepositoryContext, TechStack, CodePatterns, SecurityAssessment, QualityMetrics
from test_question_generator import Question, SmartQuestionGenerator


class AgentType(Enum):
    """Available agent templates."""
    ORCHESTRATOR = "orchestrator"
    SPECIALIST = "specialist"
    REFEREE = "referee"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TEST = "test"


class FrameworkType(Enum):
    """Available mental model frameworks."""
    MAPS = "M.A.P.S"  # Mapping→Analysis→Pattern Detection→Synthesis
    COGNITIVE = "C.O.G.N.I.T.I.V.E"  # Contextual→Organizational→Generative→...
    GENE_EDIT = "G.E.N.E. E.D.I.T"  # Generate→Evaluate→Navigate→...
    POSSIBILITY = "P.O.S.S.I.B.I.L.I.T.Y"  # Pattern→Optimization→...
    CUSTOM = "Custom"


@dataclass
class AgentTool:
    """Represents a tool available to an agent."""
    name: str
    description: str
    category: str  # file_operations, search, analysis, generation, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTemplate:
    """Represents an agent template configuration."""
    name: str
    type: AgentType
    description: str
    framework: FrameworkType
    default_tools: List[AgentTool] = field(default_factory=list)
    delegation_targets: List[AgentType] = field(default_factory=list)
    specialization_hint: Optional[str] = None


@dataclass
class UserResponses:
    """User responses to generated questions."""
    responses: Dict[str, List[str]] = field(default_factory=dict)
    mode: str = "smart"
    specialization: Optional[str] = None
    template_preference: Optional[AgentType] = None


@dataclass
class AgentSpecification:
    """Complete agent specification."""
    name: str
    description: str
    type: AgentType
    framework: FrameworkType
    tools: List[AgentTool]
    delegation_network: List[AgentType]
    methodology: str
    specialization: str
    capabilities: List[str]
    usage_patterns: List[str]
    yaml_content: str


class IntelligentAgentGenerator:
    """Generates intelligent agents based on context and user responses."""

    def __init__(self):
        self.templates = self._load_agent_templates()
        self.available_tools = self._load_available_tools()
        # Initialize skills integration for enhanced validation and export
        try:
            from skills_integration import get_skills_integrator
            self.skills_integrator = get_skills_integrator()
        except ImportError:
            self.skills_integrator = None

    def _load_agent_templates(self) -> Dict[AgentType, AgentTemplate]:
        """Load available agent templates."""
        return {
            AgentType.ORCHESTRATOR: AgentTemplate(
                name="Orchestrator Agent",
                type=AgentType.ORCHESTRATOR,
                description="Chief-of-staff orchestrator that manages parallel agent workflows",
                framework=FrameworkType.MAPS,
                default_tools=[
                    AgentTool("Task", "Launch specialized agents", "delegation"),
                    AgentTool("Bash", "Execute system commands", "system"),
                    AgentTool("Read", "Read files", "file_operations")
                ],
                delegation_targets=[AgentType.SPECIALIST, AgentType.REFEREE, AgentType.SECURITY]
            ),
            AgentType.SPECIALIST: AgentTemplate(
                name="Specialist Agent",
                type=AgentType.SPECIALIST,
                description="Domain specialist for specific technical areas",
                framework=FrameworkType.COGNITIVE,
                default_tools=[
                    AgentTool("Read", "Read files", "file_operations"),
                    AgentTool("Grep", "Search content", "search"),
                    AgentTool("Edit", "Edit files", "file_operations")
                ],
                delegation_targets=[AgentType.SECURITY, AgentType.PERFORMANCE]
            ),
            AgentType.SECURITY: AgentTemplate(
                name="Security Analyst",
                type=AgentType.SECURITY,
                description="Security specialist for vulnerability detection and compliance",
                framework=FrameworkType.COGNITIVE,
                default_tools=[
                    AgentTool("Read", "Read files", "file_operations"),
                    AgentTool("Grep", "Search for security patterns", "search"),
                    AgentTool("Bash", "Run security tools", "system"),
                    AgentTool("Task", "Delegate to other security tools", "delegation")
                ],
                delegation_targets=[AgentType.SPECIALIST]
            ),
            AgentType.PERFORMANCE: AgentTemplate(
                name="Performance Auditor",
                type=AgentType.PERFORMANCE,
                description="Performance optimization specialist",
                framework=FrameworkType.MAPS,
                default_tools=[
                    AgentTool("Read", "Analyze code structure", "file_operations"),
                    AgentTool("Bash", "Run performance profiling", "system"),
                    AgentTool("Grep", "Find bottlenecks", "search")
                ],
                delegation_targets=[AgentType.SPECIALIST]
            ),
            AgentType.TEST: AgentTemplate(
                name="Test Generator",
                type=AgentType.TEST,
                description="Comprehensive test generation specialist",
                framework=FrameworkType.GENE_EDIT,
                default_tools=[
                    AgentTool("Read", "Read source code", "file_operations"),
                    AgentTool("Write", "Generate test files", "file_operations"),
                    AgentTool("Edit", "Update existing tests", "file_operations"),
                    AgentTool("Bash", "Run test suites", "system")
                ],
                delegation_targets=[AgentType.SPECIALIST, AgentType.PERFORMANCE]
            ),
            AgentType.REFEREE: AgentTemplate(
                name="Referee Agent",
                type=AgentType.REFEREE,
                description="Convergent synthesis primitive for deterministic evaluation",
                framework=FrameworkType.COGNITIVE,
                default_tools=[
                    AgentTool("Task", "Manage parallel agent outputs", "delegation"),
                    AgentTool("Read", "Analyze agent results", "file_operations"),
                    AgentTool("Bash", "Run validation tools", "system")
                ],
                delegation_targets=[]
            )
        }

    def _load_available_tools(self) -> List[AgentTool]:
        """Load all available tools for agent configuration."""
        return [
            AgentTool("Read", "Read files from filesystem", "file_operations"),
            AgentTool("Write", "Write files to filesystem", "file_operations"),
            AgentTool("Edit", "Edit existing files", "file_operations"),
            AgentTool("Grep", "Search file contents", "search"),
            AgentTool("Glob", "Find files by pattern", "search"),
            AgentTool("Bash", "Execute system commands", "system"),
            AgentTool("Task", "Launch specialized agents", "delegation"),
            AgentTool("WebFetch", "Fetch web content", "external"),
            AgentTool("WebSearch", "Search the web", "external"),
            AgentTool("TodoWrite", "Manage task lists", "productivity"),
            AgentTool("AskUserQuestion", "Ask user questions", "interaction"),
            AgentTool("ExitPlanMode", "Exit planning mode", "workflow")
        ]

    def select_template(self, context: RepositoryContext, user_responses: UserResponses) -> AgentTemplate:
        """
        Select the most appropriate template based on context and user responses with skill integration.

        Args:
            context: Repository context analysis
            user_responses: User responses to questions

        Returns:
            Selected agent template
        """
        # Direct user preference takes priority
        if user_responses.template_preference:
            return self.templates[user_responses.template_preference]

        # Get skill-enhanced template recommendations
        skill_templates = []
        if self.skills_integrator:
            template_result = self.skills_integrator.discover_templates_for_context(context)
            if template_result.success:
                skill_templates = template_result.data

        # Enhanced template selection using skill insights
        if skill_templates:
            # Check user responses for template selection
            template_response = user_responses.responses.get("Agent Template Selection", [])
            if template_response:
                # Parse skill-based template selection
                for response in template_response:
                    for skill_template in skill_templates:
                        template_name = skill_template.get('name', '').lower()
                        if template_name.lower() in response.lower():
                            # Map skill template names to our AgentType enums
                            agent_type = self._map_skill_template_to_type(template_name)
                            if agent_type in self.templates:
                                return self.templates[agent_type]

            # Check coordination responses
            coordination_response = user_responses.responses.get("Multi-Agent Coordination", [])
            if coordination_response and any("orchestrator" in coord.lower() for coord in coordination_response):
                return self.templates[AgentType.ORCHESTRATOR]

        # Enhanced security-focused selection using skill insights
        if context.security_assessment.has_security_files and context.security_assessment.security_score >= 7:
            if "Vulnerability Detection" in user_responses.responses.get("Security Focus", []):
                # Check if security-specialist template is recommended by skills
                security_recommended = any(
                    'security' in template.get('tags', []) or
                    template.get('name') == 'Specialist'
                    for template in skill_templates
                )
                if security_recommended:
                    return self.templates[AgentType.SPECIALIST]  # Will be customized for security
                return self.templates[AgentType.SECURITY]

        # Performance-focused selection for complex projects with skill insights
        if context.code_patterns.complexity_score >= 8:
            # Check if orchestrator is recommended by skills for complex projects
            orchestrator_recommended = any(
                template.get('name') == 'Orchestrator' and
                template.get('context_score', 0) > 0.7
                for template in skill_templates
            )

            if orchestrator_recommended:
                return self.templates[AgentType.ORCHESTRATOR]

            if "Code Quality" in user_responses.responses.get("Performance Focus", []):
                return self.templates[AgentType.SPECIALIST]
            elif "Performance" in user_responses.responses.get("Performance Focus", []):
                return self.templates[AgentType.PERFORMANCE]

        # Testing-focused selection
        if context.quality_metrics.test_coverage_score < 5:
            return self.templates[AgentType.TEST]

        # Well-documented projects might need orchestrators
        if context.quality_metrics.documentation_quality >= 8:
            return self.templates[AgentType.ORCHESTRATOR]

        # Multi-language projects might need orchestrators (with skill confirmation)
        if len(context.tech_stack.languages) > 2:
            multi_agent_recommended = any(
                'multi-agent' in template.get('tags', []) or
                template.get('name') == 'Orchestrator'
                for template in skill_templates
            )
            if multi_agent_recommended:
                return self.templates[AgentType.ORCHESTRATOR]

        # Default to specialist
        return self.templates[AgentType.SPECIALIST]

    def _map_skill_template_to_type(self, template_name: str) -> Optional[AgentType]:
        """Map skill template names to AgentType enums."""
        mapping = {
            'orchestrator': AgentType.ORCHESTRATOR,
            'specialist': AgentType.SPECIALIST,
            'referee': AgentType.REFEREE,
            'security': AgentType.SECURITY,
            'performance': AgentType.PERFORMANCE,
            'test': AgentType.TEST
        }
        return mapping.get(template_name.lower())

    def customize_framework(self, template: AgentTemplate, context: RepositoryContext, user_responses: UserResponses) -> FrameworkType:
        """
        Customize the framework based on template, context, and user responses.

        Args:
            template: Selected agent template
            context: Repository context analysis
            user_responses: User responses to questions

        Returns:
            Customized framework type
        """
        # Start with template default
        framework = template.framework

        # Customize based on user responses
        if "API Documentation" in user_responses.responses.get("Documentation", []):
            framework = FrameworkType.GENE_EDIT  # Structured approach for documentation

        # Security-focused agents benefit from cognitive framework
        if template.type == AgentType.SECURITY:
            framework = FrameworkType.COGNITIVE

        # Complex performance agents benefit from systematic approach
        if template.type == AgentType.PERFORMANCE and context.code_patterns.complexity_score >= 8:
            framework = FrameworkType.MAPS

        return framework

    def configure_tools(self, template: AgentTemplate, context: RepositoryContext) -> List[AgentTool]:
        """
        Configure tools for the agent based on template and repository context.

        Args:
            template: Selected agent template
            context: Repository context analysis

        Returns:
            List of configured tools
        """
        tools = []

        # Start with template default tools
        tools.extend(template.default_tools)

        # Add tools based on repository characteristics
        if context.tech_stack.languages:
            # Add search tools for multi-language projects
            if len(context.tech_stack.languages) > 1:
                tools.append(AgentTool("Grep", "Search across multiple languages", "search"))
                tools.append(AgentTool("Glob", "Find files by language patterns", "search"))

        # Add security tools for security-focused projects
        if context.security_assessment.has_security_files:
            tools.append(AgentTool("Bash", "Run security scans", "system"))

        # Add performance tools for complex projects
        if context.code_patterns.complexity_score >= 8:
            tools.append(AgentTool("Bash", "Performance profiling", "system"))

        # Add web tools for projects with external dependencies
        if context.tech_stack.cloud_platforms or context.tech_stack.databases:
            tools.append(AgentTool("WebSearch", "Research best practices", "external"))

        # Add task management for orchestrators
        if template.type == AgentType.ORCHESTRATOR:
            tools.append(AgentTool("TodoWrite", "Manage complex workflows", "productivity"))

        # Add user interaction for specialists that need clarification
        if template.type == AgentType.SPECIALIST:
            tools.append(AgentTool("AskUserQuestion", "Get clarification on requirements", "interaction"))

        # Remove duplicates
        unique_tools = []
        seen_tools = set()
        for tool in tools:
            tool_key = (tool.name, tool.category)
            if tool_key not in seen_tools:
                unique_tools.append(tool)
                seen_tools.add(tool_key)

        return unique_tools

    def design_delegation_network(self, template: AgentTemplate, context: RepositoryContext) -> List[AgentType]:
        """
        Design delegation network for the agent.

        Args:
            template: Selected agent template
            context: Repository context analysis

        Returns:
            List of agent types this agent can delegate to
        """
        delegation_targets = list(template.delegation_targets)

        # Add security specialist for any project with security concerns
        if context.security_assessment.has_security_files and AgentType.SECURITY not in delegation_targets:
            delegation_targets.append(AgentType.SECURITY)

        # Add performance specialist for complex projects
        if context.code_patterns.complexity_score >= 8 and AgentType.PERFORMANCE not in delegation_targets:
            delegation_targets.append(AgentType.PERFORMANCE)

        # Add test generator for projects with low test coverage
        if context.quality_metrics.test_coverage_score < 5 and AgentType.TEST not in delegation_targets:
            delegation_targets.append(AgentType.TEST)

        return delegation_targets

    def generate_agent_specification(self, context: RepositoryContext, user_responses: UserResponses) -> AgentSpecification:
        """
        Generate complete agent specification.

        Args:
            context: Repository context analysis
            user_responses: User responses to questions

        Returns:
            Complete agent specification
        """
        # Select template
        template = self.select_template(context, user_responses)

        # Customize framework
        framework = self.customize_framework(template, context, user_responses)

        # Configure tools
        tools = self.configure_tools(template, context)

        # Design delegation network
        delegation_network = self.design_delegation_network(template, context)

        # Generate specification details
        agent_name = self._generate_agent_name(template, context, user_responses)
        description = self._generate_description(template, context, user_responses)
        methodology = self._generate_methodology(framework)
        specialization = self._generate_specialization(template, context, user_responses)
        capabilities = self._generate_capabilities(template, context, tools)
        usage_patterns = self._generate_usage_patterns(template, context)

        # Generate YAML content
        yaml_content = self._generate_yaml_content(
            agent_name, description, template.type, framework,
            tools, delegation_network, methodology, specialization,
            capabilities, usage_patterns
        )

        return AgentSpecification(
            name=agent_name,
            description=description,
            type=template.type,
            framework=framework,
            tools=tools,
            delegation_network=delegation_network,
            methodology=methodology,
            specialization=specialization,
            capabilities=capabilities,
            usage_patterns=usage_patterns,
            yaml_content=yaml_content
        )

    def _generate_agent_name(self, template: AgentTemplate, context: RepositoryContext, user_responses: UserResponses) -> str:
        """Generate appropriate agent name."""
        base_name = template.name.replace(" Agent", "").lower().replace(" ", "-")

        # Add specialization if present
        if user_responses.specialization:
            return f"{base_name}-{user_responses.specialization.lower().replace(' ', '-')}"

        return base_name

    def _generate_description(self, template: AgentTemplate, context: RepositoryContext, user_responses: UserResponses) -> str:
        """Generate agent description."""
        base_desc = template.description

        # Add context-specific details
        if context.tech_stack.frameworks:
            frameworks_str = ", ".join(context.tech_stack.frameworks[:2])
            base_desc += f" Specialized for {frameworks_str} projects."

        if context.security_assessment.has_security_files:
            base_desc += " Includes security analysis capabilities."

        return base_desc

    def _generate_methodology(self, framework: FrameworkType) -> str:
        """Generate methodology description based on framework."""
        methodologies = {
            FrameworkType.MAPS: "Mapping→Analysis→Pattern Detection→Synthesis systematic approach",
            FrameworkType.COGNITIVE: "Contextual→Organizational→Generative→Networked→Integrative→Thoughtful→Iterative→Validating→Exploratory cognitive flow",
            FrameworkType.GENE_EDIT: "Generate→Evaluate→Navigate→Execute→Develop→Iterate→Transform precision editing approach",
            FrameworkType.POSSIBILITY: "Pattern→Optimization→Synthesis→Synergy→Integration→Breakthrough→Innovation→Leverage→Intelligence→Transformation→Yield creative expansion",
            FrameworkType.CUSTOM: "Customized methodology based on specific requirements"
        }
        return methodologies.get(framework, "Customized methodology")

    def _generate_specialization(self, template: AgentTemplate, context: RepositoryContext, user_responses: UserResponses) -> str:
        """Generate agent specialization description."""
        if user_responses.specialization:
            return user_responses.specialization

        # Infer from repository context
        if context.tech_stack.frameworks:
            return f"{context.tech_stack.frameworks[0]} development"

        if context.security_assessment.has_security_files:
            return "Security analysis and vulnerability detection"

        return template.specialization_hint or "General code analysis"

    def _generate_capabilities(self, template: AgentTemplate, context: RepositoryContext, tools: List[AgentTool]) -> List[str]:
        """Generate list of agent capabilities."""
        capabilities = [
            f"Analyze {context.dominant_language} codebases",
            "Identify patterns and best practices",
            "Provide actionable recommendations"
        ]

        # Add tool-specific capabilities
        tool_capabilities = {
            "Grep": "Search and filter code patterns",
            "Bash": "Execute system commands and tools",
            "Write": "Generate code and documentation",
            "Task": "Coordinate specialized sub-agents",
            "WebSearch": "Research best practices and solutions"
        }

        for tool in tools:
            if tool.name in tool_capabilities:
                capabilities.append(tool_capabilities[tool.name])

        return capabilities

    def _generate_usage_patterns(self, template: AgentTemplate, context: RepositoryContext) -> List[str]:
        """Generate usage pattern descriptions."""
        patterns = [
            "Pre-commit code review",
            "Architecture analysis",
            "Performance optimization"
        ]

        # Add context-specific patterns
        if context.security_assessment.has_security_files:
            patterns.append("Security vulnerability assessment")

        if context.code_patterns.complexity_score >= 8:
            patterns.append("Complex code refactoring")

        return patterns

    def _generate_yaml_content(self, name: str, description: str, agent_type: AgentType,
                             framework: FrameworkType, tools: List[AgentTool],
                             delegation_network: List[AgentType], methodology: str,
                             specialization: str, capabilities: List[str],
                             usage_patterns: List[str]) -> str:
        """Generate final YAML content for the agent."""

        yaml_dict = {
            "name": f"@{name}",
            "description": description,
            "type": agent_type.value if hasattr(agent_type, 'value') else str(agent_type),
            "framework": framework.value if hasattr(framework, 'value') else str(framework),
            "methodology": methodology,
            "specialization": specialization,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category
                }
                for tool in tools
            ],
            "delegation_network": [
                f"@{target.value}" if hasattr(target, 'value') else f"@{target}"
                for target in delegation_network
            ],
            "capabilities": capabilities,
            "usage_patterns": usage_patterns
        }

        return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)

    def validate_agent_specification(self, spec: AgentSpecification) -> List[str]:
        """
        Validate generated agent specification with skill integration.

        Args:
            spec: Agent specification to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Basic structure validation
        if not spec.name:
            errors.append("Agent name is required")
        if not spec.description:
            errors.append("Agent description is required")
        if not spec.tools:
            errors.append("Agent must have at least one tool")

        # YAML content validation
        try:
            parsed = yaml.safe_load(spec.yaml_content)
            if not isinstance(parsed, dict):
                errors.append("YAML content must be a dictionary")
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML content: {e}")

        # Tool validation
        tool_names = [tool.name for tool in spec.tools]
        if len(tool_names) != len(set(tool_names)):
            errors.append("Duplicate tools detected")

        # Delegation network validation
        valid_types = {AgentType.ORCHESTRATOR, AgentType.SPECIALIST, AgentType.SECURITY,
                      AgentType.PERFORMANCE, AgentType.TEST, AgentType.REFEREE}
        for target in spec.delegation_network:
            if target not in valid_types:
                errors.append(f"Invalid delegation target: {target}")

        # Enhanced validation using skills if available
        if self.skills_integrator:
            try:
                skill_validation = self.skills_integrator.validate_agent_with_skill(spec)
                if skill_validation.success:
                    skill_data = skill_validation.data
                    # Combine TDD validation with skill validation
                    if not skill_data.get('valid', True):
                        skill_errors = skill_data.get('errors', [])
                        # Add skill-specific errors with prefix
                        for skill_error in skill_errors:
                            if skill_error not in errors:  # Avoid duplicates
                                errors.append(f"[Skill Validation] {skill_error}")
                else:
                    # Skill validation failed, but TDD validation passed
                    # Log the failure but don't fail the agent creation
                    pass  # Could add logging here
            except Exception:
                # Skill validation failed unexpectedly, but TDD validation passed
                pass  # Could add logging here

        return errors

    def export_agent_to_skill_seekers(self, spec: AgentSpecification, output_dir: Path) -> Dict[str, Any]:
        """
        Export agent specification to Skill Seekers format using skill integration.

        Args:
            spec: Agent specification to export
            output_dir: Output directory for exported files

        Returns:
            Export result information
        """
        export_result = {
            "success": False,
            "exported_files": [],
            "error": None,
            "source": "tdd_fallback"
        }

        # Try skill-enhanced export first
        if self.skills_integrator:
            try:
                skill_export = self.skills_integrator.export_agent_with_skill(spec, output_dir)
                if skill_export.success:
                    export_result.update({
                        "success": True,
                        "exported_files": skill_export.data,
                        "source": "skill_enhanced"
                    })
                    return export_result
                # Fall back to manual export if skill export fails
            except Exception as e:
                export_result["error"] = f"Skill export failed: {e}"
                # Continue to manual export

        # Manual export fallback (original TDD implementation)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Export as agent file (same format as before)
            agent_file = output_dir / f"{spec.name.lstrip('@')}.md"
            agent_file.write_text(self._format_agent_for_export(spec))
            export_result["exported_files"].append(str(agent_file))

            # Export as skill configuration
            skill_config_file = output_dir / f"{spec.name.lstrip('@')}_config.json"
            skill_config = {
                "name": spec.name,
                "description": spec.description,
                "type": spec.type.value,
                "framework": spec.framework.value,
                "specialization": spec.specialization,
                "tools": [{"name": t.name, "description": t.description} for t in spec.tools],
                "capabilities": spec.capabilities,
                "usage_patterns": spec.usage_patterns
            }
            skill_config_file.write_text(json.dumps(skill_config, indent=2))
            export_result["exported_files"].append(str(skill_config_file))

            export_result["success"] = True
            export_result["source"] = "tdd_fallback"

        except Exception as e:
            export_result["error"] = f"Manual export failed: {e}"

        return export_result

    def _format_agent_for_export(self, spec: AgentSpecification) -> str:
        """Format agent specification for export."""
        return f"""---
name: {spec.name}
description: {spec.description}
type: {spec.type.value if hasattr(spec.type, 'value') else str(spec.type)}
framework: {spec.framework.value if hasattr(spec.framework, 'value') else str(spec.framework)}
methodology: {spec.methodology}
specialization: {spec.specialization}
tools:
{self._format_tools_for_yaml(spec.tools)}
delegation_network: {[f"@{target.value}" if hasattr(target, 'value') else f"@{target}" for target in spec.delegation_network]}
capabilities: {spec.capabilities}
usage_patterns: {spec.usage_patterns}
---

# {spec.name}

{spec.description}

## Framework
{spec.framework.value if hasattr(spec.framework, 'value') else str(spec.framework)}: {spec.methodology}

## Specialization
{spec.specialization}

## Capabilities
{chr(10).join(f"- {cap}" for cap in spec.capabilities)}

## Usage Patterns
{chr(10).join(f"- {pattern}" for pattern in spec.usage_patterns)}

## Delegation Network
Can delegate to: {', '.join(f"@{target.value}" if hasattr(target, 'value') else f"@{target}" for target in spec.delegation_network)}

---

*Generated by intelligent agent generator with skill integration*
"""

    def _format_tools_for_yaml(self, tools) -> str:
        """Format tools for YAML export."""
        tool_lines = []
        for tool in tools:
            tool_lines.append(f"  - {tool.name}: {tool.description}")
        return '\n'.join(tool_lines)


class TestIntelligentAgentGenerator:
    """Test suite for Intelligent Agent Generator using TDD methodology."""

    @pytest.fixture
    def generator(self):
        """Create an agent generator."""
        return IntelligentAgentGenerator()

    @pytest.fixture
    def security_context(self):
        """Create security-focused repository context."""
        tech_stack = TechStack(
            languages=["Python"],
            frameworks=["Django"],
            databases=["PostgreSQL"],
            build_tools=["Docker"],
            testing_frameworks=["pytest"],
            package_managers=["pip"],
            cloud_platforms=[]
        )

        code_patterns = CodePatterns(
            architectural_patterns=["MVC"],
            design_patterns=["Repository"],
            organization_structure="src-based",
            development_methodology="DevOps",
            complexity_score=6,
            maintainability_index=75
        )

        security_assessment = SecurityAssessment(
            has_security_files=True,
            security_files=["SECURITY.md", ".snyk"],
            vulnerability_tools=["Snyk"],
            compliance_frameworks=["OWASP"],
            security_score=8
        )

        quality_metrics = QualityMetrics(
            test_coverage_score=7,
            documentation_quality=6,
            code_complexity=6,
            error_handling_quality=7,
            performance_score=6
        )

        return RepositoryContext(
            path="/test/security-project",
            name="security-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=50,
            dominant_language="Python"
        )

    @pytest.fixture
    def complex_context(self):
        """Create complex project context."""
        tech_stack = TechStack(
            languages=["Python", "JavaScript", "TypeScript"],
            frameworks=["Django", "React", "Node.js"],
            databases=["PostgreSQL", "Redis", "MongoDB"],
            build_tools=["Docker", "Webpack", "Babel"],
            testing_frameworks=["pytest", "Jest", "Mocha"],
            package_managers=["pip", "npm", "yarn"],
            cloud_platforms=["AWS", "GCP"]
        )

        code_patterns = CodePatterns(
            architectural_patterns=["Microservices", "Event-Driven", "CQRS"],
            design_patterns=["Factory", "Observer", "Strategy", "Command"],
            organization_structure="src-based",
            development_methodology="DevOps",
            complexity_score=9,
            maintainability_index=40
        )

        security_assessment = SecurityAssessment(
            has_security_files=False,
            security_files=[],
            vulnerability_tools=[],
            compliance_frameworks=[],
            security_score=4
        )

        quality_metrics = QualityMetrics(
            test_coverage_score=3,
            documentation_quality=7,
            code_complexity=9,
            error_handling_quality=5,
            performance_score=4
        )

        return RepositoryContext(
            path="/test/complex-project",
            name="complex-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=200,
            dominant_language="Python"
        )

    @pytest.fixture
    def user_responses_security(self):
        """Create user responses favoring security."""
        return UserResponses(
            responses={"Security Focus": ["Vulnerability Detection", "Compliance"]},
            specialization="Security Analysis"
        )

    @pytest.fixture
    def user_responses_performance(self):
        """Create user responses favoring performance."""
        return UserResponses(
            responses={"Performance Focus": ["Performance", "Code Quality"]},
            specialization="Performance Optimization"
        )

    def test_generator_initialization(self, generator):
        """Test agent generator initialization."""
        assert len(generator.templates) == 6  # All agent types loaded
        assert len(generator.available_tools) == 12  # All tools loaded

        # Check that key templates are loaded
        assert AgentType.SECURITY in generator.templates
        assert AgentType.ORCHESTRATOR in generator.templates
        assert AgentType.SPECIALIST in generator.templates

    def test_template_selection_security_focus(self, generator, security_context, user_responses_security):
        """Test template selection for security-focused projects."""
        template = generator.select_template(security_context, user_responses_security)

        assert template.type == AgentType.SECURITY
        assert "security" in template.description.lower()

    def test_template_selection_complex_project(self, generator, complex_context, user_responses_performance):
        """Test template selection for complex projects."""
        template = generator.select_template(complex_context, user_responses_performance)

        assert template.type in [AgentType.PERFORMANCE, AgentType.SPECIALIST, AgentType.ORCHESTRATOR]

    def test_framework_customization(self, generator, security_context, user_responses_security):
        """Test framework customization based on context."""
        template = generator.select_template(security_context, user_responses_security)
        framework = generator.customize_framework(template, security_context, user_responses_security)

        assert isinstance(framework, FrameworkType)
        # Security agents should use cognitive framework
        assert framework == FrameworkType.COGNITIVE

    def test_tool_configuration(self, generator, complex_context):
        """Test tool configuration based on repository context."""
        template = generator.templates[AgentType.SPECIALIST]
        tools = generator.configure_tools(template, complex_context)

        # Should have default tools
        assert any(tool.name == "Read" for tool in tools)
        assert any(tool.name == "Grep" for tool in tools)

        # Should add tools based on context
        assert any(tool.name == "Grep" for tool in tools)  # Multi-language project
        tool_names = [tool.name for tool in tools]
        assert len(tool_names) == len(set(tool_names))  # No duplicates

    def test_delegation_network_design(self, generator, complex_context):
        """Test delegation network design."""
        template = generator.templates[AgentType.SPECIALIST]
        delegation_targets = generator.design_delegation_network(template, complex_context)

        assert isinstance(delegation_targets, list)
        # Complex project should get performance and test delegation
        assert AgentType.PERFORMANCE in delegation_targets
        assert AgentType.TEST in delegation_targets  # Low test coverage

    def test_complete_agent_specification_generation(self, generator, security_context, user_responses_security):
        """Test complete agent specification generation."""
        spec = generator.generate_agent_specification(security_context, user_responses_security)

        assert isinstance(spec, AgentSpecification)
        assert spec.name
        assert spec.description
        assert spec.type == AgentType.SECURITY
        assert isinstance(spec.framework, FrameworkType)
        assert len(spec.tools) > 0
        assert isinstance(spec.delegation_network, list)
        assert spec.methodology
        assert spec.specialization
        assert len(spec.capabilities) > 0
        assert len(spec.usage_patterns) > 0
        assert spec.yaml_content

    def test_yaml_content_generation(self, generator, security_context, user_responses_security):
        """Test YAML content generation."""
        spec = generator.generate_agent_specification(security_context, user_responses_security)

        # Verify YAML is valid
        try:
            parsed = yaml.safe_load(spec.yaml_content)
            assert isinstance(parsed, dict)
            assert "name" in parsed
            assert "description" in parsed
            assert "tools" in parsed
            assert "capabilities" in parsed
        except yaml.YAMLError:
            pytest.fail("Generated YAML content is invalid")

    def test_agent_specification_validation(self, generator, security_context, user_responses_security):
        """Test agent specification validation."""
        spec = generator.generate_agent_specification(security_context, user_responses_security)

        errors = generator.validate_agent_specification(spec)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_validation_errors_detection(self, generator):
        """Test detection of validation errors."""
        # Create invalid specification
        invalid_spec = AgentSpecification(
            name="",  # Empty name
            description="",
            type=AgentType.SPECIALIST,
            framework=FrameworkType.COGNITIVE,
            tools=[],  # No tools
            delegation_network=[AgentType.SPECIALIST],  # Self-delegation (might be invalid)
            methodology="test",
            specialization="test",
            capabilities=[],
            usage_patterns=[],
            yaml_content="invalid: yaml: content: ["
        )

        errors = generator.validate_agent_specification(invalid_spec)
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_agent_name_generation(self, generator, security_context, user_responses_security):
        """Test agent name generation."""
        spec = generator.generate_agent_specification(security_context, user_responses_security)

        assert spec.name
        assert "-" in spec.name  # Should contain hyphens
        assert spec.name.startswith("security")  # Should reflect specialization

    def test_specialization_inference(self, generator, complex_context):
        """Test specialization inference from context."""
        user_responses = UserResponses()  # No explicit specialization
        spec = generator.generate_agent_specification(complex_context, user_responses)

        # Should infer from tech stack
        assert spec.specialization
        assert len(spec.specialization) > 0

    def test_capability_generation(self, generator, security_context, user_responses_security):
        """Test capability generation based on tools and context."""
        spec = generator.generate_agent_specification(security_context, user_responses_security)

        assert len(spec.capabilities) > 0

        # Should have basic capabilities
        assert any("Analyze" in cap for cap in spec.capabilities)
        assert any("Python" in cap for cap in spec.capabilities)  # Context-specific

    def test_usage_pattern_generation(self, generator, complex_context):
        """Test usage pattern generation based on context."""
        user_responses = UserResponses()
        spec = generator.generate_agent_specification(complex_context, user_responses)

        assert len(spec.usage_patterns) > 0

        # Complex project should have complex-related patterns
        assert any("complex" in pattern.lower() for pattern in spec.usage_patterns)

    def test_template_preference_override(self, generator, security_context):
        """Test that user template preference overrides automatic selection."""
        user_responses = UserResponses(template_preference=AgentType.TEST)
        template = generator.select_template(security_context, user_responses)

        assert template.type == AgentType.TEST


class TestAgentDataClasses:
    """Test suite for agent-related dataclasses."""

    def test_agent_tool_creation(self):
        """Test AgentTool dataclass creation."""
        tool = AgentTool(
            name="Read",
            description="Read files",
            category="file_operations",
            parameters={"encoding": "utf-8"}
        )

        assert tool.name == "Read"
        assert tool.category == "file_operations"
        assert tool.parameters["encoding"] == "utf-8"

    def test_agent_template_creation(self):
        """Test AgentTemplate dataclass creation."""
        tool = AgentTool("Read", "Read files", "file_operations")
        template = AgentTemplate(
            name="Test Template",
            type=AgentType.SPECIALIST,
            description="Test template",
            framework=FrameworkType.COGNITIVE,
            default_tools=[tool],
            delegation_targets=[AgentType.SECURITY],
            specialization_hint="Test specialization"
        )

        assert template.name == "Test Template"
        assert template.type == AgentType.SPECIALIST
        assert len(template.default_tools) == 1
        assert template.default_tools[0].name == "Read"

    def test_user_responses_creation(self):
        """Test UserResponses dataclass creation."""
        responses = UserResponses(
            responses={"Focus": ["Performance"]},
            mode="smart",
            specialization="Performance Optimization",
            template_preference=AgentType.PERFORMANCE
        )

        assert responses.mode == "smart"
        assert responses.specialization == "Performance Optimization"
        assert responses.template_preference == AgentType.PERFORMANCE

    def test_agent_specification_creation(self):
        """Test AgentSpecification dataclass creation."""
        spec = AgentSpecification(
            name="test-agent",
            description="Test agent",
            type=AgentType.SPECIALIST,
            framework=FrameworkType.COGNITIVE,
            tools=[AgentTool("Read", "Read files", "file_operations")],
            delegation_network=[AgentType.SECURITY],
            methodology="Test methodology",
            specialization="Test specialization",
            capabilities=["Test capability"],
            usage_patterns=["Test pattern"],
            yaml_content="name: test-agent"
        )

        assert spec.name == "test-agent"
        assert spec.type == AgentType.SPECIALIST
        assert len(spec.tools) == 1
        assert spec.yaml_content == "name: test-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])