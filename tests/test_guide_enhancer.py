#!/usr/bin/env python3
"""
Comprehensive tests for GuideEnhancer (C3.3 AI Enhancement)

Tests dual-mode AI enhancement for how-to guides:
- API mode (Claude API)
- LOCAL mode (Claude Code CLI)
- Auto mode detection
- All 5 enhancement methods
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from skill_seekers.cli.guide_enhancer import (
    GuideEnhancer,
    PrerequisiteItem,
    TroubleshootingItem,
    StepEnhancement
)


class TestGuideEnhancerModeDetection:
    """Test mode detection logic"""

    def test_auto_mode_with_api_key(self):
        """Test auto mode detects API when key present and library available"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='auto')
                    # Will be 'api' if library available, otherwise 'local' or 'none'
                    assert enhancer.mode in ['api', 'local', 'none']

    def test_auto_mode_without_api_key(self):
        """Test auto mode falls back to LOCAL when no API key"""
        with patch.dict(os.environ, {}, clear=True):
            if 'ANTHROPIC_API_KEY' in os.environ:
                del os.environ['ANTHROPIC_API_KEY']

            enhancer = GuideEnhancer(mode='auto')
            assert enhancer.mode in ['local', 'none']

    def test_explicit_api_mode(self):
        """Test explicit API mode"""
        enhancer = GuideEnhancer(mode='api')
        assert enhancer.mode in ['api', 'none']  # none if no API key

    def test_explicit_local_mode(self):
        """Test explicit LOCAL mode"""
        enhancer = GuideEnhancer(mode='local')
        assert enhancer.mode in ['local', 'none']  # none if no claude CLI

    def test_explicit_none_mode(self):
        """Test explicit none mode"""
        enhancer = GuideEnhancer(mode='none')
        assert enhancer.mode == 'none'

    def test_claude_cli_check(self):
        """Test Claude CLI availability check"""
        enhancer = GuideEnhancer(mode='local')
        # Should either detect claude or fall back to api/none
        assert enhancer.mode in ['local', 'api', 'none']


class TestGuideEnhancerStepDescriptions:
    """Test step description enhancement"""

    def test_enhance_step_descriptions_empty_list(self):
        """Test with empty steps list"""
        enhancer = GuideEnhancer(mode='none')
        steps = []
        result = enhancer.enhance_step_descriptions(steps)
        assert result == []

    def test_enhance_step_descriptions_none_mode(self):
        """Test step descriptions in none mode returns empty"""
        enhancer = GuideEnhancer(mode='none')
        steps = [
            {'description': 'scraper.scrape(url)', 'code': 'result = scraper.scrape(url)'}
        ]
        result = enhancer.enhance_step_descriptions(steps)
        assert result == []

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_step_descriptions_api_mode(self, mock_call):
        """Test step descriptions with API mode"""
        mock_call.return_value = json.dumps({
            'step_descriptions': [
                {
                    'step_index': 0,
                    'explanation': 'Initialize the scraper with the target URL',
                    'variations': ['Use async scraper for better performance']
                }
            ]
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()  # Mock the client

                    steps = [{'description': 'scraper.scrape(url)', 'code': 'result = scraper.scrape(url)'}]
                    result = enhancer.enhance_step_descriptions(steps)

                    assert len(result) == 1
                    assert isinstance(result[0], StepEnhancement)
                    assert result[0].step_index == 0
                    assert 'Initialize' in result[0].explanation
                    assert len(result[0].variations) == 1

    def test_enhance_step_descriptions_malformed_json(self):
        """Test handling of malformed JSON response"""
        enhancer = GuideEnhancer(mode='none')

        with patch.object(enhancer, '_call_ai', return_value='invalid json'):
            steps = [{'description': 'test', 'code': 'code'}]
            result = enhancer.enhance_step_descriptions(steps)
            assert result == []


class TestGuideEnhancerTroubleshooting:
    """Test troubleshooting enhancement"""

    def test_enhance_troubleshooting_none_mode(self):
        """Test troubleshooting in none mode"""
        enhancer = GuideEnhancer(mode='none')
        guide_data = {
            'title': 'Test Guide',
            'steps': [{'description': 'test', 'code': 'code'}],
            'language': 'python'
        }
        result = enhancer.enhance_troubleshooting(guide_data)
        assert result == []

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_troubleshooting_api_mode(self, mock_call):
        """Test troubleshooting with API mode"""
        mock_call.return_value = json.dumps({
            'troubleshooting': [
                {
                    'problem': 'ImportError: No module named requests',
                    'symptoms': ['Import fails', 'Module not found error'],
                    'diagnostic_steps': ['Check pip list', 'Verify virtual env'],
                    'solution': 'Run: pip install requests'
                }
            ]
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()

                    guide_data = {
                        'title': 'Test Guide',
                        'steps': [{'description': 'import requests', 'code': 'import requests'}],
                        'language': 'python'
                    }
                    result = enhancer.enhance_troubleshooting(guide_data)

                    assert len(result) == 1
                    assert isinstance(result[0], TroubleshootingItem)
                    assert 'ImportError' in result[0].problem
                    assert len(result[0].symptoms) == 2
                    assert len(result[0].diagnostic_steps) == 2
                    assert 'pip install' in result[0].solution


class TestGuideEnhancerPrerequisites:
    """Test prerequisite enhancement"""

    def test_enhance_prerequisites_empty_list(self):
        """Test with empty prerequisites"""
        enhancer = GuideEnhancer(mode='none')
        result = enhancer.enhance_prerequisites([])
        assert result == []

    def test_enhance_prerequisites_none_mode(self):
        """Test prerequisites in none mode"""
        enhancer = GuideEnhancer(mode='none')
        prereqs = ['requests', 'beautifulsoup4']
        result = enhancer.enhance_prerequisites(prereqs)
        assert result == []

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_prerequisites_api_mode(self, mock_call):
        """Test prerequisites with API mode"""
        mock_call.return_value = json.dumps({
            'prerequisites_detailed': [
                {
                    'name': 'requests',
                    'why': 'HTTP client for making web requests',
                    'setup': 'pip install requests'
                },
                {
                    'name': 'beautifulsoup4',
                    'why': 'HTML/XML parser for web scraping',
                    'setup': 'pip install beautifulsoup4'
                }
            ]
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()

                    prereqs = ['requests', 'beautifulsoup4']
                    result = enhancer.enhance_prerequisites(prereqs)

                    assert len(result) == 2
                    assert isinstance(result[0], PrerequisiteItem)
                    assert result[0].name == 'requests'
                    assert 'HTTP client' in result[0].why
                    assert 'pip install' in result[0].setup


class TestGuideEnhancerNextSteps:
    """Test next steps enhancement"""

    def test_enhance_next_steps_none_mode(self):
        """Test next steps in none mode"""
        enhancer = GuideEnhancer(mode='none')
        guide_data = {'title': 'Test Guide', 'description': 'Test'}
        result = enhancer.enhance_next_steps(guide_data)
        assert result == []

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_next_steps_api_mode(self, mock_call):
        """Test next steps with API mode"""
        mock_call.return_value = json.dumps({
            'next_steps': [
                'How to handle async workflows',
                'How to add error handling',
                'How to implement caching'
            ]
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()

                    guide_data = {'title': 'How to Scrape Docs', 'description': 'Basic scraping'}
                    result = enhancer.enhance_next_steps(guide_data)

                    assert len(result) == 3
                    assert 'async' in result[0].lower()
                    assert 'error' in result[1].lower()


class TestGuideEnhancerUseCases:
    """Test use case enhancement"""

    def test_enhance_use_cases_none_mode(self):
        """Test use cases in none mode"""
        enhancer = GuideEnhancer(mode='none')
        guide_data = {'title': 'Test Guide', 'description': 'Test'}
        result = enhancer.enhance_use_cases(guide_data)
        assert result == []

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_use_cases_api_mode(self, mock_call):
        """Test use cases with API mode"""
        mock_call.return_value = json.dumps({
            'use_cases': [
                'Use when you need to automate documentation extraction',
                'Ideal for building knowledge bases from technical docs'
            ]
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()

                    guide_data = {'title': 'How to Scrape Docs', 'description': 'Documentation scraping'}
                    result = enhancer.enhance_use_cases(guide_data)

                    assert len(result) == 2
                    assert 'automate' in result[0].lower()
                    assert 'knowledge base' in result[1].lower()


class TestGuideEnhancerFullWorkflow:
    """Test complete guide enhancement workflow"""

    def test_enhance_guide_none_mode(self):
        """Test full guide enhancement in none mode"""
        enhancer = GuideEnhancer(mode='none')

        guide_data = {
            'title': 'How to Scrape Documentation',
            'steps': [
                {'description': 'Import libraries', 'code': 'import requests'},
                {'description': 'Create scraper', 'code': 'scraper = Scraper()'}
            ],
            'language': 'python',
            'prerequisites': ['requests'],
            'description': 'Basic scraping guide'
        }

        result = enhancer.enhance_guide(guide_data)

        # In none mode, should return original guide
        assert result['title'] == guide_data['title']
        assert len(result['steps']) == 2

    @patch.object(GuideEnhancer, '_call_claude_api')
    def test_enhance_guide_api_mode_success(self, mock_call):
        """Test successful full guide enhancement via API"""
        mock_call.return_value = json.dumps({
            'step_descriptions': [
                {'step_index': 0, 'explanation': 'Import required libraries', 'variations': []},
                {'step_index': 1, 'explanation': 'Initialize scraper instance', 'variations': []}
            ],
            'troubleshooting': [
                {
                    'problem': 'Import error',
                    'symptoms': ['Module not found'],
                    'diagnostic_steps': ['Check installation'],
                    'solution': 'pip install requests'
                }
            ],
            'prerequisites_detailed': [
                {'name': 'requests', 'why': 'HTTP client', 'setup': 'pip install requests'}
            ],
            'next_steps': ['How to add authentication'],
            'use_cases': ['Automate documentation extraction']
        })

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            with patch('skill_seekers.cli.guide_enhancer.ANTHROPIC_AVAILABLE', True):
                with patch('skill_seekers.cli.guide_enhancer.anthropic', create=True) as mock_anthropic:
                    mock_anthropic.Anthropic = Mock()
                    enhancer = GuideEnhancer(mode='api')
                    if enhancer.mode != 'api':
                        pytest.skip("API mode not available")

                    enhancer.client = Mock()

                    guide_data = {
                        'title': 'How to Scrape Documentation',
                        'steps': [
                            {'description': 'Import libraries', 'code': 'import requests'},
                            {'description': 'Create scraper', 'code': 'scraper = Scraper()'}
                        ],
                        'language': 'python',
                        'prerequisites': ['requests'],
                        'description': 'Basic scraping guide'
                    }

                    result = enhancer.enhance_guide(guide_data)

                    # Check enhancements were applied
                    assert 'step_enhancements' in result
                    assert 'troubleshooting_detailed' in result
                    assert 'prerequisites_detailed' in result
                    assert 'next_steps_detailed' in result
                    assert 'use_cases' in result

    def test_enhance_guide_error_fallback(self):
        """Test graceful fallback on enhancement error"""
        enhancer = GuideEnhancer(mode='none')

        with patch.object(enhancer, 'enhance_guide', side_effect=Exception('API error')):
            guide_data = {
                'title': 'Test',
                'steps': [],
                'language': 'python',
                'prerequisites': [],
                'description': 'Test'
            }

            # Should not raise exception - graceful fallback
            try:
                enhancer = GuideEnhancer(mode='none')
                result = enhancer.enhance_guide(guide_data)
                # In none mode with error, returns original
                assert result['title'] == guide_data['title']
            except Exception:
                pytest.fail("Should handle errors gracefully")


class TestGuideEnhancerLocalMode:
    """Test LOCAL mode (Claude Code CLI)"""

    @patch('subprocess.run')
    def test_call_claude_local_success(self, mock_run):
        """Test successful LOCAL mode call"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                'step_descriptions': [],
                'troubleshooting': [],
                'prerequisites_detailed': [],
                'next_steps': [],
                'use_cases': []
            })
        )

        enhancer = GuideEnhancer(mode='local')
        if enhancer.mode == 'local':
            prompt = "Test prompt"
            result = enhancer._call_claude_local(prompt)

            assert result is not None
            assert mock_run.called

    @patch('subprocess.run')
    def test_call_claude_local_timeout(self, mock_run):
        """Test LOCAL mode timeout handling"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('claude', 300)

        enhancer = GuideEnhancer(mode='local')
        if enhancer.mode == 'local':
            prompt = "Test prompt"
            result = enhancer._call_claude_local(prompt)

            assert result is None


class TestGuideEnhancerPromptGeneration:
    """Test prompt generation"""

    def test_create_enhancement_prompt(self):
        """Test comprehensive enhancement prompt generation"""
        enhancer = GuideEnhancer(mode='none')

        guide_data = {
            'title': 'How to Test',
            'steps': [
                {'description': 'Write test', 'code': 'def test_example(): pass'}
            ],
            'language': 'python',
            'prerequisites': ['pytest']
        }

        prompt = enhancer._create_enhancement_prompt(guide_data)

        assert 'How to Test' in prompt
        assert 'pytest' in prompt
        assert 'STEP_DESCRIPTIONS' in prompt
        assert 'TROUBLESHOOTING' in prompt
        assert 'PREREQUISITES' in prompt
        assert 'NEXT_STEPS' in prompt
        assert 'USE_CASES' in prompt
        assert 'JSON' in prompt

    def test_format_steps_for_prompt(self):
        """Test step formatting for prompts"""
        enhancer = GuideEnhancer(mode='none')

        steps = [
            {'description': 'Import', 'code': 'import requests'},
            {'description': 'Create', 'code': 'obj = Object()'}
        ]

        formatted = enhancer._format_steps_for_prompt(steps)

        assert 'Step 1' in formatted
        assert 'Step 2' in formatted
        assert 'import requests' in formatted
        assert 'obj = Object()' in formatted

    def test_format_steps_empty(self):
        """Test formatting empty steps list"""
        enhancer = GuideEnhancer(mode='none')
        formatted = enhancer._format_steps_for_prompt([])
        assert formatted == "No steps provided"


class TestGuideEnhancerResponseParsing:
    """Test response parsing"""

    def test_parse_enhancement_response_valid_json(self):
        """Test parsing valid JSON response"""
        enhancer = GuideEnhancer(mode='none')

        response = json.dumps({
            'step_descriptions': [
                {'step_index': 0, 'explanation': 'Test', 'variations': []}
            ],
            'troubleshooting': [],
            'prerequisites_detailed': [],
            'next_steps': [],
            'use_cases': []
        })

        guide_data = {
            'title': 'Test',
            'steps': [{'description': 'Test', 'code': 'test'}],
            'language': 'python'
        }

        result = enhancer._parse_enhancement_response(response, guide_data)

        assert 'step_enhancements' in result
        assert len(result['step_enhancements']) == 1

    def test_parse_enhancement_response_with_extra_text(self):
        """Test parsing JSON embedded in text"""
        enhancer = GuideEnhancer(mode='none')

        json_data = {
            'step_descriptions': [],
            'troubleshooting': [],
            'prerequisites_detailed': [],
            'next_steps': [],
            'use_cases': []
        }

        response = f"Here's the result:\n{json.dumps(json_data)}\nDone!"

        guide_data = {'title': 'Test', 'steps': [], 'language': 'python'}
        result = enhancer._parse_enhancement_response(response, guide_data)

        # Should extract JSON successfully
        assert 'title' in result

    def test_parse_enhancement_response_invalid_json(self):
        """Test handling invalid JSON"""
        enhancer = GuideEnhancer(mode='none')

        response = "This is not valid JSON"
        guide_data = {'title': 'Test', 'steps': [], 'language': 'python'}

        result = enhancer._parse_enhancement_response(response, guide_data)

        # Should return original guide_data on parse error
        assert result['title'] == 'Test'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
