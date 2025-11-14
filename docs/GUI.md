# GUI Documentation

Complete guide to using the Claude Context Monitor GUI.

## Overview

The GUI provides real-time visual monitoring of Claude Code context usage with:
- **Modern, dark-mode interface** (CustomTkinter framework)
- Color-coded progress bar with smooth animations
- Live token counts
- Large, easy-to-read percentage display
- Always-on-top window option
- Cross-platform consistent appearance

## Installation

### Prerequisites

- Python 3.8+
- CustomTkinter (modern GUI framework)
- watchdog library (for real-time updates)

### Setup

```bash
# Install all GUI dependencies
pip install -r requirements-gui.txt

# Or install individually
pip install customtkinter watchdog
```

## Running the GUI

### Basic Usage

```bash
# From the repository directory
python scripts/context-monitor-gui.py
```

The GUI will:
1. Find the most recent Claude Code session
2. Parse the transcript file
3. Display current context usage
4. Update automatically when you interact with Claude

### With Custom Config

```bash
python scripts/context-monitor-gui.py --config /path/to/config.json
```

## Features

### Real-Time Updates

The GUI monitors your Claude Code transcript file and updates instantly when:
- You send a message to Claude
- Claude responds
- Context usage changes

**Update Methods:**
- **With watchdog** (recommended): Instant updates using file system events
- **Without watchdog** (fallback): Polls every 2 seconds (configurable)

### Color Coding

The display changes color based on usage:

| Usage Range | Color | Status |
|-------------|-------|--------|
| 0-70% | 🟢 Green | Normal |
| 70-85% | 🟡 Yellow | Moderate |
| 85-95% | 🟠 Orange | High |
| 95-100% | 🔴 Red | Critical |

### Always-On-Top

The window stays visible above other applications by default, so you can monitor context while working.

To disable: Set `"always_on_top": false` in your config.

## Configuration

### Using the Built-in Settings Window

The easiest way to configure the GUI is using the **⚙️ Settings** button in the main window.

**To open settings:**
1. Click the **⚙️ Settings** button at the bottom of the main window
2. Adjust settings in the Settings window
3. Click **Save** to apply and save to config file
4. Or click **Reset to Defaults** to restore default settings

**Available Settings:**

**Display Settings:**
- **Theme** - Dark, Light, or System (follows OS theme)
- **Color Scheme** - Blue, Green, or Dark-blue
- **Always on top** - Toggle whether window stays above others
- **Window Size** - Small (400x250), Medium (450x300), or Large (500x350)

**Monitoring Settings:**
- **Alert Threshold** - Slider from 50% to 100% (default: 80%)
- **Update Interval** - How often to check for updates in seconds (default: 2)
- **Enable notifications** - Toggle desktop notifications

**Output Settings:**
- **Output File** - Filename for context notes (default: claude.md)
- **Custom Instructions** - What to include in auto-generated notes

All changes are saved to your `config.json` and most apply immediately!

### Manual Configuration (Optional)

You can also edit `config.json` directly if preferred. The GUI uses the same config as the hook system:

```json
{
  "window_width": 450,
  "window_height": 300,
  "always_on_top": true,
  "update_interval": 2,
  "threshold": 0.80,
  "appearance_mode": "dark",
  "color_theme": "blue",
  "notification_enabled": true,
  "output_file": "claude.md",
  "instructions": "Update with current progress, successes, failures, and handoff notes"
}
```

## Platform-Specific Notes

### Windows / WSL

**Windows 11 (WSLg):**
- Works out of the box
- Run `wsl --update` to ensure WSLg is current
- GUI window appears natively in Windows
- Fully integrated with Windows UI

**Windows 10 (X Server required):**
1. Install VcXsrv or Xming on Windows
2. Start X Server with "Disable access control"
3. In WSL: `export DISPLAY=:0`
4. Run the GUI

**Native Windows:**
The Python script works directly on Windows:
```cmd
python scripts\context-monitor-gui.py
```

### macOS

Works natively with tkinter:
```bash
python3 scripts/context-monitor-gui.py
```

**Note:** You may need to grant Terminal.app notification permissions for full functionality.

### Linux

Works with any desktop environment:
```bash
python3 scripts/context-monitor-gui.py
```

Requires X11 or Wayland display server (standard on all desktop Linux installations).

## Usage Patterns

### Pattern 1: Side Monitor

Run the GUI on a second monitor or half of your screen while using Claude Code on the other half.

### Pattern 2: Always Visible

Use the always-on-top feature to keep the monitor visible in the corner of your screen while working.

### Pattern 3: On-Demand

Launch the GUI only when you want to check context usage, close when done.

## Troubleshooting

### GUI Won't Start

**CustomTkinter not found:**
```bash
# Install CustomTkinter
pip install customtkinter

# Or use the requirements file
pip install -r requirements-gui.txt
```

**tkinter not found (backend dependency):**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (via Homebrew)
brew install python-tk

# Windows
# tkinter is included with Python installer - make sure you checked "tcl/tk" option
```

**No display available (WSL):**
```bash
# Check if DISPLAY is set
echo $DISPLAY

# If empty, set it
export DISPLAY=:0

# For permanent fix, add to ~/.bashrc
echo 'export DISPLAY=:0' >> ~/.bashrc
```

### GUI Not Updating

**watchdog not installed:**
- Install with: `pip install watchdog`
- GUI will work in polling mode without it, but updates every 2 seconds instead of real-time

**No active session found:**
- Start Claude Code first
- Ensure you have an active conversation
- Check that `~/.claude/projects/` exists

**Transcript not found:**
- The GUI looks for the most recent non-agent transcript
- Ensure Claude Code is creating transcript files
- Check permissions on `~/.claude/` directory

### Window Not Staying On Top

**Linux (X11):**
Some window managers don't support always-on-top. Try:
```bash
# Using wmctrl
wmctrl -r "Claude Context Monitor" -b add,above
```

**Alternative:**
Set `"always_on_top": false` and manually pin the window using your desktop environment's options.

### Performance Issues

**High CPU usage:**
- Install watchdog to avoid polling
- Increase `update_interval` in config

**Slow updates:**
- Ensure watchdog is installed
- Check that transcript file is accessible
- Verify file permissions

## Advanced Usage

### Multiple Sessions

The GUI automatically tracks the most recently active session. If you switch between projects, restart the GUI to track the new session.

### Custom Styling

The GUI uses CustomTkinter with a modern dark theme. You can customize:

**Appearance Mode:**
Edit line 67 in `context-monitor-gui.py`:
```python
ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
```

**Color Theme:**
Edit line 68 in `context-monitor-gui.py`:
```python
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
```

For advanced customization, edit the `_build_ui()` method to change fonts, colors, and layout.

### Headless Mode

The GUI requires a display. For headless servers, use the hook-only installation instead.

## Integration with Hook

The GUI and hook work independently:

**Hook (background):**
- Monitors context
- Triggers at threshold
- Updates output file
- Sends notification

**GUI (foreground):**
- Visual real-time display
- No threshold checking
- No file updates
- Just monitoring

You can run both simultaneously for complete coverage:
- GUI for visual feedback during work
- Hook for automated alerting and file updates

## Keyboard Shortcuts

- **Close window:** Standard OS close (Alt+F4 / Cmd+W / etc.)
- **Minimize:** Standard OS minimize

No custom shortcuts currently (could be added if desired).

## FAQ

**Q: Does the GUI replace the hook?**
A: No, they're complementary. The hook handles automated alerts, the GUI provides visual monitoring.

**Q: Can I resize the window?**
A: The window is fixed-size to prevent WSLg window manager issues. You can customize the size by setting `window_width` and `window_height` in your `config.json`.

**Q: Does it work with multiple Claude Code instances?**
A: It tracks the most recently active session. For multiple instances, consider running multiple GUI instances with different configs.

**Q: How much resources does it use?**
A: Very light:
- RAM: ~10-20 MB
- CPU: <1% (with watchdog), ~1-2% (polling mode)

**Q: Can I minimize to system tray?**
A: Not currently. This feature would require PySide6 (larger dependency). Could be added in future version if desired.

## See Also

- [Main README](../README.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
