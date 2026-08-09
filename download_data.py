import json
import mysql.connector
import re

from config import DB_CONFIG

def parse_images(imgurls, host):
    host = host.rstrip("/")
    paths = re.findall(r"/imgs/[^/]+\.(?:jpg|jpeg|png)", imgurls, flags=re.IGNORECASE)
    return [host + p for p in paths]

JSON_PATH = "data/taipei-attractions.json"
with open(JSON_PATH, encoding="utf-8") as file:
    data = json.load(file)

conn = mysql.connector.connect(**DB_CONFIG) # ** = 將字典拆開，還原完整 DB_CONFIG 資料
cursor = conn.cursor()
cursor.execute("DELETE FROM attraction_images")
cursor.execute("DELETE FROM attractions")

attraction_sql = """
    INSERT INTO attractions
        (id, name, category, description, address, transport, mrt, lat, lng)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
image_sql = "INSERT INTO attraction_images (attraction_id, url) VALUES (%s, %s)"

for a in data["list"]:
    cursor.execute(attraction_sql, (
        a["_id"],
        a["name"],
        a["CAT"],
        a["description"],
        a["address"],
        a["direction"],
        a["MRT"] or None,
        float(a["latitude"]),
        float(a["longitude"]),
    ))
    for url in parse_images(a["imgurls"], data["img_host"]):
        cursor.execute(image_sql, (a["_id"], url))
conn.commit()
