import os, requests
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "matdjar-secret-123"

TURSO_URL = os.getenv("TURSO_DATABASE_URL","").replace("libsql://","https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD","1234")

def turso(sql):
    if not TURSO_URL or not TURSO_TOKEN: return []
    try:
        r = requests.post(f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type":"application/json"},
            json={"requests":[{"type":"execute","stmt":{"sql":sql}},{"type":"close"}]})
        rows = r.json()['results'][0]['response']['result']['rows']
        # نحولها لقائمة بسيطة باش الـ HTML يولي ساهل
        clean = []
        for row in rows:
            clean.append([c.get('value') for c in row])
        return clean
    except: return []

turso("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
turso("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT, price REAL)")

@app.route("/")
def home():
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template("index.html", cats=cats, prods=prods)

@app.route("/admin")
def admin():
    if not session.get("admin"): return redirect("/login")
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template("admin.html", cats=cats, prods=prods)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST" and request.form.get("password")==ADMIN_PASS:
        session["admin"]=True
        return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin/add_cat", methods=["POST"])
def add_cat():
    if not session.get("admin"): return redirect("/login")
    name=request.form.get("name","").replace("'","")
    turso(f"INSERT INTO categories (name) VALUES ('{name}')")
    return redirect("/admin")

@app.route("/admin/del_cat/<cid>")
def del_cat(cid):
    turso(f"DELETE FROM categories WHERE id={cid}")
    return redirect("/admin")

@app.route("/admin/add_prod", methods=["POST"])
def add_prod():
    name=request.form.get("name","").replace("'","")
    turso(f"INSERT INTO products (name, category_id, image, price) VALUES ('{name}', {request.form.get('cat_id')}, '{request.form.get('image')}', {request.form.get('price') or 0})")
    return redirect("/admin")

@app.route("/admin/del_prod/<pid>")
def del_prod(pid):
    turso(f"DELETE FROM products WHERE id={pid}")
    return redirect("/admin")
