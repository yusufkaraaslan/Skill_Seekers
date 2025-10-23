#!/usr/bin/env python3
"""
PDF Documentation to Claude Skill Converter (Task B1.6)

Converts PDF documentation into Claude AI skills.
Uses pdf_extractor_poc.py for extraction, builds skill structure.

Usage:
    python3 pdf_scraper.py --config configs/manual_pdf.json
    python3 pdf_scraper.py --pdf manual.pdf --name myskill
    python3 pdf_scraper.py --from-json manual_extracted.json
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Import the PDF extractor
from pdf_extractor_poc import PDFExtractor


class PDFToSkillConverter:
    """Convert PDF documentation to Claude skill"""

    def __init__(self, config):
        self.config = config
        self.name = config['name']
        self.pdf_path = config.get('pdf_path', '')
        self.description = config.get('description', f'Documentation skill for {self.name}')

        # Paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Extraction options
        self.extract_options = config.get('extract_options', {})

        # Categories
        self.categories = config.get('categories', {})

        # Extracted data
        self.extracted_data = None

    def extract_pdf(self):
        """Extract content from PDF using pdf_extractor_poc.py"""
        print(f"\n🔍 Extracting from PDF: {self.pdf_path}")

        # Create extractor with options
        extractor = PDFExtractor(
            self.pdf_path,
            verbose=True,
            chunk_size=self.extract_options.get('chunk_size', 10),
            min_quality=self.extract_options.get('min_quality', 5.0),
            extract_images=self.extract_options.get('extract_images', True),
            image_dir=f"{self.skill_dir}/assets/images",
            min_image_size=self.extract_options.get('min_image_size', 100)
        )

        # Extract
        result = extractor.extract_all()

        if not result:
            print("❌ Extraction failed")
            return False

        # Save extracted data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result
        return True

    def load_extracted_data(self, json_path):
        """Load previously extracted data from JSON"""
        print(f"\n📂 Loading extracted data from: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            self.extracted_data = json.load(f)

        print(f"✅ Loaded {self.extracted_data['total_pages']} pages")
        return True

    def categorize_content(self):
        """Categorize pages based on chapters or keywords"""
        print(f"\n📋 Categorizing content...")

        categorized = {}

        # Use chapters if available
        if self.extracted_data.get('chapters'):
            for chapter in self.extracted_data['chapters']:
                category_key = self._sanitize_filename(chapter['title'])
                categorized[category_key] = {
                    'title': chapter['title'],
                    'pages': []
                }

            # Assign pages to chapters
            for page in self.extracted_data['pages']:
                page_num = page['page_number']

                # Find which chapter this page belongs to
                for chapter in self.extracted_data['chapters']:
                    if chapter['start_page'] <= page_num <= chapter['end_page']:
                        category_key = self._sanitize_filename(chapter['title'])
                        categorized[category_key]['pages'].append(page)
                        break

        # Fall back to keyword-based categorization
        elif self.categories:
            # Initialize categories
            for cat_key, keywords in self.categories.items():
                categorized[cat_key] = {
                    'title': cat_key.replace('_', ' ').title(),
                    'pages': []
                }

            # Categorize by keywords
            for page in self.extracted_data['pages']:
                text = page['text'].lower()
                headings_text = ' '.join([h['text'] for h in page['headings']]).lower()

                # Score against each category
                scores = {}
                for cat_key, keywords in self.categories.items():
                    score = sum(1 for kw in keywords if kw.lower() in text or kw.lower() in headings_text)
                    if score > 0:
                        scores[cat_key] = score

                # Assign to highest scoring category
                if scores:
                    best_cat = max(scores, key=scores.get)
                    categorized[best_cat]['pages'].append(page)
                else:
                    # Default category
                    if 'other' not in categorized:
                        categorized['other'] = {'title': 'Other', 'pages': []}
                    categorized['other']['pages'].append(page)

        else:
            # No categorization - use single category
            categorized['content'] = {
                'title': 'Content',
                'pages': self.extracted_data['pages']
            }

        print(f"✅ Created {len(categorized)} categories")
        for cat_key, cat_data in categorized.items():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} pages")

        return categorized

    def build_skill(self):
        """Build complete skill structure"""
        print(f"\n🏗️  Building skill: {self.name}")

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorize content
        categorized = self.categorize_content()

        # Generate reference files
        print(f"\n📝 Generating reference files...")
        for cat_key, cat_data in categorized.items():
            self._generate_reference_file(cat_key, cat_data)

        # Generate index
        self._generate_index(categorized)

        # Generate SKILL.md
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: python3 cli/package_skill.py {self.skill_dir}/")

    def _generate_reference_file(self, cat_key, cat_data):
        """Generate a reference markdown file for a category"""
        filename = f"{self.skill_dir}/references/{cat_key}.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {cat_data['title']}\n\n")

            for page in cat_data['pages']:
                # Add headings as section markers
                if page['headings']:
                    f.write(f"## {page['headings'][0]['text']}\n\n")

                # Add text content
                if page['text']:
                    # Limit to first 1000 chars per page to avoid huge files
                    text = page['text'][:1000]
                    f.write(f"{text}\n\n")

                # Add code samples
                if page['code_samples']:
                    f.write("### Code Examples\n\n")
                    for code in page['code_samples'][:3]:  # Limit to top 3
                        lang = code['language']
                        f.write(f"```{lang}\n{code['code']}\n```\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized):
        """Generate reference index"""
        filename = f"{self.skill_dir}/references/index.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {self.name.title()} Documentation Reference\n\n")
            f.write("## Categories\n\n")

            for cat_key, cat_data in categorized.items():
                page_count = len(cat_data['pages'])
                f.write(f"- [{cat_data['title']}]({cat_key}.md) ({page_count} pages)\n")

            f.write("\n## Statistics\n\n")
            stats = self.extracted_data.get('quality_statistics', {})
            f.write(f"- Total pages: {self.extracted_data['total_pages']}\n")
            f.write(f"- Code blocks: {self.extracted_data['total_code_blocks']}\n")
            f.write(f"- Images: {self.extracted_data['total_images']}\n")
            if stats:
                f.write(f"- Average code quality: {stats.get('average_quality', 0):.1f}/10\n")
                f.write(f"- Valid code blocks: {stats.get('valid_code_blocks', 0)}\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized):
        """Generate main SKILL.md file"""
        filename = f"{self.skill_dir}/SKILL.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {self.name.title()} Documentation Skill\n\n")
            f.write(f"{self.description}\n\n")

            f.write("## When to use this skill\n\n")
            f.write(f"Use this skill when the user asks about {self.name} documentation, ")
            f.write("including API references, tutorials, examples, and best practices.\n\n")

            f.write("## What's included\n\n")
            f.write("This skill contains:\n\n")
            for cat_key, cat_data in categorized.items():
                f.write(f"- **{cat_data['title']}**: {len(cat_data['pages'])} pages\n")

            f.write("\n## Quick Reference\n\n")

            # Get high-quality code samples
            all_code = []
            for page in self.extracted_data['pages']:
                all_code.extend(page.get('code_samples', []))

            # Sort by quality and get top 5
            all_code.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            top_code = all_code[:5]

            if top_code:
                f.write("### Top Code Examples\n\n")
                for i, code in enumerate(top_code, 1):
                    lang = code['language']
                    quality = code.get('quality_score', 0)
                    f.write(f"**Example {i}** (Quality: {quality:.1f}/10):\n\n")
                    f.write(f"```{lang}\n{code['code'][:300]}...\n```\n\n")

            f.write("## Navigation\n\n")
            f.write("See `references/index.md` for complete documentation structure.\n\n")

            # Add language statistics
            langs = self.extracted_data.get('languages_detected', {})
            if langs:
                f.write("## Languages Covered\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")

        print(f"   Generated: {filename}")

    def _sanitize_filename(self, name):
        """Convert string to safe filename"""
        # Remove special chars, replace spaces with underscores
        safe = re.sub(r'[^\w\s-]', '', name.lower())
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe


def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF documentation to Claude skill',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--config', help='PDF config JSON file')
    parser.add_argument('--pdf', help='Direct PDF file path')
    parser.add_argument('--name', help='Skill name (with --pdf)')
    parser.add_argument('--from-json', help='Build skill from extracted JSON')
    parser.add_argument('--description', help='Skill description')

    args = parser.parse_args()

    # Validate inputs
    if not (args.config or args.pdf or args.from_json):
        parser.error("Must specify --config, --pdf, or --from-json")

    # Load or create config
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    elif args.from_json:
        # Build from extracted JSON
        name = Path(args.from_json).stem.replace('_extracted', '')
        config = {
            'name': name,
            'description': args.description or f'Documentation skill for {name}'
        }
        converter = PDFToSkillConverter(config)
        converter.load_extracted_data(args.from_json)
        converter.build_skill()
        return
    else:
        # Direct PDF mode
        if not args.name:
            parser.error("Must specify --name with --pdf")
        config = {
            'name': args.name,
            'pdf_path': args.pdf,
            'description': args.description or f'Documentation skill for {args.name}',
            'extract_options': {
                'chunk_size': 10,
                'min_quality': 5.0,
                'extract_images': True,
                'min_image_size': 100
            }
        }

    # Create converter
    converter = PDFToSkillConverter(config)

    # Extract if needed
    if config.get('pdf_path'):
        if not converter.extract_pdf():
            sys.exit(1)

    # Build skill
    converter.build_skill()


if __name__ == '__main__':
    main()
