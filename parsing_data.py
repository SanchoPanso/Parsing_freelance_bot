import aiohttp
import asyncio
import lxml
import json
from bs4 import BeautifulSoup
import re
import time
import datetime
from config import headers, fl_ru_host, fl_ru_projects_url, html_examples_dir_path
from config import required_categories, required_words
import os
import sys
from exceptions import check_ddos_guard

# https://www.fl.ru/projects/?page=2&kind=1

timeout = aiohttp.ClientTimeout(total=30)
project_dict = dict()


def file_recording(file, html_text):
    for i in range(len(html_text)):
        try:
            file.write(html_text[i])
        except UnicodeEncodeError:
            pass


def get_timestamp(original_date_time):  # 2021-08-05T16:39:28+03:00     05.08.2021 | 14:24
    day = original_date_time[0:2]
    month = original_date_time[3:5]
    year = original_date_time[6:10]
    hour = original_date_time[13:15]
    minute = original_date_time[16:18]

    iso_date_time = f"{year}-{month}-{day}T{hour}:{minute}:00+03:00"
    # print(iso_date_time)

    date_time_from_iso = datetime.datetime.fromisoformat(iso_date_time)
    date_time = datetime.datetime.strftime(date_time_from_iso, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").timetuple())
    return timestamp


def get_first_link_number(soup: BeautifulSoup, page_number: int):
    """get the first link number which is the first not pinned project link"""
    first_link_number = 0
    if page_number == 1:
        label_of_pinned_orders = soup.find_all("span", string=re.compile('закреплен'))
        if len(label_of_pinned_orders) == 0:
            first_link_number = 0
        else:
            first_link_number = label_of_pinned_orders.text.split()[0]
        print(f'first_link_number {first_link_number}')
    return first_link_number


def get_project_links(soup: BeautifulSoup):
    """get project links"""
    project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                            "b-post__grid_title p-0",
                                                            "b-post__pin"])
    project_links = [i.find("a").get("href") for i in project_titles_with_links]
    return project_links


def get_project_info(soup: BeautifulSoup):
    title = soup.find("h1", class_="b-page__title").text
    description = soup.find_all("div", class_=["b-layout__txt", "b-layout__txt_padbot_20"])[7].text.strip()
    price = soup.find("span", class_="b-layout__bold").text.strip()  # may not work
    publishing_time = soup.find_all("div", class_=["b-layout__txt",
                                                   "b-layout__txt_padbot_20"])[-1].text.strip()[:18]
    timestamp = get_timestamp(publishing_time)
    return title, description, price, publishing_time, timestamp


def is_valid_project(soup: BeautifulSoup, title: str, description: str):
    project_categories_soup = soup.find_all("div", class_=["b-layout__txt",
                                                           "b-layout__txt_fontsize_11",
                                                           "b-layout__txt_padbot_20"])[-4]  # 9

    project_categories = [i.text for i in project_categories_soup.find_all("a")]
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

    final_condition = first_condition + second_condition
    return final_condition


async def parse_single_project(project_url, session: aiohttp.ClientSession, num):  # , required_categories=[]
    """
    Take data from a single page with a project description.
    !!!In case of updating site you need to review soup.find_all!!!
    """
    async with session.get(project_url, headers=headers) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, 'html.parser')

    project_id = project_url.split('/')[4]

    title, description, price, publishing_time, timestamp = get_project_info(soup)
    if is_valid_project(soup, title, description):
        project_dict[project_id] = {
            'timestamp': timestamp,
            'title': title,
            'description': description,
            'price': price
        }


async def parse_single_page_with_projects(page_url, page_number):
    kind = 1  # show only orders
    params = {'kind': kind, 'page': page_number}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(page_url, params=params, headers=headers) as resp:
                html = await resp.text()
        except Exception as exp:
            print(exp)
            sys.exit("Не удалось подключиться к сайту")

        soup = BeautifulSoup(html, 'html.parser')
        check_ddos_guard(soup)

        first_link_num = get_first_link_number(soup, page_number)
        project_links = get_project_links(soup)

        tasks = []
        for i in range(first_link_num, len(project_links)):
            # print(i)
            task = asyncio.create_task(parse_single_project(f"{fl_ru_host}{project_links[i]}", session, i + 1))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def check_news():
    return []   # not implemented

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(parse_single_page_with_projects(fl_ru_projects_url, 1))

    print(len(project_dict.keys()))

    with open('data.json', 'w') as file:
        json.dump(project_dict, file)   # срочно дописать
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())

# <title>
#    DDOS-GUARD
#   </title>