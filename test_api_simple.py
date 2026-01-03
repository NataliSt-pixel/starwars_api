"""
Тестирование Star Wars API без внешних зависимостей
"""
import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"


def make_request(method="GET", endpoint="", data=None, headers=None):
    """Универсальная функция для HTTP запросов"""
    url = f"{BASE_URL}{endpoint}"

    if headers is None:
        headers = {}

    if method == "POST" and data:
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

    request_data = None
    if data and method in ["POST", "PUT"]:
        if isinstance(data, dict):
            request_data = json.dumps(data).encode('utf-8')
        else:
            request_data = str(data).encode('utf-8')

    try:
        req = urllib.request.Request(
            url,
            data=request_data,
            headers=headers,
            method=method
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            return {
                "status": response.status,
                "headers": dict(response.headers),
                "data": json.loads(response_data) if response_data else None
            }

    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "error": e.reason,
            "data": e.read().decode('utf-8') if hasattr(e, 'read') else None
        }
    except Exception as e:
        return {
            "status": 0,
            "error": str(e),
            "data": None
        }


def wait_for_server():
    """Ожидание запуска сервера"""
    print("⏳ Ожидаю запуск сервера...")
    for i in range(30):
        try:
            response = make_request("GET", "/health")
            if response.get("status") == 200:
                print(" Сервер запущен!")
                return True
        except:
            time.sleep(0.5)
            if i % 10 == 0:
                print(f"   Попытка {i + 1}/30...")

    print(" Не удалось подключиться к серверу")
    print("   Убедитесь что сервер запущен: python run.py")
    return False


def test_health():
    """Тест проверки здоровья"""
    print("\n Тестирую /health...")
    response = make_request("GET", "/health")

    if response.get("status") == 200:
        data = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Service: {data.get('service', 'N/A')}")
        print(f"    Version: {data.get('version', 'N/A')}")
        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        return False


def test_get_characters():
    """Тест получения персонажей"""
    print("\n Тестирую GET /characters...")
    response = make_request("GET", "/characters")

    if response.get("status") == 200:
        data = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Total characters: {data.get('total', 0)}")
        print(f"    Page: {data.get('page', 1)}")

        characters = data.get("items", [])
        print(f"    Items on page: {len(characters)}")

        for i, char in enumerate(characters[:3]):
            print(f"       {char.get('name', 'Unknown')} (ID: {char.get('id', 'N/A')})")

        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        if response.get("data"):
            print(f"   Response: {response['data']}")
        return False


def test_get_character():
    """Тест получения конкретного персонажа"""
    print("\n Тестирую GET /characters/1...")
    response = make_request("GET", "/characters/1")

    if response.get("status") == 200:
        character = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Character: {character.get('name', 'Unknown')}")
        print(f"    Gender: {character.get('gender', 'N/A')}")
        print(f"    Birth year: {character.get('birth_year', 'N/A')}")
        return True
    elif response.get("status") == 404:
        print("     Character not found (maybe database is empty)")
        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        return False


def test_create_character():
    """Тест создания персонажа"""
    print("\n Тестирую POST /characters...")

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

    response = make_request(
        "POST",
        "/characters",
        data=new_character,
        headers={"Content-Type": "application/json"}
    )

    if response.get("status") in [200, 201]:
        data = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Created character: {data.get('name', 'Unknown')}")
        print(f"    ID: {data.get('id', 'N/A')}")
        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        if response.get("data"):
            print(f"   Response: {response['data']}")
        return False


def test_search():
    """Тест поиска"""
    print("\n Тестирую поиск...")

    query = "Luke"
    response = make_request("GET", f"/characters/search?q={query}")

    if response.get("status") == 200:
        data = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Found: {data.get('count', 0)} characters")

        results = data.get("results", [])
        for i, char in enumerate(results[:2]):
            print(f"       {char.get('name', 'Unknown')}")

        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        return False


def test_statistics():
    """Тест статистики"""
    print("\n Тестирую статистику...")
    response = make_request("GET", "/statistics")

    if response.get("status") == 200:
        stats = response.get("data", {})
        print(f"    Status: {response['status']}")
        print(f"    Total characters: {stats.get('total', 0)}")
        print(f"    By gender: {stats.get('by_gender', {})}")
        return True
    else:
        print(f"    Ошибка: {response.get('error', 'Unknown error')}")
        return False


def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print(" ТЕСТИРОВАНИЕ STAR WARS API")
    print("=" * 60)

    if not wait_for_server():
        return

    tests = [
        ("Health check", test_health),
        ("Get characters", test_get_characters),
        ("Get character by ID", test_get_character),
        ("Create character", test_create_character),
        ("Search characters", test_search),
        ("Statistics", test_statistics)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n Тест: {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"    ПРОЙДЕН")
            else:
                print(f"    НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"    ОШИБКА: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print(" РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "да" if success else "нет"
        print(f"{status} {test_name}")

    print("\n" + "=" * 60)
    print(f"Итого: {passed}/{total} тестов пройдено")

    if passed == total:
        print(" ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")

        print("\n Примеры использования API через curl:")
        print("   # Получить всех персонажей")
        print("   curl http://localhost:8000/api/characters")
        print()
        print("   # Создать нового персонажа")
        print('   curl -X POST http://localhost:8000/api/characters \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"uid": 1000, "name": "Yoda", "gender": "male"}\'')
        print()
        print("   # Поиск персонажей")
        print("   curl http://localhost:8000/api/characters/search?q=skywalker")
    else:
        print(f"  Пройдено только {passed} из {total} тестов")

    print("=" * 60)


def main():
    """Основная функция"""
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()