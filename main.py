import aiohttp
import asyncio
import lxml
from bs4 import BeautifulSoup
import time
import datetime
# https://www.fl.ru/projects/?page=2&kind=1

fl_ru_host = "https://www.fl.ru"
fl_ru_projects_url = "https://www.fl.ru/projects/"


def get_timestamp(original_date_time):       # 2021-08-05T16:39:28+03:00     05.08.2021 | 14:24
    day = original_date_time[0:2]
    month = original_date_time[3:5]
    year = original_date_time[6:10]
    hour = original_date_time[13:15]
    minute = original_date_time[16:18]

    iso_date_time = f"{year}-{month}-{day}T{hour}:{minute}:00+03:00"
    print(iso_date_time)

    date_time_from_iso = datetime.datetime.fromisoformat(iso_date_time)
    date_time = datetime.datetime.strftime(date_time_from_iso, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").timetuple())
    return timestamp


async def parse_single_project(project_url):            # , required_categories=[]
    """
    Take data from a single page with a project description.
    !!!In case of updating site you need to review soup.find_all!!!
    :param project_url:
    :param required_categories:
    :return:
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(project_url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'lxml')

            project_categories_soup = soup.find_all("div", class_=["b-layout__txt",
                                                                   "b-layout__txt_fontsize_11",
                                                                   "b-layout__txt_padbot_20"])[9]
            project_categories = [i.text for i in project_categories_soup.find_all("a")]

            title = soup.find("h1", class_="b-page__title").text
            description = soup.find_all("div", class_=["b-layout__txt", "b-layout__txt_padbot_20"])[7].text.strip()
            price = soup.find("span", class_="b-layout__bold").text.strip()  # may not work
            publishing_time = soup.find_all("div", class_=["b-layout__txt",
                                                           "b-layout__txt_padbot_20"])[12].text.strip()[:18]
            timestamp = get_timestamp(publishing_time)
            project_id = project_url.split('/')[4]
            # print(project_id)
            # print(title)
            # print(description)
            # print(price)

            print(timestamp)


async def parse_single_page_with_projects(page_url, page_number):
    kind = 1    # show only orders
    page = page_number
    params = {'kind': kind, 'page': page_number}
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url, params=params) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'lxml')

            if page_number == 1:
                num_of_pinned_orders = soup.find_all("span",
                                                     class_=["b-layout__txt",
                                                             "b-layout__txt_nowrap",
                                                             "b-layout__txt_color_323232"])[-1].text.split()[0]
                print(num_of_pinned_orders)


            project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                                    "b-post__grid_title p-0",
                                                                    "b-post__pin"])
            project_links = [i.find("a").get("href") for i in project_titles_with_links]
            for i in project_links:
                print(i)


async def main():
    required_categories = [['Программирование'],
                           ['Парсинг данных', 'Разработка Чат-ботов']]
    await parse_single_page_with_projects("https://www.fl.ru/projects/", 1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
