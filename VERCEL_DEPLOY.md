# Vercel deployment notes

The current demonstration backend relies on SQLite and must not be used for durable organizational documents on Vercel. `/tmp` is ephemeral and database changes may vanish on cold starts or scale-out. Configure `DEMO_PASSWORD` and `GEMINI_API_KEY` as encrypted environment variables before deployment. The repository should contain application code, not local data or secrets. Use a persistent PostgreSQL database and an object store before moving beyond synthetic demonstrations.
