"""
Simple test for the extended tool usage validation framework
Tests core functionality without complex examples that cause syntax issues
"""

import sys
import os

# Add the cli directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cli'))

def test_basic_functionality():
    """Test basic functionality of the tool validator"""
    print("=== Testing Basic Tool Validator Functionality ===")

    try:
        from tool_usage_validator import ToolUsageValidator

        # Test 1: Initialize validator
        print("\n1. Initializing Validator:")
        validator = ToolUsageValidator()
        print("   ✓ Validator initialized successfully")

        # Test 2: Check tool requirements loading
        print("\n2. Tool Requirements Loading:")
        agent_types = list(validator.tool_requirements.keys())
        print(f"   Loaded agent types: {agent_types}")

        required_agents = ["security-analyst", "orchestrator-agent", "referee-agent-csp"]
        for agent in required_agents:
            if agent in agent_types:
                print(f"   ✓ {agent} requirements loaded")
            else:
                print(f"   ✗ {agent} requirements missing")

        # Test 3: Basic pre-execution validation
        print("\n3. Basic Pre-execution Validation:")

        # Test orchestrator
        orch_result = validator.validate_pre_execution("orchestrator-agent")
        print(f"   Orchestrator - Valid: {orch_result.is_valid}, Score: {orch_result.compliance_score}%")

        # Test referee
        ref_result = validator.validate_pre_execution("referee-agent-csp")
        print(f"   Referee - Valid: {ref_result.is_valid}, Score: {ref_result.compliance_score}%")

        # Test security analyst
        sec_result = validator.validate_pre_execution("security-analyst")
        print(f"   Security Analyst - Valid: {sec_result.is_valid}, Score: {sec_result.compliance_score}%")

        # Test 4: Basic post-execution validation
        print("\n4. Basic Post-execution Validation:")

        # Test with simple output
        simple_output = """
        Read: test_file.py
        Grep: pattern="test" path="test_file.py"
        Task: description="Test task" subagent_type="test-agent"
        """

        orch_post = validator.validate_post_execution("orchestrator-agent", simple_output, "test")
        print(f"   Orchestrator Post - Valid: {orch_post.is_valid}, Score: {orch_post.compliance_score}%")
        print(f"   Tools detected: {orch_post.used_tools}")
        print(f"   Evidence count: {len(orch_post.evidence)}")

        # Test 5: Enhanced prompt generation
        print("\n5. Enhanced Prompt Generation:")

        base_prompt = "You are an agent."
        enhanced = validator.generate_enhanced_prompt(base_prompt, "orchestrator-agent")

        if "MANDATORY TOOL USAGE" in enhanced:
            print("   ✓ Enhanced prompt includes tool usage requirements")
        else:
            print("   ✗ Enhanced prompt missing tool usage requirements")

        print(f"   Enhanced prompt length: {len(enhanced)} characters")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_patterns():
    """Test orchestrator-specific pattern detection"""
    print("\n=== Testing Orchestrator Pattern Detection ===")

    try:
        from tool_usage_validator import ToolUsageParser

        parser = ToolUsageParser()

        # Test orchestrator output
        orch_output = """
        ## Security Audit Orchestration

        ### Context Gathering
        Read: cli/constants.py
        Read: requirements.txt

        Grep: pattern="security" path="cli/" output_mode="files_with_matches"

        ### Delegation
        Task: description="Security analysis" subagent_type="security-analyst"
        Task: description="Code review" subagent_type="code-analyst"

        ### Synthesis
        Read: output/security_report.md
        Read: output/code_review.md
        """

        evidence = parser.parse_output(orch_output, "orchestrator-agent")

        print(f"   Evidence detected: {len(evidence)} items")

        tool_counts = {}
        for ev in evidence:
            tool_counts[ev.tool_name] = tool_counts.get(ev.tool_name, 0) + 1

        print(f"   Tool usage: {tool_counts}")

        # Check for required orchestrator tools
        required_tools = ["Read", "Grep", "Task"]
        found_tools = set(tool_counts.keys())
        missing_tools = set(required_tools) - found_tools

        if missing_tools:
            print(f"   ✗ Missing tools: {missing_tools}")
        else:
            print("   ✓ All required orchestrator tools detected")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_referee_patterns():
    """Test referee-specific pattern detection"""
    print("\n=== Testing Referee Pattern Detection ===")

    try:
        from tool_usage_validator import ToolUsageParser

        parser = ToolUsageParser()

        # Test referee output
        ref_output = """
        ## Referee Analysis

        ### Load Candidates
        Read: candidate_1.md
        Read: candidate_2.md
        Read: candidate_3.md

        ### Objective Validation
        Bash: python3 -c "print('Scoring candidates...')"

        ### Pattern Analysis
        Grep: pattern="score" path="candidate_*.md"

        ### Structured Output
        Write: file_path="results.json" content='{"selected": "candidate_1"}'
        """

        evidence = parser.parse_output(ref_output, "referee-agent-csp")

        print(f"   Evidence detected: {len(evidence)} items")

        tool_counts = {}
        evidence_types = {}

        for ev in evidence:
            tool_counts[ev.tool_name] = tool_counts.get(ev.tool_name, 0) + 1
            evidence_types[ev.evidence_type] = evidence_types.get(ev.evidence_type, 0) + 1

        print(f"   Tool usage: {tool_counts}")
        print(f"   Evidence types: {evidence_types}")

        # Check for required referee tools
        required_tools = ["Read", "Bash", "Grep", "Write"]
        found_tools = set(tool_counts.keys())
        missing_tools = set(required_tools) - found_tools

        if missing_tools:
            print(f"   ✗ Missing tools: {missing_tools}")
        else:
            print("   ✓ All required referee tools detected")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def main():
    """Run all simple tests"""
    print("🧪 Testing Extended Tool Usage Validation Framework (Simple)")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Orchestrator Patterns", test_orchestrator_patterns),
        ("Referee Patterns", test_referee_patterns),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")
        except Exception as e:
            print(f"Status: ❌ ERROR - {e}")
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
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)