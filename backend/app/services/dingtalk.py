from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

_last_alert_times: dict[str, datetime] = {}


def is_silenced(repo_name: str, silence_minutes: int) -> bool:
    if silence_minutes <= 0:
        return False
    last_time = _last_alert_times.get(repo_name)
    if last_time is None:
        return False
    return datetime.utcnow() - last_time < timedelta(minutes=silence_minutes)


def record_alert_sent(repo_name: str) -> None:
    _last_alert_times[repo_name] = datetime.utcnow()


def send_dingtalk_alert(
    webhook_url: str,
    violations: list,
    repo_name: str,
    silence_minutes: int = 60,
) -> bool:
    if not webhook_url:
        return False

    if is_silenced(repo_name, silence_minutes):
        logger.info(
            f"DingTalk alert silenced for {repo_name} "
            f"(last sent within {silence_minutes}min window)"
        )
        return False

    by_rule: dict[str, int] = {}
    for v in violations:
        by_rule[v.rule_name] = by_rule.get(v.rule_name, 0) + 1

    lines = [f"## Git Habits Alert: {repo_name}\n"]
    lines.append(f"Detected **{len(violations)}** violation(s):\n")
    for rule, count in sorted(by_rule.items(), key=lambda x: -x[1]):
        lines.append(f"- **{rule}**: {count}")

    lines.append(f"\n### Recent violations (top 5):\n")
    for v in violations[:5]:
        lines.append(f"- `{v.commit_hash}` [{v.rule_name}] {v.description}")

    text = "\n".join(lines)

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"Git Habits Alert: {repo_name}",
            "text": text,
        },
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            record_alert_sent(repo_name)
            logger.info(f"DingTalk alert sent for {repo_name}: {len(violations)} violations")
            return True
        else:
            logger.warning(f"DingTalk alert failed: HTTP {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"DingTalk alert error: {e}")
        return False
