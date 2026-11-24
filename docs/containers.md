# Лабораторна №5 — контейнери API та спільний стек

## Запуск із чистого клону

Потрібні Git і Docker Desktop з Compose 2.24.4 або новішим. На Linux потрібний Docker Engine з Compose plugin.

```bash
mkdir -p ~/DevOps/lab-05
cd ~/DevOps/lab-05
git clone https://github.com/KushOleks/withlist-api.git
git clone https://github.com/KushOleks/wishlist-ui.git
cd withlist-api
cp .env.example .env
```

У `.env` заповніть `POSTGRES_PASSWORD` і `SECRET_KEY` різними випадковими значеннями.
Для кожного можна використати `openssl rand -hex 32`. Секрети не комітяться й не передаються в build args.
`API_PORT=8000`, `UI_PORT=8080`, `VITE_API_BASE=http://localhost:8000` підходять для запуску на цій машині.
Якщо змінюєте UI_PORT, змініть також ALLOWED_ORIGINS. Якщо змінюєте API_PORT, змініть VITE_API_BASE й перебудуйте UI.

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
curl --fail http://localhost:8000/health
```

UI: http://localhost:8080; API Swagger: http://localhost:8000/docs.
Створіть користувача й список у UI. API і UI мають опубліковані порти лише на loopback.
PostgreSQL та Redis не мають host ports. Кожен сервіс має healthcheck та restart: unless-stopped.
API залежить від здорових PostgreSQL і Redis, UI — від здорового API.
Compose відхиляє відсутній/порожній POSTGRES_PASSWORD або SECRET_KEY через `${VAR:?message}`.

На Mac із попередньою лабораторною поточні приватні значення збережені окремо в `.env.lab05`:
для цього середовища використовуйте `docker compose --env-file .env.lab05 ...`.
Том старої лабораторної не використовується: новий проект має ім’я lab05-wishlist.

## Образ API

Python 3.12.12-slim-bookworm, залежності встановлюються до копіювання коду з --no-cache-dir і --require-hashes за requirements-runtime.txt.
Процес працює від appuser (UID 10001), слухає 0.0.0.0:8000, CMD має exec-форму.
Копіюються лише потрібні Python-модулі. .dockerignore виключає env-файли, Git, тести й кеші.
Конфігурація БД, JWT, Redis і CORS надходить тільки зі змінних середовища.

## Перевірки та докази

Фактичні результати збірок, кешу, stop, збереження/видалення тестового тому,
діагностики та multi-arch manifest буде додано після виконання перевірок.
Наведені нижче команди — інструкція, а не заява про завершений результат.

```bash
docker run --rm wishlist-api:lab05-local whoami
docker run --rm wishlist-api:lab05-local ls -a
docker build --progress=plain -t wishlist-api:lab05-local .
docker buildx imagetools inspect ghcr.io/kusholeks/wishlist-api:1.0.0
```

Для перевірки тому використовується окремий disposable project `lab05-volume-proof`.
`down` залишає його named volume; `down -v` видаляє саме тестові дані цього project.
Робочий том і старий стек лабораторної №4 не видаляються.

## Режим розробки

```bash
docker compose -f compose.yaml -f compose.dev.yaml --profile dev up --build --watch
```

Після зміни вимог оновіть lock: `uv pip compile requirements.txt --python-version 3.12 --universal --generate-hashes -o requirements-runtime.txt`.

API використовує develop.watch: sync+restart для коду й rebuild для requirements.txt.
Dockerignore не дає синхронізувати .env та Git. UI монтує вихідний каталог у /app,
але /app/node_modules перекритий окремим named volume: host-залежності не замінюють Linux-залежності.
При старті dev UI виконується npm ci, тому вміст тому відповідає lock-файлу.
Зміни Vue-компонентів підхоплює Vite без docker compose build.

## CI, GHCR та сканування

Job API image (Docker) залежить від тестів. На PR збірка перевіряється без push у GHCR;
на main публікуються main і sha-<повний SHA>; на v* — version, major.minor, major та latest.
Для main/release публікуються linux/amd64 і linux/arm64 під одним тегом.
Вхід у GHCR — GITHUB_TOKEN, permissions задаються явно, PAT не використовується.
Окремий advisory job Trivy не входить до required checks; JSON-звіт зберігається артефактом.
У Summary цього job автоматично порівнюються OS-пакети та бібліотеки застосунку.
