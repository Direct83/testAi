import json
import sys


def main():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.stderr.write('Ошибка: файл data.json не найден.\n')
        sys.exit(1)
    except json.JSONDecodeError as e:
        sys.stderr.write(f'Ошибка: не удалось разобрать JSON: {e}\n')
        sys.exit(1)

    if not isinstance(data, list):
        sys.stderr.write('Ошибка: корневой элемент JSON должен быть массивом.\n')
        sys.exit(1)

    names = []
    for item in data:
        if isinstance(item, dict) and 'name' in item:
            names.append(str(item['name']))

    try:
        with open('names.txt', 'w', encoding='utf-8') as out:
            out.write('\n'.join(names))
    except OSError as e:
        sys.stderr.write(f'Ошибка записи в файл names.txt: {e}\n')
        sys.exit(1)


if __name__ == '__main__':
    main()