# GnuCash SaaS — Multi-Tenant Cloud Accounting Platform

A cloud-based accounting platform that gives each user their own GnuCash desktop instance, accessible through a web browser. Built with a multi-tenant architecture where per-user Docker containers run GnuCash via xpra HTML5, managed by a FastAPI backend with a React frontend.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (443)
                           ▼
                ┌─────────────────────┐
                │   Traefik Proxy     │
                │  (Let's Encrypt)    │
                │  HTTP→HTTPS redirect│
                └────┬──────────┬─────┘
                     │          │
          /api/*     │          │  /*
                     ▼          ▼
          ┌──────────────┐  ┌──────────────┐
          │   FastAPI    │  │   React App  │
          │   Backend    │  │   (Nginx)    │
          │   :8000      │  │   :80        │
          └──────┬───────┘  └──────────────┘
                 │
        ┌────────┼────────────┐
        │        │            │
        ▼        ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ GnuCash  │ │ GnuCash  │ │ GnuCash  │
  │ User A   │ │ User B   │ │ User C   │
  │ (xpra)   │ │ (xpra)   │ │ (xpra)   │
  │ :14500   │ │ :14500   │ │ :14500   │
  └──────────┘ └──────────┘ └──────────┘
        │        │            │
        └────────┼────────────┘
                 ▼
        ┌──────────────────┐
        │   Azure MySQL    │
        │ (Managed Service)│
        └──────────────────┘
```

**Technology Stack:**

| Component       | Technology                       |
|-----------------|----------------------------------|
| Reverse Proxy   | Traefik v3.1 + Let's Encrypt     |
| Backend API     | Python 3.12, FastAPI, Uvicorn    |
| Frontend        | React 18, TypeScript, Vite       |
| Database        | Azure MySQL (managed)            |
| Desktop Streaming | xpra HTML5 (port 14500)        |
| Containerization | Docker, Docker Compose          |
| Host OS         | Ubuntu 24.04 LTS                 |

---

## Prerequisites

- **Ubuntu 24.04 LTS** server (or compatible Linux)
- **Docker** ≥ 24.0 and **Docker Compose** ≥ 2.20
- **Azure MySQL** flexible server (provisioned and accessible)
- **Domain name** with DNS A record pointing to your server's public IP
- Ports **80** and **443** open in your firewall / Azure NSG

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/gnucash-saas.git
cd gnucash-saas
```

### 2. Create the Docker network

```bash
docker network create gnucash-net
```

### 3. Build the GnuCash container image

```bash
cd gnucash-container
docker build -t gnucash-xpra .
cd ..
```

### 4. Configure environment variables

```bash
cp .env.example .env
nano .env   # Fill in your values
```

### 5. Create the user data directory

```bash
sudo mkdir -p /opt/gnucash-data
sudo chown $USER:$USER /opt/gnucash-data
```

### 6. Start all services

```bash
docker-compose up -d --build
```

### 7. Access the platform

Open `https://your-domain.com` in your browser.

- **Dashboard (Traefik):** `http://your-server:8080`
- **API docs:** `https://your-domain.com/api/docs`

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | MySQL connection string (`mysql+pymysql://...`) | — | ✅ |
| `SECRET_KEY` | JWT signing secret (use `secrets.token_hex(32)`) | — | ✅ |
| `JWT_EXPIRATION_MINUTES` | JWT token lifetime in minutes | `60` | ❌ |
| `CORS_ORIGINS` | Comma-separated allowed origins | — | ✅ |
| `USER_DATA_PATH` | Host path for user GnuCash files | `/opt/gnucash-data` | ❌ |
| `RATE_LIMIT_LOGIN` | Login endpoint rate limit | `5/minute` | ❌ |
| `RATE_LIMIT_REGISTER` | Registration endpoint rate limit | `3/minute` | ❌ |
| `IDLE_TIMEOUT_MINUTES` | Auto-stop idle containers after N minutes | `60` | ❌ |
| `ACME_EMAIL` | Email for Let's Encrypt notifications | — | ✅ |
| `VITE_API_URL` | Frontend API base URL (build-time) | — | ✅ |

---

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | No | Register a new user |
| `POST` | `/api/auth/login` | No | Login and receive JWT token |
| `GET` | `/api/auth/me` | Yes | Get current user profile |
| `POST` | `/api/sessions` | Yes | Create a GnuCash session (provisions container) |
| `GET` | `/api/sessions` | Yes | List user's active sessions |
| `DELETE` | `/api/sessions/{id}` | Yes | Stop and remove a session |
| `POST` | `/api/files/upload` | Yes | Upload a GnuCash file |
| `GET` | `/api/files/download/{filename}` | Yes | Download a GnuCash file |
| `GET` | `/api/files` | Yes | List user's GnuCash files |
| `GET` | `/api/docs` | No | Interactive API documentation (Swagger UI) |

---

## Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # Starts Vite dev server on http://localhost:5173
```

The Vite dev server is pre-configured to proxy `/api` requests to `http://localhost:8000`.

---

## Project Structure

```
gnucash-saas/
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
│
├── traefik/
│   ├── traefik.yml             # Traefik config (HTTPS + Let's Encrypt)
│   └── acme.json               # Let's Encrypt certificates (auto-generated)
│
├── backend/
│   ├── Dockerfile              # Python 3.12-slim container
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application entry point
│   ├── auth.py                 # JWT authentication logic
│   ├── database.py             # SQLAlchemy database connection
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── docker_manager.py       # GnuCash container lifecycle management
│   ├── file_manager.py         # File upload/download endpoints
│   └── scheduler.py            # APScheduler idle session cleanup
│
├── frontend/
│   ├── Dockerfile              # Multi-stage Node 20 + Nginx
│   ├── nginx.conf              # Nginx SPA + API proxy config
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.ts          # Vite build configuration
│   ├── tsconfig.json           # TypeScript configuration
│   └── src/                    # React application source
│       ├── App.tsx
│       ├── main.tsx
│       └── ...
│
└── gnucash-container/
    └── Dockerfile              # GnuCash + xpra container image
```

---

## Security

- **HTTPS everywhere** — Traefik auto-provisions TLS certificates via Let's Encrypt
- **HTTP → HTTPS redirect** — All HTTP traffic is redirected to HTTPS
- **JWT authentication** — Stateless token-based auth with configurable expiration
- **Password hashing** — bcrypt with automatic salt generation
- **Rate limiting** — Configurable per-endpoint limits (login, registration)
- **CORS** — Strict origin allowlist via environment configuration
- **Docker socket protection** — Backend has controlled access; containers are isolated
- **Per-user isolation** — Each user gets a dedicated GnuCash container
- **Idle cleanup** — Automatic container shutdown after configurable idle timeout
- **No exposed ports** — Backend and frontend are only accessible through Traefik

---

## Troubleshooting

### Let's Encrypt certificate not issuing

1. Ensure ports 80 and 443 are open in your firewall
2. Ensure your domain's DNS A record points to the server
3. Check Traefik logs: `docker-compose logs traefik`

### Database connection errors

1. Verify `DATABASE_URL` in `.env`
2. Ensure Azure MySQL firewall allows your server's IP
3. Test connectivity: `mysql -h your-server.mysql.database.azure.com -u gnucash_admin -p`

### Container not starting

1. Check logs: `docker-compose logs <service>`
2. Ensure `gnucash-net` network exists: `docker network ls`
3. Ensure the `gnucash-xpra` image is built: `docker images | grep gnucash-xpra`

---

## License

MIT License — see [LICENSE](LICENSE) for details.
