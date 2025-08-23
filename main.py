from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure this env var is set

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf8") as f:
        return HTMLResponse(f.read())

@app.post("/api/send")
async def chat_api(user_message: str = Form(...)):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150
        )
        bot_reply = response.choices[0].message.content
        return JSONResponse({"bot_response": bot_reply})
    except Exception as e:
        return JSONResponse({"bot_response": f"OpenAI error: {str(e)}"})
