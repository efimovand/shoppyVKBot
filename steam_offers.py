from steampy.client import SteamClient, Asset
from steampy.utils import GameOptions, get_key_value_from_url, account_id_to_steam_id
import configure


# Авторизация в Steam
steam_client = SteamClient(configure.steam_apiKey)
steam_client.login(configure.steam_username, configure.steam_password, configure.steam_guard)


# Поиск ID предмета в инвентаре по его названию
def find_item_id(item_hash_name, items):
    for item in items.values():
        market_hash_name = item['market_hash_name']
        if market_hash_name != item_hash_name:
            continue
        return {
            'market_hash_name': market_hash_name,
            'id': item['id']
        }


# Отправка трейда
def sendTradeOffer(give_item, trade_link):
    game = GameOptions.CS
    my_inventory = steam_client.get_my_inventory(game)  # Получение своего инвентаря CS:GO
    my_item = find_item_id(give_item, my_inventory)  # Поиск ID нужного предмета в инвентаре
    my_item = [Asset(my_item['id'], game)]

    steam_client.make_offer_with_url(my_item, [], trade_link)


item_to_send = ''  # Название предмета для отправки
buyer_trade_link = ''  # Трейд ссылка покупателя
sendTradeOffer(item_to_send, buyer_trade_link)  # Отправка обмена
