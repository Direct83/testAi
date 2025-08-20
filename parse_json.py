import json
import sys


def main():
    data_file = "data.json"
    output_file = "names.txt"

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Ошибка: Файл '{data_file}' не найден.\n")
        sys.exit(1)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Ошибка: Некорректный JSON в файле '{data_file}': {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Ошибка при чтении файла '{data_file}': {e}\n")
        sys.exit(1)

    if not isinstance(data, list):
        sys.stderr.write("Ошибка: Ожидается JSON-массив в корне файла.\n")
        sys.exit(1)

    names = []
    for item in data:
        if isinstance(item, dict) and "name" in item:
            value = item["name"]
            if value is not None:
                names.append(str(value))

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            if names:
                f.write("\n".join(names) + "\n")
            else:
                # Пустой файл, если имен нет
                f.write("")
    except Exception as e:
        sys.stderr.write(f"Ошибка при записи в файл '{output_file}': {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()