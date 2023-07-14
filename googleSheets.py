import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import configure
import gspread
from datetime import datetime

from checkPayment import checkQIWI


CREDENTIALS_FILE = 'storageSheet_keys.json'  # Имя файла с закрытым ключом, вы должны подставить свое

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
service = discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API


# # Создание новой таблицы
# spreadsheet = service.spreadsheets().create(body = {
#     'properties': {'title': 'storageSheet', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': 'List 1',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 7}}}]
# }).execute()
#
# spreadsheetId = configure.storageSheet_sheet  # Идентификатор файла
#
# # Выдаем доступ к таблице
# driveService = discovery.build('drive', 'v3', http = httpAuth) # Выбираем работу с Google Drive и 3 версию API
#
# access = driveService.permissions().create(
#     fileId = spreadsheetId,
#     body = {'type': 'user', 'role': 'writer', 'emailAddress': configure.egor_email},  # Открываем доступ на редактирование
#     fields = 'id'
# ).execute()
#
# access = driveService.permissions().create(
#     fileId = spreadsheetId,
#     body = {'type': 'user', 'role': 'writer', 'emailAddress': configure.andrey_email},  # Открываем доступ на редактирование
#     fields = 'id'
# ).execute()


# Добавление предмета в таблицу ХРАНИЛИЩА
def addWithdrawnItem(name, buyDate, sellDate, buyPrice, minPrice, quickSell, MP_profit, QS_profit, account):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    # Добавление пустой строки в таблицу
    sheet = client.open("storageSheet").sheet1

    sheet.append_row([name, buyDate, sellDate, int(buyPrice), int(minPrice), int(quickSell), MP_profit, QS_profit, account])  # Добавление строки со значениями

    # print('UPDATED STORAGE SHEET:', 'https://docs.google.com/spreadsheets/d/' + configure.storageSheet_sheet)  # Ссылка на таблицу


# Удаление предмета из таблицы ХРАНИЛИЩА
def delWithdrawnItem(name):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    # Добавление пустой строки в таблицу
    sheet = client.open("storageSheet").worksheet("storageSheet")

    allData = sheet.get_all_values()

    row_num = 0

    for row in allData:
        if name in row:
            row_num = allData.index(row)
            break

    if row_num != 0:
        sheet.delete_rows(row_num + 1, row_num + 1)
        # print('UPDATED STORAGE SHEET:', 'https://docs.google.com/spreadsheets/d/' + configure.storageSheet_sheet)  # Ссылка на таблицу
    else:
        print("THERE ISN'T SUCH ITEM IN THE TABLE")  # Такого предмета нет в таблице


# Добавление предмета в таблицу ПРОДАННЫХ СКИНОВ
def addSoldItem(name, buyPrice, sellPrice, account):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    # Добавление пустой строки в таблицу
    sheet = client.open("storageSheet").worksheet("soldItems")

    sheet.append_row(["", "", name, int(buyPrice), int(sellPrice), datetime.now().strftime('%d.%m'), account])  # Добавление строки со значениями

    current_row = sheet.row_count + 1  # Номер текущей строки

    sheet.update_acell(f"A{current_row}", f"=ROUND(E{current_row}*0,95-D{current_row})")  # Ячейка прибыли для текущей строки
    sheet.update_acell(f"B{current_row}", f"=ROUND(E{current_row}/D{current_row}*100-100; 2)")  # Ячейка % прибыли для текущей строки
    sheet.update_acell("A1", f"=SUM(A2:A{current_row})")  # Ячейка общей прибыли
    sheet.update_acell("B1", f"=ROUND(A1*100/SUM(D2:D{current_row}); 2)")  # Ячейка среднего %

    # Подсчет прибыли за предыдущий месяц
    previous_date = str(sheet.acell(f'F{current_row - 1}').value)  # Предыдущая дата
    current_date = str(sheet.acell(f'F{current_row}').value)  # Текущая дата

    if previous_date[-1] != current_date[-1]:  # Если месяц не совпадает

        month_start_cell = 0  # Ячейка начала предыдущего месяца

        soldItemsData = getSoldItemsData()
        reversedData = list(reversed(soldItemsData))

        for i in range(1, len(reversedData) + 1):  # Обход дат таблицы с конца
            try:
                if str(reversedData[i][5])[-1] != str(reversedData[i+1][5])[-1]:
                    month_start_cell = len(soldItemsData) - i  # Номер ячейки начала предыдущего месяца
                    break
            except:
                continue

        sheet.update_acell(f"H{current_row - 1}", f"=SUM(A{month_start_cell}:A{current_row - 1})")  # Ячейка прибыли за предыдущий месяц

    # print('UPDATED SOLD ITEMS SHEET:', 'https://docs.google.com/spreadsheets/d/' + configure.soldItems_sheet)  # Ссылка на таблицу


# Извлечение всех данных из STORAGE SHEET
def getStorageData():

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("storageSheet")

    return sheet.get_all_values()


# Извлечение всех данных из SOLD ITEMS SHEET
def getSoldItemsData():

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("soldItems")

    return sheet.get_all_values()


# Создание заказа в USER ORDERS
def addOrder(user, item, price, payment=None, status=1):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("userOrders")

    sheet.append_row([user, item, price, '', status])


# Получение информации о заказе из USER ORDERS
def getOrderData(user, onlyPrice=False, onlyStatus=False, onlyItem=False):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("userOrders")
    data = sheet.get_all_values()

    if onlyPrice:  # Если запрошена только цена
        for row in data:
            if row[0] == str(user):
                return row[2]
    elif onlyItem:
        for row in data:
            if row[0] == str(user):
                return row[1]
    elif onlyStatus:
        for row in data:
            if row[0] == str(user):
                return row[4]
    else:
        for row in data:
            if row[0] == str(user):
                return row


# Обновить информацию о заказе из USER ORDERS
def updateOrder(user, price, status, payment=''):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("userOrders")
    data = sheet.get_all_values()

    match status:
        case 2:
            for row in range (1, len(data)):
                if data[row][0] == str(user) and data[row][2] == str(price):
                    sheet.update_acell(f'D{row + 1}', payment)
                    sheet.update_acell(f'E{row + 1}', status)
        case 3|4:
            for row in range (1, len(data)):
                if data[row][0] == str(user) and data[row][2] == str(price):
                    sheet.update_acell(f'E{row + 1}', status)


# Удаление заказа из USER ORDERS
def deleteOrder(user, price):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("userOrders")
    data = sheet.get_all_values()

    for row in range(1, len(data)):
        if data[row][0] == str(user) and data[row][2] == str(price) and data[row][4] == '2':
            sheet.delete_rows(row + 1, row + 1)


# Проверка наличия активного заказа у пользователя
def isActiveOrder(user):

    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open("storageSheet").worksheet("userOrders")
    data = sheet.get_all_values()

    for row in range(1, len(data)):
        if data[row][0] == str(user) and data[row][4] != '4':
            price = data[row][2]
            payment = data[row][3]
            return [True, price, payment]

    return False
