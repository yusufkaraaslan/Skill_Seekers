"""Tests for sync change detector (detector.py)."""

import hashlib
import pytest
from unittest.mock import patch, MagicMock
from skill_seekers.sync.detector import ChangeDetector
from skill_seekers.sync.models import ChangeType


@pytest.fixture
def detector():
    return ChangeDetector(timeout=10)


class TestChangeDetectorBasics:
    def test_init_default(self):
        d = ChangeDetector()
        assert d.timeout == 30

    def test_init_custom_timeout(self):
        d = ChangeDetector(timeout=5)
        assert d.timeout == 5

    def test_compute_hash_deterministic(self, detector):
        h1 = detector.compute_hash("hello world")
        h2 = detector.compute_hash("hello world")
        assert h1 == h2
        assert len(h1) == 64

    def test_compute_hash_different_content(self, detector):
        h1 = detector.compute_hash("hello world")
        h2 = detector.compute_hash("hello world!")
        assert h1 != h2

    def test_compute_hash_empty(self, detector):
        h = detector.compute_hash("")
        expected = hashlib.sha256(b"").hexdigest()
        assert h == expected

    def test_compute_hash_unicode(self, detector):
        h = detector.compute_hash("héllo wörld 🎉")
        assert len(h) == 64


class TestCheckPage:
    @patch("skill_seekers.sync.detector.requests.get")
    def test_new_page_added(self, mock_get, detector):
        mock_get.return_value.text = "new content"
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        change = detector.check_page("https://example.com", old_hash=None)

        assert change.change_type == ChangeType.ADDED
        assert change.old_hash is None
        assert change.new_hash is not None
        assert change.url == "https://example.com"

    @patch("skill_seekers.sync.detector.requests.get")
    def test_unchanged_page(self, mock_get, detector):
        content = "stable content"
        old_hash = detector.compute_hash(content)
        mock_get.return_value.text = content
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        change = detector.check_page("https://example.com", old_hash=old_hash)

        assert change.change_type == ChangeType.UNCHANGED

    @patch("skill_seekers.sync.detector.requests.get")
    def test_modified_page(self, mock_get, detector):
        old_hash = detector.compute_hash("old content")
        mock_get.return_value.text = "new content"
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        change = detector.check_page("https://example.com", old_hash=old_hash)

        assert change.change_type == ChangeType.MODIFIED
        assert change.old_hash == old_hash
        assert change.new_hash != old_hash

    @patch("skill_seekers.sync.detector.requests.get")
    def test_deleted_page(self, mock_get, detector):
        old_hash = detector.compute_hash("gone")
        from requests.exceptions import RequestException

        mock_get.side_effect = RequestException("Connection refused")

        change = detector.check_page("https://example.com", old_hash=old_hash)

        assert change.change_type == ChangeType.DELETED

    @patch("skill_seekers.sync.detector.requests.get")
    def test_generate_diff(self, mock_get, detector):
        old_content = "line 1\nline 2\nline 3"
        new_content = "line 1\nline 2 modified\nline 3\nline 4"
        old_hash = detector.compute_hash(old_content)
        mock_get.return_value.text = new_content
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        change = detector.check_page(
            "https://example.com", old_hash=old_hash, generate_diff=True, old_content=old_content
        )

        assert change.change_type == ChangeType.MODIFIED
        assert change.diff is not None
        assert "modified" in change.diff


class TestCheckPages:
    @patch("skill_seekers.sync.detector.requests.get")
    def test_multiple_pages(self, mock_get, detector):
        content = "page content"
        mock_get.return_value.text = content
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        report = detector.check_pages(
            urls=["https://a.com", "https://b.com"],
            previous_hashes={},
            generate_diffs=False,
        )

        assert report.total_pages == 2
        assert len(report.added) == 2
        assert report.skill_name == "unknown"

    @patch("skill_seekers.sync.detector.requests.get")
    def test_mixed_changes(self, mock_get, detector):
        content = detector.compute_hash("page content")
        mock_get.return_value.text = "page content"
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        report = detector.check_pages(
            urls=["https://a.com", "https://b.com"],
            previous_hashes={"https://a.com": content},
            generate_diffs=False,
        )

        assert report.total_pages == 2
        assert isinstance(report.unchanged, int)

    @patch("skill_seekers.sync.detector.requests.get")
    def test_detects_deleted_pages(self, mock_get, detector):
        mock_get.return_value.text = "current"
        mock_get.return_value.headers = {}
        mock_get.return_value.raise_for_status = MagicMock()

        report = detector.check_pages(
            urls=["https://a.com"],
            previous_hashes={"https://a.com": "abc", "https://deleted.com": "xyz"},
            generate_diffs=False,
        )

        assert len(report.deleted) == 1
        assert report.deleted[0].url == "https://deleted.com"


class TestGenerateDiff:
    def test_basic_diff(self, detector):
        old = "line1\nline2\nline3\n"
        new = "line1\nline2_modified\nline3\n"
        result = detector.generate_diff(old, new)
        assert "modified" in result

    def test_addition(self, detector):
        old = "line1\nline2\n"
        new = "line1\nline2\nline3\n"
        result = detector.generate_diff(old, new)
        assert "+line3" in result

    def test_no_diff(self, detector):
        old = "identical\n"
        new = "identical\n"
        result = detector.generate_diff(old, new)
        assert result == ""


class TestGenerateSummaryDiff:
    def test_counts(self, detector):
        old = "one\ntwo\n"
        new = "one\ntwo\nthree\nfour\n"
        result = detector.generate_summary_diff(old, new)
        assert "+2" in result

    def test_add_and_remove(self, detector):
        old = "one\ntwo\nthree\n"
        new = "one\nfour\nfive\n"
        result = detector.generate_summary_diff(old, new)
        assert "+" in result
        assert "-" in result


class TestHeaderChanges:
    @patch("skill_seekers.sync.detector.requests.head")
    def test_modified_header_detected(self, mock_head, detector):
        mock_head.return_value.headers = {"Last-Modified": "Wed, 21 Oct 2025 07:28:00 GMT"}
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.check_header_changes(
            "https://example.com", old_modified="Wed, 20 Oct 2025 07:28:00 GMT"
        )
        assert changed is True

    @patch("skill_seekers.sync.detector.requests.head")
    def test_unchanged_header(self, mock_head, detector):
        same = "Wed, 21 Oct 2025 07:28:00 GMT"
        mock_head.return_value.headers = {"Last-Modified": same}
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.check_header_changes("https://example.com", old_modified=same)
        assert changed is False

    @patch("skill_seekers.sync.detector.requests.head")
    def test_etag_change(self, mock_head, detector):
        mock_head.return_value.headers = {"ETag": '"new-etag"'}
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.check_header_changes("https://example.com", old_etag='"old-etag"')
        assert changed is True

    @patch("skill_seekers.sync.detector.requests.head")
    def test_request_error_counts_as_change(self, mock_head, detector):
        from requests.exceptions import RequestException

        mock_head.side_effect = RequestException("timeout")

        changed = detector.check_header_changes("https://example.com")
        assert changed is True

    @patch("skill_seekers.sync.detector.requests.head")
    def test_batch_check_headers(self, mock_head, detector):
        mock_head.return_value.headers = {"Last-Modified": "Wed, 22 Oct 2025 00:00:00 GMT"}
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.batch_check_headers(
            urls=["https://a.com", "https://b.com"],
            previous_metadata={
                "https://a.com": {"last-modified": "Wed, 21 Oct 2025 00:00:00 GMT"},
                "https://b.com": {"last-modified": "Wed, 22 Oct 2025 00:00:00 GMT"},
            },
        )

        assert "https://a.com" in changed
        assert "https://b.com" not in changed


class TestHeaderChangeNoValidators:
    def test_no_validators_assumes_changed(self):
        """Regression (INF-05): when the server sends neither Last-Modified nor
        ETag, the header check must report 'changed' (so a content fetch
        verifies) instead of silently 'unchanged'."""
        from unittest.mock import MagicMock, patch

        from skill_seekers.sync.detector import ChangeDetector

        det = ChangeDetector()
        resp = MagicMock()
        resp.headers = {}
        resp.raise_for_status = lambda: None
        with patch("skill_seekers.sync.detector.requests.head", return_value=resp):
            assert (
                det.check_header_changes(
                    "https://x.com", old_modified="Mon, 01 Jan 2024 00:00:00 GMT", old_etag='"abc"'
                )
                is True
            )

    @patch("skill_seekers.sync.detector.requests.head")
    def test_no_stored_validators_assumes_changed(self, mock_head, detector):
        """Regression: a never-seen URL (no stored validators) must report
        'changed' even when the server DOES send validators — there is nothing
        to compare against, so a content fetch must verify."""
        mock_head.return_value.headers = {
            "Last-Modified": "Wed, 21 Oct 2025 07:28:00 GMT",
            "ETag": '"abc"',
        }
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.check_header_changes("https://example.com/new-page")
        assert changed is True

    @patch("skill_seekers.sync.detector.requests.head")
    def test_batch_check_headers_includes_never_seen_url(self, mock_head, detector):
        """A URL absent from previous_metadata must appear in changed_urls."""
        mock_head.return_value.headers = {
            "Last-Modified": "Wed, 22 Oct 2025 00:00:00 GMT",
            "ETag": '"x"',
        }
        mock_head.return_value.raise_for_status = MagicMock()

        changed = detector.batch_check_headers(
            urls=["https://example.com/new-page"], previous_metadata={}
        )
        assert "https://example.com/new-page" in changed
