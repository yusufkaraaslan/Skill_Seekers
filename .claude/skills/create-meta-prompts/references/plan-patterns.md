<overview>
Prompt patterns for creating approaches, roadmaps, and strategies that will be consumed by subsequent prompts.
</overview>

<prompt_template>
```xml
<objective>
Create a {plan type} for {topic}.

Purpose: {What decision/implementation this enables}
Input: {Research or context being used}
Output: {topic}-plan.md with actionable phases/steps
</objective>

<context>
Research findings: @.prompts/{num}-{topic}-research/{topic}-research.md
{Additional context files}
</context>

<planning_requirements>
{What the plan needs to address}
{Constraints to work within}
{Success criteria for the planned outcome}
</planning_requirements>

<output_structure>
Save to: `.prompts/{num}-{topic}-plan/{topic}-plan.md`

Structure the plan using this XML format:

```xml
<plan>
  <summary>
    {One paragraph overview of the approach}
  </summary>

  <phases>
    <phase number="1" name="{phase-name}">
      <objective>{What this phase accomplishes}</objective>
      <tasks>
        <task priority="high">{Specific actionable task}</task>
        <task priority="medium">{Another task}</task>
      </tasks>
      <deliverables>
        <deliverable>{What's produced}</deliverable>
      </deliverables>
      <dependencies>{What must exist before this phase}</dependencies>
    </phase>
    <!-- Additional phases -->
  </phases>

  <metadata>
    <confidence level="{high|medium|low}">
      {Why this confidence level}
    </confidence>
    <dependencies>
      {External dependencies needed}
    </dependencies>
    <open_questions>
      {Uncertainties that may affect execution}
    </open_questions>
    <assumptions>
      {What was assumed in creating this plan}
    </assumptions>
  </metadata>
</plan>
```
</output_structure>

<summary_requirements>
Create `.prompts/{num}-{topic}-plan/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For plans, emphasize phase breakdown with objectives and assumptions needing validation. Next step typically: Execute first phase.
</summary_requirements>

<success_criteria>
- Plan addresses all requirements
- Phases are sequential and logical
- Tasks are specific and actionable
- Metadata captures uncertainties
- SUMMARY.md created with phase overview
- Ready for implementation prompts to consume
</success_criteria>
```
</prompt_template>

<key_principles>

<reference_research>
Plans should build on research findings:
```xml
<context>
Research findings: @.prompts/001-auth-research/auth-research.md

Key findings to incorporate:
- Recommended approach from research
- Constraints identified
- Best practices to follow
</context>
```
</reference_research>

<prompt_sized_phases>
Each phase should be executable by a single prompt:
```xml
<phase number="1" name="setup-infrastructure">
  <objective>Create base auth structure and types</objective>
  <tasks>
    <task>Create auth module directory</task>
    <task>Define TypeScript types for tokens</task>
    <task>Set up test infrastructure</task>
  </tasks>
</phase>
```
</prompt_sized_phases>

<execution_hints>
Help the next Claude understand how to proceed:
```xml
<phase number="2" name="implement-jwt">
  <execution_notes>
    This phase modifies files from phase 1.
    Reference the types created in phase 1.
    Run tests after each major change.
  </execution_notes>
</phase>
```
</execution_hints>

</key_principles>

<plan_types>

<implementation_roadmap>
For breaking down how to build something:

```xml
<objective>
Create implementation roadmap for user authentication system.

Purpose: Guide phased implementation with clear milestones
Input: Authentication research findings
Output: auth-plan.md with 4-5 implementation phases
</objective>

<context>
Research: @.prompts/001-auth-research/auth-research.md
</context>

<planning_requirements>
- Break into independently testable phases
- Each phase builds on previous
- Include testing at each phase
- Consider rollback points
</planning_requirements>
```
</implementation_roadmap>

<decision_framework>
For choosing between options:

```xml
<objective>
Create decision framework for selecting database technology.

Purpose: Make informed choice between PostgreSQL, MongoDB, and DynamoDB
Input: Database research findings
Output: database-plan.md with criteria, analysis, recommendation
</objective>

<output_structure>
Structure as decision framework:

```xml
<decision_framework>
  <options>
    <option name="PostgreSQL">
      <pros>{List}</pros>
      <cons>{List}</cons>
      <fit_score criteria="scalability">8/10</fit_score>
      <fit_score criteria="flexibility">6/10</fit_score>
    </option>
    <!-- Other options -->
  </options>

  <recommendation>
    <choice>{Selected option}</choice>
    <rationale>{Why this choice}</rationale>
    <risks>{What could go wrong}</risks>
    <mitigations>{How to address risks}</mitigations>
  </recommendation>

  <metadata>
    <confidence level="high">
      Clear winner based on requirements
    </confidence>
    <assumptions>
      - Expected data volume: 10M records
      - Team has SQL experience
    </assumptions>
  </metadata>
</decision_framework>
```
</output_structure>
```
</decision_framework>

<process_definition>
For defining workflows or methodologies:

```xml
<objective>
Create deployment process for production releases.

Purpose: Standardize safe, repeatable deployments
Input: Current infrastructure research
Output: deployment-plan.md with step-by-step process
</objective>

<output_structure>
Structure as process:

```xml
<process>
  <overview>{High-level flow}</overview>

  <steps>
    <step number="1" name="pre-deployment">
      <actions>
        <action>Run full test suite</action>
        <action>Create database backup</action>
        <action>Notify team in #deployments</action>
      </actions>
      <checklist>
        <item>Tests passing</item>
        <item>Backup verified</item>
        <item>Team notified</item>
      </checklist>
      <rollback>N/A - no changes yet</rollback>
    </step>
    <!-- Additional steps -->
  </steps>

  <metadata>
    <dependencies>
      - CI/CD pipeline configured
      - Database backup system
      - Slack webhook for notifications
    </dependencies>
    <open_questions>
      - Blue-green vs rolling deployment?
      - Automated rollback triggers?
    </open_questions>
  </metadata>
</process>
```
</output_structure>
```
</process_definition>

</plan_types>

<metadata_guidelines>
Load: [metadata-guidelines.md](metadata-guidelines.md)
</metadata_guidelines>
