<overview>
Skills use pure XML structure for consistent parsing, efficient token usage, and improved Claude performance. This reference defines the required and conditional XML tags for skill authoring, along with intelligence rules for tag selection.
</overview>

<critical_rule>
**Remove ALL markdown headings (#, ##, ###) from skill body content.** Replace with semantic XML tags. Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).
</critical_rule>

<required_tags>
Every skill MUST have these three tags:

<tag name="objective">
**Purpose**: What the skill does and why it matters. Sets context and scope.

**Content**: 1-3 paragraphs explaining the skill's purpose, domain, and value proposition.

**Example**:
```xml
<objective>
Extract text and tables from PDF files, fill forms, and merge documents using Python libraries. This skill provides patterns for common PDF operations without requiring external services or APIs.
</objective>
```
</tag>

<tag name="quick_start">
**Purpose**: Immediate, actionable guidance. Gets Claude started quickly without reading advanced sections.

**Content**: Minimal working example, essential commands, or basic usage pattern.

**Example**:
```xml
<quick_start>
Extract text with pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
</quick_start>
```
</tag>

<tag name="success_criteria">
**Purpose**: How to know the task worked. Defines completion criteria.

**Alternative name**: `<when_successful>` (use whichever fits better)

**Content**: Clear criteria for successful execution, validation steps, or expected outputs.

**Example**:
```xml
<success_criteria>
A well-structured skill has:

- Valid YAML frontmatter with descriptive name and description
- Pure XML structure with no markdown headings in body
- Required tags: objective, quick_start, success_criteria
- Progressive disclosure (SKILL.md < 500 lines, details in reference files)
- Real-world testing and iteration based on observed behavior
</success_criteria>
```
</tag>
</required_tags>

<conditional_tags>
Add these tags based on skill complexity and domain requirements:

<tag name="context">
**When to use**: Background or situational information that Claude needs before starting.

**Example**:
```xml
<context>
The Facebook Marketing API uses a hierarchy: Account → Campaign → Ad Set → Ad. Each level has different configuration options and requires specific permissions. Always verify API access before making changes.
</context>
```
</tag>

<tag name="workflow">
**When to use**: Step-by-step procedures, sequential operations, multi-step processes.

**Alternative name**: `<process>`

**Example**:
```xml
<workflow>
1. **Analyze the form**: Run analyze_form.py to extract field definitions
2. **Create field mapping**: Edit fields.json with values
3. **Validate mapping**: Run validate_fields.py
4. **Fill the form**: Run fill_form.py
5. **Verify output**: Check generated PDF
</workflow>
```
</tag>

<tag name="advanced_features">
**When to use**: Deep-dive topics that most users won't need (progressive disclosure).

**Example**:
```xml
<advanced_features>
**Custom styling**: See [styling.md](styling.md)
**Template inheritance**: See [templates.md](templates.md)
**API reference**: See [reference.md](reference.md)
</advanced_features>
```
</tag>

<tag name="validation">
**When to use**: Skills with verification steps, quality checks, or validation scripts.

**Example**:
```xml
<validation>
After making changes, validate immediately:

```bash
python scripts/validate.py output_dir/
```

Only proceed when validation passes. If errors occur, review and fix before continuing.
</validation>
```
</tag>

<tag name="examples">
**When to use**: Multi-shot learning, input/output pairs, demonstrating patterns.

**Example**:
```xml
<examples>
<example number="1">
<input>User clicked signup button</input>
<output>track('signup_initiated', { source: 'homepage' })</output>
</example>

<example number="2">
<input>Purchase completed</input>
<output>track('purchase', { value: 49.99, currency: 'USD' })</output>
</example>
</examples>
```
</tag>

<tag name="anti_patterns">
**When to use**: Common mistakes that Claude should avoid.

**Example**:
```xml
<anti_patterns>
<pitfall name="vague_descriptions">
- ❌ "Helps with documents"
- ✅ "Extract text and tables from PDF files"
</pitfall>

<pitfall name="too_many_options">
- ❌ "You can use pypdf, or pdfplumber, or PyMuPDF..."
- ✅ "Use pdfplumber for text extraction. For OCR, use pytesseract instead."
</pitfall>
</anti_patterns>
```
</tag>

<tag name="security_checklist">
**When to use**: Skills with security implications (API keys, payments, authentication).

**Example**:
```xml
<security_checklist>
- Never log API keys or tokens
- Always use environment variables for credentials
- Validate all user input before API calls
- Use HTTPS for all external requests
- Check API response status before proceeding
</security_checklist>
```
</tag>

<tag name="testing">
**When to use**: Testing workflows, test patterns, or validation steps.

**Example**:
```xml
<testing>
Test with all target models (Haiku, Sonnet, Opus):

1. Run skill on representative tasks
2. Observe where Claude struggles or succeeds
3. Iterate based on actual behavior
4. Validate XML structure after changes
</testing>
```
</tag>

<tag name="common_patterns">
**When to use**: Code examples, recipes, or reusable patterns.

**Example**:
```xml
<common_patterns>
<pattern name="error_handling">
```python
try:
    result = process_file(path)
except FileNotFoundError:
    print(f"File not found: {path}")
except Exception as e:
    print(f"Error: {e}")
```
</pattern>
</common_patterns>
```
</tag>

<tag name="reference_guides">
**When to use**: Links to detailed reference files (progressive disclosure).

**Alternative name**: `<detailed_references>`

**Example**:
```xml
<reference_guides>
For deeper topics, see reference files:

**API operations**: [references/api-operations.md](references/api-operations.md)
**Security patterns**: [references/security.md](references/security.md)
**Troubleshooting**: [references/troubleshooting.md](references/troubleshooting.md)
</reference_guides>
```
</tag>
</conditional_tags>

<intelligence_rules>
<decision_tree>
**Simple skills** (single domain, straightforward):
- Required tags only: objective, quick_start, success_criteria
- Example: Text extraction, file format conversion, simple calculations

**Medium skills** (multiple patterns, some complexity):
- Required tags + workflow/examples as needed
- Example: Document processing with steps, API integration with configuration

**Complex skills** (multiple domains, security, APIs):
- Required tags + conditional tags as appropriate
- Example: Payment processing, authentication systems, multi-step workflows with validation
</decision_tree>

<principle>
Don't over-engineer simple skills. Don't under-specify complex skills. Match tag selection to actual complexity and user needs.
</principle>

<when_to_add_conditional>
Ask these questions:

- **Context needed?** → Add `<context>`
- **Multi-step process?** → Add `<workflow>` or `<process>`
- **Advanced topics to hide?** → Add `<advanced_features>` + reference files
- **Validation required?** → Add `<validation>`
- **Pattern demonstration?** → Add `<examples>`
- **Common mistakes?** → Add `<anti_patterns>`
- **Security concerns?** → Add `<security_checklist>`
- **Testing guidance?** → Add `<testing>`
- **Code recipes?** → Add `<common_patterns>`
- **Deep references?** → Add `<reference_guides>`
</when_to_add_conditional>
</intelligence_rules>

<xml_vs_markdown_headings>
<token_efficiency>
XML tags are more efficient than markdown headings:

**Markdown headings**:
```markdown
## Quick start
## Workflow
## Advanced features
## Success criteria
```
Total: ~20 tokens, no semantic meaning to Claude

**XML tags**:
```xml
<quick_start>
<workflow>
<advanced_features>
<success_criteria>
```
Total: ~15 tokens, semantic meaning built-in
</token_efficiency>

<parsing_accuracy>
XML provides unambiguous boundaries and semantic meaning. Claude can reliably:
- Identify section boundaries
- Understand content purpose
- Skip irrelevant sections
- Parse programmatically

Markdown headings are just visual formatting. Claude must infer meaning from heading text.
</parsing_accuracy>

<consistency>
XML enforces consistent structure across all skills. All skills use the same tag names for the same purposes. Makes it easier to:
- Validate skill structure programmatically
- Learn patterns across skills
- Maintain consistent quality
</consistency>
</xml_vs_markdown_headings>

<nesting_guidelines>
<proper_nesting>
XML tags can nest for hierarchical content:

```xml
<examples>
<example number="1">
<input>User input here</input>
<output>Expected output here</output>
</example>

<example number="2">
<input>Another input</input>
<output>Another output</output>
</example>
</examples>
```
</proper_nesting>

<closing_tags>
Always close tags properly:

✅ Good:
```xml
<objective>
Content here
</objective>
```

❌ Bad:
```xml
<objective>
Content here
```
</closing_tags>

<tag_naming>
Use descriptive, semantic names:
- `<workflow>` not `<steps>`
- `<success_criteria>` not `<done>`
- `<anti_patterns>` not `<dont_do>`

Be consistent within your skill. If you use `<workflow>`, don't also use `<process>` for the same purpose.
</tag_naming>
</nesting_guidelines>

<anti_pattern>
**DO NOT use markdown headings in skill body content.**

❌ Bad (hybrid approach):
```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber...

## Advanced features

Form filling...
```

✅ Good (pure XML):
```markdown
<objective>
PDF processing with text extraction, form filling, and merging.
</objective>

<quick_start>
Extract text with pdfplumber...
</quick_start>

<advanced_features>
Form filling...
</advanced_features>
```
</anti_pattern>

<benefits>
<benefit type="clarity">
Clearly separate different sections with unambiguous boundaries
</benefit>

<benefit type="accuracy">
Reduce parsing errors. Claude knows exactly where sections begin and end.
</benefit>

<benefit type="flexibility">
Easily find, add, remove, or modify sections without rewriting
</benefit>

<benefit type="parseability">
Programmatically extract specific sections for validation or analysis
</benefit>

<benefit type="efficiency">
Lower token usage compared to markdown headings
</benefit>

<benefit type="consistency">
Standardized structure across all skills in the ecosystem
</benefit>
</benefits>

<combining_with_other_techniques>
XML tags work well with other prompting techniques:

**Multi-shot learning**:
```xml
<examples>
<example number="1">...</example>
<example number="2">...</example>
</examples>
```

**Chain of thought**:
```xml
<thinking>
Analyze the problem...
</thinking>

<answer>
Based on the analysis...
</answer>
```

**Template provision**:
```xml
<template>
```markdown
# Report Title

## Summary
...
```
</template>
```

**Reference material**:
```xml
<schema>
{
  "field": "type"
}
</schema>
```
</combining_with_other_techniques>

<tag_reference_pattern>
When referencing content in tags, use the tag name:

"Using the schema in `<schema>` tags..."
"Follow the workflow in `<workflow>`..."
"See examples in `<examples>`..."

This makes the structure self-documenting.
</tag_reference_pattern>
