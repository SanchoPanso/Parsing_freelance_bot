import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
import re
from src.json_io import get_data_from_file, write_data_into_file
from src.config import paths
from src.parsers.parsing_common import Parser, ParsingResult
import logging

kwork_host = "https://kwork.ru"
kwork_project_url = "https://kwork.ru/projects"

logger = logging.getLogger("App.KworkParser")


class KworkParser(Parser):
    async def check_news(self) -> tuple:
        """
        Method for checking news in the certain site
        :return: tuple of list with news and return code
        """
        logging.info('Checking news started')
        # create dict that is a copy of data in project_data_file
        self.project_dict_from_file = get_data_from_file('parsers\\project_data_dir\\project_data.json')
        # create empty list for found news
        news_list = []

        # some parsers use last_checking_time for define the end point
        # So there is last_checking_time initialization
        # if if is the first news checking then we suppose that last_checking_time was max_time_lag seconds ago
        current_time = time.time()
        if self.last_checking_time is None:
            self.last_checking_time = current_time - self.max_time_lag

        page_number = 1
        self.end_point_is_not_reached = True
        while self.end_point_is_not_reached:

            # parse one page with projects (result will be in self.project_dict)
            # If something went wrong, interrupt parsing
            result_code = await self.parse_single_page_with_projects(self.projects_url, page_number)
            if result_code != ParsingResult.SUCCESSFUL:
                if result_code == ParsingResult.NOT_IMPLEMENTED:
                    raise NotImplementedError
                else:
                    return news_list, result_code

            # update value of end_point_is_not_reached
            self.update_cond_for_cycle_ending()

            # in cycle if a project is valid and not in project_data_file then
            # add it to news_list and project_dict_from_file
            keys = self.project_dict.keys()
            for key in keys:
                if self.is_valid_project(self.project_dict[key]):
                    if key not in self.project_dict_from_file.keys():
                        news_list.append(self.format_new(self.project_dict[key]))
                        self.project_dict_from_file[key] = self.project_dict[key]

            # move on to the next page
            page_number += 1
            await asyncio.sleep(10)

        # if cycle is closed normally then last_checking time is corrent time
        self.last_checking_time = current_time

        # update data in project_dict_from_file
        write_data_into_file(self.project_dict_from_file, 'parsers\\project_data_dir\\project_data.json')

        # make project_dict empty for the next
        self.project_dict = dict()
        return news_list, ParsingResult.SUCCESSFUL

    async def parse_single_page_with_projects(self, page_url, page_number) -> ParsingResult:
        """start parsing of single projects placed in the page"""
        kind = 1  # this kind is needed to show only orders
        params = {'kind': kind, 'page': page_number}
        logger.debug(f"Parse page number{page_number}")
        async with aiohttp.ClientSession() as session:
            async with session.get(page_url, params=params) as resp:
                html = await resp.text()

            soup = BeautifulSoup(html, 'html.parser')

            if self.check_guard(soup):
                return ParsingResult.BLOCKED_BY_GUARD

            project_links = self.get_project_links(soup)
            print(project_links)

            tasks = []
            for i in range(0, len(project_links)):
                task = asyncio.create_task(self.parse_single_project(f"{project_links[i]}",
                                                                     True,
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
        async with session.get(project_url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

        project_info = self.get_project_info(soup)

        if None not in project_info:
            logger.debug(f"Project {project_id} successfully parsed")
            title, description, price = project_info
            self.project_dict[project_id] = {
                'url': project_url,
                'title': title,
                'description': description,
                'price': price,
            }
            print(self.project_dict[project_id])
        else:
            print(None)
            logger.debug(f"Project {project_id} didn't successfully parsed")

    def is_valid_project(self, project_info: dict) -> bool:
        """check whether the project matches the required conditions"""
        return True

    def format_new(self, new: dict):
        formatted_new = f"<a href = \'{new['url']}\'>{new['title']}</a>\n" \
                        f"{new['description']}\n"
        return formatted_new

    def update_cond_for_cycle_ending(self):
        keys = self.project_dict.keys()
        for key in keys:
            if key in self.project_dict_from_file.keys():
                self.end_point_is_not_reached = False
                return
        self.end_point_is_not_reached = True

    def check_guard(self, soup: BeautifulSoup) -> bool:
        """check whether the page is a ddos-guard page"""
        title = soup.find('title')
        if title.text.strip() == 'Доступ заблокирован':
            return True
        return False

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

    def get_project_links(self, soup: BeautifulSoup) -> list:
        """get project links"""
        project_titles_with_links = soup.find_all('div', class_=['card',
                                                                 'want-car',
                                                                 'js-want-container'])
        project_links = [i.find("a").get("href") for i in project_titles_with_links]
        return project_links

    def get_project_info(self, soup: BeautifulSoup) -> tuple:
        """
        get title, description, price from the soup of a project
        """
        card_soup = soup.find('div', class_='card__content')
        if card_soup is None:
            return None, None, None

        title = self.get_title(card_soup)
        description = self.get_description(card_soup)
        price = self.get_price(card_soup)

        return title, description, price

    def get_title(self, card_soup: BeautifulSoup) -> str or None:
        title_soup = card_soup.find("h1", class_=['fz20',
                                                  'wants-card__header-title',
                                                  'first-letter',
                                                  'breakwords',
                                                  'pr200'])
        if title_soup is None:
            title = None
        else:
            title = title_soup.text.strip()
        return title

    def get_description(self, card_soup: BeautifulSoup) -> str or None:
        description_soup = card_soup.find("div",
                                          class_=['wants-card__description-text wish_name',
                                                  'first-letter',
                                                  'br-with-lh',
                                                  'break-word']).find('div')
        if description_soup is None:
            description = None
        else:
            description = description_soup.text.strip()
        return description

    def get_price(self, card_soup: BeautifulSoup) -> str or None:
        price_soup = card_soup.find("div", class_=["wants-card__header-price",
                                                   "wants-card__price",
                                                   "m-hidden"])
        if price_soup is None:
            price = None
        else:
            price = price_soup.text.strip()
        return price


async def kwork_parser_test():
    kwork_parser = KworkParser(kwork_project_url, paths['project_data_file_path'])
    while True:
        print("начало парсинга новостей")
        news_list = await kwork_parser.check_news()
        print("новости спарсены")
        for i in news_list:
            print(i)
        await asyncio.sleep(5)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(kwork_parser_test())
