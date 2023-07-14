import configure
import python_qiwi
from datetime import datetime, timedelta
import time
from ucBrowser import createBrowserUC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from binance.client import Client
from supportFunctions import getMonthNumber


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


# Проверка оплаты SBER [✅]
def checkSber(user, price):

    start_time = datetime.now()  # Текущее время

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

    # Последние платежи
    formatted_price = "{:,.0f}".format(price).replace(",", " ")  # Форматирование цены

    for i in range (1, 30 + 1):

        print("SBER attempt #", i, " for USER ", user, sep='')

        suitable_transactions = driver.find_elements('xpath', f'//*[contains(@class, "region-operations") and @color="green" and text()="+{str(formatted_price)} "]')  # Подходящие по СУММЕ транзакции

        if suitable_transactions:  # Если есть подходящие по СУММЕ транзакции

            for j in range (len(suitable_transactions)):  # Проход по подходящим транзакциям

                suitable_transactions = driver.find_elements('xpath', f'//*[contains(@class, "region-operations") and @color="green" and text()="+{str(formatted_price)} "]')

                suitable_transactions[j].click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//h3[text()="Подробности"]')))
                time.sleep(3)

                page = str(driver.page_source)
                page = page[page.find('Дата и время'):]
                page = BeautifulSoup(page, 'lxml')

                class_pattern = re.compile("operations-details")
                transaction_date = page.find('p', class_=class_pattern, attrs={"font-weight": "regular"}).text.split()  # ДАТА платежа

                # ДЕНЬ и ВРЕМЯ платежа
                transaction_day = transaction_date[0] + '.' + getMonthNumber(transaction_date[1]) + '.' + transaction_date[2]  # ДЕНЬ платежа
                transaction_time = transaction_date[4]  # ВРЕМЯ платежа

                if (start_time - datetime.strptime(transaction_day + ':' + transaction_time, '%d.%m.%Y:%H:%M')).seconds < 900:  # Если время подходит
                    return user, True
                # # ---------- LOGGING ----------
                # else:
                #     print("OLD TRANSACTION")
                # # ---------- LOGGING ----------

                driver.back()  # Возврат на страницу истории платежей
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
                time.sleep(5)

        # # ---------- LOGGING ----------
        # else:
        #     print("NO SUITABLE TRANSACTIONS")
        # # ---------- LOGGING ----------

        time.sleep(30)  # Перерыв между попытками

        # Обновление страницы последних платежей
        driver.refresh()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
        time.sleep(5)

    driver.close()
    driver.quit()


# Проверка оплаты QIWI [✅]
def checkQIWI(user, price):

    start_time = datetime.now() - timedelta(hours=1)  # Переход в часовой пояс МСК

    wallet = python_qiwi.QiwiWаllet(configure.qiwi_phone, configure.qiwi_token)

    for i in range (1, 60 + 1):  # Проверка раз в 15 секунд на протяжении 15 минут

        print("QIWI attempt #", i, " for USER ", user, sep='')
        history = wallet.payment_history(rows_num=10)  # История платежей

        for t in history['data']:

            if t['status'] == 'SUCCESS' and t['type'] == 'IN':  # Если платеж прошел успешно

                if t['sum']['amount'] == price and t['sum']['currency'] == 643:  # Если СУММА и ВАЛЮТА платежа подходят

                    transaction_time = datetime.strptime(t['date'][:t['date'].find('+')].replace('T', ' '), '%Y-%m-%d %H:%M:%S')  # Время платежа

                    if (start_time - transaction_time).seconds < 900:  # Если ВРЕМЯ платежа подходит
                        return user, True

        time.sleep(15)


# Проверка оплаты USDT [НЕ НАЧАЛ]
def checkUSDT(user, price):

    start_time = datetime.now()  # Текущее время

    client = Client(configure.binance_token, configure.binance_secret)

    for i in range (1, 60 + 1):

        print("USDT attempt #", i, " for USER ", user, sep='')
        history = client.get_deposit_history()  # Получение последних транзакций

        for transaction in history:
            if str(transaction['amount']) == str(price) and transaction['coin'] == 'USDT' and transaction['confirmTimes'] == '1/1':  # Если СУММА, СТАТУС и ВАЛЮТА платежа подходят
                if (start_time - datetime.fromtimestamp(transaction['insertTime'] / 1000)).seconds < 900:  # Если ВРЕМЯ платежа подходит
                    return user, True

        time.sleep(15)


checkUSDT(12345, 63.08)
