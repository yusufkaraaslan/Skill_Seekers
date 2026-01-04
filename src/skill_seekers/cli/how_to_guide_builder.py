#!/usr/bin/env python3
"""
How-To Guide Builder (C3.3) - Build step-by-step guides from workflow examples

Transforms multi-step test workflows (from C3.2) into educational "how to" guides with:
- Step-by-step breakdowns
- Prerequisites and setup requirements
- Verification checkpoints
- Troubleshooting sections
- Complexity levels (beginner/intermediate/advanced)

Usage:
    # From test examples JSON
    skill-seekers build-how-to-guides --input test_examples.json

    # From directory (auto-extracts workflows)
    skill-seekers build-how-to-guides tests/

    # With AI enhancement
    skill-seekers build-how-to-guides tests/ --enhance-with-ai

Example workflow → guide transformation:
    Input:  Multi-step test showing user registration + login + session
    Output: "How To: Complete User Authentication" guide with:
            - 5 discrete steps with explanations
            - Prerequisites (database, email service)
            - Verification points at each step
            - Common pitfalls and troubleshooting
            - Related guides suggestions
"""

import ast
import re
import json
import logging
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal, Tuple, Set
from pathlib import Path
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PrerequisiteItem:
    """Enhanced prerequisite with explanation (AI enhancement)"""
    name: str
    why: str  # Why this is needed
    setup: str  # How to install/configure


@dataclass
class TroubleshootingItem:
    """Enhanced troubleshooting with solutions (AI enhancement)"""
    problem: str
    symptoms: List[str] = field(default_factory=list)  # How to recognize this issue
    solution: str = ""  # Step-by-step fix
    diagnostic_steps: List[str] = field(default_factory=list)  # How to diagnose


@dataclass
class WorkflowStep:
    """Single step in a workflow guide"""
    step_number: int
    code: str
    description: str
    expected_result: Optional[str] = None
    verification: Optional[str] = None  # Assertion or checkpoint
    setup_required: Optional[str] = None
    explanation: Optional[str] = None  # Why this step matters
    common_pitfall: Optional[str] = None  # Warning for this step
    common_variations: List[str] = field(default_factory=list)  # AI: Alternative approaches


@dataclass
class HowToGuide:
    """Complete how-to guide generated from workflow(s)"""
    guide_id: str
    title: str
    overview: str
    complexity_level: Literal["beginner", "intermediate", "advanced"]

    # Prerequisites
    prerequisites: List[str] = field(default_factory=list)
    required_imports: List[str] = field(default_factory=list)
    required_fixtures: List[str] = field(default_factory=list)

    # Content
    workflows: List[Dict] = field(default_factory=list)  # Source workflow examples
    steps: List[WorkflowStep] = field(default_factory=list)

    # Metadata
    use_case: str = ""
    tags: List[str] = field(default_factory=list)
    estimated_time: str = "10 minutes"
    source_files: List[str] = field(default_factory=list)

    # Optional AI enhancement (basic)
    common_pitfalls: List[str] = field(default_factory=list)
    troubleshooting: Dict[str, str] = field(default_factory=dict)
    variations: List[str] = field(default_factory=list)
    related_guides: List[str] = field(default_factory=list)

    # AI enhancement (comprehensive - NEW)
    prerequisites_detailed: List[PrerequisiteItem] = field(default_factory=list)
    troubleshooting_detailed: List[TroubleshootingItem] = field(default_factory=list)
    next_steps_detailed: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        # Convert WorkflowStep objects to dicts
        result['steps'] = [asdict(step) for step in self.steps]
        return result


@dataclass
class GuideCollection:
    """Collection of guides organized by category"""
    total_guides: int
    guides_by_complexity: Dict[str, int]
    guides_by_use_case: Dict[str, List[HowToGuide]]
    guides: List[HowToGuide]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'total_guides': self.total_guides,
            'guides_by_complexity': self.guides_by_complexity,
            'guides_by_use_case': {
                k: [g.to_dict() for g in v]
                for k, v in self.guides_by_use_case.items()
            },
            'guides': [g.to_dict() for g in self.guides]
        }


# ============================================================================
# WORKFLOW ANALYZER
# ============================================================================

class WorkflowAnalyzer:
    """Analyze workflow examples to extract steps and metadata"""

    def analyze_workflow(self, workflow: Dict) -> Tuple[List[WorkflowStep], Dict]:
        """
        Deep analysis of workflow structure.

        Args:
            workflow: TestExample dict from C3.2

        Returns:
            (steps, metadata) where metadata includes prerequisites, complexity, etc.
        """
        code = workflow.get('code', '')
        language = workflow.get('language', 'python').lower()

        # Extract steps based on language
        if language == 'python':
            steps = self._extract_steps_python(code, workflow)
        else:
            steps = self._extract_steps_heuristic(code, workflow)

        # Detect prerequisites
        metadata = self._detect_prerequisites(workflow)

        # Find verification points
        verifications = self._find_verification_points(code)

        # Associate verifications with steps
        for i, step in enumerate(steps):
            if i < len(verifications):
                step.verification = verifications[i]

        # Calculate complexity
        metadata['complexity_level'] = self._calculate_complexity(steps, workflow)
        metadata['estimated_time'] = self._estimate_time(steps)

        return steps, metadata

    def _extract_steps_python(self, code: str, workflow: Dict) -> List[WorkflowStep]:
        """Extract steps from Python code using AST"""
        steps = []

        try:
            tree = ast.parse(code)
            statements = []

            # Collect all statements
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.Expr, ast.Assert)):
                    statements.append(node)

            step_num = 1
            for stmt in statements:
                # Skip assertions for now (they're verifications)
                if isinstance(stmt, ast.Assert):
                    continue

                # Get code for this statement
                step_code = ast.get_source_segment(code, stmt)
                if not step_code:
                    continue

                # Generate description from code
                description = self._generate_step_description(stmt, step_code)

                # Check if next statement is assertion (verification)
                idx = statements.index(stmt)
                verification = None
                if idx + 1 < len(statements) and isinstance(statements[idx + 1], ast.Assert):
                    verification = ast.get_source_segment(code, statements[idx + 1])

                steps.append(WorkflowStep(
                    step_number=step_num,
                    code=step_code,
                    description=description,
                    verification=verification
                ))
                step_num += 1

        except SyntaxError:
            # Fall back to heuristic method
            return self._extract_steps_heuristic(code, workflow)

        return steps

    def _extract_steps_heuristic(self, code: str, workflow: Dict) -> List[WorkflowStep]:
        """Extract steps using heuristics (for non-Python or invalid syntax)"""
        steps = []
        lines = code.split('\n')

        current_step = []
        step_num = 1

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith('#'):
                if current_step:
                    # End of current step
                    step_code = '\n'.join(current_step)
                    description = self._infer_description_from_code(step_code)

                    steps.append(WorkflowStep(
                        step_number=step_num,
                        code=step_code,
                        description=description
                    ))
                    step_num += 1
                    current_step = []
                continue

            current_step.append(line)

        # Add final step
        if current_step:
            step_code = '\n'.join(current_step)
            description = self._infer_description_from_code(step_code)
            steps.append(WorkflowStep(
                step_number=step_num,
                code=step_code,
                description=description
            ))

        return steps

    def _generate_step_description(self, node: ast.AST, code: str) -> str:
        """Generate human-readable description from AST node"""
        if isinstance(node, ast.Assign):
            targets = [self._get_name(t) for t in node.targets]
            value_desc = self._describe_value(node.value)
            return f"Assign {', '.join(targets)} = {value_desc}"

        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                func_name = self._get_name(node.value.func)
                return f"Call {func_name}()"

        return code.split('\n')[0]  # First line as fallback

    def _describe_value(self, node: ast.AST) -> str:
        """Describe AST value node"""
        if isinstance(node, ast.Call):
            func_name = self._get_name(node.func)
            return f"{func_name}(...)"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        return "value"

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return "unknown"

    def _infer_description_from_code(self, code: str) -> str:
        """Infer description from code using patterns"""
        code = code.strip()

        # Method call patterns
        if '(' in code and ')' in code:
            match = re.search(r'(\w+)\s*\(', code)
            if match:
                return f"Call {match.group(1)}()"

        # Assignment patterns
        if '=' in code and not code.startswith('assert'):
            parts = code.split('=', 1)
            var_name = parts[0].strip()
            return f"Create {var_name}"

        # Assertion patterns
        if code.startswith('assert'):
            return "Verify result"

        return code.split('\n')[0]  # First line

    def _detect_prerequisites(self, workflow: Dict) -> Dict:
        """Detect prerequisites from workflow"""
        metadata = {
            'prerequisites': [],
            'required_imports': [],
            'required_fixtures': []
        }

        # Get dependencies from workflow
        dependencies = workflow.get('dependencies', [])
        metadata['required_imports'] = dependencies

        # Get setup code
        setup_code = workflow.get('setup_code')
        if setup_code:
            metadata['prerequisites'].append("Setup code must be executed first")

        # Check for common fixtures in test name or setup
        test_name = workflow.get('test_name', '').lower()
        if 'database' in test_name or (setup_code and 'database' in setup_code.lower()):
            metadata['required_fixtures'].append('database')
        if 'api' in test_name or (setup_code and 'api' in setup_code.lower()):
            metadata['required_fixtures'].append('api_client')

        return metadata

    def _find_verification_points(self, code: str) -> List[str]:
        """Find assertion statements in code"""
        verifications = []

        for line in code.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('assert'):
                verifications.append(line_stripped)

        return verifications

    def _calculate_complexity(self, steps: List[WorkflowStep], workflow: Dict) -> str:
        """Calculate complexity level"""
        num_steps = len(steps)

        # Check for advanced patterns
        code = workflow.get('code', '')
        has_async = 'async' in code or 'await' in code
        has_mock = 'mock' in code.lower() or 'patch' in code.lower()
        has_error_handling = 'try' in code or 'except' in code

        complexity_score = workflow.get('complexity_score', 0.5)

        # Determine level
        if num_steps <= 3 and not has_async and not has_mock:
            return "beginner"
        elif num_steps >= 8 or has_async or has_error_handling:
            return "advanced"
        else:
            return "intermediate"

    def _estimate_time(self, steps: List[WorkflowStep]) -> str:
        """Estimate time to complete guide"""
        num_steps = len(steps)

        if num_steps <= 3:
            return "5 minutes"
        elif num_steps <= 6:
            return "10 minutes"
        elif num_steps <= 10:
            return "15 minutes"
        else:
            return "20 minutes"


# ============================================================================
# WORKFLOW GROUPER
# ============================================================================

class WorkflowGrouper:
    """Group related workflows into coherent guides"""

    def group_workflows(
        self,
        workflows: List[Dict],
        strategy: str = "ai-tutorial-group"
    ) -> Dict[str, List[Dict]]:
        """
        Group workflows using specified strategy.

        Args:
            workflows: List of workflow examples
            strategy: "ai-tutorial-group", "file-path", "test-name", "complexity"

        Returns:
            Dict mapping group name to list of workflows
        """
        if strategy == "ai-tutorial-group":
            return self._group_by_ai_tutorial_group(workflows)
        elif strategy == "file-path":
            return self._group_by_file_path(workflows)
        elif strategy == "test-name":
            return self._group_by_test_name(workflows)
        elif strategy == "complexity":
            return self._group_by_complexity(workflows)
        else:
            # Default: AI tutorial group with fallback
            groups = self._group_by_ai_tutorial_group(workflows)
            if not groups or len(groups) == len(workflows):
                # Fallback to file path if AI grouping didn't work well
                groups = self._group_by_file_path(workflows)
            return groups

    def _group_by_ai_tutorial_group(self, workflows: List[Dict]) -> Dict[str, List[Dict]]:
        """Group by AI-generated tutorial_group (from C3.6 enhancement)"""
        groups = defaultdict(list)
        ungrouped = []

        for workflow in workflows:
            ai_analysis = workflow.get('ai_analysis', {})
            tutorial_group = ai_analysis.get('tutorial_group')

            if tutorial_group:
                groups[tutorial_group].append(workflow)
            else:
                ungrouped.append(workflow)

        # Put ungrouped workflows in individual guides
        for workflow in ungrouped:
            test_name = workflow.get('test_name', 'Unknown')
            # Clean test name for title
            title = self._clean_test_name(test_name)
            groups[title] = [workflow]

        return dict(groups)

    def _group_by_file_path(self, workflows: List[Dict]) -> Dict[str, List[Dict]]:
        """Group workflows from same test file"""
        groups = defaultdict(list)

        for workflow in workflows:
            file_path = workflow.get('file_path', '')
            # Extract meaningful name from file path
            file_name = Path(file_path).stem if file_path else 'Unknown'
            # Remove test_ prefix
            group_name = file_name.replace('test_', '').replace('_', ' ').title()
            groups[group_name].append(workflow)

        return dict(groups)

    def _group_by_test_name(self, workflows: List[Dict]) -> Dict[str, List[Dict]]:
        """Group by common test name prefixes"""
        groups = defaultdict(list)

        for workflow in workflows:
            test_name = workflow.get('test_name', '')
            # Extract prefix (e.g., test_auth_login → auth)
            prefix = self._extract_prefix(test_name)
            groups[prefix].append(workflow)

        return dict(groups)

    def _group_by_complexity(self, workflows: List[Dict]) -> Dict[str, List[Dict]]:
        """Group by complexity level"""
        groups = {
            'Beginner': [],
            'Intermediate': [],
            'Advanced': []
        }

        for workflow in workflows:
            complexity_score = workflow.get('complexity_score', 0.5)

            if complexity_score < 0.4:
                groups['Beginner'].append(workflow)
            elif complexity_score < 0.7:
                groups['Intermediate'].append(workflow)
            else:
                groups['Advanced'].append(workflow)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def _clean_test_name(self, test_name: str) -> str:
        """Clean test name to readable title"""
        # Remove test_ prefix
        name = test_name.replace('test_', '')
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Title case
        return name.title()

    def _extract_prefix(self, test_name: str) -> str:
        """Extract prefix from test name"""
        # Remove test_ prefix
        name = test_name.replace('test_', '')
        # Get first part before underscore
        parts = name.split('_')
        if len(parts) > 1:
            return parts[0].title()
        return self._clean_test_name(test_name)


# ============================================================================
# GUIDE GENERATOR
# ============================================================================

class GuideGenerator:
    """Generate markdown guides from workflow data"""

    def generate_guide_markdown(self, guide: HowToGuide) -> str:
        """
        Generate complete markdown guide.

        Args:
            guide: HowToGuide object with all data

        Returns:
            Complete markdown string
        """
        sections = []

        # Header
        sections.append(self._create_header(guide))

        # Overview
        sections.append(self._create_overview(guide))

        # Prerequisites
        if guide.prerequisites or guide.required_imports or guide.required_fixtures:
            sections.append(self._create_prerequisites(guide))

        # Step-by-step guide
        sections.append(self._create_steps_section(guide.steps))

        # Complete example
        sections.append(self._create_complete_example(guide))

        # Troubleshooting (if available)
        if guide.common_pitfalls or guide.troubleshooting:
            sections.append(self._create_troubleshooting(guide))

        # Next steps and related guides
        sections.append(self._create_next_steps(guide))

        # Footer
        sections.append(self._create_footer(guide))

        return '\n\n'.join(sections)

    def _create_header(self, guide: HowToGuide) -> str:
        """Create guide header with metadata"""
        lines = [f"# How To: {guide.title}"]
        lines.append("")
        lines.append(f"**Difficulty**: {guide.complexity_level.title()}")
        lines.append(f"**Estimated Time**: {guide.estimated_time}")

        if guide.tags:
            lines.append(f"**Tags**: {', '.join(guide.tags)}")

        return '\n'.join(lines)

    def _create_overview(self, guide: HowToGuide) -> str:
        """Create overview section"""
        return f"## Overview\n\n{guide.overview}"

    def _create_prerequisites(self, guide: HowToGuide) -> str:
        """Create prerequisites section"""
        lines = ["## Prerequisites"]
        lines.append("")

        # Checklist format
        if guide.prerequisites:
            for prereq in guide.prerequisites:
                lines.append(f"- [ ] {prereq}")
            lines.append("")

        # Required imports
        if guide.required_imports:
            lines.append("**Required Modules:**")
            for imp in guide.required_imports:
                lines.append(f"- `{imp}`")
            lines.append("")

        # Required fixtures
        if guide.required_fixtures:
            lines.append("**Required Fixtures:**")
            for fixture in guide.required_fixtures:
                lines.append(f"- `{fixture}` fixture")
            lines.append("")

        # Setup code if available
        if guide.workflows and guide.workflows[0].get('setup_code'):
            setup_code = guide.workflows[0]['setup_code']
            lines.append("**Setup Required:**")
            lines.append("```python")
            lines.append(setup_code)
            lines.append("```")

        return '\n'.join(lines)

    def _create_steps_section(self, steps: List[WorkflowStep]) -> str:
        """Create step-by-step guide section"""
        lines = ["## Step-by-Step Guide"]
        lines.append("")

        for step in steps:
            lines.append(f"### Step {step.step_number}: {step.description}")
            lines.append("")

            # Explanation if available
            if step.explanation:
                lines.append(f"**What you're doing:** {step.explanation}")
                lines.append("")

            # Code
            lines.append("```python")
            lines.append(step.code)
            lines.append("```")
            lines.append("")

            # Expected result
            if step.expected_result:
                lines.append(f"**Expected Result:** {step.expected_result}")
                lines.append("")

            # Verification checkpoint
            if step.verification:
                lines.append(f"**Verification:**")
                lines.append("```python")
                lines.append(step.verification)
                lines.append("```")
                lines.append("")

            # Common pitfall warning
            if step.common_pitfall:
                lines.append(f"⚠️ **Common Pitfall:** {step.common_pitfall}")
                lines.append("")

        return '\n'.join(lines)

    def _create_complete_example(self, guide: HowToGuide) -> str:
        """Create complete working example"""
        lines = ["## Complete Example"]
        lines.append("")
        lines.append("```python")

        # If we have workflows, use the first one's code
        if guide.workflows:
            workflow = guide.workflows[0]

            # Add setup code if present
            if workflow.get('setup_code'):
                lines.append("# Setup")
                lines.append(workflow['setup_code'])
                lines.append("")

            # Add main workflow code
            lines.append("# Workflow")
            lines.append(workflow.get('code', ''))
        else:
            # Combine all steps
            for step in guide.steps:
                lines.append(f"# Step {step.step_number}: {step.description}")
                lines.append(step.code)
                if step.verification:
                    lines.append(step.verification)
                lines.append("")

        lines.append("```")
        return '\n'.join(lines)

    def _create_troubleshooting(self, guide: HowToGuide) -> str:
        """Create troubleshooting section"""
        lines = ["## Troubleshooting"]
        lines.append("")

        # Common pitfalls
        if guide.common_pitfalls:
            lines.append("### Common Issues")
            lines.append("")
            for i, pitfall in enumerate(guide.common_pitfalls, 1):
                lines.append(f"{i}. {pitfall}")
            lines.append("")

        # Specific troubleshooting
        if guide.troubleshooting:
            for problem, solution in guide.troubleshooting.items():
                lines.append(f"### Problem: {problem}")
                lines.append("")
                lines.append(f"**Solution:** {solution}")
                lines.append("")

        return '\n'.join(lines)

    def _create_next_steps(self, guide: HowToGuide) -> str:
        """Create next steps and related guides"""
        lines = ["## Next Steps"]
        lines.append("")

        # Variations if available
        if guide.variations:
            lines.append("**Try these variations:**")
            for variation in guide.variations:
                lines.append(f"- {variation}")
            lines.append("")

        # Related guides
        if guide.related_guides:
            lines.append("## Related Guides")
            lines.append("")
            for related in guide.related_guides:
                lines.append(f"- [{related}]")
            lines.append("")

        return '\n'.join(lines)

    def _create_footer(self, guide: HowToGuide) -> str:
        """Create guide footer with metadata"""
        source_info = []
        if guide.source_files:
            source_info.append(f"Source: {', '.join(guide.source_files)}")
        source_info.append(f"Complexity: {guide.complexity_level.title()}")
        source_info.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")

        return f"---\n\n*{' | '.join(source_info)}*"

    def generate_index(self, guides: List[HowToGuide]) -> str:
        """
        Generate index/TOC markdown.

        Args:
            guides: List of all guides

        Returns:
            Index markdown string
        """
        lines = ["# How-To Guides Index"]
        lines.append("")
        lines.append(f"**Total Guides**: {len(guides)}")
        lines.append(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")

        # Group by use case
        by_use_case = defaultdict(list)
        for guide in guides:
            use_case = guide.use_case or "Other"
            by_use_case[use_case].append(guide)

        lines.append("## By Use Case")
        lines.append("")

        for use_case in sorted(by_use_case.keys()):
            case_guides = by_use_case[use_case]
            lines.append(f"### {use_case} ({len(case_guides)} guides)")
            for guide in sorted(case_guides, key=lambda g: g.complexity_level):
                # Create filename from guide title
                filename = guide.title.lower().replace(' ', '-').replace(':', '')
                lines.append(f"- [How To: {guide.title}]({use_case.lower()}/{filename}.md) - {guide.complexity_level.title()}")
            lines.append("")

        # Group by difficulty
        by_complexity = defaultdict(list)
        for guide in guides:
            by_complexity[guide.complexity_level].append(guide)

        lines.append("## By Difficulty Level")
        lines.append("")

        for level in ['beginner', 'intermediate', 'advanced']:
            if level in by_complexity:
                level_guides = by_complexity[level]
                lines.append(f"### {level.title()} ({len(level_guides)} guides)")
                for guide in sorted(level_guides, key=lambda g: g.title):
                    lines.append(f"- {guide.title}")
                lines.append("")

        return '\n'.join(lines)


# ============================================================================
# HOW-TO GUIDE BUILDER (Main Orchestrator)
# ============================================================================

class HowToGuideBuilder:
    """Main orchestrator for building how-to guides from workflow examples"""

    def __init__(self, enhance_with_ai: bool = True):
        """
        Initialize guide builder.

        Args:
            enhance_with_ai: Enable AI enhancement (requires C3.6 AI analysis in workflows)
        """
        self.enhance_with_ai = enhance_with_ai
        self.analyzer = WorkflowAnalyzer()
        self.grouper = WorkflowGrouper()
        self.generator = GuideGenerator()

    def build_guides_from_examples(
        self,
        examples: List[Dict],
        grouping_strategy: str = "ai-tutorial-group",
        output_dir: Optional[Path] = None,
        enhance_with_ai: bool = True,
        ai_mode: str = "auto"
    ) -> GuideCollection:
        """
        Main entry point - build guides from workflow examples.

        Args:
            examples: List of TestExample dicts from C3.2
            grouping_strategy: How to group workflows ("ai-tutorial-group", "file-path", etc.)
            output_dir: Optional directory to save markdown files
            enhance_with_ai: Enable comprehensive AI enhancement (default: True)
            ai_mode: AI enhancement mode - "auto", "api", "local", or "none"

        Returns:
            GuideCollection with all generated guides
        """
        logger.info(f"Building how-to guides from {len(examples)} examples...")

        # Initialize AI enhancer if requested
        enhancer = None
        if enhance_with_ai and ai_mode != "none":
            try:
                from .guide_enhancer import GuideEnhancer
                enhancer = GuideEnhancer(mode=ai_mode)
                logger.info(f"✨ AI enhancement enabled (mode: {enhancer.mode})")
            except Exception as e:
                logger.warning(f"⚠️  AI enhancement unavailable: {e}")
                logger.info("📝 Falling back to basic guide generation")

        # Filter to workflow examples only
        workflows = self._extract_workflow_examples(examples)
        logger.info(f"Found {len(workflows)} workflow examples")

        if not workflows:
            logger.warning("No workflow examples found!")
            return GuideCollection(
                total_guides=0,
                guides_by_complexity={},
                guides_by_use_case={},
                guides=[]
            )

        # Group workflows
        grouped_workflows = self.grouper.group_workflows(workflows, grouping_strategy)
        logger.info(f"Grouped into {len(grouped_workflows)} guide categories")

        # Build guides
        guides = []
        for title, workflow_group in grouped_workflows.items():
            guide = self._create_guide(title, workflow_group, enhancer)
            guides.append(guide)

        # Create collection
        collection = self._create_collection(guides)

        # Save to files if output directory provided
        if output_dir:
            self._save_guides_to_files(collection, output_dir)

        logger.info(f"✅ Generated {len(guides)} how-to guides")
        return collection

    def _extract_workflow_examples(self, examples: List[Dict]) -> List[Dict]:
        """Filter to workflow category only"""
        return [ex for ex in examples if ex.get('category') == 'workflow']

    def _create_guide(self, title: str, workflows: List[Dict], enhancer=None) -> HowToGuide:
        """
        Generate single guide from workflow(s).

        Args:
            title: Guide title
            workflows: List of related workflow examples
            enhancer: Optional GuideEnhancer instance for AI enhancement

        Returns:
            Complete HowToGuide object
        """
        # Use first workflow as primary
        primary_workflow = workflows[0]

        # Analyze workflow to extract steps
        steps, metadata = self.analyzer.analyze_workflow(primary_workflow)

        # Generate guide ID
        guide_id = hashlib.md5(title.encode()).hexdigest()[:12]

        # Extract use case from AI analysis or title
        use_case = title
        if primary_workflow.get('ai_analysis'):
            use_case = primary_workflow['ai_analysis'].get('tutorial_group', title)

        # Determine overview
        overview = self._generate_overview(primary_workflow, workflows)

        # Extract tags
        tags = primary_workflow.get('tags', [])

        # Extract source files
        source_files = [w.get('file_path', '') for w in workflows]
        source_files = [f"{Path(f).name}:{w.get('line_start', 0)}" for f, w in zip(source_files, workflows)]

        # Create guide
        guide = HowToGuide(
            guide_id=guide_id,
            title=title,
            overview=overview,
            complexity_level=metadata.get('complexity_level', 'intermediate'),
            prerequisites=metadata.get('prerequisites', []),
            required_imports=metadata.get('required_imports', []),
            required_fixtures=metadata.get('required_fixtures', []),
            workflows=workflows,
            steps=steps,
            use_case=use_case,
            tags=tags,
            estimated_time=metadata.get('estimated_time', '10 minutes'),
            source_files=source_files
        )

        # Add AI enhancements if enhancer is available
        if enhancer:
            self._enhance_guide_with_ai(guide, primary_workflow.get('ai_analysis', {}), enhancer)
        elif self.enhance_with_ai and primary_workflow.get('ai_analysis'):
            # Fallback to old enhancement method (basic)
            self._enhance_guide_with_ai_basic(guide, primary_workflow['ai_analysis'])

        return guide

    def _generate_overview(self, primary_workflow: Dict, all_workflows: List[Dict]) -> str:
        """Generate guide overview"""
        # Try to get explanation from AI analysis
        if primary_workflow.get('ai_analysis'):
            explanation = primary_workflow['ai_analysis'].get('explanation')
            if explanation:
                return explanation

        # Fallback to description
        description = primary_workflow.get('description', '')
        if description:
            return description

        # Final fallback
        return f"Learn how to use {primary_workflow.get('test_name', 'this feature')} in your code."

    def _enhance_guide_with_ai(self, guide: HowToGuide, ai_analysis: Dict, enhancer):
        """
        Comprehensively enhance guide with AI using GuideEnhancer.

        Applies all 5 enhancements:
        1. Step descriptions - Natural language explanations        2. Troubleshooting - Diagnostic flows + solutions
        3. Prerequisites - Why needed + setup
        4. Next steps - Related guides, variations
        5. Use cases - Real-world scenarios

        Args:
            guide: HowToGuide object to enhance
            ai_analysis: AI analysis data from C3.6 (for context)
            enhancer: GuideEnhancer instance
        """
        # Prepare guide data for enhancer
        guide_data = {
            'title': guide.title,
            'steps': [
                {
                    'description': step.description,
                    'code': step.code
                }
                for step in guide.steps
            ],
            'language': 'python',  # TODO: Detect from code
            'prerequisites': guide.prerequisites,
            'description': guide.overview
        }

        # Call enhancer to get all 5 enhancements
        enhanced_data = enhancer.enhance_guide(guide_data)

        # Apply step enhancements
        if 'step_enhancements' in enhanced_data:
            for enhancement in enhanced_data['step_enhancements']:
                idx = enhancement.step_index
                if 0 <= idx < len(guide.steps):
                    guide.steps[idx].explanation = enhancement.explanation
                    guide.steps[idx].common_variations = enhancement.variations

        # Apply detailed prerequisites
        if 'prerequisites_detailed' in enhanced_data:
            guide.prerequisites_detailed = enhanced_data['prerequisites_detailed']

        # Apply troubleshooting
        if 'troubleshooting_detailed' in enhanced_data:
            guide.troubleshooting_detailed = enhanced_data['troubleshooting_detailed']

        # Apply next steps
        if 'next_steps_detailed' in enhanced_data:
            guide.next_steps_detailed = enhanced_data['next_steps_detailed']

        # Apply use cases
        if 'use_cases' in enhanced_data:
            guide.use_cases = enhanced_data['use_cases']

        logger.info(f"✨ Enhanced guide '{guide.title}' with comprehensive AI improvements")

    def _enhance_guide_with_ai_basic(self, guide: HowToGuide, ai_analysis: Dict):
        """
        Basic enhancement using pre-computed AI analysis from C3.6.

        This is a fallback when GuideEnhancer is not available.

        Args:
            guide: HowToGuide object to enhance
            ai_analysis: AI analysis data from C3.6
        """
        # Add best practices as variations
        best_practices = ai_analysis.get('best_practices', [])
        guide.variations = best_practices

        # Add common mistakes as pitfalls
        common_mistakes = ai_analysis.get('common_mistakes', [])
        guide.common_pitfalls = common_mistakes

        # Add related examples as related guides
        related_examples = ai_analysis.get('related_examples', [])
        guide.related_guides = [f"How To: {ex}" for ex in related_examples]

        # Enhance step explanations
        for step in guide.steps:
            # Add explanation to steps based on best practices
            if best_practices and step.step_number <= len(best_practices):
                step.explanation = best_practices[step.step_number - 1]

    def _create_collection(self, guides: List[HowToGuide]) -> GuideCollection:
        """Create GuideCollection from guides"""
        # Count by complexity
        by_complexity = defaultdict(int)
        for guide in guides:
            by_complexity[guide.complexity_level] += 1

        # Group by use case
        by_use_case = defaultdict(list)
        for guide in guides:
            use_case = guide.use_case or "Other"
            by_use_case[use_case].append(guide)

        return GuideCollection(
            total_guides=len(guides),
            guides_by_complexity=dict(by_complexity),
            guides_by_use_case=dict(by_use_case),
            guides=guides
        )

    def _save_guides_to_files(self, collection: GuideCollection, output_dir: Path):
        """Save guides to markdown files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving guides to {output_dir}...")

        # Save individual guides
        for use_case, guides in collection.guides_by_use_case.items():
            # Create use case directory
            use_case_dir = output_dir / use_case.lower().replace(' ', '-')
            use_case_dir.mkdir(parents=True, exist_ok=True)

            for guide in guides:
                # Generate filename from title
                filename = guide.title.lower().replace(' ', '-').replace(':', '') + '.md'
                file_path = use_case_dir / filename

                # Generate and save markdown
                markdown = self.generator.generate_guide_markdown(guide)
                file_path.write_text(markdown, encoding='utf-8')

        # Save index
        index_markdown = self.generator.generate_index(collection.guides)
        (output_dir / 'index.md').write_text(index_markdown, encoding='utf-8')

        logger.info(f"✅ Saved {collection.total_guides} guides + index to {output_dir}")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI entry point for how-to guide builder"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Build how-to guides from workflow test examples (C3.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From test examples JSON (C3.2 output)
  skill-seekers build-how-to-guides --input test_examples.json

  # From directory (extracts workflows)
  skill-seekers build-how-to-guides tests/

  # Custom grouping strategy
  skill-seekers build-how-to-guides tests/ --group-by file-path

  # Custom output directory
  skill-seekers build-how-to-guides tests/ --output tutorials/

  # Without AI enhancement
  skill-seekers build-how-to-guides tests/ --no-ai

Grouping Strategies:
  - ai-tutorial-group: Use AI-generated tutorial groups (default, best)
  - file-path: Group by source test file
  - test-name: Group by test name patterns
  - complexity: Group by difficulty level
"""
    )

    parser.add_argument(
        'input',
        nargs='?',
        help='Input: directory with test files OR test_examples.json file'
    )

    parser.add_argument(
        '--input',
        dest='input_file',
        help='Input JSON file with test examples (from C3.2)'
    )

    parser.add_argument(
        '--output',
        default='output/codebase/tutorials',
        help='Output directory for generated guides (default: output/codebase/tutorials)'
    )

    parser.add_argument(
        '--group-by',
        choices=['ai-tutorial-group', 'file-path', 'test-name', 'complexity'],
        default='ai-tutorial-group',
        help='Grouping strategy (default: ai-tutorial-group)'
    )

    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI enhancement'
    )

    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output JSON summary instead of markdown files'
    )

    args = parser.parse_args()

    # Determine input source
    input_path = args.input or args.input_file

    if not input_path:
        parser.print_help()
        print("\n❌ Error: No input provided")
        print("   Provide either a directory or --input JSON file")
        sys.exit(1)

    input_path = Path(input_path)

    # Load examples
    examples = []

    if input_path.is_file() and input_path.suffix == '.json':
        # Load from JSON file
        logger.info(f"Loading examples from {input_path}...")
        with open(input_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'examples' in data:
                examples = data['examples']
            elif isinstance(data, list):
                examples = data
            else:
                print(f"❌ Error: Invalid JSON format in {input_path}")
                sys.exit(1)

    elif input_path.is_dir():
        # Extract from directory using test example extractor
        print("⚠️  Directory input requires test example extractor")
        print("   Please use test_examples.json output from C3.2")
        print(f"   Or run: skill-seekers extract-test-examples {input_path} --json > examples.json")
        sys.exit(1)

    else:
        print(f"❌ Error: Input path not found: {input_path}")
        sys.exit(1)

    # Build guides
    builder = HowToGuideBuilder(enhance_with_ai=not args.no_ai)
    output_dir = Path(args.output) if not args.json_output else None

    collection = builder.build_guides_from_examples(
        examples,
        grouping_strategy=args.group_by,
        output_dir=output_dir
    )

    # Output results
    if args.json_output:
        # JSON output
        print(json.dumps(collection.to_dict(), indent=2))
    else:
        # Summary
        print()
        print("="*60)
        print("HOW-TO GUIDES GENERATED")
        print("="*60)
        print()
        print(f"Total Guides: {collection.total_guides}")
        print()
        print("By Complexity:")
        for level, count in collection.guides_by_complexity.items():
            print(f"  - {level.title()}: {count} guides")
        print()
        print("By Use Case:")
        for use_case, guides in collection.guides_by_use_case.items():
            print(f"  - {use_case}: {len(guides)} guides")
        print()
        if output_dir:
            print(f"📁 Output directory: {output_dir}")
            print(f"📄 Index file: {output_dir}/index.md")
            print()

    sys.exit(0)


if __name__ == "__main__":
    main()
