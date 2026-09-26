from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import sqlite3
import razorpay

app = FastAPI()

conn = sqlite3.connect('ecommerce_demo.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        amount INTEGER,
        status TEXT,
        gateway_order_id TEXT
    )
''')
conn.commit()

razorpay_client = razorpay.Client(auth=("YOUR_TEST_KEY", "YOUR_TEST_SECRET"))

@app.get("/")
async def serve_frontend():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/checkout")
async def checkout():
    cursor.execute("INSERT INTO orders (item_name, amount, status) VALUES ('Test Book', 500, 'PENDING')")
    db_id = cursor.lastrowid
    
    payment_order = razorpay_client.orders.create({
        "amount": 50000, 
        "currency": "INR",
        "receipt": f"receipt_{db_id}"
    })
    
    cursor.execute("UPDATE orders SET gateway_order_id = ? WHERE id = ?", (payment_order['id'], db_id))
    conn.commit()
    
    return {"gateway_order_id": payment_order['id'], "amount": 50000}

@app.post("/webhook")
async def fake_webhook(request: Request):
    data = await request.json()
    
    if data.get("event") == "payment.captured":
        gateway_order_id = data['payload']['payment']['entity']['order_id']
        cursor.execute("UPDATE orders SET status = 'PAID' WHERE gateway_order_id = ?", (gateway_order_id,))
        conn.commit()
        
    return {"status": "ok"}
  
