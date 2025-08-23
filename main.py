from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import requests
import os

HF_MODEL = "facebook/blenderbot-400M-distill" 
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_TOKEN = os.getenv("HF_TOKEN") 

DB_FILE = "db.sqlite"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT NOT NULL,
        bot_response TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()

init_db()

def log_message(user_input, bot_response):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_input, bot_response) VALUES (?, ?)", (user_input, bot_response))
    conn.commit()
    conn.close()

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/api/send")
async def chat_api(user_message: str = Form(...)):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": user_message}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        data = response.json()
        # Data may be a list or dict depending on model API response
        bot_reply = None
        if isinstance(data, dict) and "error" in data:
            bot_reply = f"API error: {data['error']}"
        elif isinstance(data, dict) and "generated_text" in data:
            bot_reply = data["generated_text"]
        elif isinstance(data, list) and "generated_text" in data[0]:
            bot_reply = data["generated_text"]
        else:
            bot_reply = "Sorry, I could not process your request."
        # Log to DB
        log_message(user_message, bot_reply)
        return JSONResponse({"bot_response": bot_reply})
    except Exception as e:
        return JSONResponse({"bot_response": f"Error: {str(e)}"})

