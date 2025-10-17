# Repository Structure

```
doc-to-skill/
│
├── README.md                      # Main documentation (start here!)
├── QUICKSTART.md                  # 3-step quick start guide
├── LICENSE                        # MIT License
├── .gitignore                     # Git ignore rules
│
├── 🐍 Core Scripts
│   ├── doc_scraper.py             # Main scraping tool
│   ├── enhance_skill.py           # AI enhancement (API-based)
│   ├── enhance_skill_local.py     # AI enhancement (LOCAL, no API)
│   └── package_skill.py           # Skill packaging tool
│
├── 📁 configs/                    # Preset configurations
│   ├── godot.json
│   ├── react.json
│   ├── vue.json
│   ├── django.json
│   ├── fastapi.json
│   ├── steam-inventory.json
│   ├── steam-economy.json
│   └── steam-economy-complete.json
│
├── 📚 docs/                       # Detailed documentation
│   ├── CLAUDE.md                  # Technical architecture
│   ├── ENHANCEMENT.md             # AI enhancement guide
│   ├── UPLOAD_GUIDE.md            # How to upload skills
│   └── READY_TO_SHARE.md          # Sharing checklist
│
└── 📦 output/                     # Generated skills (git-ignored)
    ├── {name}_data/               # Scraped raw data (cached)
    └── {name}/                    # Built skills
        ├── SKILL.md               # Main skill file
        └── references/            # Reference documentation
```

## Key Files

### For Users:
- **README.md** - Start here for overview and installation
- **QUICKSTART.md** - Get started in 3 steps
- **configs/** - 8 ready-to-use presets

### For Developers:
- **doc_scraper.py** - Main tool (787 lines)
- **docs/CLAUDE.md** - Architecture and internals
- **docs/ENHANCEMENT.md** - How enhancement works

### For Contributors:
- **LICENSE** - MIT License
- **.gitignore** - What Git ignores
- **docs/READY_TO_SHARE.md** - Distribution guide
