import aiohttp
import asyncio
import lxml
from bs4 import BeautifulSoup
# https://www.fl.ru/projects/?page=2&kind=1

fl_ru_host = "https://www.fl.ru"
fl_ru_projects_url = "https://www.fl.ru/projects/"


async def parse_single_project(project_url, required_categories=[]):
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
            project_id = project_url.split('/')[4]
            print(project_id)
            print(title)
            print(description)
            print(price)


async def parse_single_page_with_projects(page_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'lxml')

            project_titles_with_links = soup.find_all("h2", class_=["b-post__title",
                                                                    "b-post__grid_title p-0",
                                                                    "b-post__pin"])
            project_links = [i.find("a").get("href") for i in project_titles_with_links]
            for i in project_links:
                print(i)


async def main():
    await parse_single_page_with_projects("https://www.fl.ru/projects/?kind=1")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
