#!/usr/bin/env python3
"""
SKILL.md Enhancement Script (Local - Using Claude Code)
Opens a new terminal with Claude Code to enhance SKILL.md, then reports back.
No API key needed - uses your existing Claude Code Max plan!

Usage:
    skill-seekers enhance output/steam-inventory/
    skill-seekers enhance output/react/

Terminal Selection:
    The script automatically detects which terminal app to use:
    1. SKILL_SEEKER_TERMINAL env var (highest priority)
       Example: export SKILL_SEEKER_TERMINAL="Ghostty"
    2. TERM_PROGRAM env var (current terminal)
    3. Terminal.app (fallback)

    Supported terminals: Ghostty, iTerm, Terminal, WezTerm
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

# Add parent directory to path for imports when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_seekers.cli.constants import LOCAL_CONTENT_LIMIT, LOCAL_PREVIEW_LIMIT
from skill_seekers.cli.utils import read_reference_files


def detect_terminal_app():
    """Detect which terminal app to use with cascading priority.

    Priority order:
        1. SKILL_SEEKER_TERMINAL environment variable (explicit user preference)
        2. TERM_PROGRAM environment variable (inherit current terminal)
        3. Terminal.app (fallback default)

    Returns:
        tuple: (terminal_app_name, detection_method)
            - terminal_app_name (str): Name of terminal app to launch (e.g., "Ghostty", "Terminal")
            - detection_method (str): How the terminal was detected (for logging)

    Examples:
        >>> os.environ['SKILL_SEEKER_TERMINAL'] = 'Ghostty'
        >>> detect_terminal_app()
        ('Ghostty', 'SKILL_SEEKER_TERMINAL')

        >>> os.environ['TERM_PROGRAM'] = 'iTerm.app'
        >>> detect_terminal_app()
        ('iTerm', 'TERM_PROGRAM')
    """
    # Map TERM_PROGRAM values to macOS app names
    TERMINAL_MAP = {
        'Apple_Terminal': 'Terminal',
        'iTerm.app': 'iTerm',
        'ghostty': 'Ghostty',
        'WezTerm': 'WezTerm',
    }

    # Priority 1: Check SKILL_SEEKER_TERMINAL env var (explicit preference)
    preferred_terminal = os.environ.get('SKILL_SEEKER_TERMINAL', '').strip()
    if preferred_terminal:
        return preferred_terminal, 'SKILL_SEEKER_TERMINAL'

    # Priority 2: Check TERM_PROGRAM (inherit current terminal)
    term_program = os.environ.get('TERM_PROGRAM', '').strip()
    if term_program and term_program in TERMINAL_MAP:
        return TERMINAL_MAP[term_program], 'TERM_PROGRAM'

    # Priority 3: Fallback to Terminal.app
    if term_program:
        # TERM_PROGRAM is set but unknown
        return 'Terminal', f'unknown TERM_PROGRAM ({term_program})'
    else:
        # No TERM_PROGRAM set
        return 'Terminal', 'default'


class LocalSkillEnhancer:
    def __init__(self, skill_dir):
        self.skill_dir = Path(skill_dir)
        self.references_dir = self.skill_dir / "references"
        self.skill_md_path = self.skill_dir / "SKILL.md"

    def summarize_reference(self, content: str, target_ratio: float = 0.3) -> str:
        """Intelligently summarize reference content to reduce size.

        Strategy:
        1. Keep first 20% (introduction/overview)
        2. Extract code blocks (prioritize examples)
        3. Keep headings and their first paragraph
        4. Skip repetitive content

        Args:
            content: Full reference content
            target_ratio: Target size as ratio of original (0.3 = 30%)

        Returns:
            Summarized content
        """
        lines = content.split('\n')
        target_lines = int(len(lines) * target_ratio)

        # Priority 1: Keep introduction (first 20%)
        intro_lines = int(len(lines) * 0.2)
        result_lines = lines[:intro_lines]

        # Priority 2: Extract code blocks
        in_code_block = False
        code_blocks = []
        current_block = []
        block_start_idx = 0

        for i, line in enumerate(lines[intro_lines:], start=intro_lines):
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block - add closing ``` and save
                    current_block.append(line)
                    code_blocks.append((block_start_idx, current_block))
                    current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                    block_start_idx = i
                    current_block = [line]
            elif in_code_block:
                current_block.append(line)

        # Combine: intro + code blocks + headings
        result = result_lines.copy()

        # Add code blocks first (prioritize code examples)
        for idx, block in code_blocks[:5]:  # Max 5 code blocks
            result.append("")  # Add blank line before code block
            result.extend(block)

        # Priority 3: Keep headings with first paragraph
        i = intro_lines
        headings_added = 0
        while i < len(lines) and headings_added < 10:
            line = lines[i]
            if line.startswith('#'):
                # Found heading - keep it and next 3 lines
                chunk = lines[i:min(i+4, len(lines))]
                result.extend(chunk)
                headings_added += 1
                i += 4
            else:
                i += 1

        result.append("\n\n[Content intelligently summarized - full details in reference files]")

        return '\n'.join(result)

    def create_enhancement_prompt(self, use_summarization=False, summarization_ratio=0.3):
        """Create the prompt file for Claude Code

        Args:
            use_summarization: If True, apply smart summarization to reduce size
            summarization_ratio: Target size ratio when summarizing (0.3 = 30%)
        """

        # Read reference files
        references = read_reference_files(
            self.skill_dir,
            max_chars=LOCAL_CONTENT_LIMIT,
            preview_limit=LOCAL_PREVIEW_LIMIT
        )

        if not references:
            print("❌ No reference files found")
            return None

        # Calculate total size
        total_ref_size = sum(len(c) for c in references.values())

        # Apply summarization if requested or if content is too large
        if use_summarization or total_ref_size > 30000:
            if not use_summarization:
                print(f"  ⚠️  Large skill detected ({total_ref_size:,} chars)")
                print(f"  📊 Applying smart summarization (target: {int(summarization_ratio*100)}% of original)")
                print()

            # Summarize each reference
            summarized_refs = {}
            for filename, content in references.items():
                summarized = self.summarize_reference(content, summarization_ratio)
                summarized_refs[filename] = summarized

            references = summarized_refs
            new_size = sum(len(c) for c in references.values())
            print(f"  ✓ Reduced from {total_ref_size:,} to {new_size:,} chars ({int(new_size/total_ref_size*100)}%)")
            print()

        # Read current SKILL.md
        current_skill_md = ""
        if self.skill_md_path.exists():
            current_skill_md = self.skill_md_path.read_text(encoding='utf-8')

        # Build prompt
        prompt = f"""I need you to enhance the SKILL.md file for the {self.skill_dir.name} skill.

CURRENT SKILL.MD:
{'-'*60}
{current_skill_md if current_skill_md else '(No existing SKILL.md - create from scratch)'}
{'-'*60}

REFERENCE DOCUMENTATION:
{'-'*60}
"""

        # Add references (already summarized if needed)
        for filename, content in references.items():
            # Further limit per-file to 12K to be safe
            max_per_file = 12000
            if len(content) > max_per_file:
                content = content[:max_per_file] + "\n\n[Content truncated for size...]"
            prompt += f"\n## {filename}\n{content}\n"

        prompt += f"""
{'-'*60}

YOUR TASK:
Create an EXCELLENT SKILL.md file that will help Claude use this documentation effectively.

Requirements:
1. **Clear "When to Use This Skill" section**
   - Be SPECIFIC about trigger conditions
   - List concrete use cases

2. **Excellent Quick Reference section**
   - Extract 5-10 of the BEST, most practical code examples from the reference docs
   - Choose SHORT, clear examples (5-20 lines max)
   - Include both simple and intermediate examples
   - Use proper language tags (cpp, python, javascript, json, etc.)
   - Add clear descriptions for each example

3. **Detailed Reference Files description**
   - Explain what's in each reference file
   - Help users navigate the documentation

4. **Practical "Working with This Skill" section**
   - Clear guidance for beginners, intermediate, and advanced users
   - Navigation tips

5. **Key Concepts section** (if applicable)
   - Explain core concepts
   - Define important terminology

IMPORTANT:
- Extract REAL examples from the reference docs above
- Prioritize SHORT, clear examples
- Make it actionable and practical
- Keep the frontmatter (---\\nname: ...\\n---) intact
- Use proper markdown formatting

SAVE THE RESULT:
Save the complete enhanced SKILL.md to: {self.skill_md_path.absolute()}

First, backup the original to: {self.skill_md_path.with_suffix('.md.backup').absolute()}
"""

        return prompt

    def run(self, headless=True, timeout=600):
        """Main enhancement workflow with automatic smart summarization for large skills.

        Automatically detects large skills (>30K chars) and applies smart summarization
        to ensure compatibility with Claude CLI's ~30-40K character limit.

        Smart summarization strategy:
        - Keeps first 20% (introduction/overview)
        - Extracts up to 5 best code blocks
        - Keeps up to 10 section headings with first paragraph
        - Reduces to ~30% of original size

        Args:
            headless: If True, run claude directly without opening terminal (default: True)
            timeout: Maximum time to wait for enhancement in seconds (default: 600 = 10 minutes)

        Returns:
            bool: True if enhancement process started successfully, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"LOCAL ENHANCEMENT: {self.skill_dir.name}")
        print(f"{'='*60}\n")

        # Validate
        if not self.skill_dir.exists():
            print(f"❌ Directory not found: {self.skill_dir}")
            return False

        # Read reference files
        print("📖 Reading reference documentation...")
        references = read_reference_files(
            self.skill_dir,
            max_chars=LOCAL_CONTENT_LIMIT,
            preview_limit=LOCAL_PREVIEW_LIMIT
        )

        if not references:
            print("❌ No reference files found to analyze")
            return False

        print(f"  ✓ Read {len(references)} reference files")
        total_size = sum(len(c) for c in references.values())
        print(f"  ✓ Total size: {total_size:,} characters\n")

        # Check if we need smart summarization
        use_summarization = total_size > 30000

        if use_summarization:
            print("⚠️  LARGE SKILL DETECTED")
            print(f"  📊 Reference content: {total_size:,} characters")
            print(f"  💡 Claude CLI limit: ~30,000-40,000 characters")
            print()
            print("  🔧 Applying smart summarization to ensure success...")
            print("     • Keeping introductions and overviews")
            print("     • Extracting best code examples")
            print("     • Preserving key concepts and headings")
            print("     • Target: ~30% of original size")
            print()

        # Create prompt
        print("📝 Creating enhancement prompt...")
        prompt = self.create_enhancement_prompt(use_summarization=use_summarization)

        if not prompt:
            return False

        # Save prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            prompt_file = f.name
            f.write(prompt)

        if use_summarization:
            print(f"  ✓ Prompt created and optimized ({len(prompt):,} characters)")
            print(f"  ✓ Ready for Claude CLI (within safe limits)")
            print()
        else:
            print(f"  ✓ Prompt saved ({len(prompt):,} characters)\n")

        # Headless mode: Run claude directly without opening terminal
        if headless:
            return self._run_headless(prompt_file, timeout)

        # Terminal mode: Launch Claude Code in new terminal
        print("🚀 Launching Claude Code in new terminal...")
        print("   This will:")
        print("   1. Open a new terminal window")
        print("   2. Run Claude Code with the enhancement task")
        print("   3. Claude will read the docs and enhance SKILL.md")
        print("   4. Terminal will auto-close when done")
        print()

        # Create a shell script to run in the terminal
        shell_script = f'''#!/bin/bash
claude {prompt_file}
echo ""
echo "✅ Enhancement complete!"
echo "Press any key to close..."
read -n 1
rm {prompt_file}
'''

        # Save shell script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            script_file = f.name
            f.write(shell_script)

        os.chmod(script_file, 0o755)

        # Launch in new terminal (macOS specific)
        if sys.platform == 'darwin':
            # Detect which terminal app to use
            terminal_app, detection_method = detect_terminal_app()

            # Show detection info
            if detection_method == 'SKILL_SEEKER_TERMINAL':
                print(f"   Using terminal: {terminal_app} (from SKILL_SEEKER_TERMINAL)")
            elif detection_method == 'TERM_PROGRAM':
                print(f"   Using terminal: {terminal_app} (inherited from current terminal)")
            elif detection_method.startswith('unknown TERM_PROGRAM'):
                print(f"⚠️  {detection_method}")
                print(f"   → Using Terminal.app as fallback")
            else:
                print(f"   Using terminal: {terminal_app} (default)")

            try:
                subprocess.Popen(['open', '-a', terminal_app, script_file])
            except Exception as e:
                print(f"⚠️  Error launching {terminal_app}: {e}")
                print(f"\nManually run: {script_file}")
                return False
        else:
            print("⚠️  Auto-launch only works on macOS")
            print(f"\nManually run this command in a new terminal:")
            print(f"  claude '{prompt_file}'")
            print(f"\nThen delete the prompt file:")
            print(f"  rm '{prompt_file}'")
            return False

        print("✅ New terminal launched with Claude Code!")
        print()
        print("📊 Status:")
        print(f"  - Prompt file: {prompt_file}")
        print(f"  - Skill directory: {self.skill_dir.absolute()}")
        print(f"  - SKILL.md will be saved to: {self.skill_md_path.absolute()}")
        print(f"  - Original backed up to: {self.skill_md_path.with_suffix('.md.backup').absolute()}")
        print()
        print("⏳ Wait for Claude Code to finish in the other terminal...")
        print("   (Usually takes 30-60 seconds)")
        print()
        print("💡 When done:")
        print(f"  1. Check the enhanced SKILL.md: {self.skill_md_path}")
        print(f"  2. If you don't like it, restore: mv {self.skill_md_path.with_suffix('.md.backup')} {self.skill_md_path}")
        print(f"  3. Package: skill-seekers package {self.skill_dir}/")

        return True

    def _run_headless(self, prompt_file, timeout):
        """Run Claude enhancement in headless mode (no terminal window)

        Args:
            prompt_file: Path to prompt file
            timeout: Maximum seconds to wait

        Returns:
            bool: True if enhancement succeeded
        """
        import time
        from pathlib import Path

        print("✨ Running Claude Code enhancement (headless mode)...")
        print(f"   Timeout: {timeout} seconds ({timeout//60} minutes)")
        print()

        # Record initial state
        initial_mtime = self.skill_md_path.stat().st_mtime if self.skill_md_path.exists() else 0
        initial_size = self.skill_md_path.stat().st_size if self.skill_md_path.exists() else 0

        # Start timer
        start_time = time.time()

        try:
            # Run claude command directly (this WAITS for completion)
            print("   Running: claude {prompt_file}")
            print("   ⏳ Please wait...")
            print()

            result = subprocess.run(
                ['claude', prompt_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            elapsed = time.time() - start_time

            # Check if successful
            if result.returncode == 0:
                # Verify SKILL.md was actually updated
                if self.skill_md_path.exists():
                    new_mtime = self.skill_md_path.stat().st_mtime
                    new_size = self.skill_md_path.stat().st_size

                    if new_mtime > initial_mtime and new_size > initial_size:
                        print(f"✅ Enhancement complete! ({elapsed:.1f} seconds)")
                        print(f"   SKILL.md updated: {new_size:,} bytes")
                        print()

                        # Clean up prompt file
                        try:
                            os.unlink(prompt_file)
                        except:
                            pass

                        return True
                    else:
                        print(f"⚠️  Claude finished but SKILL.md was not updated")
                        print(f"   This might indicate an error during enhancement")
                        print()
                        return False
                else:
                    print(f"❌ SKILL.md not found after enhancement")
                    return False
            else:
                print(f"❌ Claude Code returned error (exit code: {result.returncode})")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"\n⚠️  Enhancement timed out after {elapsed:.0f} seconds")
            print(f"   Timeout limit: {timeout} seconds")
            print()
            print("   Possible reasons:")
            print("   - Skill is very large (many references)")
            print("   - Claude is taking longer than usual")
            print("   - Network issues")
            print()
            print("   Try:")
            print("   1. Use terminal mode: --interactive-enhancement")
            print("   2. Reduce reference content")
            print("   3. Try again later")

            # Clean up
            try:
                os.unlink(prompt_file)
            except:
                pass

            return False

        except FileNotFoundError:
            print("❌ 'claude' command not found")
            print()
            print("   Make sure Claude Code CLI is installed:")
            print("   See: https://docs.claude.com/claude-code")
            print()
            print("   Try terminal mode instead: --interactive-enhancement")

            return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhance a skill with Claude Code (local)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Headless mode (default - runs in background)
  skill-seekers enhance output/react/

  # Interactive mode (opens terminal window)
  skill-seekers enhance output/react/ --interactive-enhancement

  # Custom timeout
  skill-seekers enhance output/react/ --timeout 1200
"""
    )

    parser.add_argument(
        'skill_directory',
        help='Path to skill directory (e.g., output/react/)'
    )

    parser.add_argument(
        '--interactive-enhancement',
        action='store_true',
        help='Open terminal window for enhancement (default: headless mode)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout in seconds for headless mode (default: 600 = 10 minutes)'
    )

    args = parser.parse_args()

    # Run enhancement
    enhancer = LocalSkillEnhancer(args.skill_directory)
    headless = not args.interactive_enhancement  # Invert: default is headless
    success = enhancer.run(headless=headless, timeout=args.timeout)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
