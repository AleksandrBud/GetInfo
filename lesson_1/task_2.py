import requests
import json

# Изучить список открытых API.
# Найти среди них любое, требующее авторизацию (любого типа).
# Выполнить запросы к нему, пройдя авторизацию.
# Ответ сервера записать в файл.

main_link = "https://api.html2pdf.app/v1/generate"
header = {"Content-Type": "application/json"}
params = {
          "url": "https://www.yandex.ru",
          "apiKey": "7e4386c141e9cc7d8b9c724d82925e7d9c8790695a24fbd3578b279c22c208d2",
          }
response = requests.get(url=main_link, headers=header, params=params)
if response.ok:
    file = open('data2.pdf', 'wb')
    file.write(response.content)
else:
    print(response.status_code)
