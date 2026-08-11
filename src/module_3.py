import os
from datetime import datetime
from src.module_1 import get_country_bbox, parse_aircraft, get_aircraft_data
from src.module_2 import DatabaseModels


class DatabaseFiller:
    """Класс для заполнения БД данными из OpenSky"""

    def __init__(self):
        max_countries = os.getenv("MAX_COUNTRIES")
        self.db = DatabaseModels()  # Используем существующий класс
        self.connection = None
        self.cursor = None
        self.country_cache = {}
        self.max_countries = int(max_countries)
        self.countries_added = 0
        self.total_countries = 0
        self._connected = False

    def connect(self):
        """Функция для подключения БД через DatabaseModels"""
        try:
            if not self.db.connect():
                return False

            self.connection = self.db.connection
            self.cursor = self.db.cursor

            # Считаем страны, которые уже есть в БД
            self.cursor.execute("SELECT COUNT(*) FROM countries")
            self.total_countries = self.cursor.fetchone()[0]
            print(f"Стран в БД: {self.total_countries}/{self.max_countries}")

            if self.total_countries >= self.max_countries:
                print(f"В БД уже достигнут лимит стран: {self.total_countries}/{self.max_countries}")
            self._connected = True
            return True

        except Exception as e:
            print(f"Ошибка при подключении к БД: {e}")
            return False

    def disconnect(self):
        """Функция для отключения БД через DatabaseModels"""
        self.db.disconnect()
        self.connection = None
        self.cursor = None

    def get_or_create_country(self, country_name) -> None:
        """Функция для получения ID страны или создания новой записи"""
        if not country_name:
            return None

        country_name = country_name.strip()

        # Проверяем кэш
        if country_name in self.country_cache:
            return self.country_cache[country_name]

        try:
            # Ищем страну в БД
            self.cursor.execute("SELECT id FROM countries WHERE name = %s", (country_name,))
            result = self.cursor.fetchone()

            if result:
                country_id = result[0]
                self.country_cache[country_name] = country_id
                return country_id

            # Проверяем лимит
            if self.total_countries >= self.max_countries:
                raise RuntimeError(f"Достигнут лимит стран: {self.max_countries}")

            # Если страна не найдена, создаем новую, при этом получаем координаты страны через Nominatim
            coords = get_country_bbox(country_name)

            if coords:
                lat_min, lon_min, lat_max, lon_max = coords
                latitude = (lat_min + lat_max) / 2
                longitude = (lon_min + lon_max) / 2
            else:
                latitude = None
                longitude = None

            # Вставляем новую страну
            self.cursor.execute(
                """
                INSERT INTO countries (name, latitude, longitude)
                VALUES (%s, %s, %s)
                RETURNING id
            """,
                (country_name, latitude, longitude),
            )

            country_id = self.cursor.fetchone()[0]
            self.country_cache[country_name] = country_id
            self.connection.commit()
            self.countries_added += 1
            self.total_countries += 1

            print(f"Добавлена новая страна: {country_name} ({self.total_countries}/{self.max_countries})")
            return country_id

        except RuntimeError:
            self.connection.rollback()
            raise

        except Exception as e:
            print(f"Ошибка при работе со страной {country_name}: {e}")
            self.connection.rollback()
            return None

    def fill_countries(self, country_names) -> int:
        """Функция для заполнения таблицы countries списком стран."""
        for country_name in country_names:
            try:
                self.get_or_create_country(country_name)

            except RuntimeError as e:
                print(f"Заполнение остановлено: {e}")
                break

        print(f"Новых стран добавлено: {self.countries_added}")
        print(f"Всего стран в БД: {self.total_countries}/{self.max_countries}")

        return self.countries_added

    def save_aircraft_data(self, states_data) -> int:
        """Функция для сохранения данных о самолетах в БД"""
        if not states_data:
            print("Нет данных для сохранения")
            return 0

        saved_count = 0
        skipped_count = 0
        total_processed = 0

        for state in states_data:
            try:
                # Парсим данные самолета
                aircraft = parse_aircraft(state)
                total_processed += 1

                # Пропускаем, если нет основных данных
                icao24 = aircraft.get("icao24")

                if not icao24:
                    skipped_count += 1
                    continue

                country_name = aircraft.get("country")

                # Получаем ID страны (с учетом лимита)
                country_id = self.get_or_create_country(country_name)

                # Проверяем, существует ли уже такой самолет
                if country_name and country_id is None:
                    skipped_count += 1
                    continue

                # Получаем скорость из данных самолета
                velocity = aircraft.get("velocity")

                # Конвертируем скорость из м/с в км/ч
                if velocity is not None:
                    speed = velocity * 3.6
                else:
                    speed = None

                # Получаем курс самолета (направление движения)
                heading = aircraft.get("heading")

                if heading is None:
                    heading = aircraft.get("true_track")  # true_track - альтернативное название курса самолета

                # Получаем текущее время для отметки last_seen
                now = datetime.now()

                # Проверяем, существует ли уже самолет с таким ICAO-кодом в БД
                self.cursor.execute("SELECT id FROM aeroplanes WHERE icao24 = %s", (icao24,))

                # Получаем результат запроса
                existing = self.cursor.fetchone()

                # Oбновляем или создаём записи
                if existing is not None:
                    # Обновляем существующий самолет
                    aeroplane_id = existing[0]
                    self.cursor.execute(
                        """
                        UPDATE aeroplanes
                        SET callsign = %s,
                            country_id = %s,
                            origin_country = %s,
                            speed = %s,
                            baro_altitude = %s,
                            latitude = %s,
                            longitude = %s,
                            heading = %s,
                            last_seen = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """,
                        (
                            aircraft.get("callsign"),
                            country_id,
                            country_name,
                            speed,
                            aircraft.get("baro_altitude"),
                            aircraft.get("latitude"),
                            aircraft.get("longitude"),
                            heading,
                            now,
                            aeroplane_id,
                        ),
                    )

                else:
                    # Создаем новый самолет
                    self.cursor.execute(
                        """
                        INSERT INTO aeroplanes
                        (icao24, callsign, country_id, origin_country,
                         speed, baro_altitude, latitude, longitude, heading, last_seen)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """,
                        (
                            icao24,
                            aircraft.get("callsign"),
                            country_id,
                            country_name,
                            speed,
                            aircraft.get("baro_altitude"),
                            aircraft.get("latitude"),
                            aircraft.get("longitude"),
                            heading,
                            now,
                        ),
                    )

                saved_count += 1

            except RuntimeError as e:
                self.connection.rollback()
                print(f"Заполнение остановлено: {e}")
                break

            except Exception as e:
                print(f"Ошибка при сохранении самолета: {e}")
                self.connection.rollback()
                continue
        return saved_count

    def fill_database(self, token, country_name=None) -> bool :
        """Основная функция для заполнения БД"""
        print("\nНачинаем заполнение базы данных...")

        # Получаем данные из OpenSky
        if country_name:
            bbox = get_country_bbox(country_name)
            if bbox:
                states = get_aircraft_data(token, country_name, bbox)
            else:
                print(f"Не удалось найти координаты для {country_name}")
                return False
        else:
            states = get_aircraft_data(token)

        if not states:
            print("Данные не получены")
            return False

        # Сохраняем данные в БД
        saved = self.save_aircraft_data(states)

        print(f"Заполнение завершено. Сохранено: {saved} записей")
        return saved > 0
