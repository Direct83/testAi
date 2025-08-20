# AI‑агент по ТЗ: локальный MCP + PR в GitHub

Минимальный прототип, который при изменении `tasks/task1.md` в репозитории:
- читает текст ТЗ;
- генерирует Python‑код из ТЗ при помощи OpenAI API;
- создаёт ветку, кладёт файл и открывает Pull Request — всё через MCP `@modelcontextprotocol/server-github`.

### Как это работает
- Локально у вас запущен MCP сервер (Node) из `mcp_node`.
- Вы меняете `tasks/task1.md`, коммитите и делаете `git push`.
- Перед пушем срабатывает локальный git‑hook `hooks/pre-push`: он запускает `agent/agent_mcp_github.py` через ваш MCP, и агент создаёт ветку и PR в GitHub. При ошибке push отменяется.

### Быстрый старт
```bash
# 1) MCP (Node)
docker build -t mcp-github -f mcp_node/Dockerfile mcp_node
docker run -d --name mcp-github-local --rm -p 8081:8080 -e GITHUB_TOKEN="<ваш_PAT>" mcp-github:latest

# 2) Переменные окружения (Git Bash)
export OPENAI_API_KEY=sk-...
export GITHUB_REPOSITORY=Direct83/testAi
export BASE_BRANCH=main
export MCP_SERVER=http://127.0.0.1:8081

# 3) Измените tasks/task1.md → коммит/пуш
git add tasks/task1.md && git commit -m "docs: update task" && git push
# при push локальный pre-push хук запустит агента и создаст PR
```

### Требования
- Python 3.11+
- Node.js 20+ (для запуска MCP‑сервера через `npx` или локального HTTP MCP)
- В репозитории GitHub Secrets:
  - `OPENAI_API_KEY` — ключ OpenAI
- Права по умолчанию у `GITHUB_TOKEN` заданы в workflow (`contents: write`, `pull-requests: write`). Токен пробрасывается в MCP через `GITHUB_PERSONAL_ACCESS_TOKEN`.

### Локальный запуск MCP и агента
```bash
python -m venv .venv && source .venv/Scripts/activate  # в Git Bash на Windows
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-5
export GITHUB_REPOSITORY=Direct83/testAi
export BASE_BRANCH=main
export GITHUB_TOKEN=ghp_xxx  # персональный токен с правами repo

# MCP (Node) через Docker
docker build -t mcp-github -f mcp_node/Dockerfile mcp_node
docker run -d --name mcp-github-local --rm -p 8081:8080 -e GITHUB_TOKEN="$GITHUB_TOKEN" mcp-github:latest

export MCP_SERVER=http://127.0.0.1:8081

python agent/agent_mcp_github.py
```

### Автозапуск при push
Git‑hook уже подключён. Поведение:
- изменили `tasks/task1.md` → `git add/commit/push`;
- хук запускает агента через ваш локальный MCP;
- по успеху push продолжается, в GitHub появляется PR.

### Структура
- `agent/agent_mcp_github.py` — основной скрипт агента (генерация и PR через MCP)
- `agent/mcp_client.py` — минимальный MCP‑клиент по stdio
- `.github/workflows/agent.yml` — ручной запуск (workflow_dispatch), автозапуск по push выключен
- `tasks/task1.md` — входное ТЗ
- `requirements.txt` — зависимости агента
- `.gitignore`, `.env.example`

### Замечания
- Для работы требуется локальный MCP (Node) на 8081 и персональный токен с правами `repo`.

