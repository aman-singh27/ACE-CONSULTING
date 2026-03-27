# JobIntel Full Application Runbook

This guide covers everything you need to start the entire JobIntel stack from scratch, including PostgreSQL, the FastAPI backend, the React/Vite frontend, and Ngrok for Apify webhooks.

---

## 🏗️ 1. Start the Database Layer
Your application relies on PostgreSQL running via Docker.
1. Open up a terminal.
2. Navigate to the backend directory:
   ```powershell
   cd "c:\Users\Aman Singh\ACE CONSULTING\jobintel\backend"
   ```
3. Start the Docker Postgres container in the background:
   ```powershell
   docker compose up -d
   ```
4. Verify it's running:
   ```powershell
   docker ps
   ```
   *(You should see `jobintel_postgres` running on port 5432).*

---

## 🌐 2. Start Ngrok (For Apify Webhooks)
Because Apify needs a public URL to send the scraped data back to your local machine, you must run an ngrok tunnel.
1. Open a **new, separate terminal**.
2. Run ngrok to tunnel traffic to your backend's port (8000):
   ```powershell
   ngrok http 8000
   ```
3. When ngrok starts, it will display a Forwarding URL that looks something like this:
   `https://1234-abcd.ngrok-free.dev`
4. **Copy this Forwarding URL!** Leave this terminal open.

---

## ⚙️ 3. Configure the Backend
Your backend needs to know the ngrok URL so it can tell Apify where to send the webhook.
1. Open the file `jobintel/backend/.env` in your editor.
2. Find the `WEBHOOK_URL` line and update it with the new ngrok URL you just copied, appending `/api/v1/webhook/apify` to the end.
   
   **Example:**
   ```env
   # Inside jobintel/backend/.env
   WEBHOOK_URL=https://1234-abcd.ngrok-free.dev/api/v1/webhook/apify
   WEBHOOK_SECRET=supersecretwebhook
   ```
   *(Note: You must update this `.env` file **every time** you restart ngrok, as the ngrok URL changes).*

---

## 🚀 4. Start the Backend API
1. Open a **new terminal**.
2. Navigate to your backend folder:
   ```powershell
   cd "c:\Users\Aman Singh\ACE CONSULTING\jobintel\backend"
   ```
3. Activate the Python virtual environment:
   ```powershell
   venv\Scripts\activate.bat
   ```
   *(If you are using PowerShell, you might need to use `venv\Scripts\Activate.ps1`)*
4. Run the database migrations (this maps the latest tables to PostgreSQL):
   ```powershell
   alembic upgrade head
   ```
5. Start the FastAPI server using Uvicorn:
   ```powershell
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
6. The backend API is now alive at `http://localhost:8000`. You can view the docs at [`http://localhost:8000/docs`](http://localhost:8000/docs). 

---

## 🎨 5. Start the Frontend Application
1. Open a **final, new terminal** (you can use Windows Command Prompt (`cmd`) for this since it's an npm command that threw path errors in PowerShell previously, though standard PowerShell works fine too).
2. Navigate to your frontend folder:
   ```powershell
   cd "c:\Users\Aman Singh\ACE CONSULTING\jobintel-frontend"
   ```
3. Run the development server:
   ```cmd
   npm run dev
   ```
4. In your terminal, you will see a local URL, usually `http://localhost:5173/`. 
5. `CTRL+Click` that link or open your browser to `http://localhost:5173/` to view the JobIntel frontend!

---

## 🎯 Summary Checklist

Before clicking anything in the app, verify your terminals:
- [x] Terminal 1: Docker Desktop / `docker compose up -d` is active.
- [x] Terminal 2: `ngrok http 8000` is running.
- [x] You pasted the ngrok Forwarding URL into `backend/.env`.
- [x] Terminal 3: The `uvicorn` backend server is running on port `8000`.
- [x] Terminal 4: The `npm run dev` frontend server is running on `5173`.
