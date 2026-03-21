# HaiBot Project Context

HaiBot is a **personal AI assistant framework** designed to run in the user's own environment (local or cloud). It connects to multiple chat channels (DingTalk, Feishu, QQ, Discord, iMessage, etc.) and provides a web-based console for interaction and configuration. The system is built for extensibility through a "Skills" architecture and supports long-term memory.

## Core Technologies

- **Language:** Python 3.10+ (Backend), TypeScript (Frontend)
- **Agent Framework:** [AgentScope](https://github.com/agentscope-ai/agentscope) & [AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime)
- **Web Backend:** [FastAPI](https://fastapi.tiangolo.com/) with Uvicorn
- **Web Frontend:** [Vue 3](https://vuejs.org/), [Vite](https://vitejs.dev/), [Pinia](https://pinia.vuejs.org/), [Element Plus](https://element-plus.org/)
- **Memory System:** [ReMe](https://github.com/agentscope-ai/ReMe)
- **Task Scheduling:** [APScheduler](https://apscheduler.readthedocs.io/)
- **Automation:** [Playwright](https://playwright.dev/) for browser-based tasks
- **CLI:** [Click](https://click.palletsprojects.com/)

## Project Structure

- `src/haibot/`: Main Python source code.
    - `agents/`: Core agent logic (`HaiBotAgent`), prompt engineering, and skills management.
    - `app/`: FastAPI application, multi-agent management, and API routers.
    - `cli/`: CLI command implementations (`init`, `app`, `models`, `skills`, etc.).
    - `providers/`: Model provider integrations (OpenAI, DashScope, Ollama, etc.).
    - `security/`: Skill scanners and tool-guard security rules.
    - `utils/`: Logging, telemetry, and common utilities.
- `frontend/`: Vue.js source code for the Web Console.
- `tests/`: Project test suite.
    - `unit/`: Unit tests for various modules.
    - `integrated/`: End-to-end and integration tests.
- `scripts/`: Utility scripts for building, testing, and deployment.
- `deploy/`: Docker and supervisor configuration files.

## Key Development Commands

### Environment Setup
```bash
# Install with dev and full extras
pip install -e ".[dev,full]"

# Setup pre-commit hooks
pre-commit install
```

### Initializing & Running
```bash
# Initialize with default settings
haibot init --defaults

# Start the application (Backend + Web Console)
haibot app
```

### Frontend Development
```bash
cd frontend
pnpm install
pnpm dev    # Start dev server
pnpm build  # Build for production (outputs to src/haibot/console/)
```

### Testing & Validation
```bash
# Run all tests
python scripts/run_tests.py

# Run specific unit tests
python scripts/run_tests.py -u providers

# Run with coverage
python scripts/run_tests.py -a -c

# Linting
pre-commit run --all-files
```

## Development Conventions

- **Surgical Updates:** Always prefer targeted changes. When modifying agent logic, check `src/haibot/agents/react_agent.py`.
- **Skills Architecture:** New capabilities should ideally be implemented as **Skills**. Skills live in `src/haibot/agents/skills/` and follow the `SKILL.md` + `scripts/` + `references/` structure.
- **Async First:** The backend is heavily asynchronous. Use `async/await` for I/O bound operations.
- **Multi-Workspace:** HaiBot supports multiple agents/workspaces. Access the active agent via `app.state.multi_agent_manager` in FastAPI routes.
- **Security:** Tools that perform destructive actions (like `execute_shell_command`) are intercepted by the `ToolGuardMixin`. Ensure security rules in `src/haibot/security/` are respected.
- **Documentation:** The project uses `README.md`, `CONTRIBUTING.md`, and an external documentation site. Ensure new features are documented.
