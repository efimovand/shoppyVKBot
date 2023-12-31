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


# Проверка оплаты TINKOFF [✅]
def checkTinkoff(user, price, invoiceDate):

    print('----- Starting TINKOFF scanning for USER', user, '-----')

    start_time = datetime.strptime(invoiceDate, '%d-%m-%Y %H:%M')  # Время выставления счета
    formatted_price = "{:,.0f}".format(int(price)).replace(",", " ")  # Форматирование цены

    driver = createBrowserUC(enableProxy=False, enableCookies=True, logging=False)
    driver.get("https://www.tinkoff.ru/events/feed/")  # Страница последних платежей Tinkoff
    time.sleep(5)

    for i in range (1, 3 + 1):  # Проверка 3 раза

        print("    TINKOFF attempt #", i, " for USER ", user, sep='')

        # Если запрошен PIN код
        if len(driver.find_elements('xpath', '//p[@class="b-paragraph b-paragraph_description"]')) != 0:
            pinCodeFields = driver.find_elements('xpath', '//input[@class="ui-field__native" and contains(@id, "pinCode")]')  # Поля ввода

            # Ввод PIN кода
            pinCodeFields[0].send_keys(configure.tinkoff_pin[0])
            time.sleep(0.5)
            pinCodeFields[1].send_keys(configure.tinkoff_pin[1])
            time.sleep(0.5)
            pinCodeFields[2].send_keys(configure.tinkoff_pin[2])
            time.sleep(0.5)
            pinCodeFields[3].send_keys(configure.tinkoff_pin[3])

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//div[contains(@class, "Tabs--module__tabItem")]')))  # Ожидание прогрузки страницы последних платежей
        time.sleep(5)

        # Поиск подходящих транзакций
        suitable_transactions = driver.find_elements('xpath', '//span[contains(@class, "TimelineItem__value") and @style="color: rgb(34, 160, 83);"]')
        if suitable_transactions:

            for j in range (len(suitable_transactions)):

                suitable_transactions = driver.find_elements('xpath', '//span[contains(@class, "TimelineItem__value") and @style="color: rgb(34, 160, 83);"]')

                if suitable_transactions[j].text.replace('\n', '') == '+' + formatted_price + ',00':  # Если СУММА подходит

                    suitable_transactions[j].click()
                    time.sleep(3)

                    transaction_date = driver.find_element('xpath', '//span[@data-qa-type="operation-popup-time"]').text.split()  # ДАТА платежа

                    # ДЕНЬ и ВРЕМЯ платежа
                    transaction_day = transaction_date[0] + '.' + getMonthNumber(transaction_date[1]) + '.' + transaction_date[2][:-1]
                    transaction_time = transaction_date[3]

                    if (datetime.strptime(transaction_day + ' ' + transaction_time, '%d.%m.%Y %H:%M') - start_time).seconds < 900:  # Если ВРЕМЯ подходит
                        driver.close()
                        driver.quit()
                        print('----- SUCCESSFUL payment from USER', user, 'with TINKOFF -----\n')
                        return user, True
                    # else:
                    #     print("OLD TRANSACTION")

                    driver.find_element('xpath', '//button[@data-qa-type="details-card-close"]').click()  # Возврат на страницу истории платежей
                    time.sleep(5)

        # else:
        #     print("NO SUITABLE TRANSACTIONS")

        time.sleep(15)  # Перерыв между попытками
        driver.refresh()  # Обновление страницы последних платежей

    driver.close()
    driver.quit()

    print('----- TINKOFF payment from USER', user, 'has not been received -----\n')


# Проверка оплаты SBER [✅]
def checkSber(user, price, invoiceDate):

    print('----- Starting SBER scanning for USER', user, '-----')

    start_time = datetime.strptime(invoiceDate, '%d-%m-%Y %H:%M')  # Время выставления счета
    formatted_price = "{:,.0f}".format(int(price)).replace(",", " ")  # Форматирование цены

    # Вход с СБЕРБАНК ОНЛАЙН
    driver = createBrowserUC(enableProxy=False, enableCookies=True, logging=False)
    driver.get("https://online.sberbank.ru/")  # Страница входа в ЛК Сбербанк

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//button[@data-testid="button-continue"]')))  # Ожидание прогрузки страницы входа

    driver.find_element('xpath', '//input[@name="login"]').send_keys(configure.sber_login)  # Заполнение ЛОГИНА
    time.sleep(1)

    driver.find_element('xpath', '//input[@name="password"]').send_keys(configure.sber_password)  # Заполнение ПАРОЛЯ
    time.sleep(1)

    driver.find_element('xpath', '//button[@data-testid="button-continue"]').click()  # Кнопка входа

    if len(driver.find_elements('xpath', '//h2[@data-testid="stage-subheader"]')) != 0:  # Пропуск лишней страницы при входе
        driver.find_element('xpath', '//button[@data-testid="button-skip"]').click()

    for i in range (1, 3 + 1):  # Проверка 3 раза

        print("    SBER attempt #", i, " for USER ", user, sep='')

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
        time.sleep(5)

        # Поиск подходящих транзакций
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

                if (datetime.strptime(transaction_day + ' ' + transaction_time, '%d.%m.%Y %H:%M') - start_time).seconds < 900:  # Если время подходит
                    driver.close()
                    driver.quit()
                    print('----- SUCCESSFUL payment from USER', user, 'with SBER -----\n')
                    return user, True
                # else:
                #     print("OLD TRANSACTION")

                driver.back()  # Возврат на страницу истории платежей
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", '//span[@class="scaffold__region-header-link-full"]')))  # Ожидание прогрузки страницы последних платежей
                time.sleep(5)

        # else:
        #     print("NO SUITABLE TRANSACTIONS")

        time.sleep(15)  # Перерыв между попытками
        driver.refresh()  # Обновление страницы последних платежей

    driver.close()
    driver.quit()

    print('----- SBER payment from USER', user, 'has not been received -----\n')


# Проверка оплаты QIWI [✅]
def checkQIWI(user, price, invoiceDate):

    print('----- Starting QIWI scanning for USER', user, '-----')

    start_time = invoiceDate - timedelta(hours=1)  # Переход в часовой пояс МСК

    for i in range (1, 3 + 1):  # Проверка 3 раза

        print("    QIWI attempt #", i, " for USER ", user, sep='')

        wallet = python_qiwi.QiwiWаllet(configure.qiwi_phone, configure.qiwi_token)
        history = wallet.payment_history(rows_num=10)  # История платежей

        for t in history['data']:

            if t['status'] == 'SUCCESS' and t['type'] == 'IN':  # Если платеж прошел успешно

                if str(t['sum']['amount']) == str(price) and t['sum']['currency'] == 643:  # Если СУММА и ВАЛЮТА платежа подходят

                    transaction_time = datetime.strptime(t['date'][:t['date'].find('+')].replace('T', ' '), '%Y-%m-%d %H:%M:%S')  # Время платежа

                    if (transaction_time - start_time).seconds < 900:  # Если ВРЕМЯ платежа подходит
                        print('----- SUCCESSFUL payment from USER', user, 'with QIWI -----\n')
                        return user, True

        time.sleep(15)

    print('----- QIWI payment from USER', user, 'has not been received -----\n')


# Проверка оплаты USDT [✅]
def checkUSDT(user, price, invoiceDate):

    print('----- Starting USDT scanning for USER', user, '-----')

    start_time = datetime.strptime(invoiceDate, '%d-%m-%Y %H:%M')  # Время выставления счета
    client = Client(configure.binance_token, configure.binance_secret)

    for i in range (1, 3 + 1):  # Проверка 3 раза

        print("    USDT attempt #", i, " for USER ", user, sep='')
        history = client.get_deposit_history()  # Получение последних транзакций

        for transaction in history:
            if str(transaction['amount']) == str(price) and transaction['coin'] == 'USDT' and transaction['confirmTimes'] == '1/1':  # Если СУММА, СТАТУС и ВАЛЮТА платежа подходят
                if (datetime.fromtimestamp(transaction['insertTime'] / 1000) - start_time).seconds < 900:  # Если ВРЕМЯ платежа подходит
                    print('----- SUCCESSFUL payment from USER', user, 'with USDT -----\n')
                    return user, True

        time.sleep(15)

    print('----- USDT payment from USER', user, 'has not been received -----\n')
