import os
import re
import pathlib
import sys
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parents[1]

def extract_filename(task_text: str) -> str:
    """
    Берём первое упоминание *.py из ТЗ. Если нет — generated.py
    """
    m = re.search(r'([A-Za-z0-9_\-./]+\.py)\b', task_text)
    return m.group(1) if m else "generated.py"

def strip_code_fences(text: str) -> str:
    """
    Убираем ```python ... ``` если модель так ответила.
    """
    t = text.strip()
    if t.startswith("```"):
        m = re.search(r"^```(?:python)?\s*([\s\S]*?)\s*```$", t, flags=re.MULTILINE)
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
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    raw = resp.choices[0].message.content or ""
    return out_name, strip_code_fences(raw)

def main():
    load_dotenv()  # локально — берём из .env; в Actions — из Secrets
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(2)
    model = os.getenv("OPENAI_MODEL", "gpt-5")

    task_path = ROOT / "tasks" / "task1.md"
    if not task_path.exists():
        print("ERROR: tasks/task1.md not found", file=sys.stderr)
        sys.exit(3)

    task_text = task_path.read_text(encoding="utf-8")
    out_name, code = generate_code(task_text, model, api_key)

    out_path = ROOT / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    print(f"Сгенерирован файл: {out_name}")

    # Сообщаем имя файла в GitHub Actions (для create-pull-request add-paths)
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a", encoding="utf-8") as f:
            print(f"generated_file={out_name}", file=f)

if __name__ == "__main__":
    main()


