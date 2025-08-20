import os, json, pathlib, sys, subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
# Обеспечиваем корректный импорт при запуске как скрипт: `python agent/run.py`
if __package__ is None or __package__ == "":
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from agent.mcp import BashMCP

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "agent" / "prompts"
OUTPUT = ROOT / "output"
TASKS = ROOT / "tasks"

class Plan(BaseModel):
    steps: List[str]
    libraries: List[str]
    edge_cases: List[str]
    tests: List[Dict[str, str]]
    cli: Dict[str, Any]

class FilesPack(BaseModel):
    files: List[Dict[str, str]]

def render_prompt(path: pathlib.Path, **vars) -> str:
    text = path.read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace(f"{{{{{k}}}}}", v)
    return text

def ask(client: OpenAI, content: str) -> str:
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL","gpt-5"),
        messages=[{"role":"user","content":content}]
    )
    return resp.choices[0].message.content or ""

def main():
    load_dotenv()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY не задан. Создайте .env и укажите ключ.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    raw_tz = (TASKS / "task1.md").read_text(encoding="utf-8")

    # Релиз 0: анализ ТЗ → plan.json
    analyze = render_prompt(PROMPTS / "analyze.md", RAW_TZ=raw_tz)
    plan_text = ask(client, analyze)
    plan = Plan.model_validate_json(plan_text)
    (OUTPUT / "plan.json").write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    # Релиз 1: генерация кода → файлы
    codegen = render_prompt(PROMPTS / "codegen.md", PLAN_JSON=plan.model_dump_json())
    files_json = ask(client, codegen)
    pack = FilesPack.model_validate_json(files_json)

    for f in pack.files:
        p = ROOT / f["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"], encoding="utf-8")

    # Установка зависимостей и pytest локально (без MCP) для надёжности
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=str(ROOT), check=False)
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=str(ROOT), check=False)

    # Релиз 2: ветка/коммит/push/PR через gh (можно пропустить через SKIP_PR=1)
    if os.environ.get("SKIP_PR", "0") != "1":
        branch = os.environ.get("GIT_BRANCH","feat/excel-mean-agent")
        base = os.environ.get("BASE_BRANCH","main")

        bash = BashMCP()
        try:
            bash.exec(f"git checkout -b {branch} || git checkout {branch}", cwd=str(ROOT))
            bash.exec("git add .", cwd=str(ROOT))
            bash.exec('git commit -m "feat: excel mean script (agent-generated)" || true', cwd=str(ROOT))
            bash.exec(f"git push --set-upstream origin {branch}", cwd=str(ROOT))

            file_list = ", ".join([f['path'] for f in pack.files])
            run_cmd = "python process_data.py --input sample.xlsx --column Price"
            tests_list = "\n".join([f"- {t.get('name','test')}" for t in plan.tests])

            pr_prompt = render_prompt(PROMPTS / "pr.md",
                                      RAW_TZ=raw_tz,
                                      FILE_LIST=file_list,
                                      RUN=run_cmd,
                                      TESTS=tests_list)
            pr_body = ask(client, pr_prompt)
            (OUTPUT / "pr_body.txt").write_text(pr_body, encoding="utf-8")

            title = "feat: Excel mean script (agent-generated)"
            bash.exec(f'gh pr create --title "{title}" --body-file output/pr_body.txt --base {base} --head {branch}', cwd=str(ROOT))
        finally:
            bash.close()

    # Без emoji для совместимости с консольной кодировкой Windows
    print("Готово: создан PR.")

if __name__ == "__main__":
    main()

