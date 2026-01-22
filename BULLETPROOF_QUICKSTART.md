# Bulletproof Quick Start Guide

**Target Audience:** Complete beginners | Never used Python/git before? Start here!

**Time:** 15-30 minutes total (including all installations)

**Result:** Working Skill Seeker installation + your first Claude skill created

---

## 📋 What You'll Need

Before starting, you need:
- A computer (macOS, Linux, or Windows with WSL)
- Internet connection
- 30 minutes of time

That's it! We'll install everything else together.

---

## Step 1: Install Python (5 minutes)

### Check if You Already Have Python

Open Terminal (macOS/Linux) or Command Prompt (Windows) and type:

```bash
python3 --version
```

**✅ If you see:** `Python 3.10.x` or `Python 3.11.x` or higher → **Skip to Step 2!**

**❌ If you see:** `command not found` or version less than 3.10 → **Continue below**

### Install Python

#### macOS:
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3
```

**Verify:**
```bash
python3 --version
# Should show: Python 3.11.x or similar
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Verify:**
```bash
python3 --version
pip3 --version
```

#### Windows:
1. Download Python from: https://www.python.org/downloads/
2. Run installer
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Open Command Prompt and verify:
```bash
python --version
```

**✅ Success looks like:**
```
Python 3.11.5
```

---

## Step 2: Install Git (3 minutes)

### Check if You Have Git

```bash
git --version
```

**✅ If you see:** `git version 2.x.x` → **Skip to Step 3!**

**❌ If not installed:**

#### macOS:
```bash
brew install git
```

#### Linux:
```bash
sudo apt install git
```

#### Windows:
Download from: https://git-scm.com/download/win

**Verify:**
```bash
git --version
# Should show: git version 2.x.x
```

---

## Step 3: Get Skill Seeker (2 minutes)

### Choose Where to Put It

Pick a location for the project. Good choices:
- macOS/Linux: `~/Projects/` or `~/Documents/`
  - Note: `~` means your home directory (`$HOME` or `/Users/yourname` on macOS, `/home/yourname` on Linux)
- Windows: `C:\Users\YourName\Projects\`

### Clone the Repository

```bash
# Create Projects directory (if it doesn't exist)
mkdir -p ~/Projects
cd ~/Projects

# Clone Skill Seeker
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git

# Enter the directory
cd Skill_Seekers
```

**✅ Success looks like:**
```
Cloning into 'Skill_Seekers'...
remote: Enumerating objects: 245, done.
remote: Counting objects: 100% (245/245), done.
```

**Verify you're in the right place:**
```bash
pwd
# Should show something like:
#   macOS: /Users/yourname/Projects/Skill_Seekers
#   Linux: /home/yourname/Projects/Skill_Seekers
# (Replace 'yourname' with YOUR actual username)

ls
# Should show: README.md, cli/, mcp/, configs/, etc.
```

**❌ If `git clone` fails:**
```bash
# Check internet connection
ping google.com

# Or download ZIP manually:
# https://github.com/yusufkaraaslan/Skill_Seekers/archive/refs/heads/main.zip
# Then unzip and cd into it
```

---

## Step 4: Setup Virtual Environment & Install Skill Seekers (3 minutes)

A virtual environment keeps Skill Seeker's dependencies isolated and prevents conflicts.

```bash
# Make sure you're in the Skill_Seekers directory
cd ~/Projects/Skill_Seekers  # ~ means your home directory ($HOME)
                             # Adjust if you chose a different location

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# Windows users: venv\Scripts\activate
```

**✅ Success looks like:**
```
(venv) username@computer Skill_Seekers %
```
Notice `(venv)` appears in your prompt - this means the virtual environment is active!

```bash
# Now install Skill Seekers package (this installs all dependencies automatically)
pip install -e .
```

**✅ Success looks like:**
```
Successfully installed skill-seekers-2.7.4 requests-2.32.5 beautifulsoup4-4.14.2 anthropic-0.76.0 ...
Obtaining file:///path/to/Skill_Seekers
Installing collected packages: skill-seekers
Successfully installed skill-seekers
```

**What just happened?**
- `pip install -e .` installs the package in "editable" mode
- The `.` means "current directory" (where pyproject.toml is)
- This automatically installs ALL required dependencies
- This registers the `skill-seekers` command so you can use it from anywhere
- The `-e` flag means changes to the code take effect immediately (useful for development)

**Important Notes:**
- **Every time** you open a new terminal to use Skill Seeker, run `source venv/bin/activate` first (Windows: `venv\Scripts\activate`)
- You'll know it's active when you see `(venv)` in your terminal prompt
- To deactivate later: just type `deactivate`

**❌ If python3 not found:**
```bash
# Try without the 3
python -m venv venv
```

**❌ If permission denied:**
```bash
# Virtual environment approach doesn't need sudo - you might have the wrong path
# Make sure you're in the Skill_Seekers directory:
pwd
# Should show something like:
#   macOS: /Users/yourname/Projects/Skill_Seekers
#   Linux: /home/yourname/Projects/Skill_Seekers
# (Replace 'yourname' with YOUR actual username)
```

**❌ If "pip: command not found":**
```bash
# Try with python -m pip instead
python3 -m pip install -e .
```

---

## Step 5: Test Your Installation (1 minute)

Let's make sure everything works:

```bash
# Test the main script can run
skill-seekers scrape --help
```

**✅ Success looks like:**
```
usage: doc_scraper.py [-h] [--config CONFIG] [--interactive] ...
```

**❌ If you see "No such file or directory":**
```bash
# Check you're in the right directory
pwd
# Should show path ending in /Skill_Seekers

# List files
ls cli/
# Should show: doc_scraper.py, estimate_pages.py, etc.
```

---

## Step 6: Create Your First Skill! (5-10 minutes)

Let's create a simple skill using a preset configuration.

### Option A: Small Test (Recommended First Time)

```bash
# Create a config for a small site first
cat > configs/test.json << 'EOF'
{
  "name": "test-skill",
  "description": "Test skill creation",
  "base_url": "https://tailwindcss.com/docs/installation",
  "selectors": {
    "main_content": "#content-wrapper",
    "title": "h1, h2, h3",
    "code_blocks": "pre code"
  },
  "max_pages": 5,
  "rate_limit": 0.5
}
EOF

# Run the scraper
skill-seekers scrape --config configs/test.json
```

**Note for Windows users:** The `cat > file << 'EOF'` syntax doesn't work in PowerShell. Instead, create the file manually:

```powershell
# In PowerShell, create configs/test.json with this content:
@"
{
  "name": "test-skill",
  "description": "Test skill creation",
  "base_url": "https://tailwindcss.com/docs/installation",
  "selectors": {
    "main_content": "#content-wrapper",
    "title": "h1, h2, h3",
    "code_blocks": "pre code"
  },
  "max_pages": 5,
  "rate_limit": 0.5
}
"@ | Out-File -FilePath configs/test.json -Encoding utf8

# Then run the scraper
skill-seekers scrape --config configs/test.json
```

**What happens:**
1. Scrapes 5 pages from Tailwind CSS docs
2. Creates `output/test-skill/` directory
3. Generates SKILL.md and reference files

**⏱️ Time:** ~30 seconds

**✅ Success looks like:**
```
Scraping: https://tailwindcss.com/docs/installation
Page 1/5: Installation
Page 2/5: Editor Setup
...
✅ Skill created at: output/test-skill/
```

### Option B: Full Example (React Docs)

```bash
# Use the React preset
skill-seekers scrape --config configs/react.json --max-pages 50
```

**⏱️ Time:** ~5 minutes

**What you get:**
- `output/react/SKILL.md` - Main skill file
- `output/react/references/` - Organized documentation

### Verify It Worked

```bash
# Check the output
ls output/test-skill/
# Should show: SKILL.md, references/, scripts/, assets/

# Look at the generated skill
head output/test-skill/SKILL.md
```

---

## Step 7: Package for Claude (30 seconds)

```bash
# Package the skill
skill-seekers package output/test-skill/
```

**✅ Success looks like:**
```
✅ Skill packaged successfully!
📦 Created: output/test-skill.zip
📏 Size: 45.2 KB

Ready to upload to Claude AI!
```

**Now you have:** `output/test-skill.zip` ready to upload to Claude!

---

## Step 8: Upload to Claude (2 minutes)

1. Go to https://claude.ai
2. Click your profile → Settings
3. Click "Knowledge" or "Skills"
4. Click "Upload Skill"
5. Select `output/test-skill.zip`
6. Done! Claude can now use this skill

---

## 🎉 Success! What's Next?

You now have a working Skill Seeker installation! Here's what you can do:

### Try Other Presets

```bash
# See all available presets
ls configs/

# Try Vue.js
skill-seekers scrape --config configs/vue.json --max-pages 50

# Try Django
skill-seekers scrape --config configs/django.json --max-pages 50
```

### Create Custom Skills

```bash
# Interactive mode - answer questions
skill-seekers scrape --interactive

# Or create config for any website
skill-seekers scrape \
  --name myframework \
  --url https://docs.myframework.com/ \
  --description "My favorite framework"
```

### Use with Claude Code (Advanced)

If you have Claude Code installed:

```bash
# One-time setup
./setup_mcp.sh

# Then use natural language in Claude Code:
# "Generate a skill for Svelte docs"
# "Package the skill at output/svelte/"
```

**See:** [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for full MCP setup

---

## 🔧 Troubleshooting

### "Command not found" errors

**Problem:** `python3: command not found`

**Solution:** Python not installed or not in PATH
- macOS/Linux: Reinstall Python with brew/apt
- Windows: Reinstall Python, check "Add to PATH"
- Try `python` instead of `python3`

### "Permission denied" errors

**Problem:** Can't install packages or run scripts

**Solution:**
```bash
# Use --user flag
pip3 install --user requests beautifulsoup4

# Or make script executable
chmod +x cli/doc_scraper.py
```

### "No such file or directory"

**Problem:** Can't find cli/doc_scraper.py

**Solution:** You're not in the right directory
```bash
# Go to the Skill_Seekers directory
cd ~/Projects/Skill_Seekers  # Adjust your path

# Verify
ls cli/
# Should show doc_scraper.py
```

### "ModuleNotFoundError" or "command not found: skill-seekers"

**Problem:** Package not installed or virtual environment not activated

**Solution:**
```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

# Install the package
pip install -e .

# If that fails, try:
python3 -m pip install -e .
```

### Scraping is slow or fails

**Problem:** Takes forever or gets errors

**Solution:**
```bash
# Use smaller max_pages for testing
skill-seekers scrape --config configs/react.json --max-pages 10

# Check internet connection
ping google.com

# Check the website is accessible
curl -I https://docs.yoursite.com
```

### Still stuck?

1. **Check our detailed troubleshooting guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Open an issue:** https://github.com/yusufkaraaslan/Skill_Seekers/issues
3. **Include this info:**
   - Operating system (macOS 13, Ubuntu 22.04, Windows 11, etc.)
   - Python version (`python3 --version`)
   - Full error message
   - What command you ran

---

## 📚 Next Steps

- **Read the full README:** [README.md](README.md)
- **Learn about presets:** [configs/](configs/)
- **Try MCP integration:** [docs/MCP_SETUP.md](docs/MCP_SETUP.md)
- **Advanced usage:** [docs/](docs/)

---

## ✅ Quick Reference

```bash
# Your typical workflow:

# 1. Create/use a config
skill-seekers scrape --config configs/react.json --max-pages 50

# 2. Package it
skill-seekers package output/react/

# 3. Upload output/react.zip to Claude

# Done! 🎉
```

**Common locations:**
- **Configs:** `configs/*.json`
- **Output:** `output/skill-name/`
- **Packaged skills:** `output/skill-name.zip`

**Time estimates:**
- Small skill (5-10 pages): 30 seconds
- Medium skill (50-100 pages): 3-5 minutes
- Large skill (500+ pages): 15-30 minutes

---

**Still confused?** That's okay! Open an issue and we'll help you get started: https://github.com/yusufkaraaslan/Skill_Seekers/issues/new
