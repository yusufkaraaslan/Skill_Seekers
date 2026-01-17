"""
Interactive Configuration Wizard for Skill Seekers

Provides user-friendly setup for GitHub tokens, API keys, and settings.
"""

import webbrowser

from .config_manager import get_config_manager


def show_welcome_message():
    """Show first-run welcome message."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              Welcome to Skill Seekers! 🎯                     ║
║                                                               ║
║  Convert documentation into LLM skills for Claude, Gemini,   ║
║  OpenAI ChatGPT, and more!                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Quick Start:

  1️⃣  Set up GitHub token (optional, but recommended):
      $ skill-seekers config --github

  2️⃣  Scrape documentation:
      $ skill-seekers scrape --config configs/react.json

  3️⃣  View available presets:
      $ skill-seekers estimate --all

For more help:
  $ skill-seekers --help
  $ skill-seekers config --help

Documentation: https://github.com/SkillSeekers/skill-seekers

""")

    config = get_config_manager()

    # Ask if user wants to run setup now
    response = input("Would you like to run the configuration wizard now? [y/N]: ").strip().lower()

    if response in ["y", "yes"]:
        main_menu()
    else:
        print("\nYou can run the configuration wizard anytime with:")
        print("  $ skill-seekers config\n")

    config.mark_welcome_shown()


def main_menu():
    """Show main configuration menu."""
    config = get_config_manager()

    while True:
        print("\n╔═══════════════════════════════════════════════════╗")
        print("║         Skill Seekers Configuration              ║")
        print("╚═══════════════════════════════════════════════════╝\n")

        print("  1. GitHub Token Setup")
        print("  2. API Keys (Claude, Gemini, OpenAI)")
        print("  3. Rate Limit Settings")
        print("  4. Resume Settings")
        print("  5. View Current Configuration")
        print("  6. Test Connections")
        print("  7. Clean Up Old Progress Files")
        print("  0. Exit\n")

        choice = input("Select an option [0-7]: ").strip()

        if choice == "1":
            github_token_menu()
        elif choice == "2":
            api_keys_menu()
        elif choice == "3":
            rate_limit_settings()
        elif choice == "4":
            resume_settings()
        elif choice == "5":
            config.display_config_summary()
            input("\nPress Enter to continue...")
        elif choice == "6":
            test_connections()
        elif choice == "7":
            config.cleanup_old_progress()
            input("\nPress Enter to continue...")
        elif choice == "0":
            print("\n✅ Configuration saved. Happy scraping! 🚀\n")
            break
        else:
            print("❌ Invalid choice. Please try again.")


def github_token_menu():
    """GitHub token configuration menu."""
    config = get_config_manager()

    while True:
        print("\n╔═══════════════════════════════════════════════════╗")
        print("║           GitHub Token Management                ║")
        print("╚═══════════════════════════════════════════════════╝\n")

        profiles = config.list_github_profiles()

        if profiles:
            print("Current Profiles:\n")
            for p in profiles:
                default = " ⭐ (default)" if p["is_default"] else ""
                print(f"  • {p['name']}{default}")
                if p["description"]:
                    print(f"    {p['description']}")
                print(f"    Strategy: {p['strategy']}, Timeout: {p['timeout']}m\n")
        else:
            print("No GitHub profiles configured.\n")

        print("Options:")
        print("  1. Add New Profile")
        print("  2. Remove Profile")
        print("  3. Set Default Profile")
        print("  4. Open GitHub Token Page")
        print("  0. Back to Main Menu\n")

        choice = input("Select an option [0-4]: ").strip()

        if choice == "1":
            add_github_profile()
        elif choice == "2":
            remove_github_profile()
        elif choice == "3":
            set_default_profile()
        elif choice == "4":
            open_github_token_page()
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice. Please try again.")


def add_github_profile():
    """Add a new GitHub profile interactively."""
    config = get_config_manager()

    print("\n📝 Add New GitHub Profile\n")

    # Profile name
    while True:
        name = input("Profile name (e.g., 'personal', 'work'): ").strip()
        if not name:
            print("❌ Profile name cannot be empty.")
            continue
        if name in config.config["github"]["profiles"]:
            print(f"❌ Profile '{name}' already exists.")
            overwrite = input("Overwrite? [y/N]: ").strip().lower()
            if overwrite not in ["y", "yes"]:
                continue
        break

    # Description
    description = input("Description (optional): ").strip()

    # Token
    print("\nTo create a GitHub token:")
    print("  1. Go to: https://github.com/settings/tokens")
    print("  2. Click 'Generate new token' → 'Generate new token (classic)'")
    print("  3. Scopes needed:")
    print("     • For public repos: 'public_repo'")
    print("     • For private repos: 'repo' (full access)")
    print("  4. Copy the token (ghp_...)\n")

    open_now = input("Open GitHub token page in browser? [Y/n]: ").strip().lower()
    if open_now not in ["n", "no"]:
        open_github_token_page()

    while True:
        token = input("\nGitHub token (ghp_...): ").strip()
        if not token:
            print("❌ Token cannot be empty.")
            continue
        if not (token.startswith("ghp_") or token.startswith("github_pat_")):
            print("⚠️  Warning: Token doesn't match GitHub format")
            proceed = input("Continue anyway? [y/N]: ").strip().lower()
            if proceed not in ["y", "yes"]:
                continue
        break

    # Rate limit strategy
    print("\nRate Limit Strategy:")
    print("  1. prompt - Ask what to do (default)")
    print("  2. wait - Wait until reset")
    print("  3. switch - Try another profile")
    print("  4. fail - Fail immediately")

    strategy_choice = input("\nSelect strategy [1-4] (default: 1): ").strip() or "1"
    strategy_map = {"1": "prompt", "2": "wait", "3": "switch", "4": "fail"}
    strategy = strategy_map.get(strategy_choice, "prompt")

    # Timeout
    timeout_input = input("\nTimeout in minutes (default: 30): ").strip() or "30"
    try:
        timeout = int(timeout_input)
    except ValueError:
        print("⚠️  Invalid timeout, using default 30 minutes")
        timeout = 30

    # Set as default
    has_profiles = bool(config.config["github"]["profiles"])
    if has_profiles:
        set_default = input("\nSet as default profile? [y/N]: ").strip().lower() in ["y", "yes"]
    else:
        set_default = True  # First profile is always default

    # Add profile
    config.add_github_profile(
        name=name,
        token=token,
        description=description,
        rate_limit_strategy=strategy,
        timeout_minutes=timeout,
        set_as_default=set_default,
    )

    print(f"\n✅ GitHub profile '{name}' added successfully!")


def remove_github_profile():
    """Remove a GitHub profile."""
    config = get_config_manager()

    profiles = config.list_github_profiles()
    if not profiles:
        print("\n❌ No profiles to remove.")
        return

    print("\n🗑️  Remove GitHub Profile\n")
    print("Available profiles:")
    for idx, p in enumerate(profiles, 1):
        default = " (default)" if p["is_default"] else ""
        print(f"  {idx}. {p['name']}{default}")

    choice = input(f"\nSelect profile to remove [1-{len(profiles)}] or 0 to cancel: ").strip()

    try:
        choice_idx = int(choice)
        if choice_idx == 0:
            return
        if 1 <= choice_idx <= len(profiles):
            profile_name = profiles[choice_idx - 1]["name"]
            confirm = input(f"Really remove profile '{profile_name}'? [y/N]: ").strip().lower()
            if confirm in ["y", "yes"]:
                config.remove_github_profile(profile_name)
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Invalid input.")


def set_default_profile():
    """Set default GitHub profile."""
    config = get_config_manager()

    profiles = config.list_github_profiles()
    if not profiles:
        print("\n❌ No profiles available.")
        return

    print("\n⭐ Set Default GitHub Profile\n")
    print("Available profiles:")
    for idx, p in enumerate(profiles, 1):
        default = " (current default)" if p["is_default"] else ""
        print(f"  {idx}. {p['name']}{default}")

    choice = input(f"\nSelect default profile [1-{len(profiles)}] or 0 to cancel: ").strip()

    try:
        choice_idx = int(choice)
        if choice_idx == 0:
            return
        if 1 <= choice_idx <= len(profiles):
            profile_name = profiles[choice_idx - 1]["name"]
            config.config["github"]["default_profile"] = profile_name
            config.save_config()
            print(f"\n✅ Set '{profile_name}' as default profile")
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Invalid input.")


def open_github_token_page():
    """Open GitHub token creation page in browser."""
    url = "https://github.com/settings/tokens/new"
    print(f"\n🌐 Opening {url}...")
    try:
        webbrowser.open(url)
        print("✅ Opened in browser")
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")
        print(f"   Please visit: {url}")


def api_keys_menu():
    """API keys configuration menu."""
    config = get_config_manager()

    print("\n╔═══════════════════════════════════════════════════╗")
    print("║              API Keys Management                 ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    print("Current status:")
    for provider in ["anthropic", "google", "openai"]:
        key = config.get_api_key(provider)
        status = "✅ Set" if key else "❌ Not set"
        source = ""
        if key:
            import os

            env_var = {
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
            }[provider]
            source = " (from environment)" if os.getenv(env_var) else " (from config)"
        print(f"  • {provider.capitalize()}: {status}{source}")

    print("\nOptions:")
    print("  1. Set Anthropic (Claude) API Key")
    print("  2. Set Google (Gemini) API Key")
    print("  3. Set OpenAI (ChatGPT) API Key")
    print("  0. Back to Main Menu\n")

    choice = input("Select an option [0-3]: ").strip()

    provider_map = {
        "1": ("anthropic", "https://console.anthropic.com/settings/keys"),
        "2": ("google", "https://makersuite.google.com/app/apikey"),
        "3": ("openai", "https://platform.openai.com/api-keys"),
    }

    if choice in provider_map:
        provider, url = provider_map[choice]
        set_api_key(provider, url)
    elif choice != "0":
        print("❌ Invalid choice.")


def set_api_key(provider: str, url: str):
    """Set an API key interactively."""
    config = get_config_manager()

    print(f"\n🔑 Set {provider.capitalize()} API Key\n")
    print(f"Get your API key at: {url}\n")

    open_now = input("Open in browser? [Y/n]: ").strip().lower()
    if open_now not in ["n", "no"]:
        try:
            webbrowser.open(url)
            print("✅ Opened in browser\n")
        except Exception:
            pass

    key = input(f"Enter {provider.capitalize()} API key (or leave empty to skip): ").strip()

    if key:
        config.set_api_key(provider, key)
    else:
        print("⏭️  Skipped")


def rate_limit_settings():
    """Configure rate limit settings."""
    config = get_config_manager()

    print("\n╔═══════════════════════════════════════════════════╗")
    print("║           Rate Limit Settings                    ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    current = config.config["rate_limit"]

    print("Current settings:")
    print(f"  • Default timeout: {current['default_timeout_minutes']} minutes")
    print(f"  • Auto-switch profiles: {current['auto_switch_profiles']}")
    print(f"  • Show countdown: {current['show_countdown']}\n")

    # Timeout
    timeout_input = input(
        f"Default timeout in minutes [{current['default_timeout_minutes']}]: "
    ).strip()
    if timeout_input:
        try:
            config.config["rate_limit"]["default_timeout_minutes"] = int(timeout_input)
        except ValueError:
            print("⚠️  Invalid input, keeping current value")

    # Auto-switch
    auto_switch_input = (
        input(f"Auto-switch to other profiles? [y/n] ({current['auto_switch_profiles']}): ")
        .strip()
        .lower()
    )
    if auto_switch_input:
        config.config["rate_limit"]["auto_switch_profiles"] = auto_switch_input in ["y", "yes"]

    # Show countdown
    countdown_input = (
        input(f"Show countdown timer? [y/n] ({current['show_countdown']}): ").strip().lower()
    )
    if countdown_input:
        config.config["rate_limit"]["show_countdown"] = countdown_input in ["y", "yes"]

    config.save_config()
    print("\n✅ Rate limit settings updated")


def resume_settings():
    """Configure resume/progress settings."""
    config = get_config_manager()

    print("\n╔═══════════════════════════════════════════════════╗")
    print("║             Resume Settings                      ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    current = config.config["resume"]

    print("Current settings:")
    print(f"  • Auto-save interval: {current['auto_save_interval_seconds']} seconds")
    print(f"  • Keep progress for: {current['keep_progress_days']} days\n")

    # Auto-save interval
    interval_input = input(
        f"Auto-save interval in seconds [{current['auto_save_interval_seconds']}]: "
    ).strip()
    if interval_input:
        try:
            config.config["resume"]["auto_save_interval_seconds"] = int(interval_input)
        except ValueError:
            print("⚠️  Invalid input, keeping current value")

    # Keep days
    days_input = input(
        f"Keep progress for how many days [{current['keep_progress_days']}]: "
    ).strip()
    if days_input:
        try:
            config.config["resume"]["keep_progress_days"] = int(days_input)
        except ValueError:
            print("⚠️  Invalid input, keeping current value")

    config.save_config()
    print("\n✅ Resume settings updated")


def test_connections():
    """Test GitHub and API connections."""
    config = get_config_manager()

    print("\n╔═══════════════════════════════════════════════════╗")
    print("║            Connection Tests                      ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    # Test GitHub tokens
    print("Testing GitHub tokens...")
    profiles = config.list_github_profiles()

    if not profiles:
        print("  ⚠️  No GitHub profiles configured")
    else:
        import requests

        for p in profiles:
            token = config.config["github"]["profiles"][p["name"]]["token"]
            try:
                response = requests.get(
                    "https://api.github.com/rate_limit",
                    headers={"Authorization": f"token {token}"},
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    remaining = data["rate"]["remaining"]
                    limit = data["rate"]["limit"]
                    print(f"  ✅ {p['name']}: {remaining}/{limit} requests remaining")
                else:
                    print(f"  ❌ {p['name']}: Invalid token (status {response.status_code})")
            except Exception as e:
                print(f"  ❌ {p['name']}: Connection failed - {e}")

    print()

    # Test API keys
    print("Testing API keys...")

    # Anthropic
    anthropic_key = config.get_api_key("anthropic")
    if anthropic_key:
        print("  ℹ️  Anthropic: Key configured (test would consume credits)")
    else:
        print("  ⚠️  Anthropic: Not configured")

    # Google
    google_key = config.get_api_key("google")
    if google_key:
        print("  ℹ️  Google: Key configured (test would consume quota)")
    else:
        print("  ⚠️  Google: Not configured")

    # OpenAI
    openai_key = config.get_api_key("openai")
    if openai_key:
        print("  ℹ️  OpenAI: Key configured (test would consume credits)")
    else:
        print("  ⚠️  OpenAI: Not configured")

    input("\nPress Enter to continue...")


def main():
    """Main entry point for config command."""
    import argparse

    parser = argparse.ArgumentParser(description="Configure Skill Seekers settings")
    parser.add_argument("--github", action="store_true", help="Go directly to GitHub token setup")
    parser.add_argument("--api-keys", action="store_true", help="Go directly to API keys setup")
    parser.add_argument("--show", action="store_true", help="Show current configuration and exit")
    parser.add_argument("--test", action="store_true", help="Test connections and exit")
    parser.add_argument("--welcome", action="store_true", help="Show welcome message")

    args = parser.parse_args()

    config = get_config_manager()

    # Handle direct options
    if args.welcome:
        show_welcome_message()
        return

    if args.show:
        config.display_config_summary()
        return

    if args.test:
        test_connections()
        return

    if args.github:
        github_token_menu()
        return

    if args.api_keys:
        api_keys_menu()
        return

    # Show main menu
    main_menu()


if __name__ == "__main__":
    main()
