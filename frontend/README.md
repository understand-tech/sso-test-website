# Frontend

React + Vite frontend for Widget SSO parent website.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Server runs at `http://localhost:5173`

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Features

- Microsoft SSO authentication
- Protected routes
- Placeholder for widget iframe integration
- Responsive design

## Configuration

The backend API URL is hardcoded to `http://localhost:8000`. For production, update the `API_BASE_URL` constant in:
- `src/App.jsx`
- `src/pages/Login.jsx`

Consider using environment variables for different environments.

