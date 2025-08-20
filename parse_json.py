import json
import sys


def main():
    data_file = "data.json"
    output_file = "names.txt"

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: файл '{data_file}' не найден.", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора JSON в '{data_file}': {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка при чтении '{data_file}': {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Ошибка: ожидается, что корневой элемент JSON — массив объектов.", file=sys.stderr)
        return 1

    names = []
    for idx, item in enumerate(data):
        if isinstance(item, dict) and "name" in item:
            value = item.get("name")
            if value is not None:
                names.append(str(value))

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            if names:
                f.write("\n".join(names) + "\n")
            else:
                f.write("")
    except Exception as e:
        print(f"Ошибка при записи в '{output_file}': {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())