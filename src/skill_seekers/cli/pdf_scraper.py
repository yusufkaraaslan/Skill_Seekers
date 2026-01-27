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

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Import the PDF extractor
from .pdf_extractor_poc import PDFExtractor


def infer_description_from_pdf(pdf_metadata: dict = None, name: str = "") -> str:
    """
    Infer skill description from PDF metadata or document properties.

    Tries to extract meaningful description from:
    1. PDF metadata fields (title, subject, keywords)
    2. Falls back to improved template

    Args:
        pdf_metadata: PDF metadata dictionary with title, subject, etc.
        name: Skill name for fallback

    Returns:
        Description string suitable for "Use when..." format
    """
    if pdf_metadata:
        # Try to use subject field (often contains description)
        if "subject" in pdf_metadata and pdf_metadata["subject"]:
            desc = str(pdf_metadata["subject"]).strip()
            if len(desc) > 20:
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                return f"Use when {desc.lower()}"

        # Try title field if meaningful
        if "title" in pdf_metadata and pdf_metadata["title"]:
            title = str(pdf_metadata["title"]).strip()
            # Skip if it's just the filename
            if len(title) > 10 and not title.endswith(".pdf"):
                return f"Use when working with {title.lower()}"

    # Improved fallback
    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this documentation"
    )


class PDFToSkillConverter:
    """Convert PDF documentation to Claude skill"""

    def __init__(self, config):
        self.config = config
        self.name = config["name"]
        self.pdf_path = config.get("pdf_path", "")
        # Set initial description (will be improved after extraction if metadata available)
        self.description = config.get(
            "description", f"Use when referencing {self.name} documentation"
        )

        # Paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Extraction options
        self.extract_options = config.get("extract_options", {})

        # Categories
        self.categories = config.get("categories", {})

        # Extracted data
        self.extracted_data = None

    def extract_pdf(self):
        """Extract content from PDF using pdf_extractor_poc.py"""
        print(f"\n🔍 Extracting from PDF: {self.pdf_path}")

        # Create extractor with options
        extractor = PDFExtractor(
            self.pdf_path,
            verbose=True,
            chunk_size=self.extract_options.get("chunk_size", 10),
            min_quality=self.extract_options.get("min_quality", 5.0),
            extract_images=self.extract_options.get("extract_images", True),
            image_dir=f"{self.skill_dir}/assets/images",
            min_image_size=self.extract_options.get("min_image_size", 100),
        )

        # Extract
        result = extractor.extract_all()

        if not result:
            print("❌ Extraction failed")
            raise RuntimeError(f"Failed to extract PDF: {self.pdf_path}")

        # Save extracted data
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result
        return True

    def load_extracted_data(self, json_path):
        """Load previously extracted data from JSON"""
        print(f"\n📂 Loading extracted data from: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)

        print(f"✅ Loaded {self.extracted_data['total_pages']} pages")
        return True

    def categorize_content(self):
        """Categorize pages based on chapters or keywords"""
        print("\n📋 Categorizing content...")

        categorized = {}

        # For single PDF source, use single category with all pages
        # This avoids bad chapter detection splitting content incorrectly
        if self.pdf_path:
            # Get PDF basename for title
            pdf_basename = Path(self.pdf_path).stem
            category_key = self._sanitize_filename(pdf_basename)

            categorized[category_key] = {
                "title": pdf_basename,
                "pages": self.extracted_data.get("pages", []),
            }

            print("✅ Created 1 category (single PDF source)")
            print(f"   - {pdf_basename}: {len(categorized[category_key]['pages'])} pages")
            return categorized

        # Use chapters if available (for multi-source scenarios)
        if self.extracted_data.get("chapters"):
            for chapter in self.extracted_data["chapters"]:
                category_key = self._sanitize_filename(chapter["title"])
                categorized[category_key] = {"title": chapter["title"], "pages": []}

            # Assign pages to chapters
            uncategorized_pages = []
            for page in self.extracted_data["pages"]:
                page_num = page["page_number"]
                assigned = False

                # Find which chapter this page belongs to
                for chapter in self.extracted_data["chapters"]:
                    if chapter["start_page"] <= page_num <= chapter["end_page"]:
                        category_key = self._sanitize_filename(chapter["title"])
                        categorized[category_key]["pages"].append(page)
                        assigned = True
                        break

                # Track pages not assigned to any chapter
                if not assigned:
                    uncategorized_pages.append(page)

            # Add uncategorized pages to a default category
            if uncategorized_pages:
                categorized["uncategorized"] = {
                    "title": "Additional Content",
                    "pages": uncategorized_pages,
                }

        # Fall back to keyword-based categorization
        elif self.categories:
            # Check if categories is already in the right format (for tests)
            # If first value is a list of dicts (pages), use as-is
            first_value = next(iter(self.categories.values()))
            if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
                # Already categorized - convert to expected format
                for cat_key, pages in self.categories.items():
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": pages,
                    }
            else:
                # Keyword-based categorization
                # Initialize categories
                for cat_key, _ in self.categories.items():
                    categorized[cat_key] = {"title": cat_key.replace("_", " ").title(), "pages": []}

                # Categorize by keywords
                for page in self.extracted_data["pages"]:
                    text = page.get("text", "").lower()
                    headings_text = " ".join([h["text"] for h in page.get("headings", [])]).lower()

                    # Score against each category
                    scores = {}
                    for cat_key, keywords in self.categories.items():
                        # Handle both string keywords and dict keywords (shouldn't happen, but be safe)
                        if isinstance(keywords, list):
                            score = sum(
                                1
                                for kw in keywords
                                if isinstance(kw, str)
                                and (kw.lower() in text or kw.lower() in headings_text)
                            )
                        else:
                            score = 0
                        if score > 0:
                            scores[cat_key] = score

                    # Assign to highest scoring category
                    if scores:
                        best_cat = max(scores, key=scores.get)
                        categorized[best_cat]["pages"].append(page)
                    else:
                        # Default category
                        if "other" not in categorized:
                            categorized["other"] = {"title": "Other", "pages": []}
                        categorized["other"]["pages"].append(page)

        else:
            # No categorization - use single category
            categorized["content"] = {"title": "Content", "pages": self.extracted_data["pages"]}

        print(f"✅ Created {len(categorized)} categories")
        for _cat_key, cat_data in categorized.items():
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
        print("\n📝 Generating reference files...")
        total_sections = len(categorized)
        section_num = 1
        for cat_key, cat_data in categorized.items():
            self._generate_reference_file(cat_key, cat_data, section_num, total_sections)
            section_num += 1

        # Generate index
        self._generate_index(categorized)

        # Generate SKILL.md
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    def _generate_reference_file(self, _cat_key, cat_data, section_num, total_sections):
        """Generate a reference markdown file for a category"""
        # Calculate page range for filename - use PDF basename
        pages = cat_data["pages"]
        if pages:
            page_nums = [p["page_number"] for p in pages]
            page_range = f"p{min(page_nums)}-p{max(page_nums)}"

            # Get PDF basename for cleaner filename
            pdf_basename = ""
            if self.pdf_path:
                pdf_basename = Path(self.pdf_path).stem

            # If only one section or section covers most pages, use simple name
            if total_sections == 1:
                filename = (
                    f"{self.skill_dir}/references/{pdf_basename}.md"
                    if pdf_basename
                    else f"{self.skill_dir}/references/main.md"
                )
            else:
                # Multiple sections: use PDF basename + page range
                base_name = pdf_basename if pdf_basename else "section"
                filename = f"{self.skill_dir}/references/{base_name}_{page_range}.md"
        else:
            filename = f"{self.skill_dir}/references/section_{section_num:02d}.md"

        with open(filename, "w", encoding="utf-8") as f:
            # Include original title in file content for reference
            f.write(f"# {cat_data['title']}\n\n")
            if pages:
                f.write(f"**Pages**: {min(page_nums)}-{max(page_nums)}\n\n")

            for page in cat_data["pages"]:
                # Add page source marker for traceability
                f.write(f"---\n\n**📄 Source: PDF Page {page['page_number']}**\n\n")

                # Add headings as section markers
                if page.get("headings"):
                    f.write(f"## {page['headings'][0]['text']}\n\n")

                # Add text content
                if page.get("text"):
                    # Include full page content (removed 1000 char limit)
                    text = page["text"]
                    f.write(f"{text}\n\n")

                # Add code samples (check both 'code_samples' and 'code_blocks' for compatibility)
                code_list = page.get("code_samples") or page.get("code_blocks")
                if code_list:
                    f.write("### Code Examples\n\n")
                    for code in code_list[:3]:  # Limit to top 3
                        lang = code.get("language", "")
                        f.write(f"```{lang}\n{code['code']}\n```\n\n")

                # Add images
                if page.get("images"):
                    # Create assets directory if needed
                    assets_dir = os.path.join(self.skill_dir, "assets")
                    os.makedirs(assets_dir, exist_ok=True)

                    f.write("### Images\n\n")
                    for img in page["images"]:
                        # Save image to assets
                        img_filename = f"page_{page['page_number']}_img_{img['index']}.png"
                        img_path = os.path.join(assets_dir, img_filename)

                        with open(img_path, "wb") as img_file:
                            img_file.write(img["data"])

                        # Add markdown image reference
                        f.write(f"![Image {img['index']}](../assets/{img_filename})\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized):
        """Generate reference index"""
        filename = f"{self.skill_dir}/references/index.md"

        # Get PDF basename
        pdf_basename = ""
        if self.pdf_path:
            pdf_basename = Path(self.pdf_path).stem

        total_sections = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Documentation Reference\n\n")
            f.write("## Categories\n\n")

            section_num = 1
            for _cat_key, cat_data in categorized.items():
                pages = cat_data["pages"]
                page_count = len(pages)

                # Calculate page range for link - use PDF basename
                if pages:
                    page_nums = [p["page_number"] for p in pages]
                    page_range = f"p{min(page_nums)}-p{max(page_nums)}"
                    page_range_str = f"Pages {min(page_nums)}-{max(page_nums)}"

                    # Use same logic as _generate_reference_file
                    if total_sections == 1:
                        link_filename = f"{pdf_basename}.md" if pdf_basename else "main.md"
                    else:
                        base_name = pdf_basename if pdf_basename else "section"
                        link_filename = f"{base_name}_{page_range}.md"
                else:
                    link_filename = f"section_{section_num:02d}.md"
                    page_range_str = "N/A"

                f.write(
                    f"- [{cat_data['title']}]({link_filename}) ({page_count} pages, {page_range_str})\n"
                )
                section_num += 1

            f.write("\n## Statistics\n\n")
            stats = self.extracted_data.get("quality_statistics", {})
            f.write(f"- Total pages: {self.extracted_data.get('total_pages', 0)}\n")
            f.write(f"- Code blocks: {self.extracted_data.get('total_code_blocks', 0)}\n")
            f.write(f"- Images: {self.extracted_data.get('total_images', 0)}\n")
            if stats:
                f.write(f"- Average code quality: {stats.get('average_quality', 0):.1f}/10\n")
                f.write(f"- Valid code blocks: {stats.get('valid_code_blocks', 0)}\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized):
        """Generate main SKILL.md file (enhanced with rich content)"""
        filename = f"{self.skill_dir}/SKILL.md"

        # Generate skill name (lowercase, hyphens only, max 64 chars)
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]

        # Truncate description to 1024 chars if needed
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filename, "w", encoding="utf-8") as f:
            # Write YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            f.write(f"# {self.name.title()} Documentation Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Enhanced "When to Use" section
            f.write("## 💡 When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Understand {self.name} concepts and fundamentals\n")
            f.write("- Look up API references and technical specifications\n")
            f.write("- Find code examples and implementation patterns\n")
            f.write("- Review tutorials, guides, and best practices\n")
            f.write("- Explore the complete documentation structure\n\n")

            # Chapter Overview (PDF structure)
            f.write("## 📖 Chapter Overview\n\n")
            total_pages = self.extracted_data.get("total_pages", 0)
            f.write(f"**Total Pages:** {total_pages}\n\n")
            f.write("**Content Breakdown:**\n\n")
            for _cat_key, cat_data in categorized.items():
                page_count = len(cat_data["pages"])
                f.write(f"- **{cat_data['title']}**: {page_count} pages\n")
            f.write("\n")

            # Extract key concepts from headings
            f.write(self._format_key_concepts())

            # Quick Reference with patterns
            f.write("## ⚡ Quick Reference\n\n")
            f.write(self._format_patterns_from_content())

            # Enhanced code examples section (top 15, grouped by language)
            all_code = []
            for page in self.extracted_data["pages"]:
                all_code.extend(page.get("code_samples", []))

            # Sort by quality and get top 15
            all_code.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            top_code = all_code[:15]

            if top_code:
                f.write("## 📝 Code Examples\n\n")
                f.write("*High-quality examples extracted from documentation*\n\n")

                # Group by language
                by_lang = {}
                for code in top_code:
                    lang = code.get("language", "unknown")
                    if lang not in by_lang:
                        by_lang[lang] = []
                    by_lang[lang].append(code)

                # Display grouped by language
                for lang in sorted(by_lang.keys()):
                    examples = by_lang[lang]
                    f.write(f"### {lang.title()} Examples ({len(examples)})\n\n")

                    for i, code in enumerate(examples[:5], 1):  # Top 5 per language
                        quality = code.get("quality_score", 0)
                        code_text = code.get("code", "")

                        f.write(f"**Example {i}** (Quality: {quality:.1f}/10):\n\n")
                        f.write(f"```{lang}\n")

                        # Show full code if short, truncate if long
                        if len(code_text) <= 500:
                            f.write(code_text)
                        else:
                            f.write(code_text[:500] + "\n...")

                        f.write("\n```\n\n")

            # Statistics
            f.write("## 📊 Documentation Statistics\n\n")
            f.write(f"- **Total Pages**: {total_pages}\n")
            total_code_blocks = self.extracted_data.get("total_code_blocks", 0)
            f.write(f"- **Code Blocks**: {total_code_blocks}\n")
            total_images = self.extracted_data.get("total_images", 0)
            f.write(f"- **Images/Diagrams**: {total_images}\n")

            # Language statistics
            langs = self.extracted_data.get("languages_detected", {})
            if langs:
                f.write(f"- **Programming Languages**: {len(langs)}\n\n")
                f.write("**Language Breakdown:**\n\n")
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {lang}: {count} examples\n")
                f.write("\n")

            # Quality metrics
            quality_stats = self.extracted_data.get("quality_statistics", {})
            if quality_stats:
                avg_quality = quality_stats.get("average_quality", 0)
                valid_blocks = quality_stats.get("valid_code_blocks", 0)
                f.write("**Code Quality:**\n\n")
                f.write(f"- Average Quality Score: {avg_quality:.1f}/10\n")
                f.write(f"- Valid Code Blocks: {valid_blocks}\n\n")

            # Navigation
            f.write("## 🗺️ Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            for _cat_key, cat_data in categorized.items():
                cat_file = self._sanitize_filename(cat_data["title"])
                f.write(f"- `references/{cat_file}.md` - {cat_data['title']}\n")
            f.write("\n")
            f.write("See `references/index.md` for complete documentation structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("**Generated by Skill Seeker** | PDF Documentation Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    def _format_key_concepts(self) -> str:
        """Extract key concepts from headings across all pages."""
        all_headings = []

        for page in self.extracted_data.get("pages", []):
            headings = page.get("headings", [])
            for heading in headings:
                text = heading.get("text", "").strip()
                level = heading.get("level", "h1")
                if text and len(text) > 3:  # Skip very short headings
                    all_headings.append((level, text))

        if not all_headings:
            return ""

        content = "## 🔑 Key Concepts\n\n"
        content += "*Main topics covered in this documentation*\n\n"

        # Group by level and show top concepts
        h1_headings = [text for level, text in all_headings if level == "h1"]
        h2_headings = [text for level, text in all_headings if level == "h2"]

        if h1_headings:
            content += "**Major Topics:**\n\n"
            for heading in h1_headings[:10]:  # Top 10
                content += f"- {heading}\n"
            content += "\n"

        if h2_headings:
            content += "**Subtopics:**\n\n"
            for heading in h2_headings[:15]:  # Top 15
                content += f"- {heading}\n"
            content += "\n"

        return content

    def _format_patterns_from_content(self) -> str:
        """Extract common patterns from text content."""
        # Look for common technical patterns in text
        patterns = []

        # Simple pattern extraction from headings and emphasized text
        for page in self.extracted_data.get("pages", []):
            _text = page.get("text", "")
            headings = page.get("headings", [])

            # Look for common pattern keywords in headings
            pattern_keywords = [
                "getting started",
                "installation",
                "configuration",
                "usage",
                "api",
                "examples",
                "tutorial",
                "guide",
                "best practices",
                "troubleshooting",
                "faq",
            ]

            for heading in headings:
                heading_text = heading.get("text", "").lower()
                for keyword in pattern_keywords:
                    if keyword in heading_text:
                        page_num = page.get("page_number", 0)
                        patterns.append(
                            {
                                "type": keyword.title(),
                                "heading": heading.get("text", ""),
                                "page": page_num,
                            }
                        )
                        break  # Only add once per heading

        if not patterns:
            return "*See reference files for detailed content*\n\n"

        content = "*Common documentation patterns found:*\n\n"

        # Group by type
        by_type = {}
        for pattern in patterns:
            ptype = pattern["type"]
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(pattern)

        # Display grouped patterns
        for ptype in sorted(by_type.keys()):
            items = by_type[ptype]
            content += f"**{ptype}** ({len(items)} sections):\n"
            for item in items[:3]:  # Top 3 per type
                content += f"- {item['heading']} (page {item['page']})\n"
            content += "\n"

        return content

    def _sanitize_filename(self, name):
        """Convert string to safe filename"""
        # Remove special chars, replace spaces with underscores
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF documentation to Claude skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--config", help="PDF config JSON file")
    parser.add_argument("--pdf", help="Direct PDF file path")
    parser.add_argument("--name", help="Skill name (with --pdf)")
    parser.add_argument("--from-json", help="Build skill from extracted JSON")
    parser.add_argument("--description", help="Skill description")

    args = parser.parse_args()

    # Validate inputs
    if not (args.config or args.pdf or args.from_json):
        parser.error("Must specify --config, --pdf, or --from-json")

    # Load or create config
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    elif args.from_json:
        # Build from extracted JSON
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": name,
            "description": args.description or f"Use when referencing {name} documentation",
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
            "name": args.name,
            "pdf_path": args.pdf,
            "description": args.description or f"Use when referencing {args.name} documentation",
            "extract_options": {
                "chunk_size": 10,
                "min_quality": 5.0,
                "extract_images": True,
                "min_image_size": 100,
            },
        }

    # Create converter
    try:
        converter = PDFToSkillConverter(config)

        # Extract if needed
        if config.get("pdf_path") and not converter.extract_pdf():
            print("\n❌ PDF extraction failed - see error above", file=sys.stderr)
            sys.exit(1)

        # Build skill
        converter.build_skill()

    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during PDF processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
