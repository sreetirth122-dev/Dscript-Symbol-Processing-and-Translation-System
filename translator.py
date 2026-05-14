import json
import os
from PIL import Image, ImageDraw
DB_FILE = os.path.join(os.getcwd(), "data", "symbol_database.json")

def load_database():
    if not os.path.exists(DB_FILE):
        return {"symbols": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def build_symbol_map(db):
    mapping = {}
    for entry in db.get("symbols", []):
        letter = entry["letter"]
        components = entry["symbol_data"]["components"]
        strokes = []
        for comp in components:
            strokes.extend(comp.get("strokes", []))
        mapping[letter] = strokes
    return mapping

def draw_symbol(draw, strokes, x_offset, y_offset, size=40):
    all_points = []
    for s in strokes:
        all_points.extend(s["points"])
    if not all_points:
        return size
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x if max_x != min_x else 1
    height = max_y - min_y if max_y != min_y else 1
    for stroke in strokes:
        pts = stroke["points"]
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            nx1 = (x1 - min_x) / width
            ny1 = (y1 - min_y) / height
            nx2 = (x2 - min_x) / width
            ny2 = (y2 - min_y) / height
            draw.line((
                    x_offset + nx1 * size,
                    y_offset + ny1 * size,
                    x_offset + nx2 * size,
                    y_offset + ny2 * size,),
                fill="black",
                width=2)
    return size

def render_sentence(text):
    db = load_database()
    symbol_map = build_symbol_map(db)
    char_width = 45
    char_height = 50
    width = len(text) * char_width + 20
    height = char_height + 20
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    x_cursor = 10
    for char in text:
        lower = char.lower()
        if lower in symbol_map:
            draw_symbol(draw, symbol_map[lower], x_cursor, 10, size=35)
            x_cursor += char_width
        elif char == " ":
            x_cursor += char_width // 2
        else:
            draw.text((x_cursor, 10), char, fill="black")
            x_cursor += char_width // 2
    return img