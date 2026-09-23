import os
import libsql_experimental as libsql
from flask import Flask, render_template_string

app = Flask(__name__)

url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")
conn = libsql.connect(database=url, auth_token=auth_token)

# انشاء الجداول اذا ما كاينينش
conn.execute("""
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY, name TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, image TEXT
)
""")
conn.commit()

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
  body{font-family: Tahoma; background:#f7f7f7; margin:0; padding:20px; direction: rtl;}
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
      <h3>الأنواع</h3>
      {% for c in cats %}
        <div class="cat">{{c[1]}}</div>
      {% endfor %}
    </div>
    <div class="products">
      {% for p in prods %}
        <div class="prod">
          <img src="{{p[3] or 'https://via.placeholder.com/150'}}">
          <div>{{p[1]}}</div>
        </div>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    cats = conn.execute("SELECT * FROM categories ORDER BY id DESC").fetchall()
    prods = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template_string(HTML, cats=cats, prods=prods)

if __name__ == "__main__":
    app.run()
