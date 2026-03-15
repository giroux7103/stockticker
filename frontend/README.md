# Stock Ticker Frontend

React + Vite UI for the Stock Ticker backend.

## Run

```bash
copy .env.example .env
npm install
npm run dev
```

## Environment

- `VITE_API_BASE` backend base URL (optional). If not set, frontend uses the current browser origin.
- `VITE_DEV_HTTPS` set to `true` to run Vite dev server over HTTPS.
- `VITE_DEV_SSL_CERT_FILE` path to TLS cert file (required when `VITE_DEV_HTTPS=true`).
- `VITE_DEV_SSL_KEY_FILE` path to TLS key file (required when `VITE_DEV_HTTPS=true`).
- `VITE_DEV_PORT` optional dev server port override (default `5173`).
