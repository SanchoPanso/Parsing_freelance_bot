import json
import os


def get_data_from_file(filename: str):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:  # file is empty
                data = dict()
    else:
        data = dict()
    return data


def insert_data_into_file(data: dict, filename: str):
    with open(filename, "w") as f:
        for key in data.keys():
            try:
                json.dump(data[key], f, indent=4, ensure_ascii=False)
            except UnicodeEncodeError:
                print('UnicodeEncodeError. Запись с ошибкой пропущена')


# with open("example.json", "w") as f:
#     json.dump({'1': 1}, f, indent=4, ensure_ascii=False)
#     json.dump({'1': 1}, f, indent=4, ensure_ascii=False)

