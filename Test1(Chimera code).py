import cv2
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os

# 1. PREPROCESSING

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    return thresh

# 2. CONNECTED COMPONENTS

def get_components(binary_img):
    num_labels, labels = cv2.connectedComponents(binary_img)
    components = []

    for label in range(1, num_labels):  # skip background
        mask = np.uint8(labels == label) * 255
        components.append(mask)

    return components

# 3. CONTOUR EXTRACTION

def extract_contours(component):
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours

# 4. SKELETONIZATION

def get_skeleton(component):
    binary = component // 255
    skeleton = skeletonize(binary)
    return skeleton.astype(np.uint8)

# 5. KEYPOINT DETECTION

def detect_keypoints(skeleton):
    keypoints = []
    h, w = skeleton.shape

    for y in range(1, h-1):
        for x in range(1, w-1):
            if skeleton[y, x] == 1:
                neighbors = np.sum(skeleton[y-1:y+2, x-1:x+2]) - 1

                if neighbors == 1:
                    keypoints.append(("endpoint", (x, y)))
                elif neighbors > 2:
                    keypoints.append(("junction", (x, y)))

    return keypoints

# 6. STROKE EXTRACTION

def extract_strokes(skeleton):
    points = np.argwhere(skeleton == 1)
    return [(int(x), int(y)) for y, x in points]

# 7. GEOMETRY CLASSIFICATION

def classify_geometry(contour):
    contour = contour.reshape(-1, 2)

    # Fit line
    [vx, vy, x, y] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)

    # Compute deviation
    distances = []
    for pt in contour:
        px, py = pt
        dist = abs(vy*(px-x) - vx*(py-y))
        distances.append(dist)

    if np.mean(distances) < 2:
        return "line"
    else:
        return "curve"

# 8. BUILD GRAPH REPRESENTATION

def build_graph(keypoints, strokes):
    G = nx.Graph()

    # Add nodes
    for idx, (ptype, coord) in enumerate(keypoints):
        G.add_node(idx, type=ptype, pos=coord)

    # Connect nodes based on proximity
    for i in range(len(keypoints)):
        for j in range(i+1, len(keypoints)):
            p1 = np.array(keypoints[i][1])
            p2 = np.array(keypoints[j][1])
            dist = np.linalg.norm(p1 - p2)

            if dist < 20:  # threshold (tune this)
                G.add_edge(i, j, weight=dist)

    return G

# 9. SPATIAL RELATIONS

def compute_spatial_relations(components):
    relations = []

    for i in range(len(components)):
        for j in range(i+1, len(components)):
            c1 = cv2.boundingRect(components[i])
            c2 = cv2.boundingRect(components[j])

            x1, y1, w1, h1 = c1
            x2, y2, w2, h2 = c2

            if y1 < y2:
                relations.append((i, j, "above"))
            elif y1 > y2:
                relations.append((i, j, "below"))

            if x1 < x2:
                relations.append((i, j, "left"))
            elif x1 > x2:
                relations.append((i, j, "right"))

    return relations

# 10. MAIN PIPELINE

def process_symbol(image_path):
    binary = preprocess_image(image_path)
    components = get_components(binary)

    symbol_data = {
        "components": [],
        "relations": []
    }

    all_keypoints = []
    all_strokes = []

    for idx, comp in enumerate(components):
        contours = extract_contours(comp)
        skeleton = get_skeleton(comp)
        keypoints = detect_keypoints(skeleton)
        strokes = extract_strokes(skeleton)

        geometry = []
        for contour in contours:
            geom_type = classify_geometry(contour)
            geometry.append(geom_type)

        component_data = {
            "id": idx,
            "keypoints": keypoints,
            "strokes": strokes,
            "geometry": geometry
        }

        symbol_data["components"].append(component_data)

        all_keypoints.extend(keypoints)
        all_strokes.extend(strokes)

    # Graph representation
    graph = build_graph(all_keypoints, all_strokes)
    symbol_data["graph"] = nx.node_link_data(graph)

    # Spatial relations
    relations = compute_spatial_relations(components)
    symbol_data["relations"] = relations

    return symbol_data



#___________________________________App and GUI part__________________________

    # from your script import process symbol

DB_FOLDER = r"D:\Github\Dscript"
DB_FILE = os.path.join(DB_FOLDER, "symbol_database.json")

# Ensure folder exists
os.makedirs(DB_FOLDER, exist_ok=True)

# -------------------------------
# DATABASE FUNCTIONS
# -------------------------------
def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_database(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


# -------------------------------
# GUI CLASS
# -------------------------------
class SymbolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dscript Symbol Mapper")

        self.db = load_database()

        # -------------------------------
        # LETTER INPUT
        # -------------------------------
        input_frame = tk.Frame(root)
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Enter Letter:").grid(row=0, column=0)
        self.letter_entry = tk.Entry(input_frame, width=5)
        self.letter_entry.grid(row=0, column=1)

        # -------------------------------
        # IMAGE DISPLAY
        # -------------------------------
        self.canvas = tk.Label(root)
        self.canvas.pack(pady=10)

        # -------------------------------
        # BUTTONS
        # -------------------------------
        btn_frame = tk.Frame(root)
        btn_frame.pack()

        tk.Button(btn_frame, text="Upload Image", command=self.load_image).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Process Symbol", command=self.process_image).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Save Mapping", command=self.save_mapping).grid(row=0, column=2, padx=5)

        # NEW CLEAR BUTTONS
        tk.Button(btn_frame, text="Clear Image", command=self.clear_image).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all).grid(row=0, column=4, padx=5)

        # -------------------------------
        # OUTPUT BOX
        # -------------------------------
        self.output_text = tk.Text(root, height=20, width=80)
        self.output_text.pack(pady=10)

        self.image_path = None
        self.current_data = None

    # -------------------------------
    # LOAD IMAGE
    # -------------------------------
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )

        if file_path:
            self.image_path = file_path

            img = Image.open(file_path)
            img = img.resize((300, 300))
            self.tk_img = ImageTk.PhotoImage(img)

            self.canvas.config(image=self.tk_img)

    # -------------------------------
    # PROCESS IMAGE
    # -------------------------------
    def process_image(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "Upload an image first!")
            return

        try:
            self.current_data = process_symbol(self.image_path)

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, json.dumps(self.current_data, indent=2))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------------
    # SAVE MAPPING
    # -------------------------------
    def save_mapping(self):
        letter = self.letter_entry.get().strip().lower()

        if not letter:
            messagebox.showwarning("Warning", "Enter a letter!")
            return

        if len(letter) != 1 or not letter.isalpha():
            messagebox.showwarning("Warning", "Enter a single English letter!")
            return

        if not self.current_data:
            messagebox.showwarning("Warning", "Process a symbol first!")
            return

        if letter not in self.db:
            self.db[letter] = []

        self.db[letter].append({
            "symbol_data": self.current_data,
            "image_path": self.image_path
        })

        save_database(self.db)

        messagebox.showinfo("Success", f"Symbol mapped to '{letter}' successfully!")

        self.letter_entry.delete(0, tk.END)

    # -------------------------------
    # CLEAR CURRENT IMAGE ONLY
    # -------------------------------
    def clear_image(self):
        self.image_path = None
        self.current_data = None

        self.canvas.config(image="")
        self.output_text.delete(1.0, tk.END)

        messagebox.showinfo("Cleared", "Current image and data cleared.")

    # -------------------------------
    # CLEAR ENTIRE DATABASE
    # -------------------------------
    def clear_all(self):
        confirm = messagebox.askyesno(
            "Confirm",
            "This will delete ALL stored symbol mappings. Continue?"
        )

        if confirm:
            self.db = {}

            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)

            self.clear_image()

            messagebox.showinfo("Reset", "All mappings have been deleted.")


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SymbolApp(root)
    root.mainloop()