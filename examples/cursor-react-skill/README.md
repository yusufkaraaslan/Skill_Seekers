# Cursor + React Skill Example

Complete example showing how to use Skill Seekers to generate Cursor rules for React development.

## What This Example Does

- ✅ Generates React documentation skill
- ✅ Creates `.cursorrules` for Cursor IDE
- ✅ Shows AI-powered React code completion
- ✅ Includes sample React project

## Quick Start

### 1. Generate React Skill

```bash
# Install Skill Seekers
pip install skill-seekers

# Generate React documentation skill
skill-seekers scrape --config configs/react.json --max-pages 100

# Package for Cursor
skill-seekers package output/react --target claude
```

This creates `output/react-claude.zip` containing `SKILL.md` (the Cursor rules file).

### 2. Extract and Copy Rules

```bash
# Extract the ZIP
unzip output/react-claude.zip -d output/react-cursor

# Copy rules to your project
cp output/react-cursor/SKILL.md example-project/.cursorrules
```

Or use the automation script:

```bash
python generate_cursorrules.py
```

### 3. Test in Cursor

```bash
# Open project in Cursor
cursor example-project/

# Try these prompts in Cursor:
# - "Create a useState hook for managing user data"
# - "Add useEffect to fetch data on mount"
# - "Implement a custom hook for form validation"
# - "Create a component with proper TypeScript types"
```

## Expected Results

### Before (Without .cursorrules)

- Generic React suggestions
- May use outdated patterns (class components, etc.)
- No TypeScript best practices
- Missing modern Hooks patterns

### After (With .cursorrules)

- React 18+ specific patterns
- Hooks-based architecture (useState, useEffect, custom hooks)
- TypeScript strict mode with proper types
- Modern best practices (functional components, composition)
- Context API and state management patterns
- Performance optimization (useMemo, useCallback)

## Automation Script

The `generate_cursorrules.py` script automates the entire workflow:

```python
#!/usr/bin/env python3
"""
Automate Cursor rules generation for React.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False

    print(f"✅ Success!")
    if result.stdout:
        print(result.stdout)

    return True


def main():
    """Run the automation workflow."""
    print("=" * 60)
    print("Cursor Rules Generator - React Example")
    print("=" * 60)

    # Step 1: Scrape React docs
    if not run_command(
        ["skill-seekers", "scrape", "--config", "configs/react.json", "--max-pages", "100"],
        "Scraping React documentation"
    ):
        sys.exit(1)

    # Step 2: Package for Cursor
    if not run_command(
        ["skill-seekers", "package", "output/react", "--target", "claude"],
        "Packaging for Cursor"
    ):
        sys.exit(1)

    # Step 3: Extract ZIP
    if not run_command(
        ["unzip", "-o", "output/react-claude.zip", "-d", "output/react-cursor"],
        "Extracting packaged skill"
    ):
        sys.exit(1)

    # Step 4: Copy to example project
    source = Path("output/react-cursor/SKILL.md")
    target = Path("example-project/.cursorrules")

    if not source.exists():
        print(f"❌ Error: {source} not found")
        sys.exit(1)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text())

    print(f"\n✅ Copied rules to {target}")

    # Success summary
    print("\n" + "=" * 60)
    print("✅ Cursor rules generated successfully!")
    print("=" * 60)
    print(f"\n📁 Rules file: {target.absolute()}")
    print("\n🚀 Next steps:")
    print("   1. Open example-project/ in Cursor")
    print("   2. Try the example prompts in the README")
    print("   3. Compare AI suggestions before/after")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
```

## Sample .cursorrules File

See `.cursorrules.example` for a sample generated rules file. Key sections include:

- **React Fundamentals** - Components, JSX, props, state
- **Hooks** - useState, useEffect, useContext, custom hooks
- **TypeScript** - Proper typing for components, props, events
- **Performance** - useMemo, useCallback, React.memo
- **Best Practices** - Component composition, error boundaries
- **Common Patterns** - Forms, data fetching, routing

## Example Project Structure

The `example-project/` directory contains a minimal React + TypeScript setup:

```
example-project/
├── .cursorrules           # Generated rules (empty initially)
├── package.json           # React + TypeScript dependencies
├── tsconfig.json          # TypeScript configuration
├── src/
│   ├── App.tsx           # Main component
│   └── index.tsx         # Entry point
└── README.md             # Project-specific instructions
```

### Testing the AI

Open `example-project/` in Cursor and try these prompts:

**1. useState Hook:**
```
Create a counter component with increment and decrement buttons
```

**Expected output with .cursorrules:**
```tsx
import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState<number>(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <button onClick={() => setCount(count - 1)}>Decrement</button>
    </div>
  );
}
```

**2. Data Fetching:**
```
Create a component that fetches user data from an API
```

**Expected output with .cursorrules:**
```tsx
import { useState, useEffect } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

export function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('https://api.example.com/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name} - {user.email}</li>
      ))}
    </ul>
  );
}
```

**3. Custom Hook:**
```
Create a custom hook for form validation
```

**Expected output with .cursorrules:**
```tsx
import { useState, useCallback } from 'react';

interface ValidationRules {
  [field: string]: (value: string) => string | null;
}

export function useFormValidation(rules: ValidationRules) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = useCallback((field: string, value: string) => {
    const error = rules[field]?.(value);
    setErrors(prev => ({
      ...prev,
      [field]: error || ''
    }));
    return !error;
  }, [rules]);

  const validateAll = useCallback((values: Record<string, string>) => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    for (const field in rules) {
      const error = rules[field](values[field] || '');
      if (error) {
        newErrors[field] = error;
        isValid = false;
      }
    }

    setErrors(newErrors);
    return isValid;
  }, [rules]);

  return { errors, validate, validateAll };
}
```

## Files in This Example

- `README.md` - This file
- `generate_cursorrules.py` - Automation script
- `.cursorrules.example` - Sample generated rules
- `example-project/` - Minimal React + TypeScript project
- `requirements.txt` - Python dependencies (skill-seekers)

## Troubleshooting

### Issue: Rules not loading

**Solution:** Restart Cursor IDE or reload window (Cmd+Shift+P → "Reload Window")

### Issue: AI not using rules

**Solution:** Check `.cursorrules` is at project root. Verify with AI: "Are you aware of .cursorrules?"

### Issue: skill-seekers not found

**Solution:** Install Skill Seekers

```bash
pip install skill-seekers
```

### Issue: Scraping fails

**Solution:** Check internet connection, or use smaller --max-pages value

```bash
skill-seekers scrape --config configs/react.json --max-pages 50
```

## Next Steps

1. Customize rules for your project needs
2. Add project-specific patterns to `.cursorrules`
3. Include internal component library documentation
4. Share with team for consistency
5. Try other frameworks (Vue, Angular, Django, etc.)

## Related Examples

- [Windsurf Example](../windsurf-fastapi-context/)
- [Cline Example](../cline-django-assistant/)
- [Continue.dev Example](../continue-dev-universal/)
- [LangChain RAG Example](../langchain-rag-pipeline/)

## Resources

- [Cursor Documentation](https://cursor.sh/docs)
- [Cursor Rules Guide](https://cursor.sh/docs/cursorrules)
- [Skill Seekers Documentation](https://github.com/yusufkaraaslan/Skill_Seekers)
- [React Documentation](https://react.dev/)
