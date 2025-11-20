<overview>
Prompt patterns for execution tasks that produce artifacts (code, documents, designs, etc.).
</overview>

<prompt_template>
```xml
<objective>
{Clear statement of what to build/create/fix}

Purpose: {Why this matters, what it enables}
Output: {What artifact(s) will be produced}
</objective>

<context>
{Referenced research/plan files if chained}
@{topic}-research.md
@{topic}-plan.md

{Project context}
@relevant-files
</context>

<requirements>
{Specific functional requirements}
{Quality requirements}
{Constraints and boundaries}
</requirements>

<implementation>
{Specific approaches or patterns to follow}
{What to avoid and WHY}
{Integration points}
</implementation>

<output>
Create/modify files:
- `./path/to/file.ext` - {description}

{For complex outputs, specify structure}
</output>

<verification>
Before declaring complete:
- {Specific test or check}
- {How to confirm it works}
- {Edge cases to verify}
</verification>

<summary_requirements>
Create `.prompts/{num}-{topic}-{purpose}/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For Do prompts, include Files Created section with paths and descriptions. Emphasize what was implemented and test status. Next step typically: Run tests or execute next phase.
</summary_requirements>

<success_criteria>
{Clear, measurable criteria}
- {Criterion 1}
- {Criterion 2}
- SUMMARY.md created with files list and next step
</success_criteria>
```
</prompt_template>

<key_principles>

<reference_chain_artifacts>
If research or plan exists, always reference them:
```xml
<context>
Research findings: @.prompts/001-auth-research/auth-research.md
Implementation plan: @.prompts/002-auth-plan/auth-plan.md
</context>
```
</reference_chain_artifacts>

<explicit_output_location>
Every artifact needs a clear path:
```xml
<output>
Create files in ./src/auth/:
- `./src/auth/middleware.ts` - JWT validation middleware
- `./src/auth/types.ts` - Auth type definitions
- `./src/auth/utils.ts` - Helper functions
</output>
```
</explicit_output_location>

<verification_matching>
Include verification that matches the task:
- Code: run tests, type check, lint
- Documents: check structure, validate links
- Designs: review against requirements
</verification_matching>

</key_principles>

<complexity_variations>

<simple_do>
Single artifact example:
```xml
<objective>
Create a utility function that validates email addresses.
</objective>

<requirements>
- Support standard email format
- Return boolean
- Handle edge cases (empty, null)
</requirements>

<output>
Create: `./src/utils/validate-email.ts`
</output>

<verification>
Test with: valid emails, invalid formats, edge cases
</verification>
```
</simple_do>

<complex_do>
Multiple artifacts with dependencies:
```xml
<objective>
Implement user authentication system with JWT tokens.

Purpose: Enable secure user sessions for the application
Output: Auth middleware, routes, types, and tests
</objective>

<context>
Research: @.prompts/001-auth-research/auth-research.md
Plan: @.prompts/002-auth-plan/auth-plan.md
Existing user model: @src/models/user.ts
</context>

<requirements>
- JWT access tokens (15min expiry)
- Refresh token rotation
- Secure httpOnly cookies
- Rate limiting on auth endpoints
</requirements>

<implementation>
Follow patterns from auth-research.md:
- Use jose library for JWT (not jsonwebtoken - see research)
- Implement refresh rotation per OWASP guidelines
- Store refresh tokens hashed in database

Avoid:
- Storing tokens in localStorage (XSS vulnerable)
- Long-lived access tokens (security risk)
</implementation>

<output>
Create in ./src/auth/:
- `middleware.ts` - JWT validation, refresh logic
- `routes.ts` - Login, logout, refresh endpoints
- `types.ts` - Token payloads, auth types
- `utils.ts` - Token generation, hashing

Create in ./src/auth/__tests__/:
- `auth.test.ts` - Unit tests for all auth functions
</output>

<verification>
1. Run test suite: `npm test src/auth`
2. Type check: `npx tsc --noEmit`
3. Manual test: login flow, token refresh, logout
4. Security check: verify httpOnly cookies, token expiry
</verification>

<success_criteria>
- All tests passing
- No type errors
- Login/logout/refresh flow works
- Tokens properly secured
- Follows patterns from research
</success_criteria>
```
</complex_do>

</complexity_variations>

<non_code_examples>

<document_creation>
```xml
<objective>
Create API documentation for the authentication endpoints.

Purpose: Enable frontend team to integrate auth
Output: OpenAPI spec + markdown guide
</objective>

<context>
Implementation: @src/auth/routes.ts
Types: @src/auth/types.ts
</context>

<requirements>
- OpenAPI 3.0 spec
- Request/response examples
- Error codes and handling
- Authentication flow diagram
</requirements>

<output>
- `./docs/api/auth.yaml` - OpenAPI spec
- `./docs/guides/authentication.md` - Integration guide
</output>

<verification>
- Validate OpenAPI spec: `npx @redocly/cli lint docs/api/auth.yaml`
- Check all endpoints documented
- Verify examples match actual implementation
</verification>
```
</document_creation>

<design_architecture>
```xml
<objective>
Design database schema for multi-tenant SaaS application.

Purpose: Support customer isolation and scaling
Output: Schema diagram + migration files
</objective>

<context>
Research: @.prompts/001-multitenancy-research/multitenancy-research.md
Current schema: @prisma/schema.prisma
</context>

<requirements>
- Row-level security per tenant
- Shared infrastructure model
- Support for tenant-specific customization
- Audit logging
</requirements>

<output>
- `./docs/architecture/tenant-schema.md` - Schema design doc
- `./prisma/migrations/add-tenancy/` - Migration files
</output>

<verification>
- Migration runs without errors
- RLS policies correctly isolate data
- Performance acceptable with 1000 tenants
</verification>
```
</design_architecture>

</non_code_examples>
