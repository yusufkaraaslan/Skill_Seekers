# Agent Scaffolding Toolkit - Test Suite

Comprehensive test suite for the agent scaffolding toolkit with 95% coverage target.

## Test Structure

```
.claude/tests/
├── conftest.py              # Shared fixtures and configuration
├── requirements.txt         # Test dependencies (pytest, PyYAML)
├── fixtures/
│   └── sample_agents.py     # Sample agent YAML for testing
├── unit/
│   ├── test_validate_agent.py       # Validation logic tests
│   ├── test_yaml_parser.py          # YAML parsing tests
│   └── test_registry_management.py  # Registry operations tests
├── integration/
│   ├── test_agent_lifecycle.py      # Complete lifecycle tests
│   └── test_agent_composition.py    # Delegation and composition tests
└── e2e/
    └── test_full_agent_lifecycle.py # End-to-end workflow tests
```

## Running Tests

### Setup

```bash
# From .claude/tests directory
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest unit/ -v

# Integration tests
pytest integration/ -v

# End-to-end tests
pytest e2e/ -v
```

### Run with Coverage

```bash
pytest --cov=../ --cov-report=html --cov-report=term
```

## Test Categories

### Unit Tests (8 tests)

**test_validate_agent.py:**
- ✅ Valid agent passes validation
- ✅ Invalid agent fails validation
- ✅ Missing YAML frontmatter fails
- ✅ Non-existent tool fails validation
- ✅ Security pattern detection
- ✅ Short description fails validation
- ✅ Delegation cycle detection

**test_yaml_parser.py:**
- ✅ Parse valid YAML frontmatter
- ✅ Parse invalid YAML raises error
- ✅ Missing frontmatter returns None
- ✅ Malformed YAML raises error
- ✅ Parse complex YAML structures

**test_registry_management.py:**
- ✅ Registry creation
- ✅ Add agent to registry
- ✅ Update existing agent in registry
- ✅ Registry preserves usage stats
- ✅ Delegation tracking in registry

### Integration Tests (8 tests)

**test_agent_lifecycle.py:**
- ✅ Agent creation and registration
- ✅ Agent modification increments version
- ✅ Agent deletion removes from registry
- ✅ Load registry on session start
- ✅ Validation blocks invalid agent
- ✅ Check agent behavior hook
- ✅ Delegation chain discovery

**test_agent_composition.py:**
- ✅ Simple delegation
- ✅ Multi-agent delegation
- ✅ Delegation chain depth
- ✅ Tool aggregation through delegation

### E2E Tests (4 tests)

**test_full_agent_lifecycle.py:**
- ✅ Complete agent creation workflow (create → validate → register)
- ✅ Agent modification workflow
- ✅ Multi-agent delegation workflow
- ✅ Session start load all agents

## Coverage Goals

| Component | Target | Description |
|-----------|--------|-------------|
| validate-agent.py | 95% | YAML validation, field checking, security patterns |
| update-registry.py | 90% | Registry updates, version management |
| load-agent-registry.py | 85% | Registry loading, agent discovery |
| check-agent-behavior.py | 80% | Behavior validation, tool checking |

**Overall Target:** 95% code coverage across all hook scripts.

## Test Fixtures

### Shared Fixtures (conftest.py)

- `temp_project_dir`: Temporary .claude structure
- `sample_agent_yaml`: Valid agent YAML
- `invalid_agent_yaml`: Invalid agent YAML
- `agent_registry`: Sample registry data
- `mock_claude_project_dir`: Mocked environment
- `create_agent_file`: Factory for creating agents
- `create_registry_file`: Factory for creating registry

### Sample Agents (fixtures/sample_agents.py)

- `VALID_MINIMAL_AGENT`: Minimal valid agent
- `VALID_DELEGATING_AGENT`: Agent with delegation
- `INVALID_MISSING_FIELDS`: Missing required fields
- `INVALID_SHORT_DESCRIPTION`: Too-short description
- `INVALID_BAD_TOOL`: Non-existent tool
- `SECURITY_RISK_AGENT`: Security anti-patterns
- `SAMPLE_REGISTRY`: Sample registry structure

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Agent Scaffolding

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd .claude/tests
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd .claude/tests
          pytest --cov=../ --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hook Integration

Already configured in `.claude/scripts/git-pre-commit-hook` to validate agents before commits.

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pytest'`

**Solution:**
```bash
cd .claude/tests
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variable Issues

**Problem:** `CLAUDE_PROJECT_DIR not set`

**Solution:** Tests automatically mock this via `conftest.py` fixtures. No manual setup needed.

### Hook Script Not Found

**Problem:** `FileNotFoundError: validate-agent.py not found`

**Solution:** Tests reference scripts at `../.claude/scripts/`. Ensure hook scripts exist.

### PyYAML Not Found

**Problem:** `ModuleNotFoundError: No module named 'yaml'`

**Solution:** Install in skill's venv:
```bash
cd .claude/skills/agent-scaffolding-toolkit
source .venv/bin/activate
pip install -r requirements.txt
```

## Test Development Guidelines

### Adding New Tests

1. **Choose appropriate category:** unit, integration, or e2e
2. **Use existing fixtures** from `conftest.py`
3. **Follow naming convention:** `test_<feature>_<scenario>()`
4. **Include docstring** explaining test purpose
5. **Assert specific outcomes** with clear messages

### Test Isolation

- Each test uses `temp_project_dir` for isolation
- No shared state between tests
- Registry files created fresh per test
- Environment variables mocked via fixtures

### Performance Considerations

- Unit tests: < 0.1s each
- Integration tests: < 1s each
- E2E tests: < 5s each
- Total suite: < 30s

## Next Steps

After test suite completion:
1. ✅ Run full test suite: `pytest -v`
2. ✅ Check coverage: `pytest --cov=../ --cov-report=html`
3. ✅ Review coverage report: `open htmlcov/index.html`
4. 🔄 Add missing tests to reach 95% coverage
5. 🔄 Integrate with CI/CD pipeline
