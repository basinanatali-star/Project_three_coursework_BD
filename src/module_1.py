import requests
import os
from dotenv import load_dotenv


def get_aircraft_data(token, country_name=None, bbox=None):
    """
    Функция для получения данных о самолетах
    Если указан bbox - получает самолеты в конкретной области
    Иначе - все самолеты в мире
    """
    load_dotenv()
    url_opensky = os.getenv("API_URL_OPENSKY")

    headers = {"Authorization": f"Bearer {token}"}
    params = {}

    # Если передан ограничивающий прямоугольник - добавляем его в запрос
    if bbox:
        lat_min, lon_min, lat_max, lon_max = bbox
        params = {"lamin": lat_min, "lomin": lon_min, "lamax": lat_max, "lomax": lon_max, "extended": 1}
        print(f"Запрашиваю самолеты в области {country_name}...")
    else:
        print("Запрашиваю все самолеты в мире...")

    try:
        response = requests.get(url_opensky, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            print(f"Найдено самолетов: {len(states)}")
            return states
        else:
            print(f"Ошибка запроса: {response.status_code}")
            print(f"Сообщение: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения: {e}")
        return []


def get_country_bbox(country_name):
    """
    Функция для получения координат страны (ограничивающий прямоугольник страны через Nominatim API)
    """
    print(f"Ищу координаты для {country_name}...")

    load_dotenv()
    url_nominatim = os.getenv("API_URL_NOMINATIM")

    params = {"q": country_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "MyOpenSkyApp/1.0 (basinanatali@gmail.com)"}

    try:
        response = requests.get(url_nominatim, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data:
            print(f"Страна {country_name} не найдена")
            return None

        bbox = data[0]["boundingbox"]
        lat_min, lat_max = float(bbox[0]), float(bbox[1])
        lon_min, lon_max = float(bbox[2]), float(bbox[3])

        print(f"{country_name}: ({lat_min:.2f}, {lon_min:.2f}) - ({lat_max:.2f}, {lon_max:.2f})")
        return lat_min, lon_min, lat_max, lon_max

    except requests.exceptions.RequestException as e:
        print(f"Ошибка: {e}")
        return None


def safe_get_state_value(state, index, default=None):
    """Функция для преобразования данных о самолете.
    Безопасно получает значение из списка state, если индекс существует
    """
    return state[index] if len(state) > index else default


def parse_aircraft(state):
    """
    Функция для преобразования данных о самолете в читаемый словарь
    """
    return {
        "icao24": safe_get_state_value(state, 0, "Unknown"),
        "callsign": safe_get_state_value(state, 1, "N/A"),
        "country": safe_get_state_value(state, 2, "Unknown"),
        "time_position": safe_get_state_value(state, 3),
        "last_contact": safe_get_state_value(state, 4),
        "longitude": safe_get_state_value(state, 5),
        "latitude": safe_get_state_value(state, 6),
        "baro_altitude": safe_get_state_value(state, 7),
        "on_ground": safe_get_state_value(state, 8, False),
        "velocity": safe_get_state_value(state, 9),
        "true_track": safe_get_state_value(state, 10),
        "vertical_rate": safe_get_state_value(state, 11),
        "sensors": safe_get_state_value(state, 12),
        "geo_altitude": safe_get_state_value(state, 13),
        "squawk": safe_get_state_value(state, 14),
        "spi": safe_get_state_value(state, 15),
        "position_source": safe_get_state_value(state, 16),
        "category": safe_get_state_value(state, 17),
    }
