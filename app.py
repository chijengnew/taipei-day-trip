from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import mysql.connector
from config import DB_CONFIG
app=FastAPI()
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