#!/usr/bin/env python3
"""
Claude Code Context Monitor
Monitors context usage and automatically takes action when threshold is reached.

Configuration is loaded from config.json in the project root or script directory.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Import the notifier
sys.path.insert(0, os.path.dirname(__file__))
from notifier import Notifier


# Default configuration
DEFAULT_CONFIG = {
    "threshold": 0.80,
    "output_file": "claude.md",
    "instructions": "Update with current progress, successes, failures, and handoff notes for the next session",
    "notification_enabled": True,
    "max_context_tokens": 200000,
    "log_enabled": True,
    "log_file": "~/.claude/context-monitor.log"
}


class ContextMonitor:
    """Monitors Claude Code context usage and takes configured actions."""

    def __init__(self, config_path=None):
        """Initialize the monitor with configuration."""
        self.config = self._load_config(config_path)
        self.log_file = Path(self.config["log_file"]).expanduser()
        self.notifier = Notifier() if self.config["notification_enabled"] else None

    def _load_config(self, config_path=None):
        """Load configuration from config.json or use defaults."""
        config = DEFAULT_CONFIG.copy()

        # Try to find config.json
        search_paths = []

        if config_path:
            search_paths.append(Path(config_path))

        # Look in project directory (cwd)
        search_paths.append(Path.cwd() / "config.json")

        # Look next to this script
        script_dir = Path(__file__).parent.parent
        search_paths.append(script_dir / "config.json")

        # Look in home directory
        search_paths.append(Path.home() / ".claude" / "context-monitor-config.json")

        for path in search_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        user_config = json.load(f)
                        config.update(user_config)
                        self._log(f"Loaded configuration from {path}")
                        break
                except Exception as e:
                    self._log(f"Error loading config from {path}: {e}")

        return config

    def _log(self, message):
        """Log a message with timestamp."""
        if not self.config.get("log_enabled", True):
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log: {e}", file=sys.stderr)

    def parse_transcript(self, transcript_path):
        """Parse the transcript JSONL file and calculate context usage."""
        try:
            transcript_path = Path(transcript_path)
            if not transcript_path.exists():
                self._log(f"Transcript file not found: {transcript_path}")
                return None

            entries = []
            with open(transcript_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Filter for valid main chain entries with usage data
            valid_entries = [
                entry for entry in entries
                if entry.get('message', {}).get('usage') is not None
                and not entry.get('isSidechain', False)
                and not entry.get('isApiErrorMessage', False)
                and entry.get('timestamp')
            ]

            if not valid_entries:
                self._log("No valid entries with usage data found")
                return None

            # Get the most recent entry by timestamp
            latest_entry = max(valid_entries, key=lambda x: x.get('timestamp', 0))
            usage = latest_entry.get('message', {}).get('usage', {})

            # Calculate total input tokens
            input_tokens = usage.get('input_tokens', 0)
            cache_read_tokens = usage.get('cache_read_input_tokens', 0)
            cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)

            total_tokens = input_tokens + cache_read_tokens + cache_creation_tokens
            max_tokens = self.config["max_context_tokens"]
            percentage = (total_tokens / max_tokens) * 100

            self._log(f"Context usage: {total_tokens}/{max_tokens} tokens ({percentage:.2f}%)")

            return {
                'total_tokens': total_tokens,
                'percentage': percentage,
                'input_tokens': input_tokens,
                'cache_read_tokens': cache_read_tokens,
                'cache_creation_tokens': cache_creation_tokens
            }

        except Exception as e:
            self._log(f"Error parsing transcript: {e}")
            return None

    def update_output_file(self, cwd, session_id, usage_info):
        """Update the configured output file with context information."""
        output_filename = self.config["output_file"]
        output_path = Path(cwd) / output_filename

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        percentage = usage_info['percentage']
        total_tokens = usage_info['total_tokens']
        max_tokens = self.config["max_context_tokens"]
        threshold_percent = self.config["threshold"] * 100

        # Custom instructions from config
        instructions = self.config["instructions"]

        update_section = f"""

---

## Context Threshold Alert - {timestamp}

**Context Usage:** {percentage:.1f}% ({total_tokens:,}/{max_tokens:,} tokens)

**Status:** Context threshold reached at {threshold_percent:.0f}%. This session should be handed off soon.

**Instructions:** {instructions}

**Action Required:**
1. Review the progress documented in this file
2. Run `/clear` when ready to start a fresh session
3. This file will serve as the context for the next session

**Current Session Info:**
- Session ID: `{session_id}`
- Threshold configured: {threshold_percent:.0f}%
- Tokens used: {total_tokens:,} / {max_tokens:,}
- Output file: `{output_filename}`

**Next Steps:**
- Continue from where this session left off
- Refer to the sections above for context on completed work and pending tasks

---

"""

        try:
            # Check if file exists, if not create with header
            if not output_path.exists():
                with open(output_path, 'w') as f:
                    f.write(f"# Claude Code Session Notes\n\nSession started: {timestamp}\n")
                self._log(f"Created new {output_filename}")

            # Append the update section
            with open(output_path, 'a') as f:
                f.write(update_section)

            self._log(f"Updated {output_filename} with context alert")
            return True

        except Exception as e:
            self._log(f"Error updating {output_filename}: {e}")
            return False

    def check_and_notify(self, hook_input):
        """Main hook execution logic."""
        try:
            session_id = hook_input.get('session_id', 'unknown')
            transcript_path = hook_input.get('transcript_path')
            cwd = hook_input.get('cwd', os.getcwd())

            self._log(f"Hook triggered for session: {session_id}")

            if not transcript_path:
                self._log("No transcript path provided in hook input")
                return 0

            # Check if we've already triggered for this session
            marker_file = Path(cwd) / ".claude" / ".context-threshold-hit"
            if marker_file.exists():
                # Already triggered, skip
                return 0

            # Parse transcript and get context usage
            usage_info = self.parse_transcript(transcript_path)

            if usage_info is None:
                return 0

            # Check if threshold exceeded
            threshold = self.config["threshold"]
            if usage_info['percentage'] / 100 >= threshold:
                self._log(f"⚠️  Context threshold exceeded: {usage_info['percentage']:.1f}%")

                # Update output file
                if self.update_output_file(cwd, session_id, usage_info):
                    # Create marker file to prevent duplicate triggers
                    marker_file.parent.mkdir(parents=True, exist_ok=True)
                    marker_file.write_text(f"{datetime.now().isoformat()}\n")

                    # Send notification
                    if self.notifier:
                        threshold_percent = threshold * 100
                        notification_sent = self.notifier.send(
                            "Claude Code - Context Alert",
                            f"Context at {usage_info['percentage']:.1f}% (threshold: {threshold_percent:.0f}%)\n"
                            f"{self.config['output_file']} has been updated.\n"
                            f"Run /clear when ready."
                        )

                        if notification_sent:
                            self._log("✓ Successfully sent notification")
                        else:
                            self._log("⚠ Notification failed")

                    self._log(f"✓ Successfully updated {self.config['output_file']}")

            return 0

        except Exception as e:
            self._log(f"Unexpected error in hook: {e}")
            return 1


def main():
    """Entry point for the hook script."""
    try:
        # Read hook input from stdin
        hook_input = json.loads(sys.stdin.read())

        # Initialize monitor (will auto-load config)
        monitor = ContextMonitor()

        # Run the check
        exit_code = monitor.check_and_notify(hook_input)
        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
