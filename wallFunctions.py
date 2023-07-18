import vk_api
import configure


# Поиск ЦЕНЫ продажи предмета
def itemWallInfo(item, onlyPrice=False):

    vk_session = vk_api.VkApi(token=configure.personal_token)
    wall_posts = vk_session.method('wall.get', {'owner_id': -219295292, 'offset': 0, 'count': 20})['items']

    if onlyPrice:  # Если запрошена только цена
        for i in wall_posts:
            post_text = i['text']  # Текст поста
            if item in post_text:
                post_text = post_text[post_text.find('Цена продажи: ') + 14:]
                return post_text[:post_text.find(' ₽')]  # Цена предмета

    else:  # Если запрошена полная информация о предмете
        for i in wall_posts:
            if item in i['text']:
                return {'id': i['id'], 'text': i['text'], 'image': i['attachments'][0]['photo']['id']}  # Получение ID, текста и изображения поста

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

    post_info = itemWallInfo(item)
    post_id = post_info['id']  # ID поста
    post_text = post_info['text']  # Текст поста
    post_image = str(post_info['image'])  # Изображение поста

    vk_session = vk_api.VkApi(token=configure.personal_token)
    vk_session.method('wall.edit', {'owner_id': -219295292, 'post_id': post_id, 'message': '🟣 ПРОДАНО 🟣' + '\n' + post_text, 'attachments': 'photo-219295292_' + post_image})
