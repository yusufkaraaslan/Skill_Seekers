"""
Test script for the extended tool usage validation framework
Tests orchestrator and referee agent validation on the security audit scenario
"""

import sys
import os
import json
from pathlib import Path

# Add the cli directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cli'))

from tool_usage_validator import ToolUsageValidator, ToolUsageEvidence


def test_orchestrator_validation():
    """Test orchestrator agent validation with security audit scenario"""
    print("=== Testing Orchestrator Agent Validation ===")

    validator = ToolUsageValidator(
        config_path="../.claude/configs/tool_usage_requirements.yaml"
    )

    # Test 1: Pre-execution validation
    print("\n1. Pre-execution Validation:")
    pre_result = validator.validate_pre_execution("orchestrator-agent")
    print(f"   Valid: {pre_result.is_valid}")
    print(f"   Compliance: {pre_result.compliance_score}%")
    print(f"   Available Tools: {pre_result.used_tools}")
    print(f"   Missing Tools: {pre_result.missing_tools}")
    print(f"   Details: {pre_result.validation_details}")

    # Test 2: Post-execution validation with proper tool usage
    print("\n2. Post-execution Validation (With Proper Tool Usage):")
    orchestrator_output = """
    ## Security Audit Orchestration

    ### Step 1: Context Gathering
    Read: cli/constants.py
    Read: requirements.txt
    Read: .claude/agents/security-analyst.md

    Grep: pattern="security" path="cli/" output_mode="files_with_matches"
    Grep: pattern="import.*requests" path="cli/" output_mode="content"

    Found 3 security-related files and HTTP imports in main modules.

    ### Step 2: Parallel Delegation
    Task: description="Web scraping security analysis" subagent_type="security-analyst"
    Task: description="GitHub integration security analysis" subagent_type="security-analyst"
    Task: description="PDF processing security analysis" subagent_type="security-analyst"

    Deployed 3 parallel security analysis tasks.

    ### Step 3: Result Synthesis
    Read: output/web_scraping_analysis.md
    Read: output/github_integration_analysis.md
    Read: output/pdf_processing_analysis.md

    Synthesized findings from 3 security domains.
    """

    post_result = validator.validate_post_execution(
        "orchestrator-agent",
        orchestrator_output,
        "orchestrator-test"
    )
    print(f"   Valid: {post_result.is_valid}")
    print(f"   Compliance: {post_result.compliance_score}%")
    print(f"   Used Tools: {post_result.used_tools}")
    print(f"   Missing Tools: {post_result.missing_tools}")
    print(f"   Evidence Count: {len(post_result.evidence)}")
    print(f"   Details: {post_result.validation_details}")

    # Test 3: Post-execution validation with poor tool usage
    print("\n3. Post-execution Validation (Poor Tool Usage):")
    poor_orchestrator_output = """
    ## Security Audit Orchestration

    I analyzed the security requirements and decided to deploy security analysts
    to examine different aspects of the codebase. Based on my understanding,
    I would coordinate three parallel analyses focusing on web scraping, GitHub
    integration, and PDF processing security.

    The subagents would then provide their findings which I would synthesize
    into a comprehensive security report.
    """

    poor_result = validator.validate_post_execution(
        "orchestrator-agent",
        poor_orchestrator_output,
        "orchestrator-poor"
    )
    print(f"   Valid: {poor_result.is_valid}")
    print(f"   Compliance: {poor_result.compliance_score}%")
    print(f"   Used Tools: {poor_result.used_tools}")
    print(f"   Missing Tools: {poor_result.missing_tools}")
    print(f"   Recommendations: {poor_result.recommendations[:2]}")  # First 2 recommendations

    return pre_result, post_result, poor_result


def test_referee_validation():
    """Test referee agent validation with security audit scenario"""
    print("\n=== Testing Referee Agent Validation ===")

    validator = ToolUsageValidator(
        config_path="../.claude/configs/tool_usage_requirements.yaml"
    )

    # Test 1: Pre-execution validation
    print("\n1. Pre-execution Validation:")
    pre_result = validator.validate_pre_execution("referee-agent-csp")
    print(f"   Valid: {pre_result.is_valid}")
    print(f"   Compliance: {pre_result.compliance_score}%")
    print(f"   Available Tools: {pre_result.used_tools}")
    print(f"   Missing Tools: {pre_result.missing_tools}")
    print(f"   Details: {pre_result.validation_details}")

    # Test 2: Post-execution validation with proper tool usage
    print("\n2. Post-execution Validation (With Proper Tool Usage):")
    referee_output = """
    ## Security Analysis Referee Synthesis

    ### Step 1: Load Specification
    Read: security_audit_specification.md
    Extracted criteria: Must identify vulnerabilities, provide CVSS scores, include remediation steps

    ### Step 2: Load All Candidates
    Read: candidate_1_security_analysis.md
    Read: candidate_2_security_analysis.md
    Read: candidate_3_security_analysis.md

    Loaded 3 candidate analyses with varying detail levels.

    ### Step 3: Objective Validation
    Bash: python3 -c "
    import json
    import re

    def analyze_candidate(filename):
        with open(filename) as f:
            content = f.read()
        return {
            'vulnerability_count': len(re.findall(r'vulnerability|CVE-', content, re.IGNORECASE)),
            'tool_usage': len(re.findall(r'bash:|pip-audit|safety', content)),
            'remediation_steps': len(re.findall(r'recommend|fix', content, re.IGNORECASE))
        }

    scores = {}
    for i in range(1, 4):
        scores[f'candidate_{i}'] = analyze_candidate(f'candidate_{i}_security_analysis.md')

    print(json.dumps(scores, indent=2))
    "

    Output: {"candidate_1": {"vulnerability_count": 8, "tool_usage": 3}, "candidate_2": {"vulnerability_count": 5, "tool_usage": 0}}

    ### Step 4: Pattern Analysis
    Grep: pattern="critical|high" path="candidate_*_security_analysis.md" output_mode="content" -n
    Grep: pattern="bash:" path="candidate_*_security_analysis.md" output_mode="content" -n

    Found critical issues in candidate_1 only.

    ### Step 5: Selection and Structured Output
    Write: file_path="synthesis_results.json" content='{"status": "SUCCESS", "selected_candidate": "candidate_1", "score": 85, "selection_reason": "Most comprehensive analysis with tool usage evidence"}'
    """

    post_result = validator.validate_post_execution(
        "referee-agent-csp",
        referee_output,
        "referee-test"
    )
    print(f"   Valid: {post_result.is_valid}")
    print(f"   Compliance: {post_result.compliance_score}%")
    print(f"   Used Tools: {post_result.used_tools}")
    print(f"   Missing Tools: {post_result.missing_tools}")
    print(f"   Evidence Count: {len(post_result.evidence)}")
    print(f"   Details: {post_result.validation_details}")

    # Test 3: Post-execution validation with theoretical analysis
    print("\n3. Post-execution Validation (Theoretical Analysis Only):")
    poor_referee_output = """
    ## Security Analysis Referee Synthesis

    I analyzed the three security audit candidates and determined that candidate 1
    appears to be the most comprehensive. Based on my review of the content,
    it identifies more vulnerabilities and provides better analysis.

    The theoretical scoring suggests candidate 1 would be the best choice,
    though I did not execute any validation commands to verify the actual
    findings.

    Candidate 2 seems adequate but less detailed, while candidate 3
    appears to have some good points but lacks depth.
    """

    poor_result = validator.validate_post_execution(
        "referee-agent-csp",
        poor_referee_output,
        "referee-poor"
    )
    print(f"   Valid: {poor_result.is_valid}")
    print(f"   Compliance: {poor_result.compliance_score}%")
    print(f"   Used Tools: {poor_result.used_tools}")
    print(f"   Missing Tools: {poor_result.missing_tools}")
    print(f"   Recommendations: {poor_result.recommendations[:2]}")  # First 2 recommendations

    return pre_result, post_result, poor_result


def test_enhanced_prompts():
    """Test enhanced prompt generation for orchestrator and referee agents"""
    print("\n=== Testing Enhanced Prompt Generation ===")

    validator = ToolUsageValidator(
        config_path="../.claude/configs/tool_usage_requirements.yaml"
    )

    # Test orchestrator prompt enhancement
    print("\n1. Orchestrator Prompt Enhancement:")
    base_prompt = "You are an orchestrator agent. Coordinate security analysis."
    enhanced_orchestrator = validator.generate_enhanced_prompt(base_prompt, "orchestrator-agent")

    # Check for key requirements
    assert "MANDATORY TOOL USAGE REQUIREMENTS" in enhanced_orchestrator
    assert "Read tool" in enhanced_orchestrator
    assert "Grep tool" in enhanced_orchestrator
    assert "Task tool" in enhanced_orchestrator
    assert "EVIDENCE REQUIRED" in enhanced_orchestrator
    print("   ✓ All required orchestrator tool usage elements present")

    # Test referee prompt enhancement
    print("\n2. Referee Prompt Enhancement:")
    base_prompt = "You are a referee agent. Analyze candidates."
    enhanced_referee = validator.generate_enhanced_prompt(base_prompt, "referee-agent-csp")

    # Check for key requirements
    assert "MANDATORY TOOL USAGE REQUIREMENTS" in enhanced_referee
    assert "Read tool" in enhanced_referee
    assert "Bash tool" in enhanced_referee
    assert "NO THEORETICAL ANALYSIS" in enhanced_referee
    assert "Write tool" in enhanced_referee
    print("   ✓ All required referee tool usage elements present")

    return enhanced_orchestrator, enhanced_referee


def test_compliance_reporting():
    """Test enhanced compliance reporting with orchestrator and referee metrics"""
    print("\n=== Testing Enhanced Compliance Reporting ===")

    validator = ToolUsageValidator(
        config_path="../.claude/configs/tool_usage_requirements.yaml"
    )

    # Simulate some history
    validator.compliance_history = [
        {
            "timestamp": "2025-01-04T10:00:00",
            "agent_id": "orchestrator-1",
            "agent_type": "orchestrator-agent",
            "compliance_score": 85.0,
            "used_tools": ["Read", "Grep", "Task"],
            "missing_tools": ["Bash"],
            "evidence_count": 6,
            "validation_details": {
                "context_gathering": 2,
                "delegation_events": 3,
                "monitoring_events": 0,
                "parallel_execution": True
            }
        },
        {
            "timestamp": "2025-01-04T10:05:00",
            "agent_id": "referee-1",
            "agent_type": "referee-agent-csp",
            "compliance_score": 75.0,
            "used_tools": ["Read", "Bash", "Write"],
            "missing_tools": ["Grep", "Task"],
            "evidence_count": 4,
            "validation_details": {
                "candidate_analysis": 3,
                "objective_validation": 1,
                "pattern_analysis": 0,
                "structured_output": 1,
                "deterministic_selection": False
            }
        },
        {
            "timestamp": "2025-01-04T10:10:00",
            "agent_id": "orchestrator-2",
            "agent_type": "orchestrator-agent",
            "compliance_score": 45.0,
            "used_tools": ["Task"],
            "missing_tools": ["Read", "Grep", "Bash"],
            "evidence_count": 1,
            "validation_details": {
                "context_gathering": 0,
                "delegation_events": 1,
                "monitoring_events": 0,
                "parallel_execution": False
            }
        }
    ]

    report = validator.get_compliance_report()

    print(f"Total Executions: {report['total_executions']}")
    print(f"Average Compliance: {report['average_compliance']}%")
    print(f"Compliance Trend: {report['compliance_trend']}")

    # Check orchestrator metrics
    if 'orchestrator_metrics' in report:
        orch_metrics = report['orchestrator_metrics']
        print(f"\nOrchestrator Metrics:")
        print(f"   Context Gathering Rate: {orch_metrics.get('context_gathering_rate', 0):.1f}%")
        print(f"   Average Delegations: {orch_metrics.get('average_delegations_per_execution', 0):.1f}")
        print(f"   Parallel Execution Rate: {orch_metrics.get('parallel_execution_rate', 0):.1f}%")

    # Check referee metrics
    if 'referee_metrics' in report:
        ref_metrics = report['referee_metrics']
        print(f"\nReferee Metrics:")
        print(f"   Objective Validation Rate: {ref_metrics.get('objective_validation_rate', 0):.1f}%")
        print(f"   Structured Output Rate: {ref_metrics.get('structured_output_rate', 0):.1f}%")
        print(f"   Deterministic Selection Rate: {ref_metrics.get('deterministic_selection_rate', 0):.1f}%")

    # Check recommendations
    if report['recommendations']:
        print(f"\nSystem Recommendations:")
        for rec in report['recommendations'][:3]:  # First 3 recommendations
            print(f"   - {rec}")

    return report


def test_security_audit_scenario():
    """Test the complete security audit scenario with enhanced validation"""
    print("\n=== Testing Complete Security Audit Scenario ===")

    validator = ToolUsageValidator(
        config_path="../.claude/configs/tool_usage_requirements.yaml"
    )

    # Simulate the security audit workflow
    workflow_results = {}

    # 1. Orchestrator pre-execution validation
    print("\n1. Orchestrator Pre-execution:")
    orch_pre = validator.validate_pre_execution("orchestrator-agent")
    workflow_results['orchestrator_pre'] = orch_pre
    print(f"   Status: {'✓ PASS' if orch_pre.is_valid else '✗ FAIL'} ({orch_pre.compliance_score}%)")

    # 2. Orchestrator execution (theoretically good)
    print("\n2. Orchestrator Execution:")
    orch_execution = """
    ## Security Audit Orchestration

    ### Context Gathering
    Read: cli/constants.py
    Read: requirements.txt
    Grep: pattern="security" path="cli/" output_mode="files_with_matches"

    ### Parallel Delegation
    Task: description="Web scraping security" subagent_type="security-analyst"
    Task: description="GitHub integration security" subagent_type="security-analyst"
    Task: description="PDF processing security" subagent_type="security-analyst"

    ### Result Synthesis
    Read: output/web_scraping_analysis.md
    Read: output/github_integration_analysis.md
    Read: output/pdf_processing_analysis.md
    """

    orch_post = validator.validate_post_execution("orchestrator-agent", orch_execution, "security-orchestrator")
    workflow_results['orchestrator_post'] = orch_post
    print(f"   Status: {'✓ PASS' if orch_post.is_valid else '✗ FAIL'} ({orch_post.compliance_score}%)")

    # 3. Referee pre-execution validation
    print("\n3. Referee Pre-execution:")
    ref_pre = validator.validate_pre_execution("referee-agent-csp")
    workflow_results['referee_pre'] = ref_pre
    print(f"   Status: {'✓ PASS' if ref_pre.is_valid else '✗ FAIL'} ({ref_pre.compliance_score}%)")

    # 4. Referee execution (theoretically good)
    print("\n4. Referee Execution:")
    ref_execution = """
    ## Security Analysis Referee Synthesis

    ### Load Specification and Candidates
    Read: security_specification.md
    Read: web_scraping_analysis.md
    Read: github_integration_analysis.md
    Read: pdf_processing_analysis.md

    ### Objective Validation
    Bash: python3 -c "
    scores = {'web_scraping': 85, 'github_integration': 75, 'pdf_processing': 90}
    print('Best candidate: pdf_processing')
    "

    ### Pattern Analysis
    Grep: pattern="CRITICAL|HIGH" path="*analysis.md" output_mode="content"

    ### Structured Output
    Write: file_path="synthesis_results.json" content='{"selected": "pdf_processing", "score": 90}'
    """

    ref_post = validator.validate_post_execution("referee-agent-csp", ref_execution, "security-referee")
    workflow_results['referee_post'] = ref_post
    print(f"   Status: {'✓ PASS' if ref_post.is_valid else '✗ FAIL'} ({ref_post.compliance_score}%)")

    # 5. Overall assessment
    print("\n5. Overall Security Audit Assessment:")
    total_steps = len(workflow_results)
    passed_steps = sum(1 for result in workflow_results.values() if result.is_valid)

    print(f"   Steps Passed: {passed_steps}/{total_steps}")
    print(f"   Overall Status: {'✓ SUCCESS' if passed_steps == total_steps else '⚠ PARTIAL SUCCESS' if passed_steps >= 3 else '✗ FAILURE'}")

    # 6. Key insights
    print("\n6. Key Validation Insights:")
    for step_name, result in workflow_results.items():
        if not result.is_valid:
            print(f"   {step_name}: {', '.join(result.missing_tools[:2])} missing")
        elif result.compliance_score < 80:
            print(f"   {step_name}: Low compliance ({result.compliance_score}%)")

    return workflow_results


def main():
    """Run all tests"""
    print("🧪 Testing Extended Tool Usage Validation Framework")
    print("=" * 60)

    try:
        # Test individual agent validations
        test_orchestrator_validation()
        test_referee_validation()

        # Test enhanced prompts
        test_enhanced_prompts()

        # Test compliance reporting
        test_compliance_reporting()

        # Test complete scenario
        test_security_audit_scenario()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)