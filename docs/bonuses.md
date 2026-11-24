# Бонусні завдання лабораторної №4

## Матриця Python та покриття

API CI виконує однакові тести з PostgreSQL і Redis на Python **3.11.9** та **3.12.12**.
`strategy.fail-fast: false` дозволяє кожному варіанту завершитися незалежно від іншого.
Для підтримки Python 3.12 `psycopg2-binary` оновлено з 2.9.7 до 2.9.10.
Залежності, включно з pytest-cov, зафіксовані з хешами в requirements-ci.txt.

Обов’язкові перевірки main після переходу на матрицю:
- `API lint (Ruff)`;
- `API tests (Python 3.11.9)`;
- `API tests (Python 3.12.12)`.

pytest-cov створює `coverage.xml` і каталог `htmlcov/`. Крок upload-artifact має
`if: always()` і виконується безпосередньо після тестів, до негативної перевірки
відключеної бази. Для кожної версії Python є окремий артефакт
`api-coverage-python-<version>`, доступний 14 днів. Якщо тести взагалі не почалися
через помилку інсталяції, звіт покриття ще не існує: upload повідомить про це.
Порогу покриття завдання не вимагає; наявні тести не покривають усі маршрути API.

Доказ збереження при падінні: [прогін 43756512715](https://github.com/KushOleks/withlist-api/actions/runs/43756512715).
Тимчасовий тест з AssertionError дав `1 failed, 3 passed` на обох версіях;
обидва jobs завершилися, і обидва артефакти покриття збережено.
Демонстраційний тест видалений у наступному коміті цього самого [PR №4](https://github.com/KushOleks/withlist-api/pull/4).

Завантажити звіт: Actions → API CI → потрібний прогін → Artifacts →
api-coverage-python-3.11.9 або api-coverage-python-3.12.12. Розпакувати ZIP і
відкрити `index.html` у каталозі HTML-звіту. XML підходить для машинної обробки.

## Незалежний нічний аудит

[PR №5 від Porchuk](https://github.com/KushOleks/withlist-api/pull/5) додає
`.github/workflows/dependency-audit.yml`: щодня о **03:17 Europe/Kyiv** та вручну через
Actions → API dependency audit → Run workflow (main).
`pip-audit==2.9.0` перевіряє requirements-ci.txt, включно з тестовими залежностями.
JSON зберігається в артефакті `api-dependency-audit` на 14 днів навіть при вразливостях.

Аудит не має події pull_request і не входить до required checks. Знайдені
вразливості залишають аудит червоним; помилки не приховуються через continue-on-error.
Виправлення залежностей потребують окремих змін і перевірки сумісності.
[Ручний контрольний запуск](https://github.com/KushOleks/withlist-api/actions/runs/43757037989).

## Захист від затримок розкладу (24 листопада 2026)

GitHub може затримувати schedule на години. Автоматичний аудит виконується лише
між 00:00 та 06:00 за Europe/Kyiv; запізнілий запуск пропускає аудит і пояснює
це в Summary. Пропуск не означає відсутності вразливостей. Ручний Run workflow
працює будь-коли. Це не гарантує щоденного виконання або часу доставки листа.
