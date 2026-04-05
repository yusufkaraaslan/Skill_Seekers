#!/usr/bin/env python3
"""
Notion Workspace to Skill Converter

Converts Notion databases and pages into AI-ready skills. Two modes:

1. **API mode** — Uses the Notion API via ``notion-client`` to fetch databases,
   pages, and blocks in real time.  Requires an integration token.
2. **Export mode** — Parses a Notion Markdown/CSV export directory downloaded
   from Settings > Export.  No token required.

Usage:
    skill-seekers notion --database-id ID --token $NOTION_TOKEN --name myskill
    skill-seekers notion --page-id ID --token $NOTION_TOKEN --name myskill
    skill-seekers notion --export-path ./notion-export/ --name myskill
    skill-seekers notion --from-json output/myskill_notion_data.json --name myskill
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# Optional dependency guard — notion-client is not a core dependency
try:
    from notion_client import Client as NotionClient
    from notion_client import APIResponseError

    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_PAGES = 500
RATE_LIMIT_DELAY = 0.35  # seconds between API requests
MAX_BLOCK_DEPTH = 5


def _check_notion_deps() -> None:
    """Raise RuntimeError if notion-client is not installed."""
    if not NOTION_AVAILABLE:
        raise RuntimeError(
            "notion-client is required for Notion API mode.\n"
            'Install with: pip install "skill-seekers[notion]"\n'
            "Or: pip install notion-client"
        )


def infer_description_from_notion(metadata: dict | None = None, name: str = "") -> str:
    """Infer a skill description from Notion workspace metadata."""
    if metadata:
        desc_text = metadata.get("description", "")
        if desc_text and len(desc_text) > 20:
            desc = desc_text.strip()[:150]
            return f"Use when {desc.lower()}"
        title_text = metadata.get("title", "")
        if title_text and len(title_text) > 10:
            return f"Use when working with {title_text.lower()}"
    return (
        f"Use when referencing {name} documentation"
        if name
        else "Use when referencing this Notion workspace"
    )


class NotionToSkillConverter:
    """Convert Notion workspace content (database or page tree) to a skill.

    Args:
        config: Dict with keys name, database_id, page_id, export_path,
                token, description, max_pages.
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.name: str = config["name"]
        self.database_id: str | None = config.get("database_id")
        self.page_id: str | None = config.get("page_id")
        self.export_path: str | None = config.get("export_path")
        self.token: str | None = config.get("token") or os.getenv("NOTION_TOKEN")
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )
        self.max_pages: int = config.get("max_pages", DEFAULT_MAX_PAGES)
        self.skill_dir: str = f"output/{self.name}"
        self.data_file: str = f"output/{self.name}_notion_data.json"
        self._client: Any = None
        self.extracted_data: dict[str, Any] | None = None
        self._pages_fetched: int = 0
        self._blocks_fetched: int = 0

    # -- Notion client ---------------------------------------------------

    def _get_client(self) -> Any:
        """Return a cached Notion API client, creating one if needed."""
        _check_notion_deps()
        if self._client is None:
            if not self.token:
                raise ValueError("Notion integration token required. Set NOTION_TOKEN or --token.")
            self._client = NotionClient(auth=self.token)
            logger.info("Notion API client initialised")
        return self._client

    # -- Public extraction -----------------------------------------------

    def extract_notion(self) -> bool:
        """Extract content from Notion (API or export mode). Saves JSON."""
        print(f"\n--- Extracting Notion content for: {self.name}")

        if self.export_path:
            pages, source_mode = self._extract_from_export(), "export"
        elif self.database_id or self.page_id:
            pages, source_mode = self._extract_via_api(), "api"
        else:
            raise ValueError("Must specify --database-id, --page-id, or --export-path.")

        metadata: dict[str, Any] = {
            "title": self.name,
            "source_mode": source_mode,
            "database_id": self.database_id,
            "page_id": self.page_id,
            "export_path": self.export_path,
        }
        if not self.config.get("description"):
            self.description = infer_description_from_notion(metadata, self.name)

        result_data: dict[str, Any] = {
            "metadata": metadata,
            "total_pages": len(pages),
            "pages_fetched": self._pages_fetched,
            "blocks_fetched": self._blocks_fetched,
            "pages": pages,
        }
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
        self.extracted_data = result_data
        print(f"   Saved extracted data to: {self.data_file}")
        print(f"   Extracted {len(pages)} pages, {self._blocks_fetched} blocks")
        return True

    # -- Load extracted data ---------------------------------------------

    def load_extracted_data(self, json_path: str | None = None) -> bool:
        """Load previously extracted Notion data from JSON."""
        path = json_path or self.data_file
        print(f"\n   Loading extracted data from: {path}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        with open(path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_pages", len(self.extracted_data.get("pages", [])))
        print(f"   Loaded {total} pages")
        return True

    # -- Categorisation --------------------------------------------------

    def categorize_content(self) -> dict[str, dict[str, Any]]:
        """Categorize pages by database properties or page hierarchy."""
        if not self.extracted_data:
            raise RuntimeError("No extracted data available.")
        print("\n   Categorizing content...")
        pages = self.extracted_data.get("pages", [])
        categorized: dict[str, dict[str, Any]] = {}
        for page in pages:
            props = page.get("properties", {})
            cat_key = self._resolve_category_key(props, page.get("parent_path", ""))
            cat_title = cat_key.replace("_", " ").title()
            categorized.setdefault(cat_key, {"title": cat_title, "pages": []})
            categorized[cat_key]["pages"].append(page)
        if list(categorized.keys()) == ["other"]:
            categorized = {"content": {"title": "Content", "pages": pages}}
        print(f"   Created {len(categorized)} categories")
        for cat_data in categorized.values():
            print(f"     - {cat_data['title']}: {len(cat_data['pages'])} pages")
        return categorized

    def _resolve_category_key(self, properties: dict[str, Any], parent_path: str) -> str:
        """Determine category from properties (tags/category/type/status) or parent path."""
        for name in ("category", "Category", "tags", "Tags", "type", "Type", "status", "Status"):
            val = properties.get(name)
            if val:
                val = val[0] if isinstance(val, list) and val else val
                if isinstance(val, str) and val.strip():
                    return self._sanitize_key(val)
        if parent_path:
            first = parent_path.strip("/").split("/")[0]
            if first:
                return self._sanitize_key(first)
        return "other"

    @staticmethod
    def _sanitize_key(text: str) -> str:
        """Convert text to safe lowercase underscore key."""
        safe = re.sub(r"[^\w\s-]", "", text.lower())
        return re.sub(r"[-\s]+", "_", safe).strip("_") or "other"

    # -- Skill building --------------------------------------------------

    def build_skill(self) -> None:
        """Build complete skill directory (SKILL.md, references, index)."""
        if not self.extracted_data:
            raise RuntimeError("No extracted data available.")
        print(f"\n   Building skill: {self.name}")
        for subdir in ("references", "scripts", "assets"):
            os.makedirs(f"{self.skill_dir}/{subdir}", exist_ok=True)
        categorized = self.categorize_content()
        print("\n   Generating reference files...")
        total_cat = len(categorized)
        for i, (cat_key, cat_data) in enumerate(categorized.items(), 1):
            self._generate_reference_file(cat_key, cat_data, i, total_cat)
        self._generate_index(categorized)
        self._generate_skill_md(categorized)
        print(f"\n   Skill built successfully: {self.skill_dir}/")
        print(f"\n   Next step: Package with: skill-seekers package {self.skill_dir}/")

    def _generate_reference_file(
        self, cat_key: str, cat_data: dict[str, Any], section_num: int, total_sections: int
    ) -> None:
        """Generate a reference markdown file for one category."""
        pages = cat_data["pages"]
        filename = f"{self.skill_dir}/references/{cat_key}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")
            for page in pages:
                title = page.get("title", "Untitled")
                f.write(f"---\n\n## {title}\n\n")
                if page.get("url"):
                    f.write(f"*Source: [{page['url']}]({page['url']})*\n\n")
                props = page.get("properties", {})
                if props:
                    f.write("**Properties:**\n\n")
                    for pn, pv in props.items():
                        pv = ", ".join(str(v) for v in pv) if isinstance(pv, list) else pv
                        f.write(f"- **{pn}:** {pv}\n")
                    f.write("\n")
                if page.get("content"):
                    f.write(f"{page['content']}\n\n")
                for blk in page.get("code_blocks", []):
                    if blk.get("caption"):
                        f.write(f"*{blk['caption']}*\n\n")
                    f.write(f"```{blk.get('language', '')}\n{blk.get('code', '')}\n```\n\n")
        print(f"     Generated: {filename} ({len(pages)} pages)")

    def _generate_index(self, categorized: dict[str, dict[str, Any]]) -> None:
        """Generate references/index.md."""
        filename = f"{self.skill_dir}/references/index.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Reference Index\n\n## Categories\n\n")
            for cat_key, cat_data in categorized.items():
                f.write(f"- [{cat_data['title']}]({cat_key}.md) ({len(cat_data['pages'])} pages)\n")
            f.write("\n## Statistics\n\n")
            f.write(f"- Total pages: {self.extracted_data.get('total_pages', 0)}\n")
            f.write(f"- Blocks fetched: {self.extracted_data.get('blocks_fetched', 0)}\n")
            f.write(
                f"- Source mode: {self.extracted_data.get('metadata', {}).get('source_mode', 'unknown')}\n"
            )
        print(f"     Generated: {filename}")

    def _generate_skill_md(self, categorized: dict[str, dict[str, Any]]) -> None:
        """Generate main SKILL.md with YAML frontmatter."""
        filename = f"{self.skill_dir}/SKILL.md"
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024]
        meta = self.extracted_data.get("metadata", {})
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n")
            f.write(f"# {self.name.title()} Documentation Skill\n\n{self.description}\n\n")
            # Source info
            f.write(
                f"## Source Information\n\n**Source mode:** {meta.get('source_mode', 'unknown')}\n"
            )
            for key in ("database_id", "page_id", "export_path"):
                if meta.get(key):
                    f.write(f"**{key.replace('_', ' ').title()}:** `{meta[key]}`\n")
            f.write("\n## When to Use This Skill\n\nUse this skill when you need to:\n")
            f.write(f"- Understand {self.name} concepts and processes\n")
            f.write("- Look up structured database entries and their properties\n")
            f.write("- Find code examples and implementation notes\n")
            f.write("- Review documentation and knowledge base articles\n")
            f.write("- Explore the workspace hierarchy and relationships\n\n")
            # Content overview
            f.write(
                f"## Content Overview\n\n**Total Pages:** {self.extracted_data.get('total_pages', 0)}\n\n"
            )
            for cd in categorized.values():
                f.write(f"- **{cd['title']}**: {len(cd['pages'])} pages\n")
            f.write("\n")
            # Key topics
            topics = self._collect_key_topics()
            if topics:
                f.write("## Key Topics\n\n")
                for t in topics[:20]:
                    f.write(f"- {t}\n")
                f.write("\n")
            # Code highlights
            all_code = self._collect_code_blocks()
            if all_code:
                f.write("## Code Examples\n\n")
                by_lang: dict[str, list[dict[str, str]]] = {}
                for blk in all_code[:30]:
                    by_lang.setdefault(blk.get("language", "plain text"), []).append(blk)
                for lang in sorted(by_lang):
                    exs = by_lang[lang]
                    f.write(f"### {lang.title()} ({len(exs)} examples)\n\n")
                    for blk in exs[:3]:
                        code = blk.get("code", "")[:500]
                        f.write(f"```{lang}\n{code}\n```\n\n")
            # Property summary
            psummary = self._collect_property_summary()
            if psummary:
                f.write("## Database Properties\n\n")
                for pn, vals in psummary.items():
                    sample = ", ".join(sorted(vals)[:5])
                    f.write(f"- **{pn}** ({len(vals)} unique): {sample}\n")
                f.write("\n")
            # Navigation
            f.write("## Navigation\n\n")
            for ck, cd in categorized.items():
                f.write(f"- `references/{ck}.md` - {cd['title']}\n")
            f.write("\nSee `references/index.md` for complete reference structure.\n\n")
            f.write("---\n\n**Generated by Skill Seeker** | Notion Scraper\n")
        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"     Generated: {filename} ({line_count} lines)")

    # -- SKILL.md helpers ------------------------------------------------

    def _collect_key_topics(self) -> list[str]:
        """Extract unique heading texts from all pages."""
        topics, seen = [], set()
        for page in self.extracted_data.get("pages", []):
            for text in [page.get("title", "")] + [
                h.get("text", "") for h in page.get("headings", [])
            ]:
                text = text.strip()
                if text and text.lower() not in seen and len(text) > 3:
                    seen.add(text.lower())
                    topics.append(text)
        return topics

    def _collect_code_blocks(self) -> list[dict[str, str]]:
        """Collect all code blocks from extracted pages."""
        return [
            blk for p in self.extracted_data.get("pages", []) for blk in p.get("code_blocks", [])
        ]

    def _collect_property_summary(self) -> dict[str, set[str]]:
        """Collect unique property values across all pages."""
        summary: dict[str, set[str]] = {}
        for page in self.extracted_data.get("pages", []):
            for pn, pv in page.get("properties", {}).items():
                summary.setdefault(pn, set())
                if isinstance(pv, list):
                    summary[pn].update(str(v) for v in pv)
                elif pv is not None:
                    summary[pn].add(str(pv))
        return {k: v for k, v in summary.items() if v}

    # ====================================================================
    # API MODE
    # ====================================================================

    def _extract_via_api(self) -> list[dict[str, Any]]:
        """Fetch pages from Notion via API (database query or page tree walk)."""
        client = self._get_client()
        if self.database_id:
            print(f"   Fetching database: {self.database_id}")
            return self._extract_database_entries(client)
        print(f"   Fetching page tree: {self.page_id}")
        return self._extract_page_tree(client, self.page_id, parent_path="")

    def _extract_database_entries(self, client: Any) -> list[dict[str, Any]]:
        """Extract entries from a Notion database with properties."""
        pages: list[dict[str, Any]] = []
        has_more, cursor = True, None
        # Fetch DB metadata
        try:
            db_meta = client.databases.retrieve(database_id=self.database_id)
            logger.info(
                "Database: %s",
                self._extract_rich_text(db_meta.get("title", [])) or self.database_id,
            )
        except Exception as e:
            logger.warning("Could not fetch database metadata: %s", e)
        # Paginate entries
        while has_more and self._pages_fetched < self.max_pages:
            try:
                params: dict[str, Any] = {"database_id": self.database_id}
                if cursor:
                    params["start_cursor"] = cursor
                resp = client.databases.query(**params)
                has_more, cursor = resp.get("has_more", False), resp.get("next_cursor")
                for entry in resp.get("results", []):
                    if self._pages_fetched >= self.max_pages:
                        break
                    pd = self._process_database_entry(client, entry)
                    if pd:
                        pages.append(pd)
                        self._pages_fetched += 1
                    time.sleep(RATE_LIMIT_DELAY)
                logger.info("   Fetched %d entries...", self._pages_fetched)
            except APIResponseError as e:
                if e.status == 429:
                    time.sleep(10)
                    continue  # noqa: E702
                logger.error("Notion API error: %s", e)
                break  # noqa: E702
            except Exception as e:
                logger.error("Error querying database: %s", e)
                break  # noqa: E702
        return pages

    def _process_database_entry(self, client: Any, entry: dict[str, Any]) -> dict[str, Any] | None:
        """Process one database entry into a page dict."""
        try:
            page_id, url = entry["id"], entry.get("url", "")
            props = self._extract_properties(entry.get("properties", {}))
            title = props.get("Name", "") or props.get("Title", "") or "Untitled"
            if isinstance(title, list):
                title = ", ".join(str(t) for t in title) or "Untitled"
            content, headings, code_blocks = self._fetch_page_blocks(client, page_id)
            return {
                "id": page_id,
                "title": title,
                "url": url,
                "properties": props,
                "content": content,
                "headings": headings,
                "code_blocks": code_blocks,
                "parent_path": "",
            }
        except Exception as e:
            logger.warning("Failed to process entry %s: %s", entry.get("id", "?"), e)
            return None

    def _extract_properties(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Flatten Notion's raw property format into simple {name: value} pairs."""
        result: dict[str, Any] = {}
        for name, data in raw.items():
            try:
                val = self._extract_property_value(data.get("type", ""), data)
                if val is not None:
                    result[name] = val
            except Exception as e:
                logger.debug("Could not extract property '%s': %s", name, e)
        return result

    def _extract_property_value(self, ptype: str, data: dict[str, Any]) -> Any:
        """Extract a single property value by its Notion type."""
        if ptype == "title":
            return self._extract_rich_text(data.get("title", []))
        if ptype == "rich_text":
            return self._extract_rich_text(data.get("rich_text", []))
        if ptype == "number":
            return data.get("number")
        if ptype == "select":
            s = data.get("select")
            return s.get("name", "") if s else None
        if ptype == "multi_select":
            return [o.get("name", "") for o in data.get("multi_select", [])]
        if ptype == "date":
            d = data.get("date")
            return (
                (f"{d['start']} - {d['end']}" if d and d.get("end") else d.get("start"))
                if d
                else None
            )
        if ptype == "checkbox":
            return data.get("checkbox", False)
        if ptype in ("url", "email", "phone_number", "created_time", "last_edited_time"):
            return data.get(ptype)
        if ptype == "status":
            s = data.get("status")
            return s.get("name", "") if s else None
        if ptype == "relation":
            rels = data.get("relation", [])
            return [r.get("id", "") for r in rels] if rels else None
        if ptype == "people":
            return [p.get("name", "") for p in data.get("people", [])] or None
        if ptype == "files":
            return [fi.get("name", "") for fi in data.get("files", [])] or None
        if ptype in ("formula", "rollup"):
            inner = data.get(ptype, {})
            return inner.get(inner.get("type", ""))
        logger.debug("Unsupported property type: %s", ptype)
        return None

    # -- Page tree (recursive) -------------------------------------------

    def _extract_page_tree(
        self, client: Any, page_id: str, parent_path: str, depth: int = 0
    ) -> list[dict[str, Any]]:
        """Recursively extract a page and its child pages."""
        if self._pages_fetched >= self.max_pages:
            return []
        pages: list[dict[str, Any]] = []
        try:
            meta = client.pages.retrieve(page_id=page_id)
            props = self._extract_properties(meta.get("properties", {}))
            title = (
                props.get("title", "")
                or props.get("Name", "")
                or props.get("Title", "")
                or "Untitled"
            )
            if isinstance(title, list):
                title = ", ".join(str(t) for t in title) or "Untitled"
            current_path = f"{parent_path}/{title}" if parent_path else title
            content, headings, code_blocks = self._fetch_page_blocks(client, page_id)
            self._pages_fetched += 1
            pages.append(
                {
                    "id": page_id,
                    "title": title,
                    "url": meta.get("url", ""),
                    "properties": props,
                    "content": content,
                    "headings": headings,
                    "code_blocks": code_blocks,
                    "parent_path": parent_path,
                    "depth": depth,
                }
            )
            logger.info("   [%d] %s", self._pages_fetched, current_path)
            time.sleep(RATE_LIMIT_DELAY)
            if depth < MAX_BLOCK_DEPTH:
                for child_id in self._get_child_pages(client, page_id):
                    if self._pages_fetched >= self.max_pages:
                        break
                    pages.extend(self._extract_page_tree(client, child_id, current_path, depth + 1))
        except APIResponseError as e:
            if e.status == 429:
                time.sleep(10)
                return self._extract_page_tree(client, page_id, parent_path, depth)
            logger.warning("API error on page %s: %s", page_id, e)
        except Exception as e:
            logger.warning("Error extracting page %s: %s", page_id, e)
        return pages

    def _get_child_pages(self, client: Any, page_id: str) -> list[str]:
        """Get IDs of child_page / child_database blocks within a page."""
        ids: list[str] = []
        has_more, cursor = True, None
        while has_more:
            try:
                params: dict[str, Any] = {"block_id": page_id}
                if cursor:
                    params["start_cursor"] = cursor
                resp = client.blocks.children.list(**params)
                has_more, cursor = resp.get("has_more", False), resp.get("next_cursor")
                for b in resp.get("results", []):
                    if b.get("type") in ("child_page", "child_database"):
                        ids.append(b["id"])
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.debug("Error listing children of %s: %s", page_id, e)
                break  # noqa: E702
        return ids

    # -- Block parsing ---------------------------------------------------

    def _fetch_page_blocks(
        self, client: Any, page_id: str, depth: int = 0
    ) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
        """Fetch all blocks for a page and convert to markdown."""
        parts, headings, code_blocks = [], [], []
        has_more, cursor = True, None
        while has_more:
            try:
                params: dict[str, Any] = {"block_id": page_id}
                if cursor:
                    params["start_cursor"] = cursor
                resp = client.blocks.children.list(**params)
                has_more, cursor = resp.get("has_more", False), resp.get("next_cursor")
                for block in resp.get("results", []):
                    self._blocks_fetched += 1
                    md, bh, bc = self._parse_notion_blocks(client, block, depth)
                    if md:
                        parts.append(md)
                    headings.extend(bh)
                    code_blocks.extend(bc)
                time.sleep(RATE_LIMIT_DELAY)
            except APIResponseError as e:
                if e.status == 429:
                    time.sleep(10)
                    continue  # noqa: E702
                logger.debug("API error fetching blocks for %s: %s", page_id, e)
                break  # noqa: E702
            except Exception as e:
                logger.debug("Error fetching blocks for %s: %s", page_id, e)
                break  # noqa: E702
        return "\n\n".join(p for p in parts if p.strip()), headings, code_blocks

    def _parse_notion_blocks(
        self, client: Any, block: dict[str, Any], depth: int = 0
    ) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
        """Convert a Notion block to markdown, recursing into children."""
        btype = block.get("type", "")
        md, headings, code_blocks = self._handle_block_type(btype, block)
        if block.get("has_children") and depth < MAX_BLOCK_DEPTH:
            child_md, ch, cc = self._fetch_page_blocks(client, block["id"], depth + 1)
            if child_md:
                if btype in ("toggle", "callout"):
                    indented = "\n".join(f"  {l}" for l in child_md.split("\n"))  # noqa: E741
                    md = f"{md}\n{indented}" if md else indented
                else:
                    md = f"{md}\n\n{child_md}" if md else child_md
            headings.extend(ch)
            code_blocks.extend(cc)
        return md, headings, code_blocks

    def _handle_block_type(
        self, btype: str, block: dict[str, Any]
    ) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
        """Handle a Notion block type: paragraph, heading, code, callout, toggle, table, etc."""
        headings: list[dict[str, str]] = []
        code_blocks: list[dict[str, str]] = []
        data = block.get(btype, {})
        md = ""

        if btype == "paragraph":
            md = self._extract_rich_text(data.get("rich_text", []))
        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            text = self._extract_rich_text(data.get("rich_text", []))
            md = f"{'#' * level} {text}"
            if text:
                headings.append({"level": f"h{level}", "text": text})
        elif btype == "code":
            lang = data.get("language", "plain text") or "plain text"
            code_text = self._extract_rich_text(data.get("rich_text", []))
            caption = self._extract_rich_text(data.get("caption", []))
            md = f"```{lang}\n{code_text}\n```"
            if code_text.strip():
                code_blocks.append({"language": lang, "code": code_text, "caption": caption})
        elif btype == "callout":
            icon = data.get("icon", {})
            emoji = icon.get("emoji", "") if icon else ""
            text = self._extract_rich_text(data.get("rich_text", []))
            md = f"> {emoji} **Callout:** {text}" if emoji else f"> **Callout:** {text}"
        elif btype == "toggle":
            md = f"<details>\n<summary>{self._extract_rich_text(data.get('rich_text', []))}</summary>"
        elif btype == "quote":
            md = f"> {self._extract_rich_text(data.get('rich_text', []))}"
        elif btype == "bulleted_list_item":
            md = f"- {self._extract_rich_text(data.get('rich_text', []))}"
        elif btype == "numbered_list_item":
            md = f"1. {self._extract_rich_text(data.get('rich_text', []))}"
        elif btype == "to_do":
            text = self._extract_rich_text(data.get("rich_text", []))
            md = f"- [{'x' if data.get('checked') else ' '}] {text}"
        elif btype == "divider":
            md = "---"
        elif btype == "table":
            md = self._handle_table_block(block)
        elif btype == "image":
            itype = data.get("type", "")
            url = data.get(itype, {}).get("url", "") if itype in ("external", "file") else ""
            cap = self._extract_rich_text(data.get("caption", []))
            md = f"![{cap or 'Image'}]({url})" if url else ""
        elif btype in ("bookmark", "embed", "link_preview"):
            url = data.get("url", "")
            cap = (
                self._extract_rich_text(data.get("caption", [])) if btype != "link_preview" else ""
            )
            md = f"[{cap or url}]({url})" if url else ""
        elif btype == "equation":
            expr = data.get("expression", "")
            md = f"$$\n{expr}\n$$" if expr else ""
        elif btype in ("child_page", "child_database"):
            md = f"**Sub-{btype.split('_')[1]}: {data.get('title', '')}**"
        elif btype in ("pdf", "video", "audio", "file"):
            ftype = data.get("type", "")
            url = data.get(ftype, {}).get("url", "") if ftype in ("external", "file") else ""
            md = f"[{btype.title()}]({url})" if url else ""
        elif btype == "link_to_page":
            lt = data.get("type", "")
            md = f"*[Link to page: {data.get(lt, '')}]*" if data.get(lt) else ""
        elif btype in (
            "column_list",
            "column",
            "synced_block",
            "template",
            "table_of_contents",
            "breadcrumb",
        ):
            md = "*[Table of Contents]*" if btype == "table_of_contents" else ""
        else:
            logger.debug("Unhandled block type: %s", btype)

        return md, headings, code_blocks

    def _handle_table_block(self, block: dict[str, Any]) -> str:
        """Convert a Notion table block into a markdown table."""
        tdata = block.get("table", {})
        has_header = tdata.get("has_column_header", False)
        rows = block.get("_table_rows", [])
        if not rows:
            return f"*[Table: {tdata.get('table_width', 0)} columns]*"
        lines = []
        for i, row in enumerate(rows):
            cells = [self._extract_rich_text(c) for c in row.get("cells", [])]
            lines.append("| " + " | ".join(cells) + " |")
            if i == 0 and has_header:
                lines.append("| " + " | ".join("---" for _ in cells) + " |")
        return "\n".join(lines)

    # -- Rich text -------------------------------------------------------

    def _extract_rich_text(self, rich_text_list: list[dict[str, Any]]) -> str:
        """Extract text with annotations (bold, italic, code, links) from Notion rich text."""
        if not rich_text_list:
            return ""
        parts = []
        for obj in rich_text_list:
            text = obj.get("plain_text", "")
            if not text:
                continue
            ann = obj.get("annotations", {})
            if ann.get("code"):
                text = f"`{text}`"
            if ann.get("bold"):
                text = f"**{text}**"
            if ann.get("italic"):
                text = f"*{text}*"
            if ann.get("strikethrough"):
                text = f"~~{text}~~"
            if ann.get("underline"):
                text = f"<u>{text}</u>"
            if obj.get("href"):
                text = f"[{text}]({obj['href']})"
            parts.append(text)
        return "".join(parts)

    # ====================================================================
    # EXPORT MODE
    # ====================================================================

    def _extract_from_export(self) -> list[dict[str, Any]]:
        """Parse a Notion Markdown/CSV export directory."""
        if not self.export_path:
            raise ValueError("export_path is required for export mode.")
        export_dir = Path(self.export_path)
        if not export_dir.exists():
            raise FileNotFoundError(f"Export directory not found: {self.export_path}")
        if not export_dir.is_dir():
            raise ValueError(f"Export path is not a directory: {self.export_path}")
        print(f"   Parsing Notion export: {self.export_path}")
        pages: list[dict[str, Any]] = []
        for root, _dirs, files in os.walk(export_dir):
            rel = str(Path(root).relative_to(export_dir))
            parent = "" if rel == "." else rel
            for fn in sorted(files):
                if self._pages_fetched >= self.max_pages:
                    break
                fp = Path(root) / fn
                if fp.suffix.lower() == ".md":
                    pd = self._parse_export_markdown(fp, parent)
                    if pd:
                        pages.append(pd)
                        self._pages_fetched += 1  # noqa: E702
                elif fp.suffix.lower() == ".csv":
                    for pd in self._parse_export_csv(fp, parent):
                        if self._pages_fetched >= self.max_pages:
                            break
                        pages.append(pd)
                        self._pages_fetched += 1  # noqa: E702
            if self._pages_fetched >= self.max_pages:
                break
        print(f"   Parsed {len(pages)} files from export directory")
        return pages

    def _parse_export_markdown(self, filepath: Path, parent_path: str) -> dict[str, Any] | None:
        """Parse a single .md file from a Notion export."""
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning("Could not read %s: %s", filepath, e)
            return None  # noqa: E702
        if not content.strip():
            return None
        lines = content.split("\n")
        title = self._clean_notion_export_title(filepath.stem)
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break  # noqa: E702
        headings = [
            {"level": f"h{len(m.group(1))}", "text": m.group(2).strip()}
            for line in lines
            if (m := re.match(r"^(#{2,6})\s+(.+)$", line))
        ]
        code_blocks = [
            {"language": lang or "plain text", "code": code.strip(), "caption": ""}
            for lang, code in re.findall(r"```(\w*)\n(.*?)```", content, re.DOTALL)
            if code.strip()
        ]
        self._blocks_fetched += len(lines) + len(code_blocks)
        body = re.sub(r"```\w*\n.*?```", "", content, flags=re.DOTALL)
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()
        return {
            "id": str(filepath),
            "title": title,
            "url": "",
            "properties": {},
            "content": body,
            "headings": headings,
            "code_blocks": code_blocks,
            "parent_path": parent_path,
        }

    def _parse_export_csv(self, filepath: Path, parent_path: str) -> list[dict[str, Any]]:
        """Parse a CSV file from a Notion database export (one page per row)."""
        pages: list[dict[str, Any]] = []
        try:
            with open(filepath, encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return pages
                title_col = reader.fieldnames[0]
                for i, row in enumerate(reader):
                    title = row.get(title_col, f"Row {i + 1}") or f"Row {i + 1}"
                    props = {k: v for k, v in row.items() if k and v}
                    body = "\n\n".join(
                        f"**{k}:** {v}"
                        for k, v in row.items()
                        if k and v and k != title_col and len(str(v)) > 10
                    )
                    pages.append(
                        {
                            "id": f"{filepath}:row:{i}",
                            "title": title,
                            "url": "",
                            "properties": props,
                            "content": body,
                            "headings": [],
                            "code_blocks": [],
                            "parent_path": parent_path,
                        }
                    )
                    self._blocks_fetched += 1
        except Exception as e:
            logger.warning("Could not parse CSV %s: %s", filepath, e)
        return pages

    @staticmethod
    def _clean_notion_export_title(stem: str) -> str:
        """Strip trailing Notion hex IDs from export filenames."""
        cleaned = re.sub(r"\s+[0-9a-f]{16,}$", "", stem)
        return cleaned.strip() or stem


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for the Notion scraper."""
    from .arguments.common import add_all_standard_arguments

    parser = argparse.ArgumentParser(
        description="Convert Notion workspace content to AI-ready skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  skill-seekers notion --database-id ID --token $NOTION_TOKEN --name myskill\n"
            "  skill-seekers notion --page-id ID --token $NOTION_TOKEN --name myskill\n"
            "  skill-seekers notion --export-path ./export/ --name myskill\n"
            "  skill-seekers notion --from-json output/myskill_notion_data.json --name myskill"
        ),
    )
    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for Notion
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0

    # Notion-specific arguments
    parser.add_argument(
        "--database-id", type=str, help="Notion database ID (API mode)", metavar="ID"
    )
    parser.add_argument(
        "--page-id", type=str, help="Notion page ID (API mode, recursive)", metavar="ID"
    )
    parser.add_argument(
        "--export-path", type=str, help="Notion export directory (export mode)", metavar="PATH"
    )
    parser.add_argument(
        "--token", type=str, help="Notion integration token (or NOTION_TOKEN env)", metavar="TOKEN"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum pages to extract (default: {DEFAULT_MAX_PAGES})",
        metavar="N",
    )
    parser.add_argument(
        "--from-json", type=str, help="Build from previously extracted JSON", metavar="FILE"
    )

    args = parser.parse_args()

    # Logging
    level = (
        logging.WARNING
        if getattr(args, "quiet", False)
        else (logging.DEBUG if getattr(args, "verbose", False) else logging.INFO)
    )
    logging.basicConfig(level=level, format="%(message)s", force=True)

    # Dry run
    if getattr(args, "dry_run", False):
        source = (
            getattr(args, "database_id", None)
            or getattr(args, "page_id", None)
            or getattr(args, "export_path", None)
            or getattr(args, "from_json", None)
            or "(none)"
        )
        print(f"\n{'=' * 60}\nDRY RUN: Notion Extraction\n{'=' * 60}")
        print(
            f"Source: {source}\nName: {getattr(args, 'name', None) or '(auto)'}\nMax pages: {args.max_pages}"
        )
        return 0

    # Validate
    has_source = any(
        getattr(args, a, None) for a in ("database_id", "page_id", "export_path", "from_json")
    )
    if not has_source:
        parser.error("Must specify --database-id, --page-id, --export-path, or --from-json")
    if not getattr(args, "name", None):
        if getattr(args, "from_json", None):
            args.name = Path(args.from_json).stem.replace("_notion_data", "")
        elif getattr(args, "export_path", None):
            args.name = Path(args.export_path).stem
        else:
            parser.error("--name is required when using --database-id or --page-id")

    # --from-json: build only
    if getattr(args, "from_json", None):
        config = {
            "name": args.name,
            "description": getattr(args, "description", None),
            "max_pages": args.max_pages,
        }
        try:
            conv = NotionToSkillConverter(config)
            conv.load_extracted_data(args.from_json)
            conv.build_skill()
        except Exception as e:
            print(f"\n   Error: {e}", file=sys.stderr)
            sys.exit(1)  # noqa: E702
        return 0

    # Full extract + build
    config: dict[str, Any] = {
        "name": args.name,
        "database_id": getattr(args, "database_id", None),
        "page_id": getattr(args, "page_id", None),
        "export_path": getattr(args, "export_path", None),
        "token": getattr(args, "token", None),
        "description": getattr(args, "description", None),
        "max_pages": args.max_pages,
    }
    try:
        conv = NotionToSkillConverter(config)
        if not conv.extract_notion():
            print("\n   Notion extraction failed", file=sys.stderr)
            sys.exit(1)  # noqa: E702
        conv.build_skill()

        # Run enhancement workflows if specified
        try:
            from skill_seekers.cli.workflow_runner import run_workflows

            run_workflows(args)
        except (ImportError, AttributeError):
            pass

        # Traditional AI enhancement
        if getattr(args, "enhance_level", 0) > 0:
            api_key = getattr(args, "api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
            skill_dir = conv.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                except ImportError:
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    LocalSkillEnhancer(Path(skill_dir)).run(headless=True)
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                LocalSkillEnhancer(Path(skill_dir)).run(headless=True)
    except RuntimeError as e:
        print(f"\n   Error: {e}", file=sys.stderr)
        sys.exit(1)  # noqa: E702
    except Exception as e:
        print(f"\n   Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)  # noqa: E702
    return 0


if __name__ == "__main__":
    sys.exit(main())
