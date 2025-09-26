import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
from datetime import datetime

# --- Core Image Analysis (unchanged) ---
def analyze_image_segments(cv_image):
    if cv_image is None: return []
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    block_size, c_val = 55, 12
    binary_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, c_val)
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=2)
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.2 * dist_transform.max(), 255, 0)
    sure_bg = cv2.dilate(opening, kernel, iterations=3)
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)
    _, markers = cv2.connectedComponents(sure_fg)
    markers += 1
    markers[unknown == 255] = 0
    bgr_image_for_watershed = cv_image.copy()
    cv2.watershed(bgr_image_for_watershed, markers)
    segments = []
    for label in np.unique(markers):
        if label < 2: continue
        mask = np.zeros(gray.shape, dtype="uint8")
        mask[markers == label] = 255
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            contour = cnts[0]
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0
            segments.append({'contour': contour, 'area': area, 'circularity': circularity})
    return segments

# --- Custom Range Slider Widget ---
class CustomRangeSlider(tk.Canvas):
    def __init__(self, master, min_var, max_var, from_, to, colors, command=None, width=120):
        super().__init__(master, bg=colors['header'], height=20, width=width, highlightthickness=0)
        self.min_var, self.max_var = min_var, max_var
        self.from_, self.to_ = from_, to
        self.colors = colors
        self.command = command
        self.handle_radius = 6
        self.active_handle = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", lambda e: setattr(self, 'active_handle', None))

    def _get_x_from_val(self, val):
        width = self.winfo_width() - 2 * self.handle_radius
        percent = (val - self.from_) / (self.to_ - self.from_) if (self.to_ - self.from_) != 0 else 0
        return self.handle_radius + percent * width

    def _get_val_from_x(self, x):
        width = self.winfo_width() - 2 * self.handle_radius
        if width <= 0: return self.from_
        click_x = max(0, min(x - self.handle_radius, width))
        percent = click_x / width
        return self.from_ + percent * (self.to_ - self.from_)

    def redraw(self):
        self.delete("all")
        width = self.winfo_width()
        if width < 20: return
        line_y = self.winfo_height() / 2
        min_x = self._get_x_from_val(self.min_var.get())
        max_x = self._get_x_from_val(self.max_var.get())
        self.create_line(self.handle_radius, line_y, width - self.handle_radius, line_y, fill=self.colors['slider_bg'], width=2)
        self.create_line(min_x, line_y, max_x, line_y, fill=self.colors['slider_handle'], width=3)
        self.create_oval(min_x - self.handle_radius, line_y - self.handle_radius, min_x + self.handle_radius, line_y + self.handle_radius, fill=self.colors['slider_handle'], outline="")
        self.create_oval(max_x - self.handle_radius, line_y - self.handle_radius, max_x + self.handle_radius, line_y + self.handle_radius, fill=self.colors['slider_handle'], outline="")

    def _on_press(self, event):
        min_x = self._get_x_from_val(self.min_var.get())
        max_x = self._get_x_from_val(self.max_var.get())
        self.active_handle = "min" if abs(event.x - min_x) < abs(event.x - max_x) else "max"
        self._on_drag(event)

    def _on_drag(self, event):
        if not self.active_handle: return
        new_val = self._get_val_from_x(event.x)
        rounded_val = round(new_val, 2)
        if self.active_handle == "min": self.min_var.set(min(rounded_val, self.max_var.get()))
        else: self.max_var.set(max(rounded_val, self.min_var.get()))
        self.redraw()
        if self.command: self.command()

# --- Custom Rounded Button Widget ---
class RoundedButton(tk.Canvas):
    def __init__(self, master, text, command=None, colors=None, width=120, height=35):
        self.width, self.height, self.radius = width, height, 10
        super().__init__(master, bg=colors['header'], width=self.width, height=self.height, highlightthickness=0)
        self.text = text
        self.command = command
        self.colors = colors
        self.current_fill = self.colors['button_bg']
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.redraw()

    def redraw(self):
        self.delete("all")
        x1, y1, x2, y2 = 0, 0, self.width, self.height
        r = self.radius
        self.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, fill=self.current_fill, outline="")
        self.create_oval(x2 - 2*r, y1, x2, y1 + 2*r, fill=self.current_fill, outline="")
        self.create_oval(x1, y2 - 2*r, x1 + 2*r, y2, fill=self.current_fill, outline="")
        self.create_oval(x2 - 2*r, y2 - 2*r, x2, y2, fill=self.current_fill, outline="")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=self.current_fill, outline="")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=self.current_fill, outline="")
        font = ('Helvetica', 9)
        self.create_text(self.width/2, self.height/2, text=self.text, fill=self.colors['button_text'], font=font)

    def _on_press(self, event): self.current_fill = self.colors['button_active']; self.redraw()
    def _on_release(self, event): self.current_fill = self.colors['button_hover']; self.redraw(); self.command() if self.command else None
    def _on_enter(self, event): self.current_fill = self.colors['button_hover']; self.redraw()
    def _on_leave(self, event): self.current_fill = self.colors['button_bg']; self.redraw()

# --- Main Application Class ---
class ParticleCounterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CR-39 Particle Counter")
        self.geometry("1200x800")
        self.minsize(900, 650)

        self.padding = 10
        self.header_height = 90
        self.colors = {'bg': "#212121", 'header': "#1a1a1a", 'text': "#E0E0E0", 'green_accent': "#00FF00", 'slider_bg': "#424242", 'slider_handle': "#BDBDBD", 'button_bg': "#333333", 'button_hover': "#454545", 'button_active': "#202020", 'button_text': "#FFFFFF"}
        self.FONT_NORMAL = ('Helvetica', 9)
        self.FONT_BOLD = ('Helvetica', 10, 'bold')
        self.FONT_COUNT = ('Helvetica', 15, 'bold')
        self.configure(bg=self.colors['bg'])

        self.original_cv_image = None
        self.current_image_path = ""
        self.current_image_name = ""
        self.all_segments = []
        self.control_widgets = []
        self._update_job = None
        self.current_particle_count = 0
        
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.is_panning = False
        
        self.image_padding = 2
        
        self.zoom_controls_visible = False
        self.zoom_controls = []
        
        self.edit_mode = False
        self.manual_additions = []
        self.manual_removals = set()
        self.default_r = 10
        
        self.tolerance = 2  # pixels tolerance for clicking near contour
        
        self.setup_styles()
        self.create_header()
        self.create_image_area()
        self.setup_controls()
        self.update_controls_state("disabled")

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background=self.colors['bg'], borderwidth=0, relief='flat')
        style.configure("Header.TFrame", background=self.colors['header'], borderwidth=0, relief='flat')

    def create_header(self):
        self.header_frame = ttk.Frame(self, style="Header.TFrame", height=self.header_height)
        self.header_frame.pack(fill=tk.X, padx=self.padding, pady=(self.padding, 5))
        self.header_frame.pack_propagate(False)
        
        self.header_frame.grid_columnconfigure(0, weight=0, minsize=80)
        self.header_frame.grid_columnconfigure(1, weight=0, minsize=80)
        self.header_frame.grid_columnconfigure(2, weight=0, minsize=80)
        self.header_frame.grid_columnconfigure(3, weight=0, minsize=180)
        self.header_frame.grid_columnconfigure(4, weight=1, minsize=300)
        self.header_frame.grid_rowconfigure(0, weight=1)

    def create_image_area(self):
        self.image_canvas = tk.Canvas(self, bg=self.colors['bg'], highlightthickness=0)
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=self.padding, pady=(5, self.padding))
        self.image_canvas.bind("<Configure>", lambda e: self.update_display())
        
        self.image_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.image_canvas.bind("<Button-4>", self.on_mousewheel)
        self.image_canvas.bind("<Button-5>", self.on_mousewheel)
        self.image_canvas.bind("<ButtonPress-2>", self.start_pan)
        self.image_canvas.bind("<B2-Motion>", self.do_pan)
        self.image_canvas.bind("<ButtonRelease-2>", self.end_pan)
        self.image_canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.image_canvas.bind("<B1-Motion>", self.do_pan)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_pan)
        self.image_canvas.bind("<Enter>", self.canvas_enter)
        self.image_canvas.bind("<Leave>", self.canvas_leave)
        self.image_canvas.bind("<Motion>", self.on_mouse_motion)

        self.image_canvas.tag_bind("upload_graphic", "<Button-1>", self.on_upload_graphic_click)
        self.image_canvas.tag_bind("upload_graphic", "<Enter>", self.on_upload_graphic_enter)
        self.image_canvas.tag_bind("upload_graphic", "<Leave>", self.on_upload_graphic_leave)
        
        self.image_canvas.bind("<KeyPress>", self.on_key_press)
        self.image_canvas.focus_set()

    def setup_controls(self):
        self.min_area_var = tk.DoubleVar(value=75)
        self.max_area_var = tk.DoubleVar(value=2000)
        self.min_circ_var = tk.DoubleVar(value=0.65)
        self.max_circ_var = tk.DoubleVar(value=1.00)
        
        self.min_area_str_var = tk.StringVar(value=f"{self.min_area_var.get():.2f}")
        self.max_area_str_var = tk.StringVar(value=f"{self.max_area_var.get():.2f}")
        self.min_circ_str_var = tk.StringVar(value=f"{self.min_circ_var.get():.2f}")
        self.max_circ_str_var = tk.StringVar(value=f"{self.max_circ_var.get():.2f}")

        upload_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        upload_frame.grid(row=0, column=0, sticky='nsew', padx=(15, 5), pady=10)
        upload_frame.grid_rowconfigure(0, weight=1)
        
        self.load_button = RoundedButton(upload_frame, text="Upload\nImage", command=self.load_image, colors=self.colors, width=70, height=40)
        self.load_button.pack(anchor='center')

        save_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        save_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 5), pady=10)
        save_frame.grid_rowconfigure(0, weight=1)
        
        self.save_button = RoundedButton(save_frame, text="Save\nResults", command=self.save_results, colors=self.colors, width=70, height=40)
        self.save_button.pack(anchor='center')

        edit_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        edit_frame.grid(row=0, column=2, sticky='nsew', padx=(5, 5), pady=10)
        edit_frame.grid_rowconfigure(0, weight=1)
        
        self.edit_button = RoundedButton(edit_frame, text="Edit\nParticles", command=self.toggle_edit_mode, colors=self.colors, width=70, height=40)
        self.edit_button.pack(anchor='center')

        count_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        count_frame.grid(row=0, column=3, sticky='nsew', padx=(5, 10), pady=10)
        count_frame.grid_rowconfigure(0, weight=1)
        
        self.count_var = tk.StringVar(value="Particle Count: --")
        count_entry = tk.Entry(count_frame, textvariable=self.count_var,
                              readonlybackground=self.colors['header'], fg=self.colors['green_accent'],
                              font=self.FONT_COUNT, state="readonly", justify='center',
                              borderwidth=0, relief='flat', highlightthickness=0, width=18)
        count_entry.pack(anchor='center')

        right_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        right_frame.grid(row=0, column=4, sticky='nsew', padx=(10, 15), pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_columnconfigure(1, weight=1)

        area_frame = ttk.Frame(right_frame, style="Header.TFrame")
        area_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        area_title = tk.Label(area_frame, text="Filter Area (px²)", 
                             bg=self.colors['header'], fg=self.colors['text'],
                             font=self.FONT_BOLD)
        area_title.pack(anchor='w')
        
        area_control_frame = ttk.Frame(area_frame, style="Header.TFrame")
        area_control_frame.pack(fill='x', pady=(2, 0))
        
        area_min_entry = tk.Entry(area_control_frame, width=6, textvariable=self.min_area_str_var, 
                                 font=self.FONT_NORMAL, bg=self.colors['button_bg'], 
                                 fg=self.colors['text'], insertbackground=self.colors['text'],
                                 borderwidth=0, relief='flat', highlightthickness=0)
        area_min_entry.pack(side='left', padx=(0, 3))
        
        self.area_slider = CustomRangeSlider(area_control_frame, self.min_area_var, self.max_area_var, 
                                           1, 5000, self.colors, command=self.schedule_update, width=100)
        self.area_slider.pack(side='left', padx=3, fill='x', expand=True)
        
        area_max_entry = tk.Entry(area_control_frame, width=6, textvariable=self.max_area_str_var,
                                 font=self.FONT_NORMAL, bg=self.colors['button_bg'], 
                                 fg=self.colors['text'], insertbackground=self.colors['text'],
                                 borderwidth=0, relief='flat', highlightthickness=0)
        area_max_entry.pack(side='left', padx=(3, 0))

        circ_frame = ttk.Frame(right_frame, style="Header.TFrame")
        circ_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        circ_title = tk.Label(circ_frame, text="Circularity",
                             bg=self.colors['header'], fg=self.colors['text'],
                             font=self.FONT_BOLD)
        circ_title.pack(anchor='w')
        
        circ_control_frame = ttk.Frame(circ_frame, style="Header.TFrame")
        circ_control_frame.pack(fill='x', pady=(2, 0))
        
        circ_min_entry = tk.Entry(circ_control_frame, width=6, textvariable=self.min_circ_str_var,
                                 font=self.FONT_NORMAL, bg=self.colors['button_bg'], 
                                 fg=self.colors['text'], insertbackground=self.colors['text'],
                                 borderwidth=0, relief='flat', highlightthickness=0)
        circ_min_entry.pack(side='left', padx=(0, 3))
        
        self.circ_slider = CustomRangeSlider(circ_control_frame, self.min_circ_var, self.max_circ_var, 
                                           0.0, 1.0, self.colors, command=self.schedule_update, width=100)
        self.circ_slider.pack(side='left', padx=3, fill='x', expand=True)
        
        circ_max_entry = tk.Entry(circ_control_frame, width=6, textvariable=self.max_circ_str_var,
                                 font=self.FONT_NORMAL, bg=self.colors['button_bg'], 
                                 fg=self.colors['text'], insertbackground=self.colors['text'],
                                 borderwidth=0, relief='flat', highlightthickness=0)
        circ_max_entry.pack(side='left', padx=(3, 0))

        self.control_widgets = [area_min_entry, area_max_entry, self.area_slider, 
                               circ_min_entry, circ_max_entry, self.circ_slider, self.save_button, self.edit_button]

        self._is_updating_from_trace = False
        def setup_two_way_binding(d_var, s_var, entry_widget):
            def _update_s_from_d(*args):
                if self._is_updating_from_trace: return
                self._is_updating_from_trace = True
                try:
                    s_var.set(f"{d_var.get():.2f}")
                    self.schedule_update(d_var)
                finally:
                    self._is_updating_from_trace = False

            def _update_d_from_s(*args):
                if self._is_updating_from_trace: return
                self._is_updating_from_trace = True
                try:
                    d_var.set(float(s_var.get()))
                except (ValueError, tk.TclError):
                    pass
                finally:
                    self._is_updating_from_trace = False
            
            def _format_on_focus_out(event):
                if self._is_updating_from_trace: return
                self._is_updating_from_trace = True
                try:
                    s_var.set(f"{d_var.get():.2f}")
                finally:
                    self._is_updating_from_trace = False

            d_var.trace_add("write", _update_s_from_d)
            s_var.trace_add("write", _update_d_from_s)
            entry_widget.bind("<FocusOut>", _format_on_focus_out)

        setup_two_way_binding(self.min_area_var, self.min_area_str_var, area_min_entry)
        setup_two_way_binding(self.max_area_var, self.max_area_str_var, area_max_entry)
        setup_two_way_binding(self.min_circ_var, self.min_circ_str_var, circ_min_entry)
        setup_two_way_binding(self.max_circ_var, self.max_circ_str_var, circ_max_entry)


    def on_canvas_click(self, event):
        if self.edit_mode:
            self.manual_edit(event)
        else:
            self.start_pan(event)

    def on_upload_graphic_click(self, event):
        self.load_image()

    def on_upload_graphic_enter(self, event):
        self.image_canvas.config(cursor="hand2")
        hover_color = self.colors['slider_handle']
        self.image_canvas.itemconfig("upload_shape", fill=hover_color)
        self.image_canvas.itemconfig("upload_arc", outline=hover_color)
        self.image_canvas.itemconfig("upload_text", fill=self.colors['green_accent'])

    def on_upload_graphic_leave(self, event):
        self.image_canvas.config(cursor="")
        base_color = self.colors['slider_bg']
        self.image_canvas.itemconfig("upload_shape", fill=base_color)
        self.image_canvas.itemconfig("upload_arc", outline=base_color)
        self.image_canvas.itemconfig("upload_text", fill=self.colors['text'])

    def calculate_fit_to_window_zoom(self):
        if self.original_cv_image is None: return 1.0
        canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        if canvas_w < 20 or canvas_h < 20: return 1.0
        img_h, img_w = self.original_cv_image.shape[:2]
        padding = 4
        available_w, available_h = canvas_w - 2 * padding, canvas_h - 2 * padding
        return min(available_w / img_w, available_h / img_h)

    def fit_to_window(self):
        if self.original_cv_image is None: return
        self.zoom_factor = self.calculate_fit_to_window_zoom()
        self.image_offset_x, self.image_offset_y = 0, 0
        self.update_display()

    def zoom_in(self):
        if self.original_cv_image is None: return
        old_zoom = self.zoom_factor
        self.zoom_factor = min(self.max_zoom, self.zoom_factor + self.zoom_step)
        if self.zoom_factor != old_zoom: self.constrain_pan_offset(); self.update_display()

    def zoom_out(self):
        if self.original_cv_image is None: return
        old_zoom = self.zoom_factor
        self.zoom_factor = max(self.min_zoom, self.zoom_factor - self.zoom_step)
        if self.zoom_factor != old_zoom: self.constrain_pan_offset(); self.update_display()

    def create_zoom_controls(self):
        if self.original_cv_image is None: return
        canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        button_size, margin, spacing, radius = 30, 15, 3.75, 6
        fit_x, fit_y = canvas_w - margin - button_size // 2, canvas_h - margin - button_size // 2
        zoom_out_x, zoom_out_y = fit_x - button_size - spacing, fit_y
        zoom_in_x, zoom_in_y = zoom_out_x - button_size - spacing, fit_y
        
        def draw_rounded_square(x, y, size, fill, tag):
            x1, y1, x2, y2, r = x - size//2, y - size//2, x + size//2, y + size//2, radius
            self.image_canvas.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, fill=fill, outline="", tags=tag)
            self.image_canvas.create_oval(x2 - 2*r, y1, x2, y1 + 2*r, fill=fill, outline="", tags=tag)
            self.image_canvas.create_oval(x1, y2 - 2*r, x1 + 2*r, y2, fill=fill, outline="", tags=tag)
            self.image_canvas.create_oval(x2 - 2*r, y2 - 2*r, x2, y2, fill=fill, outline="", tags=tag)
            self.image_canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tag)
            self.image_canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tag)
        
        draw_rounded_square(zoom_in_x, zoom_in_y, button_size, "#333333", "zoom_in")
        self.image_canvas.create_text(zoom_in_x, zoom_in_y, text="+", fill="#FFFFFF", font=("Helvetica", 13, "bold"), tags="zoom_in")
        draw_rounded_square(zoom_out_x, zoom_out_y, button_size, "#333333", "zoom_out")
        self.image_canvas.create_text(zoom_out_x, zoom_out_y, text="−", fill="#FFFFFF", font=("Helvetica", 13, "bold"), tags="zoom_out")
        draw_rounded_square(fit_x, fit_y, button_size, "#333333", "fit_to_window")
        self.image_canvas.create_text(fit_x, fit_y, text="⬜", fill="#FFFFFF", font=("Helvetica", 12, "bold"), tags="fit_to_window")
        
        self.image_canvas.tag_bind("zoom_in", "<Button-1>", self.on_zoom_in_click)
        self.image_canvas.tag_bind("zoom_out", "<Button-1>", self.on_zoom_out_click)
        self.image_canvas.tag_bind("fit_to_window", "<Button-1>", self.on_fit_click)

    def on_zoom_in_click(self, event):
        self.image_canvas.itemconfig("zoom_in", fill="#202020"); self.after(100, lambda: self.image_canvas.itemconfig("zoom_in", fill="#333333")); self.zoom_in()
    def on_zoom_out_click(self, event):
        self.image_canvas.itemconfig("zoom_out", fill="#202020"); self.after(100, lambda: self.image_canvas.itemconfig("zoom_out", fill="#333333")); self.zoom_out()
    def on_fit_click(self, event):
        self.image_canvas.itemconfig("fit_to_window", fill="#202020"); self.after(100, lambda: self.image_canvas.itemconfig("fit_to_window", fill="#333333")); self.fit_to_window()

    def on_mouse_motion(self, event): pass

    def calculate_image_boundaries(self, canvas_w, canvas_h, img_w, img_h):
        scaled_w, scaled_h = int(img_w * self.zoom_factor), int(img_h * self.zoom_factor)
        max_offset_x = max(0, (scaled_w - canvas_w) / 2 + self.image_padding) if scaled_w > canvas_w else 0
        max_offset_y = max(0, (scaled_h - canvas_h) / 2 + self.image_padding) if scaled_h > canvas_h else 0
        return max_offset_x, max_offset_y

    def constrain_pan_offset(self):
        if self.original_cv_image is None: return
        canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        img_h, img_w = self.original_cv_image.shape[:2]
        max_offset_x, max_offset_y = self.calculate_image_boundaries(canvas_w, canvas_h, img_w, img_h)
        self.image_offset_x = max(-max_offset_x, min(max_offset_x, self.image_offset_x))
        self.image_offset_y = max(-max_offset_y, min(max_offset_y, self.image_offset_y))

    def load_image(self):
        filepath = filedialog.askopenfilename(title="Select a CR-39 Image File", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tif")])
        if not filepath: return
        self.current_image_path, self.current_image_name = filepath, os.path.basename(filepath)
        self.zoom_factor, self.image_offset_x, self.image_offset_y = 1.0, 0, 0
        self.hide_zoom_controls()
        self.original_cv_image = cv2.imread(filepath)
        print("Image loaded, starting analysis...")
        self.all_segments = analyze_image_segments(self.original_cv_image)
        print(f"Analysis complete. Found {len(self.all_segments)} potential segments.")
        if self.all_segments:
            areas = [s['area'] for s in self.all_segments]
            avg_area = np.mean(areas)
            self.default_r = int(np.sqrt(avg_area / np.pi))
        else:
            self.default_r = 10
        self.manual_additions = []
        self.manual_removals = set()
        self.update_controls_state("normal")
        self.update_display()
        self.show_zoom_controls()

    def save_results(self):
        if self.original_cv_image is None: messagebox.showwarning("No Image", "Please load an image first."); return
        min_area, max_area = round(self.min_area_var.get(), 2), round(self.max_area_var.get(), 2)
        min_circ, max_circ = round(self.min_circ_var.get(), 2), round(self.max_circ_var.get(), 2)
        result_text = f"Particle Counts: {self.current_particle_count} in image {self.current_image_name} of min area: {min_area}, max area: {max_area} and circularity between {min_circ} - {max_circ}."
        print(f"\033[92m{result_text}\033[0m")
        default_filename = f"particle_analysis_{self.current_image_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        save_path = filedialog.asksaveasfilename(title="Save Analysis Results", defaultextension=".txt", initialfile=default_filename, filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if save_path:
            try:
                with open(save_path, 'w') as f: f.write(result_text)
                messagebox.showinfo("Success", f"Results saved successfully to:\n{save_path}")
            except Exception as e: messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def schedule_update(self, changed_var=None):
        if self._update_job: self.after_cancel(self._update_job)
        self._update_job = self.after(20, self.update_display)
        if changed_var:
            if changed_var in (self.min_area_var, self.max_area_var): self.area_slider.redraw()
            elif changed_var in (self.min_circ_var, self.max_circ_var): self.circ_slider.redraw()

    def update_display(self):
        self.image_canvas.delete("all")
        if self.original_cv_image is None:
            canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
            if canvas_w < 20 or canvas_h < 20: return
            
            center_x, center_y = canvas_w / 2, canvas_h / 2
            
            s = 150
            y_offset = -s / 4
            icon_color = self.colors['slider_bg']
            
            base_tags = ("upload_graphic",)
            shape_tags = base_tags + ("upload_shape",)
            arc_tags = base_tags + ("upload_arc",)
            
            r = s / 8
            line_width = 2
            x1, y1 = center_x - s/2, center_y - s/2 + y_offset
            x2, y2 = center_x + s/2, center_y + s/2 + y_offset

            self.image_canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style=tk.ARC, outline=icon_color, width=line_width, tags=arc_tags)
            self.image_canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style=tk.ARC, outline=icon_color, width=line_width, tags=arc_tags)
            self.image_canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style=tk.ARC, outline=icon_color, width=line_width, tags=arc_tags)
            self.image_canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style=tk.ARC, outline=icon_color, width=line_width, tags=arc_tags)
            self.image_canvas.create_line(x1+r, y1, x2-r, y1, fill=icon_color, width=line_width, tags=shape_tags)
            self.image_canvas.create_line(x1+r, y2, x2-r, y2, fill=icon_color, width=line_width, tags=shape_tags)
            self.image_canvas.create_line(x1, y1+r, x1, y2-r, fill=icon_color, width=line_width, tags=shape_tags)
            self.image_canvas.create_line(x2, y1+r, x2, y2-r, fill=icon_color, width=line_width, tags=shape_tags)
            
            sun_r = s / 12
            sun_x, sun_y = x1 + s * 0.3, y1 + s * 0.3
            self.image_canvas.create_oval(sun_x-sun_r, sun_y-sun_r, sun_x+sun_r, sun_y+sun_r, fill=icon_color, outline="", tags=shape_tags)

            m1_points = [
                x1 + s * 0.05, y2,
                x1 + s * 0.35, y1 + s * 0.4,
                x1 + s * 0.65, y2
            ]
            m2_points = [
                x1 + s * 0.5, y2,
                x1 + s * 0.75, y1 + s * 0.5,
                x2 - s * 0.05, y2
            ]
            self.image_canvas.create_polygon(m1_points, fill=icon_color, outline="", tags=shape_tags)
            self.image_canvas.create_polygon(m2_points, fill=icon_color, outline="", tags=shape_tags)

            large_font = ('Helvetica', 14, 'bold')
            text_y = y2 + 30
            self.image_canvas.create_text(center_x, text_y, text="Click to Upload Image", 
                                          fill=self.colors['text'], font=large_font, 
                                          tags=base_tags + ("upload_text",))
        else:
            canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
            if canvas_w < 20 or canvas_h < 20: return
            img_h, img_w = self.original_cv_image.shape[:2]
            self.constrain_pan_offset()
            display_w, display_h = int(img_w * self.zoom_factor), int(img_h * self.zoom_factor)
            scaled_display_image = cv2.resize(self.original_cv_image, (display_w, display_h), interpolation=cv2.INTER_AREA)
            min_a, max_a = self.min_area_var.get(), self.max_area_var.get()
            min_c, max_c = self.min_circ_var.get(), self.max_circ_var.get()
            display_image = scaled_display_image.copy()
            particle_count = 0
            scale_factor_for_contours = self.zoom_factor
            
            for i, seg in enumerate(self.all_segments):
                if i in self.manual_removals: continue
                if min_a <= seg['area'] <= max_a and min_c <= seg['circularity'] <= max_c:
                    particle_count += 1
                    scaled_contour = (seg['contour'] * scale_factor_for_contours).astype(np.int32)
                    cv2.drawContours(display_image, [scaled_contour], -1, (0, 255, 0), 1)
            
            for seg in self.manual_additions:
                if min_a <= seg['area'] <= max_a and min_c <= seg['circularity'] <= max_c:
                    particle_count += 1
                    scaled_contour = (seg['contour'] * scale_factor_for_contours).astype(np.int32)
                    cv2.drawContours(display_image, [scaled_contour], -1, (0, 255, 0), 1)
            
            self.current_particle_count = particle_count
            self.count_var.set(f"Particle Count: {particle_count}")
            img_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            self.photo_image = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
            img_x, img_y = canvas_w // 2 + self.image_offset_x, canvas_h // 2 + self.image_offset_y
            self.image_canvas.create_image(img_x, img_y, anchor=tk.CENTER, image=self.photo_image)
            
            if self.zoom_controls_visible: self.hide_zoom_controls(); self.show_zoom_controls()

    def on_mousewheel(self, event):
        if self.original_cv_image is None: return
        zoom_change = self.zoom_step if (event.num == 4 or event.delta > 0) else -self.zoom_step
        old_zoom = self.zoom_factor
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_change))
        if self.zoom_factor != old_zoom:
            mouse_x, mouse_y = event.x - self.image_canvas.winfo_width() // 2, event.y - self.image_canvas.winfo_height() // 2
            zoom_ratio = self.zoom_factor / old_zoom
            self.image_offset_x = mouse_x + (self.image_offset_x - mouse_x) * zoom_ratio
            self.image_offset_y = mouse_y + (self.image_offset_y - mouse_y) * zoom_ratio
            self.constrain_pan_offset(); self.update_display()

    def on_key_press(self, event):
        if self.original_cv_image is None or not (event.state & 0x4): return
        if event.keysym in ['plus', 'equal', 'KP_Add']: self.zoom_in()
        elif event.keysym in ['minus', 'KP_Subtract']: self.zoom_out()

    def start_pan(self, event):
        if self.original_cv_image is None or self.edit_mode: return
        self.image_canvas.focus_set(); self.is_panning = True
        self.pan_start_x, self.pan_start_y = event.x, event.y

    def do_pan(self, event):
        if not self.is_panning or self.original_cv_image is None: return
        dx, dy = event.x - self.pan_start_x, event.y - self.pan_start_y
        self.image_offset_x += dx; self.image_offset_y += dy
        self.constrain_pan_offset()
        self.pan_start_x, self.pan_start_y = event.x, event.y
        self.update_display()

    def end_pan(self, event): self.is_panning = False
    def canvas_enter(self, event): self.image_canvas.focus_set()
    def canvas_leave(self, event): pass

    def show_zoom_controls(self):
        if self.original_cv_image is not None and not self.zoom_controls_visible:
            self.create_zoom_controls(); self.zoom_controls_visible = True

    def hide_zoom_controls(self):
        if self.zoom_controls_visible:
            self.image_canvas.delete("zoom_in", "zoom_out", "fit_to_window")
            self.zoom_controls_visible = False

    def update_controls_state(self, state="disabled"):
        for widget in self.control_widgets:
            if hasattr(widget, 'config'): widget.config(state=state)

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.image_canvas.config(cursor="crosshair")
            self.edit_button.current_fill = self.colors['button_active']
            self.edit_button.redraw()
            messagebox.showinfo("Edit Mode", "Click on a particle to remove it (green contour disappears). Click on empty area to add a new particle (green circle appears). Particle count updates live.")
        else:
            self.image_canvas.config(cursor="")
            self.edit_button.current_fill = self.colors['button_bg']
            self.edit_button.redraw()

    def get_original_coord(self, canvas_x, canvas_y):
        if self.original_cv_image is None: return None, None
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        orig_h, orig_w = self.original_cv_image.shape[:2]
        display_w = orig_w * self.zoom_factor
        display_h = orig_h * self.zoom_factor
        top_left_x = canvas_w / 2 + self.image_offset_x - display_w / 2
        top_left_y = canvas_h / 2 + self.image_offset_y - display_h / 2
        scaled_x = canvas_x - top_left_x
        scaled_y = canvas_y - top_left_y
        if scaled_x < 0 or scaled_y < 0 or scaled_x > display_w or scaled_y > display_h:
            return None, None
        orig_x = scaled_x / self.zoom_factor
        orig_y = scaled_y / self.zoom_factor
        return int(orig_x), int(orig_y)

    def manual_edit(self, event):
        orig_x, orig_y = self.get_original_coord(event.x, event.y)
        if orig_x is None or orig_y is None: return
        min_a, max_a = self.min_area_var.get(), self.max_area_var.get()
        min_c, max_c = self.min_circ_var.get(), self.max_circ_var.get()
        hit = False
        # Check manual additions first (remove if clicked)
        for j in range(len(self.manual_additions) - 1, -1, -1):
            seg = self.manual_additions[j]
            if min_a <= seg['area'] <= max_a and min_c <= seg['circularity'] <= max_c:
                dist = cv2.pointPolygonTest(seg['contour'], (orig_x, orig_y), True)
                if dist > -self.tolerance:
                    del self.manual_additions[j]
                    hit = True
                    break
        if not hit:
            # Check detected segments (remove if clicked)
            for i, seg in enumerate(self.all_segments):
                if i in self.manual_removals: continue
                if min_a <= seg['area'] <= max_a and min_c <= seg['circularity'] <= max_c:
                    dist = cv2.pointPolygonTest(seg['contour'], (orig_x, orig_y), True)
                    if dist > -self.tolerance:
                        self.manual_removals.add(i)
                        hit = True
                        break
        if not hit:
            # Add new particle if clicked on empty area
            orig_h, orig_w = self.original_cv_image.shape[:2]
            if 0 <= orig_x < orig_w and 0 <= orig_y < orig_h:
                r = self.default_r
                contour = self.create_circle_contour(orig_x, orig_y, r)
                area = np.pi * r**2
                circularity = 1.0
                self.manual_additions.append({'contour': contour, 'area': area, 'circularity': circularity})
        self.update_display()

    def create_circle_contour(self, cx, cy, r):
        theta = np.linspace(0, 2*np.pi, 50)
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        points = np.column_stack((x, y)).astype(np.int32)
        return points.reshape((-1, 1, 2))

if __name__ == "__main__":
    app = ParticleCounterApp()
    app.mainloop()