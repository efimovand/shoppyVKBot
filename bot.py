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


vk_session = vk_api.VkApi(token=configure.group_token)
longpoll = VkLongPoll(vk_session)


# Функция отправки сообщения пользователю
def send_message(user_id, message, keyboard=None):
    if not keyboard:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0})
    else:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0, 'keyboard': keyboard.get_keyboard()})


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

            message = event.text.replace('&quot;', '')  # Текст сообщения
            user = event.user_id  # ID пользователя


            # Если отправили ССЫЛКУ на пост
            if "vk.com/shoppycsgo?w=wall" in message or "vk.com/wall-" in message:

                send_message(user, 'Секунду, проверяю пост... 🔎')

                # Проверка наличия активного заказа у пользователя
                activeOrderInfo = isActiveOrder(user)
                if activeOrderInfo[0]:
                    send_message(user, f'У вас уже есть активный заказ. Завершите его, оплатив сумму {activeOrderInfo[1]} на {activeOrderInfo[2]}, или дождитесь истечения времени оплаты — 15 минут.')

                else:  # Если активного заказа нет

                    validationResult = parsePost(message)  # Проверка корректности ссылки и получение данных о предмете

                    if type(validationResult) == dict:

                        # Поиск предмета по таблицам
                        itemActualStatus = itemStatus(validationResult['name'])
                        match itemActualStatus:
                            case True:
                                acceptItem(user, validationResult['name'], validationResult['price'])  # Подтверждение покупки предмета
                            case True, str():
                                send_message(user, f'Обратите внимание, что предмет будет доступен для обмена {itemActualStatus[1]} в 10:00 по МСК.\nЕсли вы оплатите его сейчас, мы забронируем предмет и отправим его вам в указанную дату.')
                                acceptItem(user, validationResult['name'], validationResult['price'])  # Подтверждение брони предмета
                            case False:
                                send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                            case None:
                                send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                    else:  # Ссылка на неверный пост / ошибка проверки
                        send_message(user, validationResult)


            # Если отправили НАЗВАНИЕ предмета
            elif (' | ' in message) or (' (' in message) or (')' in message):

                # Проверка наличия активного заказа у пользователя
                activeOrderInfo = isActiveOrder(user)
                if activeOrderInfo[0]:
                    send_message(user, f'У вас уже есть активный заказ. Завершите его, оплатив сумму {activeOrderInfo[1]} на {activeOrderInfo[2]}, или дождитесь истечения времени оплаты — 15 минут.')

                else:  # Если активного заказа нет

                    if " | " in message and " (" in message and ")" in message:

                        send_message(user, 'Секунду, ищу предмет... 🔎')

                        message = message.replace('"', '').replace('\n', '')  # Удаление случайных символов из сообщения
                        print(message)

                        # Поиск предмета по таблицам
                        itemActualStatus = itemStatus(message)
                        match itemActualStatus:
                            case True:
                                item_price = itemWallPrice(message)  # Поиск цены предмета
                                acceptItem(user, event.text.replace('&quot;', ''), item_price)  # Подтверждение покупки предмета
                            case True, str():
                                send_message(user, f'Обратите внимание, что предмет будет доступен для обмена {itemActualStatus[1]} в 12:00 МСК.\nЕсли вы оплатите его сейчас, мы забронируем предмет и отправим его вам в указанную дату.')
                                item_price = itemWallPrice(message)  # Поиск цены предмета
                                acceptItem(user, event.text.replace('&quot;', ''), item_price)  # Подтверждение покупки предмета
                            case False:
                                send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                            case None:
                                send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                    else:
                        send_message(user, 'Введите полное название предмета на английском языке.\nЕго можно скопировать из поста с предметом на стене группы.\nНапример, "𝙰𝚆𝙿 | 𝙰𝚜𝚒𝚒𝚖𝚘𝚟 (𝙵𝚒𝚎𝚕𝚍-𝚃𝚎𝚜𝚝𝚎𝚍)"')


            # Подтверждение заказа
            elif message == 'Да' or message == 'Нет':

                if message == 'Да':  # Создание заказа и переход к оплате

                    last_message = get_last_message(user)  # Получение информации о последнем сообщении

                    if last_message['from_id'] == -219295292 and 'Подтвердите покупку' in last_message['text']:  # Если последнее сообщение было корректным

                        # Получение информации о предмете
                        last_message_text = last_message['text']
                        item = last_message_text[last_message_text.find('\n') + 1:last_message_text.rfind('\n')]
                        price = last_message_text[last_message_text.rfind('Цена: ') + 6:last_message_text.rfind(' ₽')]

                        addOrder(user, item, price)  # Создание заказа в БД
                        choosePaymentSystem(user)  # Выбор платежной системы

                    else:
                        send_message(user, 'Возможно, произошла ошибка.\n\nПожалуйста, укажите ссылку на пост https://vk.com/shoppycsgo, либо название предмета из поста.')

                else:
                    send_message(user, 'Проверьте ссылку на пост и попробуйте отправить ее заново. Если ошибка сохраняется, напишите @id222224804 (Администратору) - он сам проведет оплату и отправит вам предмет.')


            # Способ оплаты
            elif message == 'Тинькофф' or message == 'СБЕР' or message == 'QIWI' or message == 'USDT':

                price = getOrderData(user, onlyPrice=True)  # Сумма заказа
                updateOrder(user, price, status=2, payment=message)  # Обновление статуса заказа на 'ВЫСТАВЛЕН СЧЕТ'

                match message:

                    case 'Тинькофф':

                        send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.tinkoff_pay}')

                        if checkTinkoff(user, price) == (user, True):
                            transactionSuccess(user, price)
                        else:
                            transactionError(user, price, message)

                    case 'СБЕР':

                        send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.sber_pay}')

                        if checkSber(user, price) == (user, True):
                            transactionSuccess(user, price)
                        else:
                            transactionError(user, price, message)

                    case 'QIWI':

                        send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.qiwi_pay}')

                        if checkQIWI(user, price) == (user, True):
                            transactionSuccess(user, price)
                        else:
                            transactionError(user, price, message)

                    case 'USDT':

                        price_USDT = round(price / actualUSD(), 2)  # Цена заказа в USDT
                        send_message(user, f'Оплатите {price_USDT} USDT по указанным реквизитам в течение 15 минут:\n{configure.usdt_pay}')

                        if checkUSDT(user, price_USDT) == (user, True):
                            transactionSuccess(user, price_USDT)
                        else:
                            transactionError(user, price, message, USDT=True)


            # Ссылка на обмен [TEXT / URL]
            elif 'steamcommunity.com/tradeoffer' in message or event.attachments:

                # Если ссылка была отправлена как URL
                if event.attachments:
                    if event.attachments['attach1_type'] == 'link' and 'steamcommunity.com/tradeoffer' in event.attachments['attach1_url']:
                        message = event.attachments['attach1_url']
                    else:
                        send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\n\nПожалуйста, укажите ссылку на пост https://vk.com/shoppycsgo, либо название предмета из поста.')

                match getOrderData(user, onlyStatus=True):  # Проверка статуса заказа

                    case '2':  # ВЫСТАВЛЕН СЧЕТ
                        send_message(user, 'Пока мы не получили от вас оплату — обычно это происходит в течение 15 минут. Если произошла ошибка, напишите нам в ЛС')

                    case '3':  # ОПЛАЧЕНО
                        item = getOrderData(user, onlyItem=True)
                        price = getOrderData(user, onlyPrice=True)
                        try:
                            # sendTradeOffer(item, message)  # Отправка предмета пользователю
                            print(f'SENDING OFFER: "{item}"')
                            updateOrder(user, price, status=4)  # Обновление статуса заказа на 'ВЫПОЛНЕН'
                            send_message(user, f'Ваш предмет {item} вам успешно отправлен! Примите его в течение 2 часов.')
                        except:
                            send_message(user, 'Не удалось отправить обмен. Напишите нам в ЛС')

                    case '3*':  # ЗАБРОНИРОВАНО
                        pass

                    case _:
                        send_message(user, 'У вас нет текущих заказов. Если произошла ошибка, напишите нам в ЛС')


            else:  # Указана неподдерживаемая фраза
                send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\n\nПожалуйста, укажите ссылку на пост https://vk.com/shoppycsgo, либо название предмета из поста.')


# Подтверждение заказа
def acceptItem(user, name, price):
    markup = VkKeyboard(one_time=True)
    markup.add_button('Да', VkKeyboardColor.POSITIVE)
    markup.add_button('Нет', VkKeyboardColor.NEGATIVE)
    send_message(user, f'Подтвердите покупку:\n{name}\nЦена: {price} ₽', keyboard=markup)


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
def transactionError(user, price, message, USDT=False):
    currency = ' USDT' if USDT else '₽'
    send_message(f'Мы не получили от вас оплату {price}{currency} на {message} в течение 15 минут. Если произошла ошибка, напишите нам в ЛС')
    deleteOrder(user, price)


# Недоступный способ оплаты
def unablePaymentWay(user):
    send_message(user, 'Данный способ оплаты на данный момент недоступен. Попробуйте один из других.')
    time.sleep(3)
    choosePaymentSystem(user)


if __name__ == '__main__':
    main()
