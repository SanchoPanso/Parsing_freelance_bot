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


def write_data_into_file(data: dict, filename: str):
    with open(filename, "w") as f:
        try:
            json.dump(data, f, indent=4, ensure_ascii=False)
        except UnicodeEncodeError:
            print('UnicodeEncodeError. Не удалось записать данные')


# with open("example.json", "w") as f:
#     json.dump({'1': 1}, f, indent=4, ensure_ascii=False)
#     json.dump({'1': 1}, f, indent=4, ensure_ascii=False)

