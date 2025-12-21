# Example Team Config Repository

This is an **example config repository** demonstrating how teams can share custom configs via git.

## Purpose

This repository shows how to:
- Structure a custom config repository
- Share team-specific documentation configs
- Use git-based config sources with Skill Seekers

## Structure

```
example-team/
├── README.md           # This file
├── react-custom.json   # Custom React config (modified selectors)
├── vue-internal.json   # Internal Vue docs config
└── company-api.json    # Company API documentation config
```

## Usage with Skill Seekers

### Option 1: Use this repo directly (for testing)

```python
# Using MCP tools (recommended)
add_config_source(
    name="example-team",
    git_url="file:///path/to/Skill_Seekers/configs/example-team"
)

fetch_config(source="example-team", config_name="react-custom")
```

### Option 2: Create your own team repo

```bash
# 1. Create new repo
mkdir my-team-configs
cd my-team-configs
git init

# 2. Add configs
cp /path/to/configs/react.json ./react-custom.json
# Edit configs as needed...

# 3. Commit and push
git add .
git commit -m "Initial team configs"
git remote add origin https://github.com/myorg/team-configs.git
git push -u origin main

# 4. Register with Skill Seekers
add_config_source(
    name="team",
    git_url="https://github.com/myorg/team-configs.git",
    token_env="GITHUB_TOKEN"
)

# 5. Use it
fetch_config(source="team", config_name="react-custom")
```

## Config Naming Best Practices

- Use descriptive names: `react-custom.json`, `vue-internal.json`
- Avoid name conflicts with official configs
- Include version if needed: `api-v2.json`
- Group by category: `frontend/`, `backend/`, `mobile/`

## Private Repositories

For private repos, set the appropriate token environment variable:

```bash
# GitHub
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# GitLab
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Bitbucket
export BITBUCKET_TOKEN=xxxxxxxxxxxxx
```

Then register the source:

```python
add_config_source(
    name="private-team",
    git_url="https://github.com/myorg/private-configs.git",
    source_type="github",
    token_env="GITHUB_TOKEN"
)
```

## Testing This Example

```bash
# From Skill_Seekers root directory
cd /mnt/1ece809a-2821-4f10-aecb-fcdf34760c0b/Git/Skill_Seekers

# Test with file:// URL (no auth needed)
python3 -c "
from skill_seekers.mcp.source_manager import SourceManager
from skill_seekers.mcp.git_repo import GitConfigRepo

# Add source
sm = SourceManager()
sm.add_source(
    name='example-team',
    git_url='file://$(pwd)/configs/example-team',
    branch='main'
)

# Clone and fetch config
gr = GitConfigRepo()
repo_path = gr.clone_or_pull('example-team', 'file://$(pwd)/configs/example-team')
config = gr.get_config(repo_path, 'react-custom')
print(f'✅ Loaded config: {config[\"name\"]}')
"
```

## Contributing

This is just an example! Create your own team repo with:
- Your team's custom selectors
- Internal documentation configs
- Company-specific configurations

## See Also

- [GIT_CONFIG_SOURCES.md](../../docs/GIT_CONFIG_SOURCES.md) - Complete guide
- [MCP_SETUP.md](../../docs/MCP_SETUP.md) - MCP server setup
- [README.md](../../README.md) - Main documentation
