#!/bin/bash
# Installation script for Claude Context Monitor

set -e

echo "🚀 Claude Context Monitor - Installation"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we're in a project directory or installing globally
if [ -f ".claude/settings.json" ] || [ -f ".claude/settings.local.json" ]; then
    INSTALL_TYPE="project"
    echo "📁 Detected Claude Code project directory"
else
    echo "📁 No Claude Code project detected in current directory"
    echo ""
    echo "Choose installation type:"
    echo "  1) Project-specific (install in current directory)"
    echo "  2) Global (install in ~/.claude/)"
    read -p "Enter choice [1-2]: " choice

    case $choice in
        1) INSTALL_TYPE="project" ;;
        2) INSTALL_TYPE="global" ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
fi

echo ""
echo "Installation type: $INSTALL_TYPE"
echo ""

# Copy scripts
if [ "$INSTALL_TYPE" = "project" ]; then
    echo "📦 Installing to current project..."

    # Create directories
    mkdir -p scripts
    mkdir -p .claude

    # Copy scripts
    cp "$SCRIPT_DIR/scripts/context-monitor.py" scripts/
    cp "$SCRIPT_DIR/scripts/notifier.py" scripts/
    chmod +x scripts/context-monitor.py scripts/notifier.py

    # Copy config if it doesn't exist
    if [ ! -f "config.json" ]; then
        cp "$SCRIPT_DIR/config.json.example" config.json
        echo "✓ Created config.json (customize as needed)"
    else
        echo "✓ config.json already exists (skipping)"
    fi

    # Update or create .claude/settings.json
    if [ -f ".claude/settings.json" ]; then
        echo "⚠️  .claude/settings.json already exists"
        echo "You'll need to manually add the hook configuration:"
        echo ""
        cat "$SCRIPT_DIR/.claude/settings.json.example"
        echo ""
    else
        cp "$SCRIPT_DIR/.claude/settings.json.example" .claude/settings.json
        echo "✓ Created .claude/settings.json with hook configuration"
    fi

    echo ""
    echo "✅ Project installation complete!"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Review and customize config.json"
    echo "  2. If you already had .claude/settings.json, merge the hook configuration"
    echo "  3. Start Claude Code and the monitor will run automatically"

else
    echo "📦 Installing globally to ~/.claude/..."

    # Create directories
    mkdir -p ~/.claude/hooks
    mkdir -p ~/.claude

    # Copy scripts
    cp "$SCRIPT_DIR/scripts/context-monitor.py" ~/.claude/hooks/
    cp "$SCRIPT_DIR/scripts/notifier.py" ~/.claude/hooks/
    chmod +x ~/.claude/hooks/context-monitor.py ~/.claude/hooks/notifier.py

    # Copy config if it doesn't exist
    if [ ! -f ~/.claude/context-monitor-config.json ]; then
        cp "$SCRIPT_DIR/config.json.example" ~/.claude/context-monitor-config.json
        echo "✓ Created ~/.claude/context-monitor-config.json"
    else
        echo "✓ config already exists at ~/.claude/context-monitor-config.json"
    fi

    # Update global settings
    SETTINGS_FILE=~/.claude/settings.json
    if [ -f "$SETTINGS_FILE" ]; then
        echo "⚠️  Global settings file exists: $SETTINGS_FILE"
        echo "You'll need to manually add the hook configuration:"
        echo ""
        echo '{
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
}'
        echo ""
    else
        echo '{
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
}' > "$SETTINGS_FILE"
        echo "✓ Created $SETTINGS_FILE with hook configuration"
    fi

    echo ""
    echo "✅ Global installation complete!"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Review and customize ~/.claude/context-monitor-config.json"
    echo "  2. If you already had settings.json, merge the hook configuration"
    echo "  3. The monitor will run automatically in all Claude Code sessions"
fi

echo ""
echo "📚 Documentation: https://github.com/MidniteJesus/claude-context-monitor"
echo "🐛 Issues: https://github.com/MidniteJesus/claude-context-monitor/issues"
echo ""
echo "Enjoy! 🎉"
