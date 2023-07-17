from googleSheets import getStorageData, getUserOrdersData
from datetime import datetime
# from steam_offers import sendTradeOffer
from bot import send_message
from googleSheets import updateOrder


# Поиск забронированных предметов, доступных для обмена
def checkBookedItems():

    bookedItems = []  # Текущие забронированные предметы
    tradableItems = []  # Доступные для обмена предметы

    userOrders = getUserOrdersData()[1:]
    for row in userOrders:
        if ('*' in row[1]) and (row[4] == '3') and ((datetime.now() - datetime.strptime(row[5], '%d-%m-%Y %H:%M')).days >= 0):  # Если совпадает тип, статус и дата
            bookedItems.append({'name': row[1].replace('*', ''), 'price': row[2], 'user': row[0], 'tradeLink': row[6]})

    storageSheet = getStorageData()[1:]
    for row in storageSheet:
        if datetime.strptime(row[2], '%d.%m.%Y') <= datetime.now():
            tradableItems.append(row[0])

    commonItems = [item for item in bookedItems if item['name'] in tradableItems]  # Забронированные предметы, доступные для обмена
    return commonItems


# Отправка забронированных предметов, доступных для обмена
def sendBookedItems():

    print('----- Sending actual BOOKED items -----')

    bookedItems = checkBookedItems()

    if bookedItems:

        print('    Some actual BOOKED items were found')

        for item in bookedItems:
            # sendTradeOffer(item['name'], item['tradeLink'])  # Отправка предмета покупателю
            send_message(item['user'], f"Добрый день! ☀️\nПредмет [club219295292|{item['name']}] успешно вам отправлен! Примите его в течение 2 часов.")  # Сообщение об отправленном предмете
            updateOrder(item['user'], item['price'], status=4)

    else:
        print('----- There are no any actual BOOKED items -----')
        return

    print('----- The BOOKED items were sent to their customers -----')

sendBookedItems()
