from flask import Flask, render_template_string, request, redirect, jsonify
import os

app = Flask(name)

FALLBACK_PRODUCTS = [
    {"id": 1, "name": "حذاء عصري", "price": 4500, "description": "متوفر", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"},
    {"id": 2, "name": "كسوة تقليدية", "price": 7500, "description": "صناعة تقليدية", "image_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400"},
]

supabase = None

def get_supabase_client():
    global supabase
    if supabase is not None:
        return supabase
    try:
        from supabase import create_client
        URL = os.environ.get("SUPABASE_URL")
        KEY = os.environ.get("SUPABASE_KEY")
        if URL and KEY and len(URL) > 10:
            supabase = create_client(URL, KEY)
            # نجربو طلب خفيف باش نتأكدو
            supabase.table("products").select("id").limit(1).execute()
            print("✅ Supabase تصلح!")
            return supabase
    except Exception as e:
        print(f"Retry failed: {e}")
        supabase = None
    return None

def get_products():
    client = get_supabase_client()
    if client:
        try:
            res = client.table("products").select("*").execute()
            return res.data if res.data else FALLBACK_PRODUCTS
        except:
            return FALLBACK_PRODUCTS
    return FALLBACK_PRODUCTS

def check_db_status():
    return get_supabase_client() is not None

# باقي الدوال add/delete كيما من قبل
def add_product_db(data):
    client = get_supabase_client()
    if client:
        try:
            client.table("products").insert(data).execute()
            return True
        except: return False
    else:
        FALLBACK_PRODUCTS.append({**data, "id": max([p['id'] for p in FALLBACK_PRODUCTS], default=0)+1})
        return True

def delete_product_db(pid):
    global FALLBACK_PRODUCTS
    client = get_supabase_client()
    if client:
        try: client.table("products").delete().eq("id", pid).execute()
        except: pass
    else:
        FALLBACK_PRODUCTS = [p for p in FALLBACK_PRODUCTS if str(p['id']) != str(pid)]

ADMIN_PASSWORD = "matdjar123"

STORE_TEMPLATE = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:sans-serif;background:#f5f5f5;margin:0;padding:10px}
.header{background:white;padding:15px;text-align:center;border-radius:12px;margin-bottom:15px}
.card{background:white;border-radius:12px;overflow:hidden;margin-bottom:15px;box-shadow:0 2px 8px #0001}
.card img{width:100%;height:220px;object-fit:cover;background:#eee}
.card-body{padding:12px}.price{color:#00a859;font-weight:bold;font-size:18px}
.btn{display:block;background:#25D366;color:white;text-align:center;padding:12px;border-radius:8px;text-decoration:none;margin-top:10px;font-weight:bold}
.alert{padding:12px;border-radius:8px;margin-bottom:15px;text-align:center}
.alert-warn{background:#fff3cd;border:1px solid #ffc107}
.alert-ok{background:#d1e7dd;border:1px solid #198754}
.btn-retry{background:#0d6efd;color:white;border:none;padding:8px 15px;border-radius:6px;margin-top:8px;cursor:pointer}
</style></head><body>
<div class="header"><h1>🛍️ mat_djar</h1></div>

<div id="status-box">
{% if supabase_status %}
<div class="alert alert-ok">✅ المتجر مربوط بقاعدة البيانات - كل المنتجات محفوظة</div>
{% else %}
<div class="alert alert-warn">
⚠️ المتجر يخدم في الوضع المؤقت<br><small>قاعدة البيانات غير متصلة حاليا</small><br>
<button class="btn-retry" onclick="retryDB()">🔄 إعادة محاولة الاتصال</button>
<div id="retry-msg" style="margin-top:8px;font-size:13px"></div>
</div>
{% endif %}
</div>

{% for p in products %}
<div class="card"><img src="{{ p.get('image_url') or 'https://via.placeholder.com/400' }}"><div class="card-body">
<h3>{{ p['name'] }}</h3><p>{{ p['description'] }}</p><div class="price">{{ p['price'] }} دج</div>
<a class="btn" href="https://wa.me/213XXXXXXXXX?text=طلب {{ p['name'] }}">اطلب واتساب</a>
</div></div>
{% endfor %}

<script>
async function retryDB(){
  document.getElementById('retry-msg').innerText = 'جاري المحاولة...';
  try{
    let res = await fetch('/api/retry-db');
    let data = await res.json();
    if(data.connected){
      document.getElementById('retry-msg').innerText = '✅ تصلحت! نعاود نحمل الصفحة...';
      setTimeout(()=> location.reload(), 1000);
    } else {
      document.getElementById('retry-msg').innerText = '❌ مازال ما كاينش، نعاود بعد 10 ثواني';
    }
  }catch(e){ document.getElementById('retry-msg').innerText = 'خطأ في الشبكة'; }
}
// محاولة تلقائية كل 15 ثانية
setInterval(retryDB, 15000);
</script>

<div style="text-align:center;margin:20px"><a href="/admin?password=matdjar123">دخول الادارة</a></div>
</body></html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<h1>لوحة التحكم</h1><p>{% if supabase_status %}✅ Supabase{% else %}⚠️ مؤقت{% endif %}</p>
<form method="post" action="/admin/add?password={{ pwd }}">
<input name="name" placeholder="اسم" required><br><br>
<input name="price" type="number" placeholder="سعر" required><br><br>
<input name="description" placeholder="وصف"><br><br>
<input name="image_url" placeholder="رابط صورة"><br><br>
<button>زيد</button></form><hr>
{% for p in products %}<div>{{ p['name'] }} <a href="/admin/delete/{{ p['id'] }}?password={{ pwd }}">[حذف]</a></div>{% endfor %}
<a href="/">رجوع</a></body></html>
"""

@app.route("/")
def store(): return render_template_string(STORE_TEMPLATE, products=get_products(), supabase_status=check_db_status())

@app.route("/api/retry-db")
def retry_db():
    connected = check_db_status()
    return jsonify({"connected": connected, "mode": "supabase" if connected else "fallback"})

@app.route("/admin")
def admin():
    pwd=request.args.get("password","")
    if pwd!=ADMIN_PASSWORD: return '<form><input name="password" type="password"><button>دخول</button></form>'
    return render_template_string(ADMIN_TEMPLATE, products=get_products(), supabase_status=check_db_status(), pwd=pwd)

@app.route("/admin/add", methods=["POST"])
def add_p():
    pwd=request.args.get("password","")
    if pwd!=ADMIN_PASSWORD: return "ممنوع"
    add_product_db({"name":request.form["name"],"price":int(request.form["price"]),"description":request.form.get("description",""),"image_url":request.form.get("image_url","")})
    return redirect(f"/admin?password={pwd}")

@app.route("/admin/delete/<pid>")
def del_p(pid):
    pwd=request.args.get("password","")
    if pwd!=ADMIN_PASSWORD: return "ممنوع"
    delete_product_db(pid)
    return redirect(f"/admin?password={pwd}")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
