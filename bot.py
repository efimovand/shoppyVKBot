import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import configure
from validatePost import validatePost
from itemInfo import itemStatus, itemWallPrice


vk_session = vk_api.VkApi(token=configure.group_token)
longpoll = VkLongPoll(vk_session)


# Функция отправки сообщения пользователю
def send_message(user_id, message):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0})


def main():

    print("BOT is working...")

    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            message = event.text.lower()  # Текст сообщения
            user = event.user_id  # ID пользователя


            # Если отправили ССЫЛКУ на пост
            if "vk.com/shoppycsgo?w=wall" in message or "vk.com/wall-" in message:

                send_message(user, 'Секунду, проверяю пост... 🔎')

                validationResult = validatePost(message)  # Проверка корректности ссылки и получение данных о предмете

                if type(validationResult) == dict:

                    # Поиск предмета по таблицам
                    itemActualStatus = itemStatus(message)
                    match itemActualStatus:
                        case True:
                            acceptItem(validationResult['name'], validationResult['price'])
                        case False:
                            send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                        case _:
                            send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                else:  # Ссылка на неверный пост / ошибка проверки
                    send_message(user, validationResult)


            # Если отправили НАЗВАНИЕ предмета
            elif " | " or message or " (" in message or ")" in message:

                if " | " in message and " (" in message and ")" in message:

                    message = message.replace('"', '').replace('\n', '')  # Удаление случайных символов из сообщения

                    # Поиск предмета по таблицам
                    itemActualStatus = itemStatus(message)
                    match itemActualStatus:
                        case True:
                            item_price = itemWallPrice(message)
                            acceptItem(message, item_price)
                        case False:
                            send_message(user, 'К сожалению, данный предмет был недавно продан.\nНо не стоит расстраиваться, ведь скоро новое поступление! 🚚')
                        case _:
                            send_message(user, 'К сожалению, данный предмет не найден. Попробуйте указать ссылку на пост с предметом или повторите попытку позже.')

                else:
                    send_message(user, 'Введите полное название предмета на английском языке.\nЕго можно скопировать из поста с предметом на стене группы.\nНапример, "𝙰𝚆𝙿 | 𝙰𝚜𝚒𝚒𝚖𝚘𝚟 (𝙵𝚒𝚎𝚕𝚍-𝚃𝚎𝚜𝚝𝚎𝚍)"')


            else:  # Указана не ССЫЛКА на любой пост / не НАЗВАНИЕ предмета
                send_message(user, 'Данный бот может получить ссылку на пост со стены сообщества или название желаемого предмета, а затем принять оплату и передать вам предмет.\nПожалуйста, укажите ссылку на пост [https://vk.com/shoppycsgo|SHOPPY | Продажа скинов CSGO], либо название предмета из поста.')


def acceptItem(name, price):
    pass


if __name__ == '__main__':
    main()