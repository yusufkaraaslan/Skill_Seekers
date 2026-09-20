"""Single home for the "one safe path segment" check (CWE-22).

Config names, source names, workflow names and skill names all end up as one
component of a filesystem path under a directory we own. Every boundary that
turns user or tool input into such a component validates it here, so the next
traversal fix is applied once, not in four copies.
"""

from __future__ import annotations

import re

# Allowlist, not a denylist: a leading letter or digit rules out ``.``, ``..``,
# ``.git`` and other dot-files; the character class rules out separators on
# both platforms, drive prefixes, NUL bytes and whitespace.
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_path_segment(name: object, *, label: str = "name") -> str:
    """Return ``name`` if it is safe to use as a single path segment.

    Raises:
        ValueError: for anything that is not a non-empty ASCII slug made of
            letters, digits, ``.``, ``_`` and ``-`` starting with a letter or
            digit, or that contains ``..``.
    """
    if not isinstance(name, str) or not SAFE_SEGMENT_RE.match(name) or ".." in name:
        raise ValueError(
            f"Invalid {label} {name!r}: must be a single path segment that starts with a "
            "letter or digit and uses only letters, digits, '.', '_' or '-'."
        )
    return name
