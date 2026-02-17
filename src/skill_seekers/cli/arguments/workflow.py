"""
CLI arguments for enhancement workflows.

Supports:
- --enhance-workflow: Use predefined workflow
- --enhance-stage: Quick inline stages
- --var: Override workflow variables
- --workflow-dry-run: Preview workflow without execution
"""

# Enhancement workflow arguments
WORKFLOW_ARGUMENTS = {
    "enhance_workflow": {
        "flags": ("--enhance-workflow",),
        "kwargs": {
            "action": "append",
            "help": "Enhancement workflow to use (name or path to YAML file). "
            "Can be used multiple times to chain workflows. "
            "Examples: 'security-focus', 'architecture-comprehensive', "
            "'~/.config/skill-seekers/workflows/my-workflow.yaml'. "
            "Multiple: --enhance-workflow security-focus --enhance-workflow minimal",
            "metavar": "WORKFLOW",
        },
    },
    "enhance_stage": {
        "flags": ("--enhance-stage",),
        "kwargs": {
            "type": str,
            "action": "append",
            "help": "Add inline enhancement stage. Format: 'name:prompt'. "
            "Can be used multiple times. Example: "
            "--enhance-stage 'security:Analyze for security issues' "
            "--enhance-stage 'cleanup:Remove boilerplate sections'",
            "metavar": "NAME:PROMPT",
        },
    },
    "workflow_var": {
        "flags": ("--var",),
        "kwargs": {
            "type": str,
            "action": "append",
            "help": "Override workflow variable. Format: 'key=value'. "
            "Can be used multiple times. Example: "
            "--var focus_area=performance --var detail_level=basic",
            "metavar": "KEY=VALUE",
        },
    },
    "workflow_dry_run": {
        "flags": ("--workflow-dry-run",),
        "kwargs": {
            "action": "store_true",
            "help": "Show workflow stages without executing (dry run mode)",
        },
    },
    "workflow_history": {
        "flags": ("--workflow-history",),
        "kwargs": {
            "type": str,
            "help": "Save workflow execution history to file",
            "metavar": "FILE",
        },
    },
}


def add_workflow_arguments(parser, include_all=True):
    """Add workflow arguments to parser."""
    for arg_name, arg_config in WORKFLOW_ARGUMENTS.items():
        if include_all or arg_name in ["enhance_workflow", "enhance_stage"]:
            parser.add_argument(*arg_config["flags"], **arg_config["kwargs"])
