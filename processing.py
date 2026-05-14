import compression
import cv2 
import numpy as np 
from skimage.morphology import skeletonize 
import networkx as nx 

def preprocess_image(image_path): 
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) 
    if img is None: 
        raise ValueError("Invalid image path")
    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV) 
    return thresh 
    
def get_components(binary_img, min_size=30, merge_threshold=15): 
    num_labels, labels = cv2.connectedComponents(binary_img) 
    raw_components = [] 
    for label in range(1, num_labels): 
        mask = np.uint8(labels == label) * 255
        if cv2.countNonZero(mask) < min_size:
            continue 
        raw_components.append(mask) 
    merged = []
    used = [False] * len(raw_components)
    for i in range(len(raw_components)):
        if used[i]:
            continue
        base = raw_components[i].copy()
        used[i] = True
        x1, y1, w1, h1 = cv2.boundingRect(base)
        for j in range(i+1, len(raw_components)):
            if used[j]:
                continue
            x2, y2, w2, h2 = cv2.boundingRect(raw_components[j])
            close_x = abs(x1 - x2) < merge_threshold
            close_y = abs(y1 - y2) < merge_threshold
            if close_x and close_y:
                base = cv2.bitwise_or(base, raw_components[j])
                used[j] = True
                x1, y1, w1, h1 = cv2.boundingRect(base)
        merged.append(base)
    return merged

def extract_contours(component): 
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
    return contours 

def get_skeleton(component):
    binary = component // 255 
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    skeleton = skeletonize(binary) 
    return skeleton.astype(np.uint8) 

def get_neighbors(skeleton, x, y): 
    neighbors = [] 
    h, w = skeleton.shape 
    for dy in [-1, 0, 1]: 
        for dx in [-1, 0, 1]: 
            if dx == 0 and dy == 0: 
                continue 
            nx, ny = x + dx, y + dy 
            if 0 <= nx < w and 0 <= ny < h: 
                if skeleton[ny, nx] == 1: 
                    neighbors.append((nx, ny)) 
    return neighbors 

def detect_keypoints(skeleton): 
    keypoints = [] 
    h, w = skeleton.shape 
    for y in range(1, h-1): 
        for x in range(1, w-1): 
            if skeleton[y, x] == 1: 
                neighbors = get_neighbors(skeleton, x, y) 
                if len(neighbors) == 1: 
                    keypoints.append(("endpoint", (x, y))) 
                elif len(neighbors) > 2: 
                    keypoints.append(("junction", (x, y))) 
    return keypoints 

def compute_stroke_features(points):
    if len(points) < 3:
        return {
            "num_corners": 0,
            "corner_angles": [],
            "is_straight": True}
    directions = []
    for i in range(1, len(points)):
        x1, y1 = points[i-1]
        x2, y2 = points[i]
        dx, dy = x2 - x1, y2 - y1
        norm = np.hypot(dx, dy)
        if norm == 0:
            continue
        directions.append((dx/norm, dy/norm))
    corner_angles = []
    for i in range(1, len(directions)):
        v1 = np.array(directions[i-1])
        v2 = np.array(directions[i])
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angle = np.degrees(np.arccos(dot))
        if angle > 25:
            corner_angles.append(angle)
    num_corners = len(corner_angles)
    return {
        "num_corners": num_corners,
        "corner_angles": corner_angles,
        "is_straight": num_corners == 0}

def extract_strokes(skeleton, keypoints):
    visited_edges = set()
    strokes = []
    keypoint_coords = set(coord for _, coord in keypoints)
    if len(keypoints) == 0:
        coords = set((x, y) for y, x in np.argwhere(skeleton == 1))
        start = min(coords)
        path = [start]
        visited = {start}
        current = start
        prev = None
        while True:
            neighbors = get_neighbors(skeleton, current[0], current[1])
            if prev and prev in neighbors:
                neighbors.remove(prev)
            next_candidates = [n for n in neighbors if n not in visited]
            if not next_candidates:
                break
            next_pt = next_candidates[0]
            path.append(next_pt)
            visited.add(next_pt)
            prev = current
            current = next_pt
        features = compute_stroke_features(path)
        return [{
            "points": path,
            "length": len(path),
            "num_corners": features["num_corners"],
            "corner_angles": features["corner_angles"],
            "is_straight": features["is_straight"],
            "is_loop": True}]
    def trace_edge(start, next_pt):
        path = [start, next_pt]
        current = next_pt
        prev = start
        while True:
            edge=(prev, current)
            rev_edge = (current, prev)
            visited_edges.add(edge)
            visited_edges.add(rev_edge)
            if current in keypoint_coords and current != start:
                break
            neighbors = get_neighbors(skeleton, current[0], current[1])
            if prev in neighbors:
                neighbors.remove(prev)
            if not neighbors:
                break
            next_candidates = [n for n in neighbors 
                               if (current, n) not in visited_edges]
            if next_candidates:
                next_step = next_candidates[0]
            else:
                break
            path.append(next_step)
            prev = current
            current = next_step
        return path    
    for _, kp in keypoints:
        neighbors = get_neighbors(skeleton, kp[0], kp[1])
        for n in neighbors:
            edge = (kp, n)
            if edge in visited_edges:
                continue
            path = trace_edge(kp, n)
            if len(path) > 1:
                features = compute_stroke_features(path)
                strokes.append({
                    "points": path,
                    "length": len(path),
                    "num_corners": features["num_corners"],
                    "corner_angles": features["corner_angles"],
                    "is_straight": features["is_straight"],
                    "is_loop": False})
    all_pixels = set((x, y) for y, x in np.argwhere(skeleton == 1))
    for p in all_pixels:
        neighbors = get_neighbors(skeleton, p[0], p[1])
        for n in neighbors:
            edge = (p, n)
            if edge in visited_edges:
                continue
            path = trace_edge(p, n)
            if len(path) > 1:
                features = compute_stroke_features(path)
                strokes.append({
                    "points": path,
                    "length": len(path),
                    "num_corners": features["num_corners"],
                    "corner_angles": features["corner_angles"],
                    "is_straight": features["is_straight"],
                    "is_loop": False})
    return strokes

def build_graph(keypoints, strokes): 
    G = nx.Graph() 
    kp_index = {coord: i for i, (_, coord) in enumerate(keypoints)} 
    for idx, (ptype, coord) in enumerate(keypoints): 
        G.add_node(idx, type=ptype, pos=coord) 
    for stroke in strokes: 
        points = stroke["points"] 
        stroke_kps = [pt for pt in points if pt in kp_index] 
        for i in range(len(stroke_kps)-1): 
            a = kp_index[stroke_kps[i]] 
            b = kp_index[stroke_kps[i+1]] 
            G.add_edge(a, b, weight=stroke["length"], corners=stroke["num_corners"]) 
    return G 

def compute_spatial_relations(components):
    relations = []
    for i in range(len(components)):
        for j in range(i+1, len(components)):
            x1, y1, w1, h1 = cv2.boundingRect(components[i])
            x2, y2, w2, h2 = cv2.boundingRect(components[j])
            if y1 < y2:
                relations.append((i, j, "above"))
            elif y1 > y2:
                relations.append((i, j, "below"))
            if x1 < x2:
                relations.append((i, j, "left"))
            elif x1 > x2:
                relations.append((i, j, "right"))
    return relations

def normalize_symbol(keypoints, strokes):
    all_points = []
    for _, (x, y) in keypoints:
        all_points.append((x, y))
    for stroke in strokes:
        all_points.extend(stroke["points"])
    if not all_points:
        return keypoints, strokes
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y
    scale = max(width, height)
    if scale == 0:
        scale = 1
    compression_factor = 0.6
    if height > width:
        scale_y = scale
        scale_x = scale
        compress_y = compression_factor
        compress_x = 1.0
    else:
        scale_x = scale
        scale_y = scale
        compress_x = compression_factor
        compress_y = 1.0
    norm_keypoints = []
    for t, (x, y) in keypoints:
        nx = ((x - min_x) / scale_x) * compress_x
        ny = ((y - min_y) / scale_y) * compress_y
        norm_keypoints.append((t, (nx, ny)))
    norm_strokes = []
    for stroke in strokes:
        new_points = []
        for x, y in stroke["points"]:
            nx = ((x - min_x) / scale_x) * compress_x
            ny = ((y - min_y) / scale_y) * compress_y
            new_points.append((nx, ny))
        norm_strokes.append({
            "points": new_points,
            "length": len(new_points),
            "num_corners": stroke.get("num_corners", 0),
            "corner_angles": stroke.get("corner_angles", []),
            "is_straight": stroke.get("is_straight", False),
            "is_loop": stroke.get("is_loop", False)})
    return norm_keypoints, norm_strokes

def process_symbol(image_path): 
    binary = preprocess_image(image_path) 
    components = get_components(binary) 
    symbol_data = {"components": [], "relations": []} 
    all_keypoints = [] 
    all_strokes = []
    for idx, comp in enumerate(components): 
        skeleton = get_skeleton(comp) 
        keypoints = detect_keypoints(skeleton) 
        num_junctions = sum(1 for t, _ in keypoints if t == "junction")
        num_endpoints = sum(1 for t, _ in keypoints if t == "endpoint")
        strokes = extract_strokes(skeleton, keypoints)
        all_keypoints.extend(keypoints)
        all_strokes.extend(strokes)
        component_data = { 
            "id": idx, 
            "keypoints": keypoints, 
            "strokes": strokes,
            "structure": {
                "junctions": num_junctions,
                "endpoints": num_endpoints}, 
            "geometry": {
                "num_strokes": len(strokes),
                "total_corners": sum(s["num_corners"] for s in strokes),
                "has_loop": any(s.get("is_loop", False) for s in strokes)}} 
        symbol_data["components"].append(component_data) 
    all_keypoints, all_strokes = normalize_symbol(all_keypoints, all_strokes)
    stroke_idx = 0
    for comp in symbol_data["components"]:
        num = len(comp["strokes"])
        comp["strokes"] = all_strokes[stroke_idx:stroke_idx + num]
        stroke_idx += num
    graph = build_graph(all_keypoints, all_strokes)
    symbol_data["graph"] = nx.node_link_data(graph) 
    symbol_data["relations"] = compute_spatial_relations(components) 
    return symbol_data