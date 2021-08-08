import asyncio
import json
from parsing_data import parse_single_project, parse_single_page_with_projects, project_dict
from config import fl_ru_projects_url


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(parse_single_page_with_projects(fl_ru_projects_url, 1))

    print(len(project_dict.keys()))

    with open('data.json', 'w') as file:
        json.dump(project_dict, file)   # срочно дописать


if __name__ == '__main__':
    main()
