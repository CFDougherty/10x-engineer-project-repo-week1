# Running PromptLab Application

## Quick Start with Docker (Recommended)

```bash
docker-compose up --build
```

This will:
- Start the backend API on port 8000
- Start the frontend on port 3000
- Access the application at: http://localhost:3000

## Running Locally Without Docker

### 1. Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start the backend
cd backend
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 2. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start the frontend
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

## Troubleshooting

### If the page doesn't load after the fix:

1. Make sure both backend and frontend are running
2. Check that the backend is accessible at http://localhost:8000/health
3. Clear your browser cache and refresh
4. Check the browser console for any errors

### Common Issues:

- **ThemeProvider Error**: Fixed by adding ThemeProvider to main.tsx
- **Backend not running**: Start the backend first before the frontend
- **Port conflicts**: Change the port in the commands if 8000 or 5173 are in use

## API Testing

You can test the API directly using Swagger UI at http://localhost:8000/docs or with curl commands:

```bash
# Health check
curl http://localhost:8000/health

# Create a collection
curl -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test Collection","description":"Test"}'

# List collections
curl http://localhost:8000/collections
```

## Notes

- Storage is in-memory, so data will be lost when you restart the backend
- The frontend connects to the backend at http://localhost:8000 by default
- For production, use the Docker setup