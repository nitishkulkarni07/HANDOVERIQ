# Deploy HandoverIQ using Supabase PostgreSQL

Project: https://supabase.com/dashboard/project/rhgqgusbpjgqnsgvpfuq

The private `handoveriq` schema and its five tables have been created in Supabase.
The backend now uses PostgreSQL when `DATABASE_URL` is present; without it, local SQLite is used (temporary on Vercel).

1. In the Supabase project dashboard click **Connect**, then select **Transaction pooler** (port 6543). Copy the **URI** connection string. Replace `[YOUR-PASSWORD]` with your database password, URL-encoding reserved characters if required.
2. In Vercel, open project **handoveriq** > **Settings** > **Environment Variables**. Add **DATABASE_URL** as a **Sensitive** variable for Production (and Preview if needed). Paste the URI directly into Vercel; never share or commit this value.
3. Redeploy from the latest GitHub commit (a new deployment is required to pick up environment variables).
4. Log in as lead, upload a fresh document, click **Open source lines**, then refresh and repeat. Test the AI Assistant as well.

Only documents added after the persistent database is enabled are retained; data on temporary Vercel SQLite may no longer be recoverable. All application tables live in the unexposed `handoveriq` schema; do not add Data API grants to `anon` or `authenticated`.

Configure `AUTH_SECRET`, `DEMO_PASSWORD`, `GEMINI_API_KEY` as server-only variables, with no keys in the public repository.
