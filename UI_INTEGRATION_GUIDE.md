# UI Integration Guide
## How the CLI Refactor Enables Future UI Development

**Date:** 2026-02-14  
**Status:** Planning Document  
**Related:** CLI_REFACTOR_PROPOSAL.md

---

## Executive Summary

The "Pure Explicit" architecture proposed for fixing #285 is **ideal** for UI development because:

1. ✅ **Single source of truth** for all command options
2. ✅ **Self-documenting** argument definitions
3. ✅ **Easy to introspect** for dynamic form generation
4. ✅ **Consistent validation** between CLI and UI

**Recommendation:** Proceed with the refactor. It actively enables future UI work.

---

## Why This Architecture is UI-Friendly

### Current Problem (Without Refactor)

```python
# BEFORE: Arguments scattered in multiple files
# doc_scraper.py
def create_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Skill name")  # ← Here
    parser.add_argument("--max-pages", type=int)      # ← Here
    return parser

# parsers/scrape_parser.py  
class ScrapeParser:
    def add_arguments(self, parser):
        parser.add_argument("--name", help="Skill name")  # ← Duplicate!
        # max-pages forgotten!
```

**UI Problem:** Which arguments exist? What's the full schema? Hard to discover.

### After Refactor (UI-Friendly)

```python
# AFTER: Centralized, structured definitions
# arguments/scrape.py

SCRAPER_ARGUMENTS = {
    "name": {
        "type": str,
        "help": "Skill name",
        "ui_label": "Skill Name",
        "ui_section": "Basic",
        "placeholder": "e.g., React"
    },
    "max_pages": {
        "type": int,
        "help": "Maximum pages to scrape",
        "ui_label": "Max Pages",
        "ui_section": "Limits",
        "min": 1,
        "max": 1000,
        "default": 100
    },
    "async_mode": {
        "type": bool,
        "help": "Use async scraping",
        "ui_label": "Async Mode",
        "ui_section": "Performance",
        "ui_widget": "checkbox"
    }
}

def add_scrape_arguments(parser):
    for name, config in SCRAPER_ARGUMENTS.items():
        parser.add_argument(f"--{name}", **config)
```

**UI Benefit:** Arguments are data! Easy to iterate and build forms.

---

## UI Architecture Options

### Option 1: Console UI (TUI) - Recommended First Step

**Libraries:** `rich`, `textual`, `inquirer`, `questionary`

```python
# Example: TUI using the shared argument definitions
# src/skill_seekers/ui/console/scrape_wizard.py

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from skill_seekers.cli.arguments.scrape import SCRAPER_ARGUMENTS
from skill_seekers.cli.presets.scrape_presets import PRESETS


class ScrapeWizard:
    """Interactive TUI for scrape command."""
    
    def __init__(self):
        self.console = Console()
        self.results = {}
    
    def run(self):
        """Run the wizard."""
        self.console.print(Panel.fit(
            "[bold blue]Skill Seekers - Scrape Wizard[/bold blue]",
            border_style="blue"
        ))
        
        # Step 1: Choose preset (simplified) or custom
        use_preset = Confirm.ask("Use a preset configuration?")
        
        if use_preset:
            self._select_preset()
        else:
            self._custom_configuration()
        
        # Execute
        self._execute()
    
    def _select_preset(self):
        """Let user pick a preset."""
        from rich.table import Table
        
        table = Table(title="Available Presets")
        table.add_column("Preset", style="cyan")
        table.add_column("Description")
        table.add_column("Time")
        
        for name, preset in PRESETS.items():
            table.add_row(name, preset.description, preset.estimated_time)
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "Select preset",
            choices=list(PRESETS.keys()),
            default="standard"
        )
        
        self.results["preset"] = choice
    
    def _custom_configuration(self):
        """Interactive form based on argument definitions."""
        
        # Group by UI section
        sections = {}
        for name, config in SCRAPER_ARGUMENTS.items():
            section = config.get("ui_section", "General")
            if section not in sections:
                sections[section] = []
            sections[section].append((name, config))
        
        # Render each section
        for section_name, fields in sections.items():
            self.console.print(f"\n[bold]{section_name}[/bold]")
            
            for name, config in fields:
                value = self._prompt_for_field(name, config)
                self.results[name] = value
    
    def _prompt_for_field(self, name: str, config: dict):
        """Generate appropriate prompt based on argument type."""
        
        label = config.get("ui_label", name)
        help_text = config.get("help", "")
        
        if config.get("type") == bool:
            return Confirm.ask(f"{label}?", default=config.get("default", False))
        
        elif config.get("type") == int:
            return IntPrompt.ask(
                f"{label}",
                default=config.get("default")
            )
        
        else:
            return Prompt.ask(
                f"{label}",
                default=config.get("default", ""),
                show_default=True
            )
```

**Benefits:**
- ✅ Reuses all validation and help text
- ✅ Consistent with CLI behavior
- ✅ Can run in any terminal
- ✅ No web server needed

---

### Option 2: Web UI (Gradio/Streamlit)

**Libraries:** `gradio`, `streamlit`, `fastapi + htmx`

```python
# Example: Web UI using Gradio
# src/skill_seekers/ui/web/app.py

import gradio as gr
from skill_seekers.cli.arguments.scrape import SCRAPER_ARGUMENTS


def create_scrape_interface():
    """Create Gradio interface for scrape command."""
    
    # Generate inputs from argument definitions
    inputs = []
    
    for name, config in SCRAPER_ARGUMENTS.items():
        arg_type = config.get("type")
        label = config.get("ui_label", name)
        help_text = config.get("help", "")
        
        if arg_type == bool:
            inputs.append(gr.Checkbox(
                label=label,
                info=help_text,
                value=config.get("default", False)
            ))
        
        elif arg_type == int:
            inputs.append(gr.Number(
                label=label,
                info=help_text,
                value=config.get("default"),
                minimum=config.get("min"),
                maximum=config.get("max")
            ))
        
        else:
            inputs.append(gr.Textbox(
                label=label,
                info=help_text,
                placeholder=config.get("placeholder", ""),
                value=config.get("default", "")
            ))
    
    return gr.Interface(
        fn=run_scrape,
        inputs=inputs,
        outputs="text",
        title="Skill Seekers - Scrape Documentation",
        description="Convert documentation to AI-ready skills"
    )
```

**Benefits:**
- ✅ Automatic form generation from argument definitions
- ✅ Runs in browser
- ✅ Can be deployed as web service
- ✅ Great for non-technical users

---

### Option 3: Desktop GUI (Tkinter/PyQt)

```python
# Example: Tkinter GUI
# src/skill_seekers/ui/desktop/app.py

import tkinter as tk
from tkinter import ttk
from skill_seekers.cli.arguments.scrape import SCRAPER_ARGUMENTS


class SkillSeekersGUI:
    """Desktop GUI for Skill Seekers."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Skill Seekers")
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs from command arguments
        self._create_scrape_tab()
        self._create_github_tab()
    
    def _create_scrape_tab(self):
        """Create scrape tab from argument definitions."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scrape")
        
        # Group by section
        sections = {}
        for name, config in SCRAPER_ARGUMENTS.items():
            section = config.get("ui_section", "General")
            sections.setdefault(section, []).append((name, config))
        
        # Create form fields
        row = 0
        for section_name, fields in sections.items():
            # Section label
            ttk.Label(tab, text=section_name, font=('Arial', 10, 'bold')).grid(
                row=row, column=0, columnspan=2, pady=(10, 5), sticky='w'
            )
            row += 1
            
            for name, config in fields:
                # Label
                label = ttk.Label(tab, text=config.get("ui_label", name))
                label.grid(row=row, column=0, sticky='w', padx=5)
                
                # Input widget
                if config.get("type") == bool:
                    var = tk.BooleanVar(value=config.get("default", False))
                    widget = ttk.Checkbutton(tab, variable=var)
                else:
                    var = tk.StringVar(value=str(config.get("default", "")))
                    widget = ttk.Entry(tab, textvariable=var, width=40)
                
                widget.grid(row=row, column=1, sticky='ew', padx=5)
                
                # Help tooltip (simplified)
                if "help" in config:
                    label.bind("<Enter>", lambda e, h=config["help"]: self._show_tooltip(h))
                
                row += 1
```

---

## Enhancing Arguments for UI

To make arguments even more UI-friendly, we can add optional UI metadata:

```python
# arguments/scrape.py - Enhanced with UI metadata

SCRAPER_ARGUMENTS = {
    "url": {
        "type": str,
        "help": "Documentation URL to scrape",
        
        # UI-specific metadata (optional)
        "ui_label": "Documentation URL",
        "ui_section": "Source",  # Groups fields in UI
        "ui_order": 1,  # Display order
        "placeholder": "https://docs.example.com",
        "required": True,
        "validate": "url",  # Auto-validate as URL
    },
    
    "name": {
        "type": str,
        "help": "Name for the generated skill",
        
        "ui_label": "Skill Name",
        "ui_section": "Output",
        "ui_order": 2,
        "placeholder": "e.g., React, Python, Docker",
        "validate": r"^[a-zA-Z0-9_-]+$",  # Regex validation
    },
    
    "max_pages": {
        "type": int,
        "help": "Maximum pages to scrape",
        "default": 100,
        
        "ui_label": "Max Pages",
        "ui_section": "Limits",
        "ui_widget": "slider",  # Use slider in GUI
        "min": 1,
        "max": 1000,
        "step": 10,
    },
    
    "async_mode": {
        "type": bool,
        "help": "Enable async mode for faster scraping",
        "default": False,
        
        "ui_label": "Async Mode",
        "ui_section": "Performance",
        "ui_widget": "toggle",  # Use toggle switch in GUI
        "advanced": True,  # Hide in simple mode
    },
    
    "api_key": {
        "type": str,
        "help": "API key for enhancement",
        
        "ui_label": "API Key",
        "ui_section": "Authentication",
        "ui_widget": "password",  # Mask input
        "env_var": "ANTHROPIC_API_KEY",  # Can read from env
    }
}
```

---

## UI Modes

With this architecture, we can support multiple UI modes:

```bash
# CLI mode (default)
skill-seekers scrape --url https://react.dev --name react

# TUI mode (interactive)
skill-seekers ui scrape

# Web mode
skill-seekers ui --web

# Desktop mode  
skill-seekers ui --desktop
```

### Implementation

```python
# src/skill_seekers/cli/ui_command.py

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", help="Command to run in UI")
    parser.add_argument("--web", action="store_true", help="Launch web UI")
    parser.add_argument("--desktop", action="store_true", help="Launch desktop UI")
    parser.add_argument("--port", type=int, default=7860, help="Port for web UI")
    args = parser.parse_args()
    
    if args.web:
        from skill_seekers.ui.web.app import launch_web_ui
        launch_web_ui(port=args.port)
    
    elif args.desktop:
        from skill_seekers.ui.desktop.app import launch_desktop_ui
        launch_desktop_ui()
    
    else:
        # Default to TUI
        from skill_seekers.ui.console.app import launch_tui
        launch_tui(command=args.command)
```

---

## Migration Path to UI

### Phase 1: Refactor (Current Proposal)
- Create `arguments/` module with structured definitions
- Keep CLI working exactly as before
- **Enables:** UI can introspect arguments

### Phase 2: Add TUI (Optional, ~1 week)
- Build console UI using `rich` or `textual`
- Reuses argument definitions
- **Benefit:** Better UX for terminal users

### Phase 3: Add Web UI (Optional, ~2 weeks)
- Build web UI using `gradio` or `streamlit`
- Same argument definitions
- **Benefit:** Accessible to non-technical users

### Phase 4: Add Desktop GUI (Optional, ~3 weeks)
- Build native desktop app using `tkinter` or `PyQt`
- **Benefit:** Standalone application experience

---

## Code Example: Complete UI Integration

Here's how a complete integration would look:

```python
# src/skill_seekers/arguments/base.py

from dataclasses import dataclass
from typing import Optional, Any, Callable


@dataclass
class ArgumentDef:
    """Definition of a CLI argument with UI metadata."""
    
    # Core argparse fields
    name: str
    type: type
    help: str
    default: Any = None
    choices: Optional[list] = None
    action: Optional[str] = None
    
    # UI metadata (all optional)
    ui_label: Optional[str] = None
    ui_section: str = "General"
    ui_order: int = 0
    ui_widget: str = "auto"  # auto, text, checkbox, slider, select, etc.
    placeholder: Optional[str] = None
    required: bool = False
    advanced: bool = False  # Hide in simple mode
    
    # Validation
    validate: Optional[str] = None  # "url", "email", regex pattern
    min: Optional[float] = None
    max: Optional[float] = None
    
    # Environment
    env_var: Optional[str] = None  # Read default from env


class ArgumentRegistry:
    """Registry of all command arguments."""
    
    _commands = {}
    
    @classmethod
    def register(cls, command: str, arguments: list[ArgumentDef]):
        """Register arguments for a command."""
        cls._commands[command] = arguments
    
    @classmethod
    def get_arguments(cls, command: str) -> list[ArgumentDef]:
        """Get all arguments for a command."""
        return cls._commands.get(command, [])
    
    @classmethod
    def to_argparse(cls, command: str, parser):
        """Add registered arguments to argparse parser."""
        for arg in cls._commands.get(command, []):
            kwargs = {
                "help": arg.help,
                "default": arg.default,
            }
            if arg.type != bool:
                kwargs["type"] = arg.type
            if arg.action:
                kwargs["action"] = arg.action
            if arg.choices:
                kwargs["choices"] = arg.choices
            
            parser.add_argument(f"--{arg.name}", **kwargs)
    
    @classmethod
    def to_ui_form(cls, command: str) -> list[dict]:
        """Convert arguments to UI form schema."""
        return [
            {
                "name": arg.name,
                "label": arg.ui_label or arg.name,
                "type": arg.ui_widget if arg.ui_widget != "auto" else cls._infer_widget(arg),
                "section": arg.ui_section,
                "order": arg.ui_order,
                "required": arg.required,
                "placeholder": arg.placeholder,
                "validation": arg.validate,
                "min": arg.min,
                "max": arg.max,
            }
            for arg in cls._commands.get(command, [])
        ]
    
    @staticmethod
    def _infer_widget(arg: ArgumentDef) -> str:
        """Infer UI widget type from argument type."""
        if arg.type == bool:
            return "checkbox"
        elif arg.choices:
            return "select"
        elif arg.type == int and arg.min is not None and arg.max is not None:
            return "slider"
        else:
            return "text"


# Register all commands
from .scrape import SCRAPE_ARGUMENTS
from .github import GITHUB_ARGUMENTS

ArgumentRegistry.register("scrape", SCRAPE_ARGUMENTS)
ArgumentRegistry.register("github", GITHUB_ARGUMENTS)
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Is this refactor UI-friendly?** | ✅ Yes, actively enables UI development |
| **What UI types are supported?** | Console (TUI), Web, Desktop GUI |
| **How much extra work for UI?** | Minimal - reuse argument definitions |
| **Can we start with CLI only?** | ✅ Yes, UI is optional future work |
| **Should we add UI metadata now?** | Optional - can be added incrementally |

---

## Recommendation

1. **Proceed with the refactor** - It's the right foundation
2. **Start with CLI** - Get it working first
3. **Add basic UI metadata** - Just `ui_label` and `ui_section`
4. **Build TUI later** - When you want better terminal UX
5. **Consider Web UI** - If you need non-technical users

The refactor **doesn't commit you to a UI**, but makes it **easy to add one later**.

---

*End of Document*
