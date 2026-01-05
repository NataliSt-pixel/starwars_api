import pytest
import asyncio
import aiohttp
import json


async def test_health_check():
    """Тест проверки здоровья"""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/health') as response:
            assert response.status == 200
            data = await response.json()
            assert data['status'] == 'ok'


async def test_register_and_login():
    """Тест регистрации и входа"""
    async with aiohttp.ClientSession() as session:
        user_data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'test123'
        }

        async with session.post('http://localhost:8000/api/register',
                                json=user_data) as response:
            assert response.status == 201
            data = await response.json()
            assert data['username'] == 'testuser2'

        async with session.post('http://localhost:8000/api/login',
                                json={'username': 'testuser2', 'password': 'test123'}) as response:
            assert response.status == 200
            data = await response.json()
            assert 'access_token' in data
            return data['access_token']


async def test_create_ad_with_auth():
    """Тест создания объявления с аутентификацией"""
    token = await test_register_and_login()

    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'Bearer {token}'}

        ad_data = {
            'title': 'Test Advertisement',
            'description': 'This is a test advertisement'
        }

        async with session.post('http://localhost:8000/api/ads',
                                json=ad_data,
                                headers=headers) as response:
            assert response.status == 201
            data = await response.json()
            assert data['title'] == 'Test Advertisement'


async def test_get_ads():
    """Тест получения объявлений"""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/ads') as response:
            assert response.status == 200
            data = await response.json()
            assert 'items' in data
            assert 'total' in data


async def run_all_tests():
    """Запуск всех тестов"""
    print("Запуск тестов Advertisements API...")

    tests = [
        test_health_check,
        test_register_and_login,
        test_create_ad_with_auth,
        test_get_ads
    ]

    for test in tests:
        try:
            await test()
            print(f" {test.__name__}")
        except Exception as e:
            print(f" {test.__name__}: {e}")


if __name__ == '__main__':
    asyncio.run(run_all_tests())