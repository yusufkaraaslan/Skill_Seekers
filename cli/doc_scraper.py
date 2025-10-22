#!/usr/bin/env python3
"""
Documentation to Claude Skill Converter
Single tool to scrape any documentation and create high-quality Claude skills.

Usage:
    python3 cli/doc_scraper.py --interactive
    python3 cli/doc_scraper.py --config configs/godot.json
    python3 cli/doc_scraper.py --url https://react.dev/ --name react
"""

import os
import sys
import json
import time
import re
import argparse
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque, defaultdict


class DocToSkillConverter:
    def __init__(self, config, dry_run=False, resume=False):
        self.config = config
        self.name = config['name']
        self.base_url = config['base_url']
        self.dry_run = dry_run
        self.resume = resume

        # Paths
        self.data_dir = f"output/{self.name}_data"
        self.skill_dir = f"output/{self.name}"
        self.checkpoint_file = f"{self.data_dir}/checkpoint.json"

        # Checkpoint config
        checkpoint_config = config.get('checkpoint', {})
        self.checkpoint_enabled = checkpoint_config.get('enabled', False)
        self.checkpoint_interval = checkpoint_config.get('interval', 1000)

        # Parallel scraping config
        self.workers = config.get('workers', 1)

        # State
        self.visited_urls = set()
        # Support multiple starting URLs
        start_urls = config.get('start_urls', [self.base_url])
        self.pending_urls = deque(start_urls)
        self.pages = []
        self.pages_scraped = 0

        # Thread-safe lock for parallel scraping
        if self.workers > 1:
            import threading
            self.lock = threading.Lock()

        # Create directories (unless dry-run)
        if not dry_run:
            os.makedirs(f"{self.data_dir}/pages", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
            os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Load checkpoint if resuming
        if resume and not dry_run:
            self.load_checkpoint()
    
    def is_valid_url(self, url):
        """Check if URL should be scraped"""
        if not url.startswith(self.base_url):
            return False

        # Include patterns
        includes = self.config.get('url_patterns', {}).get('include', [])
        if includes and not any(pattern in url for pattern in includes):
            return False

        # Exclude patterns
        excludes = self.config.get('url_patterns', {}).get('exclude', [])
        if any(pattern in url for pattern in excludes):
            return False

        return True

    def save_checkpoint(self):
        """Save progress checkpoint"""
        if not self.checkpoint_enabled or self.dry_run:
            return

        checkpoint_data = {
            "config": self.config,
            "visited_urls": list(self.visited_urls),
            "pending_urls": list(self.pending_urls),
            "pages_scraped": self.pages_scraped,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checkpoint_interval": self.checkpoint_interval
        }

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            print(f"  💾 Checkpoint saved ({self.pages_scraped} pages)")
        except Exception as e:
            print(f"  ⚠️  Failed to save checkpoint: {e}")

    def load_checkpoint(self):
        """Load progress from checkpoint"""
        if not os.path.exists(self.checkpoint_file):
            print("ℹ️  No checkpoint found, starting fresh")
            return

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            self.visited_urls = set(checkpoint_data["visited_urls"])
            self.pending_urls = deque(checkpoint_data["pending_urls"])
            self.pages_scraped = checkpoint_data["pages_scraped"]

            print(f"✅ Resumed from checkpoint")
            print(f"   Pages already scraped: {self.pages_scraped}")
            print(f"   URLs visited: {len(self.visited_urls)}")
            print(f"   URLs pending: {len(self.pending_urls)}")
            print(f"   Last updated: {checkpoint_data['last_updated']}")
            print("")

        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            print("   Starting fresh")

    def clear_checkpoint(self):
        """Remove checkpoint file"""
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                print(f"✅ Checkpoint cleared")
            except Exception as e:
                print(f"⚠️  Failed to clear checkpoint: {e}")

    def extract_content(self, soup, url):
        """Extract content with improved code and pattern detection"""
        page = {
            'url': url,
            'title': '',
            'content': '',
            'headings': [],
            'code_samples': [],
            'patterns': [],  # NEW: Extract common patterns
            'links': []
        }
        
        selectors = self.config.get('selectors', {})
        
        # Extract title
        title_elem = soup.select_one(selectors.get('title', 'title'))
        if title_elem:
            page['title'] = self.clean_text(title_elem.get_text())
        
        # Find main content
        main_selector = selectors.get('main_content', 'div[role="main"]')
        main = soup.select_one(main_selector)
        
        if not main:
            print(f"⚠ No content: {url}")
            return page
        
        # Extract headings with better structure
        for h in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = self.clean_text(h.get_text())
            if text:
                page['headings'].append({
                    'level': h.name,
                    'text': text,
                    'id': h.get('id', '')
                })
        
        # Extract code with language detection
        code_selector = selectors.get('code_blocks', 'pre code')
        for code_elem in main.select(code_selector):
            code = code_elem.get_text()
            if len(code.strip()) > 10:
                # Try to detect language
                lang = self.detect_language(code_elem, code)
                page['code_samples'].append({
                    'code': code.strip(),
                    'language': lang
                })
        
        # Extract patterns (NEW: common code patterns)
        page['patterns'] = self.extract_patterns(main, page['code_samples'])
        
        # Extract paragraphs
        paragraphs = []
        for p in main.find_all('p'):
            text = self.clean_text(p.get_text())
            if text and len(text) > 20:  # Skip very short paragraphs
                paragraphs.append(text)
        
        page['content'] = '\n\n'.join(paragraphs)
        
        # Extract links
        for link in main.find_all('a', href=True):
            href = urljoin(url, link['href'])
            # Strip anchor fragments to avoid treating #anchors as separate pages
            href = href.split('#')[0]
            if self.is_valid_url(href) and href not in page['links']:
                page['links'].append(href)
        
        return page
    
    def detect_language(self, elem, code):
        """Detect programming language from code block"""
        # Check class attribute
        classes = elem.get('class', [])
        for cls in classes:
            if 'language-' in cls:
                return cls.replace('language-', '')
            if 'lang-' in cls:
                return cls.replace('lang-', '')
        
        # Check parent pre element
        parent = elem.parent
        if parent and parent.name == 'pre':
            classes = parent.get('class', [])
            for cls in classes:
                if 'language-' in cls:
                    return cls.replace('language-', '')
        
        # Heuristic detection
        if 'import ' in code and 'from ' in code:
            return 'python'
        if 'const ' in code or 'let ' in code or '=>' in code:
            return 'javascript'
        if 'func ' in code and 'var ' in code:
            return 'gdscript'
        if 'def ' in code and ':' in code:
            return 'python'
        if '#include' in code or 'int main' in code:
            return 'cpp'
        
        return 'unknown'
    
    def extract_patterns(self, main, code_samples):
        """Extract common coding patterns (NEW FEATURE)"""
        patterns = []
        
        # Look for "Example:" or "Pattern:" sections
        for elem in main.find_all(['p', 'div']):
            text = elem.get_text().lower()
            if any(word in text for word in ['example:', 'pattern:', 'usage:', 'typical use']):
                # Get the code that follows
                next_code = elem.find_next(['pre', 'code'])
                if next_code:
                    patterns.append({
                        'description': self.clean_text(elem.get_text()),
                        'code': next_code.get_text().strip()
                    })
        
        return patterns[:5]  # Limit to 5 most relevant patterns
    
    def clean_text(self, text):
        """Clean text content"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def save_page(self, page):
        """Save page data"""
        url_hash = hashlib.md5(page['url'].encode()).hexdigest()[:10]
        safe_title = re.sub(r'[^\w\s-]', '', page['title'])[:50]
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        filename = f"{safe_title}_{url_hash}.json"
        filepath = os.path.join(self.data_dir, "pages", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(page, f, indent=2, ensure_ascii=False)
    
    def scrape_page(self, url):
        """Scrape a single page (thread-safe)"""
        try:
            # Scraping part (no lock needed - independent)
            headers = {'User-Agent': 'Mozilla/5.0 (Documentation Scraper)'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            page = self.extract_content(soup, url)

            # Thread-safe operations (lock required)
            if self.workers > 1:
                with self.lock:
                    print(f"  {url}")
                    self.save_page(page)
                    self.pages.append(page)

                    # Add new URLs
                    for link in page['links']:
                        if link not in self.visited_urls and link not in self.pending_urls:
                            self.pending_urls.append(link)
            else:
                # Single-threaded mode (no lock needed)
                print(f"  {url}")
                self.save_page(page)
                self.pages.append(page)

                # Add new URLs
                for link in page['links']:
                    if link not in self.visited_urls and link not in self.pending_urls:
                        self.pending_urls.append(link)

            # Rate limiting
            rate_limit = self.config.get('rate_limit', 0.5)
            if rate_limit > 0:
                time.sleep(rate_limit)

        except Exception as e:
            if self.workers > 1:
                with self.lock:
                    print(f"  ✗ Error on {url}: {e}")
            else:
                print(f"  ✗ Error: {e}")
    
    def scrape_all(self):
        """Scrape all pages (supports parallel scraping)"""
        print(f"\n{'='*60}")
        if self.dry_run:
            print(f"DRY RUN: {self.name}")
        else:
            print(f"SCRAPING: {self.name}")
        print(f"{'='*60}")
        print(f"Base URL: {self.base_url}")

        if self.dry_run:
            print(f"Mode: Preview only (no actual scraping)\n")
        else:
            print(f"Output: {self.data_dir}")
            if self.workers > 1:
                print(f"Workers: {self.workers} parallel threads")
            print()

        max_pages = self.config.get('max_pages', 500)

        # Handle unlimited mode
        if max_pages is None or max_pages == -1:
            print(f"⚠️  UNLIMITED MODE: No page limit (will scrape all pages)\n")
            unlimited = True
        else:
            unlimited = False

        # Dry run: preview first 20 URLs
        preview_limit = 20 if self.dry_run else max_pages

        # Single-threaded mode (original sequential logic)
        if self.workers <= 1:
            while self.pending_urls and (unlimited or len(self.visited_urls) < preview_limit):
                url = self.pending_urls.popleft()

                if url in self.visited_urls:
                    continue

                self.visited_urls.add(url)

                if self.dry_run:
                    # Just show what would be scraped
                    print(f"  [Preview] {url}")
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0 (Documentation Scraper - Dry Run)'}
                        response = requests.get(url, headers=headers, timeout=10)
                        soup = BeautifulSoup(response.content, 'html.parser')

                        main_selector = self.config.get('selectors', {}).get('main_content', 'div[role="main"]')
                        main = soup.select_one(main_selector)

                        if main:
                            for link in main.find_all('a', href=True):
                                href = urljoin(url, link['href'])
                                if self.is_valid_url(href) and href not in self.visited_urls:
                                    self.pending_urls.append(href)
                    except:
                        pass
                else:
                    self.scrape_page(url)
                    self.pages_scraped += 1

                    if self.checkpoint_enabled and self.pages_scraped % self.checkpoint_interval == 0:
                        self.save_checkpoint()

                if len(self.visited_urls) % 10 == 0:
                    print(f"  [{len(self.visited_urls)} pages]")

        # Multi-threaded mode (parallel scraping)
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            print(f"🚀 Starting parallel scraping with {self.workers} workers\n")

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = []

                while self.pending_urls and (unlimited or len(self.visited_urls) < preview_limit):
                    # Get next batch of URLs (thread-safe)
                    batch = []
                    batch_size = min(self.workers * 2, len(self.pending_urls))

                    with self.lock:
                        for _ in range(batch_size):
                            if not self.pending_urls:
                                break
                            url = self.pending_urls.popleft()

                            if url not in self.visited_urls:
                                self.visited_urls.add(url)
                                batch.append(url)

                    # Submit batch to executor
                    for url in batch:
                        if unlimited or len(self.visited_urls) <= preview_limit:
                            future = executor.submit(self.scrape_page, url)
                            futures.append(future)

                    # Wait for some to complete before submitting more
                    completed = 0
                    for future in as_completed(futures[:batch_size]):
                        # Check for exceptions
                        try:
                            future.result()  # Raises exception if scrape_page failed
                        except Exception as e:
                            with self.lock:
                                print(f"  ⚠️  Worker exception: {e}")

                        completed += 1

                        with self.lock:
                            self.pages_scraped += 1

                            if self.checkpoint_enabled and self.pages_scraped % self.checkpoint_interval == 0:
                                self.save_checkpoint()

                            if self.pages_scraped % 10 == 0:
                                print(f"  [{self.pages_scraped} pages scraped]")

                    # Remove completed futures
                    futures = [f for f in futures if not f.done()]

                # Wait for remaining futures
                for future in as_completed(futures):
                    # Check for exceptions
                    try:
                        future.result()
                    except Exception as e:
                        with self.lock:
                            print(f"  ⚠️  Worker exception: {e}")

                    with self.lock:
                        self.pages_scraped += 1

        if self.dry_run:
            print(f"\n✅ Dry run complete: would scrape ~{len(self.visited_urls)} pages")
            if len(self.visited_urls) >= preview_limit:
                print(f"   (showing first {preview_limit}, actual scraping may find more)")
            print(f"\n💡 To actually scrape, run without --dry-run")
        else:
            print(f"\n✅ Scraped {len(self.visited_urls)} pages")
            self.save_summary()
    
    def save_summary(self):
        """Save scraping summary"""
        summary = {
            'name': self.name,
            'total_pages': len(self.pages),
            'base_url': self.base_url,
            'pages': [{'title': p['title'], 'url': p['url']} for p in self.pages]
        }
        
        with open(f"{self.data_dir}/summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def load_scraped_data(self):
        """Load previously scraped data"""
        pages = []
        pages_dir = Path(self.data_dir) / "pages"
        
        if not pages_dir.exists():
            return []
        
        for json_file in pages_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    pages.append(json.load(f))
            except Exception as e:
                print(f"⚠ Error loading {json_file}: {e}")
        
        return pages
    
    def smart_categorize(self, pages):
        """Improved categorization with better pattern matching"""
        category_defs = self.config.get('categories', {})
        
        # Default smart categories if none provided
        if not category_defs:
            category_defs = self.infer_categories(pages)
        
        categories = {cat: [] for cat in category_defs.keys()}
        categories['other'] = []
        
        for page in pages:
            url = page['url'].lower()
            title = page['title'].lower()
            content = page.get('content', '').lower()[:500]  # Check first 500 chars
            
            categorized = False
            
            # Match against keywords
            for cat, keywords in category_defs.items():
                score = 0
                for keyword in keywords:
                    keyword = keyword.lower()
                    if keyword in url:
                        score += 3
                    if keyword in title:
                        score += 2
                    if keyword in content:
                        score += 1
                
                if score >= 2:  # Threshold for categorization
                    categories[cat].append(page)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(page)
        
        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}
        
        return categories
    
    def infer_categories(self, pages):
        """Infer categories from URL patterns (IMPROVED)"""
        url_segments = defaultdict(int)
        
        for page in pages:
            path = urlparse(page['url']).path
            segments = [s for s in path.split('/') if s and s not in ['en', 'stable', 'latest', 'docs']]
            
            for seg in segments:
                url_segments[seg] += 1
        
        # Top segments become categories
        top_segments = sorted(url_segments.items(), key=lambda x: x[1], reverse=True)[:8]
        
        categories = {}
        for seg, count in top_segments:
            if count >= 3:  # At least 3 pages
                categories[seg] = [seg]
        
        # Add common defaults
        if 'tutorial' not in categories and any('tutorial' in url for url in [p['url'] for p in pages]):
            categories['tutorials'] = ['tutorial', 'guide', 'getting-started']
        
        if 'api' not in categories and any('api' in url or 'reference' in url for url in [p['url'] for p in pages]):
            categories['api'] = ['api', 'reference', 'class']
        
        return categories
    
    def generate_quick_reference(self, pages):
        """Generate quick reference from common patterns (NEW FEATURE)"""
        quick_ref = []
        
        # Collect all patterns
        all_patterns = []
        for page in pages:
            all_patterns.extend(page.get('patterns', []))
        
        # Get most common code patterns
        seen_codes = set()
        for pattern in all_patterns:
            code = pattern['code']
            if code not in seen_codes and len(code) < 300:
                quick_ref.append(pattern)
                seen_codes.add(code)
                if len(quick_ref) >= 15:
                    break
        
        return quick_ref
    
    def create_reference_file(self, category, pages):
        """Create enhanced reference file"""
        if not pages:
            return
        
        lines = []
        lines.append(f"# {self.name.title()} - {category.replace('_', ' ').title()}\n")
        lines.append(f"**Pages:** {len(pages)}\n")
        lines.append("---\n")
        
        for page in pages:
            lines.append(f"## {page['title']}\n")
            lines.append(f"**URL:** {page['url']}\n")
            
            # Table of contents from headings
            if page.get('headings'):
                lines.append("**Contents:**")
                for h in page['headings'][:10]:
                    level = int(h['level'][1]) if len(h['level']) > 1 else 1
                    indent = "  " * max(0, level - 2)
                    lines.append(f"{indent}- {h['text']}")
                lines.append("")
            
            # Content
            if page.get('content'):
                content = page['content'][:2500]
                if len(page['content']) > 2500:
                    content += "\n\n*[Content truncated]*"
                lines.append(content)
                lines.append("")
            
            # Code examples with language
            if page.get('code_samples'):
                lines.append("**Examples:**\n")
                for i, sample in enumerate(page['code_samples'][:4], 1):
                    lang = sample.get('language', 'unknown')
                    code = sample.get('code', sample if isinstance(sample, str) else '')
                    lines.append(f"Example {i} ({lang}):")
                    lines.append(f"```{lang}")
                    lines.append(code[:600])
                    if len(code) > 600:
                        lines.append("...")
                    lines.append("```\n")
            
            lines.append("---\n")
        
        filepath = os.path.join(self.skill_dir, "references", f"{category}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"  ✓ {category}.md ({len(pages)} pages)")
    
    def create_enhanced_skill_md(self, categories, quick_ref):
        """Create SKILL.md with actual examples (IMPROVED)"""
        description = self.config.get('description', f'Comprehensive assistance with {self.name}')
        
        # Extract actual code examples from docs
        example_codes = []
        for pages in categories.values():
            for page in pages[:3]:  # First 3 pages per category
                for sample in page.get('code_samples', [])[:2]:  # First 2 samples per page
                    code = sample.get('code', sample if isinstance(sample, str) else '')
                    lang = sample.get('language', 'unknown')
                    if len(code) < 200 and lang != 'unknown':
                        example_codes.append((lang, code))
                    if len(example_codes) >= 10:
                        break
                if len(example_codes) >= 10:
                    break
            if len(example_codes) >= 10:
                break
        
        content = f"""---
name: {self.name}
description: {description}
---

# {self.name.title()} Skill

Comprehensive assistance with {self.name} development, generated from official documentation.

## When to Use This Skill

This skill should be triggered when:
- Working with {self.name}
- Asking about {self.name} features or APIs
- Implementing {self.name} solutions
- Debugging {self.name} code
- Learning {self.name} best practices

## Quick Reference

### Common Patterns

"""
        
        # Add actual quick reference patterns
        if quick_ref:
            for i, pattern in enumerate(quick_ref[:8], 1):
                content += f"**Pattern {i}:** {pattern.get('description', 'Example pattern')}\n\n"
                content += "```\n"
                content += pattern.get('code', '')[:300]
                content += "\n```\n\n"
        else:
            content += "*Quick reference patterns will be added as you use the skill.*\n\n"
        
        # Add example codes from docs
        if example_codes:
            content += "### Example Code Patterns\n\n"
            for i, (lang, code) in enumerate(example_codes[:5], 1):
                content += f"**Example {i}** ({lang}):\n```{lang}\n{code}\n```\n\n"
        
        content += f"""## Reference Files

This skill includes comprehensive documentation in `references/`:

"""
        
        for cat in sorted(categories.keys()):
            content += f"- **{cat}.md** - {cat.replace('_', ' ').title()} documentation\n"
        
        content += """
Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
"""
        
        filepath = os.path.join(self.skill_dir, "SKILL.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ SKILL.md (enhanced with {len(example_codes)} examples)")
    
    def create_index(self, categories):
        """Create navigation index"""
        lines = []
        lines.append(f"# {self.name.title()} Documentation Index\n")
        lines.append("## Categories\n")
        
        for cat, pages in sorted(categories.items()):
            lines.append(f"### {cat.replace('_', ' ').title()}")
            lines.append(f"**File:** `{cat}.md`")
            lines.append(f"**Pages:** {len(pages)}\n")
        
        filepath = os.path.join(self.skill_dir, "references", "index.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("  ✓ index.md")
    
    def build_skill(self):
        """Build the skill from scraped data"""
        print(f"\n{'='*60}")
        print(f"BUILDING SKILL: {self.name}")
        print(f"{'='*60}\n")
        
        # Load data
        print("Loading scraped data...")
        pages = self.load_scraped_data()
        
        if not pages:
            print("✗ No scraped data found!")
            return False
        
        print(f"  ✓ Loaded {len(pages)} pages\n")
        
        # Categorize
        print("Categorizing pages...")
        categories = self.smart_categorize(pages)
        print(f"  ✓ Created {len(categories)} categories\n")
        
        # Generate quick reference
        print("Generating quick reference...")
        quick_ref = self.generate_quick_reference(pages)
        print(f"  ✓ Extracted {len(quick_ref)} patterns\n")
        
        # Create reference files
        print("Creating reference files...")
        for cat, cat_pages in categories.items():
            self.create_reference_file(cat, cat_pages)
        
        # Create index
        self.create_index(categories)
        print()
        
        # Create enhanced SKILL.md
        print("Creating SKILL.md...")
        self.create_enhanced_skill_md(categories, quick_ref)
        
        print(f"\n✅ Skill built: {self.skill_dir}/")
        return True


def validate_config(config):
    """Validate configuration structure"""
    errors = []
    warnings = []

    # Required fields
    required_fields = ['name', 'base_url']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: '{field}'")

    # Validate name (alphanumeric, hyphens, underscores only)
    if 'name' in config:
        if not re.match(r'^[a-zA-Z0-9_-]+$', config['name']):
            errors.append(f"Invalid name: '{config['name']}' (use only letters, numbers, hyphens, underscores)")

    # Validate base_url
    if 'base_url' in config:
        if not config['base_url'].startswith(('http://', 'https://')):
            errors.append(f"Invalid base_url: '{config['base_url']}' (must start with http:// or https://)")

    # Validate selectors structure
    if 'selectors' in config:
        if not isinstance(config['selectors'], dict):
            errors.append("'selectors' must be a dictionary")
        else:
            recommended_selectors = ['main_content', 'title', 'code_blocks']
            for selector in recommended_selectors:
                if selector not in config['selectors']:
                    warnings.append(f"Missing recommended selector: '{selector}'")
    else:
        warnings.append("Missing 'selectors' section (recommended)")

    # Validate url_patterns
    if 'url_patterns' in config:
        if not isinstance(config['url_patterns'], dict):
            errors.append("'url_patterns' must be a dictionary")
        else:
            for key in ['include', 'exclude']:
                if key in config['url_patterns']:
                    if not isinstance(config['url_patterns'][key], list):
                        errors.append(f"'url_patterns.{key}' must be a list")

    # Validate categories
    if 'categories' in config:
        if not isinstance(config['categories'], dict):
            errors.append("'categories' must be a dictionary")
        else:
            for cat_name, keywords in config['categories'].items():
                if not isinstance(keywords, list):
                    errors.append(f"'categories.{cat_name}' must be a list of keywords")

    # Validate rate_limit
    if 'rate_limit' in config:
        try:
            rate = float(config['rate_limit'])
            if rate < 0:
                errors.append(f"'rate_limit' must be non-negative (got {rate})")
            elif rate > 10:
                warnings.append(f"'rate_limit' is very high ({rate}s) - this may slow down scraping significantly")
        except (ValueError, TypeError):
            errors.append(f"'rate_limit' must be a number (got {config['rate_limit']})")

    # Validate max_pages
    if 'max_pages' in config:
        max_p_value = config['max_pages']

        # Allow None for unlimited
        if max_p_value is None:
            warnings.append("'max_pages' is None (unlimited) - this will scrape ALL pages. Use with caution!")
        else:
            try:
                max_p = int(max_p_value)
                # Allow -1 for unlimited
                if max_p == -1:
                    warnings.append("'max_pages' is -1 (unlimited) - this will scrape ALL pages. Use with caution!")
                elif max_p < 1:
                    errors.append(f"'max_pages' must be at least 1 or -1 for unlimited (got {max_p})")
                elif max_p > 10000:
                    warnings.append(f"'max_pages' is very high ({max_p}) - scraping may take a very long time")
            except (ValueError, TypeError):
                errors.append(f"'max_pages' must be an integer, -1, or null (got {config['max_pages']})")

    # Validate start_urls if present
    if 'start_urls' in config:
        if not isinstance(config['start_urls'], list):
            errors.append("'start_urls' must be a list")
        else:
            for url in config['start_urls']:
                if not url.startswith(('http://', 'https://')):
                    errors.append(f"Invalid start_url: '{url}' (must start with http:// or https://)")

    return errors, warnings


def load_config(config_path):
    """Load and validate configuration from file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)

    # Validate config
    errors, warnings = validate_config(config)

    # Show warnings (non-blocking)
    if warnings:
        print(f"⚠️  Configuration warnings in {config_path}:")
        for warning in warnings:
            print(f"   - {warning}")
        print()

    # Show errors (blocking)
    if errors:
        print(f"❌ Configuration validation errors in {config_path}:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)

    return config


def interactive_config():
    """Interactive configuration"""
    print("\n" + "="*60)
    print("Documentation to Skill Converter")
    print("="*60 + "\n")
    
    config = {}
    
    # Basic info
    config['name'] = input("Skill name (e.g., 'react', 'godot'): ").strip()
    config['description'] = input("Skill description: ").strip()
    config['base_url'] = input("Base URL (e.g., https://docs.example.com/): ").strip()
    
    if not config['base_url'].endswith('/'):
        config['base_url'] += '/'
    
    # Selectors
    print("\nCSS Selectors (press Enter for defaults):")
    selectors = {}
    selectors['main_content'] = input("  Main content [div[role='main']]: ").strip() or "div[role='main']"
    selectors['title'] = input("  Title [title]: ").strip() or "title"
    selectors['code_blocks'] = input("  Code blocks [pre code]: ").strip() or "pre code"
    config['selectors'] = selectors
    
    # URL patterns
    print("\nURL Patterns (comma-separated, optional):")
    include = input("  Include: ").strip()
    exclude = input("  Exclude: ").strip()
    config['url_patterns'] = {
        'include': [p.strip() for p in include.split(',') if p.strip()],
        'exclude': [p.strip() for p in exclude.split(',') if p.strip()]
    }
    
    # Settings
    rate = input("\nRate limit (seconds) [0.5]: ").strip()
    config['rate_limit'] = float(rate) if rate else 0.5
    
    max_p = input("Max pages [500]: ").strip()
    config['max_pages'] = int(max_p) if max_p else 500
    
    return config


def check_existing_data(name):
    """Check if scraped data already exists"""
    data_dir = f"output/{name}_data"
    if os.path.exists(data_dir) and os.path.exists(f"{data_dir}/summary.json"):
        with open(f"{data_dir}/summary.json", 'r') as f:
            summary = json.load(f)
        return True, summary.get('total_pages', 0)
    return False, 0


def main():
    parser = argparse.ArgumentParser(
        description='Convert documentation websites to Claude skills',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive configuration mode')
    parser.add_argument('--config', '-c', type=str,
                       help='Load configuration from file (e.g., configs/godot.json)')
    parser.add_argument('--name', type=str,
                       help='Skill name')
    parser.add_argument('--url', type=str,
                       help='Base documentation URL')
    parser.add_argument('--description', '-d', type=str,
                       help='Skill description')
    parser.add_argument('--skip-scrape', action='store_true',
                       help='Skip scraping, use existing data')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what will be scraped without actually scraping')
    parser.add_argument('--enhance', action='store_true',
                       help='Enhance SKILL.md using Claude API after building (requires API key)')
    parser.add_argument('--enhance-local', action='store_true',
                       help='Enhance SKILL.md using Claude Code in new terminal (no API key needed)')
    parser.add_argument('--api-key', type=str,
                       help='Anthropic API key for --enhance (or set ANTHROPIC_API_KEY)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint (for interrupted scrapes)')
    parser.add_argument('--fresh', action='store_true',
                       help='Clear checkpoint and start fresh')
    parser.add_argument('--rate-limit', '-r', type=float, metavar='SECONDS',
                       help='Override rate limit in seconds (default: from config or 0.5). Use 0 for no delay.')
    parser.add_argument('--workers', '-w', type=int, metavar='N',
                       help='Number of parallel workers for faster scraping (default: 1, max: 10)')
    parser.add_argument('--no-rate-limit', action='store_true',
                       help='Disable rate limiting completely (same as --rate-limit 0)')

    args = parser.parse_args()

    # Get configuration
    if args.config:
        config = load_config(args.config)
    elif args.interactive or not (args.name and args.url):
        config = interactive_config()
    else:
        config = {
            'name': args.name,
            'description': args.description or f'Comprehensive assistance with {args.name}',
            'base_url': args.url,
            'selectors': {
                'main_content': "div[role='main']",
                'title': 'title',
                'code_blocks': 'pre code'
            },
            'url_patterns': {'include': [], 'exclude': []},
            'rate_limit': 0.5,
            'max_pages': 500
        }

    # Apply CLI overrides
    if args.no_rate_limit:
        config['rate_limit'] = 0
        print(f"⚡ Rate limiting disabled")
    elif args.rate_limit is not None:
        config['rate_limit'] = args.rate_limit
        if args.rate_limit == 0:
            print(f"⚡ Rate limiting disabled")
        else:
            print(f"⚡ Rate limit override: {args.rate_limit}s per page")

    if args.workers:
        # Validate workers count
        if args.workers < 1:
            print(f"❌ Error: --workers must be at least 1")
            sys.exit(1)
        if args.workers > 10:
            print(f"⚠️  Warning: --workers capped at 10 (requested {args.workers})")
            args.workers = 10
        config['workers'] = args.workers
        if args.workers > 1:
            print(f"🚀 Parallel scraping enabled: {args.workers} workers")
    
    # Dry run mode - preview only
    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN MODE")
        print(f"{'='*60}")
        print("This will show what would be scraped without saving anything.\n")

        converter = DocToSkillConverter(config, dry_run=True)
        converter.scrape_all()

        print(f"\n📋 Configuration Summary:")
        print(f"   Name: {config['name']}")
        print(f"   Base URL: {config['base_url']}")
        print(f"   Max pages: {config.get('max_pages', 500)}")
        print(f"   Rate limit: {config.get('rate_limit', 0.5)}s")
        print(f"   Categories: {len(config.get('categories', {}))}")
        return

    # Check for existing data
    exists, page_count = check_existing_data(config['name'])

    if exists and not args.skip_scrape:
        print(f"\n✓ Found existing data: {page_count} pages")
        response = input("Use existing data? (y/n): ").strip().lower()
        if response == 'y':
            args.skip_scrape = True

    # Create converter
    converter = DocToSkillConverter(config, resume=args.resume)

    # Handle fresh start (clear checkpoint)
    if args.fresh:
        converter.clear_checkpoint()

    # Scrape or skip
    if not args.skip_scrape:
        try:
            converter.scrape_all()
            # Save final checkpoint
            if converter.checkpoint_enabled:
                converter.save_checkpoint()
                print("\n💾 Final checkpoint saved")
                # Clear checkpoint after successful completion
                converter.clear_checkpoint()
                print("✅ Scraping complete - checkpoint cleared")
        except KeyboardInterrupt:
            print("\n\nScraping interrupted.")
            if converter.checkpoint_enabled:
                converter.save_checkpoint()
                print(f"💾 Progress saved to checkpoint")
                print(f"   Resume with: --config {args.config if args.config else 'config.json'} --resume")
            response = input("Continue with skill building? (y/n): ").strip().lower()
            if response != 'y':
                return
    else:
        print(f"\n⏭️  Skipping scrape, using existing data")

    # Build skill
    success = converter.build_skill()

    if not success:
        sys.exit(1)

    # Optional enhancement with Claude API
    if args.enhance:
        print(f"\n{'='*60}")
        print(f"ENHANCING SKILL.MD WITH CLAUDE API")
        print(f"{'='*60}\n")

        try:
            import subprocess
            enhance_cmd = ['python3', 'cli/enhance_skill.py', f'output/{config["name"]}/']
            if args.api_key:
                enhance_cmd.extend(['--api-key', args.api_key])

            result = subprocess.run(enhance_cmd, check=True)
            if result.returncode == 0:
                print("\n✅ Enhancement complete!")
        except subprocess.CalledProcessError:
            print("\n⚠ Enhancement failed, but skill was still built")
        except FileNotFoundError:
            print("\n⚠ enhance_skill.py not found. Run manually:")
            print(f"  python3 cli/enhance_skill.py output/{config['name']}/")

    # Optional enhancement with Claude Code (local, no API key)
    if args.enhance_local:
        print(f"\n{'='*60}")
        print(f"ENHANCING SKILL.MD WITH CLAUDE CODE (LOCAL)")
        print(f"{'='*60}\n")

        try:
            import subprocess
            enhance_cmd = ['python3', 'cli/enhance_skill_local.py', f'output/{config["name"]}/']
            subprocess.run(enhance_cmd, check=True)
        except subprocess.CalledProcessError:
            print("\n⚠ Enhancement failed, but skill was still built")
        except FileNotFoundError:
            print("\n⚠ enhance_skill_local.py not found. Run manually:")
            print(f"  python3 cli/enhance_skill_local.py output/{config['name']}/")

    print(f"\n📦 Package your skill:")
    print(f"  python3 cli/package_skill.py output/{config['name']}/")

    if not args.enhance and not args.enhance_local:
        print(f"\n💡 Optional: Enhance SKILL.md with Claude:")
        print(f"  API-based:  python3 cli/enhance_skill.py output/{config['name']}/")
        print(f"              or re-run with: --enhance")
        print(f"  Local (no API key): python3 cli/enhance_skill_local.py output/{config['name']}/")
        print(f"                      or re-run with: --enhance-local")


if __name__ == "__main__":
    main()
