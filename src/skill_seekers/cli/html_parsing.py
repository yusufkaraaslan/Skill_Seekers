"""Lenient HTML parsing with parser fallback (issue #96, task F1.4).

BeautifulSoup's stdlib ``html.parser`` backend can choke on severely
malformed markup (unterminated comments, broken declarations, pathological
nesting): instead of raising it may silently yield a tree with no tags at
all, and the page would be scraped as empty. ``parse_html`` detects both
failure modes and retries with more lenient parsers — ``lxml`` if installed,
then ``html5lib`` (browser-grade error recovery).

``html.parser`` stays first in the chain so output for well-formed
documents is byte-identical to what BeautifulSoup produced before this
module existed.
"""

import logging
import re

from bs4 import BeautifulSoup
from bs4.builder import builder_registry

logger = logging.getLogger(__name__)

#: Parsers tried in order. The first is the historical default; the rest are
#: skipped silently when their backing library is not installed.
PARSER_CHAIN = ("html.parser", "lxml", "html5lib")

_TAG_PATTERN_STR = re.compile(r"<[a-zA-Z]")
_TAG_PATTERN_BYTES = re.compile(rb"<[a-zA-Z]")


def _looks_like_html(markup: str | bytes) -> bool:
    """True when the markup contains something tag-like.

    Plain-text responses legitimately parse to a tag-free tree; only
    tag-bearing markup that comes back tag-free indicates parser failure.
    """
    if isinstance(markup, bytes):
        return _TAG_PATTERN_BYTES.search(markup) is not None
    return _TAG_PATTERN_STR.search(markup) is not None


def available_parsers(chain: tuple[str, ...] = PARSER_CHAIN) -> list[str]:
    """Subset of ``chain`` whose backing libraries are importable."""
    return [name for name in chain if builder_registry.lookup(name) is not None]


def parse_html(
    markup: str | bytes,
    context: str = "",
    parsers: tuple[str, ...] = PARSER_CHAIN,
) -> BeautifulSoup:
    """Parse HTML, falling back to lenient parsers on failure.

    A parse counts as failed when the parser raises, or when it returns a
    tree with no tags for markup that clearly contains tags. ``context``
    (e.g. the page URL) is only used in log messages.

    Always returns a soup: if every parser fails, the least-bad result is
    returned so callers keep their existing "empty page" behaviour instead
    of crashing.
    """
    primary = parsers[0] if parsers else "html.parser"
    empty_soup = None
    last_error: Exception | None = None

    for parser in parsers:
        if builder_registry.lookup(parser) is None:
            continue
        try:
            soup = BeautifulSoup(markup, parser)
        except Exception as e:
            last_error = e
            logger.debug("HTML parser %s failed%s: %s", parser, _ctx(context), e)
            continue
        if soup.find(True) is not None or not _looks_like_html(markup):
            if parser != primary:
                logger.warning(
                    "Primary HTML parser %s produced no usable tree%s; recovered with %s",
                    primary,
                    _ctx(context),
                    parser,
                )
            return soup
        if empty_soup is None:
            empty_soup = soup

    if empty_soup is not None:
        logger.warning(
            "All available HTML parsers (%s) produced a tag-free tree%s",
            ", ".join(available_parsers(parsers)),
            _ctx(context),
        )
        return empty_soup
    if last_error is not None:
        raise last_error
    # No parser in the chain was available; html.parser always is.
    return BeautifulSoup(markup, "html.parser")


def _ctx(context: str) -> str:
    return f" for {context}" if context else ""
