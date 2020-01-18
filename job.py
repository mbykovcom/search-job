from datetime import datetime

from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool
from selenium import webdriver

FILE = "data.txt"
URL = {'base': 'https://spb.hh.ru/search/vacancy?area=2&items_on_page=20', 'text': '&text=',
       'search_period': '&search_period=',
       'page': '&page='}
INFO = {'url': '', 'period': 7, 'login': '', 'password': '', 'search': '', 'not_search_word': '', 'skill': ''}
headers = {'accept': '*/*',
           'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/79.0.3945.117 Safari/537.36'}
DRIVER = None


def get_data(file):
    """
    Получение информации о описке из файла data.txt и записывает данные в словарь INFO
    :param file: путь к файлу с данными
    :return:
    """
    try:
        print('\n -- Читаем файл с данными о запросе...')
        with open(file, 'r') as f:
            data = f.readlines()
            for i in range(len(data)):
                d = data[i].strip().split(':')
                if d[0] == 'skill':
                    INFO[d[0]] = d[1].replace(' ', '').lower().split(',')
                elif d[0] == 'not_search_word':
                    INFO[d[0]] = d[1].replace(' ', '').lower().split(',')
                else:
                    INFO[d[0]] = d[1].strip()
        INFO['url'] = URL['base'] + URL['text'] + INFO['search'] + URL['search_period'] + str(INFO['period']) + URL[
            'page']
    except:
        print('Ошибка чтения файла с данными {}'.format(file))
    finally:
        print(' -- Выполненно\n\n'
              '-----------------------------------\n')


def get_html(url):
    session = requests.Session()
    respons = session.get(url, headers=headers)
    return respons.content


def get_total_pages(url):
    try:
        print(' -- Подсчет страниц с подходящими вакансиями...')
        html = get_html(url)
        soup = BeautifulSoup(html, 'lxml')
        pagination = soup.find_all('a', attrs={'data-qa': 'pager-page'})
        if not pagination:
            print(' -- Найдено {0} страниц по запросу {1}.\n\n'
                  '-----------------------------------\n'.format(1, INFO['search']))
            return 1
        print(' -- Найдено {0} страниц по запросу {1}.\n\n'
              '-----------------------------------\n'.format(pagination[-1].text, INFO['search']))
        return int(pagination[-1].text)
    except:
        print('Ошибка подсчета!')


def check_skill(link, skills):
    try:
        html = get_html(link)
        soup = BeautifulSoup(html, 'lxml')
        spans = soup.find_all('span', class_='bloko-tag__section bloko-tag__section_text')
        skills_list = []
        for span in spans:
            skills_list.append(span.text.lower())
        return not set(skills).isdisjoint(skills_list)
    except:
        print('Ошибка проверки вакансии на искомые навыки!')


def auth_hh():
    global DRIVER
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)
    DRIVER = driver
    try:
        print('\n -- Авторизируемся на сайте hh.ru...')
        driver.get('https://spb.hh.ru/account/login?backurl=%2F')
        driver.find_element_by_name('username').send_keys(INFO['login'])
        driver.find_element_by_name('password').send_keys(INFO['password'])
        driver.find_element_by_xpath("//input[@data-qa='account-login-submit']").click()
    except:
        print('Ошибка авторизации')
        return None
    finally:
        print(' -- Выполнено\n\n'
              '-----------------------------------\n')


def add_favorites(link):
    try:
        DRIVER.get(link)
        try:
            DRIVER.find_element_by_xpath(
                "//button[@class='bloko-button bloko-button_icon-only bloko-button_minor']").click()
        except:
            DRIVER.find_element_by_xpath("//button[@class='bloko-button bloko-button_icon-only']").click()
    except:
        print('Ошибка добавления вакансий в избранное!')


def get_jobs(url, pages):
    print(' -- Ищем подходящие вакансии...')
    links_vacancy = []
    print('\t', end='')
    for i in range(pages):
        print('.', end='')
        html = get_html(url + str(i))
        soup = BeautifulSoup(html, 'lxml')
        divs = soup.find_all('div', class_='resume-search-item__name')
        for div in divs:
            vacancy = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'})
            name = vacancy.text.lower().replace('/', ' ').replace('(', '').replace(')', '').split()
            if (not set(INFO['search'].lower().split()).isdisjoint(name)) and \
                    (set(INFO['not_search_word']).isdisjoint(name)):
                if check_skill(vacancy.get('href'), INFO['skill']):
                    links_vacancy.append(vacancy.get('href'))
    count = len(links_vacancy)
    auth_hh()
    print(' -- Добавляем найденные вакансии в Избранное...')
    for i in range(count):
        add_favorites(links_vacancy[i])
    text = 'ваканс'
    if count > 0:
        if count % 10 == 1:
            text += 'ия'
        elif count % 10 < 5:
            text += 'ии'
        elif count % 10 > 4:
            text += 'ий'
        print(' -- Готово! Добавлено {0} {1} в Избранное.\n'  # Добавить вариации слова вакансии
              '    Перейти на сайт: https://spb.hh.ru/applicant/favorite_vacancies?from=header_new'.format(count, text))
    else:
        print('Подходящих вакансий не найдено :( \n'
              'Поменяйте параметры в файле на другие.')


def main():
    start = datetime.now()
    get_data(FILE)
    pages = get_total_pages(INFO['url'])
    get_jobs(INFO['url'], pages)
    end = datetime.now()
    total = end - start
    print('\n   Потрачено времени: ' + str(total))


if __name__ == '__main__':
    main()
