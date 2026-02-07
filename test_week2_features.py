#!/usr/bin/env python3
"""
Quick validation script for Week 2 features.
Run this to verify all new capabilities are working.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_vector_databases():
    """Test all 4 vector database adaptors."""
    from skill_seekers.cli.adaptors import get_adaptor
    import json

    print("📦 Testing vector database adaptors...")

    # Create minimal test data
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / 'test_skill'
        skill_dir.mkdir()
        (skill_dir / 'SKILL.md').write_text('# Test\n\nContent.')

        targets = ['weaviate', 'chroma', 'faiss', 'qdrant']
        for target in targets:
            try:
                adaptor = get_adaptor(target)
                package_path = adaptor.package(skill_dir, Path(tmpdir))
                assert package_path.exists(), f"{target} package not created"
                print(f"   ✅ {target.capitalize()}")
            except Exception as e:
                print(f"   ❌ {target.capitalize()}: {e}")
                return False

    return True


def test_streaming():
    """Test streaming ingestion."""
    from skill_seekers.cli.streaming_ingest import StreamingIngester

    print("📈 Testing streaming ingestion...")

    try:
        large_content = "Test content. " * 500
        ingester = StreamingIngester(chunk_size=1000, chunk_overlap=100)

        chunks = list(ingester.chunk_document(
            large_content,
            {'source': 'test'}
        ))

        assert len(chunks) > 5, "Expected multiple chunks"
        assert all(len(chunk[0]) <= 1100 for chunk in chunks), "Chunk too large"

        print(f"   ✅ Chunked {len(large_content)} chars into {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"   ❌ Streaming test failed: {e}")
        return False


def test_incremental():
    """Test incremental updates."""
    from skill_seekers.cli.incremental_updater import IncrementalUpdater
    import time

    print("⚡ Testing incremental updates...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / 'test_skill'
            skill_dir.mkdir()

            # Create references directory
            refs_dir = skill_dir / 'references'
            refs_dir.mkdir()

            # Create initial version
            (skill_dir / 'SKILL.md').write_text('# V1\n\nInitial content.')
            (refs_dir / 'guide.md').write_text('# Guide\n\nInitial guide.')

            updater = IncrementalUpdater(skill_dir)
            updater.current_versions = updater._scan_documents()  # Scan before saving
            updater.save_current_versions()

            # Small delay to ensure different timestamps
            time.sleep(0.01)

            # Make changes
            (skill_dir / 'SKILL.md').write_text('# V2\n\nUpdated content.')
            (refs_dir / 'new_ref.md').write_text('# New Reference\n\nNew documentation.')

            # Detect changes (loads previous versions internally)
            updater2 = IncrementalUpdater(skill_dir)
            changes = updater2.detect_changes()

            # Verify we have changes
            assert changes.has_changes, "No changes detected"
            assert len(changes.added) > 0, f"New file not detected"
            assert len(changes.modified) > 0, f"Modified file not detected"

            print(f"   ✅ Detected {len(changes.added)} added, {len(changes.modified)} modified")
            return True
    except Exception as e:
        print(f"   ❌ Incremental test failed: {e}")
        return False


def test_multilang():
    """Test multi-language support."""
    from skill_seekers.cli.multilang_support import (
        LanguageDetector,
        MultiLanguageManager
    )

    print("🌍 Testing multi-language support...")

    try:
        detector = LanguageDetector()

        # Test language detection
        en_text = "This is an English document about programming."
        es_text = "Este es un documento en español sobre programación."

        en_detected = detector.detect(en_text)
        es_detected = detector.detect(es_text)

        assert en_detected.code == 'en', f"Expected 'en', got '{en_detected.code}'"
        assert es_detected.code == 'es', f"Expected 'es', got '{es_detected.code}'"

        # Test filename detection
        assert detector.detect_from_filename('README.en.md') == 'en'
        assert detector.detect_from_filename('guide.es.md') == 'es'

        # Test manager
        manager = MultiLanguageManager()
        manager.add_document('doc.md', en_text, {})
        manager.add_document('doc.es.md', es_text, {})

        languages = manager.get_languages()
        assert 'en' in languages and 'es' in languages

        print(f"   ✅ Detected {len(languages)} languages")
        return True
    except Exception as e:
        print(f"   ❌ Multi-language test failed: {e}")
        return False


def test_embeddings():
    """Test embedding pipeline."""
    from skill_seekers.cli.embedding_pipeline import (
        EmbeddingPipeline,
        EmbeddingConfig
    )

    print("💰 Testing embedding pipeline...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = EmbeddingConfig(
                provider='local',
                model='test-model',
                dimension=64,
                batch_size=10,
                cache_dir=Path(tmpdir)
            )

            pipeline = EmbeddingPipeline(config)

            # Test generation (first run)
            texts = ['doc1', 'doc2', 'doc3']
            result1 = pipeline.generate_batch(texts, show_progress=False)

            assert len(result1.embeddings) == 3, "Expected 3 embeddings"
            assert len(result1.embeddings[0]) == 64, "Wrong dimension"
            assert result1.generated_count == 3, "Should generate all on first run"

            # Test caching (second run with same texts)
            result2 = pipeline.generate_batch(texts, show_progress=False)

            assert result2.cached_count == 3, "Caching not working"
            assert result2.generated_count == 0, "Should not generate on second run"

            print(f"   ✅ First run: {result1.generated_count} generated")
            print(f"   ✅ Second run: {result2.cached_count} cached (100% cache hit)")
            return True
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        return False


def test_quality():
    """Test quality metrics."""
    from skill_seekers.cli.quality_metrics import QualityAnalyzer

    print("📊 Testing quality metrics...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / 'test_skill'
            skill_dir.mkdir()

            # Create test skill
            (skill_dir / 'SKILL.md').write_text('# Test Skill\n\nContent.')

            refs_dir = skill_dir / 'references'
            refs_dir.mkdir()
            (refs_dir / 'guide.md').write_text('# Guide\n\nGuide content.')

            # Analyze quality
            analyzer = QualityAnalyzer(skill_dir)
            report = analyzer.generate_report()

            assert report.overall_score.total_score > 0, "Score is 0"
            assert report.overall_score.grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
            assert len(report.metrics) == 4, "Expected 4 metrics"

            print(f"   ✅ Grade: {report.overall_score.grade} ({report.overall_score.total_score:.1f}/100)")
            return True
    except Exception as e:
        print(f"   ❌ Quality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("🧪 Week 2 Feature Validation")
    print("=" * 70)
    print()

    tests = [
        ("Vector Databases", test_vector_databases),
        ("Streaming Ingestion", test_streaming),
        ("Incremental Updates", test_incremental),
        ("Multi-Language", test_multilang),
        ("Embedding Pipeline", test_embeddings),
        ("Quality Metrics", test_quality),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            failed += 1
        print()

    print("=" * 70)
    print(f"📊 Results: {passed}/{len(tests)} passed")

    if failed == 0:
        print("🎉 All Week 2 features validated successfully!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
