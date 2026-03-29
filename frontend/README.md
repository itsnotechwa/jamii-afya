# Jamii Afya Frontend

React + Vite web client for Jamii Afya.

This frontend provides the user-facing experience for:
- Authentication (login flow)
- Emergency/claims browsing and detail views
- New request submission
- Contribution and donation interactions
- Admin review workflows

It communicates with the backend API using Axios.

---

## Prerequisites

- Node.js 18+ (recommended: latest LTS)
- npm 9+
- Running Jamii Afya backend API (see `../backend/README.md`)

---

## Environment Variables

Create a `.env` file in `frontend/` (or copy from `.env.example`):

```bash
cp .env.example .env
```

Required variables:

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Base URL of backend API | `http://localhost:8000` |
| `VITE_MOCK` *(optional)* | Enables demo banner in UI when `true` | `false` |

Example `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_MOCK=false
```

---

## Install and Run

From the `frontend/` directory:

```bash
npm install
npm run dev
```

Vite dev server will start at:
- `http://localhost:5173` (default)

---

## Available Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Start local development server |
| `npm run build` | Build production assets |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint checks |

---

## Project Structure

```text
frontend/
├── src/
│   ├── api/            # Axios client + endpoint modules
│   ├── components/     # Reusable UI components
│   ├── context/        # Global state/context providers
│   ├── hooks/          # Domain hooks for auth/data flows
│   ├── pages/          # Route-level pages
│   ├── routes.jsx      # App routing and guards
│   ├── App.css         # Main app styles
│   └── main.jsx        # Entry point
├── .env.example
├── package.json
└── README.md
```

---

## Backend Connectivity Notes

- Axios base URL is configured in `src/api/axios.js`:
  - `import.meta.env.VITE_API_URL || "http://localhost:8000"`
- Ensure backend CORS allows your frontend origin (for local dev typically `http://localhost:5173`).
- Authentication token is attached via Axios request interceptor.

---

## Common Troubleshooting

### 1) `vite is not recognized`
Run dependency install first:

```bash
npm install
npm run dev
```

### 2) API requests fail with CORS
- Confirm backend is running
- Confirm `VITE_API_URL` points to the backend
- Add frontend origin to backend CORS settings

### 3) Blank or unexpectedly styled page
- Confirm `src/main.jsx` imports `App.css`
- Hard refresh browser after style/cache changes

### 4) Login redirects unexpectedly to `/login`
- Token may be expired or invalid
- Clear local storage and sign in again

---

## Build for Production

```bash
npm run build
```

Output is generated in:
- `frontend/dist/`

You can test the build locally with:

```bash
npm run preview
```

---

