# File2QR

File2QR is a production-ready SaaS application for secure file sharing via QR codes.

## Architecture

This is a monorepo containing:
- `frontend/`: Next.js 14+ (App Router) application with Tailwind CSS and shadcn/ui.
- `backend/`: Django REST Framework API.

## Requirements

- Node.js (18+)
- Python (3.11+)
- Docker & Docker Compose (for PostgreSQL and Redis)

## Local Development Setup

1. Start the database services:
   ```bash
   docker-compose up -d
   ```

2. Setup Backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Update .env with your local settings
   python manage.py migrate
   python manage.py runserver
   ```

3. Setup Frontend:
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Update .env.local with your local settings
   npm run dev
   ```

## Development Workflow

- The frontend is available at `http://localhost:3000`
- The backend API is available at `http://localhost:8000`

See individual READMEs in `frontend/` and `backend/` for more specific details.
