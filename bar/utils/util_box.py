import json
import jsonlines
from typing import List


def read_json(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as f:
        data = json.load(f)
    print('read json file: %s' % file_path)
    return data


def write_json(file_path, data, encoding='utf-8'):
    with open(file_path, 'w', encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False)
    print('write json file: %s' % file_path)


def read_jsonl(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as f:
        data = [json.loads(line) for line in f]
    print('read jsonl file: %s' % file_path)
    return data


def write_jsonl(file_path, data: List, encoding='utf-8'):
    with jsonlines.open(file_path, mode='w') as writer:
        for item in data:
            writer.write(item)
    print('write jsonl file: %s' % file_path)


def read_txt(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as f:
        data = f.read()
    print('read txt file: %s' % file_path)
    return data


def save_txt(file_path, data, encoding='utf-8'):
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(data)
    print('write txt file: %s' % file_path)


def save_txt_append(file_path, data, encoding='utf-8'):
    with open(file_path, 'a', encoding=encoding) as f:
        f.write(data)
    print('write txt file: %s' % file_path)
