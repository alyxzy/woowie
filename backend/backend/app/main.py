from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2

app = FastAPI(title="Thai Drill Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL")


class User(BaseModel):
    nickname: str


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            nickname TEXT PRIMARY KEY,
            starts INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/quiz/start")
def start_quiz(user: User):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT starts FROM users WHERE nickname = %s", (user.nickname,))
    result = cur.fetchone()

    if result:
        starts = result[0] + 1
        cur.execute(
            "UPDATE users SET starts = %s WHERE nickname = %s",
            (starts, user.nickname),
        )
    else:
        starts = 1
        cur.execute(
            "INSERT INTO users (nickname, starts) VALUES (%s, %s)",
            (user.nickname, starts),
        )

    conn.commit()
    cur.close()
    conn.close()

    return {"nickname": user.nickname, "starts": starts}


@app.get("/api/user/{nickname}")
def get_user(nickname: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT starts FROM users WHERE nickname = %s", (nickname,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        return {"nickname": nickname, "starts": result[0]}
    return {"nickname": nickname, "starts": 0}
