# Phase Planning Input

**Date:** 2026-03-27
**Source:** user request

## Requested Outcome

I want the frontend to support displaying blocks beyond `text_block`,
specifically `image_block`, `audio_block`, and `video_block`.

I also want to add tools for the agent that can call:
- Claude Code CLI
- Codex CLI
- Gemini CLI

The CLI messages and transcript should also be synchronized into the
frontend chat display.

## Planning Notes

- This is a brownfield enhancement to the existing HaiBot runtime and web
  console.
- The feature must fit the current chat streaming, persistence, and approval
  model.
- The frontend display and the backend message contract need to stay aligned
  so live streams and history replay behave the same way.
