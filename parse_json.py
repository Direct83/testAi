import json
from pathlib import Path


def main():
    data_file = Path('data.json')
    output_file = Path('names.txt')

    try:
        with data_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file missing or invalid JSON, create/overwrite empty names.txt
        output_file.write_text('', encoding='utf-8')
        return

    names = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'name' in item and item['name'] is not None:
                names.append(str(item['name']))
    elif isinstance(data, dict):
        # Fallback: try common container keys if root is not an array
        for key in ('items', 'data', 'results'):
            arr = data.get(key)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict) and 'name' in item and item['name'] is not None:
                        names.append(str(item['name']))
                break

    output_file.write_text('\n'.join(names), encoding='utf-8')


if __name__ == '__main__':
    main()