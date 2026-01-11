#!/usr/bin/env python3
"""
Router Skill Generator with GitHub Integration (Phase 4)

Creates a router/hub skill that intelligently directs queries to specialized sub-skills.
Integrates GitHub insights (issues, metadata) for enhanced topic detection and routing.

Phase 4 enhancements:
- Enhanced topic definition using GitHub issue labels
- Router template with repository stats and top issues
- Sub-skill templates with "Common Issues" section
- GitHub issue links for context
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Import three-stream data classes (Phase 1)
try:
    from .github_fetcher import ThreeStreamData, DocsStream, InsightsStream
    from .merge_sources import categorize_issues_by_topic
    from .markdown_cleaner import MarkdownCleaner
except ImportError:
    # Fallback if github_fetcher not available
    ThreeStreamData = None
    DocsStream = None
    InsightsStream = None
    categorize_issues_by_topic = None


class RouterGenerator:
    """Generates router skills that direct to specialized sub-skills with GitHub integration"""

    def __init__(self,
                 config_paths: List[str],
                 router_name: str = None,
                 github_streams: Optional['ThreeStreamData'] = None):
        """
        Initialize router generator with optional GitHub streams.

        Args:
            config_paths: Paths to sub-skill config files
            router_name: Optional router skill name
            github_streams: Optional ThreeStreamData with docs and insights
        """
        self.config_paths = [Path(p) for p in config_paths]
        self.configs = [self.load_config(p) for p in self.config_paths]
        self.router_name = router_name or self.infer_router_name()
        self.base_config = self.configs[0]  # Use first as template
        self.github_streams = github_streams

        # Extract GitHub data if available
        self.github_metadata = None
        self.github_docs = None
        self.github_issues = None

        if github_streams and github_streams.insights_stream:
            self.github_metadata = github_streams.insights_stream.metadata
            self.github_issues = {
                'common_problems': github_streams.insights_stream.common_problems,
                'known_solutions': github_streams.insights_stream.known_solutions,
                'top_labels': github_streams.insights_stream.top_labels
            }

        if github_streams and github_streams.docs_stream:
            self.github_docs = {
                'readme': github_streams.docs_stream.readme,
                'contributing': github_streams.docs_stream.contributing
            }

    def load_config(self, path: Path) -> Dict[str, Any]:
        """Load a config file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {path}: {e}")
            sys.exit(1)

    def infer_router_name(self) -> str:
        """Infer router name from sub-skill names"""
        # Find common prefix
        names = [cfg['name'] for cfg in self.configs]
        if not names:
            return "router"

        # Get common prefix before first dash
        first_name = names[0]
        if '-' in first_name:
            return first_name.split('-')[0]
        return first_name

    def extract_routing_keywords(self) -> Dict[str, List[str]]:
        """
        Extract keywords for routing to each skill (Phase 4 enhanced).

        Enhancement: Weight GitHub issue labels 2x in topic scoring.
        Uses C3.x patterns, examples, and GitHub insights for better routing.
        """
        routing = {}

        for config in self.configs:
            name = config['name']
            keywords = []

            # Extract from categories (base weight: 1x)
            if 'categories' in config:
                keywords.extend(config['categories'].keys())

            # Extract from name (part after dash)
            if '-' in name:
                skill_topic = name.split('-', 1)[1]
                keywords.append(skill_topic)

            # Phase 4: Add GitHub issue labels (weight 2x by including twice)
            if self.github_issues:
                # Get top labels related to this skill topic
                top_labels = self.github_issues.get('top_labels', [])
                skill_keywords = set(keywords)

                for label_info in top_labels[:10]:  # Top 10 labels
                    label = label_info['label'].lower()

                    # Check if label relates to any skill keyword
                    if any(keyword.lower() in label or label in keyword.lower() for keyword in skill_keywords):
                        # Add twice for 2x weight
                        keywords.append(label)
                        keywords.append(label)

            # NEW: Extract skill-specific labels from individual issues
            skill_keywords_set = set(keywords)
            skill_specific_labels = self._extract_skill_specific_labels(name, skill_keywords_set)
            for label in skill_specific_labels:
                keywords.append(label)
                keywords.append(label)  # 2x weight

            routing[name] = keywords

        return routing

    def _extract_skill_specific_labels(self, skill_name: str, skill_keywords: set) -> List[str]:
        """
        Extract labels from GitHub issues that match this specific skill.

        Scans all common_problems and known_solutions for issues whose labels
        match the skill's keywords, then extracts ALL labels from those issues.
        This provides richer, skill-specific routing keywords.

        Args:
            skill_name: Name of the skill
            skill_keywords: Set of keywords already associated with the skill

        Returns:
            List of skill-specific labels (excluding generic ones)
        """
        if not self.github_issues:
            return []

        common_problems = self.github_issues.get('common_problems', [])
        known_solutions = self.github_issues.get('known_solutions', [])
        all_issues = common_problems + known_solutions

        matching_labels = set()

        for issue in all_issues:
            issue_labels = issue.get('labels', [])
            issue_labels_lower = [label.lower() for label in issue_labels]

            # Check if this issue relates to the skill
            has_match = any(
                keyword.lower() in label or label in keyword.lower()
                for keyword in skill_keywords
                for label in issue_labels_lower
            )

            if has_match:
                # Add ALL labels from this matching issue
                for label in issue_labels_lower:
                    # Skip generic labels that don't add routing value
                    if label not in ['bug', 'enhancement', 'question', 'help wanted',
                                   'good first issue', 'documentation', 'duplicate']:
                        matching_labels.add(label)

        return list(matching_labels)

    def _generate_frontmatter(self, routing_keywords: Dict[str, List[str]]) -> str:
        """
        Generate YAML frontmatter compliant with agentskills.io spec.

        Required fields:
        - name: router name (1-64 chars, lowercase-hyphen)
        - description: when to use (1-1024 chars, keyword-rich)

        Optional fields:
        - license: MIT (from config or default)
        - compatibility: Python version, dependencies
        """
        # Build comprehensive description from all sub-skills
        all_topics = []
        for config in self.configs:
            desc = config.get('description', '')
            # Extract key topics from description (simple extraction)
            topics = [word.strip() for word in desc.split(',') if word.strip()]
            all_topics.extend(topics[:2])  # Max 2 topics per skill

        # Create keyword-rich description
        unique_topics = list(dict.fromkeys(all_topics))[:7]  # Top 7 unique topics

        if unique_topics:
            topics_str = ', '.join(unique_topics)
            description = f"{self.router_name.title()} framework. Use when working with: {topics_str}"
        else:
            description = f"Use when working with {self.router_name.title()} development and programming"

        # Truncate to 200 chars for performance (agentskills.io recommendation)
        if len(description) > 200:
            description = description[:197] + "..."

        # Extract license and compatibility
        license_info = "MIT"
        compatibility = "See sub-skills for specific requirements"

        # Try to get language-specific compatibility if GitHub metadata available
        if self.github_metadata:
            language = self.github_metadata.get('language', '')
            compatibility_map = {
                'Python': f'Python 3.10+, requires {self.router_name} package',
                'JavaScript': f'Node.js 18+, requires {self.router_name} package',
                'TypeScript': f'Node.js 18+, TypeScript 5+, requires {self.router_name} package',
                'Go': f'Go 1.20+, requires {self.router_name} package',
                'Rust': f'Rust 1.70+, requires {self.router_name} package',
                'Java': f'Java 17+, requires {self.router_name} package',
            }
            if language in compatibility_map:
                compatibility = compatibility_map[language]

            # Try to extract license
            if isinstance(self.github_metadata.get('license'), dict):
                license_info = self.github_metadata['license'].get('name', 'MIT')

        frontmatter = f"""---
name: {self.router_name}
description: {description}
license: {license_info}
compatibility: {compatibility}
---"""

        return frontmatter

    def _extract_clean_readme_section(self, readme: str) -> str:
        """
        Extract and clean README quick start section.

        Args:
            readme: Full README content

        Returns:
            Cleaned quick start section (HTML removed, properly truncated)
        """
        cleaner = MarkdownCleaner()

        # Extract first meaningful section (1500 chars soft limit - extends for complete code blocks)
        quick_start = cleaner.extract_first_section(readme, max_chars=1500)

        # Additional validation
        if len(quick_start) < 50:  # Too short, probably just title
            # Try to get more content
            quick_start = cleaner.extract_first_section(readme, max_chars=2000)

        return quick_start

    def _extract_topic_from_skill(self, skill_name: str) -> str:
        """
        Extract readable topic from skill name.

        Examples:
        - "fastmcp-oauth" -> "OAuth authentication"
        - "react-hooks" -> "React hooks"
        - "django-orm" -> "Django ORM"

        Args:
            skill_name: Skill name (e.g., "fastmcp-oauth")

        Returns:
            Readable topic string
        """
        # Remove router name prefix
        if skill_name.startswith(f"{self.router_name}-"):
            topic = skill_name[len(self.router_name)+1:]
        else:
            topic = skill_name

        # Capitalize and add context
        topic = topic.replace('-', ' ').title()

        # Add common suffixes for context
        topic_map = {
            'oauth': 'OAuth authentication',
            'auth': 'authentication',
            'async': 'async patterns',
            'api': 'API integration',
            'orm': 'ORM queries',
            'hooks': 'hooks',
            'routing': 'routing',
            'testing': 'testing',
            '2d': '2D development',
            '3d': '3D development',
            'scripting': 'scripting',
            'physics': 'physics',
        }

        topic_lower = topic.lower()
        for key, value in topic_map.items():
            if key in topic_lower:
                return value

        return topic

    def _generate_dynamic_examples(self, routing_keywords: Dict[str, List[str]]) -> str:
        """
        Generate examples dynamically from actual sub-skill names and keywords.

        Creates 2-3 realistic examples showing:
        1. Single skill activation
        2. Different skill activation
        3. Complex query routing (if 2+ skills)

        Args:
            routing_keywords: Dictionary mapping skill names to keywords

        Returns:
            Formatted examples section
        """
        examples = []

        # Get list of sub-skills
        skill_names = list(routing_keywords.keys())

        if len(skill_names) == 0:
            return ""

        # Example 1: Single skill activation (first sub-skill)
        if len(skill_names) >= 1:
            first_skill = skill_names[0]
            first_keywords = routing_keywords[first_skill][:2]  # Top 2 keywords

            # Extract topic from skill name
            topic = self._extract_topic_from_skill(first_skill)
            keyword = first_keywords[0] if first_keywords else topic

            examples.append(
                f'**Q:** "How do I implement {keyword}?"\n'
                f'**A:** Activates {first_skill} skill'
            )

        # Example 2: Different skill (second sub-skill if available)
        if len(skill_names) >= 2:
            second_skill = skill_names[1]
            second_keywords = routing_keywords[second_skill][:2]

            topic = self._extract_topic_from_skill(second_skill)
            keyword = second_keywords[0] if second_keywords else topic

            examples.append(
                f'**Q:** "Working with {keyword} in {self.router_name.title()}"\n'
                f'**A:** Activates {second_skill} skill'
            )

        # Example 3: Multi-skill activation (if 2+ skills)
        if len(skill_names) >= 2:
            skill_1 = skill_names[0]
            skill_2 = skill_names[1]

            topic_1 = self._extract_topic_from_skill(skill_1)
            topic_2 = self._extract_topic_from_skill(skill_2)

            examples.append(
                f'**Q:** "Combining {topic_1} with {topic_2}"\n'
                f'**A:** Activates {skill_1} + {skill_2} skills'
            )

        return '\n\n'.join(examples)

    def _generate_examples_from_github(self, routing_keywords: Dict[str, List[str]]) -> str:
        """
        Generate examples from real GitHub issue titles.

        Uses actual user questions from GitHub issues to create realistic examples.
        Matches issues to skills based on labels for relevance.
        Fallback to keyword-based examples if no GitHub data available.

        Args:
            routing_keywords: Dictionary mapping skill names to keywords

        Returns:
            Formatted examples section with real user questions
        """
        if not self.github_issues:
            return self._generate_dynamic_examples(routing_keywords)

        examples = []
        common_problems = self.github_issues.get('common_problems', [])

        if not common_problems:
            return self._generate_dynamic_examples(routing_keywords)

        # Match issues to skills based on labels (generate up to 3 examples)
        for skill_name, keywords in list(routing_keywords.items())[:3]:
            skill_keywords_lower = [k.lower() for k in keywords]
            matched_issue = None

            # Find first issue matching this skill's keywords
            for issue in common_problems:
                issue_labels = [label.lower() for label in issue.get('labels', [])]
                if any(label in skill_keywords_lower for label in issue_labels):
                    matched_issue = issue
                    common_problems.remove(issue)  # Don't reuse same issue
                    break

            if matched_issue:
                title = matched_issue.get('title', '')
                question = self._convert_issue_to_question(title)
                examples.append(
                    f'**Q:** "{question}"\n'
                    f'**A:** Activates {skill_name} skill'
                )
            else:
                # Fallback to keyword-based example for this skill
                topic = self._extract_topic_from_skill(skill_name)
                keyword = keywords[0] if keywords else topic
                examples.append(
                    f'**Q:** "Working with {keyword} in {self.router_name.title()}"\n'
                    f'**A:** Activates {skill_name} skill'
                )

        return '\n\n'.join(examples) if examples else self._generate_dynamic_examples(routing_keywords)

    def _convert_issue_to_question(self, issue_title: str) -> str:
        """
        Convert GitHub issue title to natural question format.

        Examples:
        - "OAuth fails on redirect" → "How do I fix OAuth redirect failures?"
        - "ApiKey Header documentation" → "How do I use ApiKey Header?"
        - "Add WebSocket support" → "How do I handle WebSocket support?"

        Args:
            issue_title: Raw GitHub issue title

        Returns:
            Natural question format suitable for examples
        """
        title_lower = issue_title.lower()

        # Pattern 1: Error/Failure issues
        if 'fail' in title_lower or 'error' in title_lower or 'issue' in title_lower:
            cleaned = issue_title.replace(' fails', '').replace(' errors', '').replace(' issue', '')
            return f"How do I fix {cleaned.lower()}?"

        # Pattern 2: Documentation requests
        if 'documentation' in title_lower or 'docs' in title_lower:
            cleaned = issue_title.replace(' documentation', '').replace(' docs', '')
            return f"How do I use {cleaned.lower()}?"

        # Pattern 3: Feature requests
        if title_lower.startswith('add ') or title_lower.startswith('added '):
            feature = issue_title.replace('Add ', '').replace('Added ', '')
            return f"How do I implement {feature.lower()}?"

        # Default: Generic question
        return f"How do I handle {issue_title.lower()}?"

    def _extract_common_patterns(self) -> List[Dict[str, str]]:
        """
        Extract problem-solution patterns from closed GitHub issues.

        Analyzes closed issues (known_solutions) to identify common patterns
        that users encountered and resolved. These patterns are shown in the
        Common Patterns section of the router skill.

        Returns:
            List of pattern dicts with 'problem', 'solution', 'issue_number'
        """
        if not self.github_issues:
            return []

        known_solutions = self.github_issues.get('known_solutions', [])
        if not known_solutions:
            return []

        patterns = []

        # Top 5 closed issues with most engagement (comments indicate usefulness)
        top_solutions = sorted(known_solutions, key=lambda x: x.get('comments', 0), reverse=True)[:5]

        for issue in top_solutions:
            title = issue.get('title', '')
            number = issue.get('number', 0)
            problem, solution = self._parse_issue_pattern(title)

            patterns.append({
                'problem': problem,
                'solution': solution,
                'issue_number': number
            })

        return patterns

    def _parse_issue_pattern(self, issue_title: str) -> tuple:
        """
        Parse issue title to extract problem-solution pattern.

        Analyzes the structure of closed issue titles to infer the problem
        and solution pattern. Common patterns include fixes, additions, and resolutions.

        Examples:
        - "Fixed OAuth redirect" → ("OAuth redirect not working", "See fix implementation")
        - "Added API key support" → ("Missing API key support", "Use API key support feature")
        - "Resolved timeout errors" → ("Timeout errors issue", "See resolution approach")

        Args:
            issue_title: Title of closed GitHub issue

        Returns:
            Tuple of (problem_description, solution_hint)
        """
        title_lower = issue_title.lower()

        # Pattern 1: "Fixed X" → "X not working" / "See fix"
        if title_lower.startswith('fixed ') or title_lower.startswith('fix '):
            problem_text = issue_title.replace('Fixed ', '').replace('Fix ', '')
            return (f"{problem_text} not working", "See fix implementation details")

        # Pattern 2: "Resolved X" → "X issue" / "See resolution"
        if title_lower.startswith('resolved ') or title_lower.startswith('resolve '):
            problem_text = issue_title.replace('Resolved ', '').replace('Resolve ', '')
            return (f"{problem_text} issue", "See resolution approach")

        # Pattern 3: "Added X" → "Missing X" / "Use X"
        if title_lower.startswith('added ') or title_lower.startswith('add '):
            feature_text = issue_title.replace('Added ', '').replace('Add ', '')
            return (f"Missing {feature_text}", f"Use {feature_text} feature")

        # Default: Use title as-is
        return (issue_title, "See issue for solution details")

    def _detect_framework(self) -> Optional[str]:
        """
        Detect framework from router name and GitHub metadata.

        Identifies common frameworks (fastapi, django, react, etc.) from
        router name or repository description. Used to provide framework-specific
        hello world templates when README lacks code examples.

        Returns:
            Framework identifier (e.g., 'fastapi', 'django') or None if unknown
        """
        router_lower = self.router_name.lower()

        framework_keywords = {
            'fastapi': 'fastapi',
            'django': 'django',
            'flask': 'flask',
            'react': 'react',
            'vue': 'vue',
            'express': 'express',
            'fastmcp': 'fastmcp',
            'mcp': 'fastmcp',
        }

        # Check router name first
        for keyword, framework in framework_keywords.items():
            if keyword in router_lower:
                return framework

        # Check GitHub description if available
        if self.github_metadata:
            description = self.github_metadata.get('description', '').lower()
            for keyword, framework in framework_keywords.items():
                if keyword in description:
                    return framework

        return None

    def _get_framework_hello_world(self, framework: str) -> str:
        """
        Get framework-specific hello world template.

        Provides basic installation + hello world code for common frameworks.
        Used as fallback when README doesn't contain code examples.

        Args:
            framework: Framework identifier (e.g., 'fastapi', 'react')

        Returns:
            Formatted Quick Start section with install + hello world code
        """
        templates = {
            'fastapi': """## Quick Start

```bash
pip install fastapi uvicorn
```

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Run: uvicorn main:app --reload
```
""",
            'fastmcp': """## Quick Start

```bash
pip install fastmcp
```

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def greet(name: str) -> str:
    return f"Hello, {name}!"
```
""",
            'django': """## Quick Start

```bash
pip install django
django-admin startproject mysite
cd mysite
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see your Django app.
""",
            'react': """## Quick Start

```bash
npx create-react-app my-app
cd my-app
npm start
```

```jsx
function App() {
  return <h1>Hello World</h1>;
}

export default App;
```
""",
        }

        return templates.get(framework, "")

    def _generate_comprehensive_description(self) -> str:
        """
        Generate router description that covers all sub-skill topics.

        Extracts key topics from all sub-skill descriptions and combines them
        into a comprehensive "Use when working with:" list.

        Returns:
            Comprehensive description string
        """
        all_topics = []

        for config in self.configs:
            desc = config.get('description', '')
            # Extract key topics from description (simple comma-separated extraction)
            topics = [topic.strip() for topic in desc.split(',') if topic.strip()]
            all_topics.extend(topics[:2])  # Max 2 topics per skill

        # Deduplicate and take top 5-7 topics
        unique_topics = list(dict.fromkeys(all_topics))[:7]

        if not unique_topics:
            return f'Use when working with {self.router_name} development and programming'

        # Format as user-friendly bulleted list
        description = f"""Use this skill when working with:
- {self.router_name.title()} framework (general questions)
"""

        for topic in unique_topics:
            # Clean up topic text (remove "when working with" prefixes if present)
            topic = topic.replace('when working with', '').strip()
            topic = topic.replace('Use when', '').strip()
            if topic:
                description += f"- {topic}\n"

        # Add comprehensive footer items
        description += f"- {self.router_name.upper()} protocol implementation\n"
        description += f"- {self.router_name.title()} configuration and setup"

        return description

    def generate_skill_md(self) -> str:
        """
        Generate router SKILL.md content (Phase 4 enhanced).

        Enhancement: Include repository stats, README quick start, and top 5 GitHub issues.
        With YAML frontmatter for agentskills.io compliance.
        """
        routing_keywords = self.extract_routing_keywords()

        # NEW: Generate YAML frontmatter
        frontmatter = self._generate_frontmatter(routing_keywords)

        # NEW: Generate comprehensive description from all sub-skills
        when_to_use = self._generate_comprehensive_description()

        skill_md = frontmatter + "\n\n" + f"""# {self.router_name.replace('-', ' ').title()} Documentation

## When to Use This Skill

{when_to_use}

This is a router skill that directs your questions to specialized sub-skills for efficient, focused assistance.

"""

        # Phase 4: Add GitHub repository metadata
        if self.github_metadata:
            # NEW: Use html_url from GitHub metadata instead of base_url from config
            repo_url = self.github_metadata.get('html_url', '')
            stars = self.github_metadata.get('stars', 0)
            language = self.github_metadata.get('language', 'Unknown')
            description = self.github_metadata.get('description', '')

            skill_md += f"""## Repository Info

**Repository:** {repo_url}
**Stars:** ⭐ {stars:,} | **Language:** {language}
{f'**Description:** {description}' if description else ''}

"""

        # Phase 4: Add Quick Start from README
        if self.github_docs and self.github_docs.get('readme'):
            readme = self.github_docs['readme']

            # NEW: Clean HTML and extract meaningful content
            quick_start = self._extract_clean_readme_section(readme)

            if quick_start:
                skill_md += f"""## Quick Start

{quick_start}

*For detailed setup, see references/getting_started.md*

"""
            else:
                # NEW: Fallback to framework-specific hello world (Phase 2, Fix 5)
                framework = self._detect_framework()
                if framework:
                    hello_world = self._get_framework_hello_world(framework)
                    if hello_world:
                        skill_md += hello_world + "\n*Note: Generic template. See references/getting_started.md for project-specific setup.*\n\n"
        else:
            # No README available - try framework fallback
            framework = self._detect_framework()
            if framework:
                hello_world = self._get_framework_hello_world(framework)
                if hello_world:
                    skill_md += hello_world + "\n*Note: Generic template. Check repository for specific installation instructions.*\n\n"

        skill_md += """## How It Works

This skill analyzes your question and activates the appropriate specialized skill(s):

"""

        # List sub-skills
        for config in self.configs:
            name = config['name']
            desc = config.get('description', '')
            # Remove router name prefix from description if present
            if desc.startswith(f"{self.router_name.title()} -"):
                desc = desc.split(' - ', 1)[1]

            skill_md += f"### {name}\n{desc}\n\n"

        # Routing logic
        skill_md += """## Routing Logic

The router analyzes your question for topic keywords and activates relevant skills:

**Keywords → Skills:**
"""

        for skill_name, keywords in routing_keywords.items():
            # NEW: Deduplicate keywords for display while preserving order
            unique_keywords = list(dict.fromkeys(keywords))  # Preserves order, removes duplicates
            keyword_str = ", ".join(unique_keywords)
            skill_md += f"- {keyword_str} → **{skill_name}**\n"

        # Quick reference
        skill_md += f"""

## Quick Reference

For quick answers, this router provides basic overview information. For detailed documentation, the specialized skills contain comprehensive references.

### Getting Started

1. Ask your question naturally - mention the topic area
2. The router will activate the appropriate skill(s)
3. You'll receive focused, detailed answers from specialized documentation

### Examples

"""

        # NEW: Generate examples from GitHub issues (with fallback to keyword-based)
        dynamic_examples = self._generate_examples_from_github(routing_keywords)
        if dynamic_examples:
            skill_md += dynamic_examples + "\n\n"

        skill_md += """### All Available Skills

"""

        # List all skills
        for config in self.configs:
            skill_md += f"- **{config['name']}**\n"

        # Phase 4: Add Common Issues from GitHub (Summary with Reference)
        if self.github_issues:
            common_problems = self.github_issues.get('common_problems', [])[:5]  # Top 5

            if common_problems:
                skill_md += """

## Common Issues

Top 5 GitHub issues from the community:

"""
                for i, issue in enumerate(common_problems, 1):
                    title = issue.get('title', '')
                    number = issue.get('number', 0)
                    comments = issue.get('comments', 0)

                    skill_md += f"{i}. **{title}** (Issue #{number}, {comments} comments)\n"

                skill_md += "\n*For details and solutions, see references/github_issues.md*\n"

        # NEW: Add Common Patterns section (Phase 2, Fix 4)
        if self.github_issues:
            patterns = self._extract_common_patterns()

            if patterns:
                skill_md += """

## Common Patterns

Problem-solution patterns from resolved GitHub issues:

"""
                for i, pattern in enumerate(patterns, 1):
                    problem = pattern['problem']
                    solution = pattern['solution']
                    issue_num = pattern['issue_number']

                    skill_md += f"**Pattern {i}**: {problem}\n"
                    skill_md += f"→ **Solution**: {solution} ([Issue #{issue_num}](references/github_issues.md))\n\n"

        # NEW: Add References section
        skill_md += """

## References

Detailed documentation available in:

"""
        if self.github_issues:
            skill_md += "- `references/github_issues.md` - Community problems and solutions\n"
        if self.github_docs and self.github_docs.get('readme'):
            skill_md += "- `references/getting_started.md` - Detailed setup guide\n"

        skill_md += f"""

## Need Help?

Simply ask your question and mention the topic. The router will find the right specialized skill for you!

---

*This is a router skill. For complete documentation, see the specialized skills listed above.*
"""

        return skill_md

    def generate_subskill_issues_section(self, skill_name: str, topics: List[str]) -> str:
        """
        Generate "Common Issues" section for a sub-skill (Phase 4).

        Args:
            skill_name: Name of the sub-skill
            topics: List of topic keywords for this skill

        Returns:
            Markdown section with relevant GitHub issues
        """
        if not self.github_issues or not categorize_issues_by_topic:
            return ""

        common_problems = self.github_issues.get('common_problems', [])
        known_solutions = self.github_issues.get('known_solutions', [])

        # Categorize issues by topic
        categorized = categorize_issues_by_topic(common_problems, known_solutions, topics)

        # Build issues section
        issues_md = """

## Common Issues (from GitHub)

GitHub issues related to this topic:

"""

        has_issues = False

        # Add categorized issues
        for topic, issues in categorized.items():
            if not issues:
                continue

            has_issues = True
            issues_md += f"\n### {topic.title()}\n\n"

            for issue in issues[:3]:  # Top 3 per topic
                title = issue.get('title', '')
                number = issue.get('number', 0)
                state = issue.get('state', 'unknown')
                comments = issue.get('comments', 0)
                labels = issue.get('labels', [])

                # Format issue
                state_icon = "🔴" if state == "open" else "✅"
                issues_md += f"**{state_icon} Issue #{number}: {title}**\n"
                issues_md += f"- Status: {state.title()}\n"
                issues_md += f"- {comments} comments\n"
                if labels:
                    issues_md += f"- Labels: {', '.join(labels)}\n"
                issues_md += "\n"

        if not has_issues:
            return ""  # No relevant issues for this skill

        return issues_md

    def create_router_config(self) -> Dict[str, Any]:
        """Create router configuration"""
        routing_keywords = self.extract_routing_keywords()

        router_config = {
            "name": self.router_name,
            "description": self.base_config.get('description', f'Use when working with {self.router_name} documentation (router for multiple sub-skills)'),
            "base_url": self.base_config['base_url'],
            "selectors": self.base_config.get('selectors', {}),
            "url_patterns": self.base_config.get('url_patterns', {}),
            "rate_limit": self.base_config.get('rate_limit', 0.5),
            "max_pages": 500,  # Router only scrapes overview pages
            "_router": True,
            "_sub_skills": [cfg['name'] for cfg in self.configs],
            "_routing_keywords": routing_keywords
        }

        return router_config

    def _generate_github_issues_reference(self) -> str:
        """
        Generate detailed GitHub issues reference file.

        Returns:
            Markdown content for github_issues.md
        """
        md = "# Common GitHub Issues\n\n"
        md += "Top issues reported by the community:\n\n"

        common_problems = self.github_issues.get('common_problems', [])[:10] if self.github_issues else []
        known_solutions = self.github_issues.get('known_solutions', [])[:10] if self.github_issues else []

        if common_problems:
            md += "## Open Issues (Common Problems)\n\n"
            for i, issue in enumerate(common_problems, 1):
                title = issue.get('title', '')
                number = issue.get('number', 0)
                comments = issue.get('comments', 0)
                labels = issue.get('labels', [])
                if isinstance(labels, list):
                    labels_str = ', '.join(str(label) for label in labels)
                else:
                    labels_str = str(labels) if labels else ''

                md += f"### {i}. {title}\n\n"
                md += f"**Issue**: #{number}\n"
                md += f"**Comments**: {comments}\n"
                if labels_str:
                    md += f"**Labels**: {labels_str}\n"
                md += f"**Link**: https://github.com/{self.github_metadata.get('html_url', '').replace('https://github.com/', '')}/issues/{number}\n\n" if self.github_metadata else "\n\n"

        if known_solutions:
            md += "\n## Closed Issues (Known Solutions)\n\n"
            for i, issue in enumerate(known_solutions, 1):
                title = issue.get('title', '')
                number = issue.get('number', 0)
                comments = issue.get('comments', 0)

                md += f"### {i}. {title}\n\n"
                md += f"**Issue**: #{number} (Closed)\n"
                md += f"**Comments**: {comments}\n"
                if self.github_metadata:
                    md += f"**Link**: https://github.com/{self.github_metadata.get('html_url', '').replace('https://github.com/', '')}/issues/{number}\n\n"
                else:
                    md += "\n\n"

        return md

    def _generate_getting_started_reference(self) -> str:
        """
        Generate getting started reference from README.

        Returns:
            Markdown content for getting_started.md
        """
        md = "# Getting Started\n\n"
        md += "*Extracted from project README*\n\n"

        if self.github_docs and self.github_docs.get('readme'):
            readme = self.github_docs['readme']

            # Clean and extract full quick start section (up to 2000 chars)
            cleaner = MarkdownCleaner()
            content = cleaner.extract_first_section(readme, max_chars=2000)

            md += content
        else:
            md += "No README content available.\n"

        return md

    def _generate_reference_files(self, references_dir: Path):
        """
        Generate reference files for progressive disclosure.

        Files created:
        - github_issues.md: Detailed GitHub issues with solutions
        - getting_started.md: Full README quick start

        Args:
            references_dir: Path to references/ directory
        """
        # 1. GitHub Issues Reference
        if self.github_issues:
            issues_md = self._generate_github_issues_reference()
            with open(references_dir / 'github_issues.md', 'w') as f:
                f.write(issues_md)

        # 2. Getting Started Reference
        if self.github_docs and self.github_docs.get('readme'):
            getting_started_md = self._generate_getting_started_reference()
            with open(references_dir / 'getting_started.md', 'w') as f:
                f.write(getting_started_md)

    def generate(self, output_dir: Path = None) -> Tuple[Path, Path]:
        """Generate router skill and config with progressive disclosure"""
        if output_dir is None:
            output_dir = self.config_paths[0].parent

        output_dir = Path(output_dir)

        # Generate SKILL.md
        skill_md = self.generate_skill_md()
        skill_path = output_dir.parent / f"output/{self.router_name}/SKILL.md"
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        with open(skill_path, 'w') as f:
            f.write(skill_md)

        # NEW: Create references/ directory and generate reference files
        references_dir = skill_path.parent / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        self._generate_reference_files(references_dir)

        # Generate config
        router_config = self.create_router_config()
        config_path = output_dir / f"{self.router_name}.json"

        with open(config_path, 'w') as f:
            json.dump(router_config, f, indent=2)

        return config_path, skill_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate router/hub skill for split documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate router from multiple configs
  python3 generate_router.py configs/godot-2d.json configs/godot-3d.json configs/godot-scripting.json

  # Use glob pattern
  python3 generate_router.py configs/godot-*.json

  # Custom router name
  python3 generate_router.py configs/godot-*.json --name godot-hub

  # Custom output directory
  python3 generate_router.py configs/godot-*.json --output-dir configs/routers/
        """
    )

    parser.add_argument(
        'configs',
        nargs='+',
        help='Sub-skill config files'
    )

    parser.add_argument(
        '--name',
        help='Router skill name (default: inferred from sub-skills)'
    )

    parser.add_argument(
        '--output-dir',
        help='Output directory (default: same as input configs)'
    )

    args = parser.parse_args()

    # Filter out router configs (avoid recursion)
    config_files = []
    for path_str in args.configs:
        path = Path(path_str)
        if path.exists() and not path.stem.endswith('-router'):
            config_files.append(path_str)

    if not config_files:
        print("❌ Error: No valid config files provided")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("ROUTER SKILL GENERATOR")
    print(f"{'='*60}")
    print(f"Sub-skills: {len(config_files)}")
    for cfg in config_files:
        print(f"  - {Path(cfg).stem}")
    print("")

    # Generate router
    generator = RouterGenerator(config_files, args.name)
    config_path, skill_path = generator.generate(args.output_dir)

    print(f"✅ Router config created: {config_path}")
    print(f"✅ Router SKILL.md created: {skill_path}")
    print("")
    print(f"{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print(f"1. Review router SKILL.md: {skill_path}")
    print(f"2. Optionally scrape router (for overview pages):")
    print(f"     skill-seekers scrape --config {config_path}")
    print("3. Package router skill:")
    print(f"     skill-seekers package output/{generator.router_name}/")
    print("4. Upload router + all sub-skills to Claude")
    print("")


if __name__ == "__main__":
    main()
