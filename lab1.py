import tkinter as tk
from tkinter import ttk
import colorsys

def cmyk_to_rgb(c, m, y, k):
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return round(r), round(g), round(b)

def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(r, g, b)
    if k == 1:
        return 0.0, 0.0, 0.0, 1.0
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c, m, y, k

class ColorConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Цветовые модели: RGB, CMYK, HLS")
        self.root.geometry("800x700")
        self.updating = False

        self.hls = [0.0, 0.5, 1.0]  # H, L, S
        self.create_widgets()
        self.update_all_from_hls()
        self.redraw_color_picker()

    def create_widgets(self):
        # ========== Цветовой селектор ==========
        picker_frame = ttk.Frame(self.root)
        picker_frame.pack(pady=10, padx=10, fill="x")

        # Hue-ползунок (вертикальный)
        self.hue_canvas = tk.Canvas(picker_frame, width=30, height=256, relief="sunken", bd=2)
        self.hue_canvas.pack(side="left", padx=(0, 10))
        self.hue_canvas.bind("<Button-1>", self.on_hue_click)
        self.hue_canvas.bind("<B1-Motion>", self.on_hue_click)

        # SL-квадрат
        self.sl_canvas = tk.Canvas(picker_frame, width=256, height=256, relief="sunken", bd=2)
        self.sl_canvas.pack(side="left")
        self.sl_canvas.bind("<Button-1>", self.on_sl_click)
        self.sl_canvas.bind("<B1-Motion>", self.on_sl_click)

        # ========== Панели моделей с ПОЛЗУНКАМИ и полями ==========
        models_frame = ttk.Frame(self.root)
        models_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_rgb = ttk.LabelFrame(models_frame, text="RGB")
        self.frame_cmyk = ttk.LabelFrame(models_frame, text="CMYK")
        self.frame_hls = ttk.LabelFrame(models_frame, text="HLS")

        for f in (self.frame_rgb, self.frame_cmyk, self.frame_hls):
            f.pack(fill="x", pady=3)

        # --- RGB с ползунками ---
        self.rgb_vars = [tk.IntVar() for _ in range(3)]
        self.rgb_sliders = []
        for i, name in enumerate("RGB"):
            f = ttk.Frame(self.frame_rgb)
            f.pack(fill="x", padx=5, pady=2)
            ttk.Label(f, text=name, width=3).pack(side="left")
            slider = ttk.Scale(f, from_=0, to=255, variable=self.rgb_vars[i], command=lambda v, idx=i: self.on_rgb_slider(idx))
            slider.pack(side="left", fill="x", expand=True, padx=5)
            entry = ttk.Entry(f, textvariable=self.rgb_vars[i], width=6)
            entry.pack(side="right")
            self.rgb_sliders.append(slider)
            self.rgb_vars[i].trace_add("write", lambda *_, idx=i: self.on_rgb_entry(idx))

        # --- CMYK с ползунками ---
        self.cmyk_vars = [tk.DoubleVar() for _ in range(4)]
        for i, name in enumerate("CMYK"):
            f = ttk.Frame(self.frame_cmyk)
            f.pack(fill="x", padx=5, pady=2)
            ttk.Label(f, text=name, width=3).pack(side="left")
            slider = ttk.Scale(f, from_=0, to=1, variable=self.cmyk_vars[i], command=lambda v, idx=i: self.on_cmyk_slider(idx))
            slider.pack(side="left", fill="x", expand=True, padx=5)
            entry = ttk.Entry(f, textvariable=self.cmyk_vars[i], width=8)
            entry.pack(side="right")
            self.cmyk_vars[i].trace_add("write", lambda *_, idx=i: self.on_cmyk_entry(idx))

        # --- HLS с ползунками ---
        self.h_var = tk.DoubleVar()
        self.l_var = tk.DoubleVar()
        self.s_var = tk.DoubleVar()
        self.hls_vars = [self.h_var, self.l_var, self.s_var]
        self.hls_max = [360, 1, 1]
        for i, (name, max_val) in enumerate([("H", 360), ("L", 1), ("S", 1)]):
            f = ttk.Frame(self.frame_hls)
            f.pack(fill="x", padx=5, pady=2)
            ttk.Label(f, text=name, width=3).pack(side="left")
            slider = ttk.Scale(f, from_=0, to=max_val, variable=self.hls_vars[i], command=lambda v, idx=i: self.on_hls_slider(idx))
            slider.pack(side="left", fill="x", expand=True, padx=5)
            entry = ttk.Entry(f, textvariable=self.hls_vars[i], width=8)
            entry.pack(side="right")
            self.hls_vars[i].trace_add("write", lambda *_, idx=i: self.on_hls_entry(idx))

    # ========== Обработчики ==========
    def safe_set(self, var, value, decimals=0):
        self.updating = True
        try:
            if decimals == 0:
                var.set(int(round(value)))
            else:
                var.set(round(value, decimals))
        finally:
            self.updating = False

    def update_if_not_updating(self, func):
        if not self.updating:
            func()

    # --- RGB ---
    def on_rgb_slider(self, idx):
        self.update_if_not_updating(lambda: self.process_rgb())

    def on_rgb_entry(self, idx):
        if self.updating: return
        try:
            r = max(0, min(255, self.rgb_vars[0].get()))
            g = max(0, min(255, self.rgb_vars[1].get()))
            b = max(0, min(255, self.rgb_vars[2].get()))
            self.safe_set(self.rgb_vars[0], r)
            self.safe_set(self.rgb_vars[1], g)
            self.safe_set(self.rgb_vars[2], b)
            self.process_rgb()
        except Exception:
            pass

    def process_rgb(self):
        r, g, b = [v.get() for v in self.rgb_vars]
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        self.hls = [h * 360, l, s]
        self.update_all_from_hls()

    # --- CMYK ---
    def on_cmyk_slider(self, idx):
        self.update_if_not_updating(lambda: self.process_cmyk())

    def on_cmyk_entry(self, idx):
        if self.updating: return
        try:
            vals = [max(0.0, min(1.0, v.get())) for v in self.cmyk_vars]
            for i, val in enumerate(vals):
                self.safe_set(self.cmyk_vars[i], val, 2)
            self.process_cmyk()
        except Exception:
            pass

    def process_cmyk(self):
        c, m, y, k = [v.get() for v in self.cmyk_vars]
        r, g, b = cmyk_to_rgb(c, m, y, k)
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        self.hls = [h * 360, l, s]
        self.update_all_from_hls()

    # --- HLS ---
    def on_hls_slider(self, idx):
        self.update_if_not_updating(lambda: self.process_hls())

    def on_hls_entry(self, idx):
        if self.updating: return
        try:
            val = float(self.hls_vars[idx].get())
            val = max(0.0, min(self.hls_max[idx], val))
            self.safe_set(self.hls_vars[idx], val, 2)
            self.process_hls()
        except Exception:
            pass

    def process_hls(self):
        h = self.h_var.get()
        l = self.l_var.get()
        s = self.s_var.get()
        self.hls = [h, l, s]
        self.update_all_from_hls()

    # --- Клик по селектору ---
    def on_hue_click(self, event):
        y = min(255, max(0, event.y))
        self.hls[0] = 360 * (255 - y) / 255
        self.update_all_from_hls()

    def on_sl_click(self, event):
        x = min(255, max(0, event.x))
        y = min(255, max(0, event.y))
        self.hls[2] = x / 255.0          # Saturation
        self.hls[1] = 1.0 - y / 255.0    # Lightness
        self.update_all_from_hls()

    # ========== Обновление всего ==========
    def update_all_from_hls(self):
        if self.updating:
            return
        h, l, s = self.hls
        h_norm = (h % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h_norm, l, s)
        r, g, b = round(r * 255), round(g * 255), round(b * 255)

        # Обновляем RGB
        self.safe_set(self.rgb_vars[0], r)
        self.safe_set(self.rgb_vars[1], g)
        self.safe_set(self.rgb_vars[2], b)

        # Обновляем CMYK
        c, m, y, k = rgb_to_cmyk(r, g, b)
        self.safe_set(self.cmyk_vars[0], c, 2)
        self.safe_set(self.cmyk_vars[1], m, 2)
        self.safe_set(self.cmyk_vars[2], y, 2)
        self.safe_set(self.cmyk_vars[3], k, 2)

        # Обновляем HLS
        self.safe_set(self.h_var, h % 360, 2)
        self.safe_set(self.l_var, l, 2)
        self.safe_set(self.s_var, s, 2)

        # Перерисовываем селектор с курсорами
        self.redraw_color_picker()

    # ========== Быстрая отрисовка с курсорами ==========
    def redraw_color_picker(self):
        hue = self.hls[0]
        h_norm = (hue % 360) / 360.0
        w, h_canvas = 256, 256

        self.hue_canvas.delete("all")
        self.sl_canvas.delete("all")

        # Hue-градиент
        for i in range(256):
            h_val = (360 - 360 * i / 255) / 360.0
            rgb = colorsys.hls_to_rgb(h_val, 0.5, 1.0)
            col = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
            self.hue_canvas.create_line(0, i, 30, i, fill=col)

        # SL-квадрат (блоки 8x8)
        block = 8
        for y in range(0, h_canvas, block):
            light = 1.0 - (y + block/2) / h_canvas
            for x in range(0, w, block):
                sat = (x + block/2) / w
                r, g, b = colorsys.hls_to_rgb(h_norm, light, sat)
                col = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                self.sl_canvas.create_rectangle(x, y, x+block, y+block, fill=col, outline="")

        # === Курсор на Hue-ползунке ===
        hue_y = 255 - (hue % 360) * 255 / 360
        self.hue_canvas.create_line(0, hue_y, 30, hue_y, fill="white", width=2)
        self.hue_canvas.create_line(0, hue_y, 30, hue_y, fill="black", width=1)

        # === Крестик в SL-квадрате ===
        sat_x = self.hls[2] * 255
        light_y = (1.0 - self.hls[1]) * 255
        cx, cy = sat_x, light_y
        size = 5
        # Белый крест (толстый)
        self.sl_canvas.create_line(cx - size, cy, cx + size, cy, fill="white", width=2)
        self.sl_canvas.create_line(cx, cy - size, cx, cy + size, fill="white", width=2)
        # Чёрный контур (тонкий)
        self.sl_canvas.create_line(cx - size, cy, cx + size, cy, fill="black", width=1)
        self.sl_canvas.create_line(cx, cy - size, cx, cy + size, fill="black", width=1)

# ========== Запуск ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = ColorConverterApp(root)
    root.mainloop()