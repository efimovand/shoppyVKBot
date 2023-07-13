import configure
import python_qiwi
from datetime import datetime, timedelta
import time


def checkTinkoff(user, price):
    pass


def checkSber(user, price):
    pass


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


def checkUSDT(user, price):
    pass
