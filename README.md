# gemini-web2api — Vercel

This repository contains the Vercel deployment wrapper for the upstream `Sophomoresty/gemini-web2api` project.

## Deploy to any Vercel account

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/abinsaji2008/gemini-web2api)

Open the button while signed in to the **Vercel account that should own the deployment**. The repository is public, so Vercel can import it directly.

### Required environment variables

Set these in the Vercel project when needed:

- `GEMINI_COOKIE` — Gemini browser cookie string.
- `GEMINI_API_KEYS` — optional comma-separated API keys for protecting the OpenAI-compatible endpoint.
- `GEMINI_AUTH_USER` — optional Google account index such as `0` or `1`.
- `GEMINI_XSRF_TOKEN` — optional Gemini XSRF token.
- `GEMINI_TIMEOUT_SEC` — optional request timeout in seconds.

The upstream runtime is pinned in `api/index.py`, so Vercel does not have to build the upstream Git repository as a Python package.

## Endpoints

After deployment:

- `GET /` — health/version response
- `GET /v1/models` — OpenAI-compatible model list
- `POST /v1/chat/completions` — OpenAI-compatible chat API
- `POST /v1/responses` — Responses API
- `GET /v1beta/models` — Gemini-compatible model list
- `POST /v1beta/models/<model>:generateContent` — Gemini-compatible generation

Use the deployed Vercel URL as the base URL.
