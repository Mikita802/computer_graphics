import tkinter as tk
from math import isclose

# ---------- ВХОДНЫЕ ДАННЫЕ ----------
# Вариант 1: прямоугольник → оба алгоритма
INPUT_DATA = """
4
10 10 100 50
20 80 120 30
50 50 150 100
30 20 90 70
4
40 40
100 40
100 100
40 100
# """

# Вариант 2: выпуклый многоугольник → только Кирус–Бек
#INPUT_DATA = """
#2
#0 0 120 120
#20 100 100 20
#5
#30 30
#90 30
#110 60
#80 100
#40 90
#"""
# ------------------------------------

def parse_input(data):
    lines = [line.strip() for line in data.strip().splitlines() if line.strip()]
    n = int(lines[0])
    segments = []
    idx = 1
    for _ in range(n):
        x1, y1, x2, y2 = map(float, lines[idx].split())
        segments.append(((x1, y1), (x2, y2)))
        idx += 1

    tokens = lines[idx].split()
    if len(tokens) == 4:
        xmin, ymin, xmax, ymax = map(float, tokens)
        if xmin > xmax: xmin, xmax = xmax, xmin
        if ymin > ymax: ymin, ymax = ymax, ymin
        rect = (xmin, ymin, xmax, ymax)
        rect_poly = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        return segments, rect, rect_poly
    elif len(tokens) == 1:
        m = int(tokens[0])
        poly = []
        for i in range(1, m + 1):
            x, y = map(float, lines[idx + i].split())
            poly.append((x, y))
        return segments, None, poly
    else:
        raise ValueError("Формат: после отрезков либо 4 числа (прямоугольник), либо m и m вершин")

INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

def compute_code(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin: code |= LEFT
    elif x > xmax: code |= RIGHT
    if y < ymin: code |= BOTTOM
    elif y > ymax: code |= TOP
    return code

def cohen_sutherland_clip(segment, rect):
    (x0, y0), (x1, y1) = segment
    xmin, ymin, xmax, ymax = rect
    code0 = compute_code(x0, y0, xmin, ymin, xmax, ymax)
    code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)

    while True:
        if not (code0 | code1):
            return ((x0, y0), (x1, y1))
        elif code0 & code1:
            return None
        else:
            outcode = code0 if code0 != INSIDE else code1
            if outcode & TOP:
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
                y = ymax
            elif outcode & BOTTOM:
                x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
                y = ymin
            elif outcode & RIGHT:
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
                x = xmax
            elif outcode & LEFT:
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
                x = xmin

            if outcode == code0:
                x0, y0 = x, y
                code0 = compute_code(x0, y0, xmin, ymin, xmax, ymax)
            else:
                x1, y1 = x, y
                code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)

def cyrus_beck_clip(segment, poly):
    p1, p2 = segment
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    D = (dx, dy)

    if abs(dx) < 1e-12 and abs(dy) < 1e-12:
        return None 

    t_enter = 0.0
    t_exit = 1.0

    n = len(poly)
    for i in range(n):
        v1 = poly[i]
        v2 = poly[(i + 1) % n]

        edge_x = v2[0] - v1[0]
        edge_y = v2[1] - v1[1]
        Nx = -edge_y
        Ny = edge_x

        S = Nx * dx + Ny * dy

        w_x = p1[0] - v1[0]
        w_y = p1[1] - v1[1]
        w_dot = Nx * w_x + Ny * w_y

        if abs(S) < 1e-12:
            if w_dot < 0:
                return None
            else:
                continue   

        t = -w_dot / S

        if S > 0:
            if t > t_exit:
                return None
            if t > t_enter:
                t_enter = t
        else:
            if t < t_enter:
                return None
            if t < t_exit:
                t_exit = t

        if t_enter > t_exit:
            return None

    if t_enter <= t_exit:
        x1 = p1[0] + t_enter * dx
        y1 = p1[1] + t_enter * dy
        x2 = p1[0] + t_exit * dx
        y2 = p1[1] + t_exit * dy
        return ((x1, y1), (x2, y2))
    return None

class ClippingApp:
    def __init__(self, root, segments, clip_rect, clip_poly):
        self.segments = segments
        self.clip_rect = clip_rect
        self.clip_poly = clip_poly

        all_x = [x for seg in segments for (x, _) in seg] + [p[0] for p in clip_poly]
        all_y = [y for seg in segments for (_, y) in seg] + [p[1] for p in clip_poly]
        margin = 10
        self.wx_min = min(all_x) - margin
        self.wx_max = max(all_x) + margin
        self.wy_min = min(all_y) - margin
        self.wy_max = max(all_y) + margin

        self.w, self.h = 800, 600
        self.canvas = tk.Canvas(root, width=self.w, height=self.h, bg='white')
        self.canvas.pack()
        self.draw()

    def world_to_canvas(self, x, y):
        cx = (x - self.wx_min) / (self.wx_max - self.wx_min) * self.w
        cy = self.h - (y - self.wy_min) / (self.wy_max - self.wy_min) * self.h
        return cx, cy

    def draw(self):
        if self.wx_min <= 0 <= self.wx_max:
            _, oy = self.world_to_canvas(0, 0)
            self.canvas.create_line(0, oy, self.w, oy, fill='lightgray', dash=(2, 2))
        if self.wy_min <= 0 <= self.wy_max:
            ox, _ = self.world_to_canvas(0, 0)
            self.canvas.create_line(ox, 0, ox, self.h, fill='lightgray', dash=(2, 2))

        poly_canvas = [self.world_to_canvas(x, y) for (x, y) in self.clip_poly]
        self.canvas.create_polygon(poly_canvas, outline='blue', fill='', width=2)

        for seg in self.segments:
            p1 = self.world_to_canvas(*seg[0])
            p2 = self.world_to_canvas(*seg[1])
            self.canvas.create_line(p1, p2, fill='gray')

        if self.clip_rect is not None:
            for seg in self.segments:
                res = cohen_sutherland_clip(seg, self.clip_rect)
                if res:
                    p1 = self.world_to_canvas(*res[0])
                    p2 = self.world_to_canvas(*res[1])
                    self.canvas.create_line(p1, p2, fill='green', width=2)

        for seg in self.segments:
            res = cyrus_beck_clip(seg, self.clip_poly)
            if res:
                p1 = self.world_to_canvas(*res[0])
                p2 = self.world_to_canvas(*res[1])
                self.canvas.create_line(p1, p2, fill='red', width=2, dash=(4, 2))

if __name__ == "__main__":
    segments, clip_rect, clip_poly = parse_input(INPUT_DATA)
    root = tk.Tk()
    root.title("Кирус–Бек (красный пунктир)")
    app = ClippingApp(root, segments, clip_rect, clip_poly)
    root.mainloop()