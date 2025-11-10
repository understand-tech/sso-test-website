# Widget SSO Demo

This repository is a reference implementation of a **parent website** that embeds the Understand Tech widget with **single sign-on (SSO)** via Microsoft Azure Active Directory. Use it as a starting point for your own integration or as living documentation for how the OTT-based widget handshake works end-to-end.

## Highlights

- **Production-like flow**: FastAPI backend issues JWT cookies, brokers widget One-Time Tokens (OTTs), and keeps the Widget API key server-side.
- **Modern frontend**: React + Vite sample app that drives the OAuth login and coordinates the OTT exchange with the embedded widget.
- **Complete playbook**: Step-by-step setup, quickstart, and integration-test guides so you can go from zero to a working SSO demo quickly.

## How the SSO Flow Works

1. User clicks **Sign in with Microsoft** on the parent site.
2. Backend exchanges the auth code for tokens and stores user details in an `auth_token` HTTP-only cookie (JWT).
3. Frontend requests an OTT from `/widget/get-ott` once the user is authenticated.
4. Backend calls the Understand Tech API with your `WIDGET_API_KEY` to mint a signed, origin-bound OTT.
5. Frontend posts the OTT into the widget iframe; the widget exchanges it for its own secure session cookie.
6. Widget is now fully authenticated and ready for chat or other assistant experiences.

For a deeper dive into the architecture and sequence diagrams, see the guides listed below.

## Documentation Map

- `SETUP.md` – Install, configure Azure AD, and run both services locally.
- `QUICKSTART.md` – TL;DR for getting Microsoft SSO + widget OTT exchange working.
- `WIDGET_INTEGRATION_TEST.md` – Manual test script and troubleshooting checklist.
- `backend/README.md` – Backend-only instructions, environment variables, and API reference.

## Getting Started

Follow the [setup guide](SETUP.md) to register your Azure app, configure environment variables, and run the dev servers. When both services are up you can sign in with Microsoft, watch the OTT handoff in your logs, and verify that the widget comes up authenticated.

## Repository Layout

```
widget-sso/
├── backend/                 # FastAPI service that handles OAuth & widget OTT
├── frontend/                # React/Vite SPA hosting the widget container
├── README.md                # Overview (this file)
├── QUICKSTART.md            # High-level bring-up steps
├── SETUP.md                 # Detailed Azure + local environment setup
└── WIDGET_INTEGRATION_TEST.md # Manual QA guide for the OTT flow
```

Happy shipping! If anything in the docs is unclear, open an issue or drop a note to the Understand Tech team. 
