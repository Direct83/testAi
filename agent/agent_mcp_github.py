import os, re, pathlib, sys
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI
from agent.mcp_client import MCPClient

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
    run_id = os.getenv("GITHUB_RUN_ID", "local")
    head_branch = f"ai-mcp-{run_id}"

    # Запускаем GitHub MCP server через npx; токен Actions маппим в ожидаемую переменную
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is missing", file=sys.stderr); sys.exit(5)

    mcp = MCPClient(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": token}
    )

    try:
        # 1) создаём ветку от base (если её нет)
        mcp.tools_call("create_branch", {
            "owner": owner,
            "repo": repo,
            "branch": head_branch,
            "from_branch": base_branch
        })

        # 2) кладём (создаём/обновляем) файл в ветке
        mcp.tools_call("create_or_update_file", {
            "owner": owner,
            "repo": repo,
            "path": out_name,
            "content": code,
            "message": f"feat(agent): add {out_name} from tasks",
            "branch": head_branch
        })

        # 3) создаём PR
        pr = mcp.tools_call("create_pull_request", {
            "owner": owner,
            "repo": repo,
            "title": f"AI: {out_name} из tasks/task1.md",
            "body": "PR создан агентом через MCP GitHub server. #ai-generated",
            "head": head_branch,
            "base": base_branch,
            "draft": False
        })
        print("PR created:", pr)

    finally:
        mcp.close()

    # публикуем имя файла в GHA outputs (на всякий)
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a", encoding="utf-8") as f:
            print(f"generated_file={out_name}", file=f)

if __name__ == "__main__":
    main()


