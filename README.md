# BodyLingo onboarding

Responsive React + Vite onboarding experience for BodyLingo. The app contains the intro carousel, welcome, sign up, log in, password reset mock, personal details, and communication preferences screens. Authentication is mock-only; passwords are never saved. Onboarding answers are kept in `sessionStorage` so they survive going back to edit.

## Run locally

```sh
pnpm install
pnpm dev
```

To create a production build, run `pnpm build`.

## Dashboard handoff

The preferences form finishes by navigating to `/dashboard` by default. Set `VITE_DASHBOARD_ROUTE` in a local `.env.local` file to point at the dashboard route integrated by the rest of the team, for example:

```sh
VITE_DASHBOARD_ROUTE=/dashboard
```

## Onboarding files

- `src/App.jsx` — screens, routes, form validation, mock authentication, and onboarding state.
- `src/styles.css` — responsive visual design, illustrations, and component styling.
- `src/main.jsx` — React entry point and router setup.
- `index.html` — app metadata and mount point.
