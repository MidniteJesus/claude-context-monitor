#!/usr/bin/env python3
"""
Cross-platform notification system for Claude Context Monitor.
Automatically detects the platform and uses the appropriate notification method.
"""

import platform
import subprocess
import sys
import os


class Notifier:
    """Cross-platform notification handler."""

    def __init__(self):
        self.system = platform.system()
        self.is_wsl = self._detect_wsl()

    def _detect_wsl(self):
        """Detect if running in WSL (Windows Subsystem for Linux)."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False

    def send(self, title, message):
        """
        Send a notification using the appropriate method for the platform.

        Args:
            title (str): Notification title
            message (str): Notification message

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            if self.is_wsl or self.system == "Windows":
                return self._notify_windows(title, message)
            elif self.system == "Darwin":
                return self._notify_macos(title, message)
            elif self.system == "Linux":
                return self._notify_linux(title, message)
            else:
                print(f"Unsupported platform: {self.system}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Notification failed: {e}", file=sys.stderr)
            return False

    def _notify_windows(self, title, message):
        """Send Windows toast notification via PowerShell."""
        # Escape special characters for PowerShell
        title = title.replace('"', '`"').replace("'", "''")
        message = message.replace('"', '`"').replace("'", "''")

        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$toastXml = [xml] $template.GetXml()
$toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) > $null
$toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{message}")) > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($toastXml.OuterXml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Context Monitor").Show($toast)
"""

        powershell_paths = [
            "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
            "powershell.exe",
            "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        ]

        for ps_path in powershell_paths:
            try:
                result = subprocess.run(
                    [ps_path, "-Command", ps_script],
                    capture_output=True,
                    timeout=5,
                    check=False
                )
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return False

    def _notify_macos(self, title, message):
        """Send macOS notification using osascript."""
        script = f'display notification "{message}" with title "{title}"'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
            check=False
        )
        return result.returncode == 0

    def _notify_linux(self, title, message):
        """Send Linux notification using notify-send."""
        try:
            result = subprocess.run(
                ["notify-send", "-u", "critical", "-t", "10000", title, message],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            # Fallback: try using dbus directly
            return self._notify_linux_dbus(title, message)

    def _notify_linux_dbus(self, title, message):
        """Fallback Linux notification using dbus-send."""
        try:
            result = subprocess.run([
                "dbus-send",
                "--session",
                "--type=method_call",
                "--dest=org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications.Notify",
                f"string:Claude Context Monitor",
                "uint32:0",
                "string:",
                f"string:{title}",
                f"string:{message}",
                "array:string:",
                "dict:string:string:",
                "int32:10000"
            ], capture_output=True, timeout=5, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False


def main():
    """Test the notification system."""
    if len(sys.argv) < 3:
        print("Usage: notifier.py <title> <message>")
        sys.exit(1)

    title = sys.argv[1]
    message = sys.argv[2]

    notifier = Notifier()
    success = notifier.send(title, message)

    if success:
        print(f"Notification sent successfully on {notifier.system}")
        sys.exit(0)
    else:
        print(f"Failed to send notification on {notifier.system}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
