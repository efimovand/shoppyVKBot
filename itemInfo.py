from googleSheets import getStorageData, getSoldItemsData
from ucBrowser import createBrowserUC
from bs4 import BeautifulSoup


# Определение текущего СТАТУСА предмета (доступен / продан / не найден)
def itemStatus(name):

    # Получение данных Storage
    storage = getStorageData()
    for i in range(1, len(storage)):
        if (storage[i][0]).lower() == name:
            return True

    # Получение данных Sold Items
    soldItems = getSoldItemsData()
    for j in range(len(soldItems) - 10, len(soldItems)):
        if (soldItems[j][2]).lower() == name:
            return False

    return None


# Поиск ЦЕНЫ продажи предмета
def itemWallPrice(name):

    driver = createBrowserUC(enableProxy=False)
    driver.get('https://vk.com/shoppycsgo')
    page = driver.page_source
    page = BeautifulSoup(page, 'lxml')
    driver.quit()

    wall = page.findAll('div', class_="wall_text")  # Все посты в группе

    for post in wall:  # Поиск по постам
        if name in post.text.lower():
            text = post.text[post.text.find('Цена продажи: ') + 14:]
            price = text[:text.find(' ₽')]
            return price
