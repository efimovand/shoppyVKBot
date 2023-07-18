from googleSheets import getStorageData, getSoldItemsData
from datetime import datetime


# Определение текущего СТАТУСА предмета (доступен / продан / не найден)
def itemStatus(name):

    # Получение данных Storage
    storage = getStorageData()
    for i in range(1, len(storage)):
        if storage[i][0] == name:
            date = datetime.strptime(storage[i][2] + ' 11:00', '%d.%m.%Y %H:%M')  # Проверка доступности предмета
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
