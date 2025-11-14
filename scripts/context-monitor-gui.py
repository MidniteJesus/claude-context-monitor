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
    "always_on_top": True,
    "notification_enabled": True,
    "output_file": "claude.md",
    "instructions": "Update with current progress, successes, failures, and handoff notes",
    "appearance_mode": "dark",  # "dark", "light", "system"
    "color_theme": "blue"  # "blue", "green", "dark-blue"
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


class SettingsWindow:
    """Settings window for configuring the monitor."""

    def __init__(self, parent, config, config_path, on_save_callback):
        self.parent = parent
        self.config = config.copy()
        self.config_path = config_path
        self.on_save_callback = on_save_callback

        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x600")
        self.window.resizable(False, False)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Build UI
        self._build_ui()

        # Center on parent
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the settings interface."""
        # Main container with scrollbar
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Display Settings Section
        display_frame = ctk.CTkFrame(main_frame)
        display_frame.pack(fill="x", pady=(0, 15))

        display_label = ctk.CTkLabel(
            display_frame,
            text="Display Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        display_label.pack(anchor="w", padx=15, pady=(10, 10))

        # Appearance Mode
        appearance_container = ctk.CTkFrame(display_frame, fg_color="transparent")
        appearance_container.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            appearance_container,
            text="Theme:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))

        self.appearance_var = ctk.StringVar(value=self.config.get("appearance_mode", "dark"))
        self.appearance_menu = ctk.CTkOptionMenu(
            appearance_container,
            values=["dark", "light", "system"],
            variable=self.appearance_var,
            command=self._on_appearance_change
        )
        self.appearance_menu.pack(side="left")

        # Color Theme
        color_container = ctk.CTkFrame(display_frame, fg_color="transparent")
        color_container.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            color_container,
            text="Color Scheme:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))

        self.color_var = ctk.StringVar(value=self.config.get("color_theme", "blue"))
        self.color_menu = ctk.CTkOptionMenu(
            color_container,
            values=["blue", "green", "dark-blue"],
            variable=self.color_var,
            command=self._on_color_change
        )
        self.color_menu.pack(side="left")

        # Always on Top
        self.always_on_top_var = ctk.BooleanVar(value=self.config.get("always_on_top", True))
        self.always_on_top_check = ctk.CTkCheckBox(
            display_frame,
            text="Always on top",
            variable=self.always_on_top_var,
            font=ctk.CTkFont(size=12)
        )
        self.always_on_top_check.pack(anchor="w", padx=15, pady=(5, 10))

        # Window Size
        size_container = ctk.CTkFrame(display_frame, fg_color="transparent")
        size_container.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(
            size_container,
            text="Window Size:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))

        self.size_var = ctk.StringVar(value=self._get_size_preset())
        self.size_menu = ctk.CTkOptionMenu(
            size_container,
            values=["Small (400x250)", "Medium (450x300)", "Large (500x350)"],
            variable=self.size_var
        )
        self.size_menu.pack(side="left")

        # Monitoring Settings Section
        monitor_frame = ctk.CTkFrame(main_frame)
        monitor_frame.pack(fill="x", pady=(0, 15))

        monitor_label = ctk.CTkLabel(
            monitor_frame,
            text="Monitoring Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        monitor_label.pack(anchor="w", padx=15, pady=(10, 10))

        # Threshold Slider
        threshold_container = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        threshold_container.pack(fill="x", padx=15, pady=5)

        threshold_label_frame = ctk.CTkFrame(threshold_container, fg_color="transparent")
        threshold_label_frame.pack(fill="x")

        ctk.CTkLabel(
            threshold_label_frame,
            text="Alert Threshold:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self.threshold_value_label = ctk.CTkLabel(
            threshold_label_frame,
            text=f"{int(self.config.get('threshold', 0.80) * 100)}%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.threshold_value_label.pack(side="right")

        self.threshold_slider = ctk.CTkSlider(
            threshold_container,
            from_=50,
            to=100,
            number_of_steps=50,
            command=self._on_threshold_change
        )
        self.threshold_slider.set(self.config.get("threshold", 0.80) * 100)
        self.threshold_slider.pack(fill="x", pady=(5, 0))

        # Update Interval
        interval_container = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        interval_container.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            interval_container,
            text="Update Interval (seconds):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))

        self.interval_var = ctk.StringVar(value=str(self.config.get("update_interval", 2)))
        self.interval_entry = ctk.CTkEntry(
            interval_container,
            width=60,
            textvariable=self.interval_var
        )
        self.interval_entry.pack(side="left")

        # Notifications Toggle
        self.notification_var = ctk.BooleanVar(value=self.config.get("notification_enabled", True))
        self.notification_check = ctk.CTkCheckBox(
            monitor_frame,
            text="Enable notifications",
            variable=self.notification_var,
            font=ctk.CTkFont(size=12)
        )
        self.notification_check.pack(anchor="w", padx=15, pady=(5, 10))

        # Output Settings Section
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", pady=(0, 15))

        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.pack(anchor="w", padx=15, pady=(10, 10))

        # Output File
        file_container = ctk.CTkFrame(output_frame, fg_color="transparent")
        file_container.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            file_container,
            text="Output File:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")

        self.output_file_var = ctk.StringVar(value=self.config.get("output_file", "claude.md"))
        self.output_file_entry = ctk.CTkEntry(
            file_container,
            textvariable=self.output_file_var,
            width=300
        )
        self.output_file_entry.pack(fill="x", pady=(5, 0))

        # Custom Instructions
        instructions_container = ctk.CTkFrame(output_frame, fg_color="transparent")
        instructions_container.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkLabel(
            instructions_container,
            text="Custom Instructions:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")

        self.instructions_text = ctk.CTkTextbox(
            instructions_container,
            height=80,
            width=300
        )
        self.instructions_text.pack(fill="x", pady=(5, 0))
        self.instructions_text.insert("1.0", self.config.get("instructions", ""))

        # Action Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        self.save_button = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._on_save,
            width=120
        )
        self.save_button.pack(side="left", padx=(0, 10))

        self.reset_button = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._on_reset,
            width=120,
            fg_color="gray40",
            hover_color="gray30"
        )
        self.reset_button.pack(side="left", padx=(0, 10))

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=120,
            fg_color="transparent",
            border_width=2
        )
        self.cancel_button.pack(side="right")

    def _get_size_preset(self):
        """Get the current size preset name."""
        width = self.config.get("window_width", 450)
        height = self.config.get("window_height", 300)

        if width == 400 and height == 250:
            return "Small (400x250)"
        elif width == 500 and height == 350:
            return "Large (500x350)"
        else:
            return "Medium (450x300)"

    def _on_threshold_change(self, value):
        """Update threshold label when slider moves."""
        self.threshold_value_label.configure(text=f"{int(value)}%")

    def _on_appearance_change(self, choice):
        """Apply appearance mode immediately."""
        ctk.set_appearance_mode(choice)

    def _on_color_change(self, choice):
        """Apply color theme immediately."""
        ctk.set_default_color_theme(choice)

    def _on_save(self):
        """Save settings to config file."""
        try:
            # Parse size preset
            size_preset = self.size_var.get()
            if "Small" in size_preset:
                width, height = 400, 250
            elif "Large" in size_preset:
                width, height = 500, 350
            else:
                width, height = 450, 300

            # Update config
            self.config["threshold"] = self.threshold_slider.get() / 100
            self.config["update_interval"] = int(self.interval_var.get())
            self.config["always_on_top"] = self.always_on_top_var.get()
            self.config["notification_enabled"] = self.notification_var.get()
            self.config["output_file"] = self.output_file_var.get()
            self.config["instructions"] = self.instructions_text.get("1.0", "end-1c")
            self.config["window_width"] = width
            self.config["window_height"] = height
            self.config["appearance_mode"] = self.appearance_var.get()
            self.config["color_theme"] = self.color_var.get()

            # Save to file
            if self.config_path:
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                print(f"Settings saved to: {self.config_path}")

            # Notify parent
            self.on_save_callback(self.config)

            # Close window
            self.window.destroy()

        except Exception as e:
            print(f"Error saving settings: {e}")

    def _on_reset(self):
        """Reset all settings to defaults."""
        # Update UI elements
        self.threshold_slider.set(DEFAULT_CONFIG["threshold"] * 100)
        self.interval_var.set(str(DEFAULT_CONFIG["update_interval"]))
        self.always_on_top_var.set(DEFAULT_CONFIG["always_on_top"])
        self.notification_var.set(DEFAULT_CONFIG["notification_enabled"])
        self.output_file_var.set(DEFAULT_CONFIG["output_file"])
        self.instructions_text.delete("1.0", "end")
        self.instructions_text.insert("1.0", DEFAULT_CONFIG["instructions"])
        self.appearance_var.set(DEFAULT_CONFIG["appearance_mode"])
        self.color_var.set(DEFAULT_CONFIG["color_theme"])
        self.size_var.set("Medium (450x300)")

        # Apply appearance changes
        ctk.set_appearance_mode(DEFAULT_CONFIG["appearance_mode"])
        ctk.set_default_color_theme(DEFAULT_CONFIG["color_theme"])

    def _on_cancel(self):
        """Close without saving."""
        self.window.destroy()


class ContextMonitorGUI:
    """Main GUI application for context monitoring."""

    def __init__(self, config_path=None):
        self.config_path = self._find_config_path(config_path)
        self.config = self._load_config()

        # Set appearance mode and color theme from config
        ctk.set_appearance_mode(self.config.get("appearance_mode", "dark"))
        ctk.set_default_color_theme(self.config.get("color_theme", "blue"))

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
        self.settings_window = None

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

    def _find_config_path(self, config_path=None):
        """Find the configuration file path."""
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
                return path

        # Return default path if none exist
        return Path.home() / ".claude" / "context-monitor-config.json"

    def _load_config(self):
        """Load configuration from file or use defaults."""
        config = DEFAULT_CONFIG.copy()

        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                    print(f"Loaded config from: {self.config_path}")
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

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

        # Settings button
        self.settings_button = ctk.CTkButton(
            main_frame,
            text="⚙️ Settings",
            command=self._open_settings,
            width=120,
            height=32,
            fg_color="transparent",
            border_width=2
        )
        self.settings_button.pack(pady=(15, 0))

    def _open_settings(self):
        """Open the settings window."""
        if self.settings_window is None or not self.settings_window.window.winfo_exists():
            self.settings_window = SettingsWindow(
                self.root,
                self.config,
                self.config_path,
                self._on_settings_saved
            )

    def _on_settings_saved(self, new_config):
        """Handle settings being saved."""
        self.config = new_config

        # Apply immediate changes
        self.root.attributes('-topmost', self.config.get("always_on_top", True))

        # Restart polling if interval changed
        if hasattr(self, '_polling_active'):
            # Will pick up new interval on next poll cycle
            pass

        print("Settings applied successfully")

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
        threshold = self.config.get("threshold", 0.80) * 100
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
        self._polling_active = True
        interval = self.config.get("update_interval", 2) * 1000  # Convert to ms
        self._poll_update()
        self.root.after(interval, self._poll_loop)
        self.status_label.configure(text="● Monitoring (polling)")
        print(f"Started polling monitoring (every {interval/1000}s)")

    def _poll_loop(self):
        """Polling loop for file updates."""
        if hasattr(self, '_polling_active') and self._polling_active:
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
        if hasattr(self, '_polling_active'):
            self._polling_active = False
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
