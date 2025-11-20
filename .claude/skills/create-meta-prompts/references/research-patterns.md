<overview>
Prompt patterns for gathering information that will be consumed by planning or implementation prompts.
</overview>

<prompt_template>
```xml
<research_objective>
Research {topic} to inform {subsequent use}.

Purpose: {What decision/implementation this enables}
Scope: {Boundaries of the research}
Output: {topic}-research.md with structured findings
</research_objective>

<research_scope>
<include>
{What to investigate}
{Specific questions to answer}
</include>

<exclude>
{What's out of scope}
{What to defer to later research}
</exclude>

<sources>
{Priority sources: official docs, specific sites}
{Time constraints: prefer 2024-2025 sources}
</sources>
</research_scope>

<output_structure>
Save to: `.prompts/{num}-{topic}-research/{topic}-research.md`

Structure findings using this XML format:

```xml
<research>
  <summary>
    {2-3 paragraph executive summary of key findings}
  </summary>

  <findings>
    <finding category="{category}">
      <title>{Finding title}</title>
      <detail>{Detailed explanation}</detail>
      <source>{Where this came from}</source>
      <relevance>{Why this matters for the goal}</relevance>
    </finding>
    <!-- Additional findings -->
  </findings>

  <recommendations>
    <recommendation priority="high">
      <action>{What to do}</action>
      <rationale>{Why}</rationale>
    </recommendation>
    <!-- Additional recommendations -->
  </recommendations>

  <code_examples>
    {Relevant code patterns, snippets, configurations}
  </code_examples>

  <metadata>
    <confidence level="{high|medium|low}">
      {Why this confidence level}
    </confidence>
    <dependencies>
      {What's needed to act on this research}
    </dependencies>
    <open_questions>
      {What couldn't be determined}
    </open_questions>
    <assumptions>
      {What was assumed}
    </assumptions>
  </metadata>
</research>
```
</output_structure>

<summary_requirements>
Create `.prompts/{num}-{topic}-research/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For research, emphasize key recommendation and decision readiness. Next step typically: Create plan.
</summary_requirements>

<success_criteria>
- All scope questions answered
- Sources are current (2024-2025)
- Findings are actionable
- Metadata captures gaps
- SUMMARY.md created with substantive one-liner
- Ready for planning/implementation to consume
</success_criteria>
```
</prompt_template>

<key_principles>

<structure_for_consumption>
The next Claude needs to quickly extract relevant information:
```xml
<finding category="authentication">
  <title>JWT vs Session Tokens</title>
  <detail>
    JWTs are preferred for stateless APIs. Sessions better for
    traditional web apps with server-side rendering.
  </detail>
  <source>OWASP Authentication Cheatsheet 2024</source>
  <relevance>
    Our API-first architecture points to JWT approach.
  </relevance>
</finding>
```
</structure_for_consumption>

<include_code_examples>
The implementation prompt needs patterns to follow:
```xml
<code_examples>
<example name="jwt-verification">
```typescript
import { jwtVerify } from 'jose';

const { payload } = await jwtVerify(
  token,
  new TextEncoder().encode(secret),
  { algorithms: ['HS256'] }
);
```
Source: jose library documentation
</example>
</code_examples>
```
</include_code_examples>

<explicit_confidence>
Help the next Claude know what to trust:
```xml
<metadata>
  <confidence level="medium">
    API documentation is comprehensive but lacks real-world
    performance benchmarks. Rate limits are documented but
    actual behavior may differ under load.
  </confidence>
</metadata>
```
</explicit_confidence>

</key_principles>

<research_types>

<technology_research>
For understanding tools, libraries, APIs:

```xml
<research_objective>
Research JWT authentication libraries for Node.js.

Purpose: Select library for auth implementation
Scope: Security, performance, maintenance status
Output: jwt-research.md
</research_objective>

<research_scope>
<include>
- Available libraries (jose, jsonwebtoken, etc.)
- Security track record
- Bundle size and performance
- TypeScript support
- Active maintenance
- Community adoption
</include>

<exclude>
- Implementation details (for planning phase)
- Specific code architecture (for implementation)
</exclude>

<sources>
- Official library documentation
- npm download stats
- GitHub issues/security advisories
- Prefer sources from 2024-2025
</sources>
</research_scope>
```
</technology_research>

<best_practices_research>
For understanding patterns and standards:

```xml
<research_objective>
Research authentication security best practices.

Purpose: Inform secure auth implementation
Scope: Current standards, common vulnerabilities, mitigations
Output: auth-security-research.md
</research_objective>

<research_scope>
<include>
- OWASP authentication guidelines
- Token storage best practices
- Common vulnerabilities (XSS, CSRF)
- Secure cookie configuration
- Password hashing standards
</include>

<sources>
- OWASP Cheatsheets
- Security advisories
- Reputable security blogs (2024-2025)
</sources>
</research_scope>
```
</best_practices_research>

<api_service_research>
For understanding external services:

```xml
<research_objective>
Research Stripe API for payment integration.

Purpose: Plan payment implementation
Scope: Endpoints, authentication, webhooks, testing
Output: stripe-research.md
</research_objective>

<research_scope>
<include>
- API structure and versioning
- Authentication methods
- Key endpoints for our use case
- Webhook events and handling
- Testing and sandbox environment
- Error handling patterns
- SDK availability
</include>

<exclude>
- Pricing details
- Account setup process
</exclude>

<sources>
- Stripe official documentation
- Stripe API changelog (latest version)
- Context7 MCP for current patterns
</sources>
</research_scope>
```
</api_service_research>

<comparison_research>
For evaluating options:

```xml
<research_objective>
Research database options for multi-tenant SaaS.

Purpose: Inform database selection decision
Scope: PostgreSQL, MongoDB, DynamoDB for our use case
Output: database-research.md
</research_objective>

<research_scope>
<include>
For each option:
- Multi-tenancy support patterns
- Scaling characteristics
- Cost model
- Operational complexity
- Team expertise requirements
</include>

<evaluation_criteria>
- Data isolation requirements
- Expected query patterns
- Scale projections
- Team familiarity
</evaluation_criteria>
</research_scope>
```
</comparison_research>

</research_types>

<metadata_guidelines>
Load: [metadata-guidelines.md](metadata-guidelines.md)
</metadata_guidelines>

<tool_usage>

<context7_mcp>
For library documentation:
```
Use mcp__context7__resolve-library-id to find library
Then mcp__context7__get-library-docs for current patterns
```
</context7_mcp>

<web_search>
For recent articles and updates:
```
Search: "{topic} best practices 2024"
Search: "{library} security vulnerabilities 2024"
```
</web_search>

<web_fetch>
For specific documentation pages:
```
Fetch official docs, API references, changelogs
```
</web_fetch>

Include tool usage hints in research prompts when specific sources are needed.
</tool_usage>
