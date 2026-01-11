#!/usr/bin/env python3
"""
Source Merger for Multi-Source Skills

Merges documentation and code data intelligently with GitHub insights:
- Rule-based merge: Fast, deterministic rules
- Claude-enhanced merge: AI-powered reconciliation

Handles conflicts and creates unified API reference with GitHub metadata.

Multi-layer architecture (Phase 3):
- Layer 1: C3.x code (ground truth)
- Layer 2: HTML docs (official intent)
- Layer 3: GitHub docs (README/CONTRIBUTING)
- Layer 4: GitHub insights (issues)
"""

import json
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from .conflict_detector import Conflict, ConflictDetector

# Import three-stream data classes (Phase 1)
try:
    from .github_fetcher import ThreeStreamData, CodeStream, DocsStream, InsightsStream
except ImportError:
    # Fallback if github_fetcher not available
    ThreeStreamData = None
    CodeStream = None
    DocsStream = None
    InsightsStream = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def categorize_issues_by_topic(
    problems: List[Dict],
    solutions: List[Dict],
    topics: List[str]
) -> Dict[str, List[Dict]]:
    """
    Categorize GitHub issues by topic keywords.

    Args:
        problems: List of common problems (open issues with 5+ comments)
        solutions: List of known solutions (closed issues with comments)
        topics: List of topic keywords to match against

    Returns:
        Dict mapping topic to relevant issues
    """
    categorized = {topic: [] for topic in topics}
    categorized['other'] = []

    all_issues = problems + solutions

    for issue in all_issues:
        # Get searchable text
        title = issue.get('title', '').lower()
        labels = [label.lower() for label in issue.get('labels', [])]
        text = f"{title} {' '.join(labels)}"

        # Find best matching topic
        matched_topic = None
        max_matches = 0

        for topic in topics:
            # Count keyword matches
            topic_keywords = topic.lower().split()
            matches = sum(1 for keyword in topic_keywords if keyword in text)

            if matches > max_matches:
                max_matches = matches
                matched_topic = topic

        # Categorize by best match or 'other'
        if matched_topic and max_matches > 0:
            categorized[matched_topic].append(issue)
        else:
            categorized['other'].append(issue)

    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


def generate_hybrid_content(
    api_data: Dict,
    github_docs: Optional[Dict],
    github_insights: Optional[Dict],
    conflicts: List[Conflict]
) -> Dict[str, Any]:
    """
    Generate hybrid content combining API data with GitHub context.

    Args:
        api_data: Merged API data
        github_docs: GitHub docs stream (README, CONTRIBUTING, docs/*.md)
        github_insights: GitHub insights stream (metadata, issues, labels)
        conflicts: List of detected conflicts

    Returns:
        Hybrid content dict with enriched API reference
    """
    hybrid = {
        'api_reference': api_data,
        'github_context': {}
    }

    # Add GitHub documentation layer
    if github_docs:
        hybrid['github_context']['docs'] = {
            'readme': github_docs.get('readme'),
            'contributing': github_docs.get('contributing'),
            'docs_files_count': len(github_docs.get('docs_files', []))
        }

    # Add GitHub insights layer
    if github_insights:
        metadata = github_insights.get('metadata', {})
        hybrid['github_context']['metadata'] = {
            'stars': metadata.get('stars', 0),
            'forks': metadata.get('forks', 0),
            'language': metadata.get('language', 'Unknown'),
            'description': metadata.get('description', '')
        }

        # Add issue insights
        common_problems = github_insights.get('common_problems', [])
        known_solutions = github_insights.get('known_solutions', [])

        hybrid['github_context']['issues'] = {
            'common_problems_count': len(common_problems),
            'known_solutions_count': len(known_solutions),
            'top_problems': common_problems[:5],  # Top 5 most-discussed
            'top_solutions': known_solutions[:5]
        }

        hybrid['github_context']['top_labels'] = github_insights.get('top_labels', [])

    # Add conflict summary
    hybrid['conflict_summary'] = {
        'total_conflicts': len(conflicts),
        'by_type': {},
        'by_severity': {}
    }

    for conflict in conflicts:
        # Count by type
        conflict_type = conflict.type
        hybrid['conflict_summary']['by_type'][conflict_type] = \
            hybrid['conflict_summary']['by_type'].get(conflict_type, 0) + 1

        # Count by severity
        severity = conflict.severity
        hybrid['conflict_summary']['by_severity'][severity] = \
            hybrid['conflict_summary']['by_severity'].get(severity, 0) + 1

    # Add GitHub issue links for relevant APIs
    if github_insights:
        hybrid['issue_links'] = _match_issues_to_apis(
            api_data.get('apis', {}),
            github_insights.get('common_problems', []),
            github_insights.get('known_solutions', [])
        )

    return hybrid


def _match_issues_to_apis(
    apis: Dict[str, Dict],
    problems: List[Dict],
    solutions: List[Dict]
) -> Dict[str, List[Dict]]:
    """
    Match GitHub issues to specific APIs by keyword matching.

    Args:
        apis: Dict of API data keyed by name
        problems: List of common problems
        solutions: List of known solutions

    Returns:
        Dict mapping API names to relevant issues
    """
    issue_links = {}
    all_issues = problems + solutions

    for api_name in apis.keys():
        # Extract searchable keywords from API name
        api_keywords = api_name.lower().replace('_', ' ').split('.')

        matched_issues = []
        for issue in all_issues:
            title = issue.get('title', '').lower()
            labels = [label.lower() for label in issue.get('labels', [])]
            text = f"{title} {' '.join(labels)}"

            # Check if any API keyword appears in issue
            if any(keyword in text for keyword in api_keywords):
                matched_issues.append({
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'comments': issue.get('comments')
                })

        if matched_issues:
            issue_links[api_name] = matched_issues

    return issue_links


class RuleBasedMerger:
    """
    Rule-based API merger using deterministic rules with GitHub insights.

    Multi-layer architecture (Phase 3):
    - Layer 1: C3.x code (ground truth)
    - Layer 2: HTML docs (official intent)
    - Layer 3: GitHub docs (README/CONTRIBUTING)
    - Layer 4: GitHub insights (issues)

    Rules:
    1. If API only in docs → Include with [DOCS_ONLY] tag
    2. If API only in code → Include with [UNDOCUMENTED] tag
    3. If both match perfectly → Include normally
    4. If conflict → Include both versions with [CONFLICT] tag, prefer code signature
    """

    def __init__(self,
                 docs_data: Dict,
                 github_data: Dict,
                 conflicts: List[Conflict],
                 github_streams: Optional['ThreeStreamData'] = None):
        """
        Initialize rule-based merger with GitHub streams support.

        Args:
            docs_data: Documentation scraper data (Layer 2: HTML docs)
            github_data: GitHub scraper data (Layer 1: C3.x code)
            conflicts: List of detected conflicts
            github_streams: Optional ThreeStreamData with docs and insights (Layers 3-4)
        """
        self.docs_data = docs_data
        self.github_data = github_data
        self.conflicts = conflicts
        self.github_streams = github_streams

        # Build conflict index for fast lookup
        self.conflict_index = {c.api_name: c for c in conflicts}

        # Extract APIs from both sources
        detector = ConflictDetector(docs_data, github_data)
        self.docs_apis = detector.docs_apis
        self.code_apis = detector.code_apis

        # Extract GitHub streams if available
        self.github_docs = None
        self.github_insights = None
        if github_streams:
            # Layer 3: GitHub docs
            if github_streams.docs_stream:
                self.github_docs = {
                    'readme': github_streams.docs_stream.readme,
                    'contributing': github_streams.docs_stream.contributing,
                    'docs_files': github_streams.docs_stream.docs_files
                }

            # Layer 4: GitHub insights
            if github_streams.insights_stream:
                self.github_insights = {
                    'metadata': github_streams.insights_stream.metadata,
                    'common_problems': github_streams.insights_stream.common_problems,
                    'known_solutions': github_streams.insights_stream.known_solutions,
                    'top_labels': github_streams.insights_stream.top_labels
                }

    def merge_all(self) -> Dict[str, Any]:
        """
        Merge all APIs using rule-based logic with GitHub insights (Phase 3).

        Returns:
            Dict containing merged API data with hybrid content
        """
        logger.info("Starting rule-based merge with GitHub streams...")

        merged_apis = {}

        # Get all unique API names
        all_api_names = set(self.docs_apis.keys()) | set(self.code_apis.keys())

        for api_name in sorted(all_api_names):
            merged_api = self._merge_single_api(api_name)
            merged_apis[api_name] = merged_api

        logger.info(f"Merged {len(merged_apis)} APIs")

        # Build base result
        merged_data = {
            'merge_mode': 'rule-based',
            'apis': merged_apis,
            'summary': {
                'total_apis': len(merged_apis),
                'docs_only': sum(1 for api in merged_apis.values() if api['status'] == 'docs_only'),
                'code_only': sum(1 for api in merged_apis.values() if api['status'] == 'code_only'),
                'matched': sum(1 for api in merged_apis.values() if api['status'] == 'matched'),
                'conflict': sum(1 for api in merged_apis.values() if api['status'] == 'conflict')
            }
        }

        # Generate hybrid content if GitHub streams available (Phase 3)
        if self.github_streams:
            logger.info("Generating hybrid content with GitHub insights...")
            hybrid_content = generate_hybrid_content(
                api_data=merged_data,
                github_docs=self.github_docs,
                github_insights=self.github_insights,
                conflicts=self.conflicts
            )

            # Merge hybrid content into result
            merged_data['github_context'] = hybrid_content.get('github_context', {})
            merged_data['conflict_summary'] = hybrid_content.get('conflict_summary', {})
            merged_data['issue_links'] = hybrid_content.get('issue_links', {})

            logger.info(f"Added GitHub context: {len(self.github_insights.get('common_problems', []))} problems, "
                       f"{len(self.github_insights.get('known_solutions', []))} solutions")

        return merged_data

    def _merge_single_api(self, api_name: str) -> Dict[str, Any]:
        """
        Merge a single API using rules.

        Args:
            api_name: Name of the API to merge

        Returns:
            Merged API dict
        """
        in_docs = api_name in self.docs_apis
        in_code = api_name in self.code_apis
        has_conflict = api_name in self.conflict_index

        # Rule 1: Only in docs
        if in_docs and not in_code:
            conflict = self.conflict_index.get(api_name)
            return {
                'name': api_name,
                'status': 'docs_only',
                'source': 'documentation',
                'data': self.docs_apis[api_name],
                'warning': 'This API is documented but not found in codebase',
                'conflict': conflict.__dict__ if conflict else None
            }

        # Rule 2: Only in code
        if in_code and not in_docs:
            is_private = api_name.startswith('_')
            conflict = self.conflict_index.get(api_name)
            return {
                'name': api_name,
                'status': 'code_only',
                'source': 'code',
                'data': self.code_apis[api_name],
                'warning': 'This API exists in code but is not documented' if not is_private else 'Internal/private API',
                'conflict': conflict.__dict__ if conflict else None
            }

        # Both exist - check for conflicts
        docs_info = self.docs_apis[api_name]
        code_info = self.code_apis[api_name]

        # Rule 3: Both match perfectly (no conflict)
        if not has_conflict:
            return {
                'name': api_name,
                'status': 'matched',
                'source': 'both',
                'docs_data': docs_info,
                'code_data': code_info,
                'merged_signature': self._create_merged_signature(code_info, docs_info),
                'merged_description': docs_info.get('docstring') or code_info.get('docstring')
            }

        # Rule 4: Conflict exists - prefer code signature, keep docs description
        conflict = self.conflict_index[api_name]

        return {
            'name': api_name,
            'status': 'conflict',
            'source': 'both',
            'docs_data': docs_info,
            'code_data': code_info,
            'conflict': conflict.__dict__,
            'resolution': 'prefer_code_signature',
            'merged_signature': self._create_merged_signature(code_info, docs_info),
            'merged_description': docs_info.get('docstring') or code_info.get('docstring'),
            'warning': conflict.difference
        }

    def _create_merged_signature(self, code_info: Dict, docs_info: Dict) -> str:
        """
        Create merged signature preferring code data.

        Args:
            code_info: API info from code
            docs_info: API info from docs

        Returns:
            Merged signature string
        """
        name = code_info.get('name', docs_info.get('name'))
        params = code_info.get('parameters', docs_info.get('parameters', []))
        return_type = code_info.get('return_type', docs_info.get('return_type'))

        # Build parameter string
        param_strs = []
        for param in params:
            param_str = param['name']
            if param.get('type_hint'):
                param_str += f": {param['type_hint']}"
            if param.get('default'):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)

        signature = f"{name}({', '.join(param_strs)})"

        if return_type:
            signature += f" -> {return_type}"

        return signature


class ClaudeEnhancedMerger:
    """
    Claude-enhanced API merger using local Claude Code with GitHub insights.

    Opens Claude Code in a new terminal to intelligently reconcile conflicts.
    Uses the same approach as enhance_skill_local.py.

    Multi-layer architecture (Phase 3):
    - Layer 1: C3.x code (ground truth)
    - Layer 2: HTML docs (official intent)
    - Layer 3: GitHub docs (README/CONTRIBUTING)
    - Layer 4: GitHub insights (issues)
    """

    def __init__(self,
                 docs_data: Dict,
                 github_data: Dict,
                 conflicts: List[Conflict],
                 github_streams: Optional['ThreeStreamData'] = None):
        """
        Initialize Claude-enhanced merger with GitHub streams support.

        Args:
            docs_data: Documentation scraper data (Layer 2: HTML docs)
            github_data: GitHub scraper data (Layer 1: C3.x code)
            conflicts: List of detected conflicts
            github_streams: Optional ThreeStreamData with docs and insights (Layers 3-4)
        """
        self.docs_data = docs_data
        self.github_data = github_data
        self.conflicts = conflicts
        self.github_streams = github_streams

        # First do rule-based merge as baseline
        self.rule_merger = RuleBasedMerger(docs_data, github_data, conflicts, github_streams)

    def merge_all(self) -> Dict[str, Any]:
        """
        Merge all APIs using Claude enhancement.

        Returns:
            Dict containing merged API data
        """
        logger.info("Starting Claude-enhanced merge...")

        # Create temporary workspace
        workspace_dir = self._create_workspace()

        # Launch Claude Code for enhancement
        logger.info("Launching Claude Code for intelligent merging...")
        logger.info("Claude will analyze conflicts and create reconciled API reference")

        try:
            self._launch_claude_merge(workspace_dir)

            # Read enhanced results
            merged_data = self._read_merged_results(workspace_dir)

            logger.info("Claude-enhanced merge complete")
            return merged_data

        except Exception as e:
            logger.error(f"Claude enhancement failed: {e}")
            logger.info("Falling back to rule-based merge")
            return self.rule_merger.merge_all()

    def _create_workspace(self) -> str:
        """
        Create temporary workspace with merge context.

        Returns:
            Path to workspace directory
        """
        workspace = tempfile.mkdtemp(prefix='skill_merge_')
        logger.info(f"Created merge workspace: {workspace}")

        # Write context files for Claude
        self._write_context_files(workspace)

        return workspace

    def _write_context_files(self, workspace: str):
        """Write context files for Claude to analyze."""

        # 1. Write conflicts summary
        conflicts_file = os.path.join(workspace, 'conflicts.json')
        with open(conflicts_file, 'w') as f:
            json.dump({
                'conflicts': [c.__dict__ for c in self.conflicts],
                'summary': {
                    'total': len(self.conflicts),
                    'by_type': self._count_by_field('type'),
                    'by_severity': self._count_by_field('severity')
                }
            }, f, indent=2)

        # 2. Write documentation APIs
        docs_apis_file = os.path.join(workspace, 'docs_apis.json')
        detector = ConflictDetector(self.docs_data, self.github_data)
        with open(docs_apis_file, 'w') as f:
            json.dump(detector.docs_apis, f, indent=2)

        # 3. Write code APIs
        code_apis_file = os.path.join(workspace, 'code_apis.json')
        with open(code_apis_file, 'w') as f:
            json.dump(detector.code_apis, f, indent=2)

        # 4. Write merge instructions for Claude
        instructions = """# API Merge Task

You are merging API documentation from two sources:
1. Official documentation (user-facing)
2. Source code analysis (implementation reality)

## Context Files:
- `conflicts.json` - All detected conflicts between sources
- `docs_apis.json` - APIs from documentation
- `code_apis.json` - APIs from source code

## Your Task:
For each conflict, reconcile the differences intelligently:

1. **Prefer code signatures as source of truth**
   - Use actual parameter names, types, defaults from code
   - Code is what actually runs, docs might be outdated

2. **Keep documentation descriptions**
   - Docs are user-friendly, code comments might be technical
   - Keep the docs' explanation of what the API does

3. **Add implementation notes for discrepancies**
   - If docs differ from code, explain the difference
   - Example: "⚠️ The `snap` parameter exists in code but is not documented"

4. **Flag missing APIs clearly**
   - Missing in docs → Add [UNDOCUMENTED] tag
   - Missing in code → Add [REMOVED] or [DOCS_ERROR] tag

5. **Create unified API reference**
   - One definitive signature per API
   - Clear warnings about conflicts
   - Implementation notes where helpful

## Output Format:
Create `merged_apis.json` with this structure:

```json
{
  "apis": {
    "API.name": {
      "signature": "final_signature_here",
      "parameters": [...],
      "return_type": "type",
      "description": "user-friendly description",
      "implementation_notes": "Any discrepancies or warnings",
      "source": "both|docs_only|code_only",
      "confidence": "high|medium|low"
    }
  }
}
```

Take your time to analyze each conflict carefully. The goal is to create the most accurate and helpful API reference possible.
"""

        instructions_file = os.path.join(workspace, 'MERGE_INSTRUCTIONS.md')
        with open(instructions_file, 'w') as f:
            f.write(instructions)

        logger.info(f"Wrote context files to {workspace}")

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count conflicts by a specific field."""
        counts = {}
        for conflict in self.conflicts:
            value = getattr(conflict, field)
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _launch_claude_merge(self, workspace: str):
        """
        Launch Claude Code to perform merge.

        Similar to enhance_skill_local.py approach.
        """
        # Create a script that Claude will execute
        script_path = os.path.join(workspace, 'merge_script.sh')

        script_content = f"""#!/bin/bash
# Automatic merge script for Claude Code

cd "{workspace}"

echo "📊 Analyzing conflicts..."
cat conflicts.json | head -20

echo ""
echo "📖 Documentation APIs: $(cat docs_apis.json | grep -c '\"name\"')"
echo "💻 Code APIs: $(cat code_apis.json | grep -c '\"name\"')"
echo ""
echo "Please review the conflicts and create merged_apis.json"
echo "Follow the instructions in MERGE_INSTRUCTIONS.md"
echo ""
echo "When done, save merged_apis.json and close this terminal."

# Wait for user to complete merge
read -p "Press Enter when merge is complete..."
"""

        with open(script_path, 'w') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)

        # Open new terminal with Claude Code
        # Try different terminal emulators
        terminals = [
            ['x-terminal-emulator', '-e'],
            ['gnome-terminal', '--'],
            ['xterm', '-e'],
            ['konsole', '-e']
        ]

        for terminal_cmd in terminals:
            try:
                cmd = terminal_cmd + ['bash', script_path]
                subprocess.Popen(cmd)
                logger.info(f"Opened terminal with {terminal_cmd[0]}")
                break
            except FileNotFoundError:
                continue

        # Wait for merge to complete
        merged_file = os.path.join(workspace, 'merged_apis.json')
        logger.info(f"Waiting for merged results at: {merged_file}")
        logger.info("Close the terminal when done to continue...")

        # Poll for file existence
        import time
        timeout = 3600  # 1 hour max
        elapsed = 0
        while not os.path.exists(merged_file) and elapsed < timeout:
            time.sleep(5)
            elapsed += 5

        if not os.path.exists(merged_file):
            raise TimeoutError("Claude merge timed out after 1 hour")

    def _read_merged_results(self, workspace: str) -> Dict[str, Any]:
        """Read merged results from workspace."""
        merged_file = os.path.join(workspace, 'merged_apis.json')

        if not os.path.exists(merged_file):
            raise FileNotFoundError(f"Merged results not found: {merged_file}")

        with open(merged_file, 'r') as f:
            merged_data = json.load(f)

        return {
            'merge_mode': 'claude-enhanced',
            **merged_data
        }


def merge_sources(docs_data_path: str,
                  github_data_path: str,
                  output_path: str,
                  mode: str = 'rule-based',
                  github_streams: Optional['ThreeStreamData'] = None) -> Dict[str, Any]:
    """
    Merge documentation and GitHub data with optional GitHub streams (Phase 3).

    Multi-layer architecture:
    - Layer 1: C3.x code (ground truth)
    - Layer 2: HTML docs (official intent)
    - Layer 3: GitHub docs (README/CONTRIBUTING) - from github_streams
    - Layer 4: GitHub insights (issues) - from github_streams

    Args:
        docs_data_path: Path to documentation data JSON
        github_data_path: Path to GitHub data JSON
        output_path: Path to save merged output
        mode: 'rule-based' or 'claude-enhanced'
        github_streams: Optional ThreeStreamData with docs and insights

    Returns:
        Merged data dict with hybrid content
    """
    # Load data
    with open(docs_data_path, 'r') as f:
        docs_data = json.load(f)

    with open(github_data_path, 'r') as f:
        github_data = json.load(f)

    # Detect conflicts
    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector.detect_all_conflicts()

    logger.info(f"Detected {len(conflicts)} conflicts")

    # Log GitHub streams availability
    if github_streams:
        logger.info("GitHub streams available for multi-layer merge")
        if github_streams.docs_stream:
            logger.info(f"  - Docs stream: README, {len(github_streams.docs_stream.docs_files)} docs files")
        if github_streams.insights_stream:
            problems = len(github_streams.insights_stream.common_problems)
            solutions = len(github_streams.insights_stream.known_solutions)
            logger.info(f"  - Insights stream: {problems} problems, {solutions} solutions")

    # Merge based on mode
    if mode == 'claude-enhanced':
        merger = ClaudeEnhancedMerger(docs_data, github_data, conflicts, github_streams)
    else:
        merger = RuleBasedMerger(docs_data, github_data, conflicts, github_streams)

    merged_data = merger.merge_all()

    # Save merged data
    with open(output_path, 'w') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Merged data saved to: {output_path}")

    return merged_data


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Merge documentation and code sources')
    parser.add_argument('docs_data', help='Path to documentation data JSON')
    parser.add_argument('github_data', help='Path to GitHub data JSON')
    parser.add_argument('--output', '-o', default='merged_data.json', help='Output file path')
    parser.add_argument('--mode', '-m', choices=['rule-based', 'claude-enhanced'],
                       default='rule-based', help='Merge mode')

    args = parser.parse_args()

    merged = merge_sources(args.docs_data, args.github_data, args.output, args.mode)

    # Print summary
    summary = merged.get('summary', {})
    print(f"\n✅ Merge complete ({merged.get('merge_mode')})")
    print(f"   Total APIs: {summary.get('total_apis', 0)}")
    print(f"   Matched: {summary.get('matched', 0)}")
    print(f"   Docs only: {summary.get('docs_only', 0)}")
    print(f"   Code only: {summary.get('code_only', 0)}")
    print(f"   Conflicts: {summary.get('conflict', 0)}")
    print(f"\n📄 Saved to: {args.output}")
