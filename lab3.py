import tkinter as tk
from tkinter import ttk, messagebox
import time


GRID_MIN = -30
GRID_MAX = 30
GRID_SIZE = GRID_MAX - GRID_MIN + 1
PIXEL_SCALE = 12
CANVAS_SIZE = GRID_SIZE * PIXEL_SCALE

class RasterLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Рисование прямых и окружностей")
        self.root.geometry("850x720")

        self.entries = {}

        control = ttk.Frame(root)
        control.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        ttk.Label(control, text="Алгоритм:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0,5))
        self.algo = tk.StringVar(value="step")
        for text, val in [
            ("Пошаговый", "step"),
            ("ЦДА", "dda"),
            ("Брезенхем (отрезок)", "bresenham_line"),
            ("Брезенхем (окружность)", "bresenham_circle")
        ]:
            ttk.Radiobutton(control, text=text, variable=self.algo, value=val).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(control, text="Координаты отрезка:", font=("Arial", 9, "underline")).pack(anchor=tk.W, pady=(15,5))
        self.create_coord_entry(control, "x1:", "x1", -20)
        self.create_coord_entry(control, "y1:", "y1", -10)
        self.create_coord_entry(control, "x2:", "x2", 20)
        self.create_coord_entry(control, "y2:", "y2", 15)

        ttk.Label(control, text="Окружность:", font=("Arial", 9, "underline")).pack(anchor=tk.W, pady=(15,5))
        self.create_coord_entry(control, "Центр X:", "cx", 0)
        self.create_coord_entry(control, "Центр Y:", "cy", 0)
        self.create_coord_entry(control, "Радиус:", "r", 15)

        ttk.Button(control, text="Выполнить", command=self.run).pack(pady=20)

        self.time_label = ttk.Label(control, text="Время: —", font=("Arial", 9))
        self.time_label.pack(anchor=tk.W)

        canvas_frame = ttk.Frame(root)
        canvas_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.canvas.pack()
        self.draw_grid()

    def create_coord_entry(self, parent, label_text, var_name, default):
        frame = ttk.Frame(parent)
        frame.pack(anchor=tk.W, pady=2)
        ttk.Label(frame, text=label_text, width=12, anchor="w").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=8)
        entry.insert(0, str(default))
        entry.pack(side=tk.LEFT)
        self.entries[var_name] = entry

    def get_int(self, name):
        try:
            val = int(self.entries[name].get())
            return val
        except ValueError:
            raise ValueError(f"Некорректное значение: {name}")

    def draw_grid(self):
        self.canvas.delete("all")
        center_px = (GRID_MAX) * PIXEL_SCALE

        for i in range(GRID_SIZE):
            x = i * PIXEL_SCALE
            y = i * PIXEL_SCALE
            self.canvas.create_line(x, 0, x, CANVAS_SIZE, fill="lightgray")
            self.canvas.create_line(0, y, CANVAS_SIZE, y, fill="lightgray")

        self.canvas.create_line(center_px, 0, center_px, CANVAS_SIZE, fill="black", width=2)
        self.canvas.create_line(0, center_px, CANVAS_SIZE, center_px, fill="black", width=2)

        self.canvas.create_text(center_px - 10, 10, text="Y", anchor="w", font=("Arial", 9, "bold"))
        self.canvas.create_text(CANVAS_SIZE - 10, center_px + 10, text="X", anchor="e", font=("Arial", 9, "bold"))

        for i in range(GRID_MIN, GRID_MAX + 1):
            if i % 5 == 0 and i != 0:
                # По X
                x_px = (i - GRID_MIN) * PIXEL_SCALE
                self.canvas.create_text(x_px, center_px + 15, text=str(i), font=("Arial", 7))
                # По Y
                y_px = (-i - GRID_MIN) * PIXEL_SCALE
                self.canvas.create_text(center_px - 15, y_px, text=str(i), font=("Arial", 7))

    def grid_to_canvas(self, gx, gy):
        x = (gx - GRID_MIN) * PIXEL_SCALE
        y = (-gy - GRID_MIN) * PIXEL_SCALE
        return x, y

    def plot(self, gx, gy, color="red"):
        if gx < GRID_MIN or gx > GRID_MAX or gy < GRID_MIN or gy > GRID_MAX:
            return
        x, y = self.grid_to_canvas(gx, gy)
        self.canvas.create_rectangle(x, y, x + PIXEL_SCALE, y + PIXEL_SCALE, fill=color, outline="")

    def plot8circle(self, cx, cy, x, y, color="blue"):
        points = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x),
        ]
        for px, py in points:
            self.plot(px, py, color)

    def run(self):
        self.draw_grid()
        algo = self.algo.get()

        start_time = time.perf_counter()
        try:
            if algo in ("step", "dda", "bresenham_line"):
                x1 = self.get_int("x1")
                y1 = self.get_int("y1")
                x2 = self.get_int("x2")
                y2 = self.get_int("y2")
                if algo == "step":
                    self.step_line(x1, y1, x2, y2)
                elif algo == "dda":
                    self.dda_line(x1, y1, x2, y2)
                elif algo == "bresenham_line":
                    self.bresenham_line_full(x1, y1, x2, y2)
            elif algo == "bresenham_circle":
                cx = self.get_int("cx")
                cy = self.get_int("cy")
                r = self.get_int("r")
                if r <= 0:
                    raise ValueError("Радиус должен быть положительным")
                self.bresenham_circle_full(cx, cy, r)
            else:
                raise ValueError("Неизвестный алгоритм")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        elapsed = time.perf_counter() - start_time
        self.time_label.config(text=f"Время: {elapsed:.7f} с")

    def step_line(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            self.plot(x1, y1)
            return
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = x1, y1
        for _ in range(int(steps) + 1):
            self.plot(round(x), round(y))
            x += x_inc
            y += y_inc

    def dda_line(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        L = max(abs(dx), abs(dy))
        if L == 0:
            self.plot(x1, y1)
            return
        x_inc = dx / L
        y_inc = dy / L
        x, y = x1, y1
        for _ in range(int(L) + 1):
            self.plot(round(x), round(y))
            x += x_inc
            y += y_inc

    def bresenham_line_full(self, x1, y1, x2, y2):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        x, y = x1, y1
        while True:
            self.plot(x, y)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def bresenham_circle_full(self, cx, cy, r):
        x = 0
        y = r
        e = 3 - 2 * r
        self.plot8circle(cx, cy, x, y)
        while y >= x:
            x += 1
            if e >= 0:
                y -= 1
                e += 4 * (x - y) + 10
            else:
                e += 4 * x + 6
            self.plot8circle(cx, cy, x, y)

if __name__ == "__main__":
    root = tk.Tk()
    app = RasterLabApp(root)
    root.mainloop()