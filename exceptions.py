import asyncio
from bs4 import BeautifulSoup
import sys


def check_ddos_guard(soup):
    title = soup.find('title')
    if title.text.strip() == 'DDOS-GUARD':
        print('Сработала защита ddos-guard')
        sys.exit()
