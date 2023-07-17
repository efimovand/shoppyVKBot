import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardButton, VkKeyboardColor
import configure
from itemInfo import itemStatus, itemWallPrice, parsePost
from googleSheets import addOrder, getOrderData, updateOrder, deleteOrder, isActiveOrder, delWithdrawnItem, addSoldItem
from checkPayment import checkTinkoff, checkSber, checkQIWI, checkUSDT
# from steam_offers import sendTradeOffer
from supportFunctions import actualUSD
import time
from datetime import datetime


vk_session = vk_api.VkApi(token=configure.group_token)
longpoll = VkLongPoll(vk_session)


# Функция отправки сообщения пользователю
def send_message(user_id, message, keyboard=None):
    if not keyboard:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0, 'dont_parse_links': 1})
    else:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0, 'dont_parse_links': 1, 'keyboard': keyboard.get_keyboard()})


# Функция получения предыдущего сообщения в диалоге
def get_last_message(user_id, onlyText=False):
    last_messages = vk_session.method('messages.getHistory', {'offset': 1, 'count': 1, 'user_id': user_id, 'peer_id': user_id, 'rev': 0, 'group_id': 219295292})
    if onlyText:
        return last_messages['items'][0]['text']
    else:
        return last_messages['items'][0]


def main():

    print("\nBOT is working...\n")

    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            message = event.text.replace('&quot;', '').replace('"', '').replace('\n', '')  # Текст сообщения после удаления случайных символов
            user = event.user_id  # ID пользователя


            # Если отправили ССЫЛКУ на пост
            if "vk.com/shoppycsgo?w=wall" in message or "vk.com/wall-" in message:

                send_message(user, 'Секунду, проверяю пост... 🔎')

                # Проверка наличия активного заказа у пользователя
                activeOrderInfo = isActiveOrder(user)
                if activeOrderInfo[0]:
                    send_message(user, f'У вас уже есть активный заказ.\nЗавершите его, оплатив @club219295292 ({activeOrderInfo[1]}) на @club219295292 ({activeOrderInfo[2]}), или дождитесь истечения времени оплаты — 15 минут.')

                else:  # Если активного заказа нет

                    validationResult = parsePost(message)  # Проверка корректности ссылки и получение данных о предмете

                    if type(validationResult) == dict:

                        item = validationResult['name']
                        price = validationResult['price']
                        respondOnItemStatus(user, item, wallPrice=False, price=price)  # Формирование подтверждения заказа

                    else:  # Ссылка на неверный пост / ошибка проверки
                        send_message(user, validationResult)


            # Если отправили НАЗВАНИЕ предмета
            elif (' | ' in message) or (' (' in message) or (')' in message):

                # Проверка наличия активного заказа у пользователя
                activeOrderInfo = isActiveOrder(user)
                if activeOrderInfo[0]:
                    send_message(user, f'У вас уже есть активный заказ.\nЗавершите его, оплатив @club219295292 ({activeOrderInfo[1]} ₽) на @club219295292 ({activeOrderInfo[2]}), или дождитесь истечения времени оплаты — 15 минут.')

                else:  # Если активного заказа нет

                    if " | " in message and " (" in message and ")" in message:

                        send_message(user, 'Секунду, ищу предмет... 🔎')
                        respondOnItemStatus(user, message, wallPrice=True)  # Формирование подтверждения заказа

                    else:
                        send_message(user, 'Введите полное название предмета на английском языке.\nЕго можно скопировать из поста с предметом на стене группы.\nНапример, "𝙰𝚆𝙿 | 𝙰𝚜𝚒𝚒𝚖𝚘𝚟 (𝙵𝚒𝚎𝚕𝚍-𝚃𝚎𝚜𝚝𝚎𝚍)"')


            # Подтверждение заказа
            elif message == 'Да' or message == 'Нет':

                if message == 'Да':  # Создание заказа и переход к оплате

                    last_message = get_last_message(user)  # Получение информации о последнем сообщении

                    if last_message['from_id'] == -219295292 and 'Подтвердите покупку' in last_message['text']:  # Если последнее сообщение было корректным

                        # Получение информации о предмете
                        last_message_text = last_message['text']
                        item = last_message_text[last_message_text.find('|') + 1:last_message_text.find(']')]  # Название
                        price = last_message_text[last_message_text.find('Цена: ') + 21:last_message_text.find(' ₽')]  # Цена

                        item += '' if last_message_text.find('Предмет будет отправлен') == -1 else '*'  # Покупка / Бронь

                        addOrder(user, item, price)  # Создание заказа в БД
                        choosePaymentSystem(user)  # Выбор платежной системы

                    else:
                        send_message(user, 'Возможно, произошла ошибка.\n\nПожалуйста, укажите ссылку на пост @club219295292 (SHOPPY | Продажа скинов CS:GO), либо название предмета из поста.')

                else:
                    send_message(user, 'Проверьте ссылку на пост и попробуйте отправить ее заново. Если ошибка сохраняется, напишите @id222224804 (Администратору) - он сам проведет оплату и отправит вам предмет.')


            # Способ оплаты
            elif message == 'Тинькофф' or message == 'СБЕР' or message == 'QIWI' or message == 'USDT':

                if getOrderData(user, onlyStatus=True) == '1':  # Если текущий заказ находится в статусе 'СОЗДАН'

                    price = getOrderData(user, onlyPrice=True)  # Сумма заказа
                    updateOrder(user, price, status=2, payment=message)  # Обновление статуса заказа на 'ВЫСТАВЛЕН СЧЕТ'

                    markup = VkKeyboard(one_time=True)
                    markup.add_button('Оплачено', VkKeyboardColor.POSITIVE)  # Кнопка подтверждения оплаты

                    match message:
                        case 'Тинькофф':
                            send_message(user, f'Оплатите @club219295292 ({price} ₽) по указанным реквизитам в течение 15 минут:\n@club219295292 ({configure.tinkoff_pay})', keyboard=markup)
                        case 'СБЕР':
                            send_message(user, f'Оплатите @club219295292 ({price} ₽) по указанным реквизитам в течение 15 минут:\n@club219295292 ({configure.sber_pay})', keyboard=markup)
                        case 'QIWI':
                            send_message(user, f'Оплатите @club219295292 ({price} ₽) по указанным реквизитам в течение 15 минут:\n@club219295292 ({configure.qiwi_pay})', keyboard=markup)
                        case 'USDT':
                            price_USDT = round(price / actualUSD(), 2)  # Сумма заказа в USDT
                            send_message(user, f'Оплатите @club219295292 ({price_USDT}) USDT по указанным реквизитам в течение 15 минут:\n@club219295292 ({configure.usdt_pay})', keyboard=markup)

                else:
                    send_message(user, 'На данный момент у вас нет активного заказа.\nСоздайте новый, отправив название предмета или ссылку на пост @club219295292 (SHOPPY | Продажа скинов CS:GO).')


            # Подтверждение оплаты
            elif message == 'Оплачено':

                send_message(user, 'Проверяю оплату... 🔎')

                # Получение информации о заказе
                orderData = getOrderData(user)
                status = orderData[4]  # Статус
                invoiceDate = datetime.strptime(orderData[5], '%d-%m-%Y %H:%M')  # Время выставления счета
                price = orderData[2]  # Сумма
                payment = orderData[3]  # Способ оплаты

                if status == '2':  # Если текущий заказ находится в статусе 'ВЫСТАВЛЕН СЧЕТ'

                    if (datetime.now() - invoiceDate).seconds < 900:  # Если с момента выставления счета прошло < 15 минут

                        # Проверка оплаты
                        match payment:
                            case 'Тинькофф':
                                if checkTinkoff(user, price, invoiceDate) == (user, True):
                                    transactionSuccess(user, price)
                                else:
                                    transactionNone(user, price, payment)
                            case 'СБЕР':
                                if checkSber(user, price, invoiceDate) == (user, True):
                                    transactionSuccess(user, price)
                                else:
                                    transactionNone(user, price, payment)
                            case 'QIWI':
                                if checkQIWI(user, price, invoiceDate) == (user, True):
                                    transactionSuccess(user, price)
                                else:
                                    transactionNone(user, price, payment)
                            case 'USDT':
                                price = round(price / actualUSD(), 2)  # Сумма заказа в USDT
                                if checkUSDT(user, price, invoiceDate) == (user, True):
                                    transactionSuccess(user, price)
                                else:
                                    transactionNone(user, price, payment)

                        # transactionSuccess(user, price)

                    else:
                        updateOrder(user, price, status=0)
                        send_message(user, 'С момента выставления счета прошло более 15 минут. Пожалуйста, создайте заказ заново.\nЕсли произошла ошибка, напишите нам в ЛС.')

                else:
                    send_message(user, 'На данный момент у вас нет активного заказа для оплаты. Если произошла ошибка, напишите нам в ЛС')


            # Ссылка на обмен [TEXT / URL]
            elif 'steamcommunity.com/tradeoffer' in message or event.attachments:

                # Если ссылка была отправлена как URL
                if event.attachments:
                    if event.attachments['attach1_type'] == 'link' and 'steamcommunity.com/tradeoffer' in event.attachments['attach1_url']:
                        message = event.attachments['attach1_url']
                    else:
                        send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\n\nПожалуйста, укажите ссылку на пост @club219295292 (SHOPPY | Продажа скинов CS:GO), либо название предмета из поста.')

                match getOrderData(user, onlyStatus=True):  # Проверка статуса заказа

                    case '2':  # ВЫСТАВЛЕН СЧЕТ
                        send_message(user, 'Пока мы не получили от вас оплату — обычно это происходит в течение 15 минут. Если произошла ошибка, напишите нам в ЛС')

                    case '3':  # ОПЛАЧЕНО

                        item = getOrderData(user, onlyItem=True)
                        price = getOrderData(user, onlyPrice=True)

                        if not '*' in item:  # Покупка
                            try:
                                # sendTradeOffer(item, message)  # Отправка предмета пользователю
                                print(f'SENDING OFFER: "{item}"')
                                updateOrder(user, price, status=4, tradeLink=message)  # Обновление статуса заказа на 'ВЫПОЛНЕН'
                                # delWithdrawnItem()  # Удаление предмета из Storage
                                # addSoldItem()  # Добавление предмета в Sold Items
                                send_message(user, f'Предмет [club219295292|{item}] успешно вам отправлен! Примите его в течение 2 часов.')
                            except:
                                send_message(user, 'Не удалось отправить обмен. Напишите нам в ЛС')

                        else:  # Бронь
                            print(f'ITEM HAS BEEN BOOKED: "{item.replace("*", "")}"')
                            sendDate = itemStatus(item.replace("*", ""))[1]  # Дата отправки предмета
                            updateOrder(user, price, status=4, tradeLink=message)  # Обновление статуса заказа на 'ВЫПОЛНЕН'
                            send_message(user, f'Предмет [club219295292|{item.replace("*", "")}] успешно забронирован!\nОн будет отправлен вам @club219295292 ({sendDate}) в 10:00 по МСК.')

                    case _:
                        send_message(user, 'У вас нет текущих заказов. Если произошла ошибка, напишите нам в ЛС')


            else:  # Указана неподдерживаемая фраза
                send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\n\nПожалуйста, укажите ссылку на пост @club219295292 (SHOPPY | Продажа скинов CS:GO), либо название предмета из поста.')


# Подтверждение заказа
def acceptItem(user, item, price, sendDate=''):

    markup = VkKeyboard(one_time=True)
    markup.add_button('Да', VkKeyboardColor.POSITIVE)
    markup.add_button('Нет', VkKeyboardColor.NEGATIVE)

    if not sendDate:  # Если предмет доступен для обмена
        send_message(user, f'Подтвердите покупку:\n[club219295292|{item}]\nЦена: @club219295292 ({price} ₽)', keyboard=markup)
    else:
        send_message(user, f'Подтвердите покупку:\n[club219295292|{item}]\nЦена: @club219295292 ({price} ₽)\nПредмет будет отправлен @club219295292 ({sendDate} в 10:00 МСК).', keyboard=markup)


# Выбор платежной системы
def choosePaymentSystem(user):
    markup = VkKeyboard(one_time=True)
    markup.add_button('Тинькофф', VkKeyboardColor.PRIMARY)
    markup.add_button('СБЕР', VkKeyboardColor.POSITIVE)
    markup.add_line()
    markup.add_button('QIWI', VkKeyboardColor.SECONDARY)
    markup.add_button('USDT', VkKeyboardColor.NEGATIVE)
    send_message(user, f'Выберите способ оплаты:', keyboard=markup)


# Успешная оплата
def transactionSuccess(user, price):
    updateOrder(user, price, status=3)  # Обновление статуса заказа на 'ОПЛАЧЕНО'
    send_message(user, 'Оплата получена ✅\nОтправьте вашу ссылку на обмен')


# Неуспешная оплата
def transactionNone(user, price, payment, USDT=False):
    currency = ' USDT' if USDT else '₽'
    send_message(f'Мы не получили от вас оплату {price}{currency} на {payment}.\nЕсли произошла ошибка, напишите нам в ЛС')
    deleteOrder(user, price)


# Недоступный способ оплаты
def unablePaymentWay(user):
    send_message(user, 'Данный способ оплаты на данный момент недоступен. Попробуйте один из других.')
    time.sleep(3)
    choosePaymentSystem(user)


# Формирование подтверждения заказа исходя из статуса предмета
def respondOnItemStatus(user, item, wallPrice, price=''):

    itemActualStatus = itemStatus(item)  # Поиск предмета по таблицам

    match itemActualStatus:  # Статус предмета

        case True:  # Доступен
            item_price = itemWallPrice(item) if wallPrice else price  # Поиск цены предмета
            if item_price is None:  # Если на стене такого предмета нет
                send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')
            else:
                acceptItem(user, item, item_price)

        case True, str():  # Недоступен для обмена
            item_price = itemWallPrice(item) if wallPrice else price  # Поиск цены предмета
            send_message(user, f'Обратите внимание, что предмет будет доступен для обмена @club219295292 ({itemActualStatus[1]} в 10:00 МСК).\nЕсли вы оплатите его сейчас, мы забронируем предмет и отправим его вам в указанную дату.')
            acceptItem(user, item, item_price, sendDate=itemActualStatus[1])  # Подтверждение покупки предмета

        case False:  # Продан
            send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, совсем скоро новое поступление! 🚚')

        case None:  # Отсутствует
            send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')


if __name__ == '__main__':
    main()
