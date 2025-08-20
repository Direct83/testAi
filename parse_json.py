import json
import sys


def main():
    input_filename = "data.json"
    output_filename = "names.txt"

    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Ошибка: файл data.json не найден.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Ошибка: Ожидался JSON-массив в корне файла.", file=sys.stderr)
        sys.exit(1)

    names = []
    for item in data:
        if isinstance(item, dict) and "name" in item:
            value = item["name"]
            if value is None:
                continue
            names.append(str(value))

    try:
        with open(output_filename, "w", encoding="utf-8") as out:
            for name in names:
                out.write(name + "\n")
    except OSError as e:
        print(f"Ошибка записи в файл {output_filename}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()