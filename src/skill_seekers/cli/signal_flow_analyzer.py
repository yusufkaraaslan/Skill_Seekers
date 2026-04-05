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
            sig: len(conns) for sig, conns in self.signal_connections.items() if len(conns) >= 3
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
        total_connections = sum(len(conns) for conns in self.signal_connections.values())
        total_emissions = sum(len(emits) for emits in self.signal_emissions.items())

        # Find most connected signals
        most_connected = sorted(
            self.signal_connections.items(), key=lambda x: len(x[1]), reverse=True
        )[:5]

        # Find most emitted signals
        most_emitted = sorted(self.signal_emissions.items(), key=lambda x: len(x[1]), reverse=True)[
            :5
        ]

        # Signal density (signals per GDScript file)
        gdscript_files = sum(1 for f in self.files if f.get("language") == "GDScript")
        signal_density = total_signals / gdscript_files if gdscript_files > 0 else 0

        return {
            "total_signals": total_signals,
            "total_connections": total_connections,
            "total_emissions": total_emissions,
            "signal_density": round(signal_density, 2),
            "gdscript_files": gdscript_files,
            "most_connected_signals": [
                {"signal": sig, "connection_count": len(conns)} for sig, conns in most_connected
            ],
            "most_emitted_signals": [
                {"signal": sig, "emission_count": len(emits)} for sig, emits in most_emitted
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

    def extract_signal_usage_patterns(self) -> list[dict[str, Any]]:
        """
        Extract common signal usage patterns for how-to guide generation.

        Returns:
            List of signal usage patterns with connect/emit/handle examples
        """
        patterns = []

        # For each signal, find usage examples (connect + emit + handle)
        for signal_name, signal_info in self.signal_declarations.items():
            # Find connections to this signal
            connections = self.signal_connections.get(signal_name, [])
            emissions = self.signal_emissions.get(signal_name, [])

            if not connections and not emissions:
                continue  # Skip signals with no usage

            # Build usage pattern
            pattern = {
                "signal_name": signal_name,
                "signal_file": signal_info.get("file", ""),
                "parameters": signal_info.get("parameters", ""),
                "documentation": signal_info.get("documentation"),
                "connections": connections[:3],  # Top 3 connections
                "emissions": emissions[:3],  # Top 3 emissions
                "usage_count": len(connections) + len(emissions),
            }

            patterns.append(pattern)

        # Sort by usage count (most used first)
        patterns.sort(key=lambda x: x["usage_count"], reverse=True)

        return patterns[:10]  # Top 10 most used signals

    def generate_how_to_guides(self, output_dir: Path, ai_mode: str = "LOCAL") -> str:
        """
        Generate signal-based how-to guides using AI.

        Args:
            output_dir: Directory to save guides
            ai_mode: "LOCAL" (Claude Code) or "API" (Anthropic API)

        Returns:
            Path to generated guide file
        """
        patterns = self.extract_signal_usage_patterns()

        if not patterns:
            return ""

        # Build guide content
        guide_content = "# Signal Usage How-To Guides\n\n"
        guide_content += "*AI-generated guides for common signal patterns*\n\n"
        guide_content += "## Table of Contents\n\n"

        for i, pattern in enumerate(patterns, 1):
            signal_name = pattern["signal_name"]
            guide_content += (
                f"{i}. [How to use `{signal_name}`](#{signal_name.lower().replace('_', '-')})\n"
            )

        guide_content += "\n---\n\n"

        # Generate guide for each pattern
        for pattern in patterns:
            guide_section = self._generate_signal_guide(pattern, ai_mode)
            guide_content += guide_section + "\n---\n\n"

        # Save guide
        guide_file = output_dir / "signals" / "signal_how_to_guides.md"
        with open(guide_file, "w") as f:
            f.write(guide_content)

        return str(guide_file)

    def _generate_signal_guide(self, pattern: dict[str, Any], ai_mode: str) -> str:
        """
        Generate a how-to guide for a single signal using AI.

        Args:
            pattern: Signal usage pattern data
            ai_mode: "LOCAL" or "API"

        Returns:
            Markdown guide content
        """
        signal_name = pattern["signal_name"]
        params = pattern["parameters"]
        docs = pattern["documentation"]
        connections = pattern["connections"]
        emissions = pattern["emissions"]

        # Build guide without AI (basic template)
        guide = f"## How to use `{signal_name}`\n\n"

        if docs:
            guide += f"**Description:** {docs}\n\n"

        if params:
            guide += f"**Parameters:** `{params}`\n\n"

        guide += "### Step 1: Connect to the signal\n\n"
        guide += "```gdscript\n"
        if connections:
            handler = connections[0].get("handler", "_on_signal")
            file_context = Path(connections[0].get("file", "")).stem
            guide += f"# In {file_context}.gd\n"
            guide += f"{signal_name}.connect({handler})\n"
        else:
            guide += f"{signal_name}.connect(_on_{signal_name.split('.')[-1]})\n"
        guide += "```\n\n"

        guide += "### Step 2: Emit the signal\n\n"
        guide += "```gdscript\n"
        if emissions:
            args = emissions[0].get("arguments", "")
            file_context = Path(emissions[0].get("file", "")).stem
            guide += f"# In {file_context}.gd\n"
            guide += f"{signal_name}.emit({args})\n"
        else:
            guide += f"{signal_name}.emit()\n"
        guide += "```\n\n"

        guide += "### Step 3: Handle the signal\n\n"
        guide += "```gdscript\n"
        if connections:
            handler = connections[0].get("handler", "_on_signal")
            if params:
                # Parse params to function signature
                param_list = params.split(",")
                param_names = [p.split(":")[0].strip() for p in param_list]
                func_params = ", ".join(param_names)
                guide += f"func {handler}({func_params}):\n"
                guide += f"    # Handle {signal_name} event\n"
                guide += f"    print('Signal received with:', {param_names[0] if param_names else 'null'})\n"
            else:
                guide += f"func {handler}():\n"
                guide += f"    # Handle {signal_name} event\n"
                guide += f"    print('Signal received')\n"
        else:
            guide += f"func _on_{signal_name.split('.')[-1]}():\n"
            guide += f"    # Handle {signal_name} event\n"
            guide += f"    pass\n"
        guide += "```\n\n"

        # Add usage examples
        if len(connections) > 1 or len(emissions) > 1:
            guide += "### Common Usage Locations\n\n"
            if connections:
                guide += "**Connected in:**\n"
                for conn in connections[:3]:
                    file_path = Path(conn.get("file", "")).stem
                    handler = conn.get("handler", "")
                    guide += f"- `{file_path}.gd` → `{handler}()`\n"
                guide += "\n"

            if emissions:
                guide += "**Emitted from:**\n"
                for emit in emissions[:3]:
                    file_path = Path(emit.get("file", "")).stem
                    guide += f"- `{file_path}.gd`\n"
                guide += "\n"

        return guide

    def save_analysis(self, output_dir: Path, ai_mode: str = "LOCAL"):
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

        # Generate how-to guides
        try:
            guide_file = self.generate_how_to_guides(output_dir, ai_mode)
            if guide_file:
                import logging

                logger = logging.getLogger(__name__)
                logger.info(f"📚 Generated signal how-to guides: {guide_file}")
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate signal how-to guides: {e}")

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
        lines.append(f"- **Signal Density**: {stats['signal_density']} signals per file\n")

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
                lines.append(f"- **{item['signal']}**: {item['connection_count']} connections")
            lines.append("")

        with open(output_dir / "signal_reference.md", "w") as f:
            f.write("\n".join(lines))
