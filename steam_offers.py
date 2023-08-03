from steampy.client import SteamClient, Asset
from steampy.utils import GameOptions, get_key_value_from_url, account_id_to_steam_id
import configure


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
def sendTradeOffer(give_item, trade_link, sender):

    # Авторизация в Steam
    steam_client = SteamClient(configure.steam_apiKey)
    steam_client.login(configure.steam_username, configure.steam_password, f"steam_guard_{sender}.json")  # Активный аккаунт

    # Поиск нужного предмета
    my_inventory = steam_client.get_my_inventory(GameOptions.CS)  # Получение своего инвентаря CS:GO
    my_item = find_item_id(give_item, my_inventory)  # Поиск ID нужного предмета в инвентаре
    my_asset = [Asset(my_item['id'], GameOptions.CS)]

    # Отправка обмена
    try:
        steam_client.make_offer_with_url(my_asset, [], trade_link)
    except Exception as e:
        print(e)
