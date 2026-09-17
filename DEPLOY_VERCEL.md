# Vercel deployment

This repository contains a Vercel-compatible Python entrypoint at `api/index.py` and a Vercel configuration at `vercel.json`.

## Important: deploy the latest `main` commit

The Vercel Python runtime requires either a top-level `handler` class inheriting from `BaseHTTPRequestHandler` or a top-level WSGI/ASGI `app`. This repository's `api/index.py` exposes the required `handler` class.

If your Vercel build log says:

```text
Could not find a top-level "app", "application", or "handler" in "api/index.py".
```

check the **commit SHA** shown near the start of the Vercel build log. The `723deac` commit is an older version that does not contain the fixed entrypoint. Deploy the current `main` commit instead.

Also, if Vercel still prints:

```text
WARNING! Due to `builds` existing in your configuration file...
```

then the deployment is using the old `vercel.json`. The current file uses the `functions` and `rewrites` configuration and does not contain a `builds` block.

## Deploy later

1. Import `https://github.com/abinsaji2008/gemini-web2api` into your Vercel account.
2. Select the `main` branch.
3. Make sure the deployment is based on the latest commit on `main`, not an older deployment or an old commit such as `723deac`.
4. Vercel should detect `api/index.py` as the Python function entrypoint.
5. Add `GEMINI_API_KEYS` as a Vercel Environment Variable if you want API authentication. Separate multiple keys with commas.
6. Optional variables:
   - `GEMINI_AUTH_USER`
   - `GEMINI_XSRF_TOKEN`
   - `GEMINI_TIMEOUT_SEC`
   - `HTTPS_PROXY`
7. Do not commit Gemini session cookies or private API keys to GitHub.

## Important note about `GEMINI_COOKIE_FILE`

Vercel functions use an ephemeral filesystem. A local `cookie.txt` file should not be assumed to exist in production. For authenticated Gemini routing, provide the cookie in a secure environment-specific mechanism and adapt the runtime configuration accordingly rather than committing a cookie file.

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

## Troubleshooting

### Vercel says `handler` is missing

Verify that the build log is using the latest `main` commit and that `api/index.py` contains a top-level class named `handler`.

### Vercel still warns about `builds`

Verify that the deployed `vercel.json` is the current version and does not contain a top-level `builds` array. If you are redeploying an older deployment, create a new deployment from the latest Git commit instead.
