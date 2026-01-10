#!/usr/bin/env python3
"""
API Reference Builder

Generates markdown API documentation from code analysis results.
Supports Python, JavaScript/TypeScript, and C++.

Output Format:
- One .md file per analyzed source file
- Organized by: Classes → Methods, then standalone Functions
- Includes: Signatures, parameters, return types, docstrings

Usage:
    from skill_seekers.cli.api_reference_builder import APIReferenceBuilder

    builder = APIReferenceBuilder(code_analysis_results)
    builder.build_reference(output_dir)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class APIReferenceBuilder:
    """
    Builds markdown API reference from code analysis results.

    Processes code analysis data and generates well-formatted markdown
    documentation for each analyzed source file.
    """

    def __init__(self, code_analysis: Dict[str, Any]):
        """
        Initialize builder with code analysis results.

        Args:
            code_analysis: Dictionary containing analyzed files and their code structures.
                          Expected format: {'files': [{'file': 'path', 'classes': [...], 'functions': [...]}]}
        """
        self.code_analysis = code_analysis
        self.files_data = code_analysis.get('files', [])

    def build_reference(self, output_dir: Path) -> Dict[str, Path]:
        """
        Generate markdown files for each analyzed source file.

        Args:
            output_dir: Directory to save generated markdown files

        Returns:
            Dictionary mapping source file paths to generated markdown file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        for file_data in self.files_data:
            source_file = file_data.get('file', 'unknown')
            language = file_data.get('language', 'Unknown')

            # Skip files with no analysis
            if not file_data.get('classes') and not file_data.get('functions'):
                continue

            # Generate markdown content
            markdown_content = self._generate_file_reference(file_data, source_file, language)

            # Determine output filename
            output_filename = self._get_output_filename(source_file)
            output_path = output_dir / output_filename

            # Write markdown file
            output_path.write_text(markdown_content, encoding='utf-8')
            generated_files[source_file] = output_path

        return generated_files

    def _get_output_filename(self, source_file: str) -> str:
        """
        Generate output filename from source file path.

        Args:
            source_file: Path to source file

        Returns:
            Safe filename for markdown output
        """
        # Get base filename
        basename = Path(source_file).name

        # Replace extension with .md
        name_without_ext = basename.rsplit('.', 1)[0] if '.' in basename else basename
        return f"{name_without_ext}.md"

    def _generate_file_reference(self, file_data: Dict[str, Any],
                                 source_file: str, language: str) -> str:
        """
        Generate complete markdown reference for a single file.

        Args:
            file_data: Analysis data for the file
            source_file: Path to source file
            language: Programming language

        Returns:
            Complete markdown content
        """
        lines = []

        # Header
        filename = Path(source_file).name
        lines.append(f"# API Reference: {filename}\n")
        lines.append(f"**Language**: {language}\n")
        lines.append(f"**Source**: `{source_file}`\n")
        lines.append("---\n")

        # Classes section
        classes = file_data.get('classes', [])
        if classes:
            lines.append("## Classes\n")
            for cls in classes:
                lines.append(self._format_class(cls))
                lines.append("\n")

        # Functions section
        functions = file_data.get('functions', [])
        if functions:
            lines.append("## Functions\n")
            for func in functions:
                lines.append(self._format_function(func))
                lines.append("\n")

        return '\n'.join(lines)

    def _format_class(self, class_sig: Dict[str, Any]) -> str:
        """
        Format class signature as markdown.

        Args:
            class_sig: Class signature dictionary

        Returns:
            Formatted markdown for class
        """
        lines = []

        # Class name
        class_name = class_sig.get('name', 'Unknown')
        lines.append(f"### {class_name}\n")

        # Docstring
        docstring = class_sig.get('docstring')
        if docstring:
            lines.append(f"{docstring}\n")

        # Inheritance
        base_classes = class_sig.get('base_classes', [])
        if base_classes:
            bases_str = ', '.join(base_classes)
            lines.append(f"**Inherits from**: {bases_str}\n")
        else:
            lines.append("**Inherits from**: (none)\n")

        # Methods
        methods = class_sig.get('methods', [])
        if methods:
            lines.append("#### Methods\n")
            for method in methods:
                lines.append(self._format_method(method))
                lines.append("")

        return '\n'.join(lines)

    def _format_method(self, method_sig: Dict[str, Any]) -> str:
        """
        Format method signature as markdown.

        Args:
            method_sig: Method signature dictionary

        Returns:
            Formatted markdown for method
        """
        lines = []

        # Method signature
        signature = self._build_signature(method_sig)
        lines.append(f"##### {signature}\n")

        # Docstring
        docstring = method_sig.get('docstring')
        if docstring:
            lines.append(f"{docstring}\n")

        # Decorators
        decorators = method_sig.get('decorators', [])
        if decorators:
            dec_str = ', '.join(f"`@{d}`" for d in decorators)
            lines.append(f"**Decorators**: {dec_str}\n")

        # Parameters table
        params = method_sig.get('parameters', [])
        if params:
            lines.append(self._format_parameters(params))
            lines.append("")

        # Return type
        return_type = method_sig.get('return_type')
        if return_type:
            lines.append(f"**Returns**: `{return_type}`\n")

        return '\n'.join(lines)

    def _format_function(self, func_sig: Dict[str, Any]) -> str:
        """
        Format function signature as markdown.

        Args:
            func_sig: Function signature dictionary

        Returns:
            Formatted markdown for function
        """
        lines = []

        # Function signature
        signature = self._build_signature(func_sig)
        lines.append(f"### {signature}\n")

        # Async indicator
        if func_sig.get('is_async'):
            lines.append("**Async function**\n")

        # Docstring
        docstring = func_sig.get('docstring')
        if docstring:
            lines.append(f"{docstring}\n")

        # Parameters table
        params = func_sig.get('parameters', [])
        if params:
            lines.append(self._format_parameters(params))
            lines.append("")

        # Return type
        return_type = func_sig.get('return_type')
        if return_type:
            lines.append(f"**Returns**: `{return_type}`\n")
        else:
            lines.append("**Returns**: (none)\n")

        return '\n'.join(lines)

    def _build_signature(self, sig: Dict[str, Any]) -> str:
        """
        Build function/method signature string.

        Args:
            sig: Signature dictionary

        Returns:
            Formatted signature string
        """
        name = sig.get('name', 'unknown')
        params = sig.get('parameters', [])
        return_type = sig.get('return_type')

        # Build parameter list
        param_strs = []
        for param in params:
            param_str = param.get('name', '')

            # Add type hint if available
            type_hint = param.get('type_hint')
            if type_hint:
                param_str += f": {type_hint}"

            # Add default value if available
            default = param.get('default')
            if default:
                param_str += f" = {default}"

            param_strs.append(param_str)

        params_str = ', '.join(param_strs)

        # Build full signature
        if return_type:
            return f"{name}({params_str}) → {return_type}"
        else:
            return f"{name}({params_str})"

    def _format_parameters(self, params: List[Dict]) -> str:
        """
        Format parameter list as markdown table.

        Args:
            params: List of parameter dictionaries

        Returns:
            Formatted markdown table
        """
        if not params:
            return ""

        lines = []
        lines.append("**Parameters**:")
        lines.append("")
        lines.append("| Name | Type | Default | Description |")
        lines.append("|------|------|---------|-------------|")

        for param in params:
            name = param.get('name', '-')
            type_hint = param.get('type_hint', '-')
            default = param.get('default')

            # Show "-" for parameters without defaults
            default_str = default if default is not None else '-'

            # For description, use empty for now (would need JSDoc/docstring parsing)
            description = "-"

            lines.append(f"| {name} | {type_hint} | {default_str} | {description} |")

        return '\n'.join(lines)


def main():
    """
    Command-line interface for API reference generation.

    Reads code analysis JSON and generates markdown API documentation.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate API reference from code analysis results'
    )

    parser.add_argument('input_file', help='Code analysis JSON file')
    parser.add_argument('output_dir', help='Output directory for markdown files')

    args = parser.parse_args()

    # Read code analysis
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    with open(input_path, 'r', encoding='utf-8') as f:
        code_analysis = json.load(f)

    # Build API reference
    builder = APIReferenceBuilder(code_analysis)
    generated_files = builder.build_reference(Path(args.output_dir))

    # Report results
    print(f"✅ Generated {len(generated_files)} API reference files")
    print(f"📁 Output directory: {args.output_dir}")
    for source, output in generated_files.items():
        print(f"  • {output.name} (from {Path(source).name})")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
