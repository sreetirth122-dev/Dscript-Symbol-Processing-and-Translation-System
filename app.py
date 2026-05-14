import os
import tkinter as tk
import math
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
from processing import process_symbol
from database import load_database, save_database, DB_FILE
from translator import render_sentence

class SymbolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dscript System")
        self.db = load_database()
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)
        self.show_home()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Dscript System", font=("Arial", 18)).pack(pady=20)
        tk.Button(
            self.main_frame,
            text="Input Symbol Data",
            width=20,
            command=self.show_input_screen).pack(pady=10)
        tk.Button(
            self.main_frame,
            text="View Saved Data",
            width=20,
            command=self.show_viewer_screen).pack(pady=10)
        tk.Button(
            self.main_frame,
            text="Translator",
            width=20,
            command=self.show_translator_screen).pack(pady=10)

    def show_input_screen(self):
        self.clear_frame()
        tk.Button(self.main_frame, text="← Back", command=self.show_home).pack(anchor="w")
        frame = tk.Frame(self.main_frame)
        frame.pack(pady=5)
        tk.Label(frame, text="Enter Letter:").grid(row=0, column=0)
        self.letter_entry = tk.Entry(frame, width=5)
        self.letter_entry.grid(row=0, column=1)
        self.canvas = tk.Label(self.main_frame)
        self.canvas.pack(pady=10)
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Upload Image", command=self.load_image).grid(row=0, column=0)
        tk.Button(btn_frame, text="Save Mapping", command=self.save_mapping).grid(row=0, column=2)
        self.output_text = tk.Text(self.main_frame, height=20, width=80)
        self.output_text.pack()
        self.image_path = None
        self.current_data = None

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if not file_path:
            return
        self.image_path = file_path
        img = Image.open(file_path)
        img.thumbnail((300, 300))
        tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(image=tk_img)
        self.canvas.image = tk_img
        try:
            self.current_data = process_symbol(self.image_path)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, json.dumps(self.current_data, indent=2))
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")
            self.current_data = None

    def process_image(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "Upload image first")
            return
        try:
            self.current_data = process_symbol(self.image_path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, json.dumps(self.current_data, indent=2))

    def save_mapping(self):
        letter = self.letter_entry.get().strip().lower()
        if not letter:
            messagebox.showwarning("Warning", "Enter a letter!")
            return
        if not letter.isalpha():
            messagebox.showwarning("Enter English letters!")
            return
        if not self.current_data:
            messagebox.showwarning("Warning", "Process a symbol first!")
            return
        from database import generate_symbol_id, current_timestamp
        symbol_entry = {
            "id": generate_symbol_id(self.db),
            "letter": letter,
            "symbol_data": self.current_data,
            "image_path": self.image_path,
            "timestamp": current_timestamp()}
        if "symbols" not in self.db:
             self.db["symbols"] = []
        self.db["symbols"].append(symbol_entry)
        save_database(self.db)
        messagebox.showinfo("Saved", f"Symbol stored as '{letter}'")
        self.letter_entry.delete(0, tk.END)

    def clear_all(self):
        confirm = messagebox.askyesno("Confirm","This will delete ALL stored symbol mappings. Continue?")
        if confirm:
            self.db = {"symbols": []}
            save_database(self.db)
            messagebox.showinfo("Reset", "All mappings have been deleted.")
            self.show_viewer_screen()
    
    def delete_symbol(self, entry, window):
        confirm = messagebox.askyesno("Confirm","Delete this symbol permanently?")
        if not confirm:
            return
        self.db["symbols"] = [
            s for s in self.db.get("symbols", [])
            if s["id"] != entry["id"]]
        save_database(self.db)
        window.destroy()
        self.db = load_database()
        messagebox.showinfo("Deleted", "Symbol removed successfully.")
        self.show_viewer_screen()

    def show_viewer_screen(self):
        self.clear_frame()
        self.db = load_database()
        tk.Button(self.main_frame, text="← Back", command=self.show_home).pack(anchor="w")
        tk.Button(self.main_frame, text="Clear All Data", command=self.clear_all).pack(pady=5)
        container = tk.Frame(self.main_frame)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.display_symbols(scroll_frame)

    def show_enlarged(self, entry):
        top = tk.Toplevel(self.root)
        top.title("Symbol Details")
        main_frame = tk.Frame(top)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", padx=10)
        if not os.path.exists(entry["image_path"]):
            messagebox.showerror("Error", "Image file not found")
            return
        tk.Button(top, text="Delete this Symbol", command=lambda: self.delete_symbol(entry, top)).pack(pady=10)
        img = Image.open(entry["image_path"]).resize((300, 300))
        tk_img = ImageTk.PhotoImage(img)
        img_label = tk.Label(left_frame, image=tk_img)
        img_label.image = tk_img
        img_label.pack()
        tk.Label(
            left_frame,
            text=f"Letter: {entry['letter']}\nID: {entry['id']}",
            font=("Arial", 14)).pack(pady=10)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        symbol_data = entry.get("symbol_data", {})
        components = symbol_data.get("components", [])
        relations = symbol_data.get("relations", [])
        graph = symbol_data.get("graph", {})
        stats_frame = tk.LabelFrame(right_frame, text="Summary")
        stats_frame.pack(fill="x", pady=5)
        num_components = len(components)
        num_keypoints = sum(len(c.get("keypoints", [])) for c in components)
        num_strokes = sum(len(c.get("strokes", [])) for c in components)
        num_relations = len(relations)
        num_graph_nodes = len(graph.get("nodes", []))
        num_graph_edges = len(graph.get("links", []))
        tk.Label(stats_frame, text=f"Components: {num_components}").pack(anchor="w")
        tk.Label(stats_frame, text=f"Keypoints: {num_keypoints}").pack(anchor="w")
        tk.Label(stats_frame, text=f"Strokes: {num_strokes}").pack(anchor="w")
        tk.Label(stats_frame, text=f"Relations: {num_relations}").pack(anchor="w")
        tk.Label(stats_frame, text=f"Graph Nodes: {num_graph_nodes}").pack(anchor="w")
        tk.Label(stats_frame, text=f"Graph Edges: {num_graph_edges}").pack(anchor="w")
        geometry_frame = tk.LabelFrame(right_frame, text="Geometry")
        geometry_frame.pack(fill="x", pady=5)
        geometries = []
        for c in components:
            geometries.extend(c.get("geometry", []))
        tk.Label(
            geometry_frame,
            text=f"Types: {', '.join(set(geometries)) if geometries else 'None'}").pack(anchor="w")
        raw_frame = tk.LabelFrame(right_frame, text="Raw Data")
        raw_frame.pack(fill="both", expand=True, pady=5)
        text_widget = tk.Text(raw_frame, wrap="none")
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(raw_frame, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.insert("1.0", json.dumps(symbol_data, indent=2))
        text_widget.config(state="disabled")
    
    def show_translator_screen(self):
        self.clear_frame()
        tk.Button(self.main_frame, text="← Back", command=self.show_home).pack(anchor="w")
        tk.Label(self.main_frame, text="Enter Sentence:").pack(pady=5)
        self.translate_entry = tk.Entry(self.main_frame, width=60)
        self.translate_entry.pack(pady=5)
        tk.Button(
            self.main_frame,
            text="Translate",
            command=self.run_translation).pack(pady=10)
        self.translate_output = tk.Label(self.main_frame)
        self.translate_output.pack(pady=10)

    def run_translation(self):
        text = self.translate_entry.get()
        if not text:
            messagebox.showwarning("Warning", "Enter text first")
            return
        img = render_sentence(text)
        tk_img = ImageTk.PhotoImage(img)
        self.translate_output.config(image=tk_img)
        self.translate_output.image = tk_img

    def display_symbols(self, parent):
        self.db = load_database()
        symbols = self.db.get("symbols", [])
        cols = 4
        if not symbols:
            tk.Label(parent, text="No symbols stored yet").pack()
            return
        for idx, entry in enumerate(symbols):
            row = idx // cols
            col = idx % cols
            frame = tk.Frame(parent, bd=1, relief="solid", padx=5, pady=5)
            frame.grid(row=row, column=col, padx=5, pady=5)
            try:
                if not os.path.exists(entry["image_path"]):
                    tk.Label(frame, text="Image missing").pack()
                img = Image.open(entry["image_path"]).resize((100, 100))
                tk_img = ImageTk.PhotoImage(img)
                label = tk.Label(frame, image=tk_img)
                label.image = tk_img
                label.pack()
                tk.Label(frame, text=f"Letter: {entry['letter']}").pack()
                label.bind(
                    "<Button-1>",
                    lambda e, entry=entry: self.show_enlarged(entry))
            except Exception as e:
                print(e)
                tk.Label(frame, text="Image Error").pack()

#_______Main_____________
if __name__ == "__main__":
    root = tk.Tk()
    app = SymbolApp(root)
    root.mainloop()