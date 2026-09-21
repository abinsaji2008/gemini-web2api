# gemini-web2api — Vercel

A Vercel deployment wrapper for the upstream [Sophomoresty/gemini-web2api](https://github.com/Sophomoresty/gemini-web2api).

This project exposes an OpenAI-compatible API through Vercel, so it can be used from Postman, OpenAI-compatible clients, custom apps, and automation workflows.

## Features

- Deploy to Vercel with one click
- OpenAI-compatible `/v1/chat/completions`
- OpenAI-compatible `/v1/responses`
- `/v1/models` model listing
- Gemini-compatible `/v1beta/models`
- Gemini-compatible `generateContent` endpoint
- Optional API-key protection
- Optional Google account selection, XSRF token, proxy, and timeout settings
- Function-calling compatible chat requests (the API can return `tool_calls`; your application is responsible for executing the requested function)

## 1. Deploy to Vercel

### One-click deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/abinsaji2008/gemini-web2api)

1. Open the **Deploy with Vercel** button.
2. Sign in to Vercel.
3. Select the Vercel account/team that should own the project.
4. Create the project.
5. Wait for the deployment to finish.
6. Copy the deployment URL, for example:

```text
https://your-project.vercel.app
```

### Deploy from an existing Vercel project

1. Open your Vercel dashboard.
2. Click **Add New → Project**.
3. Import this GitHub repository:

```text
https://github.com/abinsaji2008/gemini-web2api
```

4. Keep the detected Python configuration.
5. Add the environment variables described below.
6. Click **Deploy**.

## 2. Configure environment variables

Open:

**Vercel → Project → Settings → Environment Variables**

### GEMINI_COOKIE

Required for Gemini web access when the upstream runtime needs your signed-in Gemini session.

Set it to your own Gemini browser cookie string.

Example format:

```text
SID=...; HSID=...; SSID=...; APISID=...; SAPISID=...
```

Do **not** commit cookies to GitHub, put them in `README.md`, or paste them into public issues.

### GEMINI_API_KEYS

Optional. A comma-separated list of API keys accepted by the OpenAI-compatible endpoints.

Example:

```text
my-secret-key
```

Multiple keys:

```text
key-one,key-two,key-three
```

Then send:

```http
Authorization: Bearer my-secret-key
```

### Optional variables

| Variable | Purpose | Example |
|---|---|---|
| `GEMINI_AUTH_USER` | Select a Google account index | `0` |
| `GEMINI_XSRF_TOKEN` | Optional Gemini XSRF token | `...` |
| `HTTPS_PROXY` | HTTPS proxy for outbound requests | `http://user:pass@host:port` |
| `GEMINI_TIMEOUT_SEC` | Request timeout in seconds | `180` |
| `GEMINI_WEB2API_UPSTREAM_REF` | Upstream Git ref used by the wrapper | `main` |

After changing environment variables, create a new deployment or redeploy the project so the new values are applied.

## 3. Check that the deployment works

Open the deployment URL in a browser:

```http
GET https://your-project.vercel.app/
```

Expected response is similar to:

```json
{
  "status": "ok",
  "version": "1.1.0",
  "models": [
    "gemini-3.7-flash",
    "gemini-3.6-flash"
  ]
}
```

Then test:

```http
GET https://your-project.vercel.app/v1/models
```

## 4. Postman — basic chat demo

### Request

**Method**

```text
POST
```

**URL**

```text
https://your-project.vercel.app/v1/chat/completions
```

### Headers

```text
Content-Type: application/json
Authorization: Bearer my-secret-key
```

If `GEMINI_API_KEYS` is not configured, the authorization header may not be required.

### Body → raw → JSON

```json
{
  "model": "gemini-3.7-flash",
  "messages": [
    {
      "role": "user",
      "content": "Hello! What is 2 + 2?"
    }
  ],
  "stream": false
}
```

### Example response

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1789975891,
  "model": "gemini-3.7-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "2 + 2 = 4."
      },
      "finish_reason": "stop"
    }
  ]
}
```

## 5. Postman — function calling demo

The OpenAI-compatible endpoint can accept `tools` definitions. When the model decides that a function is required, the response contains `tool_calls` instead of a normal final message.

### Request

```http
POST https://your-project.vercel.app/v1/chat/completions
```

Headers:

```text
Content-Type: application/json
Authorization: Bearer my-secret-key
```

Body:

```json
{
  "model": "gemini-3.7-flash",
  "messages": [
    {
      "role": "system",
      "content": "You are a patient-focused home assistant. The default light is l1. When the user says 'the light' without a number, use l1. Only use functions for devices that are available. Never invent a device."
    },
    {
      "role": "user",
      "content": "Turn on the light"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "l1",
        "description": "Control the default/main light. Use this function whenever the patient refers to 'the light' without specifying another light.",
        "parameters": {
          "type": "object",
          "properties": {
            "state": {
              "type": "string",
              "enum": [
                "on",
                "off"
              ],
              "description": "Turn the light on or off."
            }
          },
          "required": [
            "state"
          ]
        }
      }
    }
  ],
  "stream": false
}
```

A tool-call response is similar to:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_...",
            "type": "function",
            "function": {
              "name": "l1",
              "arguments": "{\\\"state\\\": \\\"on\\\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

Your application should then:

1. Detect `choices[0].message.tool_calls`.
2. Parse the function name and JSON arguments.
3. Execute the function in your own backend.
4. For a home-automation function such as `l1`, update Firebase.
5. Send the tool result back to the model to obtain the final patient-facing response.

The Vercel API does **not** directly control your ESP32 or Firebase unless you add that integration to your application.

## 6. Example home-assistant logic

For a device list such as:

```text
l1 = Light 1 (default light)
l2 = Light 2
f1 = Fan 1
```

Expected behavior:

```text
"Turn on the light"
→ l1({"state":"on"})

"Turn off the light"
→ l1({"state":"off"})

"Turn on light 2"
→ l2({"state":"on"})

"Turn on light 3"
→ no tool call
→ "I couldn't find light 3."
```

Your backend should enforce the real device list and permissions. Never rely on the model alone to authorize a physical device action.

## 7. Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Health/version response |
| GET | `/v1/models` | OpenAI-compatible model list |
| POST | `/v1/chat/completions` | OpenAI-compatible chat |
| POST | `/v1/responses` | Responses API |
| GET | `/v1beta/models` | Gemini-compatible model list |
| POST | `/v1beta/models/<model>:generateContent` | Gemini-compatible generation |

Use your deployed Vercel URL as the base URL.

## 8. OpenAI-compatible client example

You can use the deployment as the base URL for an OpenAI-compatible client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-project.vercel.app/v1",
    api_key="my-secret-key"
)

response = client.chat.completions.create(
    model="gemini-3.7-flash",
    messages=[
        {"role": "user", "content": "Explain recursion simply."}
    ]
)

print(response.choices[0].message.content)
```

## Security

Treat `GEMINI_COOKIE` like a password. Use Vercel Environment Variables and never commit it to the repository.

If a browser cookie has been exposed publicly, revoke/sign out of the affected Google session and create a fresh session before continuing.

## Notes

- This repository is a Vercel deployment wrapper around the upstream project.
- The wrapper downloads the upstream single-file implementation at runtime.
- Do not assume that a model name exposed by `/v1/models` supports image or video generation; those require separate model/API support.
