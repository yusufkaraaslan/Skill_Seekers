#!/usr/bin/env python3
"""
Enhancement Workflow Engine

Allows users to define custom AI enhancement workflows with:
- Sequential stages that build on previous results
- Custom prompts per stage
- History passing between stages
- Post-processing configuration
- Per-project and global workflow support

Usage:
    # Use global workflow
    skill-seekers analyze . --enhance-workflow security-focus

    # Use project workflow
    skill-seekers analyze . --enhance-workflow .skill-seekers/enhancement.yaml

    # Quick inline stages
    skill-seekers analyze . \\
        --enhance-stage "security:Analyze for security issues" \\
        --enhance-stage "cleanup:Remove boilerplate"
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from importlib.resources import files as importlib_files
from pathlib import Path
from typing import Any, Literal

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStage:
    """Single enhancement stage in a workflow."""

    name: str
    type: Literal["builtin", "custom"]
    target: str  # "patterns", "examples", "config", "skill_md", "all"
    prompt: str | None = None
    uses_history: bool = False
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PostProcessConfig:
    """Post-processing configuration."""

    remove_sections: list[str] = field(default_factory=list)
    reorder_sections: list[str] = field(default_factory=list)
    add_metadata: dict[str, Any] = field(default_factory=dict)
    custom_transforms: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EnhancementWorkflow:
    """Complete enhancement workflow definition."""

    name: str
    description: str
    version: str = "1.0"
    applies_to: list[str] = field(default_factory=lambda: ["codebase_analysis"])
    variables: dict[str, Any] = field(default_factory=dict)
    stages: list[WorkflowStage] = field(default_factory=list)
    post_process: PostProcessConfig = field(default_factory=PostProcessConfig)
    extends: str | None = None  # Inherit from another workflow


class WorkflowEngine:
    """
    Execute enhancement workflows with sequential stages.

    Each stage can:
    - Access previous stage results
    - Access all history
    - Access specific stages by name
    - Run custom AI prompts
    - Target specific parts of the analysis
    """

    def __init__(self, workflow: EnhancementWorkflow | str | Path):
        """
        Initialize workflow engine.

        Args:
            workflow: EnhancementWorkflow object or path to YAML file
        """
        if isinstance(workflow, (str, Path)):
            self.workflow = self._load_workflow(workflow)
        else:
            self.workflow = workflow

        self.history: list[dict[str, Any]] = []
        self.enhancer = None  # Lazy load UnifiedEnhancer

    def _load_workflow(self, workflow_ref: str | Path) -> EnhancementWorkflow:
        """Load workflow from YAML file using 3-level search order.

        Search order:
        1. Raw file path (absolute or relative) — existing behaviour
        2. ~/.config/skill-seekers/workflows/{name}.yaml — user overrides/custom
        3. skill_seekers/workflows/{name}.yaml via importlib.resources — bundled defaults
        """
        workflow_ref = Path(workflow_ref)

        # Add .yaml extension for bare names
        name_str = str(workflow_ref)
        if not name_str.endswith((".yaml", ".yml")):
            yaml_ref = Path(name_str + ".yaml")
        else:
            yaml_ref = workflow_ref

        resolved_path: Path | None = None
        yaml_text: str | None = None

        # Level 1: absolute path or relative-to-CWD
        if yaml_ref.is_absolute():
            if yaml_ref.exists():
                resolved_path = yaml_ref
        else:
            cwd_path = Path.cwd() / yaml_ref
            if cwd_path.exists():
                resolved_path = cwd_path
            elif yaml_ref.exists():
                resolved_path = yaml_ref

        # Level 2: user config directory
        if resolved_path is None:
            user_dir = Path.home() / ".config" / "skill-seekers" / "workflows"
            user_path = user_dir / yaml_ref.name
            if user_path.exists():
                resolved_path = user_path

        # Level 3: bundled package workflows via importlib.resources
        if resolved_path is None:
            bare_name = yaml_ref.name  # e.g. "security-focus.yaml"
            try:
                pkg_ref = importlib_files("skill_seekers.workflows").joinpath(bare_name)
                yaml_text = pkg_ref.read_text(encoding="utf-8")
                logger.info(f"📋 Loading bundled workflow: {bare_name}")
            except (FileNotFoundError, TypeError, ModuleNotFoundError) as exc:
                raise FileNotFoundError(
                    f"Workflow '{yaml_ref.stem}' not found. "
                    "Use 'skill-seekers workflows list' to see available workflows."
                ) from exc

        if resolved_path is not None:
            logger.info(f"📋 Loading workflow: {resolved_path}")
            with open(resolved_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_text)

        # Handle inheritance (extends)
        if "extends" in data and data["extends"]:
            parent = self._load_workflow(data["extends"])
            data = self._merge_workflows(parent, data)

        # Parse stages
        stages = []
        for stage_data in data.get("stages", []):
            stages.append(
                WorkflowStage(
                    name=stage_data["name"],
                    type=stage_data.get("type", "custom"),
                    target=stage_data.get("target", "all"),
                    prompt=stage_data.get("prompt"),
                    uses_history=stage_data.get("uses_history", False),
                    enabled=stage_data.get("enabled", True),
                    metadata=stage_data.get("metadata", {}),
                )
            )

        # Parse post-processing
        post_process_data = data.get("post_process", {})
        post_process = PostProcessConfig(
            remove_sections=post_process_data.get("remove_sections", []),
            reorder_sections=post_process_data.get("reorder_sections", []),
            add_metadata=post_process_data.get("add_metadata", {}),
            custom_transforms=post_process_data.get("custom_transforms", []),
        )

        return EnhancementWorkflow(
            name=data.get("name", "Unnamed Workflow"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            applies_to=data.get("applies_to", ["codebase_analysis"]),
            variables=data.get("variables", {}),
            stages=stages,
            post_process=post_process,
            extends=data.get("extends"),
        )

    def _merge_workflows(self, parent: EnhancementWorkflow, child_data: dict) -> dict:
        """Merge child workflow with parent (inheritance)."""
        # Start with parent as dict
        merged = {
            "name": child_data.get("name", parent.name),
            "description": child_data.get("description", parent.description),
            "version": child_data.get("version", parent.version),
            "applies_to": child_data.get("applies_to", parent.applies_to),
            "variables": {**parent.variables, **child_data.get("variables", {})},
            "stages": [],
            "post_process": {},
        }

        # Merge stages (child can override by name)
        parent_stages = {s.name: s for s in parent.stages}
        child_stages = {s["name"]: s for s in child_data.get("stages", [])}

        for name in list(parent_stages.keys()) + list(child_stages.keys()):
            if name in child_stages:
                # Child overrides parent
                stage_dict = child_stages[name]
            else:
                # Use parent stage
                stage = parent_stages[name]
                stage_dict = {
                    "name": stage.name,
                    "type": stage.type,
                    "target": stage.target,
                    "prompt": stage.prompt,
                    "uses_history": stage.uses_history,
                    "enabled": stage.enabled,
                }

            if stage_dict not in merged["stages"]:
                merged["stages"].append(stage_dict)

        # Merge post-processing
        parent_post = parent.post_process
        child_post = child_data.get("post_process", {})
        merged["post_process"] = {
            "remove_sections": child_post.get("remove_sections", parent_post.remove_sections),
            "reorder_sections": child_post.get("reorder_sections", parent_post.reorder_sections),
            "add_metadata": {
                **parent_post.add_metadata,
                **child_post.get("add_metadata", {}),
            },
            "custom_transforms": parent_post.custom_transforms
            + child_post.get("custom_transforms", []),
        }

        return merged

    def run(self, analysis_results: dict, context: dict | None = None) -> dict:
        """
        Run workflow stages sequentially.

        Args:
            analysis_results: Results from analysis (patterns, examples, etc.)
            context: Additional context variables

        Returns:
            Enhanced results after all stages
        """
        logger.info(f"🚀 Starting workflow: {self.workflow.name}")
        logger.info(f"   Description: {self.workflow.description}")
        logger.info(f"   Stages: {len(self.workflow.stages)}")

        current_results = analysis_results
        context = context or {}

        # Merge workflow variables into context
        context.update(self.workflow.variables)

        # Run each stage
        for idx, stage in enumerate(self.workflow.stages, 1):
            if not stage.enabled:
                logger.info(f"⏭️  Skipping disabled stage: {stage.name}")
                continue

            logger.info(f"🔄 Running stage {idx}/{len(self.workflow.stages)}: {stage.name}")

            # Build stage context
            stage_context = self._build_stage_context(stage, current_results, context)

            # Run stage
            try:
                stage_results = self._run_stage(stage, stage_context)

                # Save to history
                self.history.append(
                    {
                        "stage": stage.name,
                        "results": stage_results,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": stage.metadata,
                    }
                )

                # Merge stage results into current results
                current_results = self._merge_stage_results(
                    current_results, stage_results, stage.target
                )

                logger.info(f"   ✅ Stage complete: {stage.name}")

            except Exception as e:
                logger.error(f"   ❌ Stage failed: {stage.name} - {e}")
                # Continue with next stage (optional: make this configurable)
                continue

        # Post-processing
        logger.info("🔧 Running post-processing...")
        final_results = self._post_process(current_results)

        logger.info(f"✅ Workflow complete: {self.workflow.name}")
        return final_results

    def _build_stage_context(
        self, stage: WorkflowStage, current_results: dict, base_context: dict
    ) -> dict:
        """Build context for a stage (includes history if needed)."""
        context = {
            "current_results": current_results,
            **base_context,
        }

        if stage.uses_history and self.history:
            # Add previous stage
            context["previous_results"] = self.history[-1]["results"]

            # Add all history
            context["all_history"] = self.history

            # Add stages by name for easy access
            context["stages"] = {h["stage"]: h["results"] for h in self.history}

        return context

    def _run_stage(self, stage: WorkflowStage, context: dict) -> dict:
        """Run a single stage."""
        if stage.type == "builtin":
            return self._run_builtin_stage(stage, context)
        else:
            return self._run_custom_stage(stage, context)

    def _run_builtin_stage(self, stage: WorkflowStage, context: dict) -> dict:
        """Run built-in enhancement stage."""
        # Use existing enhancement system
        from skill_seekers.cli.ai_enhancer import PatternEnhancer, TestExampleEnhancer

        current = context["current_results"]

        # Determine what to enhance based on target
        if stage.target == "patterns" and "patterns" in current:
            enhancer = PatternEnhancer()
            enhanced_patterns = enhancer.enhance_patterns(current["patterns"])
            return {"patterns": enhanced_patterns}

        elif stage.target == "examples" and "examples" in current:
            enhancer = TestExampleEnhancer()
            enhanced_examples = enhancer.enhance_examples(current["examples"])
            return {"examples": enhanced_examples}

        else:
            logger.warning(f"Unknown builtin target: {stage.target}")
            return {}

    def _run_custom_stage(self, stage: WorkflowStage, context: dict) -> dict:
        """Run custom AI enhancement stage."""
        if not stage.prompt:
            logger.warning(f"Custom stage '{stage.name}' has no prompt")
            return {}

        # Lazy load enhancer
        if not self.enhancer:
            from skill_seekers.cli.ai_enhancer import AIEnhancer

            self.enhancer = AIEnhancer()

        # Format prompt with context
        try:
            formatted_prompt = stage.prompt.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context variable: {e}")
            formatted_prompt = stage.prompt

        # Call AI with custom prompt
        logger.info(f"   🤖 Running custom AI prompt...")
        response = self.enhancer._call_claude(formatted_prompt, max_tokens=3000)

        if not response:
            logger.warning(f"   ⚠️  No response from AI")
            return {}

        # Try to parse as JSON first, fallback to plain text
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Plain text response
            result = {"content": response, "stage": stage.name}

        return result

    def _merge_stage_results(self, current: dict, stage_results: dict, target: str) -> dict:
        """Merge stage results into current results."""
        if target == "all":
            # Merge everything
            return {**current, **stage_results}
        else:
            # Merge only specific target
            current[target] = stage_results.get(target, stage_results)
            return current

    def _post_process(self, results: dict) -> dict:
        """Apply post-processing configuration."""
        config = self.workflow.post_process

        # Remove sections
        for section in config.remove_sections:
            if section in results:
                logger.info(f"   🗑️  Removing section: {section}")
                del results[section]

        # Add metadata
        if config.add_metadata:
            if "metadata" not in results:
                results["metadata"] = {}
            results["metadata"].update(config.add_metadata)
            logger.info(f"   📝 Added metadata: {list(config.add_metadata.keys())}")

        # Reorder sections (for SKILL.md generation)
        if config.reorder_sections and "skill_md_sections" in results:
            logger.info(f"   🔄 Reordering sections...")
            # This will be used during SKILL.md generation
            results["section_order"] = config.reorder_sections

        # Custom transforms (extensibility)
        for transform in config.custom_transforms:
            logger.info(f"   ⚙️  Applying transform: {transform.get('name', 'unknown')}")
            # TODO: Implement custom transform system

        return results

    def save_history(self, output_path: Path):
        """Save workflow execution history."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        history_data = {
            "workflow": self.workflow.name,
            "version": self.workflow.version,
            "executed_at": datetime.now().isoformat(),
            "stages": self.history,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)

        logger.info(f"💾 Saved workflow history: {output_path}")


def list_bundled_workflows() -> list[str]:
    """Return names of all bundled default workflows (without .yaml extension)."""
    try:
        pkg = importlib_files("skill_seekers.workflows")
        names = []
        for item in pkg.iterdir():
            name = str(item.name)
            if name.endswith((".yaml", ".yml")):
                names.append(name.removesuffix(".yaml").removesuffix(".yml"))
        return sorted(names)
    except Exception:
        return []


def list_user_workflows() -> list[str]:
    """Return names of all user-defined workflows (without .yaml extension)."""
    user_dir = Path.home() / ".config" / "skill-seekers" / "workflows"
    if not user_dir.exists():
        return []
    names = []
    for p in user_dir.iterdir():
        if p.suffix in (".yaml", ".yml"):
            names.append(p.stem)
    return sorted(names)
