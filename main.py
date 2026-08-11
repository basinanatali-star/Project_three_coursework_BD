from src.module_1 import get_aircraft_data, parse_aircraft, get_country_bbox
from src.module_2 import DatabaseModels
from src.module_3 import DatabaseFiller
from src.module_4 import test_db_manager
from src.getting_a_token import get_token
from config import COUNTRIES


def main():
    print("=" * 50)
    print("МОНИТОРИНГ САМОЛЕТОВ")
    print("=" * 50)

    # Получение токена
    token = get_token()
    if not token:
        print("Не удалось получить токен. Программа завершена.")
        return
    print("-" * 50)

    # Выбор всех самолетов в мире или конкретных странах
    print("\nВыберите режим работы:")
    print("1 - Получить все самолеты в мире")
    print("2 - Получить самолеты в конкретных странах")

    choice = input("\nВаш выбор (1 или 2): ").strip()

    if choice == "1":
        # Получение всех самолетов
        print("\n" + "-" * 50)
        states = get_aircraft_data(token)

        if states:
            print(f"\nВСЕГО САМОЛЕТОВ: {len(states)}")
            print("\nПервые 5 самолетов:")
            for i, state in enumerate(states[:5]):
                aircraft = parse_aircraft(state)
                print(f"\n{i + 1}. {aircraft['callsign']} ({aircraft['icao24']})")
                print(f"   Страна: {aircraft['country']}")
                if aircraft["latitude"] and aircraft["longitude"]:
                    print(f"   Координаты: {aircraft['latitude']:.4f}, {aircraft['longitude']:.4f}")
                else:
                    print("   Координаты: нет данных")
                if aircraft["baro_altitude"]:
                    print(f"   Высота: {aircraft['baro_altitude']:.0f} м")
                if aircraft["velocity"]:
                    print(f"   Скорость: {aircraft['velocity'] * 3.6:.0f} км/ч")
                print(f"   Статус: {'На земле' if aircraft['on_ground'] else 'В воздухе'}")
                if aircraft["category"]:
                    print(f"   Категория самолета: {aircraft['category']}")

    elif choice == "2":
        # Получение самолетов в конкретных странах
        print("\n" + "-" * 50)
        all_data = {}
        countries = COUNTRIES

        for country in countries:
            print(f"\nОбработка: {country}")
            bbox = get_country_bbox(country)

            if bbox:
                states = get_aircraft_data(token, country, bbox)
                all_data[country] = [parse_aircraft(s) for s in states]
            else:
                all_data[country] = []

        # Выводим результаты по странам
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ ПО СТРАНАМ")
        print("=" * 50)

        for country, aircrafts in all_data.items():
            print(f"\n{country}: {len(aircrafts)} самолетов")
            if aircrafts:
                print("   Список позывных:")
                for aircraft in aircrafts[:10]:  # Показываем первые 10
                    print(f"   - {aircraft['callsign']} ({aircraft['icao24']})")
                if len(aircrafts) > 10:
                    print(f"   ... и еще {len(aircrafts) - 10} самолетов")

    else:
        print("Неверный выбор")

    print("\n" + "=" * 50)
    print("СОЗДАНИЕ ТАБЛИЦ")
    print("=" * 50)

    db = DatabaseModels()
    db.init_database()

    print("\n" + "=" * 50)
    print("СТАТИСТИКА ЗАПОЛНЕНИЯ БД")
    print("=" * 50)

    # Получаем токен
    token = get_token()

    if not token:
        print("Токен не найден в .env файле")
        return
    try:
        # Создаем экземпляр для заполнения БД
        filler = DatabaseFiller()

        if not filler.connect():
            print("Не удалось подключиться к БД")
            return

        # Заполняем БД данными (все самолеты в мире)
        success = filler.fill_database(token)

        if success:
            print("\nБаза данных успешно заполнена!")
        else:
            print("\nНе удалось заполнить базу данных")

            # Отключаемся от БД
            filler.disconnect()

    except Exception as e:
        print(f"Ошибка: {e}")

    print("\n" + "=" * 50)
    print("ПОЛУЧЕНИЕ ИНФОРМАЦИИ ИЗ БД")
    print("=" * 50)

    test_db_manager()


if __name__ == "__main__":
    main()
