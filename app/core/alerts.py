"""
Proactive Alert System — SOW §6.2

Dispatches critical intelligence to external channels via webhooks.

Supported channels:
  - Discord (webhook URL)
  - Slack (incoming webhook)
  - Email (via existing mailer.py / Resend)

Alert types:
  - CVE_DETECTED      → Critical security vulnerability
  - BREAKING_CHANGE   → Breaking change in a dependency
  - TRENDING_SPIKE    → Unusual spike in community interest
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from enum import Enum

from app.core.logger import logger


class AlertType(Enum):
    CVE_DETECTED = "cve_detected"
    BREAKING_CHANGE = "breaking_change"
    TRENDING_SPIKE = "trending_spike"
    DEPRECATION = "deprecation"
    RISK_HIGH = "risk_high"


class AlertChannel(Enum):
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"


# Severity-based emoji for clear visual priority
SEVERITY_EMOJI = {
    "CRITICAL": "🚨",
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
    "INFO": "ℹ️",
}


class AlertDispatcher:
    """
    Dispatches alerts to configured webhooks.

    Configuration via environment variables:
        DISCORD_WEBHOOK_URL → Discord channel
        SLACK_WEBHOOK_URL   → Slack channel
        ALERT_EMAIL         → Email recipient (via Resend)
    """

    def __init__(self):
        self.discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
        self.slack_url = os.environ.get("SLACK_WEBHOOK_URL")
        self.alert_email = os.environ.get("ALERT_EMAIL")

        self._alert_log: List[Dict] = []

    @property
    def configured_channels(self) -> List[str]:
        """List of configured alert channels."""
        channels = []
        if self.discord_url:
            channels.append("discord")
        if self.slack_url:
            channels.append("slack")
        if self.alert_email:
            channels.append("email")
        return channels

    async def dispatch(self, alert_type: AlertType, message: str,
                       severity: str = "HIGH", metadata: Dict = None,
                       channels: List[str] = None):
        """
        Dispatch an alert to configured channels.

        Args:
            alert_type: Type of alert
            message: Human-readable alert message
            severity: CRITICAL / HIGH / MEDIUM / LOW / INFO
            metadata: Additional context data
            channels: Specific channels to use (default: all configured)
        """
        metadata = metadata or {}
        emoji = SEVERITY_EMOJI.get(severity, "⚠️")
        channels = channels or self.configured_channels

        # Log the alert
        alert_record = {
            "type": alert_type.value,
            "severity": severity,
            "message": message,
            "metadata": metadata,
            "channels": channels,
        }
        self._alert_log.append(alert_record)

        logger.info(f"Alert: {emoji} [{severity}] {alert_type.value}: {message[:80]}")

        # Dispatch to each channel
        results = {}
        for channel in channels:
            try:
                if channel == "discord" and self.discord_url:
                    await self._send_discord(emoji, severity, alert_type, message, metadata)
                    results["discord"] = "sent"
                elif channel == "slack" and self.slack_url:
                    await self._send_slack(emoji, severity, alert_type, message, metadata)
                    results["slack"] = "sent"
                elif channel == "email" and self.alert_email:
                    self._send_email(severity, alert_type, message, metadata)
                    results["email"] = "sent"
            except Exception as e:
                logger.error(f"Alert dispatch to {channel} failed: {e}")
                results[channel] = f"error: {e}"

        return results

    async def _send_discord(self, emoji: str, severity: str,
                            alert_type: AlertType, message: str, metadata: Dict):
        """Send alert to Discord via webhook."""
        payload = {
            "embeds": [{
                "title": f"{emoji} DevPulseAI Alert — {alert_type.value.upper()}",
                "description": message,
                "color": self._severity_color(severity),
                "fields": [
                    {"name": "Severity", "value": severity, "inline": True},
                    {"name": "Type", "value": alert_type.value, "inline": True},
                ],
                "footer": {"text": "DevPulseAI v3 — Proactive Intelligence"},
            }]
        }

        # Add metadata fields
        for key, value in list(metadata.items())[:3]:
            payload["embeds"][0]["fields"].append({
                "name": key.replace("_", " ").title(),
                "value": str(value)[:100],
                "inline": True,
            })

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.discord_url, json=payload, timeout=10)
            resp.raise_for_status()

    async def _send_slack(self, emoji: str, severity: str,
                          alert_type: AlertType, message: str, metadata: Dict):
        """Send alert to Slack via incoming webhook."""
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} DevPulseAI: {alert_type.value.upper()}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Severity*: {severity}\n\n{message}"
                    }
                },
            ]
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.slack_url, json=payload, timeout=10)
            resp.raise_for_status()

    def _send_email(self, severity: str, alert_type: AlertType,
                    message: str, metadata: Dict):
        """Send alert via email (using Resend if configured)."""
        try:
            from app.core.mailer import send_email
            subject = f"[DevPulseAI] {severity}: {alert_type.value}"
            send_email(
                to=self.alert_email,
                subject=subject,
                body=message,
            )
        except Exception as e:
            logger.warning(f"Email alert failed: {e}")

    def _severity_color(self, severity: str) -> int:
        """Discord embed color for severity level."""
        colors = {
            "CRITICAL": 0xFF0000,  # Red
            "HIGH": 0xFF6600,      # Orange
            "MEDIUM": 0xFFCC00,     # Yellow
            "LOW": 0x00CC00,       # Green
            "INFO": 0x0099FF,      # Blue
        }
        return colors.get(severity, 0x808080)

    @property
    def alert_history(self) -> List[Dict]:
        """Get alert dispatch history."""
        return self._alert_log

    def status(self) -> Dict:
        """Get alert system status."""
        return {
            "configured_channels": self.configured_channels,
            "total_alerts_sent": len(self._alert_log),
            "recent_alerts": self._alert_log[-5:],
        }


# Singleton
alert_dispatcher = AlertDispatcher()
