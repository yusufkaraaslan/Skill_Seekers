#!/usr/bin/env python3
"""Render sponsor placements from ``sponsors.json`` into the READMEs and SPONSORS.md.

``sponsors.json`` is the single source of truth. This script rewrites the content
between the sponsor markers in every ``README*.md`` and regenerates ``SPONSORS.md``,
so adding a sponsor is a one-file edit instead of 13 hand edits.

Markers (already present in each README)::

    <!-- SPONSORS:START -->  ... generated ...  <!-- SPONSORS:END -->

All tiers render in that single block as ``###`` subheadings, ordered from the
highest tier down - the layout used by FastAPI and every comparable project.
Tier value is expressed by order and logo size, not by scattering placements
across the page.

Only logos/links are generated; the surrounding prose stays hand-maintained so the
translated READMEs keep their own wording.

Usage::

    python scripts/render_sponsors.py --write   # apply
    python scripts/render_sponsors.py --check   # CI drift guard (non-zero on drift)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
SPONSORS_FILE = REPO_ROOT / "sponsors.json"
SPONSORS_MD = REPO_ROOT / "SPONSORS.md"

# Tier render order, highest first. Order and logo size carry the hierarchy.
TIERS = ("partners", "platinum", "gold", "silver", "bronze")

# Logo width (px) per tier - Gold "large", Silver "medium", Bronze "small".
TIER_WIDTH = {
    "partners": 200,
    "platinum": 200,
    "gold": 180,
    "silver": 140,
    "bronze": 100,
}

TIER_LABEL = {
    "partners": "Launch Partner",
    "platinum": "Platinum Sponsors",
    "gold": "Gold Sponsors",
    "silver": "Silver Sponsors",
    "bronze": "Bronze Sponsors",
}

# Caption under each logo. Rule 2 requires paid placements to be explicitly
# labelled, so every tier except the grandfathered partner says "Sponsor".
TIER_CAPTION = {
    "partners": "Launch Partner",
    "platinum": "Sponsor — Platinum",
    "gold": "Sponsor — Gold",
    "silver": "Sponsor — Silver",
    "bronze": "Sponsor — Bronze",
}

# SPONSORSHIP.md rule 4 (link policy): standard UTM parameters are allowed for
# traffic measurement. Affiliate, referral and click-tracking parameters are not.
#
# This is a blocklist rather than an allowlist on purpose - sponsors legitimately
# use product parameters (?plan=pro, ?lang=en) that the policy says nothing about.
DISALLOWED_PARAMS = re.compile(
    r"^("
    r"ref|referrer|referral|refid|"  # referral
    r"aff|affid|affiliate|partner|pid|"  # affiliate
    r"fbclid|gclid|msclkid|dclid|twclid|ttclid|irclickid|clickid|"  # click IDs
    r"mc_[a-z]+|_hs[a-z]*"  # mailchimp / hubspot analytics
    r")$",
    re.I,
)


class PolicyError(ValueError):
    """Raised when sponsor data violates the published sponsorship policy."""


def _assert_clean_url(name: str, url: str) -> None:
    """Reject sponsor URLs carrying affiliate or click-tracking parameters.

    SPONSORSHIP.md rule 4 permits standard UTM parameters (``utm_source``,
    ``utm_medium``, ``utm_campaign``) so sponsors can measure traffic, but
    forbids affiliate/referral parameters and analytics injection.
    """
    query = urlsplit(url).query
    if not query:
        return
    offenders = sorted(k for k in parse_qs(query) if DISALLOWED_PARAMS.match(k))
    if offenders:
        raise PolicyError(
            f"{name}: sponsor URL carries affiliate/tracking parameters {offenders} - "
            f"rule 4 of SPONSORSHIP.md permits standard UTM parameters only.\n  {url}"
        )


def load_sponsors() -> dict:
    """Load and validate sponsors.json."""
    data = json.loads(SPONSORS_FILE.read_text(encoding="utf-8"))
    for tier in TIERS:
        for entry in data.get(tier, []):
            _assert_clean_url(entry["name"], entry["url"])
            for key in ("logo", "logo_svg"):
                path = entry.get(key)
                if path and not (REPO_ROOT / path).is_file():
                    raise PolicyError(f"{entry['name']}: {key} not found at {path}")
    return data


def _logo_html(entry: dict, tier: str) -> str:
    """Render one logo, captioned with its paid-placement label (rule 2).

    ``logo`` is deliberately a raster: README.md is also the PyPI project
    description, and SVG is not reliably rendered there. ``logo_svg`` keeps the
    vector source alongside it for the website.
    """
    width = entry.get("width", TIER_WIDTH[tier])
    caption = TIER_CAPTION.get(tier, "Sponsor")
    return (
        f'  <a href="{entry["url"]}">'
        f'<img src="{entry["logo"]}" alt="{entry["name"]}" width="{width}"></a>'
        f"<br/><sub><b>{caption}</b></sub>"
    )


def render_sponsors(data: dict) -> str:
    """Render every tier into one block, highest tier first."""
    out: list[str] = []
    for tier in TIERS:
        entries = data.get(tier, [])
        if not entries:
            continue
        out.append(f"### {TIER_LABEL[tier]}\n")
        out.append('<p align="center">')
        out.extend(_logo_html(e, tier) for e in entries)
        out.append("</p>\n")
        # Platinum (and grandfathered partners) may carry a short approved blurb.
        for e in entries:
            if e.get("blurb"):
                out.append(f"[{e['name']}]({e['url']}) — {e['blurb']}\n")
    return "\n".join(out).rstrip() if out else ""


def _replace_block(text: str, marker: str, body: str) -> str:
    """Replace everything between the ``START``/``END`` markers for ``marker``."""
    pattern = re.compile(
        rf"<!-- {marker}:START -->.*?<!-- {marker}:END -->",
        re.DOTALL,
    )
    if not pattern.search(text):
        return text
    rendered = f"<!-- {marker}:START -->\n{body}\n<!-- {marker}:END -->"
    # lambda avoids backslash/group-reference interpretation in the replacement
    return pattern.sub(lambda _m: rendered, text)


def render_sponsors_md(data: dict) -> str:
    """Full sponsor roll, including the Supporter tier (names only)."""
    lines = [
        "# Sponsors",
        "",
        "Skill Seekers is maintained in the open. These sponsors keep it that way.",
        "",
        f"Interested? See **[SPONSORSHIP.md]({data['policy']})** for tiers and rules, "
        f"or sponsor directly at [GitHub Sponsors]({data['sponsors_url']}).",
        "",
        "> All placements on this page are paid sponsorships and are labelled as such.",
        "> Sponsorship buys placement, not endorsement - see the rules in SPONSORSHIP.md.",
        "",
    ]
    any_listed = False
    for tier in TIERS:
        entries = data.get(tier, [])
        if not entries:
            continue
        any_listed = True
        lines += [f"## {TIER_LABEL[tier]}", ""]
        for e in entries:
            detail = e.get("note") or (f"since {e['since']}" if e.get("since") else "")
            suffix = f" — {detail}" if detail else ""
            lines.append(f"- [{e['name']}]({e['url']}){suffix}")
        lines.append("")

    supporters = data.get("supporters", [])
    lines += ["## Supporters", ""]
    if supporters:
        any_listed = True
        lines += [f"- {s}" for s in supporters]
    else:
        lines.append(f"_No supporters yet - [be the first]({data['sponsors_url']})._")
    lines.append("")

    if not any_listed:
        lines.insert(6, "_No sponsors yet._\n")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="apply changes")
    group.add_argument("--check", action="store_true", help="fail if files are out of date")
    args = parser.parse_args(argv)

    try:
        data = load_sponsors()
    except PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    block = render_sponsors(data)
    drifted: list[str] = []

    for readme in sorted(REPO_ROOT.glob("README*.md")):
        original = readme.read_text(encoding="utf-8")
        updated = _replace_block(original, "SPONSORS", block)
        if updated != original:
            drifted.append(readme.name)
            if args.write:
                readme.write_text(updated, encoding="utf-8")

    sponsors_md = render_sponsors_md(data)
    if not SPONSORS_MD.is_file() or SPONSORS_MD.read_text(encoding="utf-8") != sponsors_md:
        drifted.append(SPONSORS_MD.name)
        if args.write:
            SPONSORS_MD.write_text(sponsors_md, encoding="utf-8")

    if args.check and drifted:
        print(
            "error: sponsor placements are out of date with sponsors.json:\n  "
            + "\n  ".join(drifted)
            + "\n\nRun: python scripts/render_sponsors.py --write",
            file=sys.stderr,
        )
        return 1

    action = "updated" if args.write else "would update"
    print(f"{action} {len(drifted)} file(s)" if drifted else "sponsor placements up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
