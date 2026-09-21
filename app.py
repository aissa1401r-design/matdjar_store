from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)

# --- قائمة احتياطية اذا Supabase ما كاينش ---
FALLBACK_PRODUCTS = [
    {"id": 1, "name": "حذاء عصري", "price": 4500, "description": "متوفر جميع المقاسات"},
    {"id": 2, "name": "كسوة تقليدية", "price": 7500, "description": "صناعة تقليدية"},
]

# --- نحاولو نربطو بـ Supabase ---
supabase = None
try:
    from supabase import create_client
    URL = os.environ.get("SUPABASE_URL")
    KEY = os.environ.get("SUPABASE_KEY")
    if URL and KEY and "YOUR-PROJECT" not in URL:
        supabase = create_client(URL, KEY)
        print("✅ تم الربط مع Supabase")
    else:
        print("⚠️ مفاتيح Supabase غير موجودة - نخدم بالقائمة")
except Exception as e:
    print(f"⚠️ Supabase ما خدمش: {e} - نخدم بالقائمة")
    supabase = None

def get_products():
    if supabase:
        try:
            res = supabase.table("products").select("*").execute()
            return res.data
        except Exception as e:
            print(f"خطأ Supabase: {e}")
            return FALLBACK_PRODUCTS
    else:
        return FALLBACK_PRODUCTS

def add_product_db(data):
    if supabase:
        try:
            supabase.table("products").insert(data).execute()
            return True
        except Exception as e:
            print(f"خطأ الاضافة: {e}")
            return False
    else:
        # نزيدو للقائمة المؤقتة
        new_id = max([p['id'] for p in FALLBACK_PRODUCTS], default=0) + 1
        data['id'] = new_id
        FALLBACK_PRODUCTS.append(data)
        return True

def delete_product_db(pid):
    if supabase:
        try:
            supabase.table("products").delete().eq("id", pid).execute()
        except Exception as e:
            print(e)
    else:
        global FALLBACK_PRODUCTS
        FALLBACK_PRODUCTS = [p for p in FALLBACK_PRODUCTS if str(p['id']) != str(pid)]

ADMIN_PASSWORD = "matdjar123"

STORE_TEMPLATE = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;padding:15px} .card{border:1px solid #ddd;padding:10px;margin:10px 0;border-radius:8px}</style></head><body>
<h1>🛍️ متجر mat_djar</h1>
<p>{% if supabase_status %}✅ مربوط بقاعدة البيانات{% else %}⚠️ يخدم بالقائمة المؤقتة{% endif %}</p>
{% for p in products %}
<div class="card"><h3>{{ p['name'] }}</h3><p>{{ p['price'] }} دج</p><p>{{ p['description'] }}</p></div>
{% endfor %}
<a href="/admin?password=matdjar123">دخول الادارة</a>
</body></html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<h1>لوحة التحكم</h1>
<p>{% if supabase_status %}✅ Supabase يخدم - السلعة تبقى محفوظة{% else %}⚠️ انت تخدم بالقائمة - السلعة تروح كي يطفي السيرفر{% endif %}</p>
<form method="post" action="/admin/add?password={{ pwd }}">
  <input name="name" placeholder="اسم المنتج" required>
  <input name="price" type="number" placeholder="السعر" required>
  <input name="description" placeholder="الوصف">
  <button>زيد</button>
</form><hr>
{% for p in products %}
<div>{{ p['name'] }} - {{ p['price'] }} دج <a href="/admin/delete/{{ p['id'] }}?password={{ pwd }}" style="color:red">[حذف]</a></div>
{% endfor %}
<br><a href="/">رجوع للمتجر</a>
</body></html>
"""

@app.route("/")
def store():
    return render_template_string(STORE_TEMPLATE, products=get_products(), supabase_status=supabase is not None)

@app.route("/admin")
def admin():
    pwd = request.args.get("password","")
    if pwd != ADMIN_PASSWORD:
        return f'<form><input name="password" type="password" placeholder="كلمة السر"><button>دخول</button></form> جرب: {ADMIN_PASSWORD}'
    return render_template_string(ADMIN_TEMPLATE, products=get_products(), supabase_status=supabase is not None, pwd=pwd)
@app.route("/admin/add", methods=["POST"])
def add_p():
    pwd = request.args.get("password","")
    if pwd != ADMIN_PASSWORD: return "ممنوع"
    add_product_db({"name": request.form["name"], "price": int(request.form["price"]), "description": request.form.get("description","")})
    return redirect(f"/admin?password={pwd}")

@app.route("/admin/delete/<pid>")
def del_p(pid):
    pwd = request.args.get("password","")
    if pwd != ADMIN_PASSWORD: return "ممنوع"
    delete_product_db(pid)
    return redirect(f"/admin?password={pwd}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
