import json

def main():
    input_filename = 'data.json'
    output_filename = 'names.txt'

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create/overwrite output file even if input is missing or invalid
        with open(output_filename, 'w', encoding='utf-8'):
            pass
        return

    names = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'name' in item:
                value = item['name']
                if value is not None:
                    names.append(str(value))

    with open(output_filename, 'w', encoding='utf-8') as out:
        if names:
            out.write('\n'.join(names) + '\n')

if __name__ == '__main__':
    main()