paths = {
    'html_examples_dir_path': 'html_pages',
    'chat_id_list_file_path': 'json_dir\\chat_id_list.json',
    'project_data_file_path': 'json_dir\\project_data.json'
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/'
              'webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.135 YaBrowser/21.6.3.757 Yowser/2.5 Safari/537.36',
    }

required_categories = [['Программирование'],
                       ['Парсинг данных', 'Разработка Чат-ботов']]
required_words = ['парсер', 'парсинг', 'телеграм', 'бот']

fl_ru_host = "https://www.fl.ru"
fl_ru_projects_url = "https://www.fl.ru/projects/"

parsing_delay = 10*60
waiting_delay = 20
ddos_delay = 3*60*60
