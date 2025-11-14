# Claude Context Monitor

**Never lose context again!** Automatically monitor Claude Code's context window usage in real-time with a beautiful GUI and smart background monitoring.

This tool helps you work more efficiently with Claude Code CLI by keeping track of your context window usage and alerting you when it's time to clear and start fresh. Perfect for long coding sessions where context management is critical.

## ✨ Features

### Background Hook (Always Active)
- 🎯 **Smart threshold detection** - Get notified when context reaches your limit (default 80%)
- 📝 **Automatic session notes** - Updates your handoff file (`claude.md`) with current progress
- 🔔 **Cross-platform notifications** - Desktop alerts on Windows, WSL, macOS, and Linux
- 🚀 **Zero maintenance** - Runs automatically after every Claude response
- 📊 **Activity logging** - Track context usage history

### Modern GUI (Optional)
- 🖥️ **Real-time visual display** - See your context usage at a glance
- 🎨 **Beautiful dark/light themes** - Matches your system preferences
- 📊 **Color-coded progress** - Green → Yellow → Orange → Red as you approach the limit
- ⚙️ **Easy settings panel** - Configure everything without editing JSON files
- 🔄 **Live updates** - Instantly reflects changes as you work with Claude
- 💾 **Persistent preferences** - Your settings are remembered between sessions

## 🎬 How It Works

### Background Hook
The monitoring hook runs automatically after every Claude Code response:
1. ✅ Silently tracks your context usage in the background
2. ✅ When you hit your threshold (default 80%), it creates/updates your handoff file
3. ✅ Sends you a desktop notification so you know it's time to `/clear`
4. ✅ You start fresh with full context, using the handoff notes to continue seamlessly

### GUI Monitor (Optional)
Want to see your context usage in real-time?
```bash
cd ~/claude-context-monitor/scripts
python3 context-monitor-gui.py
```
- Watch your context fill up with a live progress bar
- Change settings on-the-fly with the built-in settings panel
- Switch between dark and light themes instantly
- No need to edit config files manually!

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

## 🖥️ GUI Mode (Optional)

For real-time visual monitoring, you can run the optional modern GUI with a sleek dark-mode interface:

### Installation

```bash
# Install GUI dependencies (CustomTkinter + watchdog)
pip install -r requirements-gui.txt

# Run the GUI
python scripts/context-monitor-gui.py
```

### Features

- **Modern dark-mode interface** - Sleek, professional CustomTkinter design
- **Built-in Settings Window** - Configure everything from the GUI (no JSON editing!)
- **Real-time updates** - Updates automatically as you work with Claude Code
- **Cross-platform consistency** - Looks identical on Windows, macOS, and Linux
- **Always-on-top** - Window stays visible above other applications
- **Color-coded display** - Green → Yellow → Orange → Red as context fills
- **Smooth animations** - Polished progress bar with dynamic color changes
- **Large, readable text** - Easy-to-read percentage and token counts
- **Token breakdown** - See exact token counts
- **Live theme switching** - Change themes and colors instantly
- **Customizable thresholds** - Adjust alert percentage with a slider

### GUI Configuration

Click the **⚙️ Settings** button in the GUI to configure:

**Display Settings:**
- Theme (Dark/Light/System)
- Color Scheme (Blue/Green/Dark-blue)
- Always-on-top toggle
- Window size presets

**Monitoring Settings:**
- Alert threshold slider (50-100%)
- Update interval
- Notification toggle

**Output Settings:**
- Output filename
- Custom instructions

All changes are saved automatically to your `config.json`!

### WSL Users

The GUI works great with WSLg (Windows 11):

```bash
# Ensure WSLg is up to date
wsl --update

# Run the GUI
python scripts/context-monitor-gui.py
```

The window will appear natively in Windows!

For more details, see [GUI Documentation](docs/GUI.md).

---

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
