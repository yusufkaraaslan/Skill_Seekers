"""
Tool Usage Validator - Enhanced for Orchestrator and Referee Agent Validation
Ensures agents properly invoke and use appropriate tools in orchestrated multi-agent workflows
Now includes validation for coordination and synthesis agents.
"""

import json
import re
import subprocess
import logging
import ast
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolRequirement:
    """Definition of a tool requirement for an agent type"""
    name: str
    command: str
    install_command: Optional[str] = None
    check_command: Optional[str] = None
    mandatory: bool = True
    category: str = "general"
    description: str = ""


@dataclass
class ToolUsageEvidence:
    """Evidence of tool usage from agent output"""
    tool_name: str
    command_invoked: str
    output_captured: bool
    success_indicators: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    agent_type: str = ""  # NEW: Track which agent type
    evidence_type: str = "command"  # NEW: command, context, synthesis


@dataclass
class ValidationResult:
    """Result of tool usage validation"""
    is_valid: bool
    compliance_score: float
    used_tools: List[str]
    missing_tools: List[str]
    failed_tools: List[str]
    evidence: List[ToolUsageEvidence]
    recommendations: List[str]
    agent_type: str = ""  # NEW: Which agent type was validated
    validation_details: Dict[str, Any] = field(default_factory=dict)  # NEW: Additional details


class ToolAvailabilityChecker:
    """Checks if required tools are available and accessible"""

    def __init__(self):
        self.checked_tools = {}

    def check_tool(self, tool: ToolRequirement) -> Tuple[bool, str]:
        """Check if a tool is available"""
        if tool.name in self.checked_tools:
            return self.checked_tools[tool.name]

        check_cmd = tool.check_command or tool.command
        try:
            # For built-in tools like Read, Grep, etc., always return True
            if tool.name in ["Read", "Grep", "Task", "Write", "Glob", "Bash"]:
                self.checked_tools[tool.name] = (True, f"Built-in tool available: {tool.name}")
                return self.checked_tools[tool.name]

            # For external tools, try version check
            result = subprocess.run(
                check_cmd.split() + ["--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.checked_tools[tool.name] = (True, result.stdout.strip())
                return self.checked_tools[tool.name]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try --help if --version failed
        try:
            result = subprocess.run(
                check_cmd.split() + ["--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.checked_tools[tool.name] = (True, "Tool available")
                return self.checked_tools[tool.name]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        self.checked_tools[tool.name] = (False, f"Tool not found: {tool.name}")
        return self.checked_tools[tool.name]

    def install_tool(self, tool: ToolRequirement) -> bool:
        """Attempt to install a missing tool"""
        if not tool.install_command:
            return False

        logger.info(f"Installing tool: {tool.name}")
        try:
            result = subprocess.run(
                tool.install_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                # Verify installation
                available, _ = self.check_tool(tool)
                if available:
                    logger.info(f"Successfully installed: {tool.name}")
                    return True
        except subprocess.TimeoutExpired:
            logger.error(f"Installation timeout for: {tool.name}")

        logger.error(f"Failed to install: {tool.name}")
        return False


class ToolUsageParser:
    """Parses agent output to detect tool usage - Enhanced for orchestrator and referee agents"""

    def __init__(self):
        self.tool_patterns = {
            # Security tools
            "pip-audit": r"(?:bash|`)\s*(pip-audit\s+.+?)`",
            "safety": r"(?:bash|`)\s*(safety\s+check\s*.+?)`",
            "pipdeptree": r"(?:bash|`)\s*(pipdeptree\s+.+?)`",
            "bandit": r"(?:bash|`)\s*(bandit\s+.+?)`",
            "semgrep": r"(?:bash|`)\s*(semgrep\s+.+?)`",

            # System tools
            "grep": r"(?:bash|`)\s*(grep\s+.+?)`",
            "find": r"(?:bash|`)\s*(find\s+.+?)`",
            "wc": r"(?:bash|`)\s*(wc\s+.+?)`",
            "ast": r"(?:bash|`)\s*(python\s+.*ast\s*.+?)`",

            # Orchestrator tools (NEW PATTERNS)
            "Read": r"(?:Read:|read_file\s*\([^)]+\))\s*(.+?)(?:\n|$)",
            "Task": r"(?:Task:|task\s*\([^)]+\))\s*(.+?)(?:\n|$)",
            "Glob": r"(?:Glob:|glob\s*\([^)]+\))\s*(.+?)(?:\n|$)",

            # Referee tools (NEW PATTERNS)
            "Write": r"(?:Write:|write_file\s*\([^)]+\))\s*(.+?)(?:\n|$)",
        }

        # Context gathering patterns for orchestrator
        self.context_patterns = {
            "file_reading": r"Read:\s*([^\n]+)",
            "pattern_searching": r"Grep:\s*pattern=[\"\']([^\"\']+)[\"\'].*path=[\"\']([^\"\']+)[\"\']",
            "task_delegation": r"Task:\s*description=[\"\']([^\"\']+)[\"\'].*subagent_type=[\"\']([^\"\']+)[\"\']",
        }

        # Synthesis patterns for referee
        self.synthesis_patterns = {
            "candidate_loading": r"Read:\s*candidate_\d+.*\.md",
            "objective_validation": r"bash:\s*python3\s+-c.*(?:scores?|validation|analysis)",
            "pattern_analysis": r"Grep:\s*pattern=[\"\']([^\"\']+)[\"\'].*path=[\"\']candidate_\d+",
            "structured_output": r"Write:\s*file_path=[\"\'].*\.json[\"\']",
        }

    def parse_output(self, agent_output: str, agent_type: str) -> List[ToolUsageEvidence]:
        """Parse agent output for tool usage evidence - Enhanced for orchestrator/referee"""
        evidence = []

        # Parse standard tool usage
        for tool_name, pattern in self.tool_patterns.items():
            matches = re.findall(pattern, agent_output, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                # Check if output was captured
                has_output = self.check_for_output_capture(agent_output, tool_name, match)

                # Check for success indicators
                success_indicators = self.extract_success_indicators(agent_output, tool_name)

                evidence.append(ToolUsageEvidence(
                    tool_name=tool_name,
                    command_invoked=match,
                    output_captured=has_output,
                    success_indicators=success_indicators,
                    agent_type=agent_type,
                    evidence_type=self.get_evidence_type(tool_name, agent_type)
                ))

        # Parse orchestrator-specific patterns
        if agent_type == "orchestrator-agent":
            evidence.extend(self.parse_orchestrator_patterns(agent_output))

        # Parse referee-specific patterns
        elif agent_type == "referee-agent-csp":
            evidence.extend(self.parse_referee_patterns(agent_output))

        return evidence

    def parse_orchestrator_patterns(self, output: str) -> List[ToolUsageEvidence]:
        """Parse orchestrator-specific tool usage patterns"""
        evidence = []

        # Context gathering evidence
        for pattern_type, pattern in self.context_patterns.items():
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                if pattern_type == "file_reading":
                    evidence.append(ToolUsageEvidence(
                        tool_name="Read",
                        command_invoked=f"Read: {match}",
                        output_captured=True,
                        success_indicators=[f"Read file: {match}"],
                        agent_type="orchestrator-agent",
                        evidence_type="context_gathering"
                    ))

                elif pattern_type == "pattern_searching":
                    pattern_name, path = match
                    evidence.append(ToolUsageEvidence(
                        tool_name="Grep",
                        command_invoked=f"Grep: pattern='{pattern_name}' path='{path}'",
                        output_captured=self.check_for_grep_output(output, pattern_name),
                        success_indicators=[f"Pattern search: {pattern_name} in {path}"],
                        agent_type="orchestrator-agent",
                        evidence_type="context_gathering"
                    ))

                elif pattern_type == "task_delegation":
                    description, subagent_type = match
                    evidence.append(ToolUsageEvidence(
                        tool_name="Task",
                        command_invoked=f"Task: description='{description}' subagent_type='{subagent_type}'",
                        output_captured=True,
                        success_indicators=[f"Delegated to {subagent_type}: {description}"],
                        agent_type="orchestrator-agent",
                        evidence_type="delegation"
                    ))

        return evidence

    def parse_referee_patterns(self, output: str) -> List[ToolUsageEvidence]:
        """Parse referee-specific tool usage patterns"""
        evidence = []

        # Synthesis evidence
        for pattern_type, pattern in self.synthesis_patterns.items():
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                if pattern_type == "candidate_loading":
                    evidence.append(ToolUsageEvidence(
                        tool_name="Read",
                        command_invoked=f"Read: {match}",
                        output_captured=True,
                        success_indicators=[f"Loaded candidate: {match}"],
                        agent_type="referee-agent-csp",
                        evidence_type="candidate_analysis"
                    ))

                elif pattern_type == "objective_validation":
                    evidence.append(ToolUsageEvidence(
                        tool_name="Bash",
                        command_invoked=match,
                        output_captured=self.check_for_bash_output(output, match),
                        success_indicators=[f"Executed validation: {match[:50]}..."],
                        agent_type="referee-agent-csp",
                        evidence_type="objective_validation"
                    ))

                elif pattern_type == "pattern_analysis":
                    pattern_name = match
                    evidence.append(ToolUsageEvidence(
                        tool_name="Grep",
                        command_invoked=f"Grep: pattern='{pattern_name}' path=candidate_*",
                        output_captured=self.check_for_grep_output(output, pattern_name),
                        success_indicators=[f"Pattern analysis: {pattern_name}"],
                        agent_type="referee-agent-csp",
                        evidence_type="pattern_analysis"
                    ))

                elif pattern_type == "structured_output":
                    evidence.append(ToolUsageEvidence(
                        tool_name="Write",
                        command_invoked=match,
                        output_captured=True,
                        success_indicators=[f"Generated structured output: {match}"],
                        agent_type="referee-agent-csp",
                        evidence_type="structured_output"
                    ))

        return evidence

    def check_for_grep_output(self, output: str, pattern_name: str) -> bool:
        """Check if grep command produced output"""
        # Look for grep results in the output
        grep_indicators = [
            rf"{pattern_name}.*:.*:",  # file:line:content format
            rf"\d+:.*{pattern_name}",  # line number with pattern
            rf"Binary file.*{pattern_name}",  # binary file match
            rf"(\d+) matches?",  # match count
        ]

        for indicator in grep_indicators:
            if re.search(indicator, output, re.IGNORECASE):
                return True

        return False

    def check_for_bash_output(self, output: str, command: str) -> bool:
        """Check if bash command produced output"""
        # Look for command output patterns
        output_indicators = [
            r"\{.*\}",  # JSON output
            r"(\d+)\.?\d*",  # Numbers/scores
            r"(Found|Detected|Identified|Calculated)",  # Success words
            r"(candidate_\d+.*score|score.*candidate_\d+)",  # Score references
        ]

        # Find the command in output and check what follows
        command_pos = output.find(command)
        if command_pos != -1:
            section_after = output[command_pos + len(command):command_pos + len(command) + 500]

            for indicator in output_indicators:
                if re.search(indicator, section_after, re.IGNORECASE):
                    return True

        return False

    def get_evidence_type(self, tool_name: str, agent_type: str) -> str:
        """Determine the type of evidence based on tool and agent type"""
        if agent_type == "orchestrator-agent":
            if tool_name in ["Read", "Grep"]:
                return "context_gathering"
            elif tool_name == "Task":
                return "delegation"
            elif tool_name == "Bash":
                return "monitoring"

        elif agent_type == "referee-agent-csp":
            if tool_name == "Read":
                return "candidate_analysis"
            elif tool_name == "Bash":
                return "objective_validation"
            elif tool_name == "Grep":
                return "pattern_analysis"
            elif tool_name == "Write":
                return "structured_output"

        return "command"  # Default for other agents

    def check_for_output_capture(self, output: str, tool_name: str, command: str) -> bool:
        """Check if the tool's output was captured in the agent response"""
        # Look for output patterns (JSON, structured data, findings, etc.)
        command_pos = output.find(command)
        if command_pos == -1:
            return False

        # Check for output after the command invocation
        section_after = output[command_pos + len(command):command_pos + len(command) + 1000]

        output_indicators = [
            r"\{.*\}",  # JSON output
            r"Found \d+ issues?",
            r"(\d+ vulnerabilities?|vulnerabilities?:)",
            r"ERROR|WARNING|INFO",
            r"(\d+ files? scanned|files?:)",
            r"(\d+ results?|results?:)",
            r"score:?\s*\d+",  # Score outputs for referee
            r"candidate.*\d+.*:",  # Candidate analysis
        ]

        for pattern in output_indicators:
            if re.search(pattern, section_after, re.IGNORECASE):
                return True

        return False

    def extract_success_indicators(self, output: str, tool_name: str) -> List[str]:
        """Extract success/failure indicators from output"""
        indicators = []

        # Common success patterns
        success_patterns = {
            "pip-audit": [r"No known vulnerabilities found", r"(\d+) vulnerabilities found"],
            "safety": [r"No known security vulnerabilities", r"(\d+) vulnerabilities found"],
            "bandit": [r"No issues identified", r"(\d+) issues? found"],
            "semgrep": [r"(\d+) findings?", r"ran (\d+) tests?"],
            "grep": [r"(\d+) matches?", r"Binary file"],
            "find": [r"(\d+) files?", r"\.\/"],

            # Orchestrator patterns
            "Read": [r"Read:\s*\S+", r"Loaded file"],
            "Task": [r"Task:\s*description=", r"Delegated to"],
            "Grep": [r"Grep:\s*pattern=", r"pattern.*results"],

            # Referee patterns
            "Bash": [r"score.*\d+", r"validation.*complete"],
            "Write": [r"Write:\s*file_path=", r"Generated.*output"],
        }

        if tool_name in success_patterns:
            for pattern in success_patterns[tool_name]:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    indicators.extend(matches)

        return indicators


class ToolUsageValidator:
    """Main validator class for tool usage in agent workflows - Enhanced for orchestrator/referee"""

    def __init__(self, config_path: Optional[str] = None):
        self.availability_checker = ToolAvailabilityChecker()
        self.usage_parser = ToolUsageParser()
        self.tool_requirements = self.load_tool_requirements(config_path)
        self.compliance_history = []

    def load_tool_requirements(self, config_path: Optional[str]) -> Dict[str, List[ToolRequirement]]:
        """Load tool requirements by agent type"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return self.parse_requirements_config(config)

        # Default requirements with orchestrator and referee agents
        return {
            "security-analyst": [
                ToolRequirement(
                    name="pip-audit",
                    command="pip-audit",
                    install_command="pip install pip-audit",
                    category="dependency",
                    description="Dependency vulnerability scanner"
                ),
                ToolRequirement(
                    name="safety",
                    command="safety",
                    install_command="pip install safety",
                    category="dependency",
                    description="Security vulnerability checker"
                ),
                ToolRequirement(
                    name="bandit",
                    command="bandit",
                    install_command="pip install bandit",
                    category="code",
                    description="Python security linter"
                ),
                ToolRequirement(
                    name="grep",
                    command="grep",
                    category="pattern",
                    description="Pattern matching tool"
                ),
                ToolRequirement(
                    name="find",
                    command="find",
                    category="system",
                    description="File system search tool"
                ),
            ],

            # NEW: Orchestrator agent requirements
            "orchestrator-agent": [
                ToolRequirement(
                    name="Read",
                    command="read_file",
                    category="context",
                    description="Read files to gather context before delegation",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Grep",
                    command="grep",
                    category="pattern",
                    description="Search for specific patterns and information",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Task",
                    command="task",
                    category="delegation",
                    description="Deploy parallel subagent tasks",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Bash",
                    command="bash",
                    category="monitoring",
                    description="Monitor and poll long-running tasks",
                    mandatory=False
                ),
            ],

            # NEW: Referee agent requirements
            "referee-agent-csp": [
                ToolRequirement(
                    name="Read",
                    command="read_file",
                    category="analysis",
                    description="Read specifications and all candidate files for evaluation",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Bash",
                    command="bash",
                    category="validation",
                    description="Execute objective validation commands and scoring",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Grep",
                    command="grep",
                    category="pattern",
                    description="Pattern matching and analysis across candidates",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Task",
                    command="task",
                    category="synthesis",
                    description="Execute final orchestration and selection steps",
                    mandatory=True
                ),
                ToolRequirement(
                    name="Write",
                    command="write_file",
                    category="output",
                    description="Generate structured JSON output for programmatic processing",
                    mandatory=True
                ),
            ],
        }

    def parse_requirements_config(self, config: Dict) -> Dict[str, List[ToolRequirement]]:
        """Parse YAML requirements configuration"""
        requirements = {}

        for agent_type, agent_config in config.get("agent_types", {}).items():
            tools = []
            for tool_config in agent_config.get("required_tools", []):
                tools.append(ToolRequirement(
                    name=tool_config["name"],
                    command=tool_config["command"],
                    install_command=tool_config.get("install_command"),
                    check_command=tool_config.get("check_command"),
                    mandatory=tool_config.get("mandatory", True),
                    category=tool_config.get("category", "general"),
                    description=tool_config.get("description", "")
                ))
            requirements[agent_type] = tools

        return requirements

    def validate_pre_execution(self, agent_type: str, working_dir: str = ".") -> ValidationResult:
        """Validate tool availability before agent execution"""
        if agent_type not in self.tool_requirements:
            return ValidationResult(
                is_valid=False,
                compliance_score=0.0,
                used_tools=[],
                missing_tools=[],
                failed_tools=[],
                evidence=[],
                recommendations=[f"Unknown agent type: {agent_type}"],
                agent_type=agent_type
            )

        requirements = self.tool_requirements[agent_type]
        available_tools = []
        missing_tools = []
        failed_tools = []

        for tool in requirements:
            is_available, message = self.availability_checker.check_tool(tool)

            if is_available:
                available_tools.append(tool.name)
            else:
                if tool.mandatory:
                    # Try to install mandatory tools
                    if self.availability_checker.install_tool(tool):
                        is_available, _ = self.availability_checker.check_tool(tool)
                        if is_available:
                            available_tools.append(tool.name)
                        else:
                            missing_tools.append(tool.name)
                    else:
                        missing_tools.append(tool.name)
                else:
                    failed_tools.append(tool.name)

        compliance_score = (len(available_tools) / len(requirements)) * 100 if requirements else 0

        # Add agent-specific validation details
        validation_details = self.get_pre_execution_details(agent_type, available_tools, missing_tools)

        return ValidationResult(
            is_valid=compliance_score >= 80.0,  # 80% threshold
            compliance_score=compliance_score,
            used_tools=available_tools,
            missing_tools=missing_tools,
            failed_tools=failed_tools,
            evidence=[],
            recommendations=self.generate_pre_execution_recommendations(
                agent_type, available_tools, missing_tools, failed_tools
            ),
            agent_type=agent_type,
            validation_details=validation_details
        )

    def get_pre_execution_details(self, agent_type: str, available: List[str], missing: List[str]) -> Dict[str, Any]:
        """Get agent-specific pre-execution validation details"""
        details = {"agent_type": agent_type, "available_tools": available, "missing_tools": missing}

        if agent_type == "orchestrator-agent":
            details["context_tools_available"] = "Read" in available and "Grep" in available
            details["delegation_available"] = "Task" in available
            details["monitoring_available"] = "Bash" in available

        elif agent_type == "referee-agent-csp":
            details["analysis_tools_available"] = "Read" in available and "Grep" in available
            details["validation_available"] = "Bash" in available
            details["synthesis_available"] = "Task" in available and "Write" in available

        return details

    def validate_post_execution(
        self,
        agent_type: str,
        agent_output: str,
        agent_id: str = "unknown"
    ) -> ValidationResult:
        """Validate that tools were actually used during execution - Enhanced for orchestrator/referee"""
        # Parse tool usage from output
        evidence = self.usage_parser.parse_output(agent_output, agent_type)

        # Get required tools
        required_tools = self.tool_requirements.get(agent_type, [])
        required_tool_names = [t.name for t in required_tools if t.mandatory]

        # Determine what was used
        used_tools = list(set([e.tool_name for e in evidence]))

        # Check for missing mandatory tools
        missing_tools = list(set(required_tool_names) - set(used_tools))

        # Check for tool execution success
        successful_tools = []
        failed_tools = []

        for ev in evidence:
            if ev.output_captured and ev.success_indicators:
                successful_tools.append(ev.tool_name)
            else:
                failed_tools.append(ev.tool_name)

        # Calculate compliance score with agent-specific logic
        compliance_score = self.calculate_compliance_score(
            agent_type, used_tools, required_tool_names, evidence
        )

        # Generate recommendations
        recommendations = self.generate_post_execution_recommendations(
            agent_type, used_tools, missing_tools, failed_tools, evidence
        )

        # Add agent-specific validation details
        validation_details = self.get_post_execution_details(agent_type, evidence, used_tools)

        # Store in history
        self.compliance_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "compliance_score": compliance_score,
            "used_tools": used_tools,
            "missing_tools": missing_tools,
            "evidence_count": len(evidence),
            "validation_details": validation_details
        })

        return ValidationResult(
            is_valid=compliance_score >= 70.0,  # 70% threshold for post-execution
            compliance_score=compliance_score,
            used_tools=used_tools,
            missing_tools=missing_tools,
            failed_tools=failed_tools,
            evidence=evidence,
            recommendations=recommendations,
            agent_type=agent_type,
            validation_details=validation_details
        )

    def calculate_compliance_score(
        self,
        agent_type: str,
        used_tools: List[str],
        required_tools: List[str],
        evidence: List[ToolUsageEvidence]
    ) -> float:
        """Calculate compliance score with agent-specific logic"""
        if not required_tools:
            return 100.0 if evidence else 0.0

        basic_compliance = (len(set(used_tools) & set(required_tools)) / len(required_tools)) * 100

        # Agent-specific scoring adjustments
        if agent_type == "orchestrator-agent":
            # Check for context gathering quality
            context_evidence = [e for e in evidence if e.evidence_type == "context_gathering"]
            if context_evidence:
                context_bonus = min(20, len(context_evidence) * 10)
                basic_compliance = min(100, basic_compliance + context_bonus)

            # Check for delegation evidence
            delegation_evidence = [e for e in evidence if e.evidence_type == "delegation"]
            if not delegation_evidence:
                basic_compliance -= 30  # Major penalty for no delegation

        elif agent_type == "referee-agent-csp":
            # Check for objective validation
            validation_evidence = [e for e in evidence if e.evidence_type == "objective_validation"]
            if not validation_evidence:
                basic_compliance -= 40  # Major penalty for no objective validation

            # Check for structured output
            output_evidence = [e for e in evidence if e.evidence_type == "structured_output"]
            if not output_evidence:
                basic_compliance -= 20  # Penalty for no structured output

            # Check for candidate analysis
            candidate_evidence = [e for e in evidence if e.evidence_type == "candidate_analysis"]
            if candidate_evidence:
                analysis_bonus = min(15, len(candidate_evidence) * 5)
                basic_compliance = min(100, basic_compliance + analysis_bonus)

        return max(0, basic_compliance)

    def get_post_execution_details(
        self,
        agent_type: str,
        evidence: List[ToolUsageEvidence],
        used_tools: List[str]
    ) -> Dict[str, Any]:
        """Get agent-specific post-execution validation details"""
        details = {
            "agent_type": agent_type,
            "used_tools": used_tools,
            "evidence_count": len(evidence),
            "evidence_types": list(set([e.evidence_type for e in evidence]))
        }

        if agent_type == "orchestrator-agent":
            details["context_gathering"] = len([e for e in evidence if e.evidence_type == "context_gathering"])
            details["delegation_events"] = len([e for e in evidence if e.evidence_type == "delegation"])
            details["monitoring_events"] = len([e for e in evidence if e.evidence_type == "monitoring"])
            details["parallel_execution"] = details["delegation_events"] > 1

        elif agent_type == "referee-agent-csp":
            details["candidate_analysis"] = len([e for e in evidence if e.evidence_type == "candidate_analysis"])
            details["objective_validation"] = len([e for e in evidence if e.evidence_type == "objective_validation"])
            details["pattern_analysis"] = len([e for e in evidence if e.evidence_type == "pattern_analysis"])
            details["structured_output"] = len([e for e in evidence if e.evidence_type == "structured_output"])
            details["deterministic_selection"] = details["objective_validation"] > 0 and details["structured_output"] > 0

        return details

    def generate_pre_execution_recommendations(
        self,
        agent_type: str,
        available: List[str],
        missing: List[str],
        failed: List[str]
    ) -> List[str]:
        """Generate recommendations for pre-execution validation"""
        recommendations = []

        if missing:
            recommendations.append(f"Install missing mandatory tools: {', '.join(missing)}")

        if failed:
            recommendations.append(f"Optional tools not available: {', '.join(failed)}")

        if len(available) == 0:
            recommendations.append("CRITICAL: No required tools available. Agent execution will fail.")

        # Agent-specific recommendations
        if agent_type == "orchestrator-agent":
            if "Read" not in available:
                recommendations.append("Orchestrator MUST be able to read files for context gathering")
            if "Task" not in available:
                recommendations.append("Orchestrator MUST be able to delegate tasks to subagents")

        elif agent_type == "referee-agent-csp":
            if "Read" not in available:
                recommendations.append("Referee MUST be able to read candidate files for analysis")
            if "Bash" not in available:
                recommendations.append("Referee MUST be able to execute validation commands")
            if "Write" not in available:
                recommendations.append("Referee MUST be able to generate structured output")

        return recommendations

    def generate_post_execution_recommendations(
        self,
        agent_type: str,
        used: List[str],
        missing: List[str],
        failed: List[str],
        evidence: List[ToolUsageEvidence]
    ) -> List[str]:
        """Generate recommendations based on execution results"""
        recommendations = []

        if missing:
            recommendations.append(f"Agent missed required tools: {', '.join(missing)}")
            recommendations.append("Update agent prompt to emphasize mandatory tool usage")

        if failed:
            recommendations.append(f"Tools executed without proper output: {', '.join(failed)}")
            recommendations.append("Ensure agents capture and analyze tool outputs")

        # Check for evidence quality
        tools_without_output = [e.tool_name for e in evidence if not e.output_captured]
        if tools_without_output:
            recommendations.append(f"Tools used but output not captured: {', '.join(tools_without_output)}")
            recommendations.append("Train agents to include tool outputs in their analysis")

        # Agent-specific recommendations
        if agent_type == "orchestrator-agent":
            context_evidence = [e for e in evidence if e.evidence_type == "context_gathering"]
            if not context_evidence:
                recommendations.append("Orchestrator must gather context before delegation")
                recommendations.append("Use Read and Grep tools to analyze the codebase before task distribution")

            delegation_evidence = [e for e in evidence if e.evidence_type == "delegation"]
            if len(delegation_evidence) < 2:
                recommendations.append("Orchestrator should demonstrate parallel delegation capability")
                recommendations.append("Use Task tool to deploy multiple subagents concurrently")

        elif agent_type == "referee-agent-csp":
            validation_evidence = [e for e in evidence if e.evidence_type == "objective_validation"]
            if not validation_evidence:
                recommendations.append("Referee must perform objective validation, not theoretical analysis")
                recommendations.append("Use Bash tool to execute validation commands and generate scores")

            output_evidence = [e for e in evidence if e.evidence_type == "structured_output"]
            if not output_evidence:
                recommendations.append("Referee must generate structured JSON output for programmatic processing")
                recommendations.append("Use Write tool to create JSON-formatted synthesis results")

            candidate_evidence = [e for e in evidence if e.evidence_type == "candidate_analysis"]
            if len(candidate_evidence) < 2:
                recommendations.append("Referee must analyze all candidate files, not just select one")
                recommendations.append("Use Read tool to load all candidate outputs before synthesis")

        return recommendations

    def generate_enhanced_prompt(self, base_prompt: str, agent_type: str) -> str:
        """Enhance agent prompt with tool usage requirements - Enhanced for orchestrator/referee"""
        if agent_type not in self.tool_requirements:
            return base_prompt

        requirements = self.tool_requirements[agent_type]
        mandatory_tools = [t for t in requirements if t.mandatory]

        tool_instructions = f"""
## MANDATORY TOOL USAGE REQUIREMENTS

You MUST use the following tools during your analysis. Do NOT rely on reasoning alone.

### Required Tools:
"""

        for tool in mandatory_tools:
            tool_instructions += f"""
- **{tool.name}**: {tool.description}
  - Category: {tool.category}
  - Must be invoked and results analyzed
"""

        # Add agent-specific instructions
        if agent_type == "orchestrator-agent":
            tool_instructions += f"""
### Orchestrator-Specific Requirements:
1. **Context Gathering First**: Before any delegation, you MUST use Read and Grep tools to understand the codebase/problem
2. **Demonstrate Parallel Delegation**: Use Task tool to deploy multiple subagents concurrently
3. **Monitor Progress**: Should use Bash tool to monitor long-running tasks
4. **Synthesize Results**: Must read and integrate outputs from delegated tasks

### Example Proper Usage:
```
Step 1: Context Gathering
Read: cli/constants.py
Read: requirements.txt
Grep: pattern="security" path="cli/" output_mode="files_with_matches"

Step 2: Parallel Delegation
Task: description="Web scraping security analysis" subagent_type="security-analyst"
Task: description="Dependency security analysis" subagent_type="security-analyst"

Step 3: Result Synthesis
Read: output/web_scraping_analysis.md
Read: output/dependency_analysis.md
# Synthesize comprehensive report
```
"""

        elif agent_type == "referee-agent-csp":
            tool_instructions += f"""
### Referee-Specific Requirements:
1. **Read All Candidates**: MUST read ALL candidate files using Read tool
2. **Objective Validation**: MUST use Bash tool to execute validation commands (no theoretical analysis)
3. **Pattern Analysis**: MUST use Grep tool to analyze patterns across candidates
4. **Structured Output**: MUST use Write tool to generate JSON-formatted results

### Example Proper Usage:
```
Step 1: Load All Candidates
Read: candidate_1_analysis.md
Read: candidate_2_analysis.md
Read: candidate_3_analysis.md

Step 2: Objective Validation
Bash: python3 -c "
# Calculate objective scores
scores = {}
for i in range(1, 4):
    with open('candidate_{i}_analysis.md'.format(i)) as f:
        content = f.read()
        scores['candidate_{i}'.format(i)] = content.count('vulnerability')
print(json.dumps(scores))
"

Step 3: Pattern Analysis
Grep: pattern="critical|high|medium" path="candidate_*_analysis.md" output_mode="content"

Step 4: Generate Structured Output
Write: file_path="synthesis_results.json" content=json_dumps(results)
```
"""

        else:
            # Standard instructions for other agents
            tool_instructions += f"""
### Tool Usage Rules:
1. **ACTUALLY EXECUTE** the tools using appropriate commands
2. **CAPTURE OUTPUT** from each tool execution
3. **ANALYZE RESULTS** - don't just mention you ran the tool
4. **REPORT FINDINGS** based on actual tool outputs
5. **INCLUDE EVIDENCE** such as specific vulnerabilities, issues, etc.

### Example Proper Usage:
```
Step 1: Running security vulnerability scan
bash: pip-audit --requirement requirements.txt --format=json

Output captured:
{{
  "vulnerabilities": [
    {{
      "name": "requests",
      "version": "2.25.1",
      "vuln_id": "CVE-2023-1234",
      "advisory": "Remote code execution vulnerability"
    }}
  ]
}}

Analysis:
Found 1 critical vulnerability in requests package...
```
"""

        tool_instructions += f"""
### WARNING: Analysis without actual tool usage will be marked INVALID.
"""

        return base_prompt + tool_instructions

    def get_compliance_report(self, timeframe: str = "all") -> Dict[str, Any]:
        """Generate compliance report for monitoring - Enhanced with orchestrator/referee metrics"""
        if timeframe == "all":
            history = self.compliance_history
        else:
            # Filter by timeframe
            cutoff = {
                "day": 1,
                "week": 7,
                "month": 30
            }.get(timeframe, 0)

            if cutoff > 0:
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=cutoff)
                history = [
                    h for h in self.compliance_history
                    if datetime.fromisoformat(h["timestamp"]) > cutoff_date
                ]
            else:
                history = []

        if not history:
            return {
                "total_executions": 0,
                "average_compliance": 0.0,
                "compliance_trend": "no_data",
                "agent_performance": {},
                "common_missing_tools": [],
                "recommendations": ["No execution history available"],
                "orchestrator_metrics": {},
                "referee_metrics": {}
            }

        # Calculate metrics
        total_executions = len(history)
        average_compliance = sum(h["compliance_score"] for h in history) / total_executions

        # Agent performance
        agent_performance = {}
        for record in history:
            agent_type = record["agent_type"]
            if agent_type not in agent_performance:
                agent_performance[agent_type] = {
                    "count": 0,
                    "total_score": 0,
                    "missing_tools": [],
                    "validation_details": []
                }

            agent_performance[agent_type]["count"] += 1
            agent_performance[agent_type]["total_score"] += record["compliance_score"]
            agent_performance[agent_type]["missing_tools"].extend(record["missing_tools"])
            agent_performance[agent_type]["validation_details"].append(record["validation_details"])

        # Calculate averages and extract orchestrator/referee metrics
        orchestrator_metrics = {}
        referee_metrics = {}

        for agent in agent_performance:
            count = agent_performance[agent]["count"]
            agent_performance[agent]["average_score"] = agent_performance[agent]["total_score"] / count
            agent_performance[agent]["common_missing"] = list(
                set(agent_performance[agent]["missing_tools"])
            )[:5]

            # Extract specific metrics for orchestrator and referee
            if agent == "orchestrator-agent":
                orchestrator_metrics = self.extract_orchestrator_metrics(
                    agent_performance[agent]["validation_details"]
                )
            elif agent == "referee-agent-csp":
                referee_metrics = self.extract_referee_metrics(
                    agent_performance[agent]["validation_details"]
                )

        # Compliance trend
        if len(history) >= 2:
            recent_avg = sum(h["compliance_score"] for h in history[-5:]) / min(5, len(history[-5:]))
            older_avg = sum(h["compliance_score"] for h in history[:-5]) / max(1, len(history[:-5]))

            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Common missing tools
        all_missing = []
        for record in history:
            all_missing.extend(record["missing_tools"])

        from collections import Counter
        common_missing = [
            {"tool": tool, "count": count}
            for tool, count in Counter(all_missing).most_common(10)
        ]

        return {
            "total_executions": total_executions,
            "average_compliance": round(average_compliance, 2),
            "compliance_trend": trend,
            "agent_performance": agent_performance,
            "common_missing_tools": common_missing,
            "orchestrator_metrics": orchestrator_metrics,
            "referee_metrics": referee_metrics,
            "recommendations": self.generate_system_recommendations(history)
        }

    def extract_orchestrator_metrics(self, validation_details: List[Dict]) -> Dict[str, Any]:
        """Extract orchestrator-specific metrics"""
        if not validation_details:
            return {}

        context_gathering = sum(1 for d in validation_details if d.get("context_gathering", 0) > 0)
        delegation_events = sum(d.get("delegation_events", 0) for d in validation_details)
        monitoring_events = sum(d.get("monitoring_events", 0) for d in validation_details)
        parallel_execution = sum(1 for d in validation_details if d.get("parallel_execution", False))

        return {
            "context_gathering_rate": (context_gathering / len(validation_details)) * 100,
            "average_delegations_per_execution": delegation_events / len(validation_details),
            "monitoring_rate": (monitoring_events / len(validation_details)) * 100,
            "parallel_execution_rate": (parallel_execution / len(validation_details)) * 100,
            "total_executions": len(validation_details)
        }

    def extract_referee_metrics(self, validation_details: List[Dict]) -> Dict[str, Any]:
        """Extract referee-specific metrics"""
        if not validation_details:
            return {}

        objective_validation = sum(1 for d in validation_details if d.get("objective_validation", 0) > 0)
        structured_output = sum(1 for d in validation_details if d.get("structured_output", 0) > 0)
        candidate_analysis = sum(d.get("candidate_analysis", 0) for d in validation_details)
        deterministic_selection = sum(1 for d in validation_details if d.get("deterministic_selection", False))

        return {
            "objective_validation_rate": (objective_validation / len(validation_details)) * 100,
            "structured_output_rate": (structured_output / len(validation_details)) * 100,
            "average_candidates_analyzed": candidate_analysis / len(validation_details),
            "deterministic_selection_rate": (deterministic_selection / len(validation_details)) * 100,
            "total_executions": len(validation_details)
        }

    def generate_system_recommendations(self, history: List[Dict]) -> List[str]:
        """Generate system-level recommendations based on compliance history"""
        recommendations = []

        if not history:
            return recommendations

        # Check overall compliance
        avg_score = sum(h["compliance_score"] for h in history) / len(history)

        if avg_score < 50:
            recommendations.append("CRITICAL: Overall tool usage compliance is below 50%")
            recommendations.append("Review and update agent prompts with mandatory tool requirements")
        elif avg_score < 70:
            recommendations.append("Tool usage compliance needs improvement")
            recommendations.append("Implement tool usage validation in orchestration workflow")

        # Check agent-specific issues
        agent_types = set(h["agent_type"] for h in history)
        for agent_type in agent_types:
            agent_records = [h for h in history if h["agent_type"] == agent_type]
            agent_avg = sum(h["compliance_score"] for h in agent_records) / len(agent_records)

            if agent_avg < 60:
                recommendations.append(f"Agent type '{agent_type}' consistently underperforms in tool usage")
                recommendations.append(f"Create tool usage templates for {agent_type}")

            # Agent-specific recommendations
            if agent_type == "orchestrator-agent":
                context_issues = sum(1 for r in agent_records if not r["validation_details"].get("context_gathering", 0))
                if context_issues > len(agent_records) * 0.5:
                    recommendations.append("Orchestrator agents frequently skip context gathering before delegation")
                    recommendations.append("Enforce mandatory Read/Grep usage before Task delegation")

            elif agent_type == "referee-agent-csp":
                validation_issues = sum(1 for r in agent_records if not r["validation_details"].get("objective_validation", 0))
                if validation_issues > len(agent_records) * 0.5:
                    recommendations.append("Referee agents frequently perform theoretical analysis without objective validation")
                    recommendations.append("Require Bash tool usage for validation commands")

        return recommendations


# Example usage and integration functions

def validate_orchestration_workflow(
    agent_configs: List[Dict],
    execution_results: List[Dict]
) -> Dict[str, ValidationResult]:
    """Validate tool usage across an entire orchestration workflow"""
    validator = ToolUsageValidator()
    results = {}

    # Pre-execution validation
    for config in agent_configs:
        agent_id = config.get("id", "unknown")
        agent_type = config.get("type", "unknown")

        pre_result = validator.validate_pre_execution(agent_type)
        results[f"{agent_id}_pre"] = pre_result

        if not pre_result.is_valid:
            logger.warning(f"Agent {agent_id} failed pre-execution validation")

    # Post-execution validation
    for result in execution_results:
        agent_id = result.get("id", "unknown")
        agent_type = result.get("type", "unknown")
        output = result.get("output", "")

        post_result = validator.validate_post_execution(agent_type, output, agent_id)
        results[f"{agent_id}_post"] = post_result

        # Check compliance
        if post_result.compliance_score < 70:
            logger.warning(
                f"Low tool usage compliance for {agent_id}: "
                f"{post_result.compliance_score}%"
            )

    return results


if __name__ == "__main__":
    # Demo usage
    validator = ToolUsageValidator()

    # Test pre-execution validation for orchestrator
    print("=== Orchestrator Pre-execution Validation ===")
    result = validator.validate_pre_execution("orchestrator-agent")
    print(f"Valid: {result.is_valid}")
    print(f"Compliance: {result.compliance_score}%")
    print(f"Available: {result.used_tools}")
    print(f"Missing: {result.missing_tools}")
    print(f"Details: {result.validation_details}")

    # Test post-execution validation for referee
    print("\n=== Referee Post-execution Validation ===")
    sample_output = """
    Convergent Synthesis Results

    Step 1: Load all candidates
    Read: candidate_1_analysis.md
    Read: candidate_2_analysis.md
    Read: candidate_3_analysis.md

    Step 2: Objective validation
    Bash: python3 -c "
    import json
    scores = {'candidate_1': 8, 'candidate_2': 6, 'candidate_3': 9}
    print(json.dumps(scores))
    "

    Step 3: Pattern analysis
    Grep: pattern="vulnerability" path="candidate_*_analysis.md"
    Grep: pattern="score" path="candidate_*_analysis.md"

    Step 4: Generate structured output
    Write: file_path="synthesis_results.json" content=json.dumps(results)
    """

    result = validator.validate_post_execution("referee-agent-csp", sample_output, "referee-test")
    print(f"Valid: {result.is_valid}")
    print(f"Compliance: {result.compliance_score}%")
    print(f"Used tools: {result.used_tools}")
    print(f"Missing tools: {result.missing_tools}")
    print(f"Details: {result.validation_details}")

    # Generate compliance report
    print("\n=== Compliance Report ===")
    report = validator.get_compliance_report()
    print(json.dumps(report, indent=2))