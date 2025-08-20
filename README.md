# AI‑агент по ТЗ: генерация кода и PR через MCP GitHub Server

Минимальный прототип, который при изменении `tasks/task1.md` в репозитории:
- читает текст ТЗ;
- генерирует Python‑код из ТЗ при помощи OpenAI API;
- создаёт ветку, кладёт файл и открывает Pull Request — всё через MCP `@modelcontextprotocol/server-github`.

### Как это работает
- GitHub Actions workflow `.github/workflows/agent.yml` триггерится на push в `tasks/**`;
- запускает `python agent/agent_mcp_github.py`;
- скрипт вызывает OpenAI и через MCP GitHub Server выполняет: `create_branch` → `create_or_update_file` → `create_pull_request`.

### Требования
- Python 3.11+
- Node.js 20+ (для запуска MCP‑сервера через `npx`)
- В репозитории GitHub Secrets:
  - `OPENAI_API_KEY` — ключ OpenAI
- Права по умолчанию у `GITHUB_TOKEN` заданы в workflow (`contents: write`, `pull-requests: write`). Токен пробрасывается в MCP через `GITHUB_PERSONAL_ACCESS_TOKEN`.

### Локальный запуск (опционально)
```bash
python -m venv .venv && source .venv/Scripts/activate  # в Git Bash на Windows
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-5
export GITHUB_REPOSITORY=Owner/Repo
export BASE_BRANCH=main
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx  # либо используйте GITHUB_TOKEN

python agent/agent_mcp_github.py
```

### Структура
- `agent/agent_mcp_github.py` — основной скрипт агента (генерация и PR через MCP)
- `agent/mcp_client.py` — минимальный MCP‑клиент по stdio
- `.github/workflows/agent.yml` — триггер пайплайна на изменения в `tasks/**`
- `tasks/task1.md` — входное ТЗ
- `requirements.txt` — зависимости агента
- `.gitignore`, `.env.example`

### Замечания
- Дополнительная установка MCP‑сервера не нужна: он запускается как `npx @modelcontextprotocol/server-github` внутри скрипта.
- Для межрепозитарных PR может потребоваться персональный токен с `repo`‑правами.

