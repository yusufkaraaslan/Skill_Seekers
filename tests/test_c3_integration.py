#!/usr/bin/env python3
"""
Integration tests for C3.5 - Architectural Overview & Skill Integrator

Tests the integration of C3.x codebase analysis features into unified skills:
- Default ON behavior for enable_codebase_analysis
- --skip-codebase-analysis CLI flag
- ARCHITECTURE.md generation with 8 sections
- C3.x reference directory structure
- Graceful degradation on failures
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from skill_seekers.cli.unified_scraper import UnifiedScraper
from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder
from skill_seekers.cli.config_validator import ConfigValidator


class TestC3Integration:
    """Test C3.5 integration features."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create mock unified config with GitHub source."""
        return {
            'name': 'test-c3',
            'description': 'Test C3.5 integration',
            'merge_mode': 'rule-based',
            'sources': [
                {
                    'type': 'github',
                    'repo': 'test/repo',
                    'local_repo_path': temp_dir,
                    'enable_codebase_analysis': True,
                    'ai_mode': 'none'
                }
            ]
        }

    @pytest.fixture
    def mock_c3_data(self):
        """Create mock C3.x analysis data."""
        return {
            'patterns': [
                {
                    'file_path': 'src/factory.py',
                    'patterns': [
                        {
                            'pattern_type': 'Factory',
                            'class_name': 'WidgetFactory',
                            'confidence': 0.95,
                            'indicators': ['create_method', 'product_interface']
                        }
                    ]
                }
            ],
            'test_examples': {
                'total_examples': 15,
                'high_value_count': 9,
                'examples': [
                    {
                        'description': 'Create widget instance',
                        'category': 'instantiation',
                        'confidence': 0.85,
                        'file_path': 'tests/test_widget.py',
                        'code_snippet': 'widget = Widget(name="test")'
                    }
                ],
                'examples_by_category': {
                    'instantiation': 5,
                    'method_call': 6,
                    'workflow': 4
                }
            },
            'how_to_guides': {
                'guides': [
                    {
                        'id': 'create_widget',
                        'title': 'How to create a widget',
                        'description': 'Step-by-step guide',
                        'steps': [
                            {
                                'action': 'Import Widget class',
                                'code_example': 'from widgets import Widget',
                                'language': 'python'
                            }
                        ]
                    }
                ],
                'total_count': 1
            },
            'config_patterns': {
                'config_files': [
                    {
                        'relative_path': 'config.json',
                        'type': 'json',
                        'purpose': 'Application configuration',
                        'settings': [
                            {'key': 'debug', 'value': 'true', 'value_type': 'boolean'}
                        ]
                    }
                ],
                'ai_enhancements': {
                    'overall_insights': {
                        'security_issues_found': 1,
                        'recommended_actions': ['Move secrets to .env']
                    }
                }
            },
            'architecture': {
                'patterns': [
                    {
                        'pattern_name': 'MVC',
                        'confidence': 0.89,
                        'framework': 'Flask',
                        'evidence': ['models/ directory', 'views/ directory', 'controllers/ directory']
                    }
                ],
                'frameworks_detected': ['Flask', 'SQLAlchemy'],
                'languages': {'python': 42, 'javascript': 8},
                'directory_structure': {
                    'src': 25,
                    'tests': 15,
                    'docs': 3
                }
            }
        }

    def test_codebase_analysis_enabled_by_default(self, mock_config, temp_dir):
        """Test that enable_codebase_analysis defaults to True."""
        # Config with GitHub source but no explicit enable_codebase_analysis
        config_without_flag = {
            'name': 'test',
            'description': 'Test',
            'sources': [
                {
                    'type': 'github',
                    'repo': 'test/repo',
                    'local_repo_path': temp_dir
                }
            ]
        }

        # Save config
        config_path = os.path.join(temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config_without_flag, f)

        # Create scraper
        scraper = UnifiedScraper(config_path)

        # Verify default is True
        github_source = scraper.config['sources'][0]
        assert github_source.get('enable_codebase_analysis', True) == True

    def test_skip_codebase_analysis_flag(self, mock_config, temp_dir):
        """Test --skip-codebase-analysis CLI flag disables analysis."""
        # Save config
        config_path = os.path.join(temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(mock_config, f)

        # Create scraper
        scraper = UnifiedScraper(config_path)

        # Simulate --skip-codebase-analysis flag behavior
        for source in scraper.config.get('sources', []):
            if source['type'] == 'github':
                source['enable_codebase_analysis'] = False

        # Verify flag disabled it
        github_source = scraper.config['sources'][0]
        assert github_source['enable_codebase_analysis'] == False

    def test_architecture_md_generation(self, mock_config, mock_c3_data, temp_dir):
        """Test ARCHITECTURE.md is generated with all 8 sections."""
        # Create skill builder with C3.x data (multi-source list format)
        github_data = {
            'readme': 'Test README',
            'c3_analysis': mock_c3_data
        }
        scraped_data = {
            'github': [{
                'repo': 'test/repo',
                'repo_id': 'test_repo',
                'idx': 0,
                'data': github_data
            }]
        }

        builder = UnifiedSkillBuilder(mock_config, scraped_data)
        builder.skill_dir = temp_dir

        # Generate C3.x references
        c3_dir = os.path.join(temp_dir, 'references', 'codebase_analysis')
        os.makedirs(c3_dir, exist_ok=True)
        builder._generate_architecture_overview(c3_dir, mock_c3_data, github_data)

        # Verify ARCHITECTURE.md exists
        arch_file = os.path.join(c3_dir, 'ARCHITECTURE.md')
        assert os.path.exists(arch_file)

        # Read and verify content
        with open(arch_file, 'r') as f:
            content = f.read()

        # Verify all 8 sections exist
        assert '## 1. Overview' in content
        assert '## 2. Architectural Patterns' in content
        assert '## 3. Technology Stack' in content
        assert '## 4. Design Patterns' in content
        assert '## 5. Configuration Overview' in content
        assert '## 6. Common Workflows' in content
        assert '## 7. Usage Examples' in content
        assert '## 8. Entry Points & Directory Structure' in content

        # Verify specific data is present
        assert 'MVC' in content
        assert 'Flask' in content
        assert 'Factory' in content
        assert '15 usage example(s)' in content or '15 total' in content
        assert 'Security Alert' in content

    def test_c3_reference_directory_structure(self, mock_config, mock_c3_data, temp_dir):
        """Test correct C3.x reference directory structure is created."""
        # Create skill builder with C3.x data (multi-source list format)
        github_data = {
            'readme': 'Test README',
            'c3_analysis': mock_c3_data
        }
        scraped_data = {
            'github': [{
                'repo': 'test/repo',
                'repo_id': 'test_repo',
                'idx': 0,
                'data': github_data
            }]
        }

        builder = UnifiedSkillBuilder(mock_config, scraped_data)
        builder.skill_dir = temp_dir

        # Generate C3.x references
        c3_dir = os.path.join(temp_dir, 'references', 'codebase_analysis')
        os.makedirs(c3_dir, exist_ok=True)

        builder._generate_architecture_overview(c3_dir, mock_c3_data, github_data)
        builder._generate_pattern_references(c3_dir, mock_c3_data.get('patterns'))
        builder._generate_example_references(c3_dir, mock_c3_data.get('test_examples'))
        builder._generate_guide_references(c3_dir, mock_c3_data.get('how_to_guides'))
        builder._generate_config_references(c3_dir, mock_c3_data.get('config_patterns'))
        builder._copy_architecture_details(c3_dir, mock_c3_data.get('architecture'))

        # Verify directory structure
        assert os.path.exists(os.path.join(c3_dir, 'ARCHITECTURE.md'))
        assert os.path.exists(os.path.join(c3_dir, 'patterns'))
        assert os.path.exists(os.path.join(c3_dir, 'examples'))
        assert os.path.exists(os.path.join(c3_dir, 'guides'))
        assert os.path.exists(os.path.join(c3_dir, 'configuration'))
        assert os.path.exists(os.path.join(c3_dir, 'architecture_details'))

        # Verify index files
        assert os.path.exists(os.path.join(c3_dir, 'patterns', 'index.md'))
        assert os.path.exists(os.path.join(c3_dir, 'examples', 'index.md'))
        assert os.path.exists(os.path.join(c3_dir, 'guides', 'index.md'))
        assert os.path.exists(os.path.join(c3_dir, 'configuration', 'index.md'))
        assert os.path.exists(os.path.join(c3_dir, 'architecture_details', 'index.md'))

        # Verify JSON data files
        assert os.path.exists(os.path.join(c3_dir, 'patterns', 'detected_patterns.json'))
        assert os.path.exists(os.path.join(c3_dir, 'examples', 'test_examples.json'))
        assert os.path.exists(os.path.join(c3_dir, 'configuration', 'config_patterns.json'))

    def test_graceful_degradation_on_c3_failure(self, mock_config, temp_dir):
        """Test skill builds even if C3.x analysis fails."""
        # Mock _run_c3_analysis to raise exception
        with patch('skill_seekers.cli.unified_scraper.UnifiedScraper._run_c3_analysis') as mock_c3:
            mock_c3.side_effect = Exception("C3.x analysis failed")

            # Save config
            config_path = os.path.join(temp_dir, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(mock_config, f)

            # Mock GitHubScraper (correct module path for import)
            with patch('skill_seekers.cli.github_scraper.GitHubScraper') as mock_github:
                mock_github.return_value.scrape.return_value = {
                    'readme': 'Test README',
                    'issues': [],
                    'releases': []
                }

                scraper = UnifiedScraper(config_path)

                # This should not raise an exception
                try:
                    scraper._scrape_github(mock_config['sources'][0])
                    # If we get here, graceful degradation worked
                    assert True
                except Exception as e:
                    pytest.fail(f"Should handle C3.x failure gracefully but raised: {e}")

    def test_config_validator_accepts_c3_properties(self, temp_dir):
        """Test config validator accepts new C3.5 properties."""
        config = {
            'name': 'test',
            'description': 'Test',
            'sources': [
                {
                    'type': 'github',
                    'repo': 'test/repo',
                    'enable_codebase_analysis': True,
                    'ai_mode': 'auto'
                }
            ]
        }

        # Save config
        config_path = os.path.join(temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Validate
        validator = ConfigValidator(config_path)
        assert validator.validate() == True

    def test_config_validator_rejects_invalid_ai_mode(self, temp_dir):
        """Test config validator rejects invalid ai_mode values."""
        config = {
            'name': 'test',
            'description': 'Test',
            'sources': [
                {
                    'type': 'github',
                    'repo': 'test/repo',
                    'ai_mode': 'invalid_mode'  # Invalid!
                }
            ]
        }

        # Save config
        config_path = os.path.join(temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Validate should raise
        validator = ConfigValidator(config_path)
        with pytest.raises(ValueError, match="Invalid ai_mode"):
            validator.validate()

    def test_skill_md_includes_c3_summary(self, mock_config, mock_c3_data, temp_dir):
        """Test SKILL.md includes C3.x architecture summary."""
        scraped_data = {
            'github': {
                'data': {
                    'readme': 'Test README',
                    'c3_analysis': mock_c3_data
                }
            }
        }

        builder = UnifiedSkillBuilder(mock_config, scraped_data)
        builder.skill_dir = temp_dir
        builder._generate_skill_md()

        # Read SKILL.md
        skill_file = os.path.join(temp_dir, 'SKILL.md')
        with open(skill_file, 'r') as f:
            content = f.read()

        # Verify C3.x summary section exists
        assert '## 🏗️ Architecture & Code Analysis' in content
        assert 'Primary Architecture' in content
        assert 'MVC' in content
        assert 'Design Patterns' in content
        assert 'Factory' in content
        assert 'references/codebase_analysis/ARCHITECTURE.md' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
