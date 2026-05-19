# Frontend Progress

Updated: 2026-05-18 20:35 Asia/Shanghai

## Scope

- Build Vue 3 frontend under `frontend/`.
- Split into `apps/admin` management console and `apps/web` public site.
- Keep API contracts aligned with `docs/api.md`.

## Status

- [x] Requirements and API docs reviewed.
- [x] Workspace structure selected.
- [x] Base project files created.
- [x] Shared API/SSE utilities implemented.
- [x] Admin MVP implemented.
- [x] Public site MVP implemented.
- [x] Local validation completed.

## Implemented

- Admin app: login, RBAC route guard, permission-filtered sidebar, dashboard, content production, LLM center, review workspace, assets/publish, reports/tasks, system settings.
- Public app: home, columns, article detail, video detail, downloads/lead form, tool recommendations.
- Admin app owns its API client, token handling, OpenAI-compatible SSE parser, permission helpers, status dictionary, and admin mock fallback data.
- Public web app owns its API client and public mock fallback data.
- There is no shared frontend package between admin and public web.

## Notes

- `pnpm` is not installed in this environment, so npm workspaces are used.
- Backend is currently empty, so API modules include mock fallback data for frontend verification.
- Per frontend quality-gate instructions, production build is not run unless explicitly requested.

## Validation

- `npm run lint`: passed.
- `npm run stylelint`: passed.
- Admin dev server: `http://127.0.0.1:5173` returned 200.
- Public web dev server: `http://127.0.0.1:5174` returned 200.
- Vite module smoke test: passed for app `.vue` and `.js` modules.
