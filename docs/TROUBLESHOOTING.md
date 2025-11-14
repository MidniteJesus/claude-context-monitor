# Troubleshooting Guide

Common issues and solutions for Claude Context Monitor.

## Table of Contents

- [Hook Not Triggering](#hook-not-triggering)
- [Notifications Not Showing](#notifications-not-showing)
- [Configuration Not Loading](#configuration-not-loading)
- [File Not Being Updated](#file-not-being-updated)
- [Python Errors](#python-errors)
- [Performance Issues](#performance-issues)

## Hook Not Triggering

### Symptom
No log entries appear, monitor never runs.

### Solutions

**1. Verify hook is registered**
```bash
# In Claude Code CLI
/hooks
```

You should see a `Stop` hook listed. If not, check your `.claude/settings.json`.

**2. Check Python path**
```bash
which python3
```

If Python is not at `/usr/bin/python3`, update the hook command in settings:
```json
{
  "command": "/path/to/python3 \"${CLAUDE_PROJECT_DIR}/scripts/context-monitor.py\""
}
```

**3. Verify script exists and is executable**
```bash
ls -la scripts/context-monitor.py
# Should show: -rwxr-xr-x

chmod +x scripts/context-monitor.py  # If not executable
```

**4. Check for syntax errors**
```bash
python3 scripts/context-monitor.py --help 2>&1
```

Should not show any Python errors.

**5. Test hook manually**
```bash
echo '{"session_id":"test","transcript_path":"~/.claude/projects/*/latest.jsonl","cwd":"'$(pwd)'"}' | python3 scripts/context-monitor.py
```

Check the log file for output.

## Notifications Not Showing

### Symptom
Monitor runs but no desktop notification appears.

### Platform-Specific Solutions

#### Windows / WSL

**Check PowerShell path:**
```bash
ls /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
```

If not found, update `notifier.py` with your PowerShell path.

**Test notification manually:**
```bash
python3 scripts/notifier.py "Test Title" "Test Message"
```

**Windows notification settings:**
- Open Windows Settings → System → Notifications
- Ensure "Get notifications from apps and other senders" is ON
- Check that Python/PowerShell notifications aren't blocked

#### macOS

**Grant terminal permissions:**
- System Preferences → Notifications & Focus
- Find Terminal (or your terminal app)
- Enable "Allow Notifications"

**Test notification:**
```bash
osascript -e 'display notification "Test message" with title "Test title"'
```

#### Linux

**Install notify-send:**
```bash
# Ubuntu/Debian
sudo apt install libnotify-bin

# Fedora
sudo dnf install libnotify

# Arch
sudo pacman -S libnotify
```

**Test notification:**
```bash
notify-send "Test Title" "Test Message"
```

**Check DBUS:**
```bash
echo $DBUS_SESSION_BUS_ADDRESS
```

Should output a path. If empty, notifications won't work in your session.

### General Solutions

**Disable and check logs:**

Set in `config.json`:
```json
{
  "notification_enabled": false
}
```

Then check if everything else works. Re-enable once other issues are resolved.

## Configuration Not Loading

### Symptom
Monitor uses default settings, ignoring your config.

### Solutions

**1. Check config file location**

The monitor searches in this order:
1. `./config.json` (current directory)
2. Script directory
3. `~/.claude/context-monitor-config.json`

Verify your config is in one of these locations.

**2. Validate JSON syntax**
```bash
python3 -m json.tool config.json
```

Should print the formatted JSON. If error, fix the syntax.

**3. Check which config is loaded**
```bash
grep "Loaded configuration" ~/.claude/context-monitor.log
```

Shows which config file was used.

**4. Check file permissions**
```bash
chmod 644 config.json
```

Ensure the file is readable.

**5. Verify config structure**

Required fields:
```json
{
  "threshold": 0.80,
  "output_file": "claude.md"
}
```

Optional fields will use defaults if missing.

## File Not Being Updated

### Symptom
Threshold reached but output file not created/updated.

### Solutions

**1. Check current working directory**

The output file is created in the `cwd` from the hook input. Verify:
```bash
grep "Hook triggered" ~/.claude/context-monitor.log
```

Look for the `cwd` value.

**2. Check write permissions**
```bash
touch claude.md  # Try creating the file manually
```

If this fails, you don't have write permissions in the directory.

**3. Check if marker file exists**
```bash
ls -la .claude/.context-threshold-hit
```

If exists, remove it to allow the hook to trigger again:
```bash
rm .claude/.context-threshold-hit
```

**4. Verify threshold is being exceeded**
```bash
grep "Context usage" ~/.claude/context-monitor.log | tail -1
```

Check if percentage is actually above your threshold.

**5. Check for errors in log**
```bash
grep -i error ~/.claude/context-monitor.log
```

## Python Errors

### ImportError: No module named 'notifier'

**Cause:** Python can't find the notifier module.

**Solution:**
Ensure both scripts are in the same directory:
```bash
ls scripts/
# Should show: context-monitor.py  notifier.py
```

### JSON Decode Error

**Cause:** Invalid hook input or corrupted transcript.

**Solution:**
Check the transcript file exists and is valid JSON:
```bash
tail ~/.claude/projects/*/$(ls -t ~/.claude/projects/*/ | head -1)
python3 -m json.tool < [transcript-file]
```

### Permission Denied

**Cause:** Script not executable or file not writable.

**Solution:**
```bash
chmod +x scripts/*.py
chmod 755 scripts/
```

## Performance Issues

### Hook Takes Too Long

**Symptom:** Claude Code becomes slow, hook times out.

**Solutions:**

**1. Increase timeout**

In `.claude/settings.json`:
```json
{
  "timeout": 30
}
```

**2. Disable logging temporarily**

In `config.json`:
```json
{
  "log_enabled": false
}
```

**3. Check transcript file size**
```bash
ls -lh ~/.claude/projects/*/*.jsonl
```

Very large files (>100MB) might cause slowness.

### High CPU Usage

**Cause:** Hook running too frequently or taking too long.

**Solution:**

Consider using a different hook event. Instead of `Stop` (runs after every response), use `PreCompact` (runs only before compaction):

```json
{
  "hooks": {
    "PreCompact": [...]
  }
}
```

## Getting Help

If these solutions don't resolve your issue:

1. **Check the log file:**
```bash
tail -100 ~/.claude/context-monitor.log
```

2. **Enable verbose logging:**

Edit `context-monitor.py` and add debug prints, or temporarily add:
```python
import traceback
traceback.print_exc()
```

3. **Open an issue:**

Visit: https://github.com/MidniteJesus/claude-context-monitor/issues

Include:
- Operating system and version
- Python version (`python3 --version`)
- Claude Code version
- Relevant log entries
- Your configuration (remove any sensitive data)

## See Also

- [Configuration Guide](./CONFIGURATION.md)
- [Main README](../README.md)
