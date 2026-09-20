from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import mysql.connector
import jwt
import requests
import secrets
import contextlib
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings
from config import (
    DB_CONFIG, JWT_KEY, JWT_ALGORITHM,
    TAPPAY_PARTNER_KEY, TAPPAY_MERCHANT_ID, TAPPAY_PAY_BY_PRIME_URL,
    BOOKING_PAGE_URL,
    )
@contextlib.asynccontextmanager
async def app_lifespan(app):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

app = FastAPI(lifespan=app_lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")

PAGE_SIZE = 8

@app.get("/member", include_in_schema=False)
async def member(request: Request):
    return FileResponse("./static/member.html", media_type="text/html")

@app.get("/api/attractions")
async def get_attractions(page: int, keyword: str = None, category: str = None):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        if keyword:
            conditions.append("(mrt = %s OR name LIKE %s)")
            params.append(keyword)
            params.append(f"%{keyword}%")

        if category:
            conditions.append("category = %s")
            params.append(category)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT id, name, category, description, address, transport, mrt, lat, lng
            FROM attractions
            {where}
            ORDER BY id
            LIMIT %s OFFSET %s
        """

        params.append(PAGE_SIZE + 1)
        params.append(page * PAGE_SIZE)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        has_next = len(rows) > PAGE_SIZE
        rows = rows[:PAGE_SIZE]

        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"SELECT attraction_id, url FROM attraction_images WHERE attraction_id IN ({placeholders}) ORDER BY id",
                ids,
                )
            images_by_id = {}
            for ir in cursor.fetchall():
                images_by_id.setdefault(ir["attraction_id"], []).append(ir["url"])
            for r in rows:
                r["images"] = images_by_id.get(r["id"], [])

        cursor.close()
        conn.close()

        return {
            "nextPage": page + 1 if has_next else None,
            "data": rows,
            }

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
            )
      
@app.get("/api/attraction/{attractionId}")
async def get_attraction_by_id(attractionId: int):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, category, description, address, transport, mrt, lat, lng "
            "FROM attractions WHERE id = %s",
            (attractionId,),
            )
        row = cursor.fetchone()

        if row is None:
            cursor.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "data incorrect"},
                )

        cursor.execute(
            "SELECT url FROM attraction_images WHERE attraction_id = %s ORDER BY id",
            (attractionId,),
            )
        row["images"] = [r["url"] for r in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {"data": row}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
            )

@app.get("/api/categories")
async def get_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT DISTINCT category FROM attractions ORDER BY category")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        categories = [row["category"] for row in rows]

        return {"data": categories}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
            )

@app.get("/api/mrts")
async def get_mrts():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT mrt
            FROM attractions
            WHERE mrt IS NOT NULL
            GROUP BY mrt
            ORDER BY COUNT(*) DESC
        """)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        mrts = [row["mrt"] for row in rows]

        return {"data": mrts}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
            )

class SignUpForm(BaseModel):
    name: str
    email: str
    password: str

class SignInForm(BaseModel):
    email: str
    password: str

def create_token(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_KEY, algorithm=JWT_ALGORITHM)

def verify_token(request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None

def generate_mcp_token():
    return secrets.token_hex(32)

def get_member_id_by_mcp_token(token):
    if not token:
        return None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT member_id FROM mcp_token WHERE token = %s", (token,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row["member_id"] if row else None
    except Exception:
        return None

@app.post("/api/user")
async def sign_up(form: SignUpForm):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM member WHERE email = %s", (form.email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Email already in use. Please log in instead."},
            )

        cursor.execute(
            "INSERT INTO member (name, email, password) VALUES (%s, %s, %s)",
            (form.name, form.email, form.password),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"ok": True}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.get("/api/user/auth")
async def get_current_user(request: Request):
    payload = verify_token(request)
    if payload is None:
        return {"data": None}
    return {
        "data": {
            "id": payload["id"],
            "name": payload["name"],
            "email": payload["email"],
        }
    }

@app.put("/api/user/auth")
async def sign_in(form: SignInForm):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email FROM member WHERE email = %s AND password = %s",
            (form.email, form.password),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user is None:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Incorrect email or password. Please try again."},
            )

        return {"token": create_token(user)}

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.get("/api/member/token")
async def get_member_mcp_token(request: Request):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT token FROM mcp_token WHERE member_id = %s",
            (payload["id"],),
        )
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return {"data": {"token": row["token"]} if row else None}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.post("/api/member/token")
async def create_member_mcp_token(request: Request):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        token = generate_mcp_token()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO mcp_token (member_id, token)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                token      = VALUES(token),
                created_at = CURRENT_TIMESTAMP
            """,
            (payload["id"], token),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"data": {"token": token}}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

class BookingForm(BaseModel):
    attractionId: int
    date: str
    time: str
    price: int

class OrderContact(BaseModel):
    name: str
    email: str
    phone: str

class OrderAttraction(BaseModel):
    id: int
    name: str
    address: str
    image: str

class OrderTrip(BaseModel):
    attraction: OrderAttraction
    date: str
    time: str

class OrderData(BaseModel):
    price: int
    trip: OrderTrip
    contact: OrderContact

class OrderForm(BaseModel):
    prime: str
    order: OrderData

@app.get("/api/booking")
async def get_booking(request: Request):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                a.id      AS attraction_id,
                a.name    AS attraction_name,
                a.address AS attraction_address,
                b.date    AS date,
                b.time    AS time,
                b.price   AS price
            FROM booking AS b
            JOIN attractions AS a ON a.id = b.attraction_id
            WHERE b.member_id = %s
            """,
            (payload["id"],),
        )
        row = cursor.fetchone()

        if row is None:
            cursor.close()
            conn.close()
            return {"data": None}

        cursor.execute(
            "SELECT url FROM attraction_images WHERE attraction_id = %s ORDER BY id LIMIT 1",
            (row["attraction_id"],),
        )
        image_row = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "data": {
                "attraction": {
                    "id": row["attraction_id"],
                    "name": row["attraction_name"],
                    "address": row["attraction_address"],
                    "image": image_row["url"] if image_row else None,
                },
                "date": row["date"].isoformat(),
                "time": row["time"],
                "price": row["price"],
            }
        }
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.post("/api/booking")
async def create_booking(request: Request, form: BookingForm):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO booking (member_id, attraction_id, date, time, price)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                attraction_id = VALUES(attraction_id),
                date          = VALUES(date),
                time          = VALUES(time),
                price         = VALUES(price)
            """,
            (payload["id"], form.attractionId, form.date, form.time, form.price),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"ok": True}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.delete("/api/booking")
async def delete_booking(request: Request):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM booking WHERE member_id = %s", (payload["id"],))
        conn.commit()
        cursor.close()
        conn.close()

        return {"ok": True}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.post("/api/orders")
async def create_order(request: Request, form: OrderForm):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        order_number = datetime.now().strftime("%Y%m%d%H%M%S") + str(payload["id"])
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO orders
                (number, member_id, attraction_id, date, time, price,
                 contact_name, contact_email, contact_phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'UNPAID')
            """,
            (
                order_number, payload["id"], form.order.trip.attraction.id,
                form.order.trip.date, form.order.trip.time, form.order.price,
                form.order.contact.name, form.order.contact.email, form.order.contact.phone,
            ),
        )
        order_id = cursor.lastrowid
        conn.commit()


        tappay_res = requests.post(
            TAPPAY_PAY_BY_PRIME_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": TAPPAY_PARTNER_KEY,
            },
            json={
                "prime": form.prime,
                "partner_key": TAPPAY_PARTNER_KEY,
                "merchant_id": TAPPAY_MERCHANT_ID,
                "amount": form.order.price,
                "details": "台北一日遊：" + form.order.trip.attraction.name,
                "cardholder": {
                    "phone_number": form.order.contact.phone,
                    "name": form.order.contact.name,
                    "email": form.order.contact.email,
                },
            },
            timeout=30,
        ).json()

        pay_status = tappay_res.get("status")
        pay_msg = tappay_res.get("msg", "")


        cursor.execute(
            """
            INSERT INTO payment
                (order_id, rec_trade_id, bank_transaction_id, status, msg, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                tappay_res.get("rec_trade_id"),
                tappay_res.get("bank_transaction_id"),
                pay_status, pay_msg, form.order.price,
            ),
        )

        if pay_status == 0:
            cursor.execute("UPDATE orders SET status = 'PAID' WHERE id = %s", (order_id,))
            cursor.execute("DELETE FROM booking WHERE member_id = %s", (payload["id"],))
            message = "付款成功"
        else:
            message = "付款失敗：" + pay_msg

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "data": {
                "number": order_number,
                "payment": {"status": pay_status, "message": message},
            }
        }
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

@app.get("/api/order/{orderNumber}")
async def get_order(request: Request, orderNumber: str):
    payload = verify_token(request)
    if payload is None:
        return JSONResponse(
            status_code=403,
            content={"error": True, "message": "Access denied. Please log in."},
        )
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                o.number        AS number,
                o.date          AS date,
                o.time          AS time,
                o.price         AS price,
                o.status        AS status,
                o.contact_name  AS contact_name,
                o.contact_email AS contact_email,
                o.contact_phone AS contact_phone,
                a.id            AS attraction_id,
                a.name          AS attraction_name,
                a.address       AS attraction_address
            FROM orders AS o
            JOIN attractions AS a ON a.id = o.attraction_id
            WHERE o.number = %s AND o.member_id = %s
            """,
            (orderNumber, payload["id"]),
        )
        row = cursor.fetchone()

        if row is None:
            cursor.close()
            conn.close()
            return {"data": None}

        cursor.execute(
            "SELECT url FROM attraction_images WHERE attraction_id = %s ORDER BY id LIMIT 1",
            (row["attraction_id"],),
        )
        image_row = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "data": {
                "number": row["number"],
                "price": row["price"],
                "status": row["status"],
                "trip": {
                    "attraction": {
                        "id": row["attraction_id"],
                        "name": row["attraction_name"],
                        "address": row["attraction_address"],
                        "image": image_row["url"] if image_row else None,
                    },
                    "date": row["date"].isoformat(),
                    "time": row["time"],
                },
                "contact": {
                    "name": row["contact_name"],
                    "email": row["contact_email"],
                    "phone": row["contact_phone"],
                },
            }
        }
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "server errors"},
        )

mcp = FastMCP(
    "台北一日遊",
    streamable_http_path="/",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)

def _search_attractions(keyword):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, name, description
        FROM attractions
        WHERE mrt = %s OR name LIKE %s
        ORDER BY id
        """,
        (keyword, f"%{keyword}%"),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def _create_booking_for_member(member_id, attraction_id, date, time, price):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO booking (member_id, attraction_id, date, time, price)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            attraction_id = VALUES(attraction_id),
            date          = VALUES(date),
            time          = VALUES(time),
            price         = VALUES(price)
        """,
        (member_id, attraction_id, date, time, price),
    )
    conn.commit()
    cursor.close()
    conn.close()

@mcp.tool(name="search_attractions", title="搜尋台北市景點", description="透過關鍵字和捷運站名搜尋台北市一日旅遊的景點")
def search_attractions(keyword: str) -> dict:
    try:
        rows = _search_attractions(keyword)
        return {
            "data": [
                {"id": r["id"], "name": r["name"], "description": r["description"]}
                for r in rows
            ]
        }
    except Exception:
        return {"error": True}

@mcp.tool(name="add_to_cart", title="預定景點導覽行程", description="根據景點編號、日期、時間、價格，預定一個景點導覽行程")
def add_to_cart(attraction_id: int, date: str, time: str, price: int, ctx: Context) -> dict:
    try:
        request = ctx.request_context.request
        auth = request.headers.get("authorization", "") if request else ""
        if not auth.startswith("Bearer "):
            return {"error": True}
        token = auth[len("Bearer "):].strip()

        member_id = get_member_id_by_mcp_token(token)
        if member_id is None:
            return {"error": True}

        if time not in ("morning", "afternoon"):
            return {"error": True}

        _create_booking_for_member(member_id, attraction_id, date, time, price)

        return {
            "ok": True,
            "message": f"台北導覽行程，預定成功，請到 {BOOKING_PAGE_URL} 完成付款。",
        }
    except Exception:
        return {"error": True}

app.mount("/mcp", mcp.streamable_http_app())