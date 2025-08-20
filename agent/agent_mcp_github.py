import os, re, pathlib, sys
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI
# Обеспечиваем корректный импорт при запуске как скрипт: `python agent/agent_mcp_github.py`
if __package__ is None or __package__ == "":
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from agent.mcp_client import MCPClient
from agent.mcp_http_client import MCPHttpClient

ROOT = pathlib.Path(__file__).resolve().parents[1]

def extract_filename(task_text: str) -> str:
    m = re.search(r'([A-Za-z0-9_\-./]+\.py)\b', task_text)
    return m.group(1) if m else "generated.py"

def strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        import re as _re
        m = _re.search(r"^```(?:python)?\s*([\s\S]*?)\s*```$", t, flags=_re.MULTILINE)
        if m:
            return m.group(1).strip()
    return t

def generate_code(task_text: str, model: str, api_key: str) -> Tuple[str, str]:
    client = OpenAI(api_key=api_key)
    out_name = extract_filename(task_text)
    prompt = (
        "Напиши полноценный рабочий Python-скрипт строго по ТЗ ниже.\n"
        "Выведи ТОЛЬКО исходный код файла, без markdown и текста вне кода.\n"
        f"Имя файла: {out_name}\n\nТЗ:\n{task_text}\n"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}]
    )
    raw = resp.choices[0].message.content or ""
    return out_name, strip_code_fences(raw)

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set", file=sys.stderr); sys.exit(2)
    model = os.getenv("OPENAI_MODEL","gpt-5")

    # читаем задание
    task_path = ROOT / "tasks" / "task1.md"
    if not task_path.exists():
        print("ERROR: tasks/task1.md not found", file=sys.stderr); sys.exit(3)
    task_text = task_path.read_text(encoding="utf-8")

    out_name, code = generate_code(task_text, model, api_key)

    # параметры репозитория/веток из env раннера
    repo_full = os.getenv("GITHUB_REPOSITORY", "")
    if "/" not in repo_full:
        print("ERROR: GITHUB_REPOSITORY is not set", file=sys.stderr); sys.exit(4)
    owner, repo = repo_full.split("/", 1)
    base_branch = os.getenv("BASE_BRANCH", os.getenv("GITHUB_REF_NAME","main"))
    # Уникальная ветка на каждый запуск, чтобы избежать 422 (PR уже существует)
    import time, random
    prefix = os.getenv("HEAD_BRANCH_PREFIX", "ai-mcp")
    ts = time.strftime("%Y%m%d-%H%M%S")
    rand = random.randint(1000, 9999)
    head_branch = f"{prefix}-{ts}-{rand}"

    # Приоритет: HTTP MCP сервер (локально в Docker) если MCP_SERVER задан,
    # иначе fallback на server-github через npx (stdio MCP).
    mcp_server = os.getenv("MCP_SERVER")
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is missing", file=sys.stderr); sys.exit(5)

    if mcp_server:
        # HTTP MCP (строгий режим, без fallback)
        http = MCPHttpClient(mcp_server, github_token=token)
        caps = http.capabilities()
        print("[agent] MCP capabilities:", caps)
        try:
            tools_list = http.tools_list()
            print("[agent] MCP tools:", tools_list)
        except Exception:
            tools_list = {}

        tools = []
        if isinstance(caps, dict) and caps.get("tools"):
            tools = caps["tools"]
        elif isinstance(tools_list, dict) and tools_list.get("tools"):
            tools = tools_list["tools"]

        t_create_branch = "create_branch"
        t_update_file = "create_or_update_file"
        t_create_pr = "create_pull_request"
        for t in tools:
            name = t if isinstance(t, str) else t.get("name")
            if not name:
                continue
            nlow = str(name).lower()
            if "branch" in nlow and "create" in nlow:
                t_create_branch = name
            if ("file" in nlow or "content" in nlow) and ("update" in nlow or "create" in nlow):
                t_update_file = name
            if ("pr" in nlow or "pull" in nlow) and "create" in nlow:
                t_create_pr = name

        http.tools_call(t_create_branch, {
            "owner": owner,
            "repo": repo,
            "branch": head_branch,
            "from_branch": base_branch
        })
        http.tools_call(t_update_file, {
            "owner": owner,
            "repo": repo,
            "path": out_name,
            "content": code,
            "message": f"feat(agent): add {out_name} from tasks",
            "branch": head_branch
        })
        pr = http.tools_call(t_create_pr, {
            "owner": owner,
            "repo": repo,
            "title": f"AI: {out_name} из tasks/task1.md",
            "body": "PR создан агентом через MCP GitHub server (HTTP). #ai-generated",
            "head": head_branch,
            "base": base_branch,
            "draft": False
        })
        print("PR created:", pr)
        return

    # Если MCP_SERVER не задан — сообщаем явно
    print("ERROR: MCP_SERVER не задан. Задайте MCP_SERVER=http://localhost:8080 и запустите снова.")
    sys.exit(7)

    # публикуем имя файла в GHA outputs (на всякий)
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a", encoding="utf-8") as f:
            print(f"generated_file={out_name}", file=f)

if __name__ == "__main__":
    main()


