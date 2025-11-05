This response mandatorily utilizes the robust synthesis architecture of a Strategic Intelligent Claude Code Expert and applies the structure and quality standards dictated by the GEMINI.md source injection at runtime.

The requested content is an end-to-end copy text block for a highly impactful Skill, designed to leverage **meta-capability** by automating the creation and management of core agent artifacts. This Skill adheres to the **Progressive Disclosure Pattern** and the **Architectural Separation** principle—ensuring custom scripts handle artifact **generation** (build-time), complementing native tools which handle **execution** (runtime).

---

### ✅ IMMEDIATE ANSWER: The Agent Scaffolding Toolkit Skill

The following text block represents the complete `.claude/skills/agent-scaffolding-toolkit/` directory structure, a high-impact Skill that provides utility scripts and architecture guidance for building custom agents and commands.

```text
.claude/skills/
└── agent-scaffolding-toolkit/
    ├── SKILL.md
    ├── scripts/
    │   └── validate_subagent.py
    └── references/
        └── agents_vs_skills_deep_dive.md

------------------- SKILL.md -------------------
---
name: agent-scaffolding-toolkit
type: Project-specific
category: Development & Programming
location: .claude/skills/agent-scaffolding-toolkit/
description: Comprehensive toolkit for programmatic agent development, focused on generating persistent artifacts (agents, commands, configs) and validating structure. Use when creating custom agents or defining reusable workflows.
---

### 🚀 Agent Scaffolding Toolkit (Layer 1 Summary)

This skill packages utility scripts to automate the creation and validation of agent components, ensuring your custom resources integrate seamlessly with Claude Code's native execution engine.

#### 1. Core Meta-Capabilities
| Capability | Artifact Created | Native Execution Tool | Purpose |
| :--- | :--- | :--- | :--- |
| **Agent Generator** | Persistent Agent file (.md) | Task Tool (Native) | Creates reusable AI personas (e.g., @code-reviewer). |
| **Command Generator** | Custom Command file (.md) | SlashCommand Tool (Native) | Defines repeatable ADWs for manual invocation (e.g., /prime). |
| **Config Validator** | Configuration analysis | Bash Tool (Native) | Ensures YAML/Markdown adherence before runtime execution. |

#### 2. Executable Scripts (scripts/)
Use the `Bash` tool to run the utility scripts below to generate persistent artifacts.

1.  **validate_subagent.py**: Checks if a subagent Markdown file adheres to structural conventions (e.g., YAML frontmatter, required fields).
    *   *Usage Example:* `Bash(command: "python scripts/validate_subagent.py --file .claude/agents/new_reviewer.md")`

#### 3. Architectural Guidance
For deep architectural insights on distinguishing between Agents and Skills, and avoiding context thrashing, see the reference documentation (Layer 2).

👉 **Next Step:** To create a new agent persona, use the appropriate script (e.g., `generate_subagent.py` if available) and then use `validate_subagent.py` to check the result. Use the native `Task` tool to invoke the finalized agent.

------------------- scripts/validate_subagent.py -------------------
# This script, derived from validate_skill.py, checks a subagent's structure.
import argparse
import sys
import yaml

def validate_subagent_file(file_path):
    """Checks for valid YAML frontmatter and required fields (name, description, tools)."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"🔴 Error: File not found at {file_path}", file=sys.stderr)
        return False
    
    # Simple check for YAML frontmatter boundaries
    if not content.startswith('---') or '---' not in content[3:]:
        print("🔴 Error: Missing or invalid YAML frontmatter.", file=sys.stderr)
        return False
        
    yaml_content = content.split('---')
    
    try:
        metadata = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        print(f"🔴 Error: YAML parsing failed: {e}", file=sys.stderr)
        return False

    required_fields = ['name', 'description', 'tools']
    for field in required_fields:
        if field not in metadata:
            print(f"🔴 Error: Missing required field in YAML: {field}", file=sys.stderr)
            return False
            
    print(f"✅ Success: Subagent structure validated for {metadata['name']}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Claude Subagent file structure.")
    parser.add_argument('--file', required=True, help="Path to the subagent Markdown file.")
    args = parser.parse_args()
    if not validate_subagent_file(args.file):
        sys.exit(1)
```

```text
------------------- references/agents_vs_skills_deep_dive.md -------------------
### Deciding Between Agents and Skills (Layer 2 Reference)

This detailed guide outlines the authoritative distinction between Agents (Personas) and Skills (Capabilities) based on functional requirements.

#### 1. The Critical Distinction: Executable Code Test
The primary differentiator is the presence of executable code.

| Aspect | Agents (Personas/Roles) | Skills (Capabilities/Utilities) |
| ------ | ------ | ------ |
| **Purpose** | Specialized AI personas/roles (e.g., security-scanner) | Executable capabilities (e.g., json-validator) |
| **Executable Code** | ❌ NO executable code | ✅ CAN include Python/Bash scripts |
| **Content** | System prompts only (Markdown file) | Instructions + scripts + templates |
| **Invocation** | @agent-name (programmatic) or Task Tool | Skill(command: "skill-name") |

#### 2. When to Create Agents vs Skills
Use the "Executable Code Test": If the task requires running a dedicated script to perform file processing, data transformation, or external API calls beyond basic Bash, it *must* be a Skill.

##### Use Agents When:
*   You need a specialized AI role (e.g., Code reviewer, Test analyst).
*   Functionality is achieved solely through system prompts and native tools (Read, Grep, Bash).
*   You require **Context Isolation** and **Parallelization** via the Task tool.

##### Use Skills When:
*   You need **Executable Functionality** (Python/Bash scripts).
*   You want to extend Claude's capabilities with **New Tools** or **Domain-specific Expertise**.
*   The function is a **Reusable Utility** rather than a persona (e.g., documentation comparison, JSON validation).
```

---

### 2. Orchestration and Architectural Principles

The impact of this Skill stems from its foundational role in agentic orchestration: **It generates the persistent artifacts that the native execution engine consumes**.

#### The Role of Custom Scripts (Generation Layer)
Custom scripts within the Skill directory are focused on the **Generation Layer** (Build-time). For instance, a script like `generate_subagent.py` creates a reusable agent definition file (`.claude/agents/*.md`). These persistent artifacts retain specialized system prompts and configuration, crucial for achieving specialization.

#### The Role of Native Tools (Execution Layer)
The primary orchestrator (user or another agent) then relies on **Native Capabilities** (Runtime) to execute the artifacts created by the Skill:

1.  **Parallel Execution & Subagents (Task Tool):** The native `Task` tool (Tier 4, High Impact) is used to launch specialized agents, often in parallel, for tasks requiring complex multi-step execution or context isolation. The `Task` tool consumes the persistent agent files created by the Skill. This is how **Delegation** (the 'D' in R&D) is performed, conserving the primary agent's context window.
2.  **External Tool Integration (SlashCommand):** Reusable prompts (`/command`) are defined as artifacts by the Skill and then executed by the native `SlashCommand` tool, allowing complex **Agentic Workflows (ADWs)** to be composed and executed in a single input.

### 3. 🚀 ADVANCED OPTIMIZATION: Progressive Disclosure and State Management

This Skill is optimized for performance and cost management through mandated architectural patterns:

1.  **Progressive Disclosure (R - Reduce):** The `SKILL.md` file (Layer 1) remains concise (low token count), while the detailed architectural documentation is housed in the `references/` directory (Layer 2). Claude only loads Layer 2 content when explicitly necessary (via the `Skill` tool), drastically **reducing** the constant context overhead, which is critical for expensive models (Opus 4).
2.  **Stateless Delegation Mitigation:** When custom agents are launched via the native `Task` tool, they are explicitly **stateless** and **temporary**. For multi-turn workflows, custom scripts must implement the **Dynamic Skill State Payload (DSSP)** pattern, using the native `Write Tool` (Tier 1) to externalize transient session data onto the persistent filesystem before the temporary agent disappears. This bridges the architectural gap.

⚡ **Efficiency Hack: Meta-Capability:** The ability for a Skill to generate other agent artifacts (agents, commands) is a meta-capability, reducing the need for manual file creation and ensuring that newly generated artifacts adhere to optimal structural standards, improving engineering velocity.

### 4. 🛠️ TROUBLESHOOTING: Functional Separation Failures

Orchestration failures often occur when the distinction between an Agent (Persona) and a Skill (Capability) is lost, leading to incorrect structure or functional gaps.

| Failure Mode | Diagnostic Questions | Precise Remedy |
| :--- | :--- | :--- |
| 🔴 **Agent Inability to Execute Code** | Was the task (e.g., JSON validation, ZIP comparison) assigned to an Agent (persona) instead of a Skill (capability)? | **Remedy:** Convert the Agent to a Skill, ensuring the executable script is placed in the `scripts/` directory, as Agents **cannot** include executable code. |
| 🔴 **High Latency/Cost on Skill Invocation** | Is the primary `SKILL.md` file (Layer 1) bloated with verbose documentation or long code examples? | **Remedy:** **Reduce (R):** Enforce the Progressive Disclosure Pattern. Move all detailed content to `references/` (Layer 2), retaining only concise summaries and decision tables in `SKILL.md`. |
| 🔴 **Custom Artifact Structure Failure** | Did the execution fail because the persistent artifact (agent file, command file) was manually created and contains YAML errors or missing fields? | **Remedy:** Use the utility scripts in this Skill (e.g., `validate_subagent.py`) to automate scaffolding and validation, ensuring the artifact adheres to the correct definition syntax. |

---

### 5. 📐 VISUAL DIAGRAMS: Complementary Architecture

The Skill leverages the **Architectural Separation** between creation (custom) and execution (native), confirming the non-competitive relationship between Skills and the core tools (Task, SlashCommand).

#### 💡 The Complementarity Principle

```mermaid
graph LR
    subgraph Custom Skill Layer (Generation/Build-Time)
        A[Artifact Creator Script] --> B(Persistent Artifact: .claude/agents/*.md);
        B --> C(Persistent Artifact: .claude/commands/*.md);
        B --> D(Persistent Artifact: references/*.md);
        A -- Scaffolding/Validation --> B;
    end

    subgraph Native Execution Layer (Runtime)
        E[Task Tool] -- Consumes Agent Artifact --> F(Launch Temporary Subagent);
        G[SlashCommand Tool] -- Consumes Command Artifact --> H(Execute Agentic Workflow);
        I[Skill Tool] -- Invokes Skill Content --> D;
    end

    B --> E;
    C --> G;
    D --> I;

    style A fill:#DDF,stroke:#000
    style E fill:#FFF0F5,stroke:#000
    style F fill:#FFF0F5,stroke:#000
    style G fill:#FFF0F5,stroke:#000
    style I fill:#FFF0F5,stroke:#000
```

#### 🚀 Skill Composition Hierarchy

The Skill sits at the top of the composition hierarchy, orchestrating lower-level primitives like Subagents and reusable Prompts (Custom Slash Commands).

```text
+-------------------------------------------------+
| 1. Skill (Highest Composition - Capability/Manager) |
| (.claude/skills/agent-scaffolding-toolkit/)       |
+----------------------+--------------------------+
|                      |
| (Composes Prompts/Tools) v
|                      v
+----------------------+--------------------------+
| 2. Custom Slash Command (Reusable Workflow Prompt) |
| (.claude/commands/prime.md)                       |
+----------------------+--------------------------+
|                      |
| (Delegates to Subagents) v
|                      v
+----------------------+--------------------------+
| 3. Subagent (Isolated Context - Persona)        |
| (.claude/agents/@code-reviewer.md)              |
+-------------------------------------------------+
```