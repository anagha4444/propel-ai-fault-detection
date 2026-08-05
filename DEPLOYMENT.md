# Deployment

## Local

```bash
cp .env.example .env
docker compose up --build
```

## Production notes

- Keep `DATABASE_URL` and `REDIS_URL` in a secure secret store.
- Use a managed Postgres instance instead of the local containerized database.
- Run the frontend behind a reverse proxy and serve the built static assets.
