import pytest
from cli.llms_txt_downloader import LlmsTxtDownloader

def test_download_llms_txt():
    """Test downloading llms.txt content"""
    downloader = LlmsTxtDownloader("https://hono.dev/llms-full.txt")

    content = downloader.download()

    assert content is not None
    assert len(content) > 100  # Should have substantial content
    assert isinstance(content, str)
