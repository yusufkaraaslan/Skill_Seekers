# /check-hook: Comprehensive Hook Validation System

Validates Claude Code hook configuration, syntax, and functionality with detailed diagnostics.

## Usage

```bash
/check-hook [options]
```

**Options**:
- `--fix`: Automatically attempt to fix common issues
- `--test`: Test each hook with sample data
- `--verbose`: Show detailed validation output
- `--hooks <type>`: Check specific hook types (SessionStart, PreToolUse, PostToolUse)

## Validation Checks

### 1. Configuration Validation
- ✅ JSON syntax verification
- ✅ Hook structure validation
- ✅ Command path resolution
- ✅ Environment variable expansion

### 2. Script Accessibility
- ✅ Executable permissions
- ✅ Python virtual environment health
- ✅ Script dependency validation
- ✅ Path resolution accuracy

### 3. Functional Testing
- ✅ Hook script execution with sample input
- ✅ Error handling validation
- ✅ Performance impact assessment
- ✅ Integration with Claude Code tools

### 4. Common Issues Detection
- 🔍 Quote escaping problems
- 🔍 Environment variable failures
- 🔍 Missing executable permissions
- 🔍 Python virtual environment issues
- 🔍 Malformed JSON structures

## Automated Fixes

When `--fix` is specified, the command automatically:

1. **Quote Issues**: Replace problematic environment variable syntax with absolute paths
2. **Permissions**: Fix executable permissions on hook scripts
3. **Python Environment**: Rebuild broken virtual environments
4. **JSON Structure**: Correct malformed JSON syntax
5. **Path Resolution**: Update broken file references

## Hook Categories Checked

### SessionStart Hooks
- Agent registry loading
- Environment initialization
- Context injection

### PreToolUse Hooks
- File operation pre-validation
- Syntax checking
- Security pre-scans

### PostToolUse Hooks
- Registry updates
- File validation
- Change logging

## Error Categories

### Critical (❌)
- Hook cannot execute
- JSON syntax errors
- Missing executable permissions
- Broken Python environments

### Warning (⚠️)
- Performance concerns
- Potential quote issues
- Missing error handling
- Deprecated patterns

### Info (ℹ️)
- Optimization suggestions
- Configuration improvements
- Best practices recommendations

## Integration Testing

The `--test` flag runs comprehensive integration tests:

```bash
# Quick validation
/check-hook

# Full validation with fixes and testing
/check-hook --fix --test --verbose

# Test specific hook type
/check-hook --hooks PreToolUse --test
```

## Troubleshooting

Common issues detected and resolved:

1. **"unexpected EOF while looking for matching '"'"**
   - Cause: Quote escaping in JSON hook commands
   - Fix: Use absolute paths instead of environment variables

2. **"permission denied"**
   - Cause: Non-executable hook scripts
   - Fix: `chmod +x` on hook scripts

3. **"No such file or directory"**
   - Cause: Broken path references
   - Fix: Update paths to use absolute locations

4. **"Invalid JSON input"**
   - Cause: Hook script expects JSON but receives none
   - Fix: Ensure proper JSON input structure

## Hook Health Scoring

After validation, provides a comprehensive health score:

- 🟢 **Excellent (95-100%)**: All hooks optimal
- 🟡 **Good (80-94%)**: Minor issues detected
- 🟠 **Fair (60-79%)**: Some issues need attention
- 🔴 **Poor (0-59%)**: Critical issues require immediate fixes

## Report Format

```
🔍 Hook Validation Report
========================

Configuration: ✅ Valid JSON syntax
Paths: ✅ All executable paths resolved
Permissions: ✅ All scripts have execute permissions
Environment: ✅ Python virtual environment healthy

SessionStart: ✅ 1/1 hooks working
PreToolUse: ✅ 1/1 hooks working
PostToolUse: ✅ 2/2 hooks working

Overall Health: 🟢 Excellent (98%)
⏱️  Total validation time: 2.3s

💡 Suggestions:
- Consider adding timeout to long-running hooks
- Monitor hook performance impact on file operations
```