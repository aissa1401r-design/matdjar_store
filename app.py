import os, requests
from flask import Flask, render_template, request, redirect, session
app = Flask(__name__)
app.secret_key = "matdjar-secret-123"

TURSO_URL = os.getenv("TURSO_DATABASE_URL","").replace("libsql://","https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD","1234")

def turso(sql):
    print(f"SQL: {sql}")
    if not TURSO_URL or not TURSO_TOKEN: return []
    try:
        r = requests.post(f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type":"application/json"},
            json={"requests":[{"type":"execute","stmt":{"sql":sql}},{"type":"close"}]})
        data = r.json()
        # لو كاين خطأ من Turso
        if 'results' not in data:
            print(f"TURSO FULL ERROR: {data}")
            return data
        res = data['results'][0]
        if 'response' not in res or 'result' not in res['response']:
            print(f"TURSO ERROR RES: {res}")
            return res
        rows = res['response']['result'].get('rows', [])
        if not rows:
            return []
        return [[c.get('value') for c in row] for row in rows]
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return str(e)

turso("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
turso("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT, price REAL)")

@app.route("/")
def home():
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    if isinstance(cats, dict) or isinstance(cats, str): cats = []
    if isinstance(prods, dict) or isinstance(prods, str): prods = []
    return render_template("index.html", cats=cats, prods=prods)

@app.route("/admin")
def admin():
    if not session.get("admin"): return redirect("/login")
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    if isinstance(cats, dict) or isinstance(cats, str): cats = []
    if isinstance(prods, dict) or isinstance(prods, str): prods = []
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
    turso(f"INSERT INTO categories (name) VALUES ('{name}')")
    return redirect("/admin")

@app.route("/admin/del_cat/<cid>")
def del_cat(cid):
    turso(f"DELETE FROM categories WHERE id={cid}")
    return redirect("/admin")

@app.route("/admin/add_prod", methods=["POST"])
def add_prod():
    name = request.form.get("name","").replace("'","''").strip()
    price = request.form.get("price","0").replace("'","")
    cat_id = request.form.get("cat_id","1").replace("'","")
    image = request.form.get("image","").replace("'","").strip()

    # تنظيف cat_id لازم يكون رقم
    try:
        int(cat_id)
    except:
        cat_id = "1"

    if not name: name = "منتج"
    if not image: image = "https://via.placeholder.com/400"

    sql = f"INSERT INTO products (name, category_id, image, price) VALUES ('{name}', {cat_id}, '{image}', {price})"
    result = turso(sql)

    # اذا كاين خطأ نوريهولك بوضوح
    if isinstance(result, dict) or isinstance(result, str):
        return f"<h1>خطأ في القاعدة</h1><pre>{result}</pre><p>SQL: {sql}</p><a href='/admin'>رجوع</a>"

    return redirect("/admin")

@app.route("/admin/del_prod/<pid>")
def del_prod(pid):
    turso(f"DELETE FROM products WHERE id={pid}")
    return redirect("/admin")

@app.route("/seed")
def seed():
    turso("DELETE FROM products"); turso("DELETE FROM categories")
    turso("INSERT INTO categories (id, name) VALUES (1, 'عام')")
    return redirect("/admin")
@app.route("/debug")
def debug():
    return f"Cats: {turso('SELECT * FROM categories')} <br> Prods: {turso('SELECT * FROM products')}"
