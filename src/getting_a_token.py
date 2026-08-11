import requests
import os
from dotenv import load_dotenv

def get_token():
    """
    Получает токен доступа к OpenSky API
    Возвращает токен или None в случае ошибки
    """
    print("Получаю токен...")

    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token_url = os.getenv("TOKEN_URL")

    # Данные для отправки
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        # Отправляем запрос
        response = requests.post(token_url, data=data)

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
