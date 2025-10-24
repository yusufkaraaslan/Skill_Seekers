import pytest
from unittest.mock import patch, Mock
from cli.llms_txt_detector import LlmsTxtDetector

def test_detect_llms_txt_variants():
    """Test detection of llms.txt file variants"""
    detector = LlmsTxtDetector("https://hono.dev/docs")

    with patch('cli.llms_txt_detector.requests.head') as mock_head:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        variants = detector.detect()

        assert variants is not None
        assert variants['url'] == 'https://hono.dev/llms-full.txt'
        assert variants['variant'] == 'full'
        mock_head.assert_called()

def test_detect_no_llms_txt():
    """Test detection when no llms.txt file exists"""
    detector = LlmsTxtDetector("https://example.com/docs")

    with patch('cli.llms_txt_detector.requests.head') as mock_head:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        variants = detector.detect()

        assert variants is None
        assert mock_head.call_count == 3  # Should try all three variants

def test_url_parsing_with_complex_paths():
    """Test URL parsing handles non-standard paths correctly"""
    detector = LlmsTxtDetector("https://example.com/docs/v2/guide")

    with patch('cli.llms_txt_detector.requests.head') as mock_head:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        variants = detector.detect()

        assert variants is not None
        assert variants['url'] == 'https://example.com/llms-full.txt'
        mock_head.assert_called_with(
            'https://example.com/llms-full.txt',
            timeout=5,
            allow_redirects=True
        )
