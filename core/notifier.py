"""
core/notifier.py - Desktop Notifications & Discord/Telegram Webhook Integration.
"""

import json
import urllib.request
import logging
from typing import Dict, Any

logger = logging.getLogger("AnimeOrganizer")


class Notifier:
    """Dispatches notifications via desktop and webhooks (Discord, Telegram)."""

    @staticmethod
    def send_desktop_notification(title: str, message: str):
        """Displays a desktop notification using native or fallback methods."""
        try:
            # Try win10toast or plyer if installed
            try:
                from plyer import notification
                notification.notify(title=title, message=message, app_name="AnimeOrganizerPro", timeout=5)
                return
            except ImportError:
                pass

            # Fallback for Windows PowerShell balloon tip
            import subprocess
            ps_cmd = f"""
            [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
            $notify = new-object system.windows.forms.notifyicon
            $notify.icon = [system.drawing.systemicons]::Information
            $notify.visible = $true
            $notify.showballoontip(10, '{title}', '{message}', [system.windows.forms.tooltipicon]::Info)
            """
            subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")

    @staticmethod
    def send_discord_webhook(webhook_url: str, summary: Dict[str, Any]) -> bool:
        """Sends a rich summary embed to a Discord Webhook URL."""
        if not webhook_url or not webhook_url.startswith("http"):
            return False

        payload = {
            "username": "Anime Organizer Pro",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/3845/3845868.png",
            "embeds": [
                {
                    "title": "🎉 File Organization Complete!",
                    "color": 3066993,  # Green
                    "fields": [
                        {"name": "✅ Processed", "value": str(summary.get("processed", 0)), "inline": True},
                        {"name": "⏭️ Skipped", "value": str(summary.get("skipped", 0)), "inline": True},
                        {"name": "🔍 Duplicates", "value": str(summary.get("duplicates", 0)), "inline": True},
                        {"name": "❌ Errors", "value": str(summary.get("errors", 0)), "inline": True},
                        {"name": "⚡ Speed", "value": f"{summary.get('files_per_sec', 0)} files/s", "inline": True},
                        {"name": "⏱️ Time", "value": f"{summary.get('duration_seconds', 0)}s", "inline": True},
                    ],
                    "footer": {"text": "Smart File Organizer Pro v4.0"}
                }
            ]
        }

        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AnimeOrganizer/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in (200, 204)
        except Exception as e:
            logger.warning(f"Discord webhook failed: {e}")
            return False

    @staticmethod
    def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
        """Sends message via Telegram Bot API."""
        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Telegram notification failed: {e}")
            return False
