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
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>متجر مات جار</title>
<style>
 *{box-sizing:border-box; margin:0; padding:0}
 body{font-family: Tahoma; background:#f1f1f1; direction:rtl; padding:10px}
 h1{margin:10px 0 20px 0; text-align:center}
.container{display:flex; gap:15px; flex-direction:column}
 @media(min-width:768px){.container{flex-direction:row} }
.cats{order:2}
 @media(min-width:768px){.cats{order:1; width:220px} }
.cats h3{margin-bottom:10px; font-size:18px}
.cat{background:white; padding:15px; border-radius:12px; margin-bottom:10px; text-align:center; font-weight:bold; font-size:16px; box-shadow:0 2px 5px #0001}
.products{order:1; display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:1}
 @media(min-width:768px){.products{order:2; grid-template-columns:repeat(3, 1fr)} }
.prod{background:white; border-radius:15px; overflow:hidden; box-shadow:0 2px 8px #0002; text-align:center; padding-bottom:10px}
.prod img{width:100%; height:180px; object-fit:cover}
.prod div{padding:10px; font-size:16px; font-weight:bold}
.seed-btn{display:block; background:#000; color:#fff; text-align:center; padding:12px; border-radius:10px; text-decoration:none; margin:20px 0}
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
      <img src="{{ p[3]['value'] or 'https://via.placeholder.com/300' }}">
      <div>{{p[1]['value']}}</div>
    </div>
    {% endfor %}
  </div>
</div>
<a class="seed-btn" href="/seed">تعمير المتجر</a>
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
