# AI‑агент по ТЗ: план → код → тесты → Pull Request

Минимальный рабочий прототип агента, который читает техническое задание, строит план реализации, генерирует Python‑код и тесты, запускает их локально и открывает Pull Request в GitHub.

## Что делает агент
1. Читает текстовое ТЗ из `tasks/task1.md`.
2. Анализирует ТЗ по промпту `agent/prompts/analyze.md` и сохраняет план в `output/plan.json`.
3. Генерирует рабочие файлы (код и тесты) по промпту `agent/prompts/codegen.md` и кладёт их в репозиторий.
4. Запускает `pytest` локально.
5. Создаёт ветку, коммит, пуш и Pull Request через `gh` CLI, формируя тело PR по `agent/prompts/pr.md` (сохраняется также в `output/pr_body.txt`).

В составе есть и упрощённый режим — генерация ровно одного файла из ТЗ (`agent/agent.py`).

## Требования
- Python 3.11+
- Node.js 18+ и npm (для запуска MCP `@modelcontextprotocol/server-bash` через `npx`)
- Git и `gh` CLI, настроенный и аутентифицированный (`gh auth login`)
- Настроенный `origin` на GitHub-репозиторий (права на push)
- Переменные окружения:
  - `OPENAI_API_KEY` — ключ OpenAI (обязателен)
  - `OPENAI_MODEL` — модель чата (по умолчанию берётся из `.env`, рекомендуется `gpt-4o-mini`)
  - `GIT_BRANCH` — имя ветки для PR (по умолчанию `feat/excel-mean-agent`)
  - `BASE_BRANCH` — базовая ветка PR (по умолчанию `main`)
  - `SKIP_PR=1` — чтобы пропустить создание PR (полезно для локальной отладки)

Пример `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
GIT_BRANCH=feat/excel-mean-agent
BASE_BRANCH=main
```

## Установка
Рекомендуется использовать виртуальное окружение Python.

```
python -m venv .venv
# Windows (Git Bash):
source .venv/Scripts/activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements-agent.txt
```

> Файл `requirements.txt` используется для зависимостей СГЕНЕРИРОВАННОГО кода. Агент самостоятельно выполнит `pip install -r requirements.txt`, если это потребуется.

## Запуск

### Быстрый режим (один файл по ТЗ)
Сгенерировать один Python‑файл из `tasks/task1.md`:
```
python agent/agent.py
```
Скрипт сохранит файл с именем, найденным в ТЗ (или `generated.py`) и выведет: `Сгенерирован файл: <имя>`.

### Полный пайплайн (план → код → тесты → PR)
```
python agent/run.py
```
Что произойдёт:
- `output/plan.json` — план реализации;
- Созданы файлы по плану (код и тесты);
- Установлены зависимости из `requirements.txt` (если есть);
- Прогнан `pytest -q`;
- Создана ветка, коммит, пуш и Pull Request в GitHub (если не задан `SKIP_PR=1`).

Чтобы пропустить создание PR (например, без настроенного `origin`):
```
SKIP_PR=1 python agent/run.py
```

## Структура
- `agent/agent.py` — простой генератор одного файла по ТЗ
- `agent/run.py` — основной оркестратор пайплайна
- `agent/mcp.py` — минимальный клиент MCP по stdio для `@modelcontextprotocol/server-bash`
- `agent/prompts/analyze.md` — промпт для анализа ТЗ → план
- `agent/prompts/codegen.md` — промпт для генерации файлов
- `agent/prompts/pr.md` — шаблон тела PR
- `tasks/task1.md` — входное ТЗ
- `output/` — сюда сохраняются артефакты (`plan.json`, `pr_body.txt` и пр.)

## Примечания по MCP и PR
- MCP‑сервер `@modelcontextprotocol/server-bash` запускается через `npx` внутри `agent/mcp.py`.
- Для PR необходимы:
  - настроенный git‑remote `origin` на GitHub;
  - `gh auth login` (или переменная `GH_TOKEN`/`GITHUB_TOKEN`).

## Частые вопросы
- Ошибка 400 про `temperature`: в коде агента параметр не передаётся. Убедитесь, что используете совместимую модель (например, `gpt-4o-mini`).
- Нет PR/ошибка `gh`: проверьте `gh auth login` и что установлен `origin` (`git remote -v`).

