import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def turso(sql):
    if not TURSO_URL or not TURSO_TOKEN:
        return []
    r = requests.post(
        f"{TURSO_URL}/v2/pipeline",
        headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
        json={"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    )
    try:
        data = r.json()
        rows = data['results'][0]['response']['result']['rows']
        return rows
    except:
        return []

# ننشؤو الجداول
turso("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
turso("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT)")

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8">
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
    {% for c in cats %}<div class="cat">{{c[1]['value'] if c[1] else ''}}</div>{% endfor %}
  </div>
  <div class="products">
    {% for p in prods %}
    <div class="prod">
      <img src="{{ (p[3]['value'] if p|length>3 and p[3] else '') or 'https://via.placeholder.com/150'}}">
      <div>{{p[1]['value']}}</div>
    </div>
    {% endfor %}
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    cats = turso("SELECT * FROM categories ORDER BY id DESC")
    prods = turso("SELECT * FROM products ORDER BY id DESC")
    return render_template_string(HTML, cats=cats, prods=prods)
INSERT INTO categories (name) VALUES ('هواتف');
INSERT INTO categories (name) VALUES ('أحذية');
INSERT INTO categories (name) VALUES ('ملابس');

INSERT INTO products (name, category_id, image) VALUES ('iPhone 15', 1, 'https://via.placeholder.com/200');
INSERT INTO products (name, category_id, image) VALUES ('حذاء نايك', 2, 'https://via.placeholder.com/200');
INSERT INTO products (name, category_id, image) VALUES ('تيشيرت', 3, 'https://via.placeholder.com/200');

if __name__ == "__main__":
    app.run()
