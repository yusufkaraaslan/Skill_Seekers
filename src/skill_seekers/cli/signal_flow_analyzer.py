"""
Signal Flow Analyzer for Godot Projects (C3.10)

Analyzes signal connections, emissions, and event flow patterns
in Godot GDScript projects.
"""

import json
from pathlib import Path
from typing import Any
from collections import defaultdict


class SignalFlowAnalyzer:
    """Analyzes signal flow patterns in Godot projects."""

    def __init__(self, analysis_results: dict[str, Any]):
        """
        Initialize with code analysis results.

        Args:
            analysis_results: Dict containing analyzed files with signal data
        """
        self.files = analysis_results.get("files", [])
        self.signal_declarations = {}  # signal_name -> [file, params, docs]
        self.signal_connections = defaultdict(list)  # signal -> [handlers]
        self.signal_emissions = defaultdict(list)  # signal -> [locations]
        self.signal_flow_chains = []  # [(source, signal, target)]

    def analyze(self) -> dict[str, Any]:
        """
        Perform signal flow analysis.

        Returns:
            Dict containing signal flow analysis results
        """
        self._extract_signals()
        self._extract_connections()
        self._extract_emissions()
        self._build_flow_chains()
        self._detect_patterns()

        return {
            "signal_declarations": self.signal_declarations,
            "signal_connections": dict(self.signal_connections),
            "signal_emissions": dict(self.signal_emissions),
            "signal_flow_chains": self.signal_flow_chains,
            "patterns": self.patterns,
            "statistics": self._calculate_statistics(),
        }

    def _extract_signals(self):
        """Extract all signal declarations."""
        for file_data in self.files:
            if file_data.get("language") != "GDScript":
                continue

            file_path = file_data["file"]
            signals = file_data.get("signals", [])

            for signal in signals:
                signal_name = signal["name"]
                self.signal_declarations[signal_name] = {
                    "file": file_path,
                    "parameters": signal.get("parameters", ""),
                    "documentation": signal.get("documentation"),
                    "line_number": signal.get("line_number", 0),
                }

    def _extract_connections(self):
        """Extract all signal connections (.connect() calls)."""
        for file_data in self.files:
            if file_data.get("language") != "GDScript":
                continue

            file_path = file_data["file"]
            connections = file_data.get("signal_connections", [])

            for conn in connections:
                signal_path = conn["signal"]
                handler = conn["handler"]
                line = conn.get("line_number", 0)

                self.signal_connections[signal_path].append(
                    {"handler": handler, "file": file_path, "line": line}
                )

    def _extract_emissions(self):
        """Extract all signal emissions (.emit() calls)."""
        for file_data in self.files:
            if file_data.get("language") != "GDScript":
                continue

            file_path = file_data["file"]
            emissions = file_data.get("signal_emissions", [])

            for emission in emissions:
                signal_path = emission["signal"]
                args = emission.get("arguments", "")
                line = emission.get("line_number", 0)

                self.signal_emissions[signal_path].append(
                    {"arguments": args, "file": file_path, "line": line}
                )

    def _build_flow_chains(self):
        """Build signal flow chains (A emits -> B connects)."""
        # For each emission, find corresponding connections
        for signal, emissions in self.signal_emissions.items():
            if signal in self.signal_connections:
                connections = self.signal_connections[signal]

                for emission in emissions:
                    for connection in connections:
                        self.signal_flow_chains.append(
                            {
                                "signal": signal,
                                "source": emission["file"],
                                "target": connection["file"],
                                "handler": connection["handler"],
                            }
                        )

    def _detect_patterns(self):
        """Detect common signal usage patterns."""
        self.patterns = {}

        # EventBus pattern - signals on autoload/global scripts
        eventbus_signals = [
            sig
            for sig, data in self.signal_declarations.items()
            if "EventBus" in data["file"]
            or "autoload" in data["file"].lower()
            or "global" in data["file"].lower()
        ]

        if eventbus_signals:
            self.patterns["EventBus Pattern"] = {
                "detected": True,
                "confidence": 0.9,
                "signals": eventbus_signals,
                "description": "Centralized event system using global signals",
            }

        # Observer pattern - signals with multiple connections
        multi_connected = {
            sig: len(conns)
            for sig, conns in self.signal_connections.items()
            if len(conns) >= 3
        }

        if multi_connected:
            self.patterns["Observer Pattern"] = {
                "detected": True,
                "confidence": 0.85,
                "signals": list(multi_connected.keys()),
                "description": f"{len(multi_connected)} signals with 3+ observers",
            }

        # Event chains - signals that trigger other signals
        chain_length = len(self.signal_flow_chains)
        if chain_length > 0:
            self.patterns["Event Chains"] = {
                "detected": True,
                "confidence": 0.8,
                "chain_count": chain_length,
                "description": "Signals that trigger other signal emissions",
            }

    def _calculate_statistics(self) -> dict[str, Any]:
        """Calculate signal usage statistics."""
        total_signals = len(self.signal_declarations)
        total_connections = sum(
            len(conns) for conns in self.signal_connections.values()
        )
        total_emissions = sum(len(emits) for emits in self.signal_emissions.items())

        # Find most connected signals
        most_connected = sorted(
            self.signal_connections.items(), key=lambda x: len(x[1]), reverse=True
        )[:5]

        # Find most emitted signals
        most_emitted = sorted(
            self.signal_emissions.items(), key=lambda x: len(x[1]), reverse=True
        )[:5]

        # Signal density (signals per GDScript file)
        gdscript_files = sum(
            1 for f in self.files if f.get("language") == "GDScript"
        )
        signal_density = (
            total_signals / gdscript_files if gdscript_files > 0 else 0
        )

        return {
            "total_signals": total_signals,
            "total_connections": total_connections,
            "total_emissions": total_emissions,
            "signal_density": round(signal_density, 2),
            "gdscript_files": gdscript_files,
            "most_connected_signals": [
                {"signal": sig, "connection_count": len(conns)}
                for sig, conns in most_connected
            ],
            "most_emitted_signals": [
                {"signal": sig, "emission_count": len(emits)}
                for sig, emits in most_emitted
            ],
        }

    def generate_signal_flow_diagram(self) -> str:
        """
        Generate a Mermaid diagram of signal flow.

        Returns:
            Mermaid diagram as string
        """
        lines = ["```mermaid", "graph LR"]

        # Add signal nodes
        for i, signal in enumerate(self.signal_declarations.keys()):
            safe_signal = signal.replace("_", "")
            lines.append(f"    {safe_signal}[({signal})]")

        # Add flow connections
        for chain in self.signal_flow_chains[:20]:  # Limit to prevent huge diagrams
            signal = chain["signal"].replace("_", "")
            source = Path(chain["source"]).stem.replace("_", "")
            target = Path(chain["target"]).stem.replace("_", "")
            handler = chain["handler"].replace("_", "")

            lines.append(f"    {source} -->|emit| {signal}")
            lines.append(f"    {signal} -->|{handler}| {target}")

        lines.append("```")
        return "\n".join(lines)

    def save_analysis(self, output_dir: Path):
        """
        Save signal flow analysis to files.

        Args:
            output_dir: Directory to save analysis results
        """
        signal_dir = output_dir / "signals"
        signal_dir.mkdir(parents=True, exist_ok=True)

        analysis = self.analyze()

        # Save JSON analysis
        with open(signal_dir / "signal_flow.json", "w") as f:
            json.dump(analysis, f, indent=2)

        # Save signal reference markdown
        self._generate_signal_reference(signal_dir, analysis)

        # Save flow diagram
        diagram = self.generate_signal_flow_diagram()
        with open(signal_dir / "signal_flow.mmd", "w") as f:
            f.write(diagram)

        return signal_dir

    def _generate_signal_reference(self, output_dir: Path, analysis: dict):
        """Generate human-readable signal reference."""
        lines = ["# Signal Reference\n"]

        # Statistics
        stats = analysis["statistics"]
        lines.append("## Statistics\n")
        lines.append(f"- **Total Signals**: {stats['total_signals']}")
        lines.append(f"- **Total Connections**: {stats['total_connections']}")
        lines.append(f"- **Total Emissions**: {stats['total_emissions']}")
        lines.append(
            f"- **Signal Density**: {stats['signal_density']} signals per file\n"
        )

        # Patterns
        if analysis["patterns"]:
            lines.append("## Detected Patterns\n")
            for pattern_name, pattern in analysis["patterns"].items():
                lines.append(f"### {pattern_name}")
                lines.append(f"- **Confidence**: {pattern['confidence']}")
                lines.append(f"- **Description**: {pattern['description']}\n")

        # Signal declarations
        lines.append("## Signal Declarations\n")
        for signal, data in analysis["signal_declarations"].items():
            lines.append(f"### `{signal}`")
            lines.append(f"- **File**: `{data['file']}`")
            if data["parameters"]:
                lines.append(f"- **Parameters**: `{data['parameters']}`")
            if data["documentation"]:
                lines.append(f"- **Documentation**: {data['documentation']}")
            lines.append("")

        # Most connected signals
        if stats["most_connected_signals"]:
            lines.append("## Most Connected Signals\n")
            for item in stats["most_connected_signals"]:
                lines.append(
                    f"- **{item['signal']}**: {item['connection_count']} connections"
                )
            lines.append("")

        with open(output_dir / "signal_reference.md", "w") as f:
            f.write("\n".join(lines))
