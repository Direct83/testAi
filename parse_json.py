import json
import sys


INPUT_FILE = "data.json"
OUTPUT_FILE = "names.txt"


def extract_names(data):
    names = []
    for item in data:
        if isinstance(item, dict) and "name" in item and item["name"] is not None:
            names.append(str(item["name"]))
    return names


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Ошибка: файл '{INPUT_FILE}' не найден.\n")
        return 1
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Ошибка: некорректный JSON в '{INPUT_FILE}': {e}\n")
        return 1
    except OSError as e:
        sys.stderr.write(f"Ошибка при чтении '{INPUT_FILE}': {e}\n")
        return 1

    if not isinstance(data, list):
        sys.stderr.write("Ошибка: ожидается JSON-массив в корне файла.\n")
        return 1

    names = extract_names(data)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            if names:
                f.write("\n".join(names) + "\n")
            else:
                # Пустой файл, если имён не найдено
                f.write("")
    except OSError as e:
        sys.stderr.write(f"Ошибка при записи в '{OUTPUT_FILE}': {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())