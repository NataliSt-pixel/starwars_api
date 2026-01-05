#!/bin/bash

echo "Тестирование Advertisements API"
echo "=================================="
echo "1. Проверка здоровья API..."
curl -s http://localhost:8000/api/health | jq '.'
echo -e "\n2. Регистрация пользователя..."
curl -s -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "test123"}' | jq '.'

echo -e "\n3. Вход пользователя..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}' | jq -r '.access_token')

echo "Токен получен: ${TOKEN:0:20}..."
echo -e "\n4. Создание объявления..."
curl -s -X POST http://localhost:8000/api/ads \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Продам велосипед", "description": "Отличный горный велосипед"}' | jq '.'

echo -e "\n5. Получение всех объявлений..."
curl -s http://localhost:8000/api/ads | jq '.'