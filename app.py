from flask import Flask, render_template_string, request, redirect, url_for
from supabase import create_client
import os

app = Flask(__name__)

# --- 1. الربط مع Supabase ---
# هذو راح تحطهم في Render كيما نقولك لتحت
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://YOUR-PROJECT.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR-KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# كلمة سر باش تدخل للادارة - بدلها كيما تحب
ADMIN_PASSWORD = "matdjar123"

# --- 2. قالب المتجر للزبائن ---
STORE_TEMPLATE = """
<h1>متجر mat_djar</h1>
{% for p in products %}
<div style="border:1px solid #ccc; margin:10px; padding:10px">
  <h3>{{ p['name'] }}</h3>
  <p>السعر: {{ p['price'] }} دج</p>
  <p>{{ p['description'] }}</p>
</div>
{% endfor %}
<a href="/admin">دخول الادارة</a>
"""

# --- 3. قالب الادارة ---
ADMIN_TEMPLATE = """
<h1>لوحة التحكم mat_djar</h1>
<form method="post" action="/admin/add">
  <input name="name" placeholder="اسم المنتج" required>
  <input name="price" type="number" placeholder="السعر" required>
  <input name="description" placeholder="الوصف">
  <button type="submit">زيد منتج</button>
</form>
<hr>
{% for p in products %}
<div>
  {{ p['name'] }} - {{ p['price'] }} دج 
  <a href="/admin/delete/{{ p['id'] }}" style="color:red"> [حذف] </a>
</div>
{% endfor %}
<a href="/">رجوع للمتجر</a>
"""

@app.route("/")
def store():
    products = supabase.table("products").select("*").execute().data
    return render_template_string(STORE_TEMPLATE, products=products)

@app.route("/admin")
def admin():
    # صفحة تسجيل دخول بسيطة
    password = request.args.get("password")
    if password != ADMIN_PASSWORD:
        return """<form><input name="password" type="password" placeholder="كلمة السر"><button>دخول</button></form> كلمة السر هي: matdjar123"""
    
    products = supabase.table("products").select("*").execute().data
    return render_template_string(ADMIN_TEMPLATE, products=products)

@app.route("/admin/add", methods=["POST"])
def add_product():
    data = {
        "name": request.form["name"],
        "price": int(request.form["price"]),
        "description": request.form.get("description", "")
    }
    supabase.table("products").insert(data).execute()
    return redirect(f"/admin?password={ADMIN_PASSWORD}")

@app.route("/admin/delete/<id>")
def delete_product(id):
    supabase.table("products").delete().eq("id", id).execute()
    return redirect(f"/admin?password={ADMIN_PASSWORD}")

if __name__ == "__main__":
    app.run()
