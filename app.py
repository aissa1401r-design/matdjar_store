import os, requests
from flask import Flask, render_template, request, redirect, session
app = Flask(__name__)
app.secret_key = "matdjar-123"

TURSO_URL = os.getenv("TURSO_DATABASE_URL","").replace("libsql://","https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD","1234")

def turso(sql):
    if not TURSO_URL: return []
    try:
        r = requests.post(f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type":"application/json"},
            json={"requests":[{"type":"execute","stmt":{"sql":sql}},{"type":"close"}]})
        j = r.json()
        rows = j['results'][0]['response']['result'].get('rows', [])
        return [[c.get('value') for c in row] for row in rows]
    except Exception as e:
        print("ERROR", e)
        return []

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
    name = request.form.get("name","").replace("'","''").strip()
    if name: turso(f"INSERT INTO categories (name) VALUES ('{name}')")
    return redirect("/admin?msg=تم حفظ النوع ✅")

@app.route("/admin/del_cat/<cid>")
def del_cat(cid):
    turso(f"DELETE FROM categories WHERE id={cid}")
    return redirect("/admin")

@app.route("/admin/add_prod", methods=["POST"])
def add_prod():
    name = request.form.get("name","").replace("'","''").strip()
    price = request.form.get("price","0").strip() or "0"
    cat_id = request.form.get("cat_id","1").strip() or "1"
    image = request.form.get("image","").replace("'","").strip()
    if not image: image = "https://via.placeholder.com/400"
    if not name: name = "منتج"
    turso(f"INSERT INTO products (name, category_id, image, price) VALUES ('{name}', {cat_id}, '{image}', {price})")
    return redirect(f"/admin?msg=تم حفظ المنتج: {name} ✅")

@app.route("/admin/del_prod/<pid>")
def del_prod(pid):
    turso(f"DELETE FROM products WHERE id={pid}")
    return redirect("/admin")

@app.route("/reset")
def reset():
    turso("DROP TABLE IF EXISTS products")
    turso("DROP TABLE IF EXISTS categories")
    turso("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
    turso("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT, price REAL)")
    turso("INSERT INTO categories (name) VALUES ('ملابس')")
    return "تم التصفير ✅ - <a href='/admin'>روح للإدارة</a>"

@app.route("/seed")
def seed():
    return redirect("/reset")

if __name__ == "__main__":
    app.run()
