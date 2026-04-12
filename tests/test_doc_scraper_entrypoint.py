from skill_seekers.cli.doc_scraper import _run_scraping


class DummyConverter:
    def __init__(self):
        self.checkpoint_loaded = False
        self.checkpoint_cleared = False
        self.scrape_all_called = False
        self.build_skill_called = False
        self.save_checkpoint_called = False

    def checkpoint_exists(self):
        return False

    def load_checkpoint(self):
        self.checkpoint_loaded = True

    def clear_checkpoint(self):
        self.checkpoint_cleared = True

    def scrape_all(self):
        self.scrape_all_called = True

    def build_skill(self):
        self.build_skill_called = True

    def save_checkpoint(self):
        self.save_checkpoint_called = True


def test_run_scraping_uses_scrape_all(monkeypatch):
    """Regression test for CLI entrypoint calling a nonexistent scrape() method."""
    converter = DummyConverter()

    monkeypatch.setattr(
        "skill_seekers.cli.doc_scraper.DocToSkillConverter",
        lambda config: converter,
    )

    result = _run_scraping({"name": "demo", "base_url": "https://example.com"})

    assert result is converter
    assert converter.scrape_all_called is True
    assert converter.build_skill_called is True


def test_run_scraping_saves_checkpoint_on_keyboard_interrupt(monkeypatch):
    """KeyboardInterrupt during scrape_all() should preserve resume state."""
    converter = DummyConverter()

    def raise_interrupt():
        raise KeyboardInterrupt

    converter.scrape_all = raise_interrupt

    monkeypatch.setattr(
        "skill_seekers.cli.doc_scraper.DocToSkillConverter",
        lambda config: converter,
    )

    result = _run_scraping({"name": "demo", "base_url": "https://example.com"})

    assert result is None
    assert converter.save_checkpoint_called is True
    assert converter.build_skill_called is False