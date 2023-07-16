from googleSheets import getStorageData, getSoldItemsData
from ucBrowser import createBrowserUC
from bs4 import BeautifulSoup
import time
from datetime import datetime


# Определение текущего СТАТУСА предмета (доступен / продан / не найден)
def itemStatus(name):

    # Получение данных Storage
    storage = getStorageData()
    for i in range(1, len(storage)):
        if storage[i][0] == name:
            date = datetime.strptime(storage[i][2], '%d.%m.%Y')  # Проверка доступности предмета
            if date > datetime.now():  # Предмет временно недоступен
                return True, storage[i][2]
            else:  # Предмет доступен
                return True

    # Получение данных Sold Items
    soldItems = getSoldItemsData()
    for j in range(len(soldItems) - 10, len(soldItems)):
        if soldItems[j][2] == name:
            return False

    return None


# Поиск ЦЕНЫ продажи предмета
def itemWallPrice(name):

    driver = createBrowserUC(enableProxy=False, logging=False)
    driver.get('https://vk.com/shoppycsgo')
    time.sleep(3)
    page = driver.page_source
    page = BeautifulSoup(page, 'lxml')
    driver.quit()

    wall = page.findAll('div', class_="wall_text")  # Все посты в группе

    for post in wall:  # Поиск по постам
        if name in post.text:
            text = post.text[post.text.find('Цена продажи: ') + 14:]
            price = text[:text.find(' ₽')]
            return price


# Получение информации о предмете из поста ВК
def parsePost(post_url):

    post_url = post_url.replace('shoppycsgo?w=', '')

    driver = createBrowserUC(enableProxy=False, logging=False)
    driver.get(url=post_url)
    time.sleep(3)

    page = driver.page_source
    page = BeautifulSoup(page, 'lxml')

    driver.close()
    driver.quit()

    try:

        if page.find('div', class_="ui_ownblock_label").text == 'SHOPPY | Продажа скинов CS:GO':

            wall_text = page.find('div', class_="wall_text").text
            item_name = wall_text[:wall_text.find(')') + 1]

            wall_text = wall_text[wall_text.find('Цена продажи: ') + 14:]
            item_price = wall_text[:wall_text.find(' ₽')]

            return {'name': item_name, 'price': item_price}

        else:
            return "Ссылка указана неверно. Вместо нее вы можете отправить название желаемого предмета, или попробовать позже."

    except:
        return "Ошибка проверки поста. Вы можете отправить название желаемого предмета, или попробовать позже."
