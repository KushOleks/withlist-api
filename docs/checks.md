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
- test_postgres.py: створює користувача та список у справжній PostgreSQL, очищує ORM identity map, викликає GET /wishlists/{id} і перевіряє отримані id/title. get_db підключено до реальної тестової транзакції; SQL не підмінено. Після тесту транзакція відкочується. Тест вимагає явний DATABASE_URL із назвою бази, що закінчується на _test, і не використовує робочу базу з .env.

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
export DATABASE_URL='postgresql://wishlist_ci:ci-only-password@localhost:15433/wishlist_test'
python -m pytest -v
```

На Mac локально підтверджено Ruff та обидва health-сценарії, а також очікуваний провал PostgreSQL-тесту на недоступному порту. Позитивний інтеграційний тест і готовність обох job services підтверджено успішним [запуском GitHub Actions](https://github.com/KushOleks/withlist-api/actions/runs/42894806678) у [PR №1](https://github.com/KushOleks/withlist-api/pull/1): Ruff пройшов, усі 3 pytest-сценарії пройшли, негативна перевірка PostgreSQL пройшла як очікуваний провал тесту. Попередній API PR №1 уже злитий у main.

Цей розділ описує первинний конвеєр API. Поточні rulesets і докази завдань №4–5 наведено нижче. Бонуси не виконувалися.

## Завдання №4 — обов’язкові перевірки main

Активний ruleset вимагає Pull Request, одне схвалення з Write-доступом, успішні перевірки GitHub Actions і актуальність гілки щодо main. Нові коміти скидають застарілі схвалення. Force-push і видалення main заборонені. Список bypass порожній: власник також має дотримуватися правил.

Обов’язкові статуси: `API lint (Ruff)`, `API tests (PostgreSQL + Redis)`.

[Демонстраційний PR №3](https://github.com/KushOleks/withlist-api/pull/3) спочатку містив безпечну помилку лінту в окремому файлі. Помилковий файл видалено в цьому самому PR; робочий код застосунку не змінюється.

### 1. Червона обов’язкова перевірка й блокування злиття

![Required CI failing і неактивна кнопка merge](assets/01-blocked.png)

На скриншоті видно failing check із позначкою Required та Merging is blocked. На цьому етапі також відсутнє обов’язкове схвалення; після виправлення виконуються обидві умови.

### 2. Конкретна помилка в журналі CI

![Рядок помилки лінтера](assets/02-error.png)

[Ruff F401: `os` imported but unused у ci_demo.py:1:8](https://github.com/KushOleks/withlist-api/actions/runs/43745707362). Наступні job пропущені через залежність від lint.

### 3. Той самий PR після виправлення

![Успішні required checks і доступне злиття](assets/03-passed.png)

[Виправлений прогін](https://github.com/KushOleks/withlist-api/actions/runs/43745991071) успішний. Скриншот показує той самий PR після виправлення, схвалення з акаунта Porchuk, зелені required checks і активну кнопку Merge pull request. Зображення збережено до злиття; після додавання файлів доказів CI й review повторюються.

## Завдання №5 — фактичний ефект кешу

| Прогін | Час | GitHub Actions |
|---|---:|---|
| Без кешу на початку першого прогону | 110 с | [прогін 42894806678](https://github.com/KushOleks/withlist-api/actions/runs/42894806678) |
| З кешем, наступний прогін | 81 с | [прогін 42900543620](https://github.com/KushOleks/withlist-api/actions/runs/42900543620) |

У першому прогоні найдовше тривало Install locked dependencies — 46 с; у теплому — setup-python у lint — 18 с.

Різниця — 29 с (26.4%). Час отримано з GitHub API run_duration_ms; тривалості кроків — із started_at/completed_at jobs. Обидва прогони мають однаковий lockfile і ключ кешу. У першому lint мав cache miss та зберіг кеш; наступні job цього ж прогону вже могли його використовувати. У наступному прогоні всі job відновили той самий кеш. Тому це порівняння холодного старту workflow з теплим, а не повністю вимкненого кешування в усіх job. Час також залежить від підготовки runner і сервісів.
