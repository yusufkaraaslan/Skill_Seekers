#!/usr/bin/env python3
"""
Markdown Cleaner Utility

Removes HTML tags and bloat from markdown content while preserving structure.
Used to clean README files and other documentation for skill generation.
"""

import re


class MarkdownCleaner:
    """Clean HTML from markdown while preserving structure"""

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Remove HTML tags while preserving text content.

        Args:
            text: Markdown text possibly containing HTML

        Returns:
            Cleaned markdown with HTML tags removed
        """
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        # Remove HTML tags but keep content
        text = re.sub(r'<[^>]+>', '', text)

        # Remove empty lines created by HTML removal
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        return text.strip()

    @staticmethod
    def extract_first_section(text: str, max_chars: int = 500) -> str:
        """
        Extract first meaningful content, respecting markdown structure.

        Captures content including section headings up to max_chars.
        For short READMEs, includes everything. For longer ones, extracts
        intro + first few sections (e.g., installation, quick start).

        Args:
            text: Full markdown text
            max_chars: Maximum characters to extract

        Returns:
            First section content (cleaned, including headings)
        """
        # Remove HTML first
        text = MarkdownCleaner.remove_html_tags(text)

        # If text is short, return it all
        if len(text) <= max_chars:
            return text.strip()

        # For longer text, extract smartly
        lines = text.split('\n')
        content_lines = []
        char_count = 0
        section_count = 0
        in_code_block = False  # Track code fence state to avoid truncating mid-block

        for line in lines:
            # Check for code fence (```)
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

            # Check for any heading (H1-H6)
            is_heading = re.match(r'^#{1,6}\s+', line)

            if is_heading:
                section_count += 1
                # Include first 4 sections (title + 3 sections like Installation, Quick Start, Features)
                if section_count <= 4:
                    content_lines.append(line)
                    char_count += len(line)
                else:
                    # Stop after 4 sections (but not if in code block)
                    if not in_code_block:
                        break
            else:
                # Include content
                content_lines.append(line)
                char_count += len(line)

            # Stop if we have enough content (but not if in code block)
            if char_count >= max_chars and not in_code_block:
                break

        result = '\n'.join(content_lines).strip()

        # If we truncated, ensure we don't break markdown (only if not in code block)
        if char_count >= max_chars and not in_code_block:
            # Find last complete sentence
            result = MarkdownCleaner._truncate_at_sentence(result, max_chars)

        return result

    @staticmethod
    def _truncate_at_sentence(text: str, max_chars: int) -> str:
        """
        Truncate at last complete sentence before max_chars.

        Args:
            text: Text to truncate
            max_chars: Maximum character count

        Returns:
            Truncated text ending at sentence boundary
        """
        if len(text) <= max_chars:
            return text

        # Find last sentence boundary before max_chars
        truncated = text[:max_chars]

        # Look for last period, exclamation, or question mark
        last_sentence = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? ')
        )

        if last_sentence > max_chars // 2:  # At least half the content
            return truncated[:last_sentence + 1]

        # Fall back to word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."

        return truncated + "..."
