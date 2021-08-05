import aiohttp
import asyncio
import lxml
from bs4 import BeautifulSoup
# https://www.fl.ru/projects/?page=2&kind=1

fr_ru_projects_url = "https://www.fl.ru/projects/"


async def parse_single_project(project_url, categories1=[], categories2=[]):
    async with aiohttp.ClientSession() as session:
        async with session.get(project_url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'lxml')

            categories1_2 = soup.find("div", class_=["b-layout__txt",
                                                 "b-layout__txt_fontsize_11",
                                                 "b-layout__txt_padbot_20"]).find_all("a")

            category1 = categories1_2[0].text  # may not work
            category2 = categories1_2[1].text  # may not work

            title = soup.find("h1", class_="b-page__title").text
            description = soup.find("div", class_="b-layout__txt b-layout__txt_padbot_20").text
            price = soup.find("span", class_="b-layout__bold").text  # may not work
            if category1 in categories1 and category2 in categories2:
                pass
            else:
                pass


async def main():
    await parse_single_project("https://www.fl.ru/projects/4809533/parser-internet-magazina.html")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())