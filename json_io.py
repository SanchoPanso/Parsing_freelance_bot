import json
import os


def get_data_from_file(filename: str):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):  # file is empty
                print(f"Возникли проблемы с открытием {filename}")
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



if __name__ == '__main__':
    print(get_data_from_file("example.json"))

