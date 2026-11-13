# FleetKit по-русски

Control plane для своего парка автоматизаций: Telegram-боты, парсеры, cron, входящие webhook.

## Зачем

Когда ботов и скриптов больше трёх, начинается хаос: кто жив, что упало, куда слать задачу. FleetKit держит это в одном месте.

## С чего начать

1. `docker compose up --build`
2. Открыть UI на `:8080`, войти bootstrap-админом
3. Создать app
4. Выпустить API-ключ
5. Запустить `examples/http-worker` с env-переменными
6. Из UI поставить job `ping`

## Типичные сценарии

- Парсер: app `parser`, schedule `*/10 * * * *`, worker забирает `schedule:...`
- Telegram: example bot кидает `ping` job из чата
- Внешний SaaS: webhook endpoint → job → твой worker

## Production

```bash
cp .env.production.example .env
# секреты ≥32 символов, свой Postgres password
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Образы после релиза: `ghcr.io/blessed-bless/fleetkit-api` и `fleetkit-web`. Как релизить: [release.md](../release.md).

## Безопасность

- Не коммить `.env` и сырые API-ключи
- Смени `FLEETKIT_SECRET_KEY` и bootstrap-пароль перед публичным деплоем
- В `FLEETKIT_ENV=production` дефолтный секрет / demo-пароль / SQLite — отказ старта
- Webhook без верной `X-FleetKit-Signature` получит 401
