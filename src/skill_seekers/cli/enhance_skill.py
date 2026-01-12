#!/usr/bin/env python3
"""
SKILL.md Enhancement Script
Uses platform AI APIs to improve SKILL.md by analyzing reference documentation.

Usage:
    # Claude (default)
    skill-seekers enhance output/react/
    skill-seekers enhance output/react/ --api-key sk-ant-...

    # Gemini
    skill-seekers enhance output/react/ --target gemini --api-key AIzaSy...

    # OpenAI
    skill-seekers enhance output/react/ --target openai --api-key sk-proj-...
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_seekers.cli.constants import API_CONTENT_LIMIT, API_PREVIEW_LIMIT
from skill_seekers.cli.utils import read_reference_files

try:
    import anthropic
except ImportError:
    print("❌ Error: anthropic package not installed")
    print("Install with: pip3 install anthropic")
    sys.exit(1)


class SkillEnhancer:
    def __init__(self, skill_dir, api_key=None):
        self.skill_dir = Path(skill_dir)
        self.references_dir = self.skill_dir / "references"
        self.skill_md_path = self.skill_dir / "SKILL.md"

        # Get API key - support both ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN
        self.api_key = (api_key or
                       os.environ.get('ANTHROPIC_API_KEY') or
                       os.environ.get('ANTHROPIC_AUTH_TOKEN'))
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN "
                "environment variable or use --api-key argument"
            )

        # Support custom base URL for alternative API endpoints
        base_url = os.environ.get('ANTHROPIC_BASE_URL')
        client_kwargs = {'api_key': self.api_key}
        if base_url:
            client_kwargs['base_url'] = base_url
            print(f"ℹ️  Using custom API base URL: {base_url}")

        self.client = anthropic.Anthropic(**client_kwargs)

    def read_current_skill_md(self):
        """Read existing SKILL.md"""
        if not self.skill_md_path.exists():
            return None
        return self.skill_md_path.read_text(encoding='utf-8')

    def enhance_skill_md(self, references, current_skill_md):
        """Use Claude to enhance SKILL.md"""

        # Build prompt
        prompt = self._build_enhancement_prompt(references, current_skill_md)

        print("\n🤖 Asking Claude to enhance SKILL.md...")
        print(f"   Input: {len(prompt):,} characters")

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Handle response content - newer SDK versions may include ThinkingBlock
            # Find the TextBlock containing the actual response
            enhanced_content = None
            for block in message.content:
                if hasattr(block, 'text'):
                    enhanced_content = block.text
                    break

            if not enhanced_content:
                print("❌ Error: No text content found in API response")
                return None

            return enhanced_content

        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            return None

    def _build_enhancement_prompt(self, references, current_skill_md):
        """Build the prompt for Claude with multi-source awareness"""

        # Extract skill name and description
        skill_name = self.skill_dir.name

        # Analyze sources
        sources_found = set()
        for metadata in references.values():
            sources_found.add(metadata['source'])

        # Analyze conflicts if present
        has_conflicts = any('conflicts' in meta['path'] for meta in references.values())

        prompt = f"""You are enhancing a Claude skill's SKILL.md file. This skill is about: {skill_name}

I've scraped documentation from multiple sources and organized it into reference files. Your job is to create an EXCELLENT SKILL.md that synthesizes knowledge from these sources.

SKILL OVERVIEW:
- Name: {skill_name}
- Source Types: {', '.join(sorted(sources_found))}
- Multi-Source: {'Yes' if len(sources_found) > 1 else 'No'}
- Conflicts Detected: {'Yes - see conflicts.md in references' if has_conflicts else 'No'}

CURRENT SKILL.MD:
{'```markdown' if current_skill_md else '(none - create from scratch)'}
{current_skill_md or 'No existing SKILL.md'}
{'```' if current_skill_md else ''}

SOURCE ANALYSIS:
This skill combines knowledge from {len(sources_found)} source type(s):

"""

        # Group references by (source_type, repo_id) for multi-source support
        by_source = {}
        for filename, metadata in references.items():
            source = metadata['source']
            repo_id = metadata.get('repo_id')  # None for single-source
            key = (source, repo_id) if repo_id else (source, None)

            if key not in by_source:
                by_source[key] = []
            by_source[key].append((filename, metadata))

        # Add source breakdown with repo identity
        for (source, repo_id) in sorted(by_source.keys()):
            files = by_source[(source, repo_id)]
            if repo_id:
                prompt += f"\n**{source.upper()} - {repo_id} ({len(files)} file(s))**\n"
            else:
                prompt += f"\n**{source.upper()} ({len(files)} file(s))**\n"
            for filename, metadata in files[:5]:  # Top 5 per source
                prompt += f"- {filename} (confidence: {metadata['confidence']}, {metadata['size']:,} chars)\n"
            if len(files) > 5:
                prompt += f"- ... and {len(files) - 5} more\n"

        prompt += "\n\nREFERENCE DOCUMENTATION:\n"

        # Add references grouped by (source, repo_id) with metadata
        for (source, repo_id) in sorted(by_source.keys()):
            if repo_id:
                prompt += f"\n### {source.upper()} SOURCES - {repo_id}\n\n"
            else:
                prompt += f"\n### {source.upper()} SOURCES\n\n"

            for filename, metadata in by_source[(source, repo_id)]:
                content = metadata['content']
                # Limit per-file to 30K
                if len(content) > 30000:
                    content = content[:30000] + "\n\n[Content truncated for size...]"

                prompt += f"\n#### {filename}\n"
                if repo_id:
                    prompt += f"*Source: {metadata['source']} ({repo_id}), Confidence: {metadata['confidence']}*\n\n"
                else:
                    prompt += f"*Source: {metadata['source']}, Confidence: {metadata['confidence']}*\n\n"
                prompt += f"```markdown\n{content}\n```\n"

        prompt += """

REFERENCE PRIORITY (when sources differ):
1. **Code patterns (codebase_analysis)**: Ground truth - what the code actually does
2. **Official documentation**: Intended API and usage patterns
3. **GitHub issues**: Real-world usage and known problems
4. **PDF documentation**: Additional context and tutorials

MULTI-REPOSITORY HANDLING:
"""

        # Detect multiple repos from same source type
        repo_ids = set()
        for metadata in references.values():
            if metadata.get('repo_id'):
                repo_ids.add(metadata['repo_id'])

        if len(repo_ids) > 1:
            prompt += f"""
⚠️ MULTIPLE REPOSITORIES DETECTED: {', '.join(sorted(repo_ids))}

This skill combines codebase analysis from {len(repo_ids)} different repositories.
Each repo has its own ARCHITECTURE.md, patterns, examples, and configuration.

When synthesizing:
- Clearly identify which content comes from which repo
- Compare and contrast patterns across repos (e.g., "httpx uses Strategy pattern 50 times, httpcore uses it 32 times")
- Highlight relationships (e.g., "httpx is a client library built on top of httpcore")
- Present examples from BOTH repos to show different use cases
- If repos serve different purposes, explain when to use each
"""
        else:
            prompt += "\nSingle repository - standard synthesis applies.\n"

        prompt += """

YOUR TASK:
Create an enhanced SKILL.md that synthesizes knowledge from multiple sources:

1. **Multi-Source Synthesis**
   - Acknowledge that this skill combines multiple sources
   - Highlight agreements between sources (builds confidence)
   - Note discrepancies transparently (if present)
   - Use source priority when synthesizing conflicting information

2. **Clear "When to Use This Skill" section**
   - Be SPECIFIC about trigger conditions
   - List concrete use cases
   - Include perspective from both docs AND real-world usage (if GitHub/codebase data available)

3. **Excellent Quick Reference section**
   - Extract 5-10 of the BEST, most practical code examples
   - Prefer examples from HIGH CONFIDENCE sources first
   - If code examples exist from codebase analysis, prioritize those (real usage)
   - If docs examples exist, include those too (official patterns)
   - Choose SHORT, clear examples (5-20 lines max)
   - Use proper language tags (cpp, python, javascript, json, etc.)
   - Add clear descriptions noting the source (e.g., "From official docs" or "From codebase")

4. **Detailed Reference Files description**
   - Explain what's in each reference file
   - Note the source type and confidence level
   - Help users navigate multi-source documentation

5. **Practical "Working with This Skill" section**
   - Clear guidance for beginners, intermediate, and advanced users
   - Navigation tips for multi-source references
   - How to resolve conflicts if present

6. **Key Concepts section** (if applicable)
   - Explain core concepts
   - Define important terminology
   - Reconcile differences between sources if needed

7. **Conflict Handling** (if conflicts detected)
   - Add a "Known Discrepancies" section
   - Explain major conflicts transparently
   - Provide guidance on which source to trust in each case

8. **Keep the frontmatter** (---\nname: ...\n---) intact

IMPORTANT:
- Extract REAL examples from the reference docs, don't make them up
- Prioritize HIGH CONFIDENCE sources when synthesizing
- Note source attribution when helpful (e.g., "Official docs say X, but codebase shows Y")
- Make discrepancies transparent, not hidden
- Prioritize SHORT, clear examples (5-20 lines max)
- Make it actionable and practical
- Don't be too verbose - be concise but useful
- Maintain the markdown structure for Claude skills
- Keep code examples properly formatted with language tags

OUTPUT:
Return ONLY the complete SKILL.md content, starting with the frontmatter (---).
"""

        return prompt

    def save_enhanced_skill_md(self, content):
        """Save the enhanced SKILL.md"""
        # Backup original
        if self.skill_md_path.exists():
            backup_path = self.skill_md_path.with_suffix('.md.backup')
            self.skill_md_path.rename(backup_path)
            print(f"  💾 Backed up original to: {backup_path.name}")

        # Save enhanced version
        self.skill_md_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Saved enhanced SKILL.md")

    def run(self):
        """Main enhancement workflow"""
        print(f"\n{'='*60}")
        print(f"ENHANCING SKILL: {self.skill_dir.name}")
        print(f"{'='*60}\n")

        # Read reference files
        print("📖 Reading reference documentation...")
        references = read_reference_files(
            self.skill_dir,
            max_chars=API_CONTENT_LIMIT,
            preview_limit=API_PREVIEW_LIMIT
        )

        if not references:
            print("❌ No reference files found to analyze")
            return False

        # Analyze sources
        sources_found = set()
        for metadata in references.values():
            sources_found.add(metadata['source'])

        print(f"  ✓ Read {len(references)} reference files")
        print(f"  ✓ Sources: {', '.join(sorted(sources_found))}")
        total_size = sum(meta['size'] for meta in references.values())
        print(f"  ✓ Total size: {total_size:,} characters\n")

        # Read current SKILL.md
        current_skill_md = self.read_current_skill_md()
        if current_skill_md:
            print(f"  ℹ Found existing SKILL.md ({len(current_skill_md)} chars)")
        else:
            print(f"  ℹ No existing SKILL.md, will create new one")

        # Enhance with Claude
        enhanced = self.enhance_skill_md(references, current_skill_md)

        if not enhanced:
            print("❌ Enhancement failed")
            return False

        print(f"  ✓ Generated enhanced SKILL.md ({len(enhanced)} chars)\n")

        # Save
        print("💾 Saving enhanced SKILL.md...")
        self.save_enhanced_skill_md(enhanced)

        print(f"\n✅ Enhancement complete!")
        print(f"\nNext steps:")
        print(f"  1. Review: {self.skill_md_path}")
        print(f"  2. If you don't like it, restore backup: {self.skill_md_path.with_suffix('.md.backup')}")
        print(f"  3. Package your skill:")
        print(f"     skill-seekers package {self.skill_dir}/")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Enhance SKILL.md using platform AI APIs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Claude (default)
  export ANTHROPIC_API_KEY=sk-ant-...
  skill-seekers enhance output/react/

  # Gemini
  export GOOGLE_API_KEY=AIzaSy...
  skill-seekers enhance output/react/ --target gemini

  # OpenAI
  export OPENAI_API_KEY=sk-proj-...
  skill-seekers enhance output/react/ --target openai

  # With explicit API key
  skill-seekers enhance output/react/ --api-key sk-ant-...

  # Dry run
  skill-seekers enhance output/godot/ --dry-run
"""
    )

    parser.add_argument('skill_dir', type=str,
                       help='Path to skill directory (e.g., output/steam-inventory/)')
    parser.add_argument('--api-key', type=str,
                       help='Platform API key (or set environment variable)')
    parser.add_argument('--target',
                       choices=['claude', 'gemini', 'openai'],
                       default='claude',
                       help='Target LLM platform (default: claude)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without calling API')

    args = parser.parse_args()

    # Validate skill directory
    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        print(f"❌ Error: Directory not found: {skill_dir}")
        sys.exit(1)

    if not skill_dir.is_dir():
        print(f"❌ Error: Not a directory: {skill_dir}")
        sys.exit(1)

    # Dry run mode
    if args.dry_run:
        print(f"🔍 DRY RUN MODE")
        print(f"   Would enhance: {skill_dir}")
        print(f"   References: {skill_dir / 'references'}")
        print(f"   SKILL.md: {skill_dir / 'SKILL.md'}")

        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            ref_files = list(refs_dir.glob("*.md"))
            print(f"   Found {len(ref_files)} reference files:")
            for rf in ref_files:
                size = rf.stat().st_size
                print(f"     - {rf.name} ({size:,} bytes)")

        print("\nTo actually run enhancement:")
        print(f"  skill-seekers enhance {skill_dir}")
        return

    # Check if platform supports enhancement
    try:
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor(args.target)

        if not adaptor.supports_enhancement():
            print(f"❌ Error: {adaptor.PLATFORM_NAME} does not support AI enhancement")
            print(f"\nSupported platforms for enhancement:")
            print("  - Claude AI (Anthropic)")
            print("  - Google Gemini")
            print("  - OpenAI ChatGPT")
            sys.exit(1)

        # Get API key
        api_key = args.api_key
        if not api_key:
            api_key = os.environ.get(adaptor.get_env_var_name(), '').strip()

        if not api_key:
            print(f"❌ Error: {adaptor.get_env_var_name()} not set")
            print(f"\nSet your API key for {adaptor.PLATFORM_NAME}:")
            print(f"  export {adaptor.get_env_var_name()}=...")
            print("Or provide it directly:")
            print(f"  skill-seekers enhance {skill_dir} --target {args.target} --api-key ...")
            sys.exit(1)

        # Run enhancement using adaptor
        print(f"\n{'='*60}")
        print(f"ENHANCING SKILL: {skill_dir}")
        print(f"Platform: {adaptor.PLATFORM_NAME}")
        print(f"{'='*60}\n")

        success = adaptor.enhance(Path(skill_dir), api_key)

        if success:
            print(f"\n✅ Enhancement complete!")
            print(f"\nNext steps:")
            print(f"  1. Review: {Path(skill_dir) / 'SKILL.md'}")
            print(f"  2. If you don't like it, restore backup: {Path(skill_dir) / 'SKILL.md.backup'}")
            print(f"  3. Package your skill:")
            print(f"     skill-seekers package {skill_dir}/ --target {args.target}")

        sys.exit(0 if success else 1)

    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\nAdaptor system not available. Reinstall skill-seekers.")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
