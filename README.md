# Procurement Intelligence SQL Agent

An AI-powered procurement analytics app. Ask procurement questions in natural language and receive read-only analysis generated from the vendor and quotation data in your PostgreSQL database.

## Requirements

- Python 3.10 or later
- PostgreSQL with the procurement database and tables described below
- A Gemini API key

## Configuration

Create `backend/.env` with your own connection string and API key:

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/procurement_agent_db
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit `.env` or share your API key. The application expects these tables:

- `vendors`: vendor contact details, performance scores, delivery metrics, and preferred-vendor status
- `quotations`: vendor, product, quantity, pricing, delivery, warranty, and payment-term details

See `backend/sql_agent.py` for the columns expected by the agent.

## Run Locally

From the repository root, install the backend dependencies and start the API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `frontend/index.html` in a browser. The frontend expects the API at `http://localhost:8000`.

The API is available at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`. Use `http://localhost:8000/health` to check the database connection.

## API

`POST /api/query` accepts a question and optional conversation history as query parameters:

```text
/api/query?question=Which%20vendors%20have%20the%20best%20delivery%20record%3F
```

Queries are intended for read-only procurement analysis. The backend validates generated SQL and blocks destructive requests.