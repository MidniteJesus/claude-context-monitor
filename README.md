# Claude Context Monitor

**Automatically monitor Claude Code's context window usage and take action when your threshold is reached.**

Never lose context again! This tool monitors your Claude Code CLI sessions in real-time and automatically updates your session notes when the context window fills up, giving you seamless handoffs between sessions.

## ✨ Features

- 🎯 **Configurable threshold** - Trigger at 80%, 90%, or any percentage you choose
- 📝 **Custom output file** - Update `claude.md`, `CONTEXT.md`, or any file you specify
- 🔔 **Cross-platform notifications** - Auto-detects Windows/WSL/macOS/Linux
- ⚙️ **Fully customizable** - Configure instructions, filenames, and behavior via `config.json`
- 🚀 **Zero maintenance** - Runs automatically in the background
- 📊 **Activity logging** - Track context usage over time

## 🎬 Demo

<!-- TODO: Add screenshot or GIF of notification -->

When your context reaches the configured threshold (default 80%):
1. ✅ Your output file is automatically updated with progress notes
2. ✅ You receive a desktop notification
3. ✅ A marker is created to prevent duplicate alerts
4. ✅ You run `/clear` when ready and continue with full context

## 📋 Requirements

- **Python 3.8+**
- **Claude Code CLI 0.8.0+**
- **Operating System**: Windows 10/11, macOS, or Linux (including WSL)

## 🚀 Quick Start

### Installation

**Option 1: One-command install (recommended)**

```bash
git clone https://github.com/MidniteJesus/claude-context-monitor.git
cd claude-context-monitor
bash install.sh
```

The installer will ask if you want project-specific or global installation.

**Option 2: Manual installation**

1. Clone the repository:
```bash
git clone https://github.com/MidniteJesus/claude-context-monitor.git
```

2. For project-specific installation:
```bash
cd your-project-directory
cp -r claude-context-monitor/scripts ./
cp claude-context-monitor/config.json.example ./config.json
cp claude-context-monitor/.claude/settings.json.example ./.claude/settings.json
```

3. For global installation:
```bash
cp claude-context-monitor/scripts/* ~/.claude/hooks/
cp claude-context-monitor/config.json.example ~/.claude/context-monitor-config.json
```

Then add the hook to `~/.claude/settings.json` (see Configuration below).

### Verify Installation

Start Claude Code and the monitor will run automatically. Check the log:

```bash
cat ~/.claude/context-monitor.log
```

You should see entries like:
```
[2025-11-13 20:15:11] Hook triggered for session: abc123...
[2025-11-13 20:15:11] Context usage: 35228/200000 tokens (17.61%)
```

## ⚙️ Configuration

### Basic Configuration

Edit `config.json` in your project root (or `~/.claude/context-monitor-config.json` for global install):

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

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `threshold` | float | `0.80` | Trigger when context reaches this percentage (0.80 = 80%) |
| `output_file` | string | `"claude.md"` | File to update when threshold is reached |
| `instructions` | string | `"Update with..."` | Custom instructions written to the output file |
| `notification_enabled` | boolean | `true` | Enable/disable desktop notifications |
| `max_context_tokens` | integer | `200000` | Maximum context size (200K for Sonnet 4.5) |
| `log_enabled` | boolean | `true` | Enable/disable activity logging |
| `log_file` | string | `"~/.claude/..."` | Path to log file |

### Hook Configuration

The hook is configured in `.claude/settings.json`:

**Project-specific:**
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

**Global:**
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

## 📚 Usage Examples

### Example 1: Higher Threshold

Want to wait until 90% before alerting?

```json
{
  "threshold": 0.90
}
```

### Example 2: Custom Output File

Prefer a different filename?

```json
{
  "output_file": "CONTEXT.md"
}
```

### Example 3: Custom Instructions

Want specific information captured?

```json
{
  "instructions": "Document: 1) Current feature being implemented, 2) Blockers encountered, 3) Next steps for continuation"
}
```

### Example 4: Disable Notifications

Running on a headless server?

```json
{
  "notification_enabled": false
}
```

## 🔧 Troubleshooting

### Hook not triggering?

**Check if hook is registered:**
```bash
# In Claude Code
/hooks
```

You should see the `Stop` hook listed.

**Check Python path:**
```bash
which python3
```

If Python is in a non-standard location, update the `command` in `.claude/settings.json`.

### Notifications not showing?

**Windows/WSL:**
- Ensure PowerShell is accessible at `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`
- Check Windows notification settings aren't blocking notifications

**macOS:**
- Grant terminal notification permissions in System Preferences → Notifications

**Linux:**
- Install `notify-send`: `sudo apt install libnotify-bin` (Ubuntu/Debian)
- Or install `dbus-send` as fallback

**Test notifications manually:**
```bash
python scripts/notifier.py "Test Title" "Test Message"
```

### Config not loading?

The monitor searches for `config.json` in this order:
1. Current working directory
2. Script directory (next to context-monitor.py)
3. `~/.claude/context-monitor-config.json`

Check the log to see which config was loaded:
```bash
tail ~/.claude/context-monitor.log
```

### Marker file preventing alerts?

If you want to reset and trigger the alert again:

```bash
rm .claude/.context-threshold-hit
```

## 🎯 Use Cases

### Use Case 1: Long Development Sessions

Working on a complex feature that spans multiple Claude sessions? The monitor automatically captures your progress at the optimal time, ensuring smooth handoffs.

### Use Case 2: Team Collaboration

Share your project with teammates. When they work with Claude Code, they'll get the same automatic context management.

### Use Case 3: Learning & Tutorials

Following a long tutorial? Never lose your place when context fills up - the monitor keeps track for you.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with [Claude Code CLI](https://claude.com/claude-code) by Anthropic.

Special thanks to the Claude Code community for inspiration and feedback.

## 📞 Support

- 📖 [Documentation](https://github.com/MidniteJesus/claude-context-monitor/blob/main/docs/CONFIGURATION.md)
- 🐛 [Report a bug](https://github.com/MidniteJesus/claude-context-monitor/issues)
- 💡 [Request a feature](https://github.com/MidniteJesus/claude-context-monitor/issues)
- 💬 [Discussions](https://github.com/MidniteJesus/claude-context-monitor/discussions)

---

Made with ❤️ by [MidniteJesus](https://github.com/MidniteJesus)

**Star this repo** ⭐ if you find it helpful!
