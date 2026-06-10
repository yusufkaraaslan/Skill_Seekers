#!/usr/bin/env python3
"""Tests for signal_flow_analyzer.py (Godot signal-flow statistics)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_seekers.cli.signal_flow_analyzer import SignalFlowAnalyzer


class TestSignalFlowStatistics:
    def test_total_emissions_counts_every_emission(self):
        """Regression for CBA-02: total_emissions must iterate .values() (the
        emission lists), not .items() (which yields 2-tuples → always 2 per
        signal, decoupled from the real count)."""
        analyzer = SignalFlowAnalyzer({})
        analyzer.signal_connections = {}
        analyzer.files = []
        analyzer.signal_emissions.clear()
        # 5 + 5 = 10 emissions across 2 signals. The old .items() bug would
        # report 2 * 2 = 4.
        analyzer.signal_emissions["sig_a"] = [{} for _ in range(5)]
        analyzer.signal_emissions["sig_b"] = [{} for _ in range(5)]

        stats = analyzer._calculate_statistics()

        assert stats["total_emissions"] == 10
