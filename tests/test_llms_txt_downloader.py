import pytest
from unittest.mock import patch, Mock
import requests
from skill_seekers.cli.llms_txt_downloader import LlmsTxtDownloader

def test_successful_download():
    """Test successful download with valid markdown content"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    mock_response = Mock()
    mock_response.text = "# Header\n\nSome content with markdown patterns.\n\n## Subheader\n\n- List item\n- Another item\n\n```python\ncode_block()\n```\n" + "x" * 200
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response) as mock_get:
        content = downloader.download()

    assert content is not None
    assert len(content) > 100
    assert isinstance(content, str)
    assert "# Header" in content
    mock_get.assert_called_once()

def test_timeout_with_retry():
    """Test timeout scenario with retry logic"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt", max_retries=2)

    with patch('requests.get', side_effect=requests.Timeout("Connection timeout")) as mock_get:
        with patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
            content = downloader.download()

    assert content is None
    assert mock_get.call_count == 2  # Should retry once (2 total attempts)
    assert mock_sleep.call_count == 1  # Should sleep once between retries

def test_empty_content_rejection():
    """Test rejection of content shorter than 100 chars"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    mock_response = Mock()
    mock_response.text = "# Short"
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response):
        content = downloader.download()

    assert content is None

def test_non_markdown_rejection():
    """Test rejection of content that doesn't look like markdown"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    mock_response = Mock()
    mock_response.text = "Plain text without any markdown patterns at all. " * 10
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response):
        content = downloader.download()

    assert content is None

def test_http_error_handling():
    """Test handling of HTTP errors (404, 500, etc.)"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt", max_retries=2)

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch('requests.get', return_value=mock_response) as mock_get:
        with patch('time.sleep'):
            content = downloader.download()

    assert content is None
    assert mock_get.call_count == 2  # Should retry once

def test_exponential_backoff():
    """Test that exponential backoff delays are correct"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt", max_retries=3)

    with patch('requests.get', side_effect=requests.Timeout("Connection timeout")):
        with patch('time.sleep') as mock_sleep:
            content = downloader.download()

    assert content is None
    # Should sleep with delays: 1s, 2s (2^0, 2^1)
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)  # First retry delay
    mock_sleep.assert_any_call(2)  # Second retry delay

def test_markdown_validation():
    """Test markdown pattern detection"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    # Test various markdown patterns
    assert downloader._is_markdown("# Header")
    assert downloader._is_markdown("## Subheader")
    assert downloader._is_markdown("```code```")
    assert downloader._is_markdown("- list item")
    assert downloader._is_markdown("* bullet point")
    assert downloader._is_markdown("`inline code`")

    # Test non-markdown content
    assert not downloader._is_markdown("Plain text without any markdown patterns")

def test_custom_timeout():
    """Test custom timeout parameter"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt", timeout=10)

    mock_response = Mock()
    mock_response.text = "# Header\n\nContent " * 50
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response) as mock_get:
        content = downloader.download()

    assert content is not None
    # Verify timeout was passed to requests.get
    call_kwargs = mock_get.call_args[1]
    assert call_kwargs['timeout'] == 10

def test_custom_max_retries():
    """Test custom max_retries parameter"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt", max_retries=5)

    with patch('requests.get', side_effect=requests.Timeout("Connection timeout")) as mock_get:
        with patch('time.sleep'):
            content = downloader.download()

    assert content is None
    assert mock_get.call_count == 5  # Should attempt 5 times

def test_user_agent_header():
    """Test that custom user agent is set"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    mock_response = Mock()
    mock_response.text = "# Header\n\nContent " * 50
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response) as mock_get:
        content = downloader.download()

    assert content is not None
    # Verify custom user agent was passed
    call_kwargs = mock_get.call_args[1]
    assert call_kwargs['headers']['User-Agent'] == 'Skill-Seekers-llms.txt-Reader/1.0'

def test_get_proper_filename():
    """Test filename conversion from .txt to .md"""
    downloader = LlmsTxtDownloader("https://hono.dev/llms-full.txt")

    filename = downloader.get_proper_filename()

    assert filename == "llms-full.md"
    assert not filename.endswith('.txt')

def test_get_proper_filename_standard():
    """Test standard variant naming"""
    downloader = LlmsTxtDownloader("https://hono.dev/llms.txt")

    filename = downloader.get_proper_filename()

    assert filename == "llms.md"

def test_get_proper_filename_small():
    """Test small variant naming"""
    downloader = LlmsTxtDownloader("https://hono.dev/llms-small.txt")

    filename = downloader.get_proper_filename()

    assert filename == "llms-small.md"

def test_is_markdown_rejects_html_doctype():
    """Test that HTML with DOCTYPE is rejected (prevents redirect trap)"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    html = '<!DOCTYPE html><html><head><title>Product Page</title></head><body>Content</body></html>'
    assert not downloader._is_markdown(html)

    # Test case-insensitive
    html_uppercase = '<!DOCTYPE HTML><HTML><BODY>Content</BODY></HTML>'
    assert not downloader._is_markdown(html_uppercase)

def test_is_markdown_rejects_html_tag():
    """Test that HTML with <html> tag is rejected (prevents redirect trap)"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    html = '<html><head><meta charset="utf-8"></head><body>Content</body></html>'
    assert not downloader._is_markdown(html)

    # Test with just opening tag
    html_partial = '<html><head>Some content'
    assert not downloader._is_markdown(html_partial)

def test_is_markdown_rejects_html_meta():
    """Test that HTML with <meta> or <head> tags is rejected"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    html_with_head = '<head><title>Page</title></head><body>Content</body>'
    assert not downloader._is_markdown(html_with_head)

    html_with_meta = '<meta charset="utf-8"><meta name="viewport" content="width=device-width">'
    assert not downloader._is_markdown(html_with_meta)

def test_is_markdown_accepts_markdown_with_html_words():
    """Test that markdown mentioning 'html' word is still accepted"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    markdown = '# Guide\n\nLearn about html tags in markdown. You can write HTML inside markdown.'
    assert downloader._is_markdown(markdown)

    # Test with actual markdown patterns
    markdown_with_code = '# HTML Tutorial\n\n```html\n<div>example</div>\n```\n\n## More content'
    assert downloader._is_markdown(markdown_with_code)

def test_html_detection_only_scans_first_500_chars():
    """Test that HTML detection only scans first 500 characters for performance"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    # HTML tag after 500 chars should not be detected
    safe_markdown = '# Header\n\n' + ('Valid markdown content. ' * 50) + '\n\n<!DOCTYPE html>'
    # This should pass because <!DOCTYPE html> is beyond first 500 chars
    if len(safe_markdown[:500]) < len('<!DOCTYPE html>'):
        # If the HTML is within 500 chars, adjust test
        assert not downloader._is_markdown(safe_markdown)
    else:
        # HTML beyond 500 chars should not trigger rejection
        assert downloader._is_markdown(safe_markdown)

def test_html_redirect_trap_scenario():
    """Test real-world scenario: llms.txt redirects to HTML product page"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    # Simulate Claude Code redirect scenario (302 to HTML page)
    html_product_page = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Claude Code - Product Page</title>
</head>
<body>
    <h1>Claude Code</h1>
    <p>Product information...</p>
</body>
</html>'''

    # Should reject this HTML even though it has <h1> tag (looks like markdown "# ")
    assert not downloader._is_markdown(html_product_page)

def test_download_rejects_html_redirect():
    """Test that download() properly rejects HTML redirects"""
    downloader = LlmsTxtDownloader("https://example.com/llms.txt")

    mock_response = Mock()
    # Simulate server returning HTML instead of markdown
    mock_response.text = '<!DOCTYPE html><html><body><h1>Product Page</h1></body></html>'
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response):
        content = downloader.download()

    # Should return None (rejected as non-markdown)
    assert content is None
