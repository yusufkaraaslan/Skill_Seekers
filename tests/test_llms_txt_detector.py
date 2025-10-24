import pytest
from cli.llms_txt_detector import LlmsTxtDetector

def test_detect_llms_txt_variants():
    """Test detection of llms.txt file variants"""
    detector = LlmsTxtDetector("https://hono.dev/docs")

    # Mock responses
    variants = detector.detect()

    assert variants is not None
    assert 'url' in variants
    assert 'variant' in variants  # 'full', 'standard', 'small'
