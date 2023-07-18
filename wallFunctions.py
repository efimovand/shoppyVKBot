import vk_api
import configure


# Поиск ЦЕНЫ продажи предмета
def itemWallPrice(item):

    vk_session = vk_api.VkApi(token=configure.personal_token)
    wall_posts = vk_session.method('wall.get', {'owner_id': -219295292, 'offset': 0, 'count': 20})['items']

    for i in wall_posts:
        post_text = i['text']  # Текст поста
        if item in post_text:
            post_text = post_text[post_text.find('Цена продажи: ') + 14:]
            return post_text[:post_text.find(' ₽')]  # Цена предмета

    return None


# Получение информации о предмете из поста ВК
def parsePost(url):

    vk_session = vk_api.VkApi(token=configure.personal_token)
    wall_posts = vk_session.method('wall.get', {'owner_id': -219295292, 'offset': 0, 'count': 20})['items']

    post_id = url[url.rfind('_') + 1:]  # ID поста

    for i in wall_posts:

        if str(i['id']) == post_id:  # Нужный пост

            post_text = i['text']  # Текст поста

            item = post_text[post_text.find('|') + 1:post_text.find(']')]  # Название предмета

            post_text = post_text[post_text.find('Цена продажи: ') + 14:]
            price =  post_text[:post_text.find(' ₽')]  # Цена предмета

            return item, price

    return False


# Добавление пометки 'ПРОДАНО' на пост
def editSoldPost(item):
    pass
