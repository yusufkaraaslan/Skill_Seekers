"""Shared workflow execution utility.

Provides a single run_workflows() function used by all scrapers
(doc_scraper, github_scraper, pdf_scraper, codebase_scraper) to execute
one or more enhancement workflows from CLI arguments.

Handles:
- Multiple --enhance-workflow flags (run in sequence)
- Inline --enhance-stage flags (combined into one inline workflow)
- --workflow-dry-run preview mode (exits after preview)
- --var variable substitution
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

logger = logging.getLogger(__name__)


def collect_workflow_vars(args: argparse.Namespace, extra: dict | None = None) -> dict:
    """Parse --var KEY=VALUE flags into a dict, optionally merged with extra context.

    extra (scraper metadata) is applied first; user --var flags take precedence.
    """
    vars_: dict = {}
    if extra:
        vars_.update(extra)
    if getattr(args, "var", None):
        for assignment in args.var:
            if "=" in assignment:
                key, value = assignment.split("=", 1)
                vars_[key.strip()] = value.strip()
    return vars_


def _build_inline_engine(args: argparse.Namespace):
    """Build a WorkflowEngine from --enhance-stage flags."""
    from skill_seekers.cli.enhancement_workflow import WorkflowEngine

    stages = []
    for i, spec in enumerate(args.enhance_stage, 1):
        if ":" in spec:
            name, prompt = spec.split(":", 1)
        else:
            name, prompt = f"stage_{i}", spec
        stages.append(
            {
                "name": name.strip(),
                "type": "custom",
                "prompt": prompt.strip(),
                "uses_history": True,
            }
        )

    inline_def = {
        "name": "inline_workflow",
        "description": "Custom inline workflow from --enhance-stage arguments",
        "stages": stages,
    }
    return WorkflowEngine(workflow_data=inline_def)


def run_workflows(
    args: argparse.Namespace,
    context: dict | None = None,
) -> tuple[bool, list[str]]:
    """Execute all enhancement workflows requested via CLI arguments.

    Runs named workflows (--enhance-workflow) in the order they were given,
    then runs the combined inline workflow (--enhance-stage) if any stages
    were specified.

    If --workflow-dry-run is set, all workflows are previewed and the process
    exits immediately (no files are modified).

    Args:
        args: Parsed CLI arguments (must contain enhance_workflow, enhance_stage,
              var, and workflow_dry_run attributes).
        context: Optional extra key/value pairs merged into workflow variables
                 (e.g. GitHub metadata). User --var flags take precedence.

    Returns:
        (any_executed, names) where any_executed is True when at least one
        workflow ran successfully and names is the list of workflow names that
        ran.
    """
    named_workflows: list[str] = getattr(args, "enhance_workflow", None) or []
    inline_stages: list[str] = getattr(args, "enhance_stage", None) or []
    dry_run: bool = getattr(args, "workflow_dry_run", False)

    if not named_workflows and not inline_stages:
        return False, []

    from skill_seekers.cli.enhancement_workflow import WorkflowEngine

    workflow_vars = collect_workflow_vars(args, extra=context)

    if workflow_vars:
        logger.info("   Workflow variables:")
        for k, v in workflow_vars.items():
            logger.info(f"     {k} = {v}")

    executed: list[str] = []

    # ── Named workflows ────────────────────────────────────────────────────
    total = len(named_workflows) + (1 if inline_stages else 0)
    if total > 1:
        logger.info(f"\n🔗 Chaining {total} workflow(s) in sequence")

    for idx, workflow_name in enumerate(named_workflows, 1):
        header = f"\n{'=' * 80}\n🔄 Workflow {idx}/{total}: {workflow_name}\n{'=' * 80}"
        logger.info(header)

        try:
            engine = WorkflowEngine(workflow_name)
        except Exception as exc:
            logger.error(f"❌ Failed to load workflow '{workflow_name}': {exc}")
            logger.info("   Skipping this workflow and continuing...")
            continue

        logger.info(f"   Description: {engine.workflow.description}")
        logger.info(f"   Stages: {len(engine.workflow.stages)}")

        if dry_run:
            logger.info("\n🔍 DRY RUN MODE - Previewing stages:")
            engine.preview(context=workflow_vars)
            continue  # Preview next workflow too

        try:
            engine.run(analysis_results={}, context=workflow_vars)
            executed.append(workflow_name)
            logger.info(f"\n✅ Workflow '{workflow_name}' completed successfully!")
        except Exception as exc:
            logger.error(f"❌ Workflow '{workflow_name}' failed: {exc}")
            import traceback

            traceback.print_exc()

    # ── Inline workflow ────────────────────────────────────────────────────
    if inline_stages:
        inline_idx = len(named_workflows) + 1
        header = (
            f"\n{'=' * 80}\n"
            f"🔄 Workflow {inline_idx}/{total}: inline ({len(inline_stages)} stage(s))\n"
            f"{'=' * 80}"
        )
        logger.info(header)

        try:
            engine = _build_inline_engine(args)
        except Exception as exc:
            logger.error(f"❌ Failed to build inline workflow: {exc}")
        else:
            if dry_run:
                logger.info("\n🔍 DRY RUN MODE - Previewing inline stages:")
                engine.preview(context=workflow_vars)
            else:
                try:
                    engine.run(analysis_results={}, context=workflow_vars)
                    executed.append("inline_workflow")
                    logger.info("\n✅ Inline workflow completed successfully!")
                except Exception as exc:
                    logger.error(f"❌ Inline workflow failed: {exc}")
                    import traceback

                    traceback.print_exc()

    if dry_run:
        logger.info("\n✅ Dry run complete! No changes made.")
        logger.info("   Remove --workflow-dry-run to execute.")
        sys.exit(0)

    if executed:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"✅ {len(executed)} workflow(s) completed: {', '.join(executed)}")
        logger.info(f"{'=' * 80}")

    return len(executed) > 0, executed
