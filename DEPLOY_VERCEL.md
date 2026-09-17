# Vercel deployment

This repository contains a Vercel-compatible Python entrypoint at `api/index.py` and `vercel.json`.

## Important

These files only configure the repository for Vercel. Nothing is deployed automatically by this change.

## Deploy later

1. Import this GitHub repository into Vercel.
2. Vercel will detect `api/index.py` as the Python function entrypoint.
3. Add `GEMINI_API_KEYS` as a Vercel Environment Variable if you want API authentication. Separate multiple keys with commas.
4. Optional variables:
   - `GEMINI_AUTH_USER`
   - `GEMINI_XSRF_TOKEN`
   - `GEMINI_COOKIE_FILE`
   - `GEMINI_TIMEOUT_SEC`
   - `HTTPS_PROXY`
5. Deploy from Vercel when you are ready.

## Local testing

Install dependencies:

```bash
pip install -r requirements.txt
```

The original local server remains available:

```bash
python gemini_web2api.py
```

## API endpoints

The project supports the upstream OpenAI-compatible endpoints such as:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/responses`

and Gemini-native endpoints under `/v1beta/models`.

Do not commit Gemini session cookies or private API keys to GitHub.
