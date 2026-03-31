#!/usr/bin/env python3
"""
Man Page to Skill Converter

Converts Unix/Linux man pages into AI-ready skills.  No external dependencies
are required beyond the Python standard library -- extraction relies on
``subprocess`` (to invoke ``man``) and ``re`` (to strip troff/groff formatting).

Three extraction strategies are supported:

1. **Live man command** -- run ``man <name>`` and capture stdout.
2. **Directory scan** -- read ``.1`` -- ``.8`` / ``.man`` files directly from
   a directory (useful when man pages are not installed system-wide).
3. **Pre-extracted JSON** -- reload a previously saved intermediate JSON file
   and jump straight to the skill-building phase.

Usage:
    skill-seekers man --man-names git,curl --name unix-tools
    skill-seekers man --man-path /usr/share/man/man1 --name coreutils
    skill-seekers man --from-json unix-tools_extracted.json
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Standard man page section names (used for parsing)
# ---------------------------------------------------------------------------
STANDARD_SECTIONS = [
    "NAME",
    "SYNOPSIS",
    "DESCRIPTION",
    "OPTIONS",
    "ARGUMENTS",
    "COMMANDS",
    "SUBCOMMANDS",
    "ENVIRONMENT",
    "ENVIRONMENT VARIABLES",
    "EXIT STATUS",
    "EXIT CODES",
    "RETURN VALUE",
    "RETURN VALUES",
    "ERRORS",
    "FILES",
    "EXAMPLES",
    "EXAMPLE",
    "DIAGNOSTICS",
    "COMPATIBILITY",
    "STANDARDS",
    "CONFORMING TO",
    "NOTES",
    "CAVEATS",
    "BUGS",
    "HISTORY",
    "AUTHORS",
    "AUTHOR",
    "COPYRIGHT",
    "LICENSE",
    "SEE ALSO",
    "REPORTING BUGS",
    "SECURITY CONSIDERATIONS",
    "CONFIGURATION",
    "DEFAULTS",
    "GIT",
]

# Man page manual section numbers
MAN_SECTION_NUMBERS = list(range(1, 9))  # 1-8

# File extensions recognised as man pages
MAN_FILE_EXTENSIONS = {f".{n}" for n in MAN_SECTION_NUMBERS} | {".man", ".1p", ".3p"}


def infer_description_from_manpages(
    names: list[str] | None = None,
    name_lines: list[str] | None = None,
    skill_name: str = "",
) -> str:
    """Infer skill description from man page NAME lines or page names.

    Args:
        names: List of man page names (e.g. ["git", "curl"]).
        name_lines: NAME section lines extracted from man pages.
        skill_name: Skill name for fallback.

    Returns:
        Description string suitable for "Use when..." format.
    """
    if name_lines:
        # NAME lines typically have the form: "command - short description"
        for line in name_lines:
            if " - " in line:
                desc = line.split(" - ", 1)[1].strip()
                if len(desc) > 20:
                    if len(desc) > 150:
                        desc = desc[:147] + "..."
                    return f"Use when {desc.lower()}"

    if names:
        joined = ", ".join(names[:5])
        suffix = f" (and {len(names) - 5} more)" if len(names) > 5 else ""
        return f"Use when referencing {joined}{suffix} command documentation"

    return (
        f"Use when referencing {skill_name} documentation"
        if skill_name
        else "Use when referencing this documentation"
    )


class ManPageToSkillConverter:
    """Convert Unix man pages into a skill directory structure.

    Supports extraction via the ``man`` command or by reading raw man-page
    files from a directory.  Parsed content is saved as an intermediate JSON
    file so that the (potentially slow) extraction step can be decoupled
    from skill generation.
    """

    def __init__(self, config: dict) -> None:
        """Initialise the converter from a configuration dictionary.

        Args:
            config: Dictionary with keys:
                - ``name``       -- skill name (required)
                - ``man_names``  -- list of man page names, e.g. ``["git", "curl"]``
                - ``man_path``   -- directory containing raw man page files
                - ``sections``   -- man section numbers to query (default all)
                - ``description``-- explicit description (optional)
                - ``categories`` -- keyword-based categorisation map (optional)
        """
        self.config = config
        self.name: str = config["name"]
        self.man_names: list[str] = config.get("man_names", [])
        self.man_path: str = config.get("man_path", "")
        self.sections: list[int] = config.get("sections", [])
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} documentation"
        )

        # Paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Categories config
        self.categories: dict = config.get("categories", {})

        # Extracted data placeholder
        self.extracted_data: dict | None = None

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_manpages(self) -> bool:
        """Extract man pages via ``man`` command or by reading files from a directory.

        Workflow:
        1. If ``man_path`` is set, read ``.1``-``.8`` / ``.man`` files from
           that directory.
        2. Otherwise, run ``man <name>`` for each entry in ``man_names``.
        3. Strip troff/groff formatting from every captured page.
        4. Parse each page into structured sections (NAME, SYNOPSIS, ...).
        5. Persist the intermediate JSON to ``self.data_file``.

        Returns:
            ``True`` on success.

        Raises:
            FileNotFoundError: If ``man_path`` does not exist.
            RuntimeError: If no man pages could be extracted.
        """
        print(f"\n🔍 Extracting man pages for skill: {self.name}")

        pages: list[dict] = []

        if self.man_path:
            pages = self._extract_from_directory(self.man_path)
        elif self.man_names:
            pages = self._extract_from_names(self.man_names)
        else:
            raise RuntimeError("No man page source specified.  Provide --man-names or --man-path.")

        if not pages:
            raise RuntimeError("No man pages could be extracted.  Check names or path.")

        # Collect NAME lines for description inference
        name_lines: list[str] = []
        for page in pages:
            name_section = page.get("sections", {}).get("NAME", "")
            if name_section:
                name_lines.append(name_section.strip())

        # Update description from man page content if not set explicitly
        if not self.config.get("description"):
            self.description = infer_description_from_manpages(
                names=self.man_names or None,
                name_lines=name_lines or None,
                skill_name=self.name,
            )

        # Build result data
        total_options = sum(len(p.get("options", [])) for p in pages)
        total_examples = sum(len(p.get("examples", [])) for p in pages)
        see_also_all: list[str] = []
        for page in pages:
            see_also_all.extend(page.get("see_also", []))

        result_data = {
            "source": self.man_path or "man command",
            "total_pages": len(pages),
            "total_options": total_options,
            "total_examples": total_examples,
            "see_also": sorted(set(see_also_all)),
            "pages": pages,
        }

        # Save extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {len(pages)} man page(s), "
            f"{total_options} options, "
            f"{total_examples} examples"
        )
        return True

    def _extract_from_names(self, names: list[str]) -> list[dict]:
        """Run ``man <name>`` for each name and parse output.

        When ``self.sections`` is set, the specific section number is passed to
        ``man`` (e.g. ``man 3 printf``).  Otherwise, the default section is used.

        Args:
            names: Man page names to look up.

        Returns:
            List of parsed page dicts.
        """
        pages: list[dict] = []
        section_targets: list[int] = self.sections or [0]  # 0 = default

        for man_name in names:
            for section_num in section_targets:
                raw = self._run_man_command(man_name, section_num or None)
                if raw is None:
                    continue
                clean = self._strip_troff_formatting(raw)
                parsed = self._parse_man_output(clean, man_name, section_num or None)
                pages.append(parsed)
                section_label = f"({section_num})" if section_num else ""
                print(f"   Extracted: {man_name}{section_label}")
        return pages

    def _extract_from_directory(self, dir_path: str) -> list[dict]:
        """Read man page files from a directory and parse them.

        Recognised extensions: ``.1`` -- ``.8``, ``.1p``, ``.3p``, ``.man``.
        Compressed files (``.gz``, ``.bz2``, ``.xz``) are also handled.

        Args:
            dir_path: Path to the directory containing man page files.

        Returns:
            List of parsed page dicts.

        Raises:
            FileNotFoundError: If ``dir_path`` does not exist.
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Man page directory not found: {dir_path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        print(f"   Scanning directory: {dir_path}")

        pages: list[dict] = []
        man_files = sorted(path.iterdir())

        for fp in man_files:
            if fp.is_dir():
                # Recurse into subdirectories (man1/, man2/, ...)
                sub_pages = self._extract_from_directory(str(fp))
                pages.extend(sub_pages)
                continue

            # Check for compressed man pages
            real_suffix = fp.suffix
            actual_path = fp
            if real_suffix in (".gz", ".bz2", ".xz"):
                real_suffix = fp.with_suffix("").suffix
                actual_path = fp

            if real_suffix not in MAN_FILE_EXTENSIONS:
                continue

            # Filter by requested sections
            section_num = self._section_from_suffix(real_suffix)
            if self.sections and section_num not in self.sections:
                continue

            raw = self._read_man_file(str(actual_path))
            if raw is None:
                continue

            clean = self._strip_troff_formatting(raw)
            man_name = fp.stem
            # Remove double-suffix for compressed files (e.g. git.1.gz -> git)
            if fp.suffix in (".gz", ".bz2", ".xz"):
                man_name = Path(man_name).stem

            parsed = self._parse_man_output(clean, man_name, section_num)
            pages.append(parsed)
            print(f"   Read file: {fp.name}")

        return pages

    @staticmethod
    def _section_from_suffix(suffix: str) -> int | None:
        """Derive the man section number from a file suffix.

        Args:
            suffix: File extension, e.g. ``.1``, ``.3p``, ``.man``.

        Returns:
            Integer section number or ``None`` if not determinable.
        """
        suffix = suffix.lstrip(".")
        # Handle POSIX extensions like 1p, 3p
        numeric = re.match(r"^(\d)", suffix)
        if numeric:
            return int(numeric.group(1))
        return None

    # ------------------------------------------------------------------
    # Man command execution
    # ------------------------------------------------------------------

    def _run_man_command(self, name: str, section: int | None = None) -> str | None:
        """Execute ``man`` and capture its output.

        Uses ``MANWIDTH=999`` to avoid unwanted line wrapping and ``col -bx``
        to strip backspace-based formatting on platforms that still use it.

        Args:
            name: Man page name (e.g. ``"git"``).
            section: Optional manual section number.

        Returns:
            Raw text output, or ``None`` on failure.
        """
        cmd: list[str] = ["man"]
        if section:
            cmd.append(str(section))
        cmd.append(name)

        env = os.environ.copy()
        # Wide output avoids mid-word breaks
        env["MANWIDTH"] = "999"
        # Force plain-text rendering (no colour escapes on some systems)
        env["MAN_KEEP_FORMATTING"] = "0"
        env["COLUMNS"] = "999"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
            if result.returncode != 0:
                section_label = f"({section}) " if section else ""
                logger.debug(
                    "man %s%s returned exit code %d: %s",
                    section_label,
                    name,
                    result.returncode,
                    result.stderr.strip(),
                )
                return None

            output = result.stdout
            if not output.strip():
                return None

            # Pipe through ``col -bx`` to strip backspace overstriking
            try:
                col_result = subprocess.run(
                    ["col", "-bx"],
                    input=output,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if col_result.returncode == 0 and col_result.stdout.strip():
                    output = col_result.stdout
            except FileNotFoundError:
                # ``col`` not available -- fall back to manual backspace removal
                output = re.sub(r".\x08", "", output)

            return output

        except FileNotFoundError:
            logger.warning("'man' command not found -- is it installed?")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("man %s timed out after 30 s", name)
            return None
        except OSError as exc:
            logger.warning("Error running man %s: %s", name, exc)
            return None

    # ------------------------------------------------------------------
    # File reading
    # ------------------------------------------------------------------

    def _read_man_file(self, filepath: str) -> str | None:
        """Read a man page file, handling optional compression.

        Supports ``.gz``, ``.bz2``, and ``.xz`` compressed files as well as
        plain text.

        Args:
            filepath: Absolute or relative path to the file.

        Returns:
            Raw file content as a string, or ``None`` on failure.
        """
        path = Path(filepath)

        try:
            if path.suffix == ".gz":
                import gzip

                with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                    return f.read()
            elif path.suffix == ".bz2":
                import bz2

                with bz2.open(path, "rt", encoding="utf-8", errors="replace") as f:
                    return f.read()
            elif path.suffix == ".xz":
                import lzma

                with lzma.open(path, "rt", encoding="utf-8", errors="replace") as f:
                    return f.read()
            else:
                with open(path, encoding="utf-8", errors="replace") as f:
                    return f.read()
        except OSError as exc:
            logger.warning("Could not read %s: %s", filepath, exc)
            return None

    # ------------------------------------------------------------------
    # Troff/groff stripping
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_troff_formatting(text: str) -> str:
        """Remove troff/groff formatting codes from raw man page text.

        This handles:
        - Backspace-based bold/underline overstriking (e.g. ``X\\bX``).
        - ANSI escape sequences.
        - Common roff macros (``.TH``, ``.SH``, ``.TP``, ``.PP``, etc.).
        - Inline font switching (``\\fB``, ``\\fI``, ``\\fR``, ``\\fP``).
        - Roff special characters (``\\-``, ``\\(aq``, ``\\(lq``, etc.).
        - Comment lines starting with ``.\\"`` or ``'\\"``.

        The goal is to produce clean, readable plain text suitable for
        further section parsing.

        Args:
            text: Raw text potentially containing troff formatting.

        Returns:
            Cleaned plain-text string.
        """
        # Remove ANSI escape sequences
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        text = re.sub(r"\x1b\([AB012]", "", text)

        # Remove backspace overstriking (bold: X\bX, underline: _\bX)
        text = re.sub(r".\x08", "", text)

        # Remove troff comment lines
        text = re.sub(r'^[.\']\\?".*$', "", text, flags=re.MULTILINE)
        text = re.sub(r"^\.\\\s*.*$", "", text, flags=re.MULTILINE)

        # Remove common roff macros at line start
        # We keep .SH content as it becomes section headers
        macro_pattern = re.compile(
            r"^\.\s*(?:TH|PP|LP|IP|TP|HP|RS|RE|br|sp|ne|nf|fi|na|ad|in|ti|nh|hy|PD|IX"
            r"|de|ft|nr|ds|rm|rn|if|ie|el|so|mso|am|ig)\b.*$",
            re.MULTILINE,
        )
        text = macro_pattern.sub("", text)

        # Convert .SH "SECTION" or .SH SECTION to plain section header
        text = re.sub(
            r'^\.\s*SH\s+"?([^"]*?)"?\s*$',
            r"\1",
            text,
            flags=re.MULTILINE,
        )
        # Convert .SS subsection headers similarly
        text = re.sub(
            r'^\.\s*SS\s+"?([^"]*?)"?\s*$',
            r"  \1",
            text,
            flags=re.MULTILINE,
        )

        # Remove .B / .I / .BI / .BR / .IR / .RB / .RI inline macros
        # Keep their text arguments
        text = re.sub(
            r"^\.\s*(?:B|I|BI|BR|IR|RB|RI|SB|SM)\s+(.*)$",
            r"\1",
            text,
            flags=re.MULTILINE,
        )

        # Remove inline font escapes (\fB, \fI, \fR, \fP, \f[...])
        text = re.sub(r"\\f[BIRP1234]", "", text)
        text = re.sub(r"\\f\[[^\]]*\]", "", text)

        # Remove other inline troff escapes
        text = re.sub(r"\\[*$]([({][^)}]+[)}]|\S)", "", text)

        # Convert troff special characters to plain equivalents
        replacements = {
            r"\-": "-",
            r"\(aq": "'",
            r"\(lq": '"',
            r"\(rq": '"',
            r"\(dq": '"',
            r"\(bu": "*",
            r"\(em": "--",
            r"\(en": "-",
            r"\(co": "(c)",
            r"\(rg": "(R)",
            r"\(tm": "(TM)",
            r"\&": "",
            r"\e": "\\",
            r"\|": "",
            r"\^": "",
            r"\~": " ",
            r"\ ": " ",
            r"\0": " ",
        }
        for troff_seq, replacement in replacements.items():
            text = text.replace(troff_seq, replacement)

        # Remove remaining backslash escapes
        text = re.sub(r"\\[(\[][a-zA-Z]{2,4}[\])]", "", text)

        # Strip stray roff size/motion escapes  \s[+-]N, \v'...', \h'...'
        text = re.sub(r"\\s[+-]?\d+", "", text)
        text = re.sub(r"\\[vh]'[^']*'", "", text)

        # Collapse multiple blank lines into at most two
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_man_output(
        self,
        text: str,
        man_name: str,
        section_num: int | None = None,
    ) -> dict:
        """Parse cleaned man page text into structured sections.

        Identifies standard man page sections (NAME, SYNOPSIS, DESCRIPTION,
        OPTIONS, EXAMPLES, SEE ALSO, etc.) by looking for lines that match
        known section headers at the start of a line with no leading
        whitespace.

        Args:
            text: Cleaned man page text (troff already stripped).
            man_name: Name of the man page.
            section_num: Manual section number (1-8) if known.

        Returns:
            Structured dict with ``name``, ``section``, ``sections``,
            ``options``, ``examples``, ``see_also``, and ``raw_text`` keys.
        """
        # Build a pattern that matches known section headings at line start
        known_uppers = [s.upper() for s in STANDARD_SECTIONS]

        sections: dict[str, str] = {}
        current_section: str | None = None
        current_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            # Check if this line is a section header
            upper_stripped = stripped.upper()
            if upper_stripped in known_uppers and not line.startswith(" "):
                # Flush previous section
                if current_section is not None:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = stripped.upper()
                current_lines = []
            else:
                current_lines.append(line)

        # Flush last section
        if current_section is not None:
            sections[current_section] = "\n".join(current_lines).strip()

        # Extract structured parts
        options = self._extract_options(sections.get("OPTIONS", ""))
        examples = self._extract_examples(sections.get("EXAMPLES", sections.get("EXAMPLE", "")))
        see_also = self._extract_see_also(sections.get("SEE ALSO", ""))

        # Build synopsis
        synopsis = sections.get("SYNOPSIS", "").strip()
        description_text = sections.get("DESCRIPTION", "").strip()

        return {
            "name": man_name,
            "section": section_num,
            "title": sections.get("NAME", man_name).strip(),
            "synopsis": synopsis,
            "description": description_text[:2000]
            if len(description_text) > 2000
            else description_text,
            "sections": sections,
            "options": options,
            "examples": examples,
            "see_also": see_also,
            "raw_text": text,
        }

    def _extract_options(self, options_text: str) -> list[dict]:
        """Parse the OPTIONS section into a list of flag/description dicts.

        Handles common option formats:
        - ``-f, --flag``
        - ``-f value``
        - ``--long-option=VALUE``

        Args:
            options_text: Raw text of the OPTIONS section.

        Returns:
            List of dicts with ``flag`` and ``description`` keys.
        """
        if not options_text.strip():
            return []

        options: list[dict] = []
        # Pattern for option lines: starts with optional whitespace then a dash
        option_re = re.compile(
            r"^\s{0,7}(-[\w](?:[\w-]*)?(?:\s*,\s*--[\w][\w-]*(?:=\S+)?)?|"
            r"--[\w][\w-]*(?:=\S+)?)"
            r"(?:\s+(.*))?$"
        )

        current_flag: str | None = None
        current_desc_lines: list[str] = []

        for line in options_text.splitlines():
            match = option_re.match(line)
            if match:
                # Flush previous option
                if current_flag is not None:
                    options.append(
                        {
                            "flag": current_flag.strip(),
                            "description": " ".join(current_desc_lines).strip(),
                        }
                    )
                current_flag = match.group(1)
                desc_part = match.group(2) or ""
                current_desc_lines = [desc_part] if desc_part else []
            elif current_flag is not None:
                # Continuation line for current option description
                stripped = line.strip()
                if stripped:
                    current_desc_lines.append(stripped)

        # Flush last option
        if current_flag is not None:
            options.append(
                {
                    "flag": current_flag.strip(),
                    "description": " ".join(current_desc_lines).strip(),
                }
            )

        return options

    def _extract_examples(self, examples_text: str) -> list[dict]:
        """Parse the EXAMPLES section into structured example blocks.

        Looks for lines that appear to be commands (starting with ``$``,
        ``#``, ``%``, or common command prefixes) versus descriptive prose.

        Args:
            examples_text: Raw text of the EXAMPLES (or EXAMPLE) section.

        Returns:
            List of dicts with ``description`` and ``command`` keys.
        """
        if not examples_text.strip():
            return []

        examples: list[dict] = []
        current_desc_lines: list[str] = []
        current_cmd_lines: list[str] = []

        # Patterns that indicate a command line
        cmd_prefixes = re.compile(r"^\s{2,}[\$#%>]?\s*\S")
        # A line that is indented and looks like code
        code_indent = re.compile(r"^\s{4,}\S")

        for line in examples_text.splitlines():
            stripped = line.strip()
            if not stripped:
                # Blank line: flush if we have a command accumulated
                if current_cmd_lines:
                    examples.append(
                        {
                            "description": " ".join(current_desc_lines).strip(),
                            "command": "\n".join(current_cmd_lines).strip(),
                        }
                    )
                    current_desc_lines = []
                    current_cmd_lines = []
                continue

            if cmd_prefixes.match(line) or code_indent.match(line):
                current_cmd_lines.append(stripped)
            else:
                if current_cmd_lines:
                    # New prose after a command block -> flush
                    examples.append(
                        {
                            "description": " ".join(current_desc_lines).strip(),
                            "command": "\n".join(current_cmd_lines).strip(),
                        }
                    )
                    current_desc_lines = []
                    current_cmd_lines = []
                current_desc_lines.append(stripped)

        # Flush remaining
        if current_cmd_lines:
            examples.append(
                {
                    "description": " ".join(current_desc_lines).strip(),
                    "command": "\n".join(current_cmd_lines).strip(),
                }
            )
        elif current_desc_lines:
            # Trailing prose with no command -- still record it
            examples.append(
                {
                    "description": " ".join(current_desc_lines).strip(),
                    "command": "",
                }
            )

        return examples

    def _extract_see_also(self, see_also_text: str) -> list[str]:
        """Parse the SEE ALSO section into a list of referenced page names.

        Typical format: ``git-log(1), git-diff(1), gitk(1)``

        Args:
            see_also_text: Raw text of the SEE ALSO section.

        Returns:
            Sorted de-duplicated list of referenced page names.
        """
        if not see_also_text.strip():
            return []

        # Match patterns like "name(N)" where N is a digit
        refs = re.findall(r"([\w.+-]+)\s*\(\d+\)", see_also_text)
        # Also capture plain references (just names separated by commas)
        if not refs:
            refs = [r.strip() for r in re.split(r"[,\n]", see_also_text) if r.strip()]

        return sorted(set(refs))

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from JSON.

        Args:
            json_path: Path to the intermediate JSON file.

        Returns:
            ``True`` on success.
        """
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_pages", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} man page(s)")
        return True

    # ------------------------------------------------------------------
    # Categorisation
    # ------------------------------------------------------------------

    def categorize_content(self) -> dict[str, dict]:
        """Categorise man pages based on name prefixes, sections, or keywords.

        Man pages are grouped by a common prefix (e.g. ``git-*`` pages all go
        under a ``git`` category) or by their manual section number.  When
        explicit ``self.categories`` are provided, keyword matching is used
        instead.

        Returns:
            Dict mapping category keys to ``{"title": ..., "pages": [...]}``
            dicts.
        """
        print("\n📋 Categorizing content...")

        categorized: dict[str, dict] = {}
        pages = self.extracted_data.get("pages", [])

        # If explicit categories are provided, use keyword matching
        if self.categories:
            first_value = next(iter(self.categories.values()), None)
            if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
                for cat_key, cat_pages in self.categories.items():
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": cat_pages,
                    }
            else:
                for cat_key in self.categories:
                    categorized[cat_key] = {
                        "title": cat_key.replace("_", " ").title(),
                        "pages": [],
                    }
                for page in pages:
                    text = page.get("description", "").lower()
                    title = page.get("title", "").lower()
                    scores: dict[str, int] = {}
                    for cat_key, keywords in self.categories.items():
                        if isinstance(keywords, list):
                            score = sum(
                                1
                                for kw in keywords
                                if isinstance(kw, str)
                                and (kw.lower() in text or kw.lower() in title)
                            )
                        else:
                            score = 0
                        if score > 0:
                            scores[cat_key] = score
                    if scores:
                        best_cat = max(scores, key=scores.get)
                        categorized[best_cat]["pages"].append(page)
                    else:
                        if "other" not in categorized:
                            categorized["other"] = {"title": "Other", "pages": []}
                        categorized["other"]["pages"].append(page)

            print(f"✅ Created {len(categorized)} categories")
            for _cat_key, cat_data in categorized.items():
                print(f"   - {cat_data['title']}: {len(cat_data['pages'])} pages")
            return categorized

        # Auto-categorise by name prefix (e.g. git-log -> git)
        if len(pages) > 1:
            prefix_groups: dict[str, list[dict]] = {}
            for page in pages:
                name = page.get("name", "unknown")
                prefix = name.split("-", 1)[0] if "-" in name else name
                prefix_groups.setdefault(prefix, []).append(page)

            # Only use prefix grouping if it actually reduces categories
            if len(prefix_groups) < len(pages):
                for prefix, group_pages in prefix_groups.items():
                    cat_key = self._sanitize_filename(prefix)
                    categorized[cat_key] = {
                        "title": prefix.title(),
                        "pages": group_pages,
                    }
            else:
                categorized["commands"] = {
                    "title": "Commands",
                    "pages": pages,
                }
        else:
            # Single man page
            page_name = pages[0].get("name", "content") if pages else "content"
            categorized[self._sanitize_filename(page_name)] = {
                "title": page_name,
                "pages": pages,
            }

        print(f"✅ Created {len(categorized)} categories")
        for _cat_key, cat_data in categorized.items():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} pages")
        return categorized

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_skill(self) -> None:
        """Build the complete skill directory structure.

        Creates the output directory, generates reference files, an index,
        and the main SKILL.md.
        """
        print(f"\n🏗️  Building skill: {self.name}")

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorise content
        categorized = self.categorize_content()

        # Generate reference files
        print("\n📝 Generating reference files...")
        total_cats = len(categorized)
        cat_num = 1
        for cat_key, cat_data in categorized.items():
            self._generate_reference_file(cat_key, cat_data, cat_num, total_cats)
            cat_num += 1

        # Generate index
        self._generate_index(categorized)

        # Generate SKILL.md
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ------------------------------------------------------------------
    # Generation (private)
    # ------------------------------------------------------------------

    def _generate_reference_file(
        self,
        cat_key: str,
        cat_data: dict,
        cat_num: int,
        total_cats: int,
    ) -> None:
        """Generate a reference markdown file for a category of man pages.

        Args:
            cat_key: Category key (sanitised).
            cat_data: Dict with ``title`` and ``pages``.
            cat_num: 1-based index of this category.
            total_cats: Total number of categories.
        """
        pages = cat_data["pages"]

        if total_cats == 1:
            filename = f"{self.skill_dir}/references/{cat_key}.md"
        else:
            filename = f"{self.skill_dir}/references/{cat_key}_{cat_num:02d}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")

            for page in pages:
                man_name = page.get("name", "unknown")
                section = page.get("section")
                section_label = f"({section})" if section else ""

                f.write(f"---\n\n## {man_name}{section_label}\n\n")

                # Title / NAME line
                title = page.get("title", "")
                if title and title != man_name:
                    f.write(f"**{title}**\n\n")

                # Synopsis
                synopsis = page.get("synopsis", "")
                if synopsis:
                    f.write("### Synopsis\n\n")
                    f.write(f"```\n{synopsis}\n```\n\n")

                # Description (truncated for reference file)
                description = page.get("description", "")
                if description:
                    f.write("### Description\n\n")
                    # Keep a reasonable amount for the reference file
                    if len(description) > 3000:
                        f.write(f"{description[:3000]}\n\n*... (truncated)*\n\n")
                    else:
                        f.write(f"{description}\n\n")

                # Options
                options = page.get("options", [])
                if options:
                    f.write("### Options\n\n")
                    for opt in options:
                        flag = opt.get("flag", "")
                        desc = opt.get("description", "")
                        f.write(f"- `{flag}`")
                        if desc:
                            # Truncate very long option descriptions
                            short_desc = desc[:200] + "..." if len(desc) > 200 else desc
                            f.write(f" -- {short_desc}")
                        f.write("\n")
                    f.write("\n")

                # Examples
                examples = page.get("examples", [])
                if examples:
                    f.write("### Examples\n\n")
                    for i, ex in enumerate(examples, 1):
                        ex_desc = ex.get("description", "")
                        ex_cmd = ex.get("command", "")
                        if ex_desc:
                            f.write(f"**Example {i}:** {ex_desc}\n\n")
                        if ex_cmd:
                            f.write(f"```bash\n{ex_cmd}\n```\n\n")

                # SEE ALSO
                see_also = page.get("see_also", [])
                if see_also:
                    f.write("### See Also\n\n")
                    f.write(", ".join(f"`{ref}`" for ref in see_also) + "\n\n")

                # Extra sections (non-standard ones we haven't explicitly handled)
                handled = {
                    "NAME",
                    "SYNOPSIS",
                    "DESCRIPTION",
                    "OPTIONS",
                    "EXAMPLES",
                    "EXAMPLE",
                    "SEE ALSO",
                }
                extra_sections = page.get("sections", {})
                for sec_name, sec_text in extra_sections.items():
                    if sec_name in handled or not sec_text.strip():
                        continue
                    f.write(f"### {sec_name.title()}\n\n")
                    if len(sec_text) > 1500:
                        f.write(f"{sec_text[:1500]}\n\n*... (truncated)*\n\n")
                    else:
                        f.write(f"{sec_text}\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized: dict[str, dict]) -> None:
        """Generate references/index.md with links to all reference files.

        Args:
            categorized: Category mapping produced by ``categorize_content()``.
        """
        filename = f"{self.skill_dir}/references/index.md"
        total_cats = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Man Pages Reference\n\n")
            f.write("## Categories\n\n")

            cat_num = 1
            for cat_key, cat_data in categorized.items():
                page_count = len(cat_data["pages"])
                if total_cats == 1:
                    link_filename = f"{cat_key}.md"
                else:
                    link_filename = f"{cat_key}_{cat_num:02d}.md"
                f.write(f"- [{cat_data['title']}]({link_filename}) ({page_count} man page(s))\n")
                cat_num += 1

            f.write("\n## All Man Pages\n\n")
            pages = self.extracted_data.get("pages", [])
            for page in sorted(pages, key=lambda p: p.get("name", "")):
                man_name = page.get("name", "unknown")
                section = page.get("section")
                section_label = f"({section})" if section else ""
                title = page.get("title", "")
                f.write(f"- **{man_name}{section_label}** -- {title}\n")

            f.write("\n## Statistics\n\n")
            f.write(f"- Total man pages: {self.extracted_data.get('total_pages', 0)}\n")
            f.write(f"- Total options: {self.extracted_data.get('total_options', 0)}\n")
            f.write(f"- Total examples: {self.extracted_data.get('total_examples', 0)}\n")

            see_also = self.extracted_data.get("see_also", [])
            if see_also:
                f.write(f"- Cross-references: {len(see_also)}\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized: dict[str, dict]) -> None:
        """Generate the main SKILL.md file.

        Args:
            categorized: Category mapping produced by ``categorize_content()``.
        """
        filename = f"{self.skill_dir}/SKILL.md"

        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        with open(filename, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            f.write(f"# {self.name.title()} Man Pages Skill\n\n")
            f.write(f"{self.description}\n\n")

            # When to Use
            f.write("## When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Understand {self.name} command-line tools and their options\n")
            f.write("- Look up command syntax and usage patterns\n")
            f.write("- Find examples of common command invocations\n")
            f.write("- Review available flags and environment variables\n")
            f.write("- Explore related commands via SEE ALSO references\n\n")

            # Quick command reference (synopses)
            pages = self.extracted_data.get("pages", [])
            synopses = [
                (p.get("name", ""), p.get("synopsis", ""))
                for p in pages
                if p.get("synopsis", "").strip()
            ]

            if synopses:
                f.write("## Quick Command Reference\n\n")
                for cmd_name, synopsis in synopses[:20]:
                    f.write(f"### {cmd_name}\n\n")
                    f.write(f"```\n{synopsis.strip()}\n```\n\n")

            # Page overview
            f.write("## Man Page Overview\n\n")
            total_pages = self.extracted_data.get("total_pages", 0)
            f.write(f"**Total Man Pages:** {total_pages}\n\n")
            f.write("**Content Breakdown:**\n\n")
            for _cat_key, cat_data in categorized.items():
                page_count = len(cat_data["pages"])
                f.write(f"- **{cat_data['title']}**: {page_count} man page(s)\n")
            f.write("\n")

            # Key options (top options across all pages)
            all_options: list[dict] = []
            for page in pages:
                for opt in page.get("options", []):
                    all_options.append(
                        {
                            "command": page.get("name", ""),
                            **opt,
                        }
                    )

            if all_options:
                f.write("## Common Options\n\n")
                f.write(f"*{len(all_options)} options extracted across all man pages*\n\n")
                # Show options for first few commands
                shown_commands: set[str] = set()
                for opt in all_options:
                    cmd = opt.get("command", "")
                    if cmd in shown_commands:
                        continue
                    if len(shown_commands) >= 5:
                        break
                    shown_commands.add(cmd)
                    # Show first 5 options per command
                    cmd_opts = [o for o in all_options if o.get("command") == cmd][:5]
                    f.write(f"### {cmd}\n\n")
                    for co in cmd_opts:
                        flag = co.get("flag", "")
                        flag_desc = co.get("description", "")
                        short_desc = flag_desc[:120] + "..." if len(flag_desc) > 120 else flag_desc
                        f.write(f"- `{flag}` -- {short_desc}\n")
                    f.write("\n")

            # Examples (top examples)
            all_examples: list[dict] = []
            for page in pages:
                for ex in page.get("examples", []):
                    all_examples.append(
                        {
                            "command_name": page.get("name", ""),
                            **ex,
                        }
                    )

            if all_examples:
                f.write("## Examples\n\n")
                f.write(f"*{len(all_examples)} example(s) extracted from man pages*\n\n")
                for ex in all_examples[:15]:
                    cmd_name = ex.get("command_name", "")
                    ex_desc = ex.get("description", "")
                    ex_cmd = ex.get("command", "")
                    if cmd_name:
                        f.write(f"### {cmd_name}\n\n")
                    if ex_desc:
                        f.write(f"{ex_desc}\n\n")
                    if ex_cmd:
                        f.write(f"```bash\n{ex_cmd}\n```\n\n")

            # Cross-references
            see_also = self.extracted_data.get("see_also", [])
            if see_also:
                f.write("## Related Commands (SEE ALSO)\n\n")
                for ref in see_also[:30]:
                    f.write(f"- `{ref}`\n")
                if len(see_also) > 30:
                    f.write(f"\n*... and {len(see_also) - 30} more*\n")
                f.write("\n")

            # Statistics
            f.write("## Documentation Statistics\n\n")
            f.write(f"- **Total Man Pages**: {total_pages}\n")
            f.write(f"- **Total Options**: {self.extracted_data.get('total_options', 0)}\n")
            f.write(f"- **Total Examples**: {self.extracted_data.get('total_examples', 0)}\n")
            f.write(f"- **Cross-references**: {len(see_also)}\n\n")

            # Navigation
            f.write("## Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            total_cats = len(categorized)
            cat_num = 1
            for _cat_key, cat_data in categorized.items():
                ref_name = f"{_cat_key}.md" if total_cats == 1 else f"{_cat_key}_{cat_num:02d}.md"
                f.write(f"- `references/{ref_name}` -- {cat_data['title']}\n")
                cat_num += 1
            f.write("\n")
            f.write("See `references/index.md` for complete reference structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("**Generated by Skill Seekers** | Man Page Scraper\n")

        # Report line count
        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().splitlines())
        print(f"   Generated: {filename} ({line_count} lines)")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Convert a string to a safe filename.

        Args:
            name: Arbitrary string.

        Returns:
            Lowercase snake_case filename-safe string.
        """
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for the man page scraper.

    Supports three workflows:

    1. ``--man-names git,curl`` -- extract named man pages via the ``man``
       command.
    2. ``--man-path /usr/share/man/man1`` -- read man page files from a
       directory.
    3. ``--from-json data.json`` -- reload previously extracted data and
       rebuild the skill.

    Returns:
        Exit code (0 on success, non-zero on error).
    """
    parser = argparse.ArgumentParser(
        description="Convert Unix man pages to a skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --man-names git,curl --name unix-tools\n"
            "  %(prog)s --man-path /usr/share/man/man1 --name coreutils\n"
            "  %(prog)s --from-json unix-tools_extracted.json\n"
        ),
    )

    # Standard arguments (name, description, output, enhance-level, etc.)
    from .arguments.common import add_all_standard_arguments

    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for man pages
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for man), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # Man-specific arguments
    parser.add_argument(
        "--man-names",
        type=str,
        help="Comma-separated list of man page names (e.g. git,curl,grep)",
        metavar="NAMES",
    )
    parser.add_argument(
        "--man-path",
        type=str,
        help="Directory containing man page files (.1-.8, .man, .gz)",
        metavar="DIR",
    )
    parser.add_argument(
        "--sections",
        type=str,
        help="Comma-separated list of man section numbers to extract (e.g. 1,3,8)",
        metavar="NUMS",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Build skill from previously extracted JSON",
        metavar="FILE",
    )

    args = parser.parse_args()

    # Logging level
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Dry run
    if getattr(args, "dry_run", False):
        source = (
            getattr(args, "man_names", None)
            or getattr(args, "man_path", None)
            or getattr(args, "from_json", None)
            or "(none)"
        )
        print(f"\n{'=' * 60}")
        print("DRY RUN: Man Page Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Sections:       {getattr(args, 'sections', None) or 'all'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate: must have at least one source
    if not (
        getattr(args, "man_names", None)
        or getattr(args, "man_path", None)
        or getattr(args, "from_json", None)
    ):
        parser.error("Must specify --man-names, --man-path, or --from-json")

    # Parse section numbers
    section_list: list[int] = []
    if getattr(args, "sections", None):
        try:
            section_list = [int(s.strip()) for s in args.sections.split(",") if s.strip()]
        except ValueError:
            parser.error("--sections must be comma-separated integers (e.g. 1,3,8)")

    # Parse man names
    man_name_list: list[str] = []
    if getattr(args, "man_names", None):
        man_name_list = [n.strip() for n in args.man_names.split(",") if n.strip()]

    # Build from JSON workflow
    if getattr(args, "from_json", None):
        name = Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": getattr(args, "name", None) or name,
            "description": getattr(args, "description", None)
            or f"Use when referencing {name} documentation",
        }
        try:
            converter = ManPageToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Auto-detect name from man names or path
    if not getattr(args, "name", None):
        if man_name_list:
            args.name = man_name_list[0] if len(man_name_list) == 1 else "man-pages"
        elif getattr(args, "man_path", None):
            args.name = Path(args.man_path).name
        else:
            args.name = "man-pages"

    config = {
        "name": args.name,
        "man_names": man_name_list,
        "man_path": getattr(args, "man_path", ""),
        "sections": section_list,
        "description": getattr(args, "description", None),
    }

    try:
        converter = ManPageToSkillConverter(config)

        # Extract
        if not converter.extract_manpages():
            print("\n❌ Man page extraction failed -- see error above", file=sys.stderr)
            sys.exit(1)

        # Build skill
        converter.build_skill()

        # Enhancement Workflow Integration
        from skill_seekers.cli.workflow_runner import run_workflows

        workflow_executed, workflow_names = run_workflows(args)
        workflow_name = ", ".join(workflow_names) if workflow_names else None

        # Traditional enhancement (complements workflow system)
        if getattr(args, "enhance_level", 0) > 0:
            api_key = getattr(args, "api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
            mode = "API" if api_key else "LOCAL"

            print("\n" + "=" * 80)
            print(f"🤖 Traditional AI Enhancement ({mode} mode, level {args.enhance_level})")
            print("=" * 80)
            if workflow_executed:
                print(f"   Running after workflow: {workflow_name}")
                print(
                    "   (Workflow provides specialized analysis,"
                    " enhancement provides general improvements)"
                )
            print("")

            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                    print("✅ API enhancement complete!")
                except ImportError:
                    print("❌ API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    agent = getattr(args, "agent", None) if args else None
                    agent_cmd = getattr(args, "agent_cmd", None) if args else None
                    enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                    enhancer.run(headless=True)
                    print("✅ Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                agent = getattr(args, "agent", None) if args else None
                agent_cmd = getattr(args, "agent_cmd", None) if args else None
                enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                enhancer.run(headless=True)
                print("✅ Local enhancement complete!")

    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during man page processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
