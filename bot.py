import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardButton, VkKeyboardColor
import configure
from validatePost import validatePost
from itemInfo import itemStatus, itemWallPrice
from googleSheets import addOrder, getOrderData, updateOrder
from checkPayment import checkTinkoff, checkSber, checkQIWI, checkUSDT
# from steam_offers import sendTradeOffer


vk_session = vk_api.VkApi(token=configure.group_token)
longpoll = VkLongPoll(vk_session)


# Функция отправки сообщения пользователю
def send_message(user_id, message, keyboard=None):
    if not keyboard:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0})
    else:
        vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0, 'keyboard': keyboard.get_keyboard()})


def main():

    print("BOT is working...")

    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            message = event.text  # Текст сообщения
            user = event.user_id  # ID пользователя


            # Если отправили ССЫЛКУ на пост
            if "vk.com/shoppycsgo?w=wall" in message or "vk.com/wall-" in message:

                send_message(user, 'Секунду, проверяю пост... 🔎')

                validationResult = validatePost(message)  # Проверка корректности ссылки и получение данных о предмете

                if type(validationResult) == dict:

                    # Поиск предмета по таблицам
                    itemActualStatus = itemStatus(validationResult['name'])
                    match itemActualStatus:
                        case True:
                            acceptItem(user, validationResult['name'], validationResult['price'])  # Подтверждение покупки предмета
                        case False:
                            send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                        case _:
                            send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                else:  # Ссылка на неверный пост / ошибка проверки
                    send_message(user, validationResult)


            # Если отправили НАЗВАНИЕ предмета
            elif (' | ' in message) or (' (' in message) or (')' in message):

                if " | " in message and " (" in message and ")" in message:

                    send_message(user, 'Секунду, ищу предмет... 🔎')

                    message = message.replace('"', '').replace('\n', '')  # Удаление случайных символов из сообщения

                    # Поиск предмета по таблицам
                    itemActualStatus = itemStatus(message)
                    match itemActualStatus:
                        case True:
                            item_price = itemWallPrice(message)  # Поиск цены предмета
                            acceptItem(user, event.text, item_price)  # Подтверждение покупки предмета
                        case False:
                            send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                        case _:
                            send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                else:
                    send_message(user, 'Введите полное название предмета на английском языке.\nЕго можно скопировать из поста с предметом на стене группы.\nНапример, "𝙰𝚆𝙿 | 𝙰𝚜𝚒𝚒𝚖𝚘𝚟 (𝙵𝚒𝚎𝚕𝚍-𝚃𝚎𝚜𝚝𝚎𝚍)"')


            # Подтверждение покупки предмета
            elif message == 'Да' or message == 'Нет':
                if message == 'Да':
                    choosePaymentSystem(user)
                else:
                    send_message(user, 'Проверьте ссылку на пост и попробуйте отправить ее заново. Если ошибка сохраняется, напишите [*https://vk.com/id222224804|Администратору] - он сам проведет оплату и отправит вам предмет.')


            # Оплата
            elif message == 'Тинькофф' or message == 'СБЕР' or message == 'QIWI' or message == 'USDT':

                price = getOrderData(user, onlyPrice=True)  # Сумма заказа

                match message:
                    case 'Тинькофф':
                        # send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.tinkoff_pay}')
                        # if checkTinkoff(user, price) == (user, True):
                        #     transactionSuccess(user, price)
                        # else:
                        #     send_message(user, f'Мы не получили от вас оплату {price}₽ на {message} в течение 15 минут. Если произошла ошибка, напишите нам в ЛС')
                        unablePaymentWay(user)

                    case 'СБЕР':
                        # send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.sber_pay}')
                        # if checkSber(user, price) == (user, True):
                        #     transactionSuccess(user, price)
                        # else:
                        #     send_message(f'Мы не получили от вас оплату {price} на {message}₽ в течение. Если произошла ошибка, напишите нам в ЛС')
                        unablePaymentWay(user)

                    case 'QIWI':
                        send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.qiwi_pay}')
                        if checkQIWI(user, price) == (user, True):
                            transactionSuccess(user, price)
                        else:
                            send_message(f'Мы не получили от вас оплату {price} на {message}₽ в течение. Если произошла ошибка, напишите нам в ЛС')

                    case 'USDT':
                        # send_message(user, f'Оплатите {price}₽ по указанным реквизитам в течение 15 минут:\n{configure.usdt_pay}')
                        # if checkUSDT(user, price) == (user, True):
                        #     transactionSuccess(user, price)
                        # else:
                        #     send_message(f'Мы не получили от вас оплату {price} на {message}₽ в течение. Если произошла ошибка, напишите нам в ЛС')
                        unablePaymentWay(user)


            # Ссылка на обмен [TEXT / URL]
            elif 'steamcommunity.com/tradeoffer' in message or event.attachments:

                # Если ссылка была отправлена как URL
                if event.attachments:
                    if event.attachments['attach1_type'] == 'link' and 'steamcommunity.com/tradeoffer' in event.attachments['attach1_url']:
                        message = event.attachments['attach1_url']

                if getOrderData(user, onlyStatus=True) == '3':  # Если статус заказа 'ОПЛАЧЕНО'
                    item = getOrderData(user, onlyItem=True)
                    price = getOrderData(user, onlyPrice=True)
                    try:
                        # sendTradeOffer(item, message)  # Отправка предмета пользователю
                        updateOrder(user, status=4, price=price)  # Обновление статуса заказа на 'ВЫПОЛНЕН'
                        pass  # Удаление заказа из активных
                        send_message(user, f'Ваш предмет {item} вам успешно отправлен! Примите его в течение 2 часов.')
                    except:
                        send_message(user, 'Не удалось отправить обмен. Напишите нам в ЛС')

                else:
                    send_message(user, 'У вас нет текущих заказов. Если произошла ошибка, напишите нам в ЛС')


            else:  # Указана неподдерживаемая фраза
                send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\n\nПожалуйста, укажите ссылку на пост https://vk.com/shoppycsgo, либо название предмета из поста.')


def acceptItem(user, name, price):
    markup = VkKeyboard(one_time=True)
    markup.add_button('Да', VkKeyboardColor.POSITIVE)
    markup.add_button('Нет', VkKeyboardColor.NEGATIVE)
    send_message(user, f'Подтвердите покупку:\n{name}\nЦена: {price} ₽', keyboard=markup)
    addOrder(user, name, price)


def choosePaymentSystem(user):
    markup = VkKeyboard(one_time=True)
    markup.add_button('Тинькофф', VkKeyboardColor.PRIMARY)
    markup.add_button('СБЕР', VkKeyboardColor.POSITIVE)
    markup.add_line()
    markup.add_button('QIWI', VkKeyboardColor.SECONDARY)
    markup.add_button('USDT', VkKeyboardColor.NEGATIVE)
    send_message(user, f'Выберите способ оплаты:', keyboard=markup)


def transactionSuccess(user, price):
    updateOrder(user, 3, price=price)
    send_message(user, 'Оплата получена ✅\nОтправьте вашу ссылку на обмен')


def unablePaymentWay(user):
    send_message(user, 'Данный способ оплаты на данный момент не работает. Попробуйте QIWI')


if __name__ == '__main__':
    main()