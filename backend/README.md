# Inevitable Backend

The backend is built with FastAPI and Python >= 3.11.

## Local Setup

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Environment Setup**
   Copy the example environment file from the repository root:
   ```bash
   cp ../.env.example .env
   ```
   Do not commit the `.env` file or include any real credentials.

5. **Run the server**
   ```bash
   inevitable
   # Or alternatively:
   # python -m inevitable.app
   ```
   The API will be accessible at `http://127.0.0.1:8000`.

## Testing

Run tests using pytest:
```bash
pytest tests/
```
