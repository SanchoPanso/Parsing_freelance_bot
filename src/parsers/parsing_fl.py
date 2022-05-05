import aiohttp
import asyncio
from bs4 import BeautifulSoup
import datetime
import re
from src.config import headers
from src.config import fl_ru_host, fl_ru_projects_url
from src.config import required_categories, required_words
from src.config import paths
from src.parsers.parsing_common import Parser, ParsingResult
import logging

logger = logging.getLogger("App.FLParser")


class FLParser(Parser):
    async def parse_single_page_with_projects(self, page_url, page_number) -> ParsingResult:
        """start parsing of single projects placed in the page"""
        kind = 1  # this kind is needed to show only orders
        params = {'kind': kind, 'page': page_number}
        logger.debug(f"Parse page number{page_number}")
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.get(page_url, params=params, headers=headers) as resp:
                    html = await resp.text()
            except Exception as exp:
                print(exp)

            soup = BeautifulSoup(html, 'html.parser')
            if self.check_ddos_guard(soup):
                return ParsingResult.BLOCKED_BY_GUARD

            first_link_num = self.get_first_link_number(soup, page_number)
            project_links, project_marks = self.get_project_links_and_marks(soup)

            tasks = []
            for i in range(first_link_num, len(project_links)):
                # print(i)
                task = asyncio.create_task(self.parse_single_project(f"{fl_ru_host}{project_links[i]}",
                                                                     project_marks[i],
                                                                     session))
                tasks.append(task)
            await asyncio.gather(*tasks)

            return ParsingResult.SUCCESSFUL

    async def parse_single_project(self, project_url: str, project_mark: bool,
                                   session: aiohttp.ClientSession):
        """
        Take data from a single page with a project description.
        !!!In case of updating site you need to review soup.find_all!!!
        """
        project_id = project_url.split('/')[4]
        logger.debug(f"Parse project {project_id}")

        async with session.get(project_url, headers=headers) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

        project_info = self.get_project_info(soup)

        if None not in project_info:
            logger.debug(f"Project {project_id} successfully parsed")
            title, description, price, publishing_time, timestamp, project_categories = project_info
            self.project_dict[project_id] = {
                'timestamp': timestamp,
                'publishing_time': publishing_time,
                'url': project_url,
                'title': title,
                'description': description,
                'price': price,
                'project_categories': project_categories,
            }
        else:
            logger.debug(f"Project {project_id} didn't successfully parsed")

    def is_valid_project(self, project_info: dict) -> bool:
        """check whether the project matches the required conditions"""
        project_categories = project_info['project_categories']
        title = project_info['title']
        description = project_info['description']
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

    def format_new(self, new: dict):
        formatted_new = f"<a href = \'{new['url']}\'>{new['title']}</a>\n" \
                        f"{new['description']}\n" \
                        f"{new['publishing_time']}"
        return formatted_new

    def update_cond_for_cycle_ending(self):
        keys = self.project_dict.keys()
        if len(keys) > 0:
            time_of_the_oldest_project = min([self.project_dict[key]['timestamp'] for key in keys])
            self.end_point_is_not_reached = time_of_the_oldest_project > self.last_checking_time

    def check_ddos_guard(self, soup: BeautifulSoup) -> bool:
        """check whether the page is a ddos-guard page"""
        title = soup.find('title')
        if title.text.strip() == 'DDOS-GUARD':
            return True
        return False

    def get_timestamp(self, original_date_time_format: str) -> float:
        """get timestamp from time like this: '05.08.2021 | 14:24'"""
        day = int(original_date_time_format[0:2])
        month = int(original_date_time_format[3:5])
        year = int(original_date_time_format[6:10])
        hour = int(original_date_time_format[13:15])
        minute = int(original_date_time_format[16:18])

        timestamp = datetime.datetime(year, month, day, hour, minute, 0).timestamp()
        return timestamp

    def get_first_link_number(self, soup: BeautifulSoup, page_number: int) -> int:
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

    def get_project_links_and_marks(self, soup: BeautifulSoup):
        """get project links"""
        project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                                "b-post__grid_title p-0",
                                                                "b-post__pin"])
        project_links = [i.find("a").get("href") for i in project_titles_with_links]

        project_divs_with_marks = soup.find_all('div', class_=['b-post',
                                                               'b-post_padbot_15',
                                                               'b-post_margbot_20',
                                                               'b-post_bordbot_eee',
                                                               'b-post_relative'])

        project_marks = [i.find('i') is not None for i in project_divs_with_marks]
        return project_links, project_marks

    def get_project_info(self, soup: BeautifulSoup) -> tuple:
        """
        get title, description, price, publishing_time, timestamp, project_categories from the soup of a project
        """
        title = self.get_title(soup)
        description = self.get_description(soup)
        price = self.get_price(soup)
        publishing_time, timestamp = self.get_publishing_time_and_timestamp(soup)
        project_categories = self.get_project_categories(soup)

        return title, description, price, publishing_time, timestamp, project_categories

    def get_title(self, soup: BeautifulSoup) -> str or None:
        title_soup = soup.find("h1", class_="b-page__title")
        if title_soup is None:
            title = None
        else:
            title = title_soup.text.strip()
        return title

    def get_description(self, soup: BeautifulSoup) -> str or None:
        description_soup_list = soup.find_all("div",
                                              class_=["b-layout__txt",
                                                      "b-layout__txt_padbot_20"])

        if len(description_soup_list) == 0:
            description = None
        else:
            description = description_soup_list[7].text.strip()
        return description

    def get_price(self, soup: BeautifulSoup) -> str or None:
        price_soup = soup.find("span", class_="b-layout__bold")
        if price_soup is None:
            price = None
        else:
            price = price_soup.text.strip()
        return price

    def get_publishing_time_and_timestamp(self, soup: BeautifulSoup) -> tuple:
        publishing_time_soup = soup.find_all("div", class_=["b-layout__txt",
                                                            "b-layout__txt_padbot_20"])
        if len(publishing_time_soup) == 0:
            publishing_time = None
            timestamp = None
        else:
            publishing_time = publishing_time_soup[-1].text.strip()[:18]
            timestamp = self.get_timestamp(publishing_time)
        return publishing_time, timestamp

    def get_project_categories(self, soup: BeautifulSoup) -> str or None:
        project_categories_soup_list = soup.find_all("div", class_=["b-layout__txt",
                                                                    "b-layout__txt_fontsize_11",
                                                                    "b-layout__txt_padbot_20"])
        if len(project_categories_soup_list) == 0:
            project_categories = []
        else:
            project_categories_soup = project_categories_soup_list[-4]  # 9
            project_categories = [i.text for i in project_categories_soup.find_all("a")]
        return project_categories


async def fl_parser_test():
    fl_parser = FLParser(fl_ru_projects_url, paths['project_data_file_path'])
    while True:
        print("начало парсинга новостей")
        news_list = await fl_parser.check_news()
        print("новости спарсены")
        for i in news_list:
            print(i)
        await asyncio.sleep(5)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fl_parser_test())
