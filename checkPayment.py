import configure
import python_qiwi
from datetime import datetime, timedelta
import time
from ucBrowser import createBrowserUC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re


# Проверка оплаты TINKOFF [В РАБОТЕ 🚧️]
def checkTinkoff(user, price):  # В РАЗРАБОТКЕ

    driver = createBrowserUC(enableProxy=False)
    driver.get("https://www.tinkoff.ru/events/feed/")  # Страница последних платежей Tinkoff

    # time.sleep(10)

    input('next?')

    page = driver.page_source
    page = BeautifulSoup(page, 'lxml')
    print(page)

    driver.close()
    driver.quit()


# Проверка оплаты SBER [В РАБОТЕ 🚧]
def checkSber(user, price):

    # Вход с СБЕРБАНК ОНЛАЙН
    driver = createBrowserUC(enableProxy=False)
    driver.get("https://online.sberbank.ru/")  # Страница входа в ЛК Сбербанк

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//button[@data-testid="button-continue"]')))  # Ожидание прогрузки страницы входа

    driver.find_element('xpath', '//input[@name="login"]').send_keys(configure.sber_login)  # Заполнение ЛОГИНА
    time.sleep(1)

    driver.find_element('xpath', '//input[@name="password"]').send_keys(configure.sber_password)  # Заполнение ПАРОЛЯ
    time.sleep(1)

    driver.find_element('xpath', '//button[@data-testid="button-continue"]').click()  # Кнопка входа

    # Пропуск лишней страницы при входе
    pass

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
    time.sleep(5)

    page = driver.page_source

    driver.close()
    driver.quit()

    # # ---------- TESTING ----------
    # file = open('testPage.txt', 'r')
    # page = file.read()
    # page = BeautifulSoup(page, 'lxml')
    # file.close()
    # # ---------- TESTING ----------

    page = str(page)

    # Отсечение лишней информацию из кода страницы
    page = page[page.find('<div class="region-operations'):]
    page = BeautifulSoup(page, 'lxml')

    # Последние платежи
    class_pattern = re.compile("region-operations")  # Регулярное выражение для поиска операций
    history = page.find_all('p', class_=class_pattern, attrs={"color": "green"})  # История входящих платежей

    for t in history:
        print(t.text, '\n')


# Проверка оплаты QIWI [✅]
def checkQIWI(user, price):

    start_time = str(datetime.now() - timedelta(hours=1))  # Переход в часовой пояс МСК
    now_day = start_time[:start_time.find(' ')]  # Текущий день
    now_time = start_time[start_time.find(' ') + 1:start_time.find('.')]  # Текущее время

    wallet = python_qiwi.QiwiWаllet(configure.qiwi_phone, configure.qiwi_token)

    for i in range (1, 60 + 1):  # Проверка раз в 15 секунд на протяжении 15 минут

        print("QIWI ATTEMPT #", i, " for USER ", user, sep='')
        history = wallet.payment_history()  # История платежей

        for t in history['data']:

            if t['statusText'] == 'Success':  # Если платеж прошел успешно

                date = str(t['date'])
                transaction_day = date[:date.find('T')]  # Дата платежа
                transaction_time = date[date.find('T') + 1:date.find('+')]  # Время платежа

                # print(transaction_day, now_day)
                # print(transaction_time, now_time, (datetime.strptime(now_time, '%H:%M:%S') - datetime.strptime(transaction_time, '%H:%M:%S')).seconds)
                # print(price, t['sum']['amount'])
                # print(643, t['sum']['currency'], '\n')

                if transaction_day == now_day and (datetime.strptime(now_time, '%H:%M:%S') - datetime.strptime(transaction_time, '%H:%M:%S')).seconds < 900:  # Если ДЕНЬ и ВРЕМЯ платежа подходят
                    if str(t['sum']['amount']) == price and t['sum']['currency'] == 643:  # Если СУММА и ВАЛЮТА платежа подходят
                        return user, True

        time.sleep(15)


# Проверка оплаты USDT [НЕ НАЧАЛ]
def checkUSDT(user, price):
    pass


checkSber('', '')
