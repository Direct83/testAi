import os
import re
import pathlib
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parents[1]

def extract_filename(task_text: str) -> str:
    m = re.search(r'([A-Za-z0-9_\-./]+\.py)\b', task_text)
    return m.group(1) if m else "generated.py"

def strip_code_fences(text: str) -> str:
    # Убираем ```python ... ``` если модель так ответила
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:python)?\s*([\s\S]*?)\s*```$", r"\1", text, flags=re.MULTILINE)
    return text

def build_prompt(task_text: str, output_file: str) -> str:
    return (
        "Напиши полноценный рабочий Python-скрипт строго по ТЗ ниже.\n"
        "Выведи ТОЛЬКО исходный код файла, без markdown и без пояснений вне кода.\n"
        f"Файл должен называться: {output_file}\n\n"
        f"ТЗ:\n{task_text}\n"
    )

def generate_code(task_text: str, model: str, api_key: str):
    client = OpenAI(api_key=api_key)
    output_file = extract_filename(task_text)
    prompt = build_prompt(task_text, output_file)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.choices[0].message.content or ""
    code = strip_code_fences(raw)
    return output_file, code

def main():
    # Локальный .env (в Actions используем secrets)
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    task_path = ROOT / "tasks" / "task1.md"
    if not task_path.exists():
        raise FileNotFoundError("tasks/task1.md не найден")

    task_text = task_path.read_text(encoding="utf-8")
    out_name, code = generate_code(task_text, model, api_key)

    out_path = ROOT / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    print(f"Сгенерирован файл: {out_name}")

if __name__ == "__main__":
    main()


