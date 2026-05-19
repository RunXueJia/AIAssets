# Hours24 Frontend

Vue 3 frontend for the Hours24 AI content asset system.

## Apps

- `apps/admin`: authenticated management console. It owns its API client, API modules, permissions, statuses, SSE parser, and admin mock data.
- `apps/web`: public content and lead-generation site. It owns its public API client and public mock data.

Admin and public web code are intentionally separated. Do not import admin code from `apps/web`, and do not import public-site code from `apps/admin`.

## Commands

Admin:

```bash
cd apps/admin
npm install
npm run dev
npm run lint
npm run stylelint
```

Public web:

```bash
cd apps/web
npm install
npm run dev
npm run lint
npm run stylelint
```

The API base URL defaults to `/api/v1`. Set `VITE_API_BASE_URL` when needed.
