from configure import proxy_ip, proxy_port, proxy_user, proxy_password
from proxy_class import ProxyExtension
import undetected_chromedriver as uc
import time


# Создание браузера через UC
def createBrowserUC(enableProxy, enableCookies=False, logging=True):

    options = uc.ChromeOptions()

    # Настройки Proxy для браузера
    if enableProxy:
        proxy = (proxy_ip, proxy_port, proxy_user, proxy_password)  # Данные Proxy
        proxy_extension = ProxyExtension(*proxy)
        options.add_argument(f"--load-extension={proxy_extension.directory}")

    # Настройки Cookies для браузера
    if enableCookies:
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument(r'user-data-dir=./Users/andrey/Library/ApplicationSupport/Google/Chrome')
        options.add_argument('--profile-directory=Profile 1')  # Chrome аккаунт

    # Создание браузера через UC
    t = 0  # Номер попытки
    while t < 10:
        try:
            driver = uc.Chrome(options=options)
            if logging:
                print(f"Successfully made UC browser with {t + 1} tries!\n")
            break
        except:
            t += 1
            time.sleep(1)
    if t >= 10:
        print("Unable to made UC browser!\n")

    # Параметры браузера
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })

    driver.set_page_load_timeout(10)  # Время на загрузку страниц
    driver.implicitly_wait(10)

    return driver
