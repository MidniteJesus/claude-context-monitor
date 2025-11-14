#!/usr/bin/env python3
"""
Claude Code Context Monitor GUI
Real-time visual display of context usage with modern, cross-platform interface.

Usage:
    python context-monitor-gui.py [--config CONFIG_PATH]
"""

import customtkinter as ctk
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import time
import threading
import argparse

# Import watchdog for file monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object  # Dummy base class
    print("Warning: watchdog not installed. Falling back to polling mode.")
    print("Install with: pip install watchdog")


# Default configuration
DEFAULT_CONFIG = {
    "threshold": 0.80,
    "max_context_tokens": 200000,
    "update_interval": 2,  # seconds (for polling mode)
    "window_width": 450,
    "window_height": 300,
    "always_on_top": True
}


class TranscriptWatcher(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watches transcript file for changes and triggers GUI updates."""

    def __init__(self, callback):
        self.callback = callback
        self.last_modified = 0

    def on_modified(self, event):
        if event.src_path.endswith('.jsonl'):
            # Debounce: only trigger if >0.5 seconds since last modification
            current_time = time.time()
            if current_time - self.last_modified > 0.5:
                self.last_modified = current_time
                self.callback()


class ContextMonitorGUI:
    """Main GUI application for context monitoring."""

    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)

        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

        self.root = ctk.CTk()
        self.root.title("Claude Context Monitor")

        # Window configuration
        width = self.config.get("window_width", 450)
        height = self.config.get("window_height", 300)
        self.root.geometry(f"{width}x{height}")

        # Make window fixed-size (removes maximize button, prevents WSLg bug)
        self.root.resizable(False, False)

        if self.config.get("always_on_top", True):
            self.root.attributes('-topmost', True)

        # Track current session
        self.current_transcript = None
        self.last_usage = None
        self.observer = None

        # Build UI
        self._build_ui()

        # Find and monitor transcript
        self._find_active_session()

        # Start monitoring
        if self.current_transcript:
            self._start_monitoring()
        else:
            self.status_label.configure(text="⚠️ No active Claude session found")

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_config(self, config_path=None):
        """Load configuration from file or use defaults."""
        config = DEFAULT_CONFIG.copy()

        search_paths = []
        if config_path:
            search_paths.append(Path(config_path))

        search_paths.extend([
            Path.cwd() / "config.json",
            Path(__file__).parent.parent / "config.json",
            Path.home() / ".claude" / "context-monitor-config.json"
        ])

        for path in search_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        user_config = json.load(f)
                        config.update(user_config)
                        print(f"Loaded config from: {path}")
                        break
                except Exception as e:
                    print(f"Error loading config from {path}: {e}")

        return config

    def _build_ui(self):
        """Build the modern GUI interface."""
        # Main frame with padding
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Claude Code Context Monitor",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Percentage display with large font
        self.percentage_label = ctk.CTkLabel(
            main_frame,
            text="Context: 0.0%",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#4CAF50"
        )
        self.percentage_label.pack(pady=(0, 15))

        # Progress bar (modern style)
        self.progress = ctk.CTkProgressBar(
            main_frame,
            width=400,
            height=20,
            corner_radius=10,
            progress_color="#4CAF50"
        )
        self.progress.set(0)
        self.progress.pack(pady=(0, 20))

        # Token count
        self.tokens_label = ctk.CTkLabel(
            main_frame,
            text="0 / 200,000 tokens",
            font=ctk.CTkFont(size=13)
        )
        self.tokens_label.pack(pady=(0, 10))

        # Status indicator with icon
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="● Initializing...",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.status_label.pack(pady=(10, 0))

    def _find_active_session(self):
        """Find the most recent Claude Code session transcript."""
        projects_dir = Path.home() / ".claude" / "projects"

        if not projects_dir.exists():
            return None

        # Find all transcript files
        transcripts = []
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                for transcript in project_dir.glob("*.jsonl"):
                    # Skip agent transcripts
                    if not transcript.name.startswith("agent-"):
                        transcripts.append(transcript)

        if not transcripts:
            return None

        # Get the most recently modified transcript
        self.current_transcript = max(transcripts, key=lambda p: p.stat().st_mtime)
        print(f"Monitoring: {self.current_transcript}")

        # Do initial parse
        self._update_display()

        return self.current_transcript

    def _parse_transcript(self):
        """Parse the transcript file and extract context usage."""
        if not self.current_transcript or not self.current_transcript.exists():
            return None

        try:
            entries = []
            with open(self.current_transcript, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Filter for valid entries with usage data
            valid_entries = [
                entry for entry in entries
                if entry.get('message', {}).get('usage') is not None
                and not entry.get('isSidechain', False)
                and not entry.get('isApiErrorMessage', False)
                and entry.get('timestamp')
            ]

            if not valid_entries:
                return None

            # Get most recent entry
            latest_entry = max(valid_entries, key=lambda x: x.get('timestamp', 0))
            usage = latest_entry.get('message', {}).get('usage', {})

            # Calculate total tokens
            input_tokens = usage.get('input_tokens', 0)
            cache_read = usage.get('cache_read_input_tokens', 0)
            cache_creation = usage.get('cache_creation_input_tokens', 0)

            total_tokens = input_tokens + cache_read + cache_creation
            max_tokens = self.config["max_context_tokens"]
            percentage = (total_tokens / max_tokens) * 100

            return {
                'total_tokens': total_tokens,
                'percentage': percentage,
                'input_tokens': input_tokens,
                'cache_read': cache_read,
                'cache_creation': cache_creation
            }

        except Exception as e:
            print(f"Error parsing transcript: {e}")
            return None

    def _update_display(self):
        """Update the GUI with current context usage."""
        usage = self._parse_transcript()

        if usage is None:
            return

        self.last_usage = usage

        # Update percentage label
        percentage = usage['percentage']
        self.percentage_label.configure(text=f"Context: {percentage:.1f}%")

        # Update progress bar (value between 0 and 1)
        self.progress.set(percentage / 100)

        # Update token count
        total = usage['total_tokens']
        max_tokens = self.config["max_context_tokens"]
        self.tokens_label.configure(text=f"{total:,} / {max_tokens:,} tokens")

        # Color coding based on usage
        if percentage >= 95:
            color = '#F44336'  # Red
            progress_color = '#F44336'
            status = "● Critical - Clear soon!"
        elif percentage >= 85:
            color = '#FF9800'  # Orange
            progress_color = '#FF9800'
            status = "● High - Approaching limit"
        elif percentage >= 70:
            color = '#FFC107'  # Yellow/Amber
            progress_color = '#FFC107'
            status = "● Moderate"
        else:
            color = '#4CAF50'  # Green
            progress_color = '#4CAF50'
            status = "● Normal"

        self.percentage_label.configure(text_color=color)
        self.progress.configure(progress_color=progress_color)
        self.status_label.configure(text=status, text_color=color)

        # Update window title with percentage
        self.root.title(f"Claude Context - {percentage:.0f}%")

    def _start_monitoring(self):
        """Start monitoring the transcript file for changes."""
        if WATCHDOG_AVAILABLE:
            self._start_watchdog_monitoring()
        else:
            self._start_polling_monitoring()

    def _start_watchdog_monitoring(self):
        """Start file watching using watchdog library."""
        try:
            event_handler = TranscriptWatcher(callback=self._on_file_changed)
            self.observer = Observer()
            self.observer.schedule(
                event_handler,
                str(self.current_transcript.parent),
                recursive=False
            )
            self.observer.start()
            self.status_label.configure(text="● Monitoring (real-time)")
            print("Started watchdog monitoring")
        except Exception as e:
            print(f"Error starting watchdog: {e}")
            self._start_polling_monitoring()

    def _start_polling_monitoring(self):
        """Fallback: Poll the file periodically."""
        interval = self.config.get("update_interval", 2) * 1000  # Convert to ms
        self._poll_update()
        self.root.after(interval, self._poll_loop)
        self.status_label.configure(text="● Monitoring (polling)")
        print(f"Started polling monitoring (every {interval/1000}s)")

    def _poll_loop(self):
        """Polling loop for file updates."""
        self._poll_update()
        interval = self.config.get("update_interval", 2) * 1000
        self.root.after(interval, self._poll_loop)

    def _poll_update(self):
        """Check for updates and refresh display."""
        self._update_display()

    def _on_file_changed(self):
        """Callback when transcript file changes (watchdog)."""
        # Schedule GUI update in main thread
        self.root.after(0, self._update_display)

    def _on_closing(self):
        """Handle window close event."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.root.destroy()

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    """Entry point for the GUI application."""
    parser = argparse.ArgumentParser(
        description="Claude Code Context Monitor GUI"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    args = parser.parse_args()

    # Create and run GUI
    app = ContextMonitorGUI(config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()
