import requests
from config import CLIENT_ID, CLIENT_SECRET, TOKEN_URL


def get_token():
    """
    Получает токен доступа к OpenSky API
    Возвращает токен или None в случае ошибки
    """
    print("Получаю токен...")

    # Данные для отправки
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    try:
        # Отправляем запрос
        response = requests.post(TOKEN_URL, data=data)

        # Проверяем успешность
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)
            print(f"Токен получен! Будет действовать {expires_in // 60} минут")
            return token
        else:
            print(f"Ошибка получения токена: {response.status_code}")
            print(f"Сообщение: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения: {e}")
        return None