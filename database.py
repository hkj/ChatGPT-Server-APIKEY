import os
import sqlite3
import secrets
import threading

DATABASE_URL = "api_keys.db"

# スレッドごとに格納されるコネクション用のコンテナを作成
_thread_local = threading.local()


def get_conn():
    if not hasattr(_thread_local, "conn"):
        _thread_local.conn = sqlite3.connect(DATABASE_URL)
    return _thread_local.conn


def close_conn():
    if hasattr(_thread_local, "conn"):
        _thread_local.conn.close()
        del _thread_local.conn


def create_table():
    conn = get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS api_keys (email TEXT PRIMARY KEY, api_key TEXT NOT NULL, deleted BOOLEAN NOT NULL DEFAULT 0)"
    )


def generate_and_store_api_key(email: str) -> str:
    api_key = secrets.token_hex(16)

    conn = get_conn()
    try:
        with conn:
            # email, 作成したapi_keyをDBに突っ込む
            conn.execute(
                "INSERT INTO api_keys (email, api_key) VALUES (?, ?)", (email, api_key)
            )
    # 既に存在していた場合
    except sqlite3.IntegrityError:
        cursor = conn.execute(
            # 削除キー、api_keyを取得
            "SELECT api_key, deleted FROM api_keys WHERE email = ?",
            (email,),
        )
        api_key, deleted = cursor.fetchone()

        # 削除フラグが立っていたら、使用不可
        if deleted:
            api_key = "deleted"

    close_conn()

    return api_key


create_table()
