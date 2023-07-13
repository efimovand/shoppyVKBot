import time
import requests
from ucBrowser import createBrowserUC
from bs4 import BeautifulSoup


url = "https://vk.com/wall-219295292_19"


def validatePost(post_url):

    driver = createBrowserUC(enableProxy=False, logging=False)
    driver.get(url=post_url)

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

    except Exception as e:
        print("Post validation error", e)
        return "Ошибка проверки поста. Вы можете отправить название желаемого предмета, или попробовать позже."
