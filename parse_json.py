import json
import sys
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "data.json"
    output_path = base_dir / "names.txt"

    try:
        with input_path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"Ошибка разбора JSON в {input_path}: {e}\n")
                sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write(f"Файл не найден: {input_path}\n")
        sys.exit(1)
    except OSError as e:
        sys.stderr.write(f"Ошибка чтения файла {input_path}: {e}\n")
        sys.exit(1)

    if not isinstance(data, list):
        sys.stderr.write("Ожидался массив JSON в корне файла data.json\n")
        sys.exit(1)

    names = []
    for item in data:
        if isinstance(item, dict) and "name" in item:
            val = item["name"]
            names.append("" if val is None else str(val))

    try:
        with output_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(names))
            if names:
                f.write("\n")
    except OSError as e:
        sys.stderr.write(f"Ошибка записи файла {output_path}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()