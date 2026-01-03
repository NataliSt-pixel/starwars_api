"""
Тестирование API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_health():
    """Тест проверки здоровья"""
    print(" Тестирую /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()


def test_get_characters():
    """Тест получения персонажей"""
    print(" Тестирую GET /characters...")
    response = requests.get(f"{BASE_URL}/characters")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Total characters: {data['total']}")
    print(f"   Page: {data['page']}")
    print(f"   Items on page: {len(data['items'])}")
    print()


def test_get_character():
    """Тест получения конкретного персонажа"""
    print(" Тестирую GET /characters/1...")
    response = requests.get(f"{BASE_URL}/characters/1")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        character = response.json()
        print(f"   Character: {character['name']}")
        print(f"   Gender: {character['gender']}")
    print()


def test_create_character():
    """Тест создания персонажа"""
    print(" Тестирую POST /characters...")
    new_character = {
        "uid": 999,
        "name": "Test Character",
        "gender": "male",
        "birth_year": "100BBY",
        "eye_color": "green"
    }

    response = requests.post(
        f"{BASE_URL}/characters",
        json=new_character,
        headers={"Content-Type": "application/json"}
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print(f"   Created character: {response.json()['name']}")
    print()


def test_search():
    """Тест поиска"""
    print(" Тестирую поиск...")
    response = requests.get(f"{BASE_URL}/characters/search?q=Luke")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Found: {data['count']} characters")
    print()


def test_statistics():
    """Тест статистики"""
    print(" Тестирую статистику...")
    response = requests.get(f"{BASE_URL}/statistics")
    print(f"   Status: {response.status_code}")
    stats = response.json()
    print(f"   Total: {stats['total']}")
    print(f"   By gender: {stats['by_gender']}")
    print()


def main():
    """Основная функция тестирования"""
    print("=" * 50)
    print(" ТЕСТИРОВАНИЕ STAR WARS API")
    print("=" * 50)

    try:
        test_health()
        test_get_characters()
        test_get_character()
        test_create_character()
        test_search()
        test_statistics()

        print(" Все тесты завершены!")

    except requests.exceptions.ConnectionError:
        print(" Не удалось подключиться к серверу")
        print(" Убедитесь что сервер запущен: python run.py")
    except Exception as e:
        print(f" Ошибка: {e}")


if __name__ == "__main__":
    main()