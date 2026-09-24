import os, requests
from flask import Flask, render_template, request, redirect, session
app = Flask(__name__)
app.secret_key = "matdjar-secret-123"

TURSO_URL = os.getenv("TURSO_DATABASE_URL","").replace("libsql://","https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD","1234")

def turso(sql):
    print(f"SQL: {sql}")
    if not TURSO_URL or not TURSO_TOKEN:
        print("TURSO ENV MISSING")
        return []
    try:
        r = requests.post(f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type":"application/json"},
            json={"requests":[{"type":"execute","stmt":{"sql":sql}},{"type":"close"}]})
        data = r.json()
        print(f"TURSO RESP: {data}")
        if 'results' in data and data['results'][0]['response']['result']['rows']:
            rows = data['results'][0]['response']['result']['rows']
            return [[c.get('value') for c in row] for row in rows]
        # اذا كان INSERT يرجع فاضي
        return []
    except Exception as e:
        print(f"TURSO ERROR: {e}")
        return f"ERROR: {e}"

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
    name=request.form.get("name","").replace("'","''")
    res = turso(f"INSERT INTO categories (name) VALUES ('{name}')")
    print(f"ADD CAT RES: {res}")
    return redirect("/admin")

@app.route("/admin/del_cat/<cid>")
def del_cat(cid):
    turso(f"DELETE FROM categories WHERE id={cid}")
    return redirect("/admin")

@app.route("/admin/add_prod", methods=["POST"])
def add_prod():
    try:
        name = request.form.get("name","").replace("'","''").strip()
        cat_id = request.form.get("cat_id") or "1"
        image = request.form.get("image","").strip()
        price = request.form.get("price") or "0"

        # حماية الرابط
        image = image.replace("'","")

        sql = f"INSERT INTO products (name, category_id, image, price) VALUES ('{name}', {cat_id}, '{image}', {price})"
        res = turso(sql)
        print(f"ADD PROD RES: {res}")
        if isinstance(res, str) and "ERROR" in res:
            return f"<h1>خطأ في القاعدة:</h1><p>{res}</p><p>SQL: {sql}</p><a href='/admin'>رجوع</a>"
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return f"Exception: {e} <br><a href='/admin'>رجوع</a>"
    return redirect("/admin")

@app.route("/admin/del_prod/<pid>")
def del_prod(pid):
    turso(f"DELETE FROM products WHERE id={pid}")
    return redirect("/admin")

# صفحة باش نشوفو الخطأ
@app.route("/debug")
def debug():
    cats = turso("SELECT * FROM categories")
    prods = turso("SELECT * FROM products")
    return f"<h1>DEBUG</h1><p>Cats: {cats}</p><p>Prods: {prods}</p><p>URL SET: {bool(TURSO_URL)}</p><a href='/admin'>admin</a>"

@app.route("/seed")
def seed():
    turso("DELETE FROM products"); turso("DELETE FROM categories")
    turso("INSERT INTO categories (id, name) VALUES (1, 'هواتف')")
    return redirect("/")
