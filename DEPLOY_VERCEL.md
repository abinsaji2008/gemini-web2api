# Vercel deployment

This repository contains a Vercel-compatible Python entrypoint at `api/index.py` and a Vercel configuration at `vercel.json`.

## What the Vercel adapter does

- Exposes the upstream `GeminiHandler` through a top-level `handler` class required by Vercel's Python runtime.
- Installs the upstream `gemini-web2api` package at a reviewed commit through `requirements.txt`.
- Keeps the original OpenAI-compatible and Gemini-native routes.
- Supports streaming through the Python runtime.
- Reads API keys and optional Gemini authentication values from Environment Variables.

## Important: deploy the latest `main` commit

The Vercel Python runtime requires either a top-level `handler` class inheriting from `BaseHTTPRequestHandler` or a top-level WSGI/ASGI `app`.

The deployment error:

```text
Could not find a top-level "app", "application", or "handler" in "api/index.py".
```

means Vercel built an older version of this repository. The current `api/index.py` contains the required top-level `handler` class.

If your Vercel log still says the build contains the old `builds` configuration, it is also using an older `vercel.json`. The current file uses `functions` and `rewrites` and has no `builds` block.

## Deploy

1. Import `https://github.com/abinsaji2008/gemini-web2api` into your Vercel account.
2. Select the `main` branch.
3. Make sure the deployment uses the latest commit on `main`. Do not use the old `723deac` deployment.
4. Vercel should detect `api/index.py` as a Python Function.
5. Add the Environment Variables below.
6. Deploy.

## Environment Variables

### API authentication

```text
GEMINI_API_KEYS=sk-your-secret-key
```

Use one key or comma-separated keys.

### Optional Gemini Web authentication

```text
GEMINI_COOKIE=SID=...; HSID=...; SSID=...; APISID=...; SAPISID=...; __Secure-1PSID=...
GEMINI_AUTH_USER=0
GEMINI_XSRF_TOKEN=...
```

`GEMINI_COOKIE` is preferred for Vercel because the function adapter writes it to the ephemeral `/tmp` filesystem at runtime rather than requiring a committed cookie file.

### Other optional settings

```text
GEMINI_TIMEOUT_SEC=180
HTTPS_PROXY=http://your-proxy:port
```

Do not put API keys or Gemini cookies in GitHub source files.

## API endpoints

OpenAI-compatible:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/responses`

Gemini-native:

- `GET /v1beta/models`
- `POST /v1beta/models/{model}:generateContent`
- `POST /v1beta/models/{model}:streamGenerateContent`

## Troubleshooting

### `handler` is missing

Check the commit SHA near the start of the Vercel build log. An older commit such as `723deac` predates the fixed `handler` entrypoint. Create a new deployment from the latest `main` commit.

### `builds` warning still appears

Make sure the deployment uses the current `vercel.json`. The current file contains `functions` and `rewrites`, not a top-level `builds` array.

### `ModuleNotFoundError: gemini_web2api`

The current `requirements.txt` installs the upstream package directly from the reviewed Git commit. Make sure the deployment is using the current `requirements.txt` from `main`, then redeploy.

### Long requests or streaming stop early

Vercel Function duration is plan-dependent. The configuration sets a 300-second maximum by default. Pro and Enterprise plans can support longer durations when configured and using the supported compute mode.
