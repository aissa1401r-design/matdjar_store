
from flask import Flask, request, redirect
import os

app = Flask(__name__)

products = [
    {"id": 1, "name": "كسوة تقليدية", "price": "3500 دج", "emoji": "👗"},
    {"id": 2, "name": "حذاء عصري", "price": "4500 دج", "emoji": "👟"},
]

def page_html():
    cards = ""
    for p in products:
        cards += f"""
        <div style="background:white;border-radius:15px;padding:12px">
            <div style="width:100%;height:150px;background:#eee;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:50px">{p['emoji']}</div>
            <h4 style="margin-top:10px">{p['name']}</h4>
            <div style="color:#666;margin-top:5px">{p['price']}</div>
            <button style="width:100%;margin-top:10px;background:black;color:white;border:none;padding:10px;border-radius:20px">اضافة للسلة</button>
        </div>
        """
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>mat_djar</title></head>
    <body style="margin:0;background:#f5f5f5;font-family:Tahoma">
        <div style="background:white;padding:15px 20px;display:flex;justify-content:space-between;align-items:center"><h1>mat_djar 🛍️</h1><a href="/admin" style="background:black;color:white;padding:10px 18px;border-radius:25px;text-decoration:none">ادارة المتجر</a></div>
        <div style="margin:20px;background:black;color:white;border-radius:20px;padding:30px;text-align:center"><h2>مرحبا بكم</h2><p>المتجر رجع يمشي - عندنا {len(products)} منتجات</p></div>
        <div style="padding:0 20px 40px"><div style="display:grid;grid-template-columns:1fr 1fr;gap:15px">{cards}</div></div>
    </body></html>
    """

def admin_html():
    items = ""
    for p in products:
        items += f"<div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee'><span>{p['emoji']} {p['name']} - {p['price']}</span><a href='/delete/{p['id']}' style='color:red;text-decoration:none'>حذف</a></div>"
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ادارة</title></head>
    <body style="background:#f5f5f5;padding:20px;font-family:Tahoma">
        <div style="background:white;border-radius:15px;padding:20px;max-width:600px;margin:0 auto 20px">
            <h2>اضافة منتج جديد</h2>
            <form method="POST" style="margin-top:15px">
                <input name="name" placeholder="اسم المنتج" required style="width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:10px">
                <input name="price" placeholder="السعر 3500 دج" required style="width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:10px">
                <input name="emoji" placeholder="ايموجي 👗" style="width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:10px">
                <button style="background:black;color:white;padding:12px;border:none;border-radius:10px;width:100%;font-weight:bold">اضافة</button>
            </form>
        </div>
        <div style="background:white;border-radius:15px;padding:20px;max-width:600px;margin:0 auto">
            <h3>المنتجات ({len(products)})</h3>{items}
            <div style="margin-top:15px;text-align:center"><a href="/">رجوع للمتجر ←</a></div>
        </div>
    </body></html>
    """

@app.route('/')
def home(): return page_html()

@app.route('/admin', methods=['GET','POST'])
def admin():
    global products
    if request.method == 'POST':
        products.append({"id": len(products)+100, "name": request.form.get('name'), "price": request.form.get('price'), "emoji": request.form.get('emoji') or "📦"})
        return redirect('/admin')
    return admin_html()

@app.route('/delete/<int:pid>')
def delete(pid):
    global products
    products = [p for p in products if p['id'] != pid]
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port)
