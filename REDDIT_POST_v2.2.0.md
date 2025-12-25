# Reddit Post - Skill Seekers v2.2.0

**Target Subreddit:** r/ClaudeAI

---

## Title

Skill Seekers v2.2.0: Official Skill Library with 24+ Presets, Free Team Sharing (No Team Plan Required), and Custom Skill Repos Support

---

## Body

Hey everyone! 👋

Just released Skill Seekers v2.2.0 - a big update for the tool that converts any documentation into Claude AI skills.

## 🎯 Headline Features:

**1. Skill Library (Official Configs)**

24+ ready-to-use skill configs including React, Django, Godot, FastAPI, and more. No setup required - just works out of the box:

```python
fetch_config(config_name="godot")
```

**You can also contribute your own configs to the official Skill Library for everyone to use!**

**2. Free Team Sharing**

Share custom skill configs across your team without needing any paid plan. Register your private repo once and everyone can access:

```python
add_config_source(name="team", git_url="https://github.com/mycompany/configs.git")
fetch_config(source="team", config_name="internal-api")
```

**3. Custom Skill Repos**

Fetch configs directly from any git URL - GitHub, GitLab, Bitbucket, or Gitea:

```python
fetch_config(git_url="https://github.com/someorg/configs.git", config_name="custom-config")
```

## Other Changes:

- **Unified Language Detector** - Support for 20+ programming languages with confidence-based detection
- **Retry Utilities** - Exponential backoff for network resilience with async support
- **Performance** - Shallow clone (10-50x faster), intelligent caching, offline mode support
- **Security** - Tokens via environment variables only (never stored in files)
- **Bug Fixes** - Fixed local repository extraction limitations

## Install/Upgrade:

```bash
pip install --upgrade skill-seekers
```

**Links:**
- GitHub: https://github.com/yusufkaraaslan/Skill_Seekers
- PyPI: https://pypi.org/project/skill-seekers/
- Release Notes: https://github.com/yusufkaraaslan/Skill_Seekers/releases/tag/v2.2.0

Let me know if you have questions! 🚀

---

## Notes

- Posted on: [Date]
- Subreddit: r/ClaudeAI
- Post URL: [Add after posting]
