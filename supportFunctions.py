import requests


# Определение номера месяца по его названию [checkSBER()]
def getMonthNumber(month):
    month_mapping = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12"
    }
    return month_mapping.get(month.lower())


# Актуальный курс USD
def actualUSD():
    try:  # Binance P2P
        dataUSD = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=USDTRUB').json()
        return float(dataUSD['weightedAvgPrice'])
    except:  # ЦБ РФ
        dataUSD = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        return float(dataUSD['Valute']['USD']['Value'])
