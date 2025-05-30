
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, uuid, os
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

class User(BaseModel):
    username: str
    password: str

class Transaksi(BaseModel):
    username: str
    nomor: str
    nominal: int
    jenis: str

class Topup(BaseModel):
    username: str
    jumlah: int

@app.post("/register")
def register(user: User):
    users = load_json("users.json")
    if any(u["username"] == user.username for u in users):
        raise HTTPException(status_code=400, detail="Username sudah ada")
    users.append({**user.dict(), "saldo": 0})
    save_json("users.json", users)
    return {"message": "Registrasi berhasil"}

@app.post("/login")
def login(user: User):
    users = load_json("users.json")
    for u in users:
        if u["username"] == user.username and u["password"] == user.password:
            return {"message": "Login sukses"}
    raise HTTPException(status_code=401, detail="Login gagal")

@app.post("/isi-pulsa")
def isi_pulsa(trans: Transaksi):
    users = load_json("users.json")
    transaksi = load_json("transaksi.json")
    user = next((u for u in users if u["username"] == trans.username), None)
    if not user or user["saldo"] < trans.nominal:
        raise HTTPException(status_code=400, detail="Saldo tidak cukup")
    user["saldo"] -= trans.nominal
    trans_id = str(uuid.uuid4())
    item = trans.dict()
    item["id"] = trans_id
    item["tanggal"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transaksi.append(item)
    save_json("users.json", users)
    save_json("transaksi.json", transaksi)
    return {"message": "Transaksi berhasil", "id": trans_id}

@app.post("/topup")
def topup(topup: Topup):
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == topup.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    user["saldo"] += topup.jumlah
    save_json("users.json", users)
    return {"message": "Topup berhasil"}

@app.get("/saldo/{username}")
def saldo(username: str):
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return {"saldo": user["saldo"]}

@app.get("/riwayat/{username}")
def riwayat(username: str):
    data = load_json("transaksi.json")
    return [d for d in data if d["username"] == username]

@app.get("/admin/users")
def list_users():
    return load_json("users.json")

@app.get("/admin/transaksi")
def semua_transaksi():
    return load_json("transaksi.json")
