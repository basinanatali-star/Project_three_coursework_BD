import psycopg2
from psycopg2 import sql
from typing import List, Dict, Any, Optional
from config import DB_CONFIG


class DBManager:
    """Класс для управления данными в БД PostgreSQL"""

    def __init__(self):
        """Инициализация менеджера БД"""
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Устанавливает соединение с БД"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("✅ Подключение к БД установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Закрывает соединение с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔒 Соединение с БД закрыто")

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[tuple]]:
        """Выполняет запрос и возвращает результат"""
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return None

            self.cursor.execute(query, params)

            # Если это SELECT запрос, возвращаем данные
            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                # Для INSERT, UPDATE, DELETE делаем commit
                self.connection.commit()
                return None

        except Exception as e:
            print(f"❌ Ошибка выполнения запроса: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    # ============================================================
    # МЕТОДЫ ДЛЯ ЗАДАНИЯ
    # ============================================================

    def get_countries_and_aeroplanes_count(self) -> List[Dict[str, Any]]:
        """
        Получает список всех стран и количество самолетов
        в их воздушных пространствах.

        Returns:
            List[Dict]: Список словарей с ключами:
                - country_name (str): Название страны
                - aeroplanes_count (int): Количество самолетов
        """
        query = """
            SELECT 
                c.name AS country_name,
                COUNT(a.id) AS aeroplanes_count
            FROM countries c
            LEFT JOIN aeroplanes a ON c.id = a.country_id
            GROUP BY c.id, c.name
            ORDER BY aeroplanes_count DESC;
        """

        result = self.execute_query(query)
        if result:
            return [
                {
                    "country_name": row[0],
                    "aeroplanes_count": row[1]
                }
                for row in result
            ]
        return []

    def get_all_aeroplanes(self) -> List[Dict[str, Any]]:
        """
        Получает список всех воздушных судов.

        Returns:
            List[Dict]: Список словарей с ключами:
                - icao24 (str): ICAO код самолета
                - callsign (str): Позывной
                - country_name (str): Страна регистрации
                - speed (float): Скорость
                - altitude (float): Высота
                - latitude (float): Широта
                - longitude (float): Долгота
                - heading (float): Курс
                - last_seen (timestamp): Время последнего обновления
        """
        query = """
            SELECT 
                a.icao24,
                a.callsign,
                c.name AS country_name,
                a.speed,
                a.altitude,
                a.latitude,
                a.longitude,
                a.heading,
                a.last_seen
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id
            ORDER BY a.callsign NULLS LAST;
        """

        result = self.execute_query(query)
        if result:
            return [
                {
                    "icao24": row[0],
                    "callsign": row[1],
                    "country_name": row[2],
                    "speed": row[3],
                    "altitude": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "heading": row[7],
                    "last_seen": row[8]
                }
                for row in result
            ]
        return []

    def get_avg_speed(self) -> float:
        """
        Получает среднюю скорость по самолетам.

        Returns:
            float: Средняя скорость (м/с), округленная до 2 знаков
        """
        query = """
            SELECT 
                COALESCE(AVG(speed), 0) AS avg_speed
            FROM aeroplanes
            WHERE speed IS NOT NULL AND speed > 0;
        """

        result = self.execute_query(query)
        if result and result[0][0] is not None:
            return round(result[0][0], 2)
        return 0.0

    def get_aeroplanes_with_higher_speed(self) -> List[Dict[str, Any]]:
        """
        Получает список всех самолетов, у которых скорость выше средней.

        Returns:
            List[Dict]: Список словарей с ключами:
                - icao24 (str): ICAO код самолета
                - callsign (str): Позывной
                - country_name (str): Страна регистрации
                - speed (float): Скорость
                - altitude (float): Высота
                - latitude (float): Широта
                - longitude (float): Долгота
                - speed_difference (float): Разница со средней скоростью
        """
        query = """
            WITH avg_speed_cte AS (
                SELECT AVG(speed) AS avg_speed
                FROM aeroplanes
                WHERE speed IS NOT NULL AND speed > 0
            )
            SELECT 
                a.icao24,
                a.callsign,
                c.name AS country_name,
                a.speed,
                a.altitude,
                a.latitude,
                a.longitude,
                ROUND(a.speed - ac.avg_speed, 2) AS speed_difference
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id
            CROSS JOIN avg_speed_cte ac
            WHERE a.speed > ac.avg_speed
            ORDER BY a.speed DESC;
        """

        result = self.execute_query(query)
        if result:
            return [
                {
                    "icao24": row[0],
                    "callsign": row[1],
                    "country_name": row[2],
                    "speed": row[3],
                    "altitude": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "speed_difference": row[7]
                }
                for row in result
            ]
        return []

    def get_aeroplanes_with_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Получает список всех самолетов, в позывном которых
        содержатся переданные в метод символы.

        Args:
            keyword (str): Ключевое слово для поиска в позывном

        Returns:
            List[Dict]: Список словарей с ключами:
                - icao24 (str): ICAO код самолета
                - callsign (str): Позывной
                - country_name (str): Страна регистрации
                - speed (float): Скорость
                - altitude (float): Высота
                - latitude (float): Широта
                - longitude (float): Долгота
                - heading (float): Курс
                - last_seen (timestamp): Время последнего обновления
        """
        query = """
            SELECT 
                a.icao24,
                a.callsign,
                c.name AS country_name,
                a.speed,
                a.altitude,
                a.latitude,
                a.longitude,
                a.heading,
                a.last_seen
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id
            WHERE a.callsign IS NOT NULL 
                AND a.callsign != ''
                AND a.callsign ILIKE %s
            ORDER BY a.callsign;
        """

        result = self.execute_query(query, (f"%{keyword}%",))
        if result:
            return [
                {
                    "icao24": row[0],
                    "callsign": row[1],
                    "country_name": row[2],
                    "speed": row[3],
                    "altitude": row[4],
                    "latitude": row[5],
                    "longitude": row[6],
                    "heading": row[7],
                    "last_seen": row[8]
                }
                for row in result
            ]
        return []


# ============================================================
# ТЕСТИРОВАНИЕ
# ============================================================

def test_db_manager():
    """Тестирует все методы DBManager"""
    db = DBManager()

    if not db.connect():
        print("❌ Не удалось подключиться к БД")
        return

    print("\n" + "=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ DBManager")
    print("=" * 60)

    # 1. get_countries_and_aeroplanes_count()
    print("\n1️⃣ get_countries_and_aeroplanes_count()")
    print("-" * 40)
    countries = db.get_countries_and_aeroplanes_count()
    if countries:
        for item in countries[:10]:
            print(f"   {item['country_name']}: {item['aeroplanes_count']} самолетов")
        if len(countries) > 10:
            print(f"   ... и еще {len(countries) - 10} стран")
    else:
        print("   ⚠️ Нет данных")

    # 2. get_all_aeroplanes()
    print("\n2️⃣ get_all_aeroplanes()")
    print("-" * 40)
    planes = db.get_all_aeroplanes()
    if planes:
        print(f"   Всего самолетов: {len(planes)}")
        for plane in planes[:5]:
            callsign = plane['callsign'] or 'Без позывного'
            country = plane['country_name'] or 'Неизвестно'
            speed = plane['speed'] or 'Нет данных'
            print(f"   {callsign} ({country}) - скорость: {speed} м/с")
        if len(planes) > 5:
            print(f"   ... и еще {len(planes) - 5} самолетов")
    else:
        print("   ⚠️ Нет данных")

    # 3. get_avg_speed()
    print("\n3️⃣ get_avg_speed()")
    print("-" * 40)
    avg_speed = db.get_avg_speed()
    print(f"   Средняя скорость: {avg_speed} м/с")
    if avg_speed > 0:
        print(f"   ({(avg_speed * 3.6):.2f} км/ч)")

    # 4. get_aeroplanes_with_higher_speed()
    print("\n4️⃣ get_aeroplanes_with_higher_speed()")
    print("-" * 40)
    fast_planes = db.get_aeroplanes_with_higher_speed()
    if fast_planes:
        print(f"   Самолетов со скоростью выше средней: {len(fast_planes)}")
        for plane in fast_planes[:5]:
            callsign = plane['callsign'] or 'Без позывного'
            country = plane['country_name'] or 'Неизвестно'
            speed = plane['speed'] or 0
            diff = plane['speed_difference'] or 0
            print(f"   {callsign} ({country}): {speed} м/с (на {diff} м/с выше среднего)")
        if len(fast_planes) > 5:
            print(f"   ... и еще {len(fast_planes) - 5} самолетов")
    else:
        print("   ⚠️ Нет данных")

    # 5. get_aeroplanes_with_keyword()
    print("\n5️⃣ get_aeroplanes_with_keyword('AFL')")
    print("-" * 40)
    found = db.get_aeroplanes_with_keyword("AFL")
    if found:
        print(f"   Найдено самолетов с 'AFL': {len(found)}")
        for plane in found[:5]:
            callsign = plane['callsign'] or 'Без позывного'
            icao = plane['icao24']
            country = plane['country_name'] or 'Неизвестно'
            print(f"   {callsign} ({icao}) - {country}")
        if len(found) > 5:
            print(f"   ... и еще {len(found) - 5} самолетов")
    else:
        print("   ⚠️ Нет данных")

    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")
    print("=" * 60)

    db.disconnect()


if __name__ == "__main__":
    test_db_manager()