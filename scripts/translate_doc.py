#!/usr/bin/env python3
"""
Translate Skill Seekers documentation to Chinese.

Usage:
    python scripts/translate_doc.py <file> --target-lang zh-CN
    python scripts/translate_doc.py docs/getting-started/02-quick-start.md
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime


def get_version() -> str:
    """Get current version from package."""
    try:
        from skill_seekers import __version__
        return __version__
    except ImportError:
        return "3.1.0"


def translate_with_anthropic(content: str, api_key: str) -> str:
    """Translate content using Anthropic Claude API."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        system_prompt = """You are a professional technical translator translating Skill Seekers documentation from English to Simplified Chinese.

Translation rules:
1. Keep technical terms in English: CLI, API, JSON, YAML, MCP, URL, HTTP, etc.
2. Keep code examples, commands, and file paths in English
3. Keep proper nouns (product names, company names) in English
4. Use Simplified Chinese (简体中文)
5. Maintain all Markdown formatting
6. Translate link text but keep link targets (will be handled separately)
7. Use professional, technical Chinese appropriate for developers
8. Preserve all code blocks, they should remain exactly the same

Output ONLY the translated content, no explanations."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate this technical documentation to Simplified Chinese:\n\n{content}"
                }
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        print(f"Translation API error: {e}")
        return None


def add_translation_header(content: str, original_file: Path, target_lang: str) -> str:
    """Add translation header to document."""
    version = get_version()
    date = datetime.now().strftime("%Y-%m-%d")
    original_name = original_file.name
    
    # Calculate relative path from docs/
    try:
        relative_path = original_file.relative_to("docs")
        original_link = f"../{relative_path}"
    except ValueError:
        original_link = f"../{original_file.name}"
    
    header = f"""> **注意：** 本文档是 [{original_name}]({original_link}) 的中文翻译。
> 
> - **最后翻译日期：** {date}
> - **英文原文版本：** {version}
> - **翻译状态：** ⚠️ 待审阅
>
> 如果本文档与英文版本有冲突，请以英文版本为准。
> 
> ---
> 
> **Note:** This document is a Chinese translation of [{original_name}]({original_link}).
> 
> - **Last translated:** {date}
> - **Original version:** {version}
> - **Translation status:** ⚠️ Pending review
>
> If there are conflicts, the English version takes precedence.

---

"""
    
    return header + content


def fix_links(content: str, original_file: Path) -> str:
    """Fix internal links to point to Chinese versions."""
    # Pattern for markdown links: [text](path)
    # We need to convert links to other docs to point to zh-CN versions
    
    def replace_link(match):
        text = match.group(1)
        path = match.group(2)
        
        # Skip external links
        if path.startswith(('http://', 'https://', '#', 'mailto:')):
            return match.group(0)
        
        # Skip anchor-only links
        if path.startswith('#'):
            return match.group(0)
        
        # For relative links to other md files, adjust path
        if path.endswith('.md'):
            # If it's a relative link, it should point to zh-CN version
            if not path.startswith('/'):
                # Count directory levels
                depth = len(original_file.parent.parts) - 1  # -1 for 'docs'
                if depth > 0:
                    # Going up to docs/, then into zh-CN/
                    prefix = '../' * depth
                    new_path = prefix + 'zh-CN/' + path.lstrip('./')
                else:
                    new_path = 'zh-CN/' + path
                return f'[{text}]({new_path})'
        
        return match.group(0)
    
    # Replace markdown links
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, content)
    
    return content


def translate_file(input_path: str, target_lang: str = "zh-CN"):
    """Translate a documentation file."""
    input_file = Path(input_path).resolve()
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return False
    
    # Read English content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove existing translation header if present (for re-translation)
    if '> **注意：**' in content[:500]:
        # Find the separator and remove everything before it
        separator_pos = content.find('---\n\n')
        if separator_pos != -1:
            content = content[separator_pos + 5:]
    
    # Translate content
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        print(f"🤖 Translating with Claude API: {input_file.name}")
        translated = translate_with_anthropic(content, api_key)
        if translated:
            content = translated
        else:
            print(f"⚠️  Translation failed, keeping original content for: {input_file.name}")
    else:
        print(f"⚠️  No ANTHROPIC_API_KEY, skipping translation for: {input_file.name}")
        return False
    
    # Fix internal links
    content = fix_links(content, input_file)
    
    # Add translation header
    content = add_translation_header(content, input_file, target_lang)
    
    # Determine output path
    try:
        relative_path = input_file.relative_to(Path("docs").resolve())
    except ValueError:
        # If file is not in docs/, use just the filename
        relative_path = Path(input_file.name)
    
    output_file = Path("docs") / target_lang / relative_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write translated content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Translate Skill Seekers documentation to Chinese"
    )
    parser.add_argument(
        "file",
        nargs='?',
        help="Path to the documentation file to translate (not needed with --batch)"
    )
    parser.add_argument(
        "--target-lang",
        default="zh-CN",
        help="Target language code (default: zh-CN)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Translate all documentation files"
    )
    
    args = parser.parse_args()
    
    if args.batch:
        # Translate all docs
        docs_dir = Path("docs")
        files_to_translate = []
        
        for pattern in ["**/*.md"]:
            files = list(docs_dir.glob(pattern))
            for f in files:
                # Skip already translated files and archive
                if "zh-CN" not in str(f) and "archive" not in str(f):
                    files_to_translate.append(f)
        
        print(f"🔄 Batch translating {len(files_to_translate)} files...")
        success_count = 0
        for f in files_to_translate:
            if translate_file(str(f), args.target_lang):
                success_count += 1
        
        print(f"\n✅ Successfully translated {success_count}/{len(files_to_translate)} files")
    else:
        # Translate single file
        translate_file(args.file, args.target_lang)


if __name__ == "__main__":
    main()
