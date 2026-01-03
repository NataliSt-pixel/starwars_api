"""
Простая проверка Star Wars API
"""
import urllib.request
import json


def check_api():
    print(" Проверка Star Wars API...")
    print("=" * 50)

    try:
        print("1. Проверка здоровья API...")
        with urllib.request.urlopen('http://localhost:8000/api/health', timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"    Статус: {response.status}")
            print(f"    Сервис: {data.get('service')}")
            print(f"    Версия: {data.get('version')}")

        print("\n2. Получение списка персонажей...")
        with urllib.request.urlopen('http://localhost:8000/api/characters', timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"    Всего персонажей: {data.get('total')}")
            print(f"    На странице: {len(data.get('items', []))}")

            for char in data.get('items', [])[:3]:
                print(f"       {char.get('name')} (ID: {char.get('id')})")

        print("\n3. Статистика...")
        with urllib.request.urlopen('http://localhost:8000/api/statistics', timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"    Всего: {data.get('total')}")
            print(f"    По полу: {data.get('by_gender')}")

        print("\n" + "=" * 50)
        print(" API работает корректно!")
        print("\n Доступные эндпоинты:")
        print("   http://localhost:8000/api/health")
        print("   http://localhost:8000/api/characters")
        print("   http://localhost:8000/api/characters/1")
        print("   http://localhost:8000/api/characters/search?q=Luke")
        print("   http://localhost:8000/api/statistics")
        print("=" * 50)

    except urllib.error.URLError as e:
        print(f" Не удалось подключиться к серверу: {e}")
        print("\n Убедитесь что сервер запущен:")
        print("   python run.py")
    except Exception as e:
        print(f" Ошибка: {e}")


if __name__ == "__main__":
    check_api()