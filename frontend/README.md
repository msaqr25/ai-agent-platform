# AI Agent Platform — Frontend

A dark-themed single-page application for interacting with AI agents. Built with React 19, TypeScript 6, Vite 8, and Tailwind CSS v4. Communicates with the backend API for agent management, chat sessions, text messaging, and voice input/output.

## Features

- **Agent management**: Create, edit, and delete AI agents through the sidebar.
- **Chat sessions**: Per-agent conversation sessions with auto-titling.
- **Text messaging**: Send and receive messages with an AI agent.
- **Voice messaging**: Record audio via the browser `MediaRecorder` API, send it for STT transcription + AI completion + TTS synthesis, and auto-play the spoken response.
- **Audio playback**: Inline audio player for assistant TTS responses with play/pause controls.
- **Dark theme**: Custom dark design system via Tailwind CSS v4 `@theme`.
- **Responsive layout**: Collapsible sidebar, session selector bar, and message area.

## Tech Stack

| Category     | Technology                                                    |
| ------------ | ------------------------------------------------------------- |
| Framework    | React 19                                                      |
| Language     | TypeScript ~6.0                                               |
| Bundler      | Vite 8                                                        |
| Styling      | Tailwind CSS v4                                               |
| Linting      | Oxlint                                                        |
| API Client   | Native `fetch`                                                |
| Audio        | `MediaRecorder` API (recording), `Audio` element (playback)   |
| Container    | Docker (multi-stage: `node:22-alpine` + `nginx:alpine`)       |

## Prerequisites

- **Node.js** 22 or later
- **npm** 10 or later

## Getting Started

### 1. Install dependencies

```sh
npm ci
```

### 2. Start the development server

```sh
npm run dev
```

The app starts at **http://localhost:5173** with hot module replacement. It proxies `/api/v1`, `/health`, and `/audio` requests to the backend at `http://localhost:8000`.

> To use a different backend URL, set the `API_PROXY_TARGET` environment variable:
> ```sh
> API_PROXY_TARGET=http://192.168.1.100:8000 npm run dev
> ```

### 3. Build for production

```sh
npm run build
```

Output is written to `dist/`. The build runs `tsc -b` for type checking before `vite build`.

### 4. Preview the production build

```sh
npm run preview
```

### 5. Lint

```sh
npm run lint
```

Uses [Oxlint](https://oxc.rs/docs/guide/usage/linter.html) with React and TypeScript plugins.

## Docker

The frontend is designed to run behind an Nginx reverse proxy inside a Docker container alongside the backend.

```sh
# From the project root:
docker compose up --build -d
```

This serves the production build at **http://localhost:8080**, with Nginx proxying `/api/`, `/health`, and `/audio` to the backend container.

### Manual Docker build

```sh
docker build -t frontend .
docker run -p 8080:80 frontend
```

The Dockerfile uses a multi-stage build:
1. **Builder** (`node:22-alpine`): installs dependencies and runs `npm run build`.
2. **Runtime** (`nginx:alpine`): serves the built assets and proxies API paths to the backend.

## Configuration

### Vite proxy (development)

Defined in `vite.config.ts`. The dev server proxies the following paths to the backend:

| Path              | Proxy Target                   |
| ----------------- | ------------------------------ |
| `/api/v1`         | `http://localhost:8000`        |
| `/health`         | `http://localhost:8000`        |
| `/audio`          | `http://localhost:8000`        |

Override with the `API_PROXY_TARGET` environment variable.

### Nginx proxy (production / Docker)

Defined in `nginx.conf`. The reverse proxy forwards `/api/`, `/health`, and `/audio` to `http://backend:8000` (the backend Docker service name).

## Project Structure

```
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite config (React, Tailwind, proxy)
├── tsconfig.json               # TypeScript project references
├── tsconfig.app.json           # TypeScript config (app source)
├── tsconfig.node.json          # TypeScript config (Node tools)
├── package.json
├── nginx.conf                  # Production Nginx config
├── Dockerfile                  # Multi-stage Docker build
├── .oxlintrc.json              # Oxlint configuration
├── public/
│   ├── favicon.svg
│   └── icons.svg
└── src/
    ├── main.tsx                # React entry point
    ├── App.tsx                 # Root component with AppProvider
    ├── index.css               # Tailwind CSS v4 with custom dark theme
    ├── api/
    │   └── client.ts           # Fetch-based API client
    ├── components/
    │   ├── Layout.tsx          # Main layout (sidebar + session bar + messages)
    │   ├── Sidebar.tsx         # Agent list with create/edit/delete
    │   ├── SessionBar.tsx      # Session selector with create/delete
    │   ├── MessageList.tsx     # Message bubbles with audio playback
    │   ├── MessageInput.tsx    # Text input + voice recording button
    │   ├── Modal.tsx           # Generic modal overlay
    │   └── ConfirmDialog.tsx   # Confirmation dialog
    ├── context/
    │   └── AppContext.tsx       # Global state (useReducer + useContext)
    └── types/
        └── index.ts            # TypeScript interfaces
```

## Architecture

### State management

All application state lives in `AppContext` using a `useReducer` + `useContext` pattern. Actions are dispatched through a discriminated union type. Key state includes:

- `agents`: list of agents
- `sessions`: sessions for the selected agent
- `messages`: messages for the selected session
- `sidebarOpen`: sidebar visibility toggle
- `isLoading` / `error`: global loading and error states

### API client

The client in `src/api/client.ts` wraps `fetch` with typed request/response methods. It automatically sets `Content-Type: application/json` for JSON bodies and uses `FormData` for voice uploads. A custom `ApiError` class provides structured error handling matching the backend's `ErrorResponse` schema.

### Voice pipeline

1. User taps the microphone button in `MessageInput`.
2. Browser `MediaRecorder` captures audio (`audio/webm` or `audio/mp4` as fallback).
3. The blob is uploaded via `FormData` to `POST /api/v1/sessions/{id}/voice/`.
4. The backend transcribes (Whisper STT), completes (GPT), and synthesizes (TTS).
5. The response includes the user message, assistant message, and audio file metadata.
6. `MessageList` auto-plays the audio and shows a play/pause button on assistant messages.

