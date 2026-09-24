import os
import requests
from flask import Flask, render_template_string, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "matdjar-secret-123"

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "1234") # الباسورد الافتراضي 1234

def turso(sql):
    if not TURSO_URL or not TURSO_TOKEN: return []
    try:
        r = requests.post(
            f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
            json={"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
        )
        data = r.json()
        rows = data['results'][0]['response']['result']['rows']
        return rows
    except Exception as e:
        print(e)
        return []

turso("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
turso("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT, price REAL)")

# ===== واجهة المتجر =====
STORE_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>متجر مات جار</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}body{font-family:Tahoma;background:#f1f1f1;direction:rtl;padding:10px}
h1{margin:10px 0;text-align:center}.container{display:flex;gap:15px;flex-direction:column}
@media(min-width:768px){.container{flex-direction:row}}
.cats{order:2}@media(min-width:768px){.cats{order:1;width:220px}}
.cat{background:white;padding:15px;border-radius:12px;margin-bottom:10px;text-align:center;font-weight:bold;box-shadow:0 2px 5px #0001}
.products{order:1;display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1}
@media(min-width:768px){.products{order:2;grid-template-columns:repeat(3,1fr)}}
.prod{background:white;border-radius:15px;overflow:hidden;box-shadow:0 2px 8px #0002;text-align:center}
.prod img{width:100%;height:200px;object-fit:cover}.prod.n{padding:10px;font-weight:bold}
a.admin{position:fixed;bottom:15px;left:15px;background:black;color:white;padding:12px 18px;border-radius:50px;text-decoration:none}
</style></head><body>
<h1>متجر مات جار</h1>
<div class="container">
  <div class="cats"><h3>الأنواع</h3>{% for c in cats %}<div class="cat">{{c[1]['value']}}</div>{% endfor %}</div>
  <div class="products">{% for p in prods %}
    <div class="prod"><img src="{{ p[3]['value'] }}"><div class="n">{{p[1]['value']}}<br><small>{{p[4]['value'] or ''}} دج</small></div></div>
  {% endfor %}</div>
</div>
<a class="admin" href="/admin">الإدارة ⚙️</a>
</body></html>
"""

# ===== واجهة الإدارة =====
ADMIN_HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>الإدارة</title><style>
body{font-family:Tahoma;background:#fff;padding:15px;direction:rtl}input,select,button{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #ccc}
button{background:black;color:white;font-weight:bold}.card{border:1px solid #eee;padding:12px;border-radius:10px;margin-bottom:10px;display:flex;gap:10px;align-items:center}
.card img{width:60px;height:60px;object-fit:cover;border-radius:8px}.del{background:red;color:white;padding:6px 10px;border-radius:6px;text-decoration:none}
h2{margin-top:25px}
</style></head><body>
<h1>لوحة الإدارة <a href="/logout" style="float:left">خروج</a></h1>

<h2>➕ زيد نوع جديد</h2>
<form method="post" action="/admin/add_cat"><input name="name" placeholder="اسم النوع مثلا: ساعات" required><button>حفظ النوع</button></form>
{% for c in cats %}<div class="card"><div style="flex:1">{{c[1]['value']}}</div><a class="del" href="/admin/del_cat/{{c[0]['value']}}">حذف</a></div>{% endfor %}
<h2>➕ زيد منتج جديد</h2>
<form method="post" action="/admin/add_prod">
<input name="name" placeholder="اسم المنتج" required>
<input name="price" placeholder="السعر" type="number">
<select name="cat_id" required>{% for c in cats %}<option value="{{c[0]['value']}}">{{c[1]['value']}}</option>{% endfor %}</select>
<input name="image" placeholder="رابط الصورة https://..." required>
<button>حفظ المنتج</button>
</form>

<h2>📦 المنتجات ({{prods|length}})</h2>
{% for p in prods %}
<div class="card"><img src="{{p[3]['value']}}"><div style="flex:1"><b>{{p[1]['value']}}</b><br><small>{{p[4]['value'] or 0}} دج</small></div>
<a class="del" href="/admin/del_prod/{{p[0]['value']}}">حذف</a></div>
{% endfor %}
<br><a href="/">← العودة للمتجر</a>
</body></html>
"""

LOGIN_HTML = """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="font-family:Tahoma;text-align:center;padding:40px" dir="rtl">
<h2>دخول الإدارة</h2><form method="post"><input name="password" type="password" placeholder="كلمة السر" style="padding:12px;width:80%">
<br><br><button style="padding:12px 30px;background:black;color:white;border-radius:8px">دخول</button></form>
<p>الافتراضي: 1234</p></body></html>
"""

@app.route("/")
def home():
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template_string(STORE_HTML, cats=cats, prods=prods)

@app.route("/admin", methods=["GET"])
def admin():
    if not session.get("admin"): return redirect("/login")
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template_string(ADMIN_HTML, cats=cats, prods=prods)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin/add_cat", methods=["POST"])
def add_cat():
    if not session.get("admin"): return redirect("/login")
    name = request.form.get("name","").replace("'","")
    turso(f"INSERT INTO categories (name) VALUES ('{name}')")
    return redirect("/admin")

@app.route("/admin/del_cat/<cid>")
def del_cat(cid):
    if not session.get("admin"): return redirect("/login")
    turso(f"DELETE FROM categories WHERE id={cid}")
    return redirect("/admin")

@app.route("/admin/add_prod", methods=["POST"])
def add_prod():
    if not session.get("admin"): return redirect("/login")
    name = request.form.get("name","").replace("'","")
    cat = request.form.get("cat_id")
    img = request.form.get("image","").replace("'","")
    price = request.form.get("price") or 0
    turso(f"INSERT INTO products (name, category_id, image, price) VALUES ('{name}', {cat}, '{img}', {price})")
    return redirect("/admin")

@app.route("/admin/del_prod/<pid>")
def del_prod(pid):
    if not session.get("admin"): return redirect("/login")
    turso(f"DELETE FROM products WHERE id={pid}")
    return redirect("/admin")

@app.route("/seed")
def seed():
    turso("DELETE FROM products"); turso("DELETE FROM categories")
    turso("INSERT INTO categories (id, name) VALUES (1, 'هواتف')")
    turso("INSERT INTO categories (id, name) VALUES (2, 'احذية')")
    turso("INSERT INTO categories (id, name) VALUES (3, 'ملابس')")
    turso("INSERT INTO products (name, category_id, image, price) VALUES ('iPhone 15', 1, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400', 180000)")
    turso("INSERT INTO products (name, category_id, image, price) VALUES ('حذاء نايك', 2, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', 8500)")
    turso("INSERT INTO products (name, category_id, image, price) VALUES ('تيشيرت', 3, 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', 2500)")
    return redirect("/")
if __name__ == "__main__":
    app.run()
