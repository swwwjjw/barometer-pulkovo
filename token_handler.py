import httpx

CLIENT_ID = "MI85K2MSM4M9BKE1D7TBBMI358QU9OQJ3ILI2CBJB81SI0K7HL2J6BO3H3TCM4OR"
CLIENT_SECRET = "V0IHK8VT0KGU14BDV742ITMGS65ISHUEUO0V8TV09R63NFU4294A25SUNKFLAQR1"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # Специальный URI для ручного ввода

# 1. Генерируем ссылку для авторизации
auth_url = f"https://hh.ru/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

print("=" * 50)
print("ШАГ 1: Откройте ЭТУ ссылку на ЛЮБОМ устройстве с браузером:")
print("=" * 50)
print(auth_url)
print("=" * 50)
print("\nИнструкция:")
print("1. Скопируйте ссылку выше")
print("2. Откройте ее в браузере на любом устройстве")
print("3. Авторизуйтесь в HH (войдите в аккаунт)")
print("4. Разрешите доступ приложению")
print("5. На странице увидите код авторизации")
print("6. Скопируйте этот код и вставьте ниже")
print("=" * 50)

# 2. Получаем код от пользователя
auth_code = input("\nВведите код авторизации с сайта HH: ").strip()

# 3. Получаем токены
with httpx.Client() as client:
    response = client.post(
        "https://hh.ru/oauth/token",
        data={
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'redirect_uri': REDIRECT_URI
        }
    )
    
    if response.status_code == 200:
        tokens = response.json()
        print(tokens)
        # Сохраняем токены в файл
        # with open("tokens.json", "w") as f:
        #    json.dump(tokens, f, indent=2)
        
        # print("Токены успешно получены и сохранены в tokens.json")
        # print(f"Access Token: {tokens['access_token'][:20]}...")
    else:
        print(f"Ошибка получения токена: {response.text}")