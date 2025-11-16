#!/usr/bin/env python3
"""
TDD Phase 2: Tests for Smart Question Generator

This test suite follows Test-Driven Development principles.
Tests are written FIRST, then implementation is created to make them pass.

The Smart Question Generator is responsible for:
- Generating contextual questions based on repository context analysis
- Supporting smart mode (2-3 strategic questions maximum)
- Handling different repository types (security-focused, complex, well-documented)
- Creating appropriate question options with multi-select support
- Graceful fallback when context analysis is limited
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

# Import classes from context_analyzer (our TDD implementation)
from context_analyzer import (
    RepositoryContext,
    TechStack,
    CodePatterns,
    SecurityAssessment,
    QualityMetrics
)


@dataclass
class Question:
    """Represents a generated question with metadata."""
    question: str
    header: str
    options: List[Dict[str, str]]
    multiSelect: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary format."""
        return {
            "question": self.question,
            "header": self.header,
            "options": self.options,
            "multiSelect": self.multiSelect
        }


@dataclass
class QuestionGenerationConfig:
    """Configuration for question generation."""
    max_questions: int = 3
    mode: str = "smart"  # smart, fast, interactive
    fallback_enabled: bool = True


class SmartQuestionGenerator:
    """Generates contextual questions based on repository analysis."""

    def __init__(self, config: Optional[QuestionGenerationConfig] = None):
        self.config = config or QuestionGenerationConfig()
        # Initialize skills integration for enhanced question generation
        try:
            from skills_integration import get_skills_integrator
            self.skills_integrator = get_skills_integrator()
        except ImportError:
            self.skills_integrator = None

    def generate_contextual_questions(self, context: RepositoryContext) -> List[Question]:
        """
        Generate contextual questions based on repository context with skill integration.

        Args:
            context: Repository context analysis

        Returns:
            List of generated questions (max 3 for smart mode)
        """
        questions = []

        # Get skill-enhanced template recommendations
        skill_templates = []
        if self.skills_integrator:
            template_result = self.skills_integrator.discover_templates_for_context(context)
            if template_result.success:
                skill_templates = template_result.data

        # Generate template selection question using skill insights
        if skill_templates and len(skill_templates) > 1:
            # Use skill-discovered templates for intelligent template selection
            top_templates = skill_templates[:3]  # Top 3 ranked templates

            template_question = Question(
                question=f"Based on repository analysis, I found {len(skill_templates)} suitable agent templates. The top recommendations are ranked by context relevance.",
                header="Agent Template Selection",
                options=[
                    {
                        "label": f"{template.get('name', 'Unknown')} (Score: {template.get('context_score', 0):.2f})",
                        "description": f"{template.get('description', 'No description')}. Ranking: {', '.join(template.get('ranking_factors', ['General fit']))}"
                    }
                    for template in top_templates
                ],
                multiSelect=False
            )
            questions.append(template_question)

        # Security-focused questions for security repositories (enhanced with skill insights)
        if context.security_assessment.has_security_files:
            # Check if security-specialist template is recommended by skills
            security_template_recommended = any(
                'security' in template.get('tags', []) or
                template.get('name') == 'Specialist'
                for template in skill_templates
            )

            question_text = f"Detected {len(context.security_assessment.security_files)} security file(s) and security score of {context.security_assessment.security_score}/10"
            if security_template_recommended:
                question_text += ". Skill analysis recommends a security-focused approach."

            security_question = Question(
                question=f"{question_text}. What's your primary security priority?",
                header="Security Focus",
                options=[
                    {"label": "Vulnerability Detection", "description": "Find and analyze security issues"},
                    {"label": "Compliance", "description": "Ensure regulatory compliance"},
                    {"label": "DevSecOps Integration", "description": "Security in CI/CD pipelines"}
                ],
                multiSelect=True
            )
            questions.append(security_question)

        # Performance questions for complex applications (enhanced with skill insights)
        if context.code_patterns.complexity_score > 7:
            # Check if orchestrator template is recommended by skills
            orchestrator_recommended = any(
                template.get('name') == 'Orchestrator'
                for template in skill_templates
            )

            question_text = f"High complexity detected ({context.code_patterns.complexity_score}/10)"
            if orchestrator_recommended:
                question_text += ". Skill analysis suggests orchestration capabilities may be valuable."

            performance_question = Question(
                question=f"{question_text}. What's your optimization priority?",
                header="Performance Focus",
                options=[
                    {"label": "Code Quality", "description": "Improve maintainability and readability"},
                    {"label": "Performance", "description": "Optimize speed and resource usage"},
                    {"label": "Testing", "description": "Enhance test coverage and quality"}
                ]
            )
            questions.append(performance_question)

        # Documentation questions for well-documented projects
        if context.quality_metrics.documentation_quality > 7:
            docs_question = Question(
                question="Strong documentation detected. What documentation enhancement do you need?",
                header="Documentation",
                options=[
                    {"label": "API Documentation", "description": "Generate comprehensive API docs"},
                    {"label": "Code Examples", "description": "Create practical usage examples"},
                    {"label": "Architecture Guides", "description": "Document system design and patterns"}
                ]
            )
            questions.append(docs_question)

        # Multi-agent coordination question (inspired by skill template analysis)
        multi_agent_recommended = any(
            'multi-agent' in template.get('tags', []) or
            template.get('name') == 'Orchestrator'
            for template in skill_templates
        )

        if multi_agent_recommended and (len(context.tech_stack.languages) > 1 or context.code_patterns.complexity_score >= 7):
            coordination_question = Question(
                question="Analysis suggests this project could benefit from multi-agent coordination. Would you like to create an orchestrator agent?",
                header="Multi-Agent Coordination",
                options=[
                    {"label": "Yes, create orchestrator", "description": "Coordinate multiple specialized agents"},
                    {"label": "No, prefer specialist", "description": "Focus on single domain expertise"},
                    {"label": "Maybe later", "description": "Start with specialist, evolve to orchestrator"}
                ]
            )
            questions.append(coordination_question)

        # Technology-specific questions (enhanced with skill insights)
        if context.tech_stack.frameworks:
            # Find skill templates relevant to the technology stack
            relevant_templates = [
                template for template in skill_templates
                if any(framework.lower() in template.get('description', '').lower()
                      for framework in context.tech_stack.frameworks)
            ]

            if relevant_templates:
                tech_insight = f" Skill templates found {len(relevant_templates)} relevant options."
            else:
                tech_insight = ""

            tech_question = Question(
                question=f"Detected {', '.join(context.tech_stack.frameworks[:2])} frameworks.{tech_insight} What type of agent assistance do you need?",
                header="Technology Focus",
                options=[
                    {"label": "Framework Optimization", "description": "Best practices and patterns"},
                    {"label": "Integration Support", "description": "API and service integration"},
                    {"label": "Migration Planning", "description": "Version upgrades and migrations"}
                ]
            )
            questions.append(tech_question)

        # Ensure we don't exceed maximum questions
        return questions[:self.config.max_questions]

    def validate_question_relevance(self, question: Question, context: RepositoryContext) -> bool:
        """
        Validate if a question is relevant for the given context.

        Args:
            question: Question to validate
            context: Repository context

        Returns:
            True if question is relevant, False otherwise
        """
        # Basic validation - question should have proper structure
        if not question.question or not question.header or not question.options:
            return False

        # Check if question options are well-formed
        for option in question.options:
            if not isinstance(option, dict) or 'label' not in option or 'description' not in option:
                return False

        return True

    def prioritize_questions(self, questions: List[Question]) -> List[Question]:
        """
        Prioritize questions based on relevance and importance.

        Args:
            questions: List of questions to prioritize

        Returns:
            Prioritized list of questions
        """
        # Security questions get highest priority
        security_questions = [q for q in questions if 'security' in q.header.lower()]

        # Performance questions for complex projects get high priority
        performance_questions = [q for q in questions if 'performance' in q.header.lower()]

        # Other questions
        other_questions = [q for q in questions if q not in security_questions and q not in performance_questions]

        # Return prioritized list
        return (security_questions + performance_questions + other_questions)[:self.config.max_questions]


class TestSmartQuestionGenerator:
    """Test suite for Smart Question Generator using TDD methodology."""

    @pytest.fixture
    def generator(self):
        """Create a default question generator."""
        return SmartQuestionGenerator()

    @pytest.fixture
    def limited_generator(self):
        """Create a generator with limited questions."""
        config = QuestionGenerationConfig(max_questions=2)
        return SmartQuestionGenerator(config)

    @pytest.fixture
    def security_focused_context(self):
        """Create a security-focused repository context."""
        tech_stack = TechStack(
            languages=["Python"],
            frameworks=["Flask"],
            databases=[],
            build_tools=[],
            testing_frameworks=["pytest"],
            package_managers=["pip"],
            cloud_platforms=[]
        )

        code_patterns = CodePatterns(
            architectural_patterns=["MVC"],
            design_patterns=["Singleton"],
            organization_structure="src-based",
            development_methodology="DevOps",
            complexity_score=6,
            maintainability_index=75
        )

        security_assessment = SecurityAssessment(
            has_security_files=True,
            security_files=["SECURITY.md", ".snyk", "bandit.yaml"],
            vulnerability_tools=["Snyk", "Bandit"],
            compliance_frameworks=["GDPR"],
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
            total_files=25,
            dominant_language="Python"
        )

    @pytest.fixture
    def complex_project_context(self):
        """Create a complex project repository context."""
        tech_stack = TechStack(
            languages=["Python", "JavaScript"],
            frameworks=["Django", "React"],
            databases=["PostgreSQL", "Redis"],
            build_tools=["Docker", "Webpack"],
            testing_frameworks=["pytest", "Jest"],
            package_managers=["pip", "npm"],
            cloud_platforms=["AWS"]
        )

        code_patterns = CodePatterns(
            architectural_patterns=["Microservices", "Event-Driven"],
            design_patterns=["Factory", "Observer", "Strategy"],
            organization_structure="src-based",
            development_methodology="DevOps",
            complexity_score=9,  # High complexity
            maintainability_index=45
        )

        security_assessment = SecurityAssessment(
            has_security_files=False,
            security_files=[],
            vulnerability_tools=[],
            compliance_frameworks=[],
            security_score=4
        )

        quality_metrics = QualityMetrics(
            test_coverage_score=8,
            documentation_quality=7,
            code_complexity=9,  # High complexity
            error_handling_quality=6,
            performance_score=5
        )

        return RepositoryContext(
            path="/test/complex-project",
            name="complex-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=150,
            dominant_language="Python"
        )

    @pytest.fixture
    def well_documented_context(self):
        """Create a well-documented repository context."""
        tech_stack = TechStack(
            languages=["Python"],
            frameworks=["Flask"],
            databases=["SQLite"],
            build_tools=[],
            testing_frameworks=["pytest"],
            package_managers=["pip"],
            cloud_platforms=[]
        )

        code_patterns = CodePatterns(
            architectural_patterns=["MVC"],
            design_patterns=["Repository"],
            organization_structure="src-based",
            development_methodology="Documentation-First",
            complexity_score=4,
            maintainability_index=85
        )

        security_assessment = SecurityAssessment(
            has_security_files=False,
            security_files=[],
            vulnerability_tools=[],
            compliance_frameworks=[],
            security_score=5
        )

        quality_metrics = QualityMetrics(
            test_coverage_score=6,
            documentation_quality=9,  # High documentation quality
            code_complexity=4,
            error_handling_quality=7,
            performance_score=7
        )

        return RepositoryContext(
            path="/test/well-documented-project",
            name="well-documented-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=35,
            dominant_language="Python"
        )

    @pytest.fixture
    def minimal_context(self):
        """Create a minimal repository context."""
        tech_stack = TechStack([], [], [], [], [], [], [])
        code_patterns = CodePatterns([], [], "", "", 5, 50)
        security_assessment = SecurityAssessment(False, [], [], [], 5)
        quality_metrics = QualityMetrics(0, 0, 5, 5, 5)

        return RepositoryContext(
            path="/test/minimal-project",
            name="minimal-project",
            tech_stack=tech_stack,
            code_patterns=code_patterns,
            security_assessment=security_assessment,
            quality_metrics=quality_metrics,
            total_files=1,
            dominant_language="Python"
        )

    def test_generator_initialization(self):
        """Test question generator initialization."""
        # Default config
        generator = SmartQuestionGenerator()
        assert generator.config.max_questions == 3
        assert generator.config.mode == "smart"
        assert generator.config.fallback_enabled is True

        # Custom config
        config = QuestionGenerationConfig(max_questions=5, mode="interactive")
        generator = SmartQuestionGenerator(config)
        assert generator.config.max_questions == 5
        assert generator.config.mode == "interactive"

    def test_generate_security_focused_questions(self, generator, security_focused_context):
        """Test question generation for security-focused projects."""
        questions = generator.generate_contextual_questions(security_focused_context)

        # Should generate at least one security question
        assert len(questions) >= 1

        # Check for security-specific question
        security_questions = [q for q in questions if 'security' in q.header.lower()]
        assert len(security_questions) >= 1

        security_question = security_questions[0]
        assert 'security' in security_question.question.lower()
        assert security_question.header == "Security Focus"
        assert len(security_question.options) == 3
        assert security_question.multiSelect is True

        # Check option structure
        option_labels = [opt['label'] for opt in security_question.options]
        expected_labels = ["Vulnerability Detection", "Compliance", "DevSecOps Integration"]
        for label in expected_labels:
            assert label in option_labels

    def test_generate_complex_project_questions(self, generator, complex_project_context):
        """Test question generation for complex projects."""
        questions = generator.generate_contextual_questions(complex_project_context)

        # Should generate performance question for high complexity
        performance_questions = [q for q in questions if 'performance' in q.header.lower()]
        assert len(performance_questions) >= 1

        performance_question = performance_questions[0]
        assert 'complexity' in performance_question.question.lower()
        assert performance_question.header == "Performance Focus"
        assert len(performance_question.options) == 3

        # Should generate technology question for multiple frameworks (if not limited by max_questions)
        tech_questions = [q for q in questions if 'technology' in q.header.lower()]
        # Note: With skills integration and max_questions limit, technology question might be replaced by higher-priority questions
        # Check for either technology question OR other relevant questions (template selection, coordination)
        relevant_questions = [q for q in questions if any(keyword in q.header.lower()
                             for keyword in ['technology', 'coordination', 'template'])]
        assert len(relevant_questions) >= 1

    def test_generate_well_documented_questions(self, generator, well_documented_context):
        """Test question generation for well-documented projects."""
        questions = generator.generate_contextual_questions(well_documented_context)

        # Should generate documentation question
        doc_questions = [q for q in questions if 'documentation' in q.header.lower()]
        assert len(doc_questions) >= 1

        doc_question = doc_questions[0]
        assert doc_question.header == "Documentation"
        assert len(doc_question.options) == 3

        # Check documentation options
        option_labels = [opt['label'] for opt in doc_question.options]
        expected_labels = ["API Documentation", "Code Examples", "Architecture Guides"]
        for label in expected_labels:
            assert label in option_labels

    def test_max_questions_limit(self, limited_generator, complex_project_context):
        """Test that question generator respects maximum questions limit."""
        questions = limited_generator.generate_contextual_questions(complex_project_context)

        # Should not exceed max_questions (2)
        assert len(questions) <= 2

    def test_minimal_context_fallback(self, generator, minimal_context):
        """Test graceful fallback for minimal repository contexts."""
        questions = generator.generate_contextual_questions(minimal_context)

        # Should handle minimal context gracefully
        assert isinstance(questions, list)
        # May return empty list or very basic questions

        # Should not crash and should return valid format
        for question in questions:
            assert isinstance(question, Question)

    def test_question_validation(self, generator, security_focused_context):
        """Test question relevance validation."""
        questions = generator.generate_contextual_questions(security_focused_context)

        for question in questions:
            # Each question should be relevant
            assert generator.validate_question_relevance(question, security_focused_context)

            # Check question structure
            assert isinstance(question.question, str)
            assert len(question.question) > 0
            assert isinstance(question.header, str)
            assert len(question.header) > 0
            assert isinstance(question.options, list)
            assert len(question.options) > 0

            # Check option structure
            for option in question.options:
                assert isinstance(option, dict)
                assert 'label' in option
                assert 'description' in option
                assert len(option['label']) > 0
                assert len(option['description']) > 0

    def test_question_prioritization(self, generator, complex_project_context):
        """Test question prioritization logic."""
        # Generate questions
        questions = generator.generate_contextual_questions(complex_project_context)

        # Prioritize them
        prioritized = generator.prioritize_questions(questions)

        # Should return valid list
        assert isinstance(prioritized, list)
        assert len(prioritized) <= generator.config.max_questions

        # Security questions should come first (if any exist)
        # This test depends on the specific context having security files
        # For complex_project_context, no security files = no security questions

    def test_question_to_dict_conversion(self):
        """Test Question to dictionary conversion."""
        question = Question(
            question="Test question?",
            header="Test",
            options=[{"label": "Option 1", "description": "Description 1"}],
            multiSelect=False
        )

        question_dict = question.to_dict()

        assert question_dict['question'] == "Test question?"
        assert question_dict['header'] == "Test"
        assert question_dict['multiSelect'] is False
        assert len(question_dict['options']) == 1
        assert question_dict['options'][0]['label'] == "Option 1"

    def test_empty_questions_list_handling(self, generator):
        """Test handling of empty questions list."""
        empty_questions = []
        prioritized = generator.prioritize_questions(empty_questions)

        assert isinstance(prioritized, list)
        assert len(prioritized) == 0

    def test_invalid_question_options(self, generator):
        """Test validation of questions with invalid options."""
        invalid_question = Question(
            question="Test?",
            header="Test",
            options=[{"bad_option": "missing_label"}],  # Invalid option structure
            multiSelect=False
        )

        context = RepositoryContext(
            path="/test",
            name="test",
            tech_stack=TechStack([], [], [], [], [], [], []),
            code_patterns=CodePatterns([], [], "", "", 5, 50),
            security_assessment=SecurityAssessment(False, [], [], [], 5),
            quality_metrics=QualityMetrics(0, 0, 5, 5, 5),
            total_files=1,
            dominant_language="Python"
        )

        # Should detect invalid question
        assert not generator.validate_question_relevance(invalid_question, context)


class TestQuestionGenerationConfig:
    """Test suite for QuestionGenerationConfig dataclass."""

    def test_config_creation(self):
        """Test config creation with default values."""
        config = QuestionGenerationConfig()

        assert config.max_questions == 3
        assert config.mode == "smart"
        assert config.fallback_enabled is True

    def test_config_custom_values(self):
        """Test config creation with custom values."""
        config = QuestionGenerationConfig(
            max_questions=5,
            mode="interactive",
            fallback_enabled=False
        )

        assert config.max_questions == 5
        assert config.mode == "interactive"
        assert config.fallback_enabled is False


class TestQuestionDataclass:
    """Test suite for Question dataclass."""

    def test_question_creation(self):
        """Test question creation and attributes."""
        options = [
            {"label": "Option 1", "description": "First option"},
            {"label": "Option 2", "description": "Second option"}
        ]

        question = Question(
            question="What is your preference?",
            header="Preferences",
            options=options,
            multiSelect=True
        )

        assert question.question == "What is your preference?"
        assert question.header == "Preferences"
        assert question.options == options
        assert question.multiSelect is True
        assert len(question.options) == 2

    def test_question_defaults(self):
        """Test question creation with default values."""
        question = Question(
            question="Test?",
            header="Test",
            options=[{"label": "Opt", "description": "Desc"}]
        )

        # multiSelect should default to False
        assert question.multiSelect is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])