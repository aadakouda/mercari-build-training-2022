import os
import logging
import pathlib
import shutil
import json
import sqlite3
import hashlib
from fastapi import File, UploadFile, Body
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.DEBUG
images = pathlib.Path(__file__).parent.resolve() / "image"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
api_url = os.environ.get('API_URL', 'http://localhost:9000')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

sqlite_path = str(pathlib.Path(os.path.dirname(__file__)).parent.resolve() / "db" / "mercari.sqlite3")

def get_items_json():
    with open('items.json', 'r', encoding='utf-8') as f:
        items_json = json.load(f)
    return items_json

def get_hash_name(image):
    image_name, image_ext = map(str, image.split('.'))
    image_hashed = hashlib.sha256(image_name.encode()).hexdigest()
    return '.'.join([image_hashed, image_ext])

def save_image(image_hashed, image_file):
    with open(images / image_hashed, 'w+b') as f:
        shutil.copyfileobj(image_file.file, f)

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(
        name: str = Body(...),
        category: str = Body(...),
        image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}")
    image_hashed = get_hash_name(image.filename)
    save_image(image_hashed, image)
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id " \
        "FROM category " \
        "WHERE name = ?",
        (category, )
    )
    res = cursor.fetchall()
    if len(res) == 0:
        cursor.execute(
            "INSERT INTO category(name)" \
            "VALUES(?)",
            (category, )
        )
        conn.commit()
        cursor.execute("SELECT id FROM category WHERE name = ?", (category, ))
        res = cursor.fetchall()
    cursor.execute("INSERT INTO items(name, category_id, image) VALUES(?, ?, ?)", (name, res[0][0], image_hashed))
    conn.commit()
    conn.close()
    return {"message": f"item received: {name}"}

@app.get("/items")
def get_items_list():
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT items.id, items.name, category.name AS category, items.image "\
        "FROM items "\
        "INNER JOIN category ON items.category_id = category.id "\
    )
    sql_res = cursor.fetchall()
    result_dict = {'items': []}
    for res in sql_res:
        item = {}
        item['name'] = res['name']
        item['category'] = res['category']
        item['image'] = api_url + '/image/' + str(res['id']) + '.jpg'
        result_dict['items'].append(item)
    return result_dict

@app.get("/items/{item_id}")
def get_item(item_id):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT items.id, items.name, category.name AS category, items.image "\
        "FROM items "\
        "INNER JOIN category ON items.category_id = category.id "\
        "WHERE items.id = ?",
        (item_id,)
    )
    sql_res = cursor.fetchone()
    conn.close()
    result_dict = {}
    result_dict['name'] = sql_res['name']
    result_dict['category'] = sql_res['category']
    result_dict['image'] = api_url + '/image/' + str(sql_res['id']) + '.jpg'
    return result_dict

@app.get("/search")
def search_items(keyword: str):
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT items.name, category.name "\
        "FROM items "\
        "INNER JOIN category ON items.category_id = category.id "\
        "WHERE items.name LIKE ?",
        ('%' + keyword + '%', )
    )
    sql_res = cursor.fetchall()
    conn.close()
    result_dict = {}
    result_dict['items'] = [{'name': name, 'category': category} for name, category in sql_res]
    return result_dict

@app.get("/image/{items_jpg}")
async def get_image(items_jpg):
    if not items_jpg.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")
    image_file, image_ext = map(str, items_jpg.split('.'))
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT image "\
        "FROM items "\
        "WHERE id = ? ",
        (image_file, )
    )
    sql_res = cursor.fetchall()
    conn.close()
    if len(sql_res) == 0:
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
    else:
        image = images / sql_res[0][0]

    return FileResponse(image)
