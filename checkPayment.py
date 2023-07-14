import configure
import python_qiwi
from datetime import datetime, timedelta
import time
from ucBrowser import createBrowserUC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re


# Определение номера месяца по его названию [checkSBER()]
def get_month_number(month_name):
    month_mapping = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12"
    }
    return month_mapping.get(month_name.lower())


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

    start_time = datetime.now() - timedelta(hours=1)  # Переход в часовой пояс МСК

    # Вход с СБЕРБАНК ОНЛАЙН
    driver = createBrowserUC(enableProxy=False)
    driver.get("https://online.sberbank.ru/")  # Страница входа в ЛК Сбербанк

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//button[@data-testid="button-continue"]')))  # Ожидание прогрузки страницы входа

    driver.find_element('xpath', '//input[@name="login"]').send_keys(configure.sber_login)  # Заполнение ЛОГИНА
    time.sleep(1)

    driver.find_element('xpath', '//input[@name="password"]').send_keys(configure.sber_password)  # Заполнение ПАРОЛЯ
    time.sleep(1)

    driver.find_element('xpath', '//button[@data-testid="button-continue"]').click()  # Кнопка входа

    if len(driver.find_elements('xpath', '//h2[@data-testid="stage-subheader"]')) != 0:  # Пропуск лишней страницы при входе
        driver.find_element('xpath', '//button[@data-testid="button-skip"]').click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
    time.sleep(5)

    page = str(driver.page_source)

    # # ---------- TESTING ----------
    # file = open('testPage.txt', 'r')
    # page = file.read()
    # page = str(BeautifulSoup(page, 'lxml'))
    # file.close()
    # # ---------- TESTING ----------

    # Отсечение лишней информацию из кода страницы
    page = page[page.find('<div class="region-operations'):]
    page = BeautifulSoup(page, 'lxml')

    # Последние платежи
    class_pattern = re.compile("region-operations")  # Регулярное выражение для поиска операций
    history = page.find_all('p', class_=class_pattern, attrs={"color": "green"})  # История входящих платежей

    for t in history:

        transaction_price = t.text[t.text.find('+') + 1:t.text.find(' RUB')].replace(' ', '')  # Сумма платежа

        if transaction_price == str(price):  # Если СУММА платежа подходит

            # Определение даты платежа
            driver.find_element('xpath', f'//*[contains(@class, "region-operations") and @color="green" and text()="{t.text.replace("RUB₽", "")}"]').click()  # Переход на страницу подробностей платежа
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//h3[text()="Подробности"]')))
            time.sleep(3)

            page = str(driver.page_source)
            page = page[page.find('Дата и время'):]
            page = BeautifulSoup(page, 'lxml')

            class_pattern = re.compile("operations-details")
            transaction_date = page.find('p', class_=class_pattern, attrs={"font-weight": "regular"}).text.split()  # ДАТА платежа

            # ДЕНЬ и ВРЕМЯ платежа
            transaction_day = transaction_date[0] + '.' + get_month_number(transaction_date[1]) + '.' + transaction_date[2]  # ДЕНЬ платежа
            transaction_time = transaction_date[4]  # ВРЕМЯ платежа

            if (start_time - datetime.strptime(transaction_day + ':' + transaction_time, '%d.%m.%Y:%H:%M')).seconds < 900:  # Если время подходит
                return user, True

            driver.back()  # Возврат на страницу истории платежей
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
            time.sleep(5)

    driver.close()
    driver.quit()


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


checkSber('', 15000)
