from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)

# --- قائمة احتياطية اذا Supabase ما كاينش ---
# وزيد في FALLBACK_PRODUCTS رابط صورة باش تجرب:
FALLBACK_PRODUCTS = [
    {"id": 1, "name": "حذاء عصري", "price": 4500, "description": "متوفر جميع المقاسات", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"},
    {"id": 2, "name": "كسوة تقليدية", "price": 7500, "description": "صناعة تقليدية", "image_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400"},
]
"""

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
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:sans-serif;background:#f5f5f5;margin:0;padding:10px}
.header{background:white;padding:15px;text-align:center;border-radius:12px;margin-bottom:15px;box-shadow:0 2px 5px #0001}
.card{background:white;border-radius:12px;overflow:hidden;margin-bottom:15px;box-shadow:0 2px 8px #0002}
.card img{width:100%;height:220px;object-fit:cover;background:#eee}
.card-body{padding:12px}
.price{color:#00a859;font-weight:bold;font-size:18px}
.btn{display:block;background:#25D366;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;margin-top:10px;font-weight:bold}
.badge{text-align:center;padding:8px;background:#fff3cd;border-radius:8px;margin-bottom:10px}
</style></head><body>
<div class="header"><h1 style="margin:0">🛍️ mat_djar متجر</h1></div>
<div class="badge">{% if supabase_status %}✅ مربوط بقاعدة البيانات{% else %}⚠️ يخدم بالقائمة المؤقتة{% endif %}</div>
{% for p in products %}
<div class="card">
  <img src="{{ p.get('image_url') or 'https://via.placeholder.com/400x300?text=mat_djar' }}">
  <div class="card-body">
    <h3 style="margin:5px 0">{{ p['name'] }}</h3>
    <p style="color:#666;margin:5px 0">{{ p['description'] }}</p>
    <div class="price">{{ p['price'] }} دج</div>
    <a class="btn" href="https://wa.me/213XXXXXXXXX?text=سلام، حبيت نكوموندي {{ p['name'] }} - {{ p['price'] }} دج" target="_blank">📲 اطلب عبر واتساب</a>
  </div>
</div>
{% endfor %}
<div style="text-align:center;margin:20px"><a href="/admin?password=matdjar123">دخول الادارة</a></div>
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
