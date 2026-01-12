#!/usr/bin/env python3
"""
SKILL.md Enhancement Script (Local - Using Claude Code)
Opens a new terminal with Claude Code to enhance SKILL.md, then reports back.
No API key needed - uses your existing Claude Code Max plan!

Usage:
    # Headless mode (default - runs in foreground, waits for completion)
    skill-seekers enhance output/react/

    # Background mode (runs in background, returns immediately)
    skill-seekers enhance output/react/ --background

    # Force mode (no confirmations, auto-yes to everything)
    skill-seekers enhance output/react/ --force

    # Daemon mode (persistent background process)
    skill-seekers enhance output/react/ --daemon

    # Interactive terminal mode
    skill-seekers enhance output/react/ --interactive-enhancement

Modes:
    - headless: Runs claude CLI directly, BLOCKS until done (default)
    - background: Runs claude CLI in background, returns immediately
    - daemon: Runs as persistent background process with monitoring
    - terminal: Opens new terminal window (interactive)

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
import json
import threading
from pathlib import Path
from datetime import datetime

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
    def __init__(self, skill_dir, force=True):
        """Initialize enhancer.

        Args:
            skill_dir: Path to skill directory
            force: If True, skip all confirmations (default: True, use --no-force to disable)
        """
        self.skill_dir = Path(skill_dir)
        self.references_dir = self.skill_dir / "references"
        self.skill_md_path = self.skill_dir / "SKILL.md"
        self.force = force
        self.status_file = self.skill_dir / ".enhancement_status.json"

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

        # Read reference files (with enriched metadata)
        references = read_reference_files(
            self.skill_dir,
            max_chars=LOCAL_CONTENT_LIMIT,
            preview_limit=LOCAL_PREVIEW_LIMIT
        )

        if not references:
            print("❌ No reference files found")
            return None

        # Analyze sources
        sources_found = set()
        for metadata in references.values():
            sources_found.add(metadata['source'])

        # Calculate total size
        total_ref_size = sum(meta['size'] for meta in references.values())

        # Apply summarization if requested or if content is too large
        if use_summarization or total_ref_size > 30000:
            if not use_summarization:
                print(f"  ⚠️  Large skill detected ({total_ref_size:,} chars)")
                print(f"  📊 Applying smart summarization (target: {int(summarization_ratio*100)}% of original)")
                print()

            # Summarize each reference
            for filename, metadata in references.items():
                summarized = self.summarize_reference(metadata['content'], summarization_ratio)
                metadata['content'] = summarized
                metadata['size'] = len(summarized)

            new_size = sum(meta['size'] for meta in references.values())
            print(f"  ✓ Reduced from {total_ref_size:,} to {new_size:,} chars ({int(new_size/total_ref_size*100)}%)")
            print()

        # Read current SKILL.md
        current_skill_md = ""
        if self.skill_md_path.exists():
            current_skill_md = self.skill_md_path.read_text(encoding='utf-8')

        # Analyze conflicts if present
        has_conflicts = any('conflicts' in meta['path'] for meta in references.values())

        # Build prompt with multi-source awareness
        prompt = f"""I need you to enhance the SKILL.md file for the {self.skill_dir.name} skill.

SKILL OVERVIEW:
- Name: {self.skill_dir.name}
- Source Types: {', '.join(sorted(sources_found))}
- Multi-Source: {'Yes' if len(sources_found) > 1 else 'No'}
- Conflicts Detected: {'Yes - see conflicts.md in references' if has_conflicts else 'No'}

CURRENT SKILL.MD:
{'-'*60}
{current_skill_md if current_skill_md else '(No existing SKILL.md - create from scratch)'}
{'-'*60}

SOURCE ANALYSIS:
{'-'*60}
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

        prompt += f"""
{'-'*60}

REFERENCE DOCUMENTATION:
{'-'*60}
"""

        # Add references grouped by (source, repo_id) with metadata
        for (source, repo_id) in sorted(by_source.keys()):
            if repo_id:
                prompt += f"\n### {source.upper()} SOURCES - {repo_id}\n\n"
            else:
                prompt += f"\n### {source.upper()} SOURCES\n\n"

            for filename, metadata in by_source[(source, repo_id)]:
                # Further limit per-file to 12K to be safe
                content = metadata['content']
                max_per_file = 12000
                if len(content) > max_per_file:
                    content = content[:max_per_file] + "\n\n[Content truncated for size...]"

                prompt += f"\n#### {filename}\n"
                if repo_id:
                    prompt += f"*Source: {metadata['source']} ({repo_id}), Confidence: {metadata['confidence']}*\n\n"
                else:
                    prompt += f"*Source: {metadata['source']}, Confidence: {metadata['confidence']}*\n\n"
                prompt += f"{content}\n"

        prompt += f"""
{'-'*60}

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
Create an EXCELLENT SKILL.md file that synthesizes knowledge from multiple sources.

Requirements:
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

IMPORTANT:
- Extract REAL examples from the reference docs above
- Prioritize HIGH CONFIDENCE sources when synthesizing
- Note source attribution when helpful (e.g., "Official docs say X, but codebase shows Y")
- Make discrepancies transparent, not hidden
- Prioritize SHORT, clear examples
- Make it actionable and practical
- Keep the frontmatter (---\\nname: ...\\n---) intact
- Use proper markdown formatting

SAVE THE RESULT:
You MUST save the complete enhanced SKILL.md file.

CRITICAL INSTRUCTIONS:
1. First, create a backup: Write the current SKILL.md content to SKILL.md.backup
2. Then, write the enhanced content to: SKILL.md

This is NOT a read-only task - you have permission to modify SKILL.md.
Even if running from within another Claude Code session, this modification is ALLOWED and EXPECTED.

VERIFICATION:
After writing, the file SKILL.md should:
- Exist in the current directory
- Be larger than the original (200-1000+ lines)
- Contain all the enhancements from the references above
"""

        return prompt

    def write_status(self, status, message="", progress=0.0, error=None):
        """Write enhancement status to file for monitoring.

        Args:
            status: One of: pending, running, completed, failed
            message: Status message
            progress: Progress percentage (0.0-1.0)
            error: Error message if failed
        """
        status_data = {
            "status": status,
            "message": message,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            "skill_dir": str(self.skill_dir),
            "error": error
        }

        self.status_file.write_text(json.dumps(status_data, indent=2), encoding='utf-8')

    def read_status(self):
        """Read enhancement status from file.

        Returns:
            dict: Status data or None if not found
        """
        if not self.status_file.exists():
            return None

        try:
            return json.loads(self.status_file.read_text(encoding='utf-8'))
        except:
            return None

    def run(self, headless=True, timeout=600, background=False, daemon=False):
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
            background: If True, run in background and return immediately (default: False)
            daemon: If True, run as persistent daemon with monitoring (default: False)

        Returns:
            bool: True if enhancement process started successfully, False otherwise
        """
        # Background mode: Run in background thread, return immediately
        if background:
            return self._run_background(headless, timeout)

        # Daemon mode: Run as persistent process with monitoring
        if daemon:
            return self._run_daemon(timeout)
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
        total_size = sum(ref['size'] for ref in references.values())
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
            # Use --dangerously-skip-permissions to bypass ALL permission checks
            print(f"   Running: claude --dangerously-skip-permissions {prompt_file}")
            print("   ⏳ Please wait...")
            print(f"   Working directory: {self.skill_dir}")
            print()

            result = subprocess.run(
                ['claude', '--dangerously-skip-permissions', prompt_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.skill_dir)  # Run from skill directory
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
                        print(f"   Initial: mtime={initial_mtime}, size={initial_size}")
                        print(f"   Final:   mtime={new_mtime}, size={new_size}")
                        print(f"   This might indicate an error during enhancement")
                        print()
                        # Show last 20 lines of stdout for debugging
                        if result.stdout:
                            print("   Last output from Claude:")
                            lines = result.stdout.strip().split('\n')[-20:]
                            for line in lines:
                                print(f"   | {line}")
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

    def _run_background(self, headless, timeout):
        """Run enhancement in background thread, return immediately.

        Args:
            headless: Run headless mode
            timeout: Timeout in seconds

        Returns:
            bool: True if background task started successfully
        """
        print(f"\n{'='*60}")
        print(f"BACKGROUND ENHANCEMENT: {self.skill_dir.name}")
        print(f"{'='*60}\n")

        # Write initial status
        self.write_status("pending", "Starting background enhancement...")

        def background_worker():
            """Worker function for background thread"""
            try:
                self.write_status("running", "Enhancement in progress...", progress=0.1)

                # Read reference files
                references = read_reference_files(
                    self.skill_dir,
                    max_chars=LOCAL_CONTENT_LIMIT,
                    preview_limit=LOCAL_PREVIEW_LIMIT
                )

                if not references:
                    self.write_status("failed", error="No reference files found")
                    return

                total_size = sum(len(c) for c in references.values())
                use_summarization = total_size > 30000

                self.write_status("running", "Creating enhancement prompt...", progress=0.3)

                # Create prompt
                prompt = self.create_enhancement_prompt(use_summarization=use_summarization)
                if not prompt:
                    self.write_status("failed", error="Failed to create prompt")
                    return

                # Save prompt to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    prompt_file = f.name
                    f.write(prompt)

                self.write_status("running", "Running Claude Code enhancement...", progress=0.5)

                # Run enhancement
                if headless:
                    # Run headless (subprocess.run - blocking in thread)
                    result = subprocess.run(
                        ['claude', prompt_file],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )

                    # Clean up
                    try:
                        os.unlink(prompt_file)
                    except:
                        pass

                    if result.returncode == 0:
                        self.write_status("completed", "Enhancement completed successfully!", progress=1.0)
                    else:
                        self.write_status("failed", error=f"Claude returned error: {result.returncode}")
                else:
                    # Terminal mode in background doesn't make sense
                    self.write_status("failed", error="Terminal mode not supported in background")

            except subprocess.TimeoutExpired:
                self.write_status("failed", error=f"Enhancement timed out after {timeout} seconds")
            except Exception as e:
                self.write_status("failed", error=str(e))

        # Start background thread
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()

        print("✅ Background enhancement started!")
        print()
        print("📊 Monitoring:")
        print(f"  - Status file: {self.status_file}")
        print(f"  - Check status: cat {self.status_file}")
        print(f"  - Or use: skill-seekers enhance-status {self.skill_dir}")
        print()
        print("💡 The enhancement will continue in the background.")
        print("   You can close this terminal - the process will keep running.")
        print()

        return True

    def _run_daemon(self, timeout):
        """Run as persistent daemon process with monitoring.

        Creates a detached background process that continues running even if parent exits.

        Args:
            timeout: Timeout in seconds

        Returns:
            bool: True if daemon started successfully
        """
        print(f"\n{'='*60}")
        print(f"DAEMON MODE: {self.skill_dir.name}")
        print(f"{'='*60}\n")

        # Write initial status
        self.write_status("pending", "Starting daemon process...")

        print("🔧 Creating daemon process...")

        # Create Python script for daemon
        daemon_script = f'''#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import tempfile
import json
from pathlib import Path
from datetime import datetime

skill_dir = Path("{self.skill_dir}")
status_file = skill_dir / ".enhancement_status.json"
skill_md_path = skill_dir / "SKILL.md"

def write_status(status, message="", progress=0.0, error=None):
    status_data = {{
        "status": status,
        "message": message,
        "progress": progress,
        "timestamp": datetime.now().isoformat(),
        "skill_dir": str(skill_dir),
        "error": error,
        "pid": os.getpid()
    }}
    status_file.write_text(json.dumps(status_data, indent=2), encoding='utf-8')

try:
    write_status("running", "Daemon started, loading references...", progress=0.1)

    # Import enhancement logic
    sys.path.insert(0, "{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

    enhancer = LocalSkillEnhancer("{self.skill_dir}")

    # Create prompt
    write_status("running", "Creating enhancement prompt...", progress=0.3)
    prompt = enhancer.create_enhancement_prompt(use_summarization=True)

    if not prompt:
        write_status("failed", error="Failed to create prompt")
        sys.exit(1)

    # Save prompt
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        prompt_file = f.name
        f.write(prompt)

    write_status("running", "Running Claude Code...", progress=0.5)

    # Run Claude
    result = subprocess.run(
        ['claude', prompt_file],
        capture_output=True,
        text=True,
        timeout={timeout}
    )

    # Clean up
    try:
        os.unlink(prompt_file)
    except:
        pass

    if result.returncode == 0:
        write_status("completed", "Enhancement completed successfully!", progress=1.0)
        sys.exit(0)
    else:
        write_status("failed", error=f"Claude returned error: {{result.returncode}}")
        sys.exit(1)

except subprocess.TimeoutExpired:
    write_status("failed", error=f"Enhancement timed out after {timeout} seconds")
    sys.exit(1)
except Exception as e:
    write_status("failed", error=str(e))
    sys.exit(1)
'''

        # Save daemon script
        daemon_script_path = self.skill_dir / ".enhancement_daemon.py"
        daemon_script_path.write_text(daemon_script, encoding='utf-8')
        daemon_script_path.chmod(0o755)

        # Start daemon process (fully detached)
        try:
            # Use nohup to detach from terminal
            log_file = self.skill_dir / ".enhancement_daemon.log"

            if self.force:
                # Force mode: No output, fully silent
                subprocess.Popen(
                    ['nohup', 'python3', str(daemon_script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            else:
                # Normal mode: Log to file
                with open(log_file, 'w') as log:
                    subprocess.Popen(
                        ['nohup', 'python3', str(daemon_script_path)],
                        stdout=log,
                        stderr=log,
                        start_new_session=True
                    )

            # Give daemon time to start
            time.sleep(1)

            # Read status to verify it started
            status = self.read_status()

            if status and status.get('status') in ['pending', 'running']:
                print("✅ Daemon process started successfully!")
                print()
                print("📊 Monitoring:")
                print(f"  - Status file: {self.status_file}")
                print(f"  - Log file: {log_file}")
                print(f"  - PID: {status.get('pid', 'unknown')}")
                print()
                print("💡 Commands:")
                print(f"  - Check status: cat {self.status_file}")
                print(f"  - View logs: tail -f {log_file}")
                print(f"  - Or use: skill-seekers enhance-status {self.skill_dir}")
                print()
                print("🔥 The daemon will continue running even if you close this terminal!")
                print()

                return True
            else:
                print("❌ Daemon failed to start")
                return False

        except Exception as e:
            print(f"❌ Failed to start daemon: {e}")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhance a skill with Claude Code (local)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Headless mode (default - runs in foreground, waits for completion, auto-force)
  skill-seekers enhance output/react/

  # Background mode (runs in background, returns immediately)
  skill-seekers enhance output/react/ --background

  # Daemon mode (persistent background process, fully detached)
  skill-seekers enhance output/react/ --daemon

  # Disable force mode (ask for confirmations)
  skill-seekers enhance output/react/ --no-force

  # Interactive mode (opens terminal window)
  skill-seekers enhance output/react/ --interactive-enhancement

  # Custom timeout
  skill-seekers enhance output/react/ --timeout 1200

Mode Comparison:
  - headless:    Runs claude CLI directly, BLOCKS until done (default)
  - background:  Runs in background thread, returns immediately
  - daemon:      Fully detached process, continues after parent exits
  - terminal:    Opens new terminal window (interactive)

Force Mode (Default ON):
  By default, all modes skip confirmations (auto-yes).
  Use --no-force to enable confirmation prompts.
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
        '--background',
        action='store_true',
        help='Run in background and return immediately (non-blocking)'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as persistent daemon process (fully detached)'
    )

    parser.add_argument(
        '--no-force',
        action='store_true',
        help='Disable force mode: enable confirmation prompts (default: force mode ON)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout in seconds for headless mode (default: 600 = 10 minutes)'
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    mode_count = sum([args.interactive_enhancement, args.background, args.daemon])
    if mode_count > 1:
        print("❌ Error: --interactive-enhancement, --background, and --daemon are mutually exclusive")
        print("   Choose only one mode")
        sys.exit(1)

    # Run enhancement
    # Force mode is ON by default, use --no-force to disable
    enhancer = LocalSkillEnhancer(args.skill_directory, force=not args.no_force)
    headless = not args.interactive_enhancement  # Invert: default is headless
    success = enhancer.run(
        headless=headless,
        timeout=args.timeout,
        background=args.background,
        daemon=args.daemon
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
