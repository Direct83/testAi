import json

def main():
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    names = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'name' in item:
                val = item['name']
                if val is not None:
                    names.append(str(val))
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and 'name' in item:
                        val = item['name']
                        if val is not None:
                            names.append(str(val))

    with open('names.txt', 'w', encoding='utf-8') as out:
        out.write('\n'.join(names))

if __name__ == '__main__':
    main()