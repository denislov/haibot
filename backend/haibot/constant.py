# -*- coding: utf-8 -*-
import os
from pathlib import Path

WORKING_DIR = (
    Path(os.environ.get("HAIBOT_WORKING_DIR", "~/.haibot"))
    .expanduser()
    .resolve()
)

JOBS_FILE = os.environ.get("HAIBOT_JOBS_FILE", "jobs.json")

CHATS_FILE = os.environ.get("HAIBOT_CHATS_FILE", "chats.json")

CONFIG_FILE = os.environ.get("HAIBOT_CONFIG_FILE", "config.json")

HEARTBEAT_FILE = os.environ.get("HAIBOT_HEARTBEAT_FILE", "HEARTBEAT.md")
HEARTBEAT_DEFAULT_EVERY = "30m"
HEARTBEAT_DEFAULT_TARGET = "main"
HEARTBEAT_TARGET_LAST = "last"

# Env key for app log level (used by CLI and app load for reload child).
LOG_LEVEL_ENV = "HAIBOT_LOG_LEVEL"

# Env to indicate running inside a container (e.g. Docker). Set to 1/true/yes.
RUNNING_IN_CONTAINER = os.environ.get("COPAW_RUNNING_IN_CONTAINER", "false")

# Playwright: use system Chromium when set (e.g. in Docker).
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH_ENV = "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"

# When True, expose /docs, /redoc, /openapi.json
# (dev only; keep False in prod).
DOCS_ENABLED = os.environ.get("HAIBOT_OPENAPI_DOCS", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Skills directories
# Active skills directory (activated skills that agents use)
ACTIVE_SKILLS_DIR = WORKING_DIR / "active_skills"
# Customized skills directory (user-created skills)
CUSTOMIZED_SKILLS_DIR = WORKING_DIR / "customized_skills"

# Memory directory
MEMORY_DIR = WORKING_DIR / "memory"

# Custom channel modules (installed via `copaw channels install`); manager
# loads BaseChannel subclasses from here.
CUSTOM_CHANNELS_DIR = WORKING_DIR / "custom_channels"

# Local models directory
MODELS_DIR = WORKING_DIR / "models"

# Memory compaction configuration
MEMORY_COMPACT_KEEP_RECENT = int(
    os.environ.get("HAIBOT_MEMORY_COMPACT_KEEP_RECENT", "3"),
)

MEMORY_COMPACT_RATIO = float(
    os.environ.get("HAIBOT_MEMORY_COMPACT_RATIO", "0.7"),
)

DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ---------------------------------------------------------------------------
# Channel availability — controlled by HAIBOT_ENABLED_CHANNELS env var.
# When unset / empty, ALL channels are available (wheel / local dev).
# Set to a comma-separated list to restrict, e.g.
#   HAIBOT_ENABLED_CHANNELS=dingtalk,feishu,qq,console
# ---------------------------------------------------------------------------
ALL_CHANNELS = ("imessage", "discord", "dingtalk", "feishu", "qq", "console")


def get_available_channels() -> tuple[str, ...]:
    """Return the tuple of channel keys that are enabled for this build/run.

    Reads ``HAIBOT_ENABLED_CHANNELS`` env var.  If unset or empty, all
    channels are available.
    """
    raw = os.environ.get("HAIBOT_ENABLED_CHANNELS", "").strip()
    if not raw:
        return ALL_CHANNELS
    enabled = tuple(ch.strip() for ch in raw.split(",") if ch.strip())
    return enabled or ALL_CHANNELS
