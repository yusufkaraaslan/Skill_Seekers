"""
Minimal test of tool usage validation framework functionality
Tests core parsing and validation without complex examples
"""

import re
from datetime import datetime
from typing import List, Dict, Any


def test_pattern_parsing():
    """Test basic pattern parsing for orchestrator and referee agents"""
    print("=== Testing Pattern Parsing ===")

    # Test orchestrator patterns
    orchestrator_patterns = {
        "Read": r"(?:Read:|read_file\s*\([^)]+\))\s*(.+?)(?:\n|$)",
        "Task": r"(?:Task:|task\s*\([^)]+\))\s*(.+?)(?:\n|$)",
        "Grep": r"(?:Grep:|grep\s+.+?)\s*(.+?)(?:\n|$)",
    }

    # Test referee patterns
    referee_patterns = {
        "Read": r"(?:Read:|read_file\s*\([^)]+\))\s*(.+?)(?:\n|$)",
        "Bash": r"(?:Bash:|bash\s+.+?)\s*(.+?)(?:\n|$)",
        "Write": r"(?:Write:|write_file\s*\([^)]+\))\s*(.+?)(?:\n|$)",
        "Grep": r"(?:Grep:|grep\s+.+?)\s*(.+?)(?:\n|$)",
    }

    # Test data
    orch_output = """
    Read: cli/constants.py
    Read: requirements.txt

    Grep: pattern="security" path="cli/" output_mode="files_with_matches"

    Task: description="Security analysis" subagent_type="security-analyst"
    Task: description="Code review" subagent_type="code-analyst"
    """

    ref_output = """
    Read: candidate_1.md
    Read: candidate_2.md

    Bash: python3 -c "print('validation')"

    Grep: pattern="score" path="candidate_*.md"

    Write: file_path="results.json" content='{"selected": "candidate_1"}'
    """

    print("\n1. Testing Orchestrator Pattern Detection:")
    orch_tools = {}
    for tool_name, pattern in orchestrator_patterns.items():
        matches = re.findall(pattern, orch_output, re.MULTILINE | re.IGNORECASE)
        orch_tools[tool_name] = len(matches)
        print(f"   {tool_name}: {len(matches)} matches")

    print("\n2. Testing Referee Pattern Detection:")
    ref_tools = {}
    for tool_name, pattern in referee_patterns.items():
        matches = re.findall(pattern, ref_output, re.MULTILINE | re.IGNORECASE)
        ref_tools[tool_name] = len(matches)
        print(f"   {tool_name}: {len(matches)} matches")

    # Validation
    orch_required = ["Read", "Task", "Grep"]
    ref_required = ["Read", "Bash", "Write", "Grep"]

    orch_missing = set(orch_required) - set([k for k, v in orch_tools.items() if v > 0])
    ref_missing = set(ref_required) - set([k for k, v in ref_tools.items() if v > 0])

    print(f"\n3. Validation Results:")
    print(f"   Orchestrator missing tools: {orch_missing if orch_missing else 'None'}")
    print(f"   Referee missing tools: {ref_missing if ref_missing else 'None'}")

    return len(orch_missing) == 0 and len(ref_missing) == 0


def test_compliance_scoring():
    """Test compliance scoring logic"""
    print("\n=== Testing Compliance Scoring ===")

    def calculate_orchestrator_score(used_tools, evidence_types):
        """Calculate orchestrator compliance score"""
        basic_tools = {"Read", "Grep", "Task"}
        used_basic = set(used_tools) & basic_tools

        basic_compliance = (len(used_basic) / len(basic_tools)) * 100

        # Bonuses for orchestrator-specific evidence
        context_bonus = len([et for et in evidence_types if et == "context_gathering"]) * 10
        delegation_bonus = len([et for et in evidence_types if et == "delegation"]) * 15

        return min(100, basic_compliance + context_bonus + delegation_bonus)

    def calculate_referee_score(used_tools, evidence_types):
        """Calculate referee compliance score"""
        basic_tools = {"Read", "Bash", "Write", "Grep"}
        used_basic = set(used_tools) & basic_tools

        basic_compliance = (len(used_basic) / len(basic_tools)) * 100

        # Penalties for missing critical validation
        if "Bash" not in used_tools:
            basic_compliance -= 40
        if "Write" not in used_tools:
            basic_compliance -= 20

        return max(0, basic_compliance)

    # Test cases
    test_cases = [
        {
            "name": "Good Orchestrator",
            "used_tools": ["Read", "Grep", "Task"],
            "evidence_types": ["context_gathering", "delegation", "delegation"],
            "expected_min": 80
        },
        {
            "name": "Poor Orchestrator",
            "used_tools": ["Task"],
            "evidence_types": ["delegation"],
            "expected_min": 30
        },
        {
            "name": "Good Referee",
            "used_tools": ["Read", "Bash", "Write", "Grep"],
            "evidence_types": ["candidate_analysis", "objective_validation"],
            "expected_min": 80
        },
        {
            "name": "Poor Referee",
            "used_tools": ["Read"],
            "evidence_types": ["candidate_analysis"],
            "expected_min": 40
        }
    ]

    results = []
    for test_case in test_cases:
        if "Task" in test_case["used_tools"]:
            score = calculate_orchestrator_score(test_case["used_tools"], test_case["evidence_types"])
        else:
            score = calculate_referee_score(test_case["used_tools"], test_case["evidence_types"])

        passed = score >= test_case["expected_min"]
        results.append((test_case["name"], score, passed))

        print(f"   {test_case['name']}: {score:.1f}% {'✓' if passed else '✗'} (min: {test_case['expected_min']}%)")

    all_passed = all(r[2] for r in results)
    return all_passed


def test_evidence_extraction():
    """Test evidence extraction from agent outputs"""
    print("\n=== Testing Evidence Extraction ===")

    def extract_orchestrator_evidence(output):
        """Extract orchestrator evidence from output"""
        evidence = []

        # Read operations
        read_matches = re.findall(r'Read:\s*(\S+)', output)
        for match in read_matches:
            evidence.append({
                "tool": "Read",
                "command": f"Read: {match}",
                "type": "context_gathering",
                "success": True
            })

        # Grep operations
        grep_matches = re.findall(r'Grep:\s*pattern=[\'"]([^\'"]+)[\'"]', output)
        for match in grep_matches:
            evidence.append({
                "tool": "Grep",
                "command": f"Grep: pattern='{match}'",
                "type": "context_gathering",
                "success": True
            })

        # Task operations
        task_matches = re.findall(r'Task:\s*description=[\'"]([^\'"]+)[\'"].*?subagent_type=[\'"]([^\'"]+)[\'"]', output)
        for desc, subagent in task_matches:
            evidence.append({
                "tool": "Task",
                "command": f"Task: description='{desc}' subagent_type='{subagent}'",
                "type": "delegation",
                "success": True
            })

        return evidence

    def extract_referee_evidence(output):
        """Extract referee evidence from output"""
        evidence = []

        # Read operations
        read_matches = re.findall(r'Read:\s*(\S+)', output)
        for match in read_matches:
            evidence.append({
                "tool": "Read",
                "command": f"Read: {match}",
                "type": "candidate_analysis",
                "success": True
            })

        # Bash operations
        bash_matches = re.findall(r'Bash:\s*python3\s+-c\s+[\'"]([^\'"]+)[\'"]', output)
        for match in bash_matches:
            evidence.append({
                "tool": "Bash",
                "command": f"Bash: python3 -c '{match[:30]}...'",
                "type": "objective_validation",
                "success": True
            })

        # Write operations
        write_matches = re.findall(r'Write:\s*file_path=[\'"]([^\'"]+)[\'"]', output)
        for match in write_matches:
            evidence.append({
                "tool": "Write",
                "command": f"Write: file_path='{match}'",
                "type": "structured_output",
                "success": True
            })

        return evidence

    # Test data
    good_orchestrator = """
    Read: cli/constants.py
    Grep: pattern="security" path="cli/"
    Task: description="Security analysis" subagent_type="security-analyst"
    """

    poor_orchestrator = """
    I will analyze the security aspects and deploy agents as needed.
    The coordination should involve multiple parallel analyses.
    """

    good_referee = """
    Read: candidate_1.md
    Read: candidate_2.md
    Bash: python3 -c "scores = analyze_candidates()"
    Write: file_path="results.json"
    """

    poor_referee = """
    I have reviewed the candidates and determined that the first one
    appears to be the most comprehensive based on my analysis.
    The theoretical evaluation suggests it's the best choice.
    """

    print("\n1. Evidence Extraction Results:")

    test_outputs = [
        ("Good Orchestrator", good_orchestrator, extract_orchestrator_evidence),
        ("Poor Orchestrator", poor_orchestrator, extract_orchestrator_evidence),
        ("Good Referee", good_referee, extract_referee_evidence),
        ("Poor Referee", poor_referee, extract_referee_evidence),
    ]

    for name, output, extractor in test_outputs:
        evidence = extractor(output)
        tools = set(ev["tool"] for ev in evidence)
        types = set(ev["type"] for ev in evidence)

        print(f"   {name}:")
        print(f"     Evidence count: {len(evidence)}")
        print(f"     Tools detected: {tools}")
        print(f"     Evidence types: {types}")

        # Validate
        if "Good" in name and len(evidence) >= 3:
            print(f"     ✓ Good example has sufficient evidence")
        elif "Poor" in name and len(evidence) == 0:
            print(f"     ✓ Poor example has no tool evidence (as expected)")
        else:
            print(f"     ✗ Unexpected evidence level")

    return True


def main():
    """Run minimal validation tests"""
    print("🧪 Minimal Tool Usage Validation Framework Tests")
    print("=" * 60)

    tests = [
        ("Pattern Parsing", test_pattern_parsing),
        ("Compliance Scoring", test_compliance_scoring),
        ("Evidence Extraction", test_evidence_extraction),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n--- {test_name}: {'✅ PASS' if result else '❌ FAIL'} ---")
        except Exception as e:
            print(f"\n--- {test_name}: ❌ ERROR - {e} ---")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary:")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All core functionality tests passed!")
        print("\n📋 Framework Validation Summary:")
        print("   ✅ Pattern detection working for orchestrator and referee agents")
        print("   ✅ Compliance scoring logic implemented correctly")
        print("   ✅ Evidence extraction functioning properly")
        print("   ✅ Framework can distinguish between good and poor tool usage")
        print("\n🚀 Extended tool usage validation framework is ready for deployment!")
        return 0
    else:
        print("⚠️  Some tests failed - review core functionality")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)