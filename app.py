import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def turso(sql):
    if not TURSO_URL or not TURSO_TOKEN:
        return []
    try:
        r = requests.post(
            f"{TURSO_URL}/v2/pipeline",
            headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
            json={"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
        )
        data = r.json()
        rows = data['results'][0]['response']['result']['rows']
        return rows
    except:
        return []

# انشاء الجداول اوتوماتيك
turso("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
turso("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT)")

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8"><title>متجر مات جار</title>
<style>
 body{font-family: Tahoma; background:#f7f7f7; padding:20px; direction:rtl}
.container{display:flex; gap:20px}
.cats{width:220px; display:flex; flex-direction:column; gap:10px}
.cat{background:white; padding:12px; border-radius:8px; text-align:center; font-weight:bold}
.products{flex:1; display:flex; flex-wrap:wrap; gap:15px; flex-direction:row-reverse; justify-content:flex-start}
.prod{background:white; width:180px; padding:10px; border-radius:8px; text-align:center}
.prod img{width:100%; height:120px; object-fit:cover; border-radius:6px}
</style>
</head>
<body>
<h1>متجر مات جار</h1>
<div class="container">
  <div class="cats">
    <h3>الأنواع من الفوق للتحت</h3>
    {% for c in cats %}<div class="cat">{{c[1]['value']}}</div>{% endfor %}
  </div>
  <div class="products">
    {% for p in prods %}
    <div class="prod">
      <img src="{{ p[3]['value'] or 'https://via.placeholder.com/150' }}">
      <div>{{p[1]['value']}}</div>
    </div>
    {% endfor %}
  </div>
</div>
<br><a href="/seed">اضغط هنا لتعمير المتجر</a>
</body>
</html>
"""

@app.route("/")
def home():
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template_string(HTML, cats=cats, prods=prods)

@app.route("/seed")
def seed():
    turso("DELETE FROM products")
    turso("DELETE FROM categories")
    turso("INSERT INTO categories (id, name) VALUES (1, 'هواتف')")
    turso("INSERT INTO categories (id, name) VALUES (2, 'احذية')")
    turso("INSERT INTO categories (id, name) VALUES (3, 'ملابس')")
    turso("INSERT INTO products (name, category_id, image) VALUES ('iPhone 15', 1, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=200')")
    turso("INSERT INTO products (name, category_id, image) VALUES ('حذاء نايك', 2, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200')")
    turso("INSERT INTO products (name, category_id, image) VALUES ('تيشيرت', 3, 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=200')")
    return "تم تعمير المتجر بنجاح! <a href='/'>روح للرئيسية</a>"

if __name__ == "__main__":
    app.run()
