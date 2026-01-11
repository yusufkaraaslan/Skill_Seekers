#!/usr/bin/env python3
"""
Unified Skill Builder

Generates final skill structure from merged multi-source data:
- SKILL.md with merged APIs and conflict warnings
- references/ with organized content by source
- Inline conflict markers (⚠️)
- Separate conflicts summary section

Supports mixed sources (documentation, GitHub, PDF) and highlights
discrepancies transparently.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedSkillBuilder:
    """
    Builds unified skill from multi-source data.
    """

    def __init__(self, config: Dict, scraped_data: Dict,
                 merged_data: Optional[Dict] = None, conflicts: Optional[List] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize skill builder.

        Args:
            config: Unified config dict
            scraped_data: Dict of scraped data by source type
            merged_data: Merged API data (if conflicts were resolved)
            conflicts: List of detected conflicts
            cache_dir: Optional cache directory for intermediate files
        """
        self.config = config
        self.scraped_data = scraped_data
        self.merged_data = merged_data
        self.conflicts = conflicts or []
        self.cache_dir = cache_dir

        self.name = config['name']
        self.description = config['description']
        self.skill_dir = f"output/{self.name}"

        # Create directories
        os.makedirs(self.skill_dir, exist_ok=True)
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

    def build(self):
        """Build complete skill structure."""
        logger.info(f"Building unified skill: {self.name}")

        # Generate main SKILL.md
        self._generate_skill_md()

        # Generate reference files by source
        self._generate_references()

        # Generate conflicts report (if any)
        if self.conflicts:
            self._generate_conflicts_report()

        logger.info(f"✅ Unified skill built: {self.skill_dir}/")

    def _load_source_skill_mds(self) -> Dict[str, str]:
        """Load standalone SKILL.md files from each source.

        Returns:
            Dict mapping source type to SKILL.md content
            e.g., {'documentation': '...', 'github': '...', 'pdf': '...'}
        """
        skill_mds = {}

        # Determine base directory for source SKILL.md files
        if self.cache_dir:
            sources_dir = Path(self.cache_dir) / "sources"
        else:
            sources_dir = Path("output")

        # Load documentation SKILL.md
        docs_skill_path = sources_dir / f"{self.name}_docs" / "SKILL.md"
        if docs_skill_path.exists():
            try:
                skill_mds['documentation'] = docs_skill_path.read_text(encoding='utf-8')
                logger.debug(f"Loaded documentation SKILL.md ({len(skill_mds['documentation'])} chars)")
            except IOError as e:
                logger.warning(f"Failed to read documentation SKILL.md: {e}")

        # Load ALL GitHub sources (multi-source support)
        github_sources = []
        for github_dir in sources_dir.glob(f"{self.name}_github_*"):
            github_skill_path = github_dir / "SKILL.md"
            if github_skill_path.exists():
                try:
                    content = github_skill_path.read_text(encoding='utf-8')
                    github_sources.append(content)
                    logger.debug(f"Loaded GitHub SKILL.md from {github_dir.name} ({len(content)} chars)")
                except IOError as e:
                    logger.warning(f"Failed to read GitHub SKILL.md from {github_dir.name}: {e}")

        if github_sources:
            # Concatenate all GitHub sources with separator
            skill_mds['github'] = '\n\n---\n\n'.join(github_sources)
            logger.debug(f"Combined {len(github_sources)} GitHub SKILL.md files")

        # Load ALL PDF sources (multi-source support)
        pdf_sources = []
        for pdf_dir in sources_dir.glob(f"{self.name}_pdf_*"):
            pdf_skill_path = pdf_dir / "SKILL.md"
            if pdf_skill_path.exists():
                try:
                    content = pdf_skill_path.read_text(encoding='utf-8')
                    pdf_sources.append(content)
                    logger.debug(f"Loaded PDF SKILL.md from {pdf_dir.name} ({len(content)} chars)")
                except IOError as e:
                    logger.warning(f"Failed to read PDF SKILL.md from {pdf_dir.name}: {e}")

        if pdf_sources:
            # Concatenate all PDF sources with separator
            skill_mds['pdf'] = '\n\n---\n\n'.join(pdf_sources)
            logger.debug(f"Combined {len(pdf_sources)} PDF SKILL.md files")

        logger.info(f"Loaded {len(skill_mds)} source SKILL.md files")
        return skill_mds

    def _parse_skill_md_sections(self, skill_md: str) -> Dict[str, str]:
        """Parse SKILL.md into sections by ## headers.

        Args:
            skill_md: Full SKILL.md content

        Returns:
            Dict mapping section name to content
            e.g., {'When to Use': '...', 'Quick Reference': '...'}
        """
        sections = {}
        current_section = None
        current_content = []

        lines = skill_md.split('\n')

        for line in lines:
            # Detect section header (## Header)
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line[3:].strip()
                # Remove emoji and markdown formatting
                current_section = current_section.split('](')[0]  # Remove links
                for emoji in ['📚', '🏗️', '⚠️', '🔧', '📖', '💡', '🎯', '📊', '🔍', '⚙️', '🧪', '📝', '🗂️', '📐', '⚡']:
                    current_section = current_section.replace(emoji, '').strip()
                current_content = []
            elif current_section:
                # Accumulate content for current section
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        logger.debug(f"Parsed {len(sections)} sections from SKILL.md")
        return sections

    def _synthesize_docs_github(self, skill_mds: Dict[str, str]) -> str:
        """Synthesize documentation + GitHub sources with weighted merge.

        Strategy:
        - Start with docs frontmatter and intro
        - Add GitHub metadata (stars, topics, language stats)
        - Merge "When to Use" from both sources
        - Merge "Quick Reference" from both sources
        - Include GitHub-specific sections (patterns, architecture)
        - Merge code examples (prioritize GitHub real usage)
        - Include Known Issues from GitHub
        - Fix placeholder text (httpx_docs → httpx)

        Args:
            skill_mds: Dict with 'documentation' and 'github' keys

        Returns:
            Synthesized SKILL.md content
        """
        docs_sections = self._parse_skill_md_sections(skill_mds.get('documentation', ''))
        github_sections = self._parse_skill_md_sections(skill_mds.get('github', ''))

        # Extract GitHub metadata from full content
        github_full = skill_mds.get('github', '')

        # Start with YAML frontmatter
        skill_name = self.name.lower().replace('_', '-').replace(' ', '-')[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        content = f"""---
name: {skill_name}
description: {desc}
---

# {self.name.title()}

{self.description}

## 📚 Sources

This skill synthesizes knowledge from multiple sources:

- ✅ **Official Documentation**: {self.config.get('sources', [{}])[0].get('base_url', 'N/A')}
- ✅ **GitHub Repository**: {[s for s in self.config.get('sources', []) if s.get('type') == 'github'][0].get('repo', 'N/A') if [s for s in self.config.get('sources', []) if s.get('type') == 'github'] else 'N/A'}

"""

        # Add GitHub Description and Metadata if present
        if 'Description' in github_sections:
            content += "## 📦 About\n\n"
            content += github_sections['Description'] + "\n\n"

        # Add Repository Info from GitHub
        if 'Repository Info' in github_sections:
            content += "### Repository Info\n\n"
            content += github_sections['Repository Info'] + "\n\n"

        # Add Language stats from GitHub
        if 'Languages' in github_sections:
            content += "### Languages\n\n"
            content += github_sections['Languages'] + "\n\n"

        content += "## 💡 When to Use This Skill\n\n"

        # Merge "When to Use" sections - Fix placeholder text
        when_to_use_added = False
        for key in ['When to Use This Skill', 'When to Use']:
            if key in docs_sections:
                # Fix placeholder text: httpx_docs → httpx
                when_content = docs_sections[key].replace('httpx_docs', self.name)
                when_content = when_content.replace('httpx_github', self.name)
                content += when_content + "\n\n"
                when_to_use_added = True
                break

        if 'When to Use This Skill' in github_sections:
            if when_to_use_added:
                content += "**From repository analysis:**\n\n"
            content += github_sections['When to Use This Skill'] + "\n\n"

        # Quick Reference: Merge from both sources
        content += "## 🎯 Quick Reference\n\n"

        if 'Quick Reference' in docs_sections:
            content += "**From Documentation:**\n\n"
            content += docs_sections['Quick Reference'] + "\n\n"

        if 'Quick Reference' in github_sections:
            # Include GitHub's Quick Reference (contains design patterns summary)
            logger.info(f"DEBUG: Including GitHub Quick Reference ({len(github_sections['Quick Reference'])} chars)")
            content += github_sections['Quick Reference'] + "\n\n"
        else:
            logger.warning("DEBUG: GitHub Quick Reference section NOT FOUND!")

        # Design Patterns (GitHub only - C3.1 analysis)
        if 'Design Patterns Detected' in github_sections:
            content += "### Design Patterns Detected\n\n"
            content += "*From C3.1 codebase analysis (confidence > 0.7)*\n\n"
            content += github_sections['Design Patterns Detected'] + "\n\n"

        # Code Examples: Prefer GitHub (real usage)
        content += "## 🧪 Code Examples\n\n"

        if 'Code Examples' in github_sections:
            content += "**From Repository Tests:**\n\n"
            # Note: GitHub section already includes "*High-quality examples from codebase (C3.2)*" label
            content += github_sections['Code Examples'] + "\n\n"
        elif 'Usage Examples' in github_sections:
            content += "**From Repository:**\n\n"
            content += github_sections['Usage Examples'] + "\n\n"

        if 'Example Code Patterns' in docs_sections:
            content += "**From Documentation:**\n\n"
            content += docs_sections['Example Code Patterns'] + "\n\n"

        # API Reference: Include from both sources
        if 'API Reference' in docs_sections or 'API Reference' in github_sections:
            content += "## 🔧 API Reference\n\n"

            if 'API Reference' in github_sections:
                # Note: GitHub section already includes "*Extracted from codebase analysis (C2.5)*" label
                content += github_sections['API Reference'] + "\n\n"

            if 'API Reference' in docs_sections:
                content += "**Official API Documentation:**\n\n"
                content += docs_sections['API Reference'] + "\n\n"

        # Known Issues: GitHub only
        if 'Known Issues' in github_sections:
            content += "## ⚠️ Known Issues\n\n"
            content += "*Recent issues from GitHub*\n\n"
            content += github_sections['Known Issues'] + "\n\n"

        # Recent Releases: GitHub only (include subsection if present)
        if 'Recent Releases' in github_sections:
            # Recent Releases might be a subsection within Known Issues
            # Check if it's standalone
            releases_content = github_sections['Recent Releases']
            if releases_content.strip() and not releases_content.startswith('###'):
                content += "### Recent Releases\n"
            content += releases_content + "\n\n"

        # Reference documentation
        content += "## 📖 Reference Documentation\n\n"
        content += "Organized by source:\n\n"
        content += "- [Documentation](references/documentation/)\n"
        content += "- [GitHub](references/github/)\n"
        content += "- [Codebase Analysis](references/codebase_analysis/ARCHITECTURE.md)\n\n"

        # Footer
        content += "---\n\n"
        content += "*Synthesized from official documentation and codebase analysis by Skill Seekers*\n"

        return content

    def _synthesize_docs_github_pdf(self, skill_mds: Dict[str, str]) -> str:
        """Synthesize all three sources: documentation + GitHub + PDF.

        Strategy:
        - Start with docs+github synthesis
        - Insert PDF chapters after Quick Reference
        - Add PDF key concepts as supplementary section

        Args:
            skill_mds: Dict with 'documentation', 'github', and 'pdf' keys

        Returns:
            Synthesized SKILL.md content
        """
        # Start with docs+github synthesis
        base_content = self._synthesize_docs_github(skill_mds)
        pdf_sections = self._parse_skill_md_sections(skill_mds.get('pdf', ''))

        # Find insertion point after Quick Reference
        lines = base_content.split('\n')
        insertion_index = -1

        for i, line in enumerate(lines):
            if line.startswith('## 🧪 Code Examples') or line.startswith('## 🔧 API Reference'):
                insertion_index = i
                break

        if insertion_index == -1:
            # Fallback: insert before Reference Documentation
            for i, line in enumerate(lines):
                if line.startswith('## 📖 Reference Documentation'):
                    insertion_index = i
                    break

        # Build PDF section
        pdf_content_lines = []

        # Add Chapter Overview
        if 'Chapter Overview' in pdf_sections:
            pdf_content_lines.append("## 📚 PDF Documentation Structure\n")
            pdf_content_lines.append("*From PDF analysis*\n")
            pdf_content_lines.append(pdf_sections['Chapter Overview'])
            pdf_content_lines.append("\n")

        # Add Key Concepts
        if 'Key Concepts' in pdf_sections:
            pdf_content_lines.append("## 🔍 Key Concepts\n")
            pdf_content_lines.append("*Extracted from PDF headings*\n")
            pdf_content_lines.append(pdf_sections['Key Concepts'])
            pdf_content_lines.append("\n")

        # Insert PDF content
        if pdf_content_lines and insertion_index != -1:
            lines[insertion_index:insertion_index] = pdf_content_lines
        elif pdf_content_lines:
            # Append at end before footer
            footer_index = -1
            for i, line in enumerate(lines):
                if line.startswith('---') and i > len(lines) - 5:
                    footer_index = i
                    break
            if footer_index != -1:
                lines[footer_index:footer_index] = pdf_content_lines

        # Update reference documentation to include PDF
        final_content = '\n'.join(lines)
        final_content = final_content.replace(
            '- [Codebase Analysis](references/codebase_analysis/ARCHITECTURE.md)\n',
            '- [Codebase Analysis](references/codebase_analysis/ARCHITECTURE.md)\n- [PDF Documentation](references/pdf/)\n'
        )

        return final_content

    def _generate_skill_md(self):
        """Generate main SKILL.md file using synthesis formulas.

        Strategy:
        1. Try to load standalone SKILL.md from each source
        2. If found, use synthesis formulas for rich content
        3. If not found, fall back to legacy minimal generation
        """
        skill_path = os.path.join(self.skill_dir, 'SKILL.md')

        # Try to load source SKILL.md files
        skill_mds = self._load_source_skill_mds()

        # Determine synthesis strategy based on available sources
        has_docs = 'documentation' in skill_mds
        has_github = 'github' in skill_mds
        has_pdf = 'pdf' in skill_mds

        content = None

        # Apply appropriate synthesis formula
        if has_docs and has_github and has_pdf:
            logger.info("Synthesizing: documentation + GitHub + PDF")
            content = self._synthesize_docs_github_pdf(skill_mds)

        elif has_docs and has_github:
            logger.info("Synthesizing: documentation + GitHub")
            content = self._synthesize_docs_github(skill_mds)

        elif has_docs and has_pdf:
            logger.info("Synthesizing: documentation + PDF")
            content = self._synthesize_docs_pdf(skill_mds)

        elif has_github and has_pdf:
            logger.info("Synthesizing: GitHub + PDF")
            content = self._synthesize_github_pdf(skill_mds)

        elif has_docs:
            logger.info("Using documentation SKILL.md as-is")
            content = skill_mds['documentation']

        elif has_github:
            logger.info("Using GitHub SKILL.md as-is")
            content = skill_mds['github']

        elif has_pdf:
            logger.info("Using PDF SKILL.md as-is")
            content = skill_mds['pdf']

        # Fallback: generate minimal SKILL.md (legacy behavior)
        if not content:
            logger.warning("No source SKILL.md files found, generating minimal SKILL.md (legacy)")
            content = self._generate_minimal_skill_md()

        # Write final content
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created SKILL.md ({len(content)} chars, ~{len(content.split())} words)")

    def _synthesize_docs_pdf(self, skill_mds: Dict[str, str]) -> str:
        """Synthesize documentation + PDF sources.

        Strategy:
        - Start with docs SKILL.md
        - Insert PDF chapters and key concepts as supplementary sections

        Args:
            skill_mds: Dict with 'documentation' and 'pdf' keys

        Returns:
            Synthesized SKILL.md content
        """
        docs_content = skill_mds['documentation']
        pdf_sections = self._parse_skill_md_sections(skill_mds['pdf'])

        lines = docs_content.split('\n')
        insertion_index = -1

        # Find insertion point before Reference Documentation
        for i, line in enumerate(lines):
            if line.startswith('## 📖 Reference') or line.startswith('## Reference'):
                insertion_index = i
                break

        # Build PDF sections
        pdf_content_lines = []

        if 'Chapter Overview' in pdf_sections:
            pdf_content_lines.append("## 📚 PDF Documentation Structure\n")
            pdf_content_lines.append("*From PDF analysis*\n")
            pdf_content_lines.append(pdf_sections['Chapter Overview'])
            pdf_content_lines.append("\n")

        if 'Key Concepts' in pdf_sections:
            pdf_content_lines.append("## 🔍 Key Concepts\n")
            pdf_content_lines.append("*Extracted from PDF headings*\n")
            pdf_content_lines.append(pdf_sections['Key Concepts'])
            pdf_content_lines.append("\n")

        # Insert PDF content
        if pdf_content_lines and insertion_index != -1:
            lines[insertion_index:insertion_index] = pdf_content_lines

        return '\n'.join(lines)

    def _synthesize_github_pdf(self, skill_mds: Dict[str, str]) -> str:
        """Synthesize GitHub + PDF sources.

        Strategy:
        - Start with GitHub SKILL.md (has C3.x analysis)
        - Add PDF documentation structure as supplementary section

        Args:
            skill_mds: Dict with 'github' and 'pdf' keys

        Returns:
            Synthesized SKILL.md content
        """
        github_content = skill_mds['github']
        pdf_sections = self._parse_skill_md_sections(skill_mds['pdf'])

        lines = github_content.split('\n')
        insertion_index = -1

        # Find insertion point before Reference Documentation
        for i, line in enumerate(lines):
            if line.startswith('## 📖 Reference') or line.startswith('## Reference'):
                insertion_index = i
                break

        # Build PDF sections
        pdf_content_lines = []

        if 'Chapter Overview' in pdf_sections:
            pdf_content_lines.append("## 📚 PDF Documentation Structure\n")
            pdf_content_lines.append("*From PDF analysis*\n")
            pdf_content_lines.append(pdf_sections['Chapter Overview'])
            pdf_content_lines.append("\n")

        # Insert PDF content
        if pdf_content_lines and insertion_index != -1:
            lines[insertion_index:insertion_index] = pdf_content_lines

        return '\n'.join(lines)

    def _generate_minimal_skill_md(self) -> str:
        """Generate minimal SKILL.md (legacy fallback behavior).

        Used when no source SKILL.md files are available.
        """
        skill_name = self.name.lower().replace('_', '-').replace(' ', '-')[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        content = f"""---
name: {skill_name}
description: {desc}
---

# {self.name.title()}

{self.description}

## 📚 Sources

This skill combines knowledge from multiple sources:

"""

        # List sources
        for source in self.config.get('sources', []):
            source_type = source['type']
            if source_type == 'documentation':
                content += f"- ✅ **Documentation**: {source.get('base_url', 'N/A')}\n"
                content += f"  - Pages: {source.get('max_pages', 'unlimited')}\n"
            elif source_type == 'github':
                content += f"- ✅ **GitHub Repository**: {source.get('repo', 'N/A')}\n"
                content += f"  - Code Analysis: {source.get('code_analysis_depth', 'surface')}\n"
                content += f"  - Issues: {source.get('max_issues', 0)}\n"
            elif source_type == 'pdf':
                content += f"- ✅ **PDF Document**: {source.get('path', 'N/A')}\n"

        # C3.x Architecture & Code Analysis section (if available)
        github_data = self.scraped_data.get('github', {}).get('data', {})
        if github_data.get('c3_analysis'):
            content += self._format_c3_summary_section(github_data['c3_analysis'])

        # Data quality section
        if self.conflicts:
            content += f"\n## ⚠️ Data Quality\n\n"
            content += f"**{len(self.conflicts)} conflicts detected** between sources.\n\n"

            # Count by type
            by_type = {}
            for conflict in self.conflicts:
                ctype = conflict.type if hasattr(conflict, 'type') else conflict.get('type', 'unknown')
                by_type[ctype] = by_type.get(ctype, 0) + 1

            content += "**Conflict Breakdown:**\n"
            for ctype, count in by_type.items():
                content += f"- {ctype}: {count}\n"

            content += f"\nSee `references/conflicts.md` for detailed conflict information.\n"

        # Merged API section (if available)
        if self.merged_data:
            content += self._format_merged_apis()

        # Quick reference from each source
        content += "\n## 📖 Reference Documentation\n\n"
        content += "Organized by source:\n\n"

        for source in self.config.get('sources', []):
            source_type = source['type']
            content += f"- [{source_type.title()}](references/{source_type}/)\n"

        # When to use this skill
        content += f"\n## 💡 When to Use This Skill\n\n"
        content += f"Use this skill when you need to:\n"
        content += f"- Understand how to use {self.name}\n"
        content += f"- Look up API documentation\n"
        content += f"- Find usage examples\n"

        if 'github' in self.scraped_data:
            content += f"- Check for known issues or recent changes\n"
            content += f"- Review release history\n"

        content += "\n---\n\n"
        content += "*Generated by Skill Seeker's unified multi-source scraper*\n"

        return content

    def _format_merged_apis(self) -> str:
        """Format merged APIs section with inline conflict warnings."""
        if not self.merged_data:
            return ""

        content = "\n## 🔧 API Reference\n\n"
        content += "*Merged from documentation and code analysis*\n\n"

        apis = self.merged_data.get('apis', {})

        if not apis:
            return content + "*No APIs to display*\n"

        # Group APIs by status
        matched = {k: v for k, v in apis.items() if v.get('status') == 'matched'}
        conflicts = {k: v for k, v in apis.items() if v.get('status') == 'conflict'}
        docs_only = {k: v for k, v in apis.items() if v.get('status') == 'docs_only'}
        code_only = {k: v for k, v in apis.items() if v.get('status') == 'code_only'}

        # Show matched APIs first
        if matched:
            content += "### ✅ Verified APIs\n\n"
            content += "*Documentation and code agree*\n\n"
            for api_name, api_data in list(matched.items())[:10]:  # Limit to first 10
                content += self._format_api_entry(api_data, inline_conflict=False)

        # Show conflicting APIs with warnings
        if conflicts:
            content += "\n### ⚠️ APIs with Conflicts\n\n"
            content += "*Documentation and code differ*\n\n"
            for api_name, api_data in list(conflicts.items())[:10]:
                content += self._format_api_entry(api_data, inline_conflict=True)

        # Show undocumented APIs
        if code_only:
            content += f"\n### 💻 Undocumented APIs\n\n"
            content += f"*Found in code but not in documentation ({len(code_only)} total)*\n\n"
            for api_name, api_data in list(code_only.items())[:5]:
                content += self._format_api_entry(api_data, inline_conflict=False)

        # Show removed/missing APIs
        if docs_only:
            content += f"\n### 📖 Documentation-Only APIs\n\n"
            content += f"*Documented but not found in code ({len(docs_only)} total)*\n\n"
            for api_name, api_data in list(docs_only.items())[:5]:
                content += self._format_api_entry(api_data, inline_conflict=False)

        content += f"\n*See references/api/ for complete API documentation*\n"

        return content

    def _format_api_entry(self, api_data: Dict, inline_conflict: bool = False) -> str:
        """Format a single API entry."""
        name = api_data.get('name', 'Unknown')
        signature = api_data.get('merged_signature', name)
        description = api_data.get('merged_description', '')
        warning = api_data.get('warning', '')

        entry = f"#### `{signature}`\n\n"

        if description:
            entry += f"{description}\n\n"

        # Add inline conflict warning
        if inline_conflict and warning:
            entry += f"⚠️ **Conflict**: {warning}\n\n"

            # Show both versions if available
            conflict = api_data.get('conflict', {})
            if conflict:
                docs_info = conflict.get('docs_info')
                code_info = conflict.get('code_info')

                if docs_info and code_info:
                    entry += "**Documentation says:**\n"
                    entry += f"```\n{docs_info.get('raw_signature', 'N/A')}\n```\n\n"
                    entry += "**Code implementation:**\n"
                    entry += f"```\n{self._format_code_signature(code_info)}\n```\n\n"

        # Add source info
        source = api_data.get('source', 'unknown')
        entry += f"*Source: {source}*\n\n"

        entry += "---\n\n"

        return entry

    def _format_code_signature(self, code_info: Dict) -> str:
        """Format code signature for display."""
        name = code_info.get('name', '')
        params = code_info.get('parameters', [])
        return_type = code_info.get('return_type')

        param_strs = []
        for param in params:
            param_str = param.get('name', '')
            if param.get('type_hint'):
                param_str += f": {param['type_hint']}"
            if param.get('default'):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)

        sig = f"{name}({', '.join(param_strs)})"
        if return_type:
            sig += f" -> {return_type}"

        return sig

    def _generate_references(self):
        """Generate reference files organized by source."""
        logger.info("Generating reference files...")

        # Generate references for each source type (now lists)
        docs_list = self.scraped_data.get('documentation', [])
        if docs_list:
            self._generate_docs_references(docs_list)

        github_list = self.scraped_data.get('github', [])
        if github_list:
            self._generate_github_references(github_list)

        pdf_list = self.scraped_data.get('pdf', [])
        if pdf_list:
            self._generate_pdf_references(pdf_list)

        # Generate merged API reference if available
        if self.merged_data:
            self._generate_merged_api_reference()

        # Generate C3.x codebase analysis references if available (multi-source)
        github_list = self.scraped_data.get('github', [])
        for github_source in github_list:
            github_data = github_source.get('data', {})
            if github_data.get('c3_analysis'):
                repo_id = github_source.get('repo_id', 'unknown')
                self._generate_c3_analysis_references(repo_id=repo_id)

    def _generate_docs_references(self, docs_list: List[Dict]):
        """Generate references from multiple documentation sources."""
        # Skip if no documentation sources
        if not docs_list:
            return

        docs_dir = os.path.join(self.skill_dir, 'references', 'documentation')
        os.makedirs(docs_dir, exist_ok=True)

        all_copied_files: List[str] = []

        # Process each documentation source
        for i, doc_source in enumerate(docs_list):
            source_id = doc_source.get('source_id', f'source_{i}')
            base_url = doc_source.get('base_url', 'Unknown')
            refs_dir = doc_source.get('refs_dir', '')

            # Create subdirectory for this source
            source_dir = os.path.join(docs_dir, source_id)
            os.makedirs(source_dir, exist_ok=True)

            copied_files: List[str] = []

            if refs_dir and os.path.isdir(refs_dir):
                for entry in sorted(os.listdir(refs_dir)):
                    src_path = os.path.join(refs_dir, entry)
                    dst_path = os.path.join(source_dir, entry)
                    if not os.path.isfile(src_path):
                        continue
                    shutil.copy2(src_path, dst_path)
                    copied_files.append(entry)

            # Create index for this source
            source_index_path = os.path.join(source_dir, 'index.md')
            with open(source_index_path, 'w', encoding='utf-8') as f:
                f.write(f"# Documentation: {source_id}\n\n")
                f.write(f"**Source**: {base_url}\n\n")
                f.write(f"**Pages**: {doc_source.get('total_pages', 'N/A')}\n\n")

                if copied_files:
                    files_no_index = [p for p in copied_files if p.lower() != 'index.md']
                    f.write("## Files\n\n")
                    for filename in files_no_index:
                        f.write(f"- [{filename}]({filename})\n")
                else:
                    f.write("No reference files available.\n")

            all_copied_files.extend(copied_files)

        # Create main index
        index_path = os.path.join(docs_dir, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Documentation References\n\n")
            f.write(f"Combined from {len(docs_list)} documentation sources.\n\n")

            f.write("## Sources\n\n")
            for doc_source in docs_list:
                source_id = doc_source.get('source_id', 'unknown')
                base_url = doc_source.get('base_url', 'Unknown')
                total_pages = doc_source.get('total_pages', 'N/A')
                f.write(f"- [{source_id}]({source_id}/index.md) - {base_url} ({total_pages} pages)\n")

        logger.info(f"Created documentation references ({len(docs_list)} sources)")

    def _generate_github_references(self, github_list: List[Dict]):
        """Generate references from multiple GitHub sources."""
        # Skip if no GitHub sources
        if not github_list:
            return

        github_dir = os.path.join(self.skill_dir, 'references', 'github')
        os.makedirs(github_dir, exist_ok=True)

        # Process each GitHub source
        for i, github_source in enumerate(github_list):
            repo = github_source.get('repo', f'repo_{i}')
            repo_id = github_source.get('repo_id', repo.replace('/', '_'))
            github_data = github_source.get('data', {})

            # Create subdirectory for this repo
            repo_dir = os.path.join(github_dir, repo_id)
            os.makedirs(repo_dir, exist_ok=True)

            # Create README reference
            if github_data.get('readme'):
                readme_path = os.path.join(repo_dir, 'README.md')
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Repository README: {repo}\n\n")
                    f.write(github_data['readme'])

            # Create issues reference
            if github_data.get('issues'):
                issues_path = os.path.join(repo_dir, 'issues.md')
                with open(issues_path, 'w', encoding='utf-8') as f:
                    f.write(f"# GitHub Issues: {repo}\n\n")
                    f.write(f"{len(github_data['issues'])} recent issues.\n\n")

                    for issue in github_data['issues'][:20]:
                        f.write(f"## #{issue['number']}: {issue['title']}\n\n")
                        f.write(f"**State**: {issue['state']}\n")
                        if issue.get('labels'):
                            f.write(f"**Labels**: {', '.join(issue['labels'])}\n")
                        f.write(f"**URL**: {issue.get('url', 'N/A')}\n\n")

            # Create releases reference
            if github_data.get('releases'):
                releases_path = os.path.join(repo_dir, 'releases.md')
                with open(releases_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Releases: {repo}\n\n")

                    for release in github_data['releases'][:10]:
                        f.write(f"## {release['tag_name']}: {release.get('name', 'N/A')}\n\n")
                        f.write(f"**Published**: {release.get('published_at', 'N/A')[:10]}\n\n")
                        if release.get('body'):
                            f.write(release['body'][:500])
                            f.write("\n\n")

            # Create index for this repo
            repo_index_path = os.path.join(repo_dir, 'index.md')
            repo_info = github_data.get('repo_info', {})
            with open(repo_index_path, 'w', encoding='utf-8') as f:
                f.write(f"# GitHub: {repo}\n\n")
                f.write(f"**Stars**: {repo_info.get('stars', 'N/A')}\n")
                f.write(f"**Language**: {repo_info.get('language', 'N/A')}\n")
                f.write(f"**Issues**: {len(github_data.get('issues', []))}\n")
                f.write(f"**Releases**: {len(github_data.get('releases', []))}\n\n")
                f.write("## Files\n\n")
                f.write("- [README.md](README.md)\n")
                if github_data.get('issues'):
                    f.write("- [issues.md](issues.md)\n")
                if github_data.get('releases'):
                    f.write("- [releases.md](releases.md)\n")

        # Create main index
        index_path = os.path.join(github_dir, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# GitHub References\n\n")
            f.write(f"Combined from {len(github_list)} GitHub repositories.\n\n")

            f.write("## Repositories\n\n")
            for github_source in github_list:
                repo = github_source.get('repo', 'unknown')
                repo_id = github_source.get('repo_id', repo.replace('/', '_'))
                github_data = github_source.get('data', {})
                repo_info = github_data.get('repo_info', {})
                stars = repo_info.get('stars', 'N/A')
                f.write(f"- [{repo}]({repo_id}/index.md) - {stars} stars\n")

        logger.info(f"Created GitHub references ({len(github_list)} repos)")

    def _generate_pdf_references(self, pdf_list: List[Dict]):
        """Generate references from PDF sources."""
        # Skip if no PDF sources
        if not pdf_list:
            return

        pdf_dir = os.path.join(self.skill_dir, 'references', 'pdf')
        os.makedirs(pdf_dir, exist_ok=True)

        # Create index
        index_path = os.path.join(pdf_dir, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# PDF Documentation\n\n")
            f.write(f"Reference from {len(pdf_list)} PDF document(s).\n\n")

        logger.info(f"Created PDF references ({len(pdf_list)} sources)")

    def _generate_merged_api_reference(self):
        """Generate merged API reference file."""
        api_dir = os.path.join(self.skill_dir, 'references', 'api')
        os.makedirs(api_dir, exist_ok=True)

        api_path = os.path.join(api_dir, 'merged_api.md')

        with open(api_path, 'w') as f:
            f.write("# Merged API Reference\n\n")
            f.write("*Combined from documentation and code analysis*\n\n")

            apis = self.merged_data.get('apis', {})

            for api_name in sorted(apis.keys()):
                api_data = apis[api_name]
                entry = self._format_api_entry(api_data, inline_conflict=True)
                f.write(entry)

        logger.info(f"Created merged API reference ({len(apis)} APIs)")

    def _generate_c3_analysis_references(self, repo_id: str = 'github'):
        """Generate codebase analysis references (C3.5) for a specific GitHub source.

        Args:
            repo_id: Repository identifier (e.g., 'encode_httpx') for multi-source support
        """
        # Find the correct github_source from the list
        github_list = self.scraped_data.get('github', [])
        github_source = None
        for source in github_list:
            if source.get('repo_id') == repo_id:
                github_source = source
                break

        if not github_source:
            logger.warning(f"GitHub source with repo_id '{repo_id}' not found")
            return

        github_data = github_source.get('data', {})
        c3_data = github_data.get('c3_analysis')

        if not c3_data:
            return

        # Create unique directory per repo for multi-source support
        c3_dir = os.path.join(self.skill_dir, 'references', 'codebase_analysis', repo_id)
        os.makedirs(c3_dir, exist_ok=True)

        logger.info("Generating C3.x codebase analysis references...")

        # Generate ARCHITECTURE.md (main deliverable)
        self._generate_architecture_overview(c3_dir, c3_data, github_data)

        # Generate subdirectories for each C3.x component
        self._generate_pattern_references(c3_dir, c3_data.get('patterns'))
        self._generate_example_references(c3_dir, c3_data.get('test_examples'))
        self._generate_guide_references(c3_dir, c3_data.get('how_to_guides'))
        self._generate_config_references(c3_dir, c3_data.get('config_patterns'))
        self._copy_architecture_details(c3_dir, c3_data.get('architecture'))

        logger.info("✅ Created codebase analysis references")

    def _generate_architecture_overview(self, c3_dir: str, c3_data: Dict, github_data: Dict):
        """Generate comprehensive ARCHITECTURE.md (C3.5 main deliverable)."""
        arch_path = os.path.join(c3_dir, 'ARCHITECTURE.md')

        with open(arch_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.name.title()} Architecture Overview\n\n")
            f.write("*Generated from C3.x automated codebase analysis*\n\n")

            # Section 1: Overview
            f.write("## 1. Overview\n\n")
            f.write(f"{self.description}\n\n")

            # Section 2: Architectural Patterns (C3.7)
            if c3_data.get('architecture'):
                arch = c3_data['architecture']
                patterns = arch.get('patterns', [])
                if patterns:
                    f.write("## 2. Architectural Patterns\n\n")
                    f.write("*Detected architectural patterns from codebase structure*\n\n")
                    for pattern in patterns[:5]:  # Top 5 patterns
                        f.write(f"### {pattern['pattern_name']}\n\n")
                        f.write(f"- **Confidence**: {pattern['confidence']:.2f}\n")
                        if pattern.get('framework'):
                            f.write(f"- **Framework**: {pattern['framework']}\n")
                        if pattern.get('evidence'):
                            f.write(f"- **Evidence**: {', '.join(pattern['evidence'][:3])}\n")
                        f.write("\n")

            # Section 3: Technology Stack
            f.write("## 3. Technology Stack\n\n")

            # Try to get languages from C3.7 architecture analysis first
            languages = {}
            if c3_data.get('architecture'):
                languages = c3_data['architecture'].get('languages', {})

            # If no languages from C3.7, try to get from GitHub data
            if not languages:
                # github_data already available from method scope
                if github_data.get('languages'):
                    # GitHub data has languages as list, convert to dict with count 1
                    languages = {lang: 1 for lang in github_data['languages']}

            if languages:
                f.write("**Languages Detected**:\n")
                for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                    if isinstance(count, int):
                        f.write(f"- {lang}: {count} files\n")
                    else:
                        f.write(f"- {lang}\n")
                f.write("\n")

            # Add frameworks if available
            if c3_data.get('architecture'):
                frameworks = c3_data['architecture'].get('frameworks_detected', [])
                if frameworks:
                    f.write("**Frameworks & Libraries**:\n")
                    for fw in frameworks[:10]:
                        f.write(f"- {fw}\n")
                    f.write("\n")

            if not languages and not (c3_data.get('architecture') and c3_data['architecture'].get('frameworks_detected')):
                f.write("*Technology stack analysis not available*\n\n")

            # Section 4: Design Patterns (C3.1)
            if c3_data.get('patterns'):
                f.write("## 4. Design Patterns\n\n")
                f.write("*Classic design patterns identified in the codebase*\n\n")

                # Summarize pattern types
                pattern_summary = {}
                for file_data in c3_data['patterns']:
                    for pattern in file_data.get('patterns', []):
                        ptype = pattern['pattern_type']
                        pattern_summary[ptype] = pattern_summary.get(ptype, 0) + 1

                if pattern_summary:
                    for ptype, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- **{ptype}**: {count} instance(s)\n")
                    f.write(f"\n📁 See `references/codebase_analysis/patterns/` for detailed analysis.\n\n")
                else:
                    f.write("*No design patterns detected.*\n\n")

            # Section 5: Configuration Overview (C3.4)
            if c3_data.get('config_patterns'):
                f.write("## 5. Configuration Overview\n\n")
                config = c3_data['config_patterns']
                config_files = config.get('config_files', [])

                if config_files:
                    f.write(f"**{len(config_files)} configuration file(s) detected**:\n\n")
                    for cf in config_files[:10]:  # Top 10
                        f.write(f"- **`{cf['relative_path']}`**: {cf['type']}\n")
                        if cf.get('purpose'):
                            f.write(f"  - Purpose: {cf['purpose']}\n")

                    # Add security warnings if available
                    if config.get('ai_enhancements'):
                        insights = config['ai_enhancements'].get('overall_insights', {})
                        security_issues = insights.get('security_issues_found', 0)
                        if security_issues > 0:
                            f.write(f"\n🔐 **Security Alert**: {security_issues} potential security issue(s) found in configurations.\n")
                            if insights.get('recommended_actions'):
                                f.write("\n**Recommended Actions**:\n")
                                for action in insights['recommended_actions'][:5]:
                                    f.write(f"- {action}\n")
                    f.write(f"\n📁 See `references/codebase_analysis/configuration/` for details.\n\n")
                else:
                    f.write("*No configuration files detected.*\n\n")

            # Section 6: Common Workflows (C3.3)
            if c3_data.get('how_to_guides'):
                f.write("## 6. Common Workflows\n\n")
                guides = c3_data['how_to_guides'].get('guides', [])

                if guides:
                    f.write(f"**{len(guides)} how-to guide(s) extracted from codebase**:\n\n")
                    for guide in guides[:10]:  # Top 10
                        f.write(f"- {guide.get('title', 'Untitled Guide')}\n")
                    f.write(f"\n📁 See `references/codebase_analysis/guides/` for detailed tutorials.\n\n")
                else:
                    f.write("*No workflow guides extracted.*\n\n")

            # Section 7: Usage Examples (C3.2)
            if c3_data.get('test_examples'):
                f.write("## 7. Usage Examples\n\n")
                examples = c3_data['test_examples']
                total = examples.get('total_examples', 0)
                high_value = examples.get('high_value_count', 0)

                if total > 0:
                    f.write(f"**{total} usage example(s) extracted from tests**:\n")
                    f.write(f"- High-value examples: {high_value}\n")

                    # Category breakdown
                    if examples.get('examples_by_category'):
                        f.write("\n**By Category**:\n")
                        for cat, count in sorted(examples['examples_by_category'].items(), key=lambda x: x[1], reverse=True):
                            f.write(f"- {cat}: {count}\n")

                    f.write(f"\n📁 See `references/codebase_analysis/examples/` for code samples.\n\n")
                else:
                    f.write("*No test examples extracted.*\n\n")

            # Section 8: Entry Points & Directory Structure
            f.write("## 8. Entry Points & Directory Structure\n\n")
            f.write("*Analysis based on codebase organization*\n\n")

            if c3_data.get('architecture'):
                dir_struct = c3_data['architecture'].get('directory_structure', {})
                if dir_struct:
                    f.write("**Main Directories**:\n")
                    for dir_name, file_count in sorted(dir_struct.items(), key=lambda x: x[1], reverse=True)[:15]:
                        f.write(f"- `{dir_name}/`: {file_count} file(s)\n")
                    f.write("\n")

            # Footer
            f.write("---\n\n")
            f.write("*This architecture overview was automatically generated by C3.x codebase analysis.*\n")
            f.write("*Last updated: skill build time*\n")

        logger.info(f"📐 Created ARCHITECTURE.md")

    def _generate_pattern_references(self, c3_dir: str, patterns_data: Dict):
        """Generate design pattern references (C3.1)."""
        if not patterns_data:
            return

        patterns_dir = os.path.join(c3_dir, 'patterns')
        os.makedirs(patterns_dir, exist_ok=True)

        # Save JSON data
        json_path = os.path.join(patterns_dir, 'detected_patterns.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)

        # Create summary markdown
        md_path = os.path.join(patterns_dir, 'index.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Design Patterns\n\n")
            f.write("*Detected patterns from C3.1 analysis*\n\n")

            for file_data in patterns_data:
                patterns = file_data.get('patterns', [])
                if patterns:
                    f.write(f"## {file_data['file_path']}\n\n")
                    for p in patterns:
                        f.write(f"### {p['pattern_type']}\n\n")
                        if p.get('class_name'):
                            f.write(f"- **Class**: `{p['class_name']}`\n")
                        if p.get('confidence'):
                            f.write(f"- **Confidence**: {p['confidence']:.2f}\n")
                        if p.get('indicators'):
                            f.write(f"- **Indicators**: {', '.join(p['indicators'][:3])}\n")
                        f.write("\n")

        logger.info(f"   ✓ Design patterns: {len(patterns_data)} files")

    def _generate_example_references(self, c3_dir: str, examples_data: Dict):
        """Generate test example references (C3.2)."""
        if not examples_data:
            return

        examples_dir = os.path.join(c3_dir, 'examples')
        os.makedirs(examples_dir, exist_ok=True)

        # Save JSON data
        json_path = os.path.join(examples_dir, 'test_examples.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(examples_data, f, indent=2, ensure_ascii=False)

        # Create summary markdown
        md_path = os.path.join(examples_dir, 'index.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Usage Examples\n\n")
            f.write("*Extracted from test files (C3.2)*\n\n")

            total = examples_data.get('total_examples', 0)
            high_value = examples_data.get('high_value_count', 0)

            f.write(f"**Total Examples**: {total}\n")
            f.write(f"**High-Value Examples**: {high_value}\n\n")

            # List high-value examples
            examples = examples_data.get('examples', [])
            high_value_examples = [e for e in examples if e.get('confidence', 0) > 0.7]

            if high_value_examples:
                f.write("## High-Value Examples\n\n")
                for ex in high_value_examples[:20]:  # Top 20
                    f.write(f"### {ex.get('description', 'Example')}\n\n")
                    f.write(f"- **Category**: {ex.get('category', 'unknown')}\n")
                    f.write(f"- **Confidence**: {ex.get('confidence', 0):.2f}\n")
                    f.write(f"- **File**: `{ex.get('file_path', 'N/A')}`\n")
                    if ex.get('code_snippet'):
                        f.write(f"\n```python\n{ex['code_snippet'][:300]}\n```\n")
                    f.write("\n")

        logger.info(f"   ✓ Test examples: {total} total, {high_value} high-value")

    def _generate_guide_references(self, c3_dir: str, guides_data: Dict):
        """Generate how-to guide references (C3.3)."""
        if not guides_data:
            return

        guides_dir = os.path.join(c3_dir, 'guides')
        os.makedirs(guides_dir, exist_ok=True)

        # Save JSON collection data
        json_path = os.path.join(guides_dir, 'guide_collection.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(guides_data, f, indent=2, ensure_ascii=False)

        guides = guides_data.get('guides', [])

        # Create index
        md_path = os.path.join(guides_dir, 'index.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# How-To Guides\n\n")
            f.write("*Workflow tutorials extracted from codebase (C3.3)*\n\n")

            f.write(f"**Total Guides**: {len(guides)}\n\n")

            if guides:
                f.write("## Available Guides\n\n")
                for guide in guides:
                    f.write(f"- [{guide.get('title', 'Untitled')}](guide_{guide.get('id', 'unknown')}.md)\n")
                f.write("\n")

        # Save individual guide markdown files
        for guide in guides:
            guide_id = guide.get('id', 'unknown')
            guide_path = os.path.join(guides_dir, f"guide_{guide_id}.md")

            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(f"# {guide.get('title', 'Untitled Guide')}\n\n")

                if guide.get('description'):
                    f.write(f"{guide['description']}\n\n")

                steps = guide.get('steps', [])
                if steps:
                    f.write("## Steps\n\n")
                    for i, step in enumerate(steps, 1):
                        f.write(f"### {i}. {step.get('action', 'Step')}\n\n")
                        if step.get('code_example'):
                            lang = step.get('language', 'python')
                            f.write(f"```{lang}\n{step['code_example']}\n```\n\n")
                        if step.get('explanation'):
                            f.write(f"{step['explanation']}\n\n")

        logger.info(f"   ✓ How-to guides: {len(guides)}")

    def _generate_config_references(self, c3_dir: str, config_data: Dict):
        """Generate configuration pattern references (C3.4)."""
        if not config_data:
            return

        config_dir = os.path.join(c3_dir, 'configuration')
        os.makedirs(config_dir, exist_ok=True)

        # Save JSON data
        json_path = os.path.join(config_dir, 'config_patterns.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        # Create summary markdown
        md_path = os.path.join(config_dir, 'index.md')
        config_files = config_data.get('config_files', [])

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Configuration Patterns\n\n")
            f.write("*Detected configuration files (C3.4)*\n\n")

            f.write(f"**Total Config Files**: {len(config_files)}\n\n")

            if config_files:
                f.write("## Configuration Files\n\n")
                for cf in config_files:
                    f.write(f"### `{cf['relative_path']}`\n\n")
                    f.write(f"- **Type**: {cf['type']}\n")
                    f.write(f"- **Purpose**: {cf.get('purpose', 'N/A')}\n")
                    f.write(f"- **Settings**: {len(cf.get('settings', []))}\n")

                    # Show AI enhancements if available
                    if cf.get('ai_enhancement'):
                        enh = cf['ai_enhancement']
                        if enh.get('security_concern'):
                            f.write(f"- **Security**: {enh['security_concern']}\n")
                        if enh.get('best_practice'):
                            f.write(f"- **Best Practice**: {enh['best_practice']}\n")

                    f.write("\n")

                # Overall insights
                if config_data.get('ai_enhancements'):
                    insights = config_data['ai_enhancements'].get('overall_insights', {})
                    if insights:
                        f.write("## Overall Insights\n\n")
                        if insights.get('security_issues_found'):
                            f.write(f"🔐 **Security Issues**: {insights['security_issues_found']}\n\n")
                        if insights.get('recommended_actions'):
                            f.write("**Recommended Actions**:\n")
                            for action in insights['recommended_actions']:
                                f.write(f"- {action}\n")
                            f.write("\n")

        logger.info(f"   ✓ Configuration files: {len(config_files)}")

    def _copy_architecture_details(self, c3_dir: str, arch_data: Dict):
        """Copy architectural pattern JSON details (C3.7)."""
        if not arch_data:
            return

        arch_dir = os.path.join(c3_dir, 'architecture_details')
        os.makedirs(arch_dir, exist_ok=True)

        # Save full JSON data
        json_path = os.path.join(arch_dir, 'architectural_patterns.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(arch_data, f, indent=2, ensure_ascii=False)

        # Create summary markdown
        md_path = os.path.join(arch_dir, 'index.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Architectural Patterns (Detailed)\n\n")
            f.write("*Comprehensive architectural analysis (C3.7)*\n\n")

            patterns = arch_data.get('patterns', [])
            if patterns:
                f.write("## Detected Patterns\n\n")
                for p in patterns:
                    f.write(f"### {p['pattern_name']}\n\n")
                    f.write(f"- **Confidence**: {p['confidence']:.2f}\n")
                    if p.get('framework'):
                        f.write(f"- **Framework**: {p['framework']}\n")
                    if p.get('evidence'):
                        f.write(f"- **Evidence**:\n")
                        for e in p['evidence'][:5]:
                            f.write(f"  - {e}\n")
                    f.write("\n")

        logger.info(f"   ✓ Architectural details: {len(patterns)} patterns")

    def _format_c3_summary_section(self, c3_data: Dict) -> str:
        """Format C3.x analysis summary for SKILL.md."""
        content = "\n## 🏗️ Architecture & Code Analysis\n\n"
        content += "*This skill includes comprehensive codebase analysis*\n\n"

        # Add architectural pattern summary
        if c3_data.get('architecture'):
            patterns = c3_data['architecture'].get('patterns', [])
            if patterns:
                top_pattern = patterns[0]
                content += f"**Primary Architecture**: {top_pattern['pattern_name']}"
                if top_pattern.get('framework'):
                    content += f" ({top_pattern['framework']})"
                content += f" - Confidence: {top_pattern['confidence']:.0%}\n\n"

        # Add design patterns summary
        if c3_data.get('patterns'):
            total_patterns = sum(len(f.get('patterns', [])) for f in c3_data['patterns'])
            if total_patterns > 0:
                content += f"**Design Patterns**: {total_patterns} detected\n"

                # Show top 3 pattern types
                pattern_summary = {}
                for file_data in c3_data['patterns']:
                    for pattern in file_data.get('patterns', []):
                        ptype = pattern['pattern_type']
                        pattern_summary[ptype] = pattern_summary.get(ptype, 0) + 1

                top_patterns = sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True)[:3]
                if top_patterns:
                    content += f"- Top patterns: {', '.join([f'{p[0]} ({p[1]})' for p in top_patterns])}\n"
                content += "\n"

        # Add test examples summary
        if c3_data.get('test_examples'):
            total = c3_data['test_examples'].get('total_examples', 0)
            high_value = c3_data['test_examples'].get('high_value_count', 0)
            if total > 0:
                content += f"**Usage Examples**: {total} extracted from tests ({high_value} high-value)\n\n"

        # Add how-to guides summary
        if c3_data.get('how_to_guides'):
            guide_count = len(c3_data['how_to_guides'].get('guides', []))
            if guide_count > 0:
                content += f"**How-To Guides**: {guide_count} workflow tutorials\n\n"

        # Add configuration summary
        if c3_data.get('config_patterns'):
            config_files = c3_data['config_patterns'].get('config_files', [])
            if config_files:
                content += f"**Configuration Files**: {len(config_files)} analyzed\n"

                # Add security warning if present
                if c3_data['config_patterns'].get('ai_enhancements'):
                    insights = c3_data['config_patterns']['ai_enhancements'].get('overall_insights', {})
                    security_issues = insights.get('security_issues_found', 0)
                    if security_issues > 0:
                        content += f"- 🔐 **Security Alert**: {security_issues} issue(s) detected\n"
                content += "\n"

        # Add link to ARCHITECTURE.md
        content += "📖 **See** `references/codebase_analysis/ARCHITECTURE.md` for complete architectural overview.\n\n"

        return content

    def _generate_conflicts_report(self):
        """Generate detailed conflicts report."""
        conflicts_path = os.path.join(self.skill_dir, 'references', 'conflicts.md')

        with open(conflicts_path, 'w') as f:
            f.write("# Conflict Report\n\n")
            f.write(f"Found **{len(self.conflicts)}** conflicts between sources.\n\n")

            # Group by severity
            high = [c for c in self.conflicts if (hasattr(c, 'severity') and c.severity == 'high') or c.get('severity') == 'high']
            medium = [c for c in self.conflicts if (hasattr(c, 'severity') and c.severity == 'medium') or c.get('severity') == 'medium']
            low = [c for c in self.conflicts if (hasattr(c, 'severity') and c.severity == 'low') or c.get('severity') == 'low']

            f.write("## Severity Breakdown\n\n")
            f.write(f"- 🔴 **High**: {len(high)} (action required)\n")
            f.write(f"- 🟡 **Medium**: {len(medium)} (review recommended)\n")
            f.write(f"- 🟢 **Low**: {len(low)} (informational)\n\n")

            # List high severity conflicts
            if high:
                f.write("## 🔴 High Severity\n\n")
                f.write("*These conflicts require immediate attention*\n\n")

                for conflict in high:
                    api_name = conflict.api_name if hasattr(conflict, 'api_name') else conflict.get('api_name', 'Unknown')
                    diff = conflict.difference if hasattr(conflict, 'difference') else conflict.get('difference', 'N/A')

                    f.write(f"### {api_name}\n\n")
                    f.write(f"**Issue**: {diff}\n\n")

            # List medium severity
            if medium:
                f.write("## 🟡 Medium Severity\n\n")

                for conflict in medium[:20]:  # Limit to 20
                    api_name = conflict.api_name if hasattr(conflict, 'api_name') else conflict.get('api_name', 'Unknown')
                    diff = conflict.difference if hasattr(conflict, 'difference') else conflict.get('difference', 'N/A')

                    f.write(f"### {api_name}\n\n")
                    f.write(f"{diff}\n\n")

        logger.info(f"Created conflicts report")


if __name__ == '__main__':
    # Test with mock data
    import sys

    if len(sys.argv) < 2:
        print("Usage: python unified_skill_builder.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Mock scraped data
    scraped_data = {
        'github': {
            'data': {
                'readme': '# Test Repository',
                'issues': [],
                'releases': []
            }
        }
    }

    builder = UnifiedSkillBuilder(config, scraped_data)
    builder.build()

    print(f"\n✅ Test skill built in: output/{config['name']}/")
