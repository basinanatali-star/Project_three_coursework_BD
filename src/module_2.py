import psycopg2
from dotenv import load_dotenv
from config import DB_CONFIG

load_dotenv()


class DatabaseModels:
    """Класс для создания структуры БД"""

    def __init__(self) :
        self.connection = None
        self.cursor = None

    def connect(self):
        """Функция для устанавливления соединения с БД"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("Подключение к БД установлено")
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Функция для закрытия соединения с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("\nСоединение с БД закрыто")

    def create_tables(self):
        """Функция для создания таблиц с правильной структурой"""

        try:

            # Таблица стран
            create_countries = """
            CREATE TABLE IF NOT EXISTS countries (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                code VARCHAR(10),
                latitude FLOAT,
                longitude FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Таблица самолетов
            create_aeroplanes = """
            CREATE TABLE IF NOT EXISTS aeroplanes (
                id SERIAL PRIMARY KEY,
                icao24 VARCHAR(50) NOT NULL UNIQUE,
                callsign VARCHAR(50),
                country_id INTEGER REFERENCES countries(id) ON DELETE SET NULL,
                origin_country VARCHAR(100),
                speed FLOAT,
                baro_altitude FLOAT,
                latitude FLOAT,
                longitude FLOAT,
                heading FLOAT,
                true_track FLOAT,
                vertical_rate FLOAT,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Создаем таблицы
            self.cursor.execute(create_countries)
            print("Таблица countries создана")

            self.cursor.execute(create_aeroplanes)
            print("Таблица aeroplanes создана")

            # self.connection.commit()
            # print("Таблицы успешно созданы")

        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")
            self.connection.rollback()
            raise

    def create_indexes(self):
        """Функция для создания индексов"""
        try:
            # Проверяем существование колонки speed
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'aeroplanes'
                    AND column_name = 'speed'
                );
            """)
            speed_exists = self.cursor.fetchone()[0]

            if not speed_exists:
                print("Колонка 'speed' не существует!")
                print("Сначала выполните recreate_tables() или добавьте колонку вручную")
                return

            print("Колонка 'speed' найдена, создаем индексы...")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_aeroplanes_country ON aeroplanes(country_id);",
                "CREATE INDEX IF NOT EXISTS idx_aeroplanes_speed ON aeroplanes(speed);",
                "CREATE INDEX IF NOT EXISTS idx_aeroplanes_callsign ON aeroplanes(callsign);",
            ]

            for index in indexes:
                self.cursor.execute(index)

            self.connection.commit()
            print(f"Успешно создано {len(indexes)} индексов")
            return True

        except Exception as e:
            print(f"Ошибка создания индексов: {e}")
            self.connection.rollback()
        return False

    def drop_tables(self):
        """Функция для удаления всех таблиц"""
        try:
            self.cursor.execute("""
                DROP TABLE IF EXISTS aeroplanes CASCADE;
                DROP TABLE IF EXISTS countries CASCADE;
            """)
            self.connection.commit()
            print("Таблицы удалены")
        except Exception as e:
            print(f"Ошибка удаления таблиц: {e}")
            self.connection.rollback()
            raise

    def recreate_tables(self):
        """Функция для пересоздания таблиц с правильной структурой"""
        try:
            print("\nПересоздание таблиц...")
            self.drop_tables()
            self.create_tables()
            self.connection.commit()
            print("Таблицы пересозданы")
            return True
        except Exception as e:
            print(f"Ошибка пересоздания: {e}")
            self.connection.rollback()
            return False

    def init_database(self):
        """Функция для инициализизации БД"""
        if not self.connect():
            return False

        try:
            print("\nИнициализация базы данных...")

            # Пересоздаем таблицы с правильной структурой
            if not self.recreate_tables():
                print("Ошибка при пересоздании таблиц")
                return False

            # Создаем индексы
            self.create_indexes()

            print("\nИнициализация БД завершена")
            return True

        except Exception as e:
            print(f"\nОшибка инициализации: {e}")
            return False
        finally:
            self.disconnect()
