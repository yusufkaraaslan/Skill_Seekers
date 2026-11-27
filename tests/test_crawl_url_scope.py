"""Keep page-file crawl scope consistent across documentation scraping and estimation."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse

import pytest

from skill_seekers.cli.doc_scraper import DocToSkillConverter
from skill_seekers.cli.estimate_pages import estimate_pages, is_valid_url


@pytest.fixture(params=["scraper", "estimator"])
def accepts(request):
    """Exercise both public URL filters with the same inputs."""
    if request.param == "estimator":
        return is_valid_url

    converter = DocToSkillConverter.__new__(DocToSkillConverter)

    def check(url, base, include, exclude):
        converter.base_url = base
        converter._include_patterns = include
        converter._exclude_patterns = exclude
        return converter.is_valid_url(url)

    return check


@pytest.mark.parametrize("extension", ["html", "htm", "xhtml", "php", "asp", "aspx", "jsp", "jspx"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_page_file_extensions(accepts, extension, uppercase):
    extension = extension.upper() if uppercase else extension
    base = f"https://docs.example.com/manual/index.{extension}"
    assert accepts("https://docs.example.com/manual/start.html", base, [], [])
    assert accepts("https://docs.example.com/manual/sub/deep.html", base, [], [])
    assert not accepts("https://docs.example.com/manual2/page.html", base, [], [])
    assert not accepts("https://docs.example.com/other/page.html", base, [], [])
    assert not accepts("https://other.example.com/manual/page.html", base, [], [])


@pytest.mark.parametrize("suffix", ["?lang=en", "#top", ";sid=1", ";sid=1?lang=en#top"])
def test_page_file_query_fragment_and_params(accepts, suffix):
    base = "https://docs.example.com/manual/index.html" + suffix
    assert accepts("https://docs.example.com/manual/start.html", base, [], [])
    assert not accepts("https://docs.example.com/other/start.html", base, [], [])


@pytest.mark.parametrize(
    "directory", ["manual", "manual/", "manual/intro", "manual.pdf", "manual.html/"]
)
def test_non_page_file_bases_retain_directory_scope(accepts, directory):
    base = "https://docs.example.com/" + directory
    assert accepts(base.rstrip("/") + "/child", base, [], [])
    assert not accepts("https://docs.example.com/other", base, [], [])
    assert not accepts(base.rstrip("/") + "2/child", base, [], [])


@pytest.mark.parametrize(
    "base", ["https://docs.example.com", "https://docs.example.com/index.html"]
)
def test_root_scope_rejects_host_prefix_matches(accepts, base):
    assert accepts("https://docs.example.com/guide/start", base, [], [])
    assert not accepts("https://docs.example.com.evil.invalid/guide/start", base, [], [])
    assert not accepts("https://docs.example.com@other.invalid/guide/start", base, [], [])


def test_page_file_scope_keeps_include_and_exclude_filters(accepts):
    base = "https://docs.example.com/manual/index.html"
    include, exclude = ["/guide/"], ["/private/"]
    assert accepts("https://docs.example.com/manual/guide/start", base, include, exclude)
    assert not accepts("https://docs.example.com/manual/api/start", base, include, exclude)
    assert not accepts(
        "https://docs.example.com/manual/guide/private/start", base, include, exclude
    )
    assert not accepts("https://docs.example.com/other/guide/start", base, include, exclude)


def test_malformed_base_is_rejected_without_crashing(accepts):
    assert not accepts(
        "https://docs.example.com/manual/start", "https://[::1/manual/index.html", [], []
    )


@pytest.fixture
def page_file_site():
    """Serve sibling/child links plus forbidden boundaries entirely on loopback."""
    requests = []
    pages = {"/manual/index.html", "/manual/start.html", "/manual/sub/deep.html"}

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(200 if urlparse(self.path).path in pages else 404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

        def do_GET(self):
            requests.append((self.headers["Host"], urlparse(self.path).path))
            self.do_HEAD()
            self.wfile.write(
                (
                    "<html><title>Docs</title><article><h1>Guide</h1><p>Documentation.</p>"
                    '<a href="/manual/start.html">Start</a>'
                    '<a href="/manual/sub/deep.html">Deep</a>'
                    '<a href="/manual/private.html">Private</a>'
                    '<a href="/manual2/page.html">Adjacent</a>'
                    '<a href="/other/page.html">Outside</a>'
                    f'<a href="http://localhost:{self.server.server_port}/manual/offhost.html">'
                    "Other host</a></article></html>"
                ).encode()
            )

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests, pages
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["sync", "async", "estimate"])
@pytest.mark.parametrize("suffix", ["", "?lang=en", ";sid=1?lang=en"])
def test_real_crawl_and_estimate_from_page_file(page_file_site, tmp_path, mode, suffix):
    host, requests, expected_pages = page_file_site
    config = {
        "name": "scope-test",
        "base_url": host + "/manual/index.html" + suffix,
        "output_dir": str(tmp_path / "skill"),
        "rate_limit": 0,
        "workers": 1,
        "async_mode": mode == "async",
        "max_pages": 10,
        "skip_llms_txt": True,
        "url_patterns": {"include": ["/manual/"], "exclude": ["/private.html"]},
        "selectors": {"main_content": "article", "title": "h1", "code_blocks": "pre"},
    }
    if mode == "estimate":
        result = estimate_pages(config, max_discovery=10, timeout=5)
        assert result["discovered"] == len(expected_pages)
        assert result["pending"] == 0
    else:
        converter = DocToSkillConverter(config)
        converter.scrape_all()
        assert {urlparse(url).path for url in converter.visited_urls} == expected_pages
        assert converter.pages_scraped == len(expected_pages)

    # Ignore best-effort sitemap and Markdown probes; inspect actual HTML requests.
    requested_pages = {(hostname, path) for hostname, path in requests if path.endswith(".html")}
    assert requested_pages == {(urlparse(host).netloc, path) for path in expected_pages}
