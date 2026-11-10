# Завдання №2 — CI для API

Конвеєр `.github/workflows/ci.yml` запускається на pull_request та push у main.

1. **API lint (Ruff)**: Ubuntu 24.04, Python 3.11.9, встановлення lockfile та перевірка Python-коду. Конфігурація — pyproject.toml. Перевіряються синтаксис, невизначені імена та невикористані імпорти (E4/E7/E9/F).
2. **API tests (PostgreSQL + Redis)**: запускається після успішного Ruff. PostgreSQL 15.10 та Redis 7.4.2 — окремі job services з health checks. Перед pytest додатково виконуються справжні SELECT 1 і Redis PING.
3. Після успішних тестів інтеграційний тест повторюється з недоступним портом PostgreSQL. Крок успішний лише якщо pytest повернув код 1 з OperationalError; це підтверджує залежність тесту від реальної бази.

Версії actions/checkout v4.2.2 та actions/setup-python v5.6.0 закріплено точними commit SHA. Дозволи workflow — лише contents: read. Secrets для тестового середовища не потрібні: його пароль і JWT-ключ призначені виключно для тимчасового CI.

## Залежності та кеш

requirements-ci.in додає pytest, httpx і Ruff до наявних залежностей. requirements-ci.txt містить точні версії прямих і транзитивних пакетів з SHA256-хешами; встановлення виконується з --require-hashes. Lockfile враховує Mac і Linux. setup-python кешує pip, ключ залежить від lockfile. Кеш не замінює встановлення пакетів.

Оновлення lockfile (з папки API, uv 0.12.14):

```bash
uv pip compile requirements-ci.in --python-version 3.11 --universal --generate-hashes -o requirements-ci.txt
```

## Тести

- test_health.py: два сценарії доступності Redis. З'єднання main.engine.connect заборонено; /health має відповідати без PostgreSQL. Redis тут підмінено для передбачуваної перевірки обох станів.
- test_postgres.py: створює користувача та список у справжній PostgreSQL, очищує ORM identity map, викликає GET /wishlists/{id} і перевіряє отримані id/title. get_db підключено до реальної тестової транзакції; SQL не підмінено. Після тесту транзакція відкочується. Тест вимагає явний TEST_DATABASE_URL із назвою бази, що закінчується на _test, і не використовує робочу базу з .env.

Створення таблиць перенесено з імпорту main.py в lifespan FastAPI. Під час звичайного старту таблиці створюються, але імпорт модуля та запит health у unit-тесті не потребують бази.

## Локальна перевірка

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-ci.txt
python -m ruff check .
python -m pytest tests/test_health.py -v
```

Для повного pytest потрібна окрема PostgreSQL-база wishlist_test (не wishlist із завдання №1):

```bash
export TEST_DATABASE_URL='postgresql://wishlist_ci:ci-only-password@localhost:15433/wishlist_test'
python -m pytest -v
```

На Mac локально підтверджено Ruff та обидва health-сценарії, а також очікуваний провал PostgreSQL-тесту на недоступному порту. Позитивний інтеграційний тест і готовність обох job services перевіряються фактичним запуском GitHub Actions; посилання на результат додається після завершення.

Завдання №3–5, required checks, rulesets і бонуси в цьому етапі не виконуються. Цей конвеєр ще не забороняє merge — це налаштовується окремо в завданні №4.
