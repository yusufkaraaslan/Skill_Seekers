"""Workflows subcommand parser."""

from .base import SubcommandParser


class WorkflowsParser(SubcommandParser):
    """Parser for the workflows subcommand."""

    @property
    def name(self) -> str:
        return "workflows"

    @property
    def help(self) -> str:
        return "Manage enhancement workflow presets"

    @property
    def description(self) -> str:
        return (
            "List, inspect, copy, add, remove, and validate enhancement workflow "
            "presets. Bundled presets ship with the package; user presets live in "
            "~/.config/skill-seekers/workflows/."
        )

    def add_arguments(self, parser) -> None:
        subparsers = parser.add_subparsers(dest="workflows_action", metavar="ACTION")

        # list
        subparsers.add_parser(
            "list",
            help="List all available workflows (bundled + user)",
        )

        # show
        show_p = subparsers.add_parser(
            "show",
            help="Print YAML content of a workflow",
        )
        show_p.add_argument("workflow_name", help="Workflow name (e.g. security-focus)")

        # copy
        copy_p = subparsers.add_parser(
            "copy",
            help="Copy bundled workflow(s) to user dir for editing",
        )
        copy_p.add_argument(
            "workflow_names",
            nargs="+",
            help="Bundled workflow name(s) to copy",
        )

        # add
        add_p = subparsers.add_parser(
            "add",
            help="Install a custom YAML file into the user workflow directory",
        )
        add_p.add_argument(
            "files",
            nargs="+",
            help="Path(s) to YAML workflow file(s) to install",
        )
        add_p.add_argument(
            "--name",
            help="Override the workflow filename (stem); only valid when adding a single file",
        )

        # remove
        remove_p = subparsers.add_parser(
            "remove",
            help="Delete workflow(s) from the user directory (bundled workflows cannot be removed)",
        )
        remove_p.add_argument(
            "workflow_names",
            nargs="+",
            help="User workflow name(s) to remove",
        )

        # validate
        validate_p = subparsers.add_parser(
            "validate",
            help="Parse and validate a workflow by name or file path",
        )
        validate_p.add_argument("workflow_name", help="Workflow name or path to YAML file")
