#!/usr/bin/env python3
"""
Index this codebase: walk files, extract symbols, and generate a JSON + Markdown index.

Usage (examples):
  python3 cli/index_codebase.py --root .
  python3 cli/index_codebase.py --depth deep --out-json code_index.json --out-md CODE_INDEX.md

Outputs by default:
  - code_index.json (machine-readable index)
  - CODE_INDEX.md  (human-friendly summary)

This uses the local CodeAnalyzer for multi-language parsing (Python, JS/TS, C/C++ [headers]).
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Local analyzer (lives in the same folder)
from code_analyzer import CodeAnalyzer


DEFAULT_EXCLUDES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "output",
}

INTERESTING_EXTS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".h": "C++",  # treat headers as C++ for richer patterns
}


def detect_language(path: str) -> Optional[str]:
    _, ext = os.path.splitext(path)
    return INTERESTING_EXTS.get(ext.lower())


def should_skip_dir(dirname: str) -> bool:
    name = os.path.basename(dirname)
    return name in DEFAULT_EXCLUDES or name.startswith(".") and name not in {".vscode"}


def iter_source_files(root: str) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories in-place to avoid descending into them
        dirnames[:] = [d for d in dirnames if not should_skip_dir(os.path.join(dirpath, d))]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            if detect_language(fpath):
                files.append(fpath)
    return files


def summarize_symbols(file_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    classes_index: Dict[str, List[Dict[str, Any]]] = {}
    functions_index: Dict[str, List[Dict[str, Any]]] = {}

    for rec in file_records:
        path = rec["path"]
        lang = rec["language"]
        for cls in rec.get("classes", []) or []:
            classes_index.setdefault(cls.get("name", ""), []).append({
                "file": path,
                "language": lang,
                "line": cls.get("line_number"),
                "bases": cls.get("base_classes", []),
            })
            # Methods
            for m in cls.get("methods", []) or []:
                functions_index.setdefault(m.get("name", ""), []).append({
                    "file": path,
                    "language": lang,
                    "line": m.get("line_number"),
                    "class": cls.get("name"),
                    "params": m.get("parameters", []),
                })

        for fn in rec.get("functions", []) or []:
            functions_index.setdefault(fn.get("name", ""), []).append({
                "file": path,
                "language": lang,
                "line": fn.get("line_number"),
                "params": fn.get("parameters", []),
            })

    return {
        "classes_by_name": classes_index,
        "functions_by_name": functions_index,
    }


def make_markdown(index: Dict[str, Any]) -> str:
    files = index["files"]
    summary = index["summary"]
    classes_by_name = index["symbol_index"]["classes_by_name"]
    functions_by_name = index["symbol_index"]["functions_by_name"]

    lines: List[str] = []
    lines.append(f"# Code Index\n")
    lines.append(f"Generated: {index['generated_at']}\n")
    lines.append("")

    lines.append("## Summary\n")
    lines.append(f"- Files analyzed: {summary['files']}\n")
    lines.append(f"- Classes found: {summary['classes']}\n")
    lines.append(f"- Functions found: {summary['functions']}\n")
    lines.append("")

    lines.append("## Files\n")
    for rec in files:
        rel = rec["rel_path"]
        lang = rec["language"]
        cls_count = len(rec.get("classes", []) or [])
        fn_count = len(rec.get("functions", []) or [])
        lines.append(f"- `{rel}` ({lang}) — {cls_count} classes, {fn_count} functions")
    lines.append("")

    if classes_by_name:
        lines.append("## Classes\n")
        for name, refs in sorted(classes_by_name.items(), key=lambda x: x[0].lower()):
            ref = refs[0]
            lines.append(f"- `{name}` — {len(refs)} occurrence(s) e.g. {ref['file']}")
        lines.append("")

    if functions_by_name:
        lines.append("## Functions\n")
        for name, refs in sorted(functions_by_name.items(), key=lambda x: x[0].lower()):
            ref = refs[0]
            lines.append(f"- `{name}` — {len(refs)} occurrence(s) e.g. {ref['file']}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Index a codebase and generate symbol index")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parser.add_argument("--depth", default="deep", choices=["surface", "deep"], help="Analysis depth")
    parser.add_argument("--out-json", default="code_index.json", help="Path to write JSON index")
    parser.add_argument("--out-md", default="CODE_INDEX.md", help="Path to write Markdown summary")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    analyzer = CodeAnalyzer(depth=args.depth)

    file_paths = iter_source_files(root)

    records: List[Dict[str, Any]] = []
    for fpath in sorted(file_paths):
        lang = detect_language(fpath)
        if not lang:
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        analysis: Dict[str, Any] = analyzer.analyze_file(fpath, content, lang) or {}
        records.append({
            "path": fpath,
            "rel_path": os.path.relpath(fpath, root),
            "language": lang,
            "classes": analysis.get("classes", []),
            "functions": analysis.get("functions", []),
        })

    symbol_index = summarize_symbols(records)
    total_classes = sum(len(r.get("classes", []) or []) for r in records)
    total_functions = sum(len(r.get("functions", []) or []) for r in records)

    final_index = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "root": root,
        "depth": args.depth,
        "summary": {
            "files": len(records),
            "classes": total_classes,
            "functions": total_functions,
        },
        "files": records,
        "symbol_index": symbol_index,
    }

    # Write JSON
    out_json = os.path.abspath(args.out_json)
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(final_index, jf, indent=2)

    # Write Markdown
    out_md = os.path.abspath(args.out_md)
    with open(out_md, "w", encoding="utf-8") as mf:
        mf.write(make_markdown(final_index))

    print(f"✅ Wrote {out_json}")
    print(f"✅ Wrote {out_md}")


if __name__ == "__main__":
    main()
