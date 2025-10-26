#!/usr/bin/env python3
"""
SKILL.md Enhancement Script (Local - Using Claude Code)
Opens a new terminal with Claude Code to enhance SKILL.md, then reports back.
No API key needed - uses your existing Claude Code Max plan!

Usage:
    python3 cli/enhance_skill_local.py output/steam-inventory/
    python3 cli/enhance_skill_local.py output/react/
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

# Add parent directory to path for imports when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.constants import LOCAL_CONTENT_LIMIT, LOCAL_PREVIEW_LIMIT
from cli.utils import read_reference_files


class LocalSkillEnhancer:
    def __init__(self, skill_dir):
        self.skill_dir = Path(skill_dir)
        self.references_dir = self.skill_dir / "references"
        self.skill_md_path = self.skill_dir / "SKILL.md"

    def create_enhancement_prompt(self):
        """Create the prompt file for Claude Code"""

        # Read reference files
        references = read_reference_files(
            self.skill_dir,
            max_chars=LOCAL_CONTENT_LIMIT,
            preview_limit=LOCAL_PREVIEW_LIMIT
        )

        if not references:
            print("❌ No reference files found")
            return None

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

        for filename, content in references.items():
            prompt += f"\n## {filename}\n{content[:15000]}\n"

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

    def run(self):
        """Main enhancement workflow"""
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

        # Create prompt
        print("📝 Creating enhancement prompt...")
        prompt = self.create_enhancement_prompt()

        if not prompt:
            return False

        # Save prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            prompt_file = f.name
            f.write(prompt)

        print(f"  ✓ Prompt saved ({len(prompt):,} characters)\n")

        # Launch Claude Code in new terminal
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
            # macOS Terminal - simple approach
            try:
                subprocess.Popen(['open', '-a', 'Terminal', script_file])
            except Exception as e:
                print(f"⚠️  Error launching terminal: {e}")
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
        print(f"  3. Package: python3 cli/package_skill.py {self.skill_dir}/")

        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cli/enhance_skill_local.py <skill_directory>")
        print()
        print("Examples:")
        print("  python3 cli/enhance_skill_local.py output/steam-inventory/")
        print("  python3 cli/enhance_skill_local.py output/react/")
        sys.exit(1)

    skill_dir = sys.argv[1]

    enhancer = LocalSkillEnhancer(skill_dir)
    success = enhancer.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
