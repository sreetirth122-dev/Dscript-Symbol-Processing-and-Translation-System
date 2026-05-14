import tkinter as tk
import json
import os

DB_FILE = os.path.join(os.getcwd(), "data", "symbol_database.json")

def load_database():
    if not os.path.exists(DB_FILE):
        return {"symbols": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def group_by_letter(db):
    grouped = {}
    for entry in db.get("symbols", []):
        letter = entry["letter"]
        grouped.setdefault(letter, []).append(entry)
    return grouped

def normalize_for_display(strokes):
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke["points"])
    if not all_points:
        return strokes
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x if max_x != min_x else 1
    height = max_y - min_y if max_y != min_y else 1
    norm_strokes = []
    for stroke in strokes:
        pts = stroke["points"]
        new_pts = []
        for x, y in pts:
            nx = (x - min_x) / width
            ny = (y - min_y) / height
            new_pts.append((nx, ny))
        norm_strokes.append({
            "points": new_pts})
    return norm_strokes

def draw_symbol(canvas, strokes, x_offset, y_offset, cell_size):
    strokes = normalize_for_display(strokes)
    padding = 10
    draw_size = cell_size - 2 * padding
    for stroke in strokes:
        pts = stroke["points"]
        if len(pts) < 2:
            continue
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            canvas.create_line(
                x_offset + padding + x1 * draw_size,
                y_offset + padding + y1 * draw_size,
                x_offset + padding + x2 * draw_size,
                y_offset + padding + y2 * draw_size,
                width=2)

def display_symbols():
    db = load_database()
    grouped = group_by_letter(db)
    root = tk.Tk()
    root.title("Dscript Symbol Viewer")
    canvas = tk.Canvas(root, width=1000, height=700, bg="white")
    canvas.pack(fill="both", expand=True)
    letters = sorted(grouped.keys())
    cols = 6
    cell_size = 150
    for idx, letter in enumerate(letters):
        row = idx // cols
        col = idx % cols
        x_offset = col * cell_size
        y_offset = row * cell_size
        canvas.create_text(
            x_offset + cell_size / 2,
            y_offset + 15,
            text=letter.upper(),
            font=("Arial", 12, "bold"))
        entry = grouped[letter][0]
        components = entry["symbol_data"]["components"]
        all_strokes = []
        for comp in components:
            all_strokes.extend(comp.get("strokes", []))
        draw_symbol(canvas, all_strokes, x_offset, y_offset + 20, cell_size)
    root.mainloop()

if __name__ == "__main__":
    display_symbols()