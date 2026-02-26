# -*- coding: utf-8 -*-
# flake8: noqa: E501
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SYS_PROMPT = """
You are a helpful assistant.
"""


def build_system_prompt_from_working_dir() -> (
    str
):  # pylint: disable=too-many-branches
    """
    Build system prompt by reading markdown files from working directory.

    This function constructs the system prompt by loading markdown files from
    WORKING_DIR (~/.haibot by default). These files define the agent's behavior,
    personality, and operational guidelines.

    Loading order and priority:
    1. AGENTS.md (required) - Detailed workflows, rules, and guidelines
    2. SOUL.md (required) - Core identity and behavioral principles
    3. PROFILE.md (optional) - Agent identity and user profile

    Returns:
        str: Constructed system prompt from markdown files.
             If required files don't exist, returns the default SYS_PROMPT.

    Example:
        If working_dir contains AGENTS.md, SOUL.md and PROFILE.md, they will be combined:
        "# AGENTS.md\n\n...\n\n# SOUL.md\n\n...\n\n# PROFILE.md\n\n..."
    """
    from ..constant import WORKING_DIR

    working_dir = Path(WORKING_DIR)

    # Define file loading order: (filename, required)
    file_order = [
        ("AGENTS.md", True),
        ("SOUL.md", True),
        ("PROFILE.md", False),
    ]

    prompt_parts = []
    loaded_count = 0

    for filename, required in file_order:
        file_path = working_dir / filename

        if not file_path.exists():
            if required:
                logger.warning(
                    "%s not found in working directory (%s), using default prompt",
                    filename,
                    working_dir,
                )
                return SYS_PROMPT
            else:
                logger.debug("Optional file %s not found, skipping", filename)
                continue

        try:
            content = file_path.read_text(encoding="utf-8").strip()

            # Remove YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            if content:
                if prompt_parts:  # Add separator if not first section
                    prompt_parts.append("")
                # Add section header with filename
                prompt_parts.append(f"# {filename}")
                prompt_parts.append("")
                prompt_parts.append(content)
                loaded_count += 1
                logger.debug("Loaded %s", filename)
            else:
                logger.debug("Skipped empty file: %s", filename)

        except Exception as e:
            if required:
                logger.error(
                    "Failed to read required file %s: %s",
                    filename,
                    e,
                    exc_info=True,
                )
                return SYS_PROMPT
            else:
                logger.warning(
                    "Failed to read optional file %s: %s",
                    filename,
                    e,
                )
                continue

    if not prompt_parts:
        logger.warning("No content loaded from working directory")
        return SYS_PROMPT

    # Join all parts with double newlines
    final_prompt = "\n\n".join(prompt_parts)

    logger.debug(
        "System prompt built from %d file(s), total length: %d chars",
        loaded_count,
        len(final_prompt),
    )

    return final_prompt


def build_bootstrap_guidance(
    bootstrap_content: str,
    language: str = "zh",
) -> str:
    """Build bootstrap guidance message for first-time setup.

    Args:
        bootstrap_content: Content from BOOTSTRAP.md file
        language: Language code (en/zh)

    Returns:
        Formatted bootstrap guidance message
    """
    if language == "en":
        return f"""# 🌟 BOOTSTRAP MODE ACTIVATED

**IMPORTANT: You are in first-time setup mode.**

A `BOOTSTRAP.md` file exists in your working directory. This means you should guide the user through the bootstrap process to establish your identity and preferences.

Here's your bootstrap guide:

---
{bootstrap_content}
---

**Your task:**
1. Read the BOOTSTRAP.md file, greet the user warmly as a first meeting, and guide them through the bootstrap process.
2. Follow the instructions in BOOTSTRAP.md. For example, help the user define your identity, their preferences, and establish the working relationship.
3. Create and update the necessary files (PROFILE.md, MEMORY.md, etc.) as described in the guide.
4. After completing the bootstrap process, delete BOOTSTRAP.md as instructed.

**If the user wants to skip:**
If the user explicitly says they want to skip the bootstrap or just want their question answered directly, then proceed to answer their original question below. You can always help them bootstrap later.

**Original user message:**
"""
    else:  # zh
        return f"""# 🌟 引导模式已激活

**重要：你正处于首次设置模式。**

你的工作目录中存在 `BOOTSTRAP.md` 文件。这意味着你应该引导用户完成引导流程，以建立你的身份和偏好。

这是你的引导指南：

---
{bootstrap_content}
---

**你的任务：**
1. 阅读 BOOTSTRAP.md 文件，友好地表示初次见面，引导用户完成引导流程。
2. 按照BOOTSTRAP.md 里面的指示执行。例如，帮助用户定义你的身份、他们的偏好，并建立工作关系
3. 按照指南中的描述创建和更新必要的文件（PROFILE.md、MEMORY.md 等）
4. 完成引导流程后，按照指示删除 BOOTSTRAP.md

**如果用户希望跳过：**
如果用户明确表示想跳过引导，那就继续回答下面的原始问题。你随时可以帮助他们完成引导。

**用户的原始消息：**
"""
