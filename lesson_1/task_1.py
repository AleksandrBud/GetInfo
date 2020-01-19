#Посмотреть документацию к API GitHub, 
#разобраться как вывести список репозиториев для конкретного пользователя,
#сохранить JSON-вывод в файле *.json.


import requests
import json

main_link = 'https://api.github.com/users/AleksandrBud/repos'
response = requests.get(main_link)
if response.ok:
    data = json.loads(response.text)
    for row in data:
        print(row['name'])
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
else:
    print('Query is not ok!')
