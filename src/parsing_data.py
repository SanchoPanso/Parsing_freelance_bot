import aiohttp
import asyncio
from bs4 import BeautifulSoup
from src.config import headers, fl_ru_host, fl_ru_projects_url
from src.config import paths
from src.config import required_categories, required_words
import datetime
import re
import sys
import time
from src.json_io import get_data_from_file, write_data_into_file
from enum import Enum

timeout = aiohttp.ClientTimeout(total=30)
project_dict = dict()
last_checking_time = None


class ParsingResult(Enum):
    SUCCESSFULLY = 0
    BLOCKED_BY_GUARD = 1


def file_recording(file, html_text):
    for i in range(len(html_text)):
        try:
            file.write(html_text[i])
        except UnicodeEncodeError:
            pass


def check_ddos_guard(soup: BeautifulSoup) -> bool:
    """check whether the page is a ddos-guard page"""
    title = soup.find('title')
    if title.text.strip() == 'DDOS-GUARD':
        return True
    return False


def get_timestamp(original_date_time_format: str) -> float:
    """get timestamp from time like this: '05.08.2021 | 14:24'"""
    day = int(original_date_time_format[0:2])
    month = int(original_date_time_format[3:5])
    year = int(original_date_time_format[6:10])
    hour = int(original_date_time_format[13:15])
    minute = int(original_date_time_format[16:18])

    timestamp = datetime.datetime(year, month, day, hour, minute, 0).timestamp()
    return timestamp


def get_first_link_number(soup: BeautifulSoup, page_number: int) -> int:
    """get the first link number which is the first not pinned project link"""
    first_link_number = 0
    if page_number == 1:
        label_of_pinned_orders = soup.find_all("span", string=re.compile('закреплен'))
        if len(label_of_pinned_orders) == 0:
            first_link_number = 0
        else:
            first_link_number = int(label_of_pinned_orders[0].text.split()[0])
        # print(f'first_link_number {first_link_number}')
    return first_link_number


def get_project_links(soup: BeautifulSoup) -> list:
    """get project links"""
    project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                            "b-post__grid_title p-0",
                                                            "b-post__pin"])
    project_links = [i.find("a").get("href") for i in project_titles_with_links]
    return project_links


def get_project_info(soup: BeautifulSoup) -> tuple:
    """
    get title, description, price, publishing_time, timestamp, project_categories from the soup of a project
    """
    try:
        title = soup.find("h1", class_="b-page__title").text.strip()
    except:
        title = None
    try:
        description = soup.find_all("div", class_=["b-layout__txt", "b-layout__txt_padbot_20"])[7].text.strip()
    except:
        description = None
    try:
        price = soup.find("span", class_="b-layout__bold").text.strip()  # may not work
    except:
        price = None
    try:
        publishing_time = soup.find_all("div", class_=["b-layout__txt",
                                                       "b-layout__txt_padbot_20"])[-1].text.strip()[:18]
        timestamp = get_timestamp(publishing_time)
    except:
        publishing_time = None
        timestamp = None
    try:
        project_categories_soup = soup.find_all("div", class_=["b-layout__txt",
                                                               "b-layout__txt_fontsize_11",
                                                               "b-layout__txt_padbot_20"])[-4]  # 9
        project_categories = [i.text for i in project_categories_soup.find_all("a")]
    except:
        project_categories = []
    return title, description, price, publishing_time, timestamp, project_categories


def is_valid_project(project_categories: list, title: str, description: str) -> bool:
    """check whether the project matches the required conditions"""
    first_condition = False
    if len(project_categories) == 2:
        if project_categories[0] in required_categories[0]:
            if project_categories[1] in required_categories[1]:
                first_condition = True

    second_condition = False
    text = f"{title} {description}".lower()
    for word in required_words:
        if re.match(word, text):
            second_condition = True
            break

    final_condition = first_condition or second_condition
    return final_condition


async def parse_single_project(project_url: str, session: aiohttp.ClientSession):
    """
    Take data from a single page with a project description.
    !!!In case of updating site you need to review soup.find_all!!!
    """
    async with session.get(project_url, headers=headers) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, 'html.parser')

    project_id = project_url.split('/')[4]

    project_info = get_project_info(soup)

    if None not in project_info:
        title, description, price, publishing_time, timestamp, project_categories = project_info
        project_dict[project_id] = {
            'timestamp': timestamp,
            'publishing_time': publishing_time,
            'url': project_url,
            'title': title,
            'description': description,
            'price': price,
            'project_categories': project_categories,
            }


async def parse_single_page_with_projects(page_url, page_number):
    """start parsing of single projects placed in the page"""
    kind = 1  # this kind is needed to show only orders
    params = {'kind': kind, 'page': page_number}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(page_url, params=params, headers=headers) as resp:
                html = await resp.text()
        except Exception as exp:
            print(exp)
            sys.exit("Не удалось подключиться к сайту")

        soup = BeautifulSoup(html, 'html.parser')
        if check_ddos_guard(soup):
            return ParsingResult.BLOCKED_BY_GUARD    # ddos guard

        first_link_num = get_first_link_number(soup, page_number)
        project_links = get_project_links(soup)

        tasks = []
        for i in range(first_link_num, len(project_links)):
            # print(i)
            task = asyncio.create_task(parse_single_project(f"{fl_ru_host}{project_links[i]}", session))
            tasks.append(task)
        await asyncio.gather(*tasks)

        return ParsingResult.SUCCESSFULLY    # success


async def check_news():
    global project_dict
    global last_checking_time
    project_dict_from_file = get_data_from_file(paths['project_data_file_path'])
    news_list = []

    max_time_lag = 5*60*60
    current_time = time.time()
    if last_checking_time is None:
        last_checking_time = current_time - max_time_lag

    page_number = 1
    end_point_is_not_reached = True
    while end_point_is_not_reached:

        result = await parse_single_page_with_projects(fl_ru_projects_url, page_number)
        if result == 1:
            return news_list, 1

        keys = project_dict.keys()
        time_of_the_oldest_project = min([project_dict[key]['timestamp'] for key in keys])
        end_point_is_not_reached = time_of_the_oldest_project > last_checking_time
        for key in keys:
            if is_valid_project(project_dict[key]['project_categories'],
                                project_dict[key]['title'],
                                project_dict[key]['description']):
                if key not in project_dict_from_file.keys():
                    news_list.append(project_dict[key])
                    project_dict_from_file[key] = project_dict[key]
        page_number += 1

    last_checking_time = current_time
    write_data_into_file(project_dict_from_file, paths['project_data_file_path'])
    project_dict = dict()
    return news_list, 0


async def unit_test():
    while True:
        print("начало парсинга новостей")
        news_list = await check_news()
        print("новости спарсены")
        for i in news_list:
            print(i)
        await asyncio.sleep(5)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unit_test())
