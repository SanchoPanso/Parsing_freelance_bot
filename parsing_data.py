import aiohttp
import asyncio
import lxml
import json
from bs4 import BeautifulSoup
import time
import datetime
from config import headers, fl_ru_host, fl_ru_projects_url, required_categories, html_examples_dir_path

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


async def parse_single_project(project_url, session: aiohttp.ClientSession, num):  # , required_categories=[]
    """
    Take data from a single page with a project description.
    !!!In case of updating site you need to review soup.find_all!!!
    """
    async with session.get(project_url, headers=headers) as resp:
        await asyncio.sleep(1)
        html = await resp.text()
        binary = await resp.content.read()
        soup = BeautifulSoup(html, 'lxml')

        project_id = project_url.split('/')[4]

        # доработать срочно!!!
        project_categories_soup = soup.find_all("div", class_=["b-layout__txt",
                                                               "b-layout__txt_fontsize_11",
                                                               "b-layout__txt_padbot_20"])[-4]  # 9
        # print(project_categories_soup)
        project_categories = [i.text for i in project_categories_soup.find_all("a")]

        try:
            if (project_categories[0] not in required_categories[0]) or \
                    (project_categories[1] not in required_categories[1]):
                print("Отклонено")
                with open(f"{html_examples_dir_path}\\project_{project_id}(canceled).html", "w") as f:
                    file_recording(f, html)
                return
        except Exception as e:
            print(e)
            with open(f"{html_examples_dir_path}\\project_{project_id}(with_error).html", "w") as f:
                file_recording(f, html)
            return

        with open(f"{html_examples_dir_path}\\project_{project_id}.html", "w") as f:
            file_recording(f, html)

        title = soup.find("h1", class_="b-page__title").text
        description = soup.find_all("div", class_=["b-layout__txt", "b-layout__txt_padbot_20"])[7].text.strip()
        price = soup.find("span", class_="b-layout__bold").text.strip()  # may not work
        publishing_time = soup.find_all("div", class_=["b-layout__txt",
                                                       "b-layout__txt_padbot_20"])[-1].text.strip()[:18]
        timestamp = get_timestamp(publishing_time)
        project_dict[project_id] = {
            'timestamp': timestamp,
            'title': title,
            'description': description,
            'price': price
        }
        # print(title)
        # print(f"Обработана {num} запись")


async def parse_single_page_with_projects(page_url, page_number):
    kind = 1  # show only orders
    params = {'kind': kind, 'page': page_number}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(page_url, params=params, headers=headers) as resp:
            time.sleep(2)
            html = await resp.text()
            binary = await resp.content.read()
            soup = BeautifulSoup(html, 'lxml')
            # print(soup)

            with open(f"{html_examples_dir_path}\\page_number_{page_number}.html", "w") as f:
                file_recording(f, html)

            first_link_num = 0
            if page_number == 1:
                num_of_pinned_orders = soup.find_all("span",
                                                     class_=["b-layout__txt",
                                                             "b-layout__txt_nowrap",
                                                             "b-layout__txt_color_323232"])  # [-1].text.split()[0]
                print(num_of_pinned_orders)
                first_link_num = 0

            project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                                    "b-post__grid_title p-0",
                                                                    "b-post__pin"])
            project_links = [i.find("a").get("href") for i in project_titles_with_links]

            tasks = list()
            for i in range(first_link_num, len(project_links)):
                # print(i)
                task = asyncio.create_task(parse_single_project(f"{fl_ru_host}{project_links[i]}", session, i + 1))
                tasks.append(task)
            await asyncio.gather(*tasks)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(parse_single_page_with_projects(fl_ru_projects_url, 1))

    print(len(project_dict.keys()))

    with open('data.json', 'w') as file:
        json.dump(project_dict, file)


if __name__ == '__main__':
    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())

# <title>
#    DDOS-GUARD
#   </title>