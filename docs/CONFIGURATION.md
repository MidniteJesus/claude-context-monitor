# Configuration Guide

Complete guide to configuring Claude Context Monitor.

## Configuration File Locations

The monitor searches for configuration in this order:

1. **Project directory**: `./config.json`
2. **Script directory**: `claude-context-monitor/config.json`
3. **Home directory**: `~/.claude/context-monitor-config.json`

The first config file found is used.

## Complete Configuration Reference

```json
{
  "threshold": 0.80,
  "output_file": "claude.md",
  "instructions": "Update with current progress, successes, failures, and handoff notes",
  "notification_enabled": true,
  "max_context_tokens": 200000,
  "log_enabled": true,
  "log_file": "~/.claude/context-monitor.log"
}
```

### `threshold`

**Type:** `float` (0.0 to 1.0)
**Default:** `0.80`
**Description:** Percentage of context usage that triggers the alert.

**Examples:**
- `0.75` - Alert at 75% (150,000 tokens for Sonnet 4.5)
- `0.80` - Alert at 80% (160,000 tokens)
- `0.90` - Alert at 90% (180,000 tokens)
- `0.95` - Alert at 95% (just before auto-compact)

**Recommendation:** Start with 0.80. If you find yourself needing more time to wrap up, lower it to 0.75.

### `output_file`

**Type:** `string`
**Default:** `"claude.md"`
**Description:** Name of the file to update when threshold is reached.

**Examples:**
- `"claude.md"` - Standard name
- `"CONTEXT.md"` - Alternative name
- `"session-notes.md"` - Custom name
- `".claude-progress.md"` - Hidden file

**Notes:**
- File is created if it doesn't exist
- File is always in the project root directory
- Updates are appended (never overwrites existing content)

### `instructions`

**Type:** `string`
**Default:** `"Update with current progress, successes, failures, and handoff notes"`
**Description:** Custom instructions written to the output file explaining what should be documented.

**Examples:**

**For feature development:**
```json
{
  "instructions": "Document: 1) What feature is being implemented, 2) Current status, 3) Remaining work, 4) Any blockers or issues"
}
```

**For bug fixing:**
```json
{
  "instructions": "Document: 1) Bug description, 2) Root cause identified, 3) Fix attempted, 4) Test results, 5) Next debugging steps"
}
```

**For refactoring:**
```json
{
  "instructions": "Document: 1) Files refactored, 2) Patterns changed, 3) Tests updated, 4) Remaining files to refactor"
}
```

### `notification_enabled`

**Type:** `boolean`
**Default:** `true`
**Description:** Enable or disable desktop notifications.

**When to disable:**
- Running on headless server
- Notifications are distracting
- Using in automated environment

**When to enable:**
- Interactive development
- Want immediate alerts
- Running locally

### `max_context_tokens`

**Type:** `integer`
**Default:** `200000`
**Description:** Maximum context window size in tokens.

**Model-specific values:**
- Claude Sonnet 4.5: `200000`
- Claude Sonnet 4 (extended): `1000000`
- Claude Opus 3.5: `200000`

**Note:** This should match the model you're using with Claude Code.

### `log_enabled`

**Type:** `boolean`
**Default:** `true`
**Description:** Enable or disable activity logging.

**Log includes:**
- Hook trigger events
- Context usage calculations
- File updates
- Notification attempts
- Errors and warnings

**When to disable:**
- Don't want log file
- Disk space concerns
- Privacy concerns

### `log_file`

**Type:** `string`
**Default:** `"~/.claude/context-monitor.log"`
**Description:** Path to the log file.

**Examples:**
- `"~/.claude/context-monitor.log"` - Default location
- `"/var/log/claude-monitor.log"` - System log directory
- `"./monitor.log"` - Project-local log
- `"/dev/null"` - Effectively disables logging

## Hook Configuration

### Project-Specific Hook

Add to `.claude/settings.json` in your project:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PROJECT_DIR}/scripts/context-monitor.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**Environment Variables Available:**
- `${CLAUDE_PROJECT_DIR}` - Project root directory
- `${CLAUDE_PLUGIN_ROOT}` - Plugin directory (if installed as plugin)

### Global Hook

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/context-monitor.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Hook Options

**`timeout`**
Maximum seconds the hook can run before being killed. Default is 60 seconds.
- Set to `10` for quick execution
- Increase if script needs more time (e.g., on slow systems)

**`type`**
Always `"command"` for shell commands.

## Advanced Configuration

### Multiple Thresholds

Want alerts at multiple percentages? Create multiple config files and run the hook multiple times with different configs (advanced users only).

### Conditional Configuration

Use different configs based on project type by symlinking `config.json` to different files:

```bash
# For feature development
ln -s config.feature.json config.json

# For bug fixing
ln -s config.bugfix.json config.json
```

### Per-Project Customization

Each project can have its own `config.json` with custom settings. Global config in `~/.claude/` serves as fallback.

## Testing Your Configuration

### Test notification system:
```bash
python scripts/notifier.py "Test" "Notification working!"
```

### Test monitor with mock input:
```bash
echo '{"session_id":"test","transcript_path":"'$(ls -t ~/.claude/projects/*/$(ls -t ~/.claude/projects/*/ | head -1) | head -1)'","cwd":"'$(pwd)'"}' | python scripts/context-monitor.py
```

### Check logs:
```bash
tail -f ~/.claude/context-monitor.log
```

### Verify hook is loaded:
In Claude Code, type `/hooks` and verify the Stop hook is listed.

## Common Configuration Patterns

### Aggressive Monitoring (Alert Early)
```json
{
  "threshold": 0.70,
  "notification_enabled": true
}
```

### Conservative Monitoring (Alert Late)
```json
{
  "threshold": 0.95,
  "notification_enabled": true
}
```

### Silent Mode (No Notifications)
```json
{
  "notification_enabled": false,
  "log_enabled": true
}
```

### Detailed Logging
```json
{
  "log_enabled": true,
  "log_file": "./detailed-monitor.log"
}
```

## Troubleshooting Configuration

### Config not loading?

Check which config is being used:
```bash
grep "Loaded configuration" ~/.claude/context-monitor.log
```

### Invalid JSON?

Validate your config:
```bash
python3 -m json.tool config.json
```

### Permissions issues?

Ensure files are readable:
```bash
chmod 644 config.json
chmod 755 scripts/*.py
```

## See Also

- [Main README](../README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
