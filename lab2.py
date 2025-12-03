import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def median_filter_rgb(img, k=5):
    if k % 2 == 0:
        k += 1
    pad = k // 2
    h, w = img.shape[:2]
    if img.ndim == 3:
        padded = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
        out = np.zeros_like(img)
        mid = (k * k) // 2
        for i in range(h):
            for j in range(w):
                window_r = padded[i:i+k, j:j+k, 0].ravel()
                window_g = padded[i:i+k, j:j+k, 1].ravel()
                window_b = padded[i:i+k, j:j+k, 2].ravel()
                out[i, j, 0] = np.partition(window_r, mid)[mid]
                out[i, j, 1] = np.partition(window_g, mid)[mid]
                out[i, j, 2] = np.partition(window_b, mid)[mid]
    else:
        padded = np.pad(img, pad, mode='edge')
        out = np.zeros_like(img)
        mid = (k * k) // 2
        for i in range(h):
            for j in range(w):
                window = padded[i:i+k, j:j+k].ravel()
                out[i, j] = np.partition(window, mid)[mid]
    return out.astype(np.uint8)


def linear_contrast(img):
    f = img.astype(np.float32)
    minv, maxv = f.min(), f.max()
    if maxv == minv:
        return img.copy()
    return ((f - minv) / (maxv - minv) * 255).astype(np.uint8)


def equalize_channel(c):
    hist, _ = np.histogram(c, bins=256, range=(0, 256))
    cdf = hist.cumsum()
    cdf_min = cdf[cdf > 0].min()
    if cdf[-1] == cdf_min:
        return c
    lut = ((cdf - cdf_min) * 255 / (cdf[-1] - cdf_min)).clip(0, 255).astype(np.uint8)
    return lut[c]


def equalize_rgb(img):
    if img.ndim == 2:
        return equalize_channel(img)
    return np.stack([equalize_channel(img[:, :, i]) for i in range(3)], axis=-1)


def rgb_to_hsv(img):
    img = img.astype(np.float32) / 255.0
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    vmax = np.max(img, axis=2)
    vmin = np.min(img, axis=2)
    diff = vmax - vmin

    h = np.zeros_like(vmax)
    s = np.where(vmax == 0, 0, diff / vmax)
    v = vmax

    mask = diff != 0
    h[mask & (vmax == r)] = (60 * ((g - b) / diff) % 6)[mask & (vmax == r)]
    h[mask & (vmax == g)] = (60 * ((b - r) / diff) + 2)[mask & (vmax == g)]
    h[mask & (vmax == b)] = (60 * ((r - g) / diff) + 4)[mask & (vmax == b)]
    h = np.clip(h, 0, 360)

    return np.stack([h, s, v], axis=-1)


def hsv_to_rgb(hsv):
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c

    rgb = np.zeros_like(hsv)
    i = (h // 60).astype(int) % 6
    rgb[i == 0] = np.stack([c, x, np.zeros_like(c)], axis=-1)[i == 0]
    rgb[i == 1] = np.stack([x, c, np.zeros_like(c)], axis=-1)[i == 1]
    rgb[i == 2] = np.stack([np.zeros_like(c), c, x], axis=-1)[i == 2]
    rgb[i == 3] = np.stack([np.zeros_like(c), x, c], axis=-1)[i == 3]
    rgb[i == 4] = np.stack([x, np.zeros_like(c), c], axis=-1)[i == 4]
    rgb[i == 5] = np.stack([c, np.zeros_like(c), x], axis=-1)[i == 5]

    rgb = (rgb + m[:, :, np.newaxis]) * 255
    return np.clip(rgb, 0, 255).astype(np.uint8)


def equalize_hsv(img):
    hsv = rgb_to_hsv(img)
    v_eq = equalize_channel((hsv[:, :, 2] * 255).astype(np.uint8))
    hsv[:, :, 2] = v_eq / 255.0
    return hsv_to_rgb(hsv)


class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка изображений")
        self.root.geometry("1100x820")

        self.original = None
        self.processed = None

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Загрузить", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Линейное контрастирование", command=self.apply_contrast).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Эквализация RGB", command=self.apply_eq_rgb).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Эквализация HSV", command=self.apply_eq_hsv).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Медианный фильтр", command=self.apply_median).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Гистограмма", command=self.show_hist).pack(side=tk.LEFT, padx=5)

        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)

        self.hist_frame = tk.Frame(root)
        self.hist_frame.pack(pady=10)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        pil_img = Image.open(path).convert("RGB")
        pil_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        self.original = np.array(pil_img)
        self.processed = self.original.copy()
        self._show_image(self.processed)

    def _show_image(self, arr):
        pil_img = Image.fromarray(arr)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=tk_img)
        self.image_label.image = tk_img

    def apply_contrast(self):
        if self.original is None:
            messagebox.showwarning("Ошибка", "Загрузите изображение")
            return
        self.processed = linear_contrast(self.original)
        self._show_image(self.processed)

    def apply_eq_rgb(self):
        if self.original is None:
            messagebox.showwarning("Ошибка", "Загрузите изображение")
            return
        self.processed = equalize_rgb(self.original)
        self._show_image(self.processed)

    def apply_eq_hsv(self):
        if self.original is None:
            messagebox.showwarning("Ошибка", "Загрузите изображение")
            return
        self.processed = equalize_hsv(self.original)
        self._show_image(self.processed)

    def apply_median(self):
        if self.original is None:
            messagebox.showwarning("Ошибка", "Загрузите изображение")
            return
        self.processed = median_filter_rgb(self.original, k=5)
        self._show_image(self.processed)

    def show_hist(self):
        if self.processed is None:
            messagebox.showwarning("Ошибка", "Нет изображения")
            return
        for w in self.hist_frame.winfo_children():
            w.destroy()
        fig, ax = plt.subplots(figsize=(5, 2))
        if self.processed.ndim == 3:
            for i, col in enumerate(['r', 'g', 'b']):
                hist, _ = np.histogram(self.processed[:, :, i], bins=256, range=(0, 256))
                ax.plot(hist, color=col)
        else:
            hist, _ = np.histogram(self.processed, bins=256, range=(0, 256))
            ax.plot(hist, color='k')
        ax.set_title("Гистограмма")
        ax.set_xlabel("Яркость")
        ax.set_ylabel("Частота")
        canvas = FigureCanvasTkAgg(fig, self.hist_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()