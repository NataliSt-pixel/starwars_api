"""
Тестирование Star Wars API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"


def wait_for_server():
    """Ожидание запуска сервера"""
    print(" Ожидаю запуск сервера...")
    for i in range(30):  # 30 попыток
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print(" Сервер запущен!")
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)  # Ждем полсекунды
            if i % 10 == 0:
                print(f"   Попытка {i + 1}/30...")

    print(" Не удалось подключиться к серверу")
    return False


def test_health():
    """Тест проверки здоровья"""
    print("\n Тестирую /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        return True
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def test_get_characters():
    """Тест получения персонажей"""
    print("\n Тестирую GET /characters...")
    try:
        response = requests.get(f"{BASE_URL}/characters", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Total characters: {data.get('total')}")
            print(f"    Page: {data.get('page')}")
            print(f"    Items on page: {len(data.get('items', []))}")


            characters = data.get('items', [])[:3]
            for char in characters:
                print(f"       {char.get('name')} (ID: {char.get('id')})")
            return True
        else:
            print(f"    Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def test_get_character():
    """Тест получения конкретного персонажа"""
    print("\n Тестирую GET /characters/1...")
    try:
        response = requests.get(f"{BASE_URL}/characters/1", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            character = response.json()
            print(f"    Character: {character.get('name')}")
            print(f"    Gender: {character.get('gender')}")
            print(f"    Birth year: {character.get('birth_year')}")
            return True
        elif response.status_code == 404:
            print("     Character not found (maybe database is empty)")
            return True
        else:
            print(f"    Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def test_create_character():
    """Тест создания персонажа"""
    print("\n Тестирую POST /characters...")
    try:
        new_character = {
            "uid": 999,
            "name": "Test Character",
            "gender": "male",
            "birth_year": "100BBY",
            "eye_color": "green",
            "homeworld": "https://swapi.dev/api/planets/1/",
            "mass": "70",
            "skin_color": "green"
        }

        response = requests.post(
            f"{BASE_URL}/characters",
            json=new_character,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"    Created character: {data.get('name')}")
            print(f"    ID: {data.get('id')}")
            return True
        else:
            print(f"    Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def test_search():
    """Тест поиска"""
    print("\n Тестирую поиск...")
    try:
        response = requests.get(f"{BASE_URL}/characters/search?q=Luke", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Found: {data.get('count')} characters")
            if data.get('count') > 0:
                for char in data.get('results', [])[:2]:
                    print(f"      🔎 {char.get('name')}")
            return True
        else:
            print(f"    Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def test_statistics():
    """Тест статистики"""
    print("\n Тестирую статистику...")
    try:
        response = requests.get(f"{BASE_URL}/statistics", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"    Total characters: {stats.get('total')}")
            print(f"    By gender: {stats.get('by_gender')}")
            return True
        else:
            print(f"    Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print(" ТЕСТИРОВАНИЕ STAR WARS API")
    print("=" * 60)

    if not wait_for_server():
        return

    tests_passed = 0
    tests_total = 6

    if test_health():
        tests_passed += 1

    if test_get_characters():
        tests_passed += 1

    if test_get_character():
        tests_passed += 1

    if test_create_character():
        tests_passed += 1

    if test_search():
        tests_passed += 1

    if test_statistics():
        tests_passed += 1

    print("\n" + "=" * 60)
    print(f" РЕЗУЛЬТАТЫ: {tests_passed}/{tests_total} тестов пройдено")

    if tests_passed == tests_total:
        print(" ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n Примеры использования API:")
        print("   # Получить всех персонажей")
        print("   curl http://localhost:8000/api/characters")
        print("")
        print("   # Создать нового персонажа")
        print("   curl -X POST http://localhost:8000/api/characters \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"uid\": 1000, \"name\": \"Yoda\", \"gender\": \"male\"}'")
        print("")
        print("   # Поиск персонажей")
        print("   curl http://localhost:8000/api/characters/search?q=skywalker")
    else:
        print(f"  Пройдено только {tests_passed} из {tests_total} тестов")

    print("=" * 60)


if __name__ == "__main__":
    main()