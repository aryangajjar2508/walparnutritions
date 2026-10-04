import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import math
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import os
import sys

class BatchMasterCardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Master Card Generator")
        self.set_fullscreen(self.root)
        self.root.configure(bg="#f5f5f5")

        # Application state variables
        self.product_type = None
        self.quantity = 0
        self.size_or_capsule = None
        self.capsule_types = None
        self.serving_size = None
        self.sugar_type = None
        self.sugar_percent = None
        self.custom_ingredients = []
        self.selected_excipients = []
        self.current_step = None

        # Data dictionaries
        self.formulations = self.load_formulations()
        self.liquid_packaging_costs = self.load_liquid_packaging_costs()
        self.capsule_pricing = self.load_capsule_pricing()
        self.sugar_cost_mapping = self.load_sugar_cost_mapping()
        self.sorbitol_cost_mapping = self.load_sorbitol_cost_mapping()
        self.predefined_liquid_other_ingredients = self.load_liquid_ingredients()
        self.ingredient_list = []
        self.rate_dict = {}

        # Rate file path
        self.rate_file_path = "rate avg.xlsx"
        self.load_rate_data()

        # Main frame
        self.main_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.show_login_window()

    def set_fullscreen(self, window):
        try:
            window.attributes('-fullscreen', True)
        except tk.TclError:
            window.state('zoomed')

    def bind_mousewheel(self, canvas):
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (AttributeError, tk.TclError):
                pass

        try:
            canvas.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))
        except tk.TclError:
            pass

    def clear_frame(self):
        try:
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass

    def go_back(self):
        self.clear_frame()
        if self.current_step == "step1":
            self.show_login_window()
        elif self.current_step == "step2_tablet_capsule" or self.current_step == "step2_liquid":
            self.show_step1_window()
        elif self.current_step == "step3":
            if self.product_type in ["Tablet", "Capsule"]:
                self.show_step2_window()
            else:
                self.show_step2_liquid_window()
        elif self.current_step == "step4":
            self.show_step3_window()
        elif self.current_step == "output":
            self.show_step4_window()

    def load_rate_data(self):
        file_path = self.rate_file_path
        if not os.path.exists(file_path):
            messagebox.showinfo("File Not Found", f"Please locate the '{self.rate_file_path}' file.")
            file_path = filedialog.askopenfilename(
                title=f"Select '{self.rate_file_path}'",
                filetypes=[("Excel files", "*.xlsx")]
            )
        if not file_path:
            messagebox.showerror("Error", "Rate file is required to run the application.")
            self.root.destroy()
            return

        try:
            rate_df = pd.read_excel(file_path, header=None)
            if rate_df.empty or len(rate_df.columns) < 2:
                raise ValueError("Excel file must have at least 2 columns (Ingredient and Rate)")

            rate_df.columns = ["Ingredient", "Rate"]
            rate_df = rate_df.dropna()

            self.ingredient_list = list(rate_df["Ingredient"].astype(str))
            self.rate_dict = dict(zip(rate_df["Ingredient"].astype(str), rate_df["Rate"]))

            if not self.ingredient_list:
                raise ValueError("No valid ingredients found in the file")

        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while loading the Excel file: {str(e)}")
            self.root.destroy()

    def load_formulations(self):
        return {
            100: {"batch_kg": 0.01, "active_mg_per_tablet": 15, "ingredients": [("Starch DCP granules", "DCP", "Powder", 0.003, 70, "B. Pest"), ("Starch paste", "Starch", "Powder", 0.0007, 45, "B. Pest"), ("Talcum", "Talcum", "Powder", 0.0007, 25, "C. Lubrication"), ("Magnesium Stearate", "Magnesium Stearate", "Powder", 0.0005, 140, "C. Lubrication"), ("SSG", "SSG", "Powder", 0.0004, 72, "C. Lubrication"), ("MCCP", "", "", 0.0004, 450, "C. Lubrication"), ("Aerosil", "Aerosil", "Powder", 0.0001, 425, "C. Lubrication"), ("COATING - IRON OXIDE RED", "Coating Powder", "Powder", 0.0003, 950, "D. Coating"), ("IPA", "IPA", "Liquid", 0.0025, 85, "D. Coating"), ("MDC", "MDC", "Liquid", 0.0035, 58, "D. Coating")]},
            400: {"batch_kg": 0.04, "active_mg_per_tablet": 150, "ingredients": [("Starch DCP granules", "DCP", "Powder", 0.012, 70, "B. Pest"), ("Starch paste", "Starch", "Powder", 0.002, 45, "B. Pest"), ("Talcum", "Talcum", "Powder", 0.004, 25, "C. Lubrication"), ("Magnesium Stearate", "Magnesium Stearate", "Powder", 0.003, 140, "C. Lubrication"), ("SSG", "SSG", "Powder", 0.002, 72, "C. Lubrication"), ("MCCP", "", "", 0.002, 450, "C. Lubrication"), ("Aerosil", "Aerosil", "Powder", 0.0005, 425, "C. Lubrication"), ("COATING - IRON OXIDE RED", "Coating Powder", "Powder", 0.0015, 950, "D. Coating"), ("IPA", "IPA", "Liquid", 0.012, 85, "D. Coating"), ("MDC", "MDC", "Liquid", 0.018, 58, "D. Coating")]},
            900: {"batch_kg": 0.09, "active_mg_per_tablet": 337.5, "ingredients": [("Starch DCP granules", "DCP", "Powder", 0.027, 70, "B. Pest"), ("Starch paste", "Starch", "Powder", 0.0045, 45, "B. Pest"), ("Talcum", "Talcum", "Powder", 0.009, 25, "C. Lubrication"), ("Magnesium Stearate", "Magnesium Stearate", "Powder", 0.00675, 140, "C. Lubrication"), ("SSG", "SSG", "Powder", 0.0045, 72, "C. Lubrication"), ("MCCP", "", "", 0.0045, 450, "C. Lubrication"), ("Aerosil", "Aerosil", "Powder", 0.001125, 425, "C. Lubrication"), ("COATING - IRON OXIDE RED", "Coating Powder", "Powder", 0.003, 950, "D. Coating"), ("IPA", "IPA", "Liquid", 0.025, 85, "D. Coating"), ("MDC", "MDC", "Liquid", 0.035, 58, "D. Coating")]},
            1000: {"batch_kg": 0.10, "active_mg_per_tablet": 420, "ingredients": [("Starch DCP granules", "DCP", "Powder", 0.030, 70, "B. Pest"), ("Starch paste", "Starch", "Powder", 0.007, 45, "B. Pest"), ("Talcum", "Talcum", "Powder", 0.007, 25, "C. Lubrication"), ("Magnesium Stearate", "Magnesium Stearate", "Powder", 0.005, 140, "C. Lubrication"), ("SSG", "SSG", "Powder", 0.004, 72, "C. Lubrication"), ("MCCP", "", "", 0.004, 450, "C. Lubrication"), ("Aerosil", "Aerosil", "Powder", 0.001, 425, "C. Lubrication"), ("COATING - IRON OXIDE RED", "Coating Powder", "Powder", 0.003, 950, "D. Coating"), ("IPA", "IPA", "Liquid", 0.025, 85, "D. Coating"), ("MDC", "MDC", "Liquid", 0.035, 58, "D. Coating")]},
            1800: {"batch_kg": 0.18, "active_mg_per_tablet": 800, "ingredients": [("Starch DCP granules", "DCP", "Powder", 0.054, 70, "B. Pest"), ("Starch paste", "Starch", "Powder", 0.010, 45, "B. Pest"), ("Talcum", "Talcum", "Powder", 0.012, 25, "C. Lubrication"), ("Magnesium Stearate", "Magnesium Stearate", "Powder", 0.009, 140, "C. Lubrication"), ("SSG", "SSG", "Powder", 0.007, 72, "C. Lubrication"), ("MCCP", "", "", 0.007, 450, "C. Lubrication"), ("Aerosil", "Aerosil", "Powder", 0.002, 425, "C. Lubrication"), ("COATING - IRON OXIDE RED", "Coating Powder", "Powder", 0.006, 950, "D. Coating"), ("IPA", "IPA", "Liquid", 0.050, 85, "D. Coating"), ("MDC", "MDC", "Liquid", 0.070, 58, "D. Coating")]},
        }

    def load_capsule_pricing(self):
        return {"00": {"veg": 0.50, "non_veg": 0.20}, "0": {"veg": 0.45, "non_veg": 0.13}, "1": {"veg": 0.40, "non_veg": 0.12}, "2": {"veg": 0.40, "non_veg": 0.11}, "DR": 0.72}

    def load_sugar_cost_mapping(self):
        return {"20%": 168, "30%": 252, "40%": 336, "50%": 420, "60%": 504}

    def load_sorbitol_cost_mapping(self):
        return {"20%": 216, "30%": 324, "40%": 432, "50%": 540, "60%": 648}

    def load_liquid_packaging_costs(self):
        return {
            "Bottle type": {
                "100ml": {
                    "round brute": 2.25,
                    "brute": 2.20,
                    "dome": 2.30
                },
                "200ml": {
                    "brute": 3.00,
                    "micro brute": 3.60,
                    "glo back": 3.50
                }
            },
            "ROPP type": {"quality": 0.55, "printed": 0.60},
            "measuring cup": {"yes": 0.25, "no": 0},
            "carton": {
                "100ml": {
                    "uv dripp off": 2.30,
                    "metallic": 3.50
                },
                "200ml": {
                    "uv dripp off": {"default": 2.45, "micro brute": 3.50},
                    "metallic": {"default": 4.00, "micro brute": 4.50}
                }
            },
            "label": {"chromo": 0.50, "metallic": 1.30},
            "shipper": {
                "100ml": {
                    "100 nos": {"5ply": 50, "7ply": 60}
                },
                "200ml": {
                    "72 nos": {"5ply": 50, "7ply": 65},
                    "60 nos": {"5ply": 45, "7ply": 60}
                }
            },
            "accessories": {"yes": 0.50, "no": 0}
        }

    def load_liquid_ingredients(self):
        return [
            {"name": "Xanthan gum - Transperent", "other": "Xanthan gum - Transperent", "type": "Powder", "qty_per_1000_bottles_kg": 0.2, "rate": 1800},
            {"name": "Mixed Fruit Flavour", "other": "Mixed Fruit", "type": "Liquid", "qty_per_1000_bottles_kg": 0.2, "rate": 650},
            {"name": "Citric acid Anhydrous", "other": "Citric acid Anhydrous", "type": "Powder", "qty_per_1000_bottles_kg": 0.12, "rate": 250},
            {"name": "Caramel Colour", "other": "Caramel Colour", "type": "Liquid", "qty_per_1000_bottles_kg": 0.2, "rate": 100},
            {"name": "Sodium Benzoate", "other": "Sodium Benzoate", "type": "Powder", "qty_per_1000_bottles_kg": 0.4, "rate": 250},
            {"name": "Sodium Methyl Parabene", "other": "Sodium Methyl Parabene", "type": "Powder", "qty_per_1000_bottles_kg": 0.4, "rate": 550},
            {"name": "Sodium Propyl Parabene", "other": "Sodium Propyl Parabene", "type": "Powder", "qty_per_1000_bottles_kg": 0.1, "rate": 450},
        ]

    def show_login_window(self):
        self.clear_frame()
        self.current_step = "login"

        main_frame = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(main_frame, text="Username:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(pady=5)
        username = tk.Entry(main_frame, font=("Segoe UI", 12))
        username.pack(pady=5)
        username.focus()

        tk.Label(main_frame, text="Password:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(pady=5)
        password = tk.Entry(main_frame, show="*", font=("Segoe UI", 12))
        password.pack(pady=5)

        def check_login(event=None):
            if username.get() == "walpar" and password.get() == "123789":
                self.show_step1_window()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")

        password.bind('<Return>', check_login)
        ttk.Button(main_frame, text="Login", command=check_login).pack(pady=10)

        ttk.Button(self.root, text="X", command=self.root.destroy).place(relx=1.0, x=-10, y=10, anchor="ne")

    def show_step1_window(self):
        self.clear_frame()
        self.current_step = "step1"

        canvas = tk.Canvas(self.main_frame, bg="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.main_frame, text="Back", command=self.go_back).place(x=10, y=10)

        tk.Label(scrollable_frame, text="Batch Manufacturing Generator", font=("Segoe UI", 16, "bold"), bg="#f5f5f5").pack(pady=20)
        product_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        product_frame.pack(pady=10)
        tk.Label(product_frame, text="Product Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(side=tk.LEFT, padx=10)

        product_type_var = tk.StringVar(value="Tablet")
        product_type_combo = ttk.Combobox(product_frame, textvariable=product_type_var, values=["Tablet", "Capsule", "Liquid"], state="readonly", width=15)
        product_type_combo.pack(side=tk.LEFT, padx=10)

        def on_product_type_change(event):
            if product_type_var.get() == "Tablet":
                tablet_frame.pack(pady=10)
                capsule_frame.pack_forget()
                liquid_frame.pack_forget()
            elif product_type_var.get() == "Capsule":
                capsule_frame.pack(pady=10)
                tablet_frame.pack_forget()
                liquid_frame.pack_forget()
            else:
                liquid_frame.pack(pady=10)
                tablet_frame.pack_forget()
                capsule_frame.pack_forget()

        product_type_combo.bind('<<ComboboxSelected>>', on_product_type_change)

        def validate_positive_integer(value):
            try:
                num = int(value)
                return num > 0
            except ValueError:
                return False

        def on_generate_click(event=None):
            try:
                self.product_type = product_type_var.get()
                if self.product_type == "Tablet":
                    size_value = size_var.get()
                    if not size_value:
                        raise ValueError("Please select a tablet size")
                    self.size_or_capsule = int(size_value)
                    quantity_str = tablets_var.get().strip()
                    if not quantity_str:
                        raise ValueError("Please enter the number of tablets")
                    if not validate_positive_integer(quantity_str):
                        raise ValueError("Number of tablets must be a positive integer")
                    self.quantity = int(quantity_str)
                    if self.size_or_capsule not in self.formulations:
                        raise ValueError("Invalid tablet size")
                    self.show_step2_window()
                elif self.product_type == "Capsule":
                    self.size_or_capsule = capsule_size_var.get()
                    if not self.size_or_capsule:
                        raise ValueError("Please select a capsule size")
                    quantity_str = capsules_var.get().strip()
                    if not quantity_str:
                        raise ValueError("Please enter the number of capsules")
                    if not validate_positive_integer(quantity_str):
                        raise ValueError("Number of capsules must be a positive integer")
                    self.quantity = int(quantity_str)
                    self.capsule_types = capsule_type_var.get()
                    if not self.capsule_types:
                        raise ValueError("Please select a capsule type.")
                    self.show_step2_window()
                elif self.product_type == "Liquid":
                    self.size_or_capsule = bottle_size_var.get()
                    if not self.size_or_capsule:
                        raise ValueError("Please select a bottle size")
                    self.serving_size = serving_size_var.get()
                    if not self.serving_size:
                        raise ValueError("Please select a serving size")
                    quantity_str = bottles_var.get().strip()
                    if not quantity_str:
                        raise ValueError("Please enter the number of bottles")
                    if not validate_positive_integer(quantity_str):
                        raise ValueError("Number of bottles must be a positive integer")
                    self.quantity = int(quantity_str)
                    self.sugar_type = sugar_type_var.get()
                    self.sugar_percent = sugar_percent_var.get()
                    if not self.sugar_type:
                        raise ValueError("Please select a sugar type")
                    if not self.sugar_percent:
                        raise ValueError("Please select a sugar percentage")
                    self.show_step2_liquid_window()
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

        # Tablet frame
        tablet_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        tk.Label(tablet_frame, text="Tablet Size (mg):", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        size_var = tk.StringVar(value="100")
        ttk.Combobox(tablet_frame, textvariable=size_var, values=["100", "400", "900", "1000", "1800"], state="readonly", width=15).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(tablet_frame, text="No. of Tablets:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        tablets_var = tk.StringVar()
        tablets_entry = tk.Entry(tablet_frame, textvariable=tablets_var, font=("Segoe UI", 12), width=20)
        tablets_entry.grid(row=1, column=1, padx=10, pady=10)
        tablets_entry.bind('<Return>', on_generate_click)
        tablet_frame.pack(pady=10)

        # Capsule frame
        capsule_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        tk.Label(capsule_frame, text="Capsule Size:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        capsule_size_var = tk.StringVar(value="00")
        ttk.Combobox(capsule_frame, textvariable=capsule_size_var, values=["00", "0", "1", "2"], state="readonly", width=15).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(capsule_frame, text="No. of Capsules:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        capsules_var = tk.StringVar()
        capsules_entry = tk.Entry(capsule_frame, textvariable=capsules_var, font=("Segoe UI", 12), width=20)
        capsules_entry.grid(row=1, column=1, padx=10, pady=10)
        capsules_entry.bind('<Return>', on_generate_click)
        tk.Label(capsule_frame, text="Capsule Type:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        type_frame = tk.Frame(capsule_frame, bg="#f5f5f5")
        type_frame.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        capsule_type_var = tk.StringVar(value="veg")
        tk.Radiobutton(type_frame, text="Veg", variable=capsule_type_var, value="veg", font=("Segoe UI", 10), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(type_frame, text="Non-Veg", variable=capsule_type_var, value="non_veg", font=("Segoe UI", 10), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(type_frame, text="DR", variable=capsule_type_var, value="DR", font=("Segoe UI", 10), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        capsule_frame.pack_forget()

        # Liquid frame
        liquid_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        tk.Label(liquid_frame, text="No. of Bottles:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        bottles_var = tk.StringVar()
        bottles_entry = tk.Entry(liquid_frame, textvariable=bottles_var, font=("Segoe UI", 12), width=20)
        bottles_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(liquid_frame, text="Bottle Size:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        bottle_size_var = tk.StringVar(value="100 ml")
        ttk.Combobox(liquid_frame, textvariable=bottle_size_var, values=["15 ml", "30 ml", "60 ml", "100 ml", "150 ml", "200 ml", "225 ml", "250 ml", "400 ml", "500 ml"], state="readonly", width=15).grid(row=1, column=1, padx=10, pady=10)
        tk.Label(liquid_frame, text="Serving Size:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        serving_size_var = tk.StringVar(value="5 ml")
        ttk.Combobox(liquid_frame, textvariable=serving_size_var, values=["1 ml", "5 ml", "10 ml", "15 ml"], state="readonly", width=15).grid(row=2, column=1, padx=10, pady=10)
        sugar_type_var = tk.StringVar(value="Sugar")
        tk.Label(liquid_frame, text="Type:", font=("Segoe UI", 12), bg="#f5f5f5").grid(row=3, column=0, sticky="e", padx=10, pady=10)

        def update_sugar_label(sugar_type):
            sugar_percent_label.config(text=f"{sugar_type} %:")

        sugar_radio = tk.Radiobutton(liquid_frame, text="Sugar", variable=sugar_type_var, value="Sugar", font=("Segoe UI", 10), bg="#f5f5f5", command=lambda: update_sugar_label("Sugar"))
        sugar_radio.grid(row=3, column=1, sticky="w")
        sugarfree_radio = tk.Radiobutton(liquid_frame, text="Sorbitol", variable=sugar_type_var, value="Sorbitol", font=("Segoe UI", 10), bg="#f5f5f5", command=lambda: update_sugar_label("Sorbitol"))
        sugarfree_radio.grid(row=3, column=1, sticky="e")
        sugar_percent_var = tk.StringVar(value="20%")
        sugar_percent_menu = ttk.Combobox(liquid_frame, textvariable=sugar_percent_var, values=["20%", "30%", "40%", "50%", "60%"], state="readonly", width=10)
        sugar_percent_menu.grid(row=4, column=1, padx=10, pady=10)
        sugar_percent_label = tk.Label(liquid_frame, text="Sugar %:", font=("Segoe UI", 12), bg="#f5f5f5")
        sugar_percent_label.grid(row=4, column=0, sticky="e", padx=10, pady=10)
        liquid_frame.pack_forget()

        ttk.Button(scrollable_frame, text="Next", command=on_generate_click, width=20).pack(pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

    def show_step2_liquid_window(self):
        self.clear_frame()
        self.current_step = "step2_liquid"

        main_frame = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="Selected Configuration:", font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack(pady=10)
        tk.Label(main_frame, text=f"Bottle Size: {self.size_or_capsule}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
        tk.Label(main_frame, text=f"Number of Bottles: {self.quantity}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
        tk.Label(main_frame, text=f"Serving Size: {self.serving_size}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
        tk.Label(main_frame, text=f"Type: {self.sugar_type}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
        if self.sugar_type in ["Sugar", "Sorbitol"]:
            tk.Label(main_frame, text=f"{self.sugar_type} Percentage: {self.sugar_percent}", font=("Segoe UI", 12), bg="#f5f5f5").pack()

        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Back", command=self.go_back).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Next - Add Ingredients", command=self.show_step3_window).pack(side=tk.LEFT, padx=10)

        ttk.Button(self.root, text="X", command=self.root.destroy).place(relx=1.0, x=-10, y=10, anchor="ne")

    def show_step2_window(self):
        self.clear_frame()
        self.current_step = "step2_tablet_capsule"

        canvas = tk.Canvas(self.main_frame, bg="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.main_frame, text="Back", command=self.go_back).place(x=10, y=10)

        tk.Label(scrollable_frame, text="Select Ingredients to Include", font=("Segoe UI", 16, "bold"), bg="#f5f5f5").pack(pady=10)
        if self.product_type == "Tablet":
            formulation_data = self.formulations.get(self.size_or_capsule, {"ingredients": []})
        else:
            formulation_data = {"ingredients": [("Di-Calcium Phosphate", "Di-Calcium Phosphate", "Powder", 0.003, 70, "B. Excipients"), ("Talcum", "Talcum", "Powder", 0.0007, 25, "B. Excipients"), ("Sodium Methyl Parabene", "Sodium Methyl Parabene", "Powder", 0.0001, 100, "B. Excipients"), ("Sodium Propyl Parabene", "Sodium Propyl Parabene", "Powder", 0.000025, 25, "B. Excipients")]}

        self.selected_excipients = []
        groups = {}
        for ingredient_data in formulation_data["ingredients"]:
            name, other, typ, qty, rate, group = ingredient_data
            if group not in groups:
                groups[group] = []
            groups[group].append(ingredient_data)

        group_vars = {}
        ingredient_vars = {}

        def toggle_group(group_name):
            state = group_vars[group_name].get()
            for ingredient_data in groups[group_name]:
                ingredient_vars[ingredient_data[0]].set(state)

        def on_ingredient_check(ingredient_name, group_name):
            all_checked = all(ingredient_vars[ingr[0]].get() for ingr in groups[group_name])
            group_vars[group_name].set(1 if all_checked else 0)

        def on_next_click():
            self.selected_excipients = [ingr for group_name, ingr_list in groups.items() for ingr in ingr_list if ingredient_vars[ingr[0]].get()]
            self.show_step3_window()

        for group_name, ingredient_list in groups.items():
            group_frame = tk.LabelFrame(scrollable_frame, text=group_name, bg="#f5f5f5", font=("Segoe UI", 12, "bold"))
            group_frame.pack(fill="x", padx=10, pady=10)
            group_vars[group_name] = tk.IntVar(value=1)
            group_cb = tk.Checkbutton(group_frame, text="Select All", variable=group_vars[group_name],
                                      command=lambda g=group_name: toggle_group(g), bg="#f5f5f5", font=("Segoe UI", 10))
            group_cb.pack(anchor="w")
            for ingredient_data in ingredient_list:
                ingredient_name = ingredient_data[0]
                ingredient_vars[ingredient_name] = tk.IntVar(value=1)
                ingredient_cb = tk.Checkbutton(group_frame, text=ingredient_name,
                                               variable=ingredient_vars[ingredient_name],
                                               command=lambda name=ingredient_name, g=group_name: on_ingredient_check(name, g),
                                               bg="#f5f5f5", font=("Segoe UI", 10))
                ingredient_cb.pack(anchor="w", padx=20)

        ttk.Button(scrollable_frame, text="Next - Add Active Ingredients", command=on_next_click, width=25).pack(pady=20)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

    def show_step3_window(self):
        self.clear_frame()
        self.current_step = "step3"

        canvas = tk.Canvas(self.main_frame, bg="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.main_frame, text="Back", command=self.go_back).place(x=10, y=10)

        tk.Label(scrollable_frame, text="Add Active Ingredients", font=("Segoe UI", 16, "bold"), bg="#f5f5f5").pack(pady=10)
        if self.product_type == "Liquid":
            tk.Label(scrollable_frame, text=f"Bottle Size: {self.size_or_capsule}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
            tk.Label(scrollable_frame, text=f"Serving Size: {self.serving_size}", font=("Segoe UI", 12), bg="#f5f5f5").pack()
            tk.Label(scrollable_frame, text=f"Number of Bottles: {self.quantity}", font=("Segoe UI", 12), bg="#f5f5f5").pack()

        ingr_name_var = tk.StringVar()
        per_unit_var = tk.DoubleVar()
        self.custom_ingredients = []

        def update_suggestions(*args):
            typed = ingr_name_var.get().strip().lower()
            suggestion_box.delete(0, tk.END)
            if len(typed) >= 1:
                for ingr in self.ingredient_list:
                    if typed in ingr.lower():
                        suggestion_box.insert(tk.END, ingr)

        def on_select(event):
            try:
                selected_index = suggestion_box.curselection()[0]
                selected = suggestion_box.get(selected_index)
                ingr_name_var.set(selected)
            except (IndexError, tk.TclError):
                pass

        def validate_ingredient_input():
            name = ingr_name_var.get().strip()
            try:
                per_unit_mg = per_unit_var.get()
            except tk.TclError:
                raise ValueError("Please enter a valid quantity")

            if not name:
                raise ValueError("Ingredient name cannot be empty.")
            if per_unit_mg <= 0:
                raise ValueError("Quantity per unit must be a positive number.")
            if name not in self.ingredient_list:
                raise ValueError("Ingredient not found in database.")

            return name, per_unit_mg

        def add_ingredient():
            try:
                name, per_unit_mg = validate_ingredient_input()

                if self.product_type == "Liquid":
                    try:
                        bottle_size_ml = float(self.size_or_capsule.replace(" ml", ""))
                        serving_size_ml = float(self.serving_size.replace(" ml", "")) if self.serving_size else 1.0
                        if serving_size_ml <= 0:
                            raise ValueError("Invalid serving size")

                        num_servings_per_bottle = bottle_size_ml / serving_size_ml
                        total_qty_mg = per_unit_mg * num_servings_per_bottle * self.quantity
                        qty_kg = total_qty_mg / 1000000
                        display_qty = f"{total_qty_mg:.2f} mg (per {self.serving_size})"
                    except (ValueError, AttributeError) as e:
                        raise ValueError(f"Error calculating liquid quantities: {str(e)}")
                else: # Tablet or Capsule
                    total_qty_mg = per_unit_mg * self.quantity
                    qty_kg = total_qty_mg / 1000000
                    display_qty = f"{total_qty_mg:.2f} mg"
                self.custom_ingredients.append({"name": name, "qty": qty_kg, "display_qty": display_qty})
                ingr_listbox.insert(tk.END, f"{name} - {display_qty} ({per_unit_mg} mg per {self.product_type if self.product_type != 'Liquid' else self.serving_size})")
                ingr_name_var.set("")
                per_unit_var.set(0.0)
                suggestion_box.delete(0, tk.END)
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

        def remove_selected_ingredient():
            try:
                selected_index = ingr_listbox.curselection()[0]
                ingr_listbox.delete(selected_index)
                del self.custom_ingredients[selected_index]
            except (IndexError, tk.TclError):
                messagebox.showwarning("Selection Error", "Please select an ingredient to remove.")

        def add_new_ingredient():
            dialog = tk.Toplevel(self.root)
            dialog.title("Add New Ingredient")
            dialog.geometry("400x300")
            dialog.configure(bg="#f5f5f5")
            dialog.transient(self.root)
            dialog.grab_set()
            tk.Label(dialog, text="Ingredient Name:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(pady=10)
            name_var = tk.StringVar()
            tk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 12), width=25).pack(pady=5)
            tk.Label(dialog, text="Rate (per kg):", bg="#f5f5f5", font=("Segoe UI", 12)).pack(pady=10)
            rate_var = tk.DoubleVar()
            tk.Entry(dialog, textvariable=rate_var, font=("Segoe UI", 12), width=25).pack(pady=5)

            def save_new_ingredient():
                name = name_var.get().strip()
                try:
                    rate = rate_var.get()
                    if not name:
                        raise ValueError("Name cannot be empty")
                    if rate <= 0:
                        raise ValueError("Rate must be a positive number")
                    if name in self.ingredient_list:
                        raise ValueError("This ingredient already exists")

                    self.ingredient_list.append(name)
                    self.rate_dict[name] = rate

                    try:
                        df = pd.DataFrame(list(self.rate_dict.items()), columns=["Ingredient", "Rate"])
                        df.to_excel(self.rate_file_path, index=False, header=False)
                        messagebox.showinfo("Success", f"Added {name} to database")
                    except Exception as file_error:
                        messagebox.showwarning("File Warning", f"Ingredient added to current session but could not update file: {str(file_error)}")

                    dialog.destroy()
                except ValueError as e:
                    messagebox.showerror("Input Error", str(e))
                except tk.TclError:
                    messagebox.showerror("Input Error", "Please enter a valid rate")

            def cancel_dialog():
                dialog.destroy()

            button_frame = tk.Frame(dialog, bg="#f5f5f5")
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Save", command=save_new_ingredient, width=15).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel_dialog, width=15).pack(side=tk.LEFT, padx=5)

        ingr_name_var.trace("w", update_suggestions)

        tk.Label(scrollable_frame, text="Ingredient Name:", font=("Segoe UI", 12), bg="#f5f5f5").pack(pady=5)
        ingr_entry = tk.Entry(scrollable_frame, textvariable=ingr_name_var, font=("Segoe UI", 12), width=30)
        ingr_entry.pack(pady=5)
        ingr_entry.bind('<Return>', lambda e: add_ingredient())
        suggestion_box = tk.Listbox(scrollable_frame, height=5, width=40, font=("Segoe UI", 12))
        suggestion_box.pack(pady=5)
        suggestion_box.bind("<<ListboxSelect>>", on_select)
        tk.Label(scrollable_frame, text=f"Quantity per {self.product_type if self.product_type != 'Liquid' else self.serving_size} (mg):", font=("Segoe UI", 12), bg="#f5f5f5").pack(pady=5)
        qty_entry = tk.Entry(scrollable_frame, textvariable=per_unit_var, font=("Segoe UI", 12), width=15)
        qty_entry.pack(pady=5)
        qty_entry.bind('<Return>', lambda e: add_ingredient())
        button_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add Ingredient", command=add_ingredient, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=remove_selected_ingredient, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add New to Database", command=add_new_ingredient, width=20).pack(side=tk.LEFT, padx=5)
        tk.Label(scrollable_frame, text="Added Ingredients:", font=("Segoe UI", 12, "bold"), bg="#f5f5f5").pack(pady=10)
        ingr_listbox = tk.Listbox(scrollable_frame, height=8, width=50, font=("Segoe UI", 12))
        ingr_listbox.pack(pady=10)
        ttk.Button(scrollable_frame, text="Finish & Select Packaging", command=self.show_step4_window, width=25).pack(pady=20)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

    def show_step4_window(self):
        self.clear_frame()
        self.current_step = "step4"

        canvas = tk.Canvas(self.main_frame, bg="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.main_frame, text="Back", command=self.go_back).place(x=10, y=10)

        tk.Label(scrollable_frame, text="Select Packaging Types:", font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack(pady=20)

        # Initialize packaging variables
        self.bottle_type_var = tk.StringVar()
        self.ropp_type_var = tk.StringVar()
        self.include_measuring_cup_var = tk.BooleanVar(value=True)
        self.carton_type_var = tk.StringVar()
        self.label_type_var = tk.StringVar()
        self.shipper_capacity_var = tk.StringVar()
        self.shipper_ply_var = tk.StringVar()
        self.include_accessories_var = tk.BooleanVar(value=False)

        # Initialize tablet/capsule packaging variables
        self.primary_packaging_type = tk.StringVar(value="STRIP")
        self.material_type = tk.StringVar(value="350 GSM")
        self.secondary_size = tk.StringVar(value="1*10")
        self.tertiary_packaging_type = tk.StringVar(value="5 PLY")
        self.jar_type = tk.StringVar(value="PET")
        self.cap_type = tk.StringVar(value="CRC")
        self.sticker_laser = tk.BooleanVar()
        self.tablets_per_jar = tk.IntVar(value=60)
        self.strip_type = tk.StringVar(value="Alu Alu")
        self.strip_size = tk.StringVar(value="1*10")
        self.loose_packaging_type = tk.StringVar(value="aluminum pouch")
        self.tablets_per_loose = tk.IntVar(value=60)
        self.secondary_packaging_method = tk.StringVar(value="Individual Carton")
        self.include_primary_var = tk.BooleanVar(value=True)
        self.include_secondary_var = tk.BooleanVar(value=True)
        self.include_tertiary_var = tk.BooleanVar(value=True)
        self.include_cellotape_var = tk.BooleanVar(value=True)

        tablet_packaging_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        liquid_packaging_frame_100ml = tk.Frame(scrollable_frame, bg="#f5f5f5")
        liquid_packaging_frame_200ml = tk.Frame(scrollable_frame, bg="#f5f5f5")
        no_packaging_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        tk.Label(no_packaging_frame, text="Detailed packaging options are only available for the 100 ml and 200 ml bottle sizes.", font=("Segoe UI", 12, "italic"), bg="#f5f5f5").pack(pady=20)

        # Liquid packaging options for 100 ml
        tk.Label(liquid_packaging_frame_100ml, text="Bottle Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w")
        bottle_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        bottle_frame_100ml.pack(fill="x", padx=20)
        tk.Radiobutton(bottle_frame_100ml, text=f"round brute (₹{self.liquid_packaging_costs['Bottle type']['100ml']['round brute']})", variable=self.bottle_type_var, value="round brute", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(bottle_frame_100ml, text=f"brute (₹{self.liquid_packaging_costs['Bottle type']['100ml']['brute']})", variable=self.bottle_type_var, value="brute", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(bottle_frame_100ml, text=f"dome (₹{self.liquid_packaging_costs['Bottle type']['100ml']['dome']})", variable=self.bottle_type_var, value="dome", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.bottle_type_var.set("round brute")

        tk.Label(liquid_packaging_frame_100ml, text="ROPP Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        ropp_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        ropp_frame_100ml.pack(fill="x", padx=20)
        tk.Radiobutton(ropp_frame_100ml, text=f"quality (₹{self.liquid_packaging_costs['ROPP type']['quality']})", variable=self.ropp_type_var, value="quality", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(ropp_frame_100ml, text=f"printed (₹{self.liquid_packaging_costs['ROPP type']['printed']})", variable=self.ropp_type_var, value="printed", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.ropp_type_var.set("quality")

        tk.Label(liquid_packaging_frame_100ml, text="Measuring Cup:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        tk.Checkbutton(liquid_packaging_frame_100ml, text="Include Measuring Cup (₹0.25)", variable=self.include_measuring_cup_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w", padx=20)

        tk.Label(liquid_packaging_frame_100ml, text="Carton:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        carton_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        carton_frame_100ml.pack(fill="x", padx=20)
        tk.Radiobutton(carton_frame_100ml, text=f"uv dripp off (₹{self.liquid_packaging_costs['carton']['100ml']['uv dripp off']})", variable=self.carton_type_var, value="uv dripp off", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(carton_frame_100ml, text=f"metallic (₹{self.liquid_packaging_costs['carton']['100ml']['metallic']})", variable=self.carton_type_var, value="metallic", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.carton_type_var.set("uv dripp off")

        tk.Label(liquid_packaging_frame_100ml, text="Label:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        label_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        label_frame_100ml.pack(fill="x", padx=20)
        tk.Radiobutton(label_frame_100ml, text=f"chromo (₹{self.liquid_packaging_costs['label']['chromo']})", variable=self.label_type_var, value="chromo", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(label_frame_100ml, text=f"metallic (₹{self.liquid_packaging_costs['label']['metallic']})", variable=self.label_type_var, value="metallic", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.label_type_var.set("chromo")

        tk.Label(liquid_packaging_frame_100ml, text="Shipper:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        shipper_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        shipper_frame_100ml.pack(fill="x", padx=20)

        self.shipper_capacity_var.set("100 nos")
        tk.Label(shipper_frame_100ml, text="100 nos capacity:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(shipper_frame_100ml, text=f"5 ply (₹{self.liquid_packaging_costs['shipper']['100ml']['100 nos']['5ply']} per 100 bottles)", variable=self.shipper_ply_var, value="5ply", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w", padx=20)
        tk.Radiobutton(shipper_frame_100ml, text=f"7 ply (₹{self.liquid_packaging_costs['shipper']['100ml']['100 nos']['7ply']} per 100 bottles)", variable=self.shipper_ply_var, value="7ply", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w", padx=20)
        self.shipper_ply_var.set("5ply")

        tk.Label(liquid_packaging_frame_100ml, text="Accessories:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        accessories_frame_100ml = tk.Frame(liquid_packaging_frame_100ml, bg="#f5f5f5")
        accessories_frame_100ml.pack(fill="x", padx=20)
        tk.Checkbutton(accessories_frame_100ml, text="Include Accessories (cello tape, wrapping, shrinking) (₹0.5)", variable=self.include_accessories_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")

        # Liquid packaging options for 200 ml
        tk.Label(liquid_packaging_frame_200ml, text="Bottle Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w")
        bottle_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        bottle_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(bottle_frame_200ml, text=f"brute (₹{self.liquid_packaging_costs['Bottle type']['200ml']['brute']})", variable=self.bottle_type_var, value="brute", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(bottle_frame_200ml, text=f"micro brute (₹{self.liquid_packaging_costs['Bottle type']['200ml']['micro brute']})", variable=self.bottle_type_var, value="micro brute", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(bottle_frame_200ml, text=f"glo back (₹{self.liquid_packaging_costs['Bottle type']['200ml']['glo back']})", variable=self.bottle_type_var, value="glo back", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.bottle_type_var.set("brute")

        tk.Label(liquid_packaging_frame_200ml, text="ROPP Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        ropp_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        ropp_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(ropp_frame_200ml, text=f"quality (₹{self.liquid_packaging_costs['ROPP type']['quality']})", variable=self.ropp_type_var, value="quality", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(ropp_frame_200ml, text=f"printed (₹{self.liquid_packaging_costs['ROPP type']['printed']})", variable=self.ropp_type_var, value="printed", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.ropp_type_var.set("quality")

        tk.Label(liquid_packaging_frame_200ml, text="Measuring Cup:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        tk.Checkbutton(liquid_packaging_frame_200ml, text="Include Measuring Cup (₹0.25)", variable=self.include_measuring_cup_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w", padx=20)

        tk.Label(liquid_packaging_frame_200ml, text="Carton:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        carton_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        carton_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(carton_frame_200ml, text="uv dripp off", variable=self.carton_type_var, value="uv dripp off", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(carton_frame_200ml, text="metallic", variable=self.carton_type_var, value="metallic", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.carton_type_var.set("uv dripp off")

        self.carton_price_label_200ml = tk.Label(carton_frame_200ml, text="", bg="#f5f5f5", font=("Segoe UI", 10, "italic"))
        self.carton_price_label_200ml.pack(anchor="w", padx=20)

        def update_carton_price_200ml(*args):
            bottle_type = self.bottle_type_var.get()
            carton_type = self.carton_type_var.get()
            if carton_type and bottle_type:
                if bottle_type == "micro brute":
                    price = self.liquid_packaging_costs['carton']['200ml'][carton_type]['micro brute']
                else:
                    price = self.liquid_packaging_costs['carton']['200ml'][carton_type]['default']
                self.carton_price_label_200ml.config(text=f"Price: ₹{price}")

        self.bottle_type_var.trace("w", update_carton_price_200ml)
        self.carton_type_var.trace("w", update_carton_price_200ml)

        tk.Label(liquid_packaging_frame_200ml, text="Label:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        label_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        label_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(label_frame_200ml, text=f"chromo (₹{self.liquid_packaging_costs['label']['chromo']})", variable=self.label_type_var, value="chromo", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(label_frame_200ml, text=f"metallic (₹{self.liquid_packaging_costs['label']['metallic']})", variable=self.label_type_var, value="metallic", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.label_type_var.set("chromo")

        tk.Label(liquid_packaging_frame_200ml, text="Shipper:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        shipper_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        shipper_frame_200ml.pack(fill="x", padx=20)

        tk.Label(shipper_frame_200ml, text="Capacity:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        capacity_frame_200ml = tk.Frame(shipper_frame_200ml, bg="#f5f5f5")
        capacity_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(capacity_frame_200ml, text="72 nos", variable=self.shipper_capacity_var, value="72 nos", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(capacity_frame_200ml, text="60 nos", variable=self.shipper_capacity_var, value="60 nos", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.shipper_capacity_var.set("72 nos")

        tk.Label(shipper_frame_200ml, text="Ply Type:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w", pady=(10,0))
        ply_frame_200ml = tk.Frame(shipper_frame_200ml, bg="#f5f5f5")
        ply_frame_200ml.pack(fill="x", padx=20)
        tk.Radiobutton(ply_frame_200ml, text="5 ply", variable=self.shipper_ply_var, value="5ply", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(ply_frame_200ml, text="7 ply", variable=self.shipper_ply_var, value="7ply", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.shipper_ply_var.set("5ply")

        self.shipper_price_label_200ml = tk.Label(ply_frame_200ml, text="", bg="#f5f5f5", font=("Segoe UI", 10, "italic"))
        self.shipper_price_label_200ml.pack(anchor="w", padx=20)

        def update_shipper_price_200ml(*args):
            capacity = self.shipper_capacity_var.get()
            ply = self.shipper_ply_var.get()
            if capacity and ply:
                price = self.liquid_packaging_costs['shipper']['200ml'][capacity][ply]
                capacity_num = capacity.split()[0]
                self.shipper_price_label_200ml.config(text=f"Price: ₹{price} per {capacity_num} bottles")

        self.shipper_capacity_var.trace("w", update_shipper_price_200ml)
        self.shipper_ply_var.trace("w", update_shipper_price_200ml)

        tk.Label(liquid_packaging_frame_200ml, text="Accessories:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w", pady=(10,0))
        accessories_frame_200ml = tk.Frame(liquid_packaging_frame_200ml, bg="#f5f5f5")
        accessories_frame_200ml.pack(fill="x", padx=20)
        tk.Checkbutton(accessories_frame_200ml, text="Include Accessories (cello tape, wrapping, shrinking) (₹0.5)", variable=self.include_accessories_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")

        # Initialize dynamic displays
        update_carton_price_200ml()
        update_shipper_price_200ml()

        # Tablet/Capsule packaging options
        primary_packaging_frame = tk.LabelFrame(tablet_packaging_frame, text="Primary Packaging", bg="#f5f5f5", font=("Segoe UI", 12, "bold"))
        primary_packaging_frame.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(primary_packaging_frame, text="Include Primary Packaging", variable=self.include_primary_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(primary_packaging_frame, text="JAR", variable=self.primary_packaging_type, value="JAR", bg="#f5f5f5", command=lambda: show_jar_options(), font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(primary_packaging_frame, text="STRIP", variable=self.primary_packaging_type, value="STRIP", bg="#f5f5f5", command=lambda: show_strip_options(), font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(primary_packaging_frame, text="LOOSE", variable=self.primary_packaging_type, value="LOOSE", bg="#f5f5f5", command=lambda: show_loose_options(), font=("Segoe UI", 12)).pack(anchor="w")

        jar_frame = tk.Frame(primary_packaging_frame, bg="#f5f5f5")
        tk.Label(jar_frame, text="JAR Type:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(jar_frame, text="PET", variable=self.jar_type, value="PET", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(jar_frame, text="HDPE", variable=self.jar_type, value="HDPE", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Label(jar_frame, text="CAP Type:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(jar_frame, text="CRC", variable=self.cap_type, value="CRC", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(jar_frame, text="CT", variable=self.cap_type, value="CT", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Label(jar_frame, text="Tablets per Jar:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        jar_tablets_entry = tk.Entry(jar_frame, textvariable=self.tablets_per_jar, font=("Segoe UI", 12), width=10)
        jar_tablets_entry.pack(anchor="w")
        tk.Checkbutton(jar_frame, text="Add dual Sticker", variable=self.sticker_laser, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")

        strip_frame = tk.Frame(primary_packaging_frame, bg="#f5f5f5")
        tk.Label(strip_frame, text="Strip Type:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(strip_frame, text="Alu Alu", variable=self.strip_type, value="Alu Alu", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(strip_frame, text="Blister", variable=self.strip_type, value="Blister", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(strip_frame, text="Pharmafoil", variable=self.strip_type, value="Pharmafoil", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Label(strip_frame, text="Strip Size:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        self.strip_size.set("1*10")
        strip_size_menu = ttk.Combobox(strip_frame, textvariable=self.strip_size, values=["1*10", "1*15", "1*4", "1*2"], state="readonly", width=10)
        strip_size_menu.pack(anchor="w")

        loose_frame = tk.Frame(primary_packaging_frame, bg="#f5f5f5")
        tk.Label(loose_frame, text="Loose Packaging Type:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(loose_frame, text="Aluminum Pouch", variable=self.loose_packaging_type, value="aluminum pouch", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(loose_frame, text="Jar", variable=self.loose_packaging_type, value="jar", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(loose_frame, text="Plastic Zip", variable=self.loose_packaging_type, value="plastic zip", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Label(loose_frame, text="Tablets per Loose Packaging:", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        loose_tablets_entry = tk.Entry(loose_frame, textvariable=self.tablets_per_loose, font=("Segoe UI", 12), width=10)
        loose_tablets_entry.pack(anchor="w")

        def show_jar_options():
            strip_frame.pack_forget()
            loose_frame.pack_forget()
            jar_frame.pack(fill="x", padx=20, pady=10)

        def show_strip_options():
            jar_frame.pack_forget()
            loose_frame.pack_forget()
            strip_frame.pack(fill="x", padx=20, pady=10)

        def show_loose_options():
            jar_frame.pack_forget()
            strip_frame.pack_forget()
            loose_frame.pack(fill="x", padx=20, pady=10)

        show_strip_options()

        secondary_packaging_frame = tk.LabelFrame(tablet_packaging_frame, text="Secondary Packaging", bg="#f5f5f5", font=("Segoe UI", 12, "bold"))
        secondary_packaging_frame.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(secondary_packaging_frame, text="Include Secondary Packaging", variable=self.include_secondary_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        method_frame = tk.Frame(secondary_packaging_frame, bg="#f5f5f5")
        method_frame.pack(fill="x", pady=5)
        tk.Label(method_frame, text="Packaging Method:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w")
        tk.Radiobutton(method_frame, text="Individual Carton", variable=self.secondary_packaging_method, value="Individual Carton", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(method_frame, text="Box in Box (10 units per box)", variable=self.secondary_packaging_method, value="Box in Box", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        material_frame = tk.Frame(secondary_packaging_frame, bg="#f5f5f5")
        material_frame.pack(fill="x", pady=5)
        tk.Label(material_frame, text="Material Type:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w")
        tk.Radiobutton(material_frame, text="300 GSM", variable=self.material_type, value="300 GSM", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(material_frame, text="350 GSM", variable=self.material_type, value="350 GSM", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(material_frame, text="Metallic", variable=self.material_type, value="Metallic", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        size_frame = tk.Frame(secondary_packaging_frame, bg="#f5f5f5")
        size_frame.pack(fill="x", pady=10)
        tk.Label(size_frame, text="Size:", font=("Segoe UI", 12), bg="#f5f5f5").pack(anchor="w")
        size_listbox_frame = tk.Frame(size_frame, bg="#f5f5f5")
        size_listbox_frame.pack(fill="x", padx=20)
        size_listbox = tk.Listbox(size_listbox_frame, height=4, width=40, font=("Segoe UI", 12))
        size_scrollbar = tk.Scrollbar(size_listbox_frame, orient="vertical", command=size_listbox.yview)
        size_listbox.config(yscrollcommand=size_scrollbar.set)
        sizes = ["1*10", "1*15", "3*10", "5*10", "6*10", "10*10"]
        for size in sizes:
            size_listbox.insert(tk.END, size)
        size_listbox.pack(side="left", fill="both", expand=True)
        size_scrollbar.pack(side="right", fill="y")

        def update_available_sizes(*args):
            size_listbox.delete(0, tk.END)
            if self.secondary_packaging_method.get() == "Box in Box":
                available_sizes = ["1*10", "3*10", "5*10", "6*10"]
            else:
                available_sizes = ["1*10", "1*15", "3*10", "5*10", "6*10", "10*10"]
            for size in available_sizes:
                size_listbox.insert(tk.END, size)

            if available_sizes:
                size_listbox.selection_set(0)

        def on_size_select(event):
            try:
                selected_index = size_listbox.curselection()[0]
                selected_size = size_listbox.get(selected_index)
                self.secondary_size.set(selected_size)
            except (IndexError, tk.TclError):
                pass

        size_listbox.bind('<<ListboxSelect>>', on_size_select)
        size_listbox.selection_set(0)
        self.secondary_size.set("1*10")
        self.secondary_packaging_method.trace("w", update_available_sizes)

        tertiary_packaging_frame = tk.LabelFrame(tablet_packaging_frame, text="Tertiary Packaging", bg="#f5f5f5", font=("Segoe UI", 12, "bold"))
        tertiary_packaging_frame.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(tertiary_packaging_frame, text="Include Tertiary Packaging", variable=self.include_tertiary_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(tertiary_packaging_frame, text="5 PLY", variable=self.tertiary_packaging_type, value="5 PLY", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Radiobutton(tertiary_packaging_frame, text="7 PLY", variable=self.tertiary_packaging_type, value="7 PLY", bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")
        cellotape_frame = tk.Frame(tablet_packaging_frame, bg="#f5f5f5")
        cellotape_frame.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(cellotape_frame, text="Include Cellotape and Wrapping", variable=self.include_cellotape_var, bg="#f5f5f5", font=("Segoe UI", 12)).pack(anchor="w")

        def on_selection_change():
            liquid_packaging_frame_100ml.pack_forget()
            liquid_packaging_frame_200ml.pack_forget()
            tablet_packaging_frame.pack_forget()
            no_packaging_frame.pack_forget()

            if self.product_type == "Liquid":
                if self.size_or_capsule == "100 ml":
                    liquid_packaging_frame_100ml.pack(pady=10)
                    # Set default shipper values for 100ml
                    self.shipper_capacity_var.set("100 nos")
                    self.shipper_ply_var.set("5ply")
                elif self.size_or_capsule == "200 ml":
                    liquid_packaging_frame_200ml.pack(pady=10)
                    # Set default shipper values for 200ml
                    self.shipper_capacity_var.set("72 nos")
                    self.shipper_ply_var.set("5ply")
                else:
                    no_packaging_frame.pack(pady=10)
            else:
                tablet_packaging_frame.pack(pady=10)

        on_selection_change()

        button_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Calculate & Generate Report", command=self.calculate_and_proceed, width=25).pack()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)

    def _calculate_liquid_packaging_cost(self):
        try:
            bottle_size = "100ml" if self.size_or_capsule == "100 ml" else "200ml"
            bottle_cost = self.liquid_packaging_costs["Bottle type"][bottle_size][self.bottle_type_var.get()]
            ropp_cost = self.liquid_packaging_costs["ROPP type"][self.ropp_type_var.get()]
            measuring_cup_cost = self.liquid_packaging_costs["measuring cup"]["yes"] if self.include_measuring_cup_var.get() else self.liquid_packaging_costs["measuring cup"]["no"]

            carton_type = self.carton_type_var.get()
            
            carton_cost_data = self.liquid_packaging_costs["carton"][bottle_size][carton_type]
            if isinstance(carton_cost_data, dict):
                # This logic is for 200ml bottles, which have nested costs
                bottle_type_for_carton = self.bottle_type_var.get()
                carton_cost = carton_cost_data.get(bottle_type_for_carton, carton_cost_data['default'])
            else:
                # This logic is for 100ml bottles, which have a direct cost
                carton_cost = carton_cost_data
            
            label_cost = self.liquid_packaging_costs["label"][self.label_type_var.get()]
            accessories_cost = self.liquid_packaging_costs["accessories"]["yes"] if self.include_accessories_var.get() else self.liquid_packaging_costs["accessories"]["no"]

            shipper_capacity = self.shipper_capacity_var.get()
            shipper_ply = self.shipper_ply_var.get()
            shipper_cost_per_shipper = self.liquid_packaging_costs["shipper"][bottle_size][shipper_capacity][shipper_ply]
            shipper_capacity_num = int(shipper_capacity.split()[0])

            num_shippers = math.ceil(self.quantity / shipper_capacity_num)
            per_bottle_costs = bottle_cost + ropp_cost + measuring_cup_cost + carton_cost + label_cost + accessories_cost
            total_packaging_cost = (self.quantity * per_bottle_costs) + (num_shippers * shipper_cost_per_shipper)

            calculation_details = (
                "Liquid Packaging Details:\n"
                f"Per Bottle Costs: ₹{per_bottle_costs:.2f} × {self.quantity} bottles = ₹{(self.quantity * per_bottle_costs):.2f}\n"
                f"Shipper Costs: ₹{shipper_cost_per_shipper:.2f} × {num_shippers} shippers = ₹{(num_shippers * shipper_cost_per_shipper):.2f}\n"
                f"Total Liquid Packaging Cost: ₹{total_packaging_cost:.2f}\n"
                "\nIndividual Component Costs (per bottle unless noted):\n"
                f"Bottle Cost: ₹{bottle_cost:.2f}\n"
                f"ROPP Cost: ₹{ropp_cost:.2f}\n"
                f"Measuring Cup Cost: ₹{measuring_cup_cost:.2f}\n"
                f"Carton Cost: ₹{carton_cost:.2f}\n"
                f"Label Cost: ₹{label_cost:.2f}\n"
                f"Accessories Cost: ₹{accessories_cost:.2f}\n"
                f"Shipper Cost: ₹{shipper_cost_per_shipper:.2f} per {shipper_capacity_num} bottles\n"
                f"Number of shippers needed: {num_shippers}\n"
            )

            return total_packaging_cost, calculation_details, num_shippers, bottle_cost, ropp_cost, measuring_cup_cost, carton_cost, label_cost, shipper_cost_per_shipper, accessories_cost

        except Exception as e:
            raise ValueError(f"Error calculating liquid packaging costs: {str(e)}")

    def calculate_and_proceed(self):
        try:
            total_packaging_cost = 0
            secondary_packaging_cost = 0
            tertiary_packaging_cost = 0
            cellotape_wrapping_cost = 0
            total_primary_packaging_cost = 0
            num_jars = 0
            num_strips = 0
            cost_per_strip = 0

            if self.product_type == "Liquid" and self.size_or_capsule in ["100 ml", "200 ml"]:
                (total_packaging_cost, calculation_details, num_shippers, bottle_cost, ropp_cost, measuring_cup_cost,
                 carton_cost, label_cost, shipper_cost, accessories_cost) = self._calculate_liquid_packaging_cost()
            else:
                calculation_details = ""
                num_shippers = 0
                bottle_cost = 0
                ropp_cost = 0
                measuring_cup_cost = 0
                carton_cost = 0
                label_cost = 0
                shipper_cost = 0
                accessories_cost = 0

                if self.include_primary_var.get():
                    if self.primary_packaging_type.get() == "JAR":
                        tablets_per_jar = max(1, self.tablets_per_jar.get())
                        num_jars = math.ceil(self.quantity / tablets_per_jar)
                        jar_cost_per_unit = {"PET": {15: 3.00, 60: 5.30, 180: 6.50, 300: 8.00}, "HDPE": {15: 3.00, 60: 5.50, 180: 7.00, 300: 9.00}}
                        cap_cost_per_unit = {"CRC": 3.50, "CT": 2.00}
                        sticker_cost_per_unit = {15: 2.00, 60: 4.50, 180: 4.85, 300: 7.00}
                        jar_cost_per_jar = jar_cost_per_unit[self.jar_type.get()].get(tablets_per_jar, 5.30)
                        cap_cost_per_jar = cap_cost_per_unit[self.cap_type.get()]
                        sticker_cost_per_jar = sticker_cost_per_unit.get(tablets_per_jar, 4.50)
                        if self.sticker_laser.get():
                            sticker_cost_per_jar += 10.00
                        total_primary_packaging_cost = num_jars * (jar_cost_per_jar + cap_cost_per_jar + sticker_cost_per_jar)
                        calculation_details += f"Primary Packaging: JAR\nNumber of Jars: {num_jars}\nTotal Cost: ₹{total_primary_packaging_cost:.2f}\n"
                    elif self.primary_packaging_type.get() == "STRIP":
                        strip_costs = {"Alu Alu": {"1*10": 1.80, "1*15": 2.20, "1*4": 1.00, "1*2": 1.00}, "Blister": {"1*10": 0.90, "1*15": 1.80, "1*4": 1.25, "1*2": 0.50}, "Pharmafoil": {"1*10": 1.00}}
                        cost_per_strip = strip_costs.get(self.strip_type.get(), {}).get(self.strip_size.get(), 1.00)
                        strip_capacity = int(self.strip_size.get().split('*')[1]) if '*' in self.strip_size.get() else 10
                        num_strips = math.ceil(self.quantity / strip_capacity)
                        total_primary_packaging_cost = num_strips * cost_per_strip
                        calculation_details += f"Primary Packaging: STRIP\nNumber of Strips: {num_strips}\nTotal Cost: ₹{total_primary_packaging_cost:.2f}\n"
                    else: # Loose
                        loose_costs = {"aluminum pouch": 15.00, "jar": 30.00, "plastic zip": 9.00}
                        loose_packaging_cost = loose_costs.get(self.loose_packaging_type.get(), 15.00)
                        tablets_per_loose = max(1, self.tablets_per_loose.get())
                        num_loose = math.ceil(self.quantity / tablets_per_loose)
                        total_primary_packaging_cost = num_loose * loose_packaging_cost
                        calculation_details += f"Primary Packaging: LOOSE\nNumber of units: {num_loose}\nTotal Cost: ₹{total_primary_packaging_cost:.2f}\n"

                if self.include_secondary_var.get():
                    secondary_cost_per_unit = {
                        "Individual Carton_350 GSM 1*10": 3.00, "Individual Carton_350 GSM 1*15": 3.00, "Individual Carton_350 GSM 3*10": 4.00, "Individual Carton_350 GSM 6*10": 5.50, "Individual Carton_350 GSM 5*10": 5.50, "Individual Carton_350 GSM 10*10": 6.50,
                        "Individual Carton_300 GSM 1*10": 2.00, "Individual Carton_300 GSM 1*15": 2.00, "Individual Carton_300 GSM 3*10": 3.00, "Individual Carton_300 GSM 6*10": 5.00, "Individual Carton_300 GSM 5*10": 5.00, "Individual Carton_300 GSM 10*10": 5.75,
                        "Box in Box_350 GSM 1*10": 1.40, "Box in Box_350 GSM 3*10": 1.50, "Box in Box_350 GSM 5*10": 1.80, "Box in Box_350 GSM 6*10": 2.15,
                        "Box in Box_300 GSM 1*10": 1.00, "Box in Box_300 GSM 3*10": 1.30, "Box in Box_300 GSM 5*10": 1.50, "Box in Box_300 GSM 6*10": 1.80,
                        "Box in Box_Metallic 1*10": 1.30, "Box in Box_Metallic 3*10": 1.50, "Box in Box_Metallic 5*10": 1.70, "Box in Box_Metallic 6*10": 2.00
                    }
                    units_needed = num_jars if self.primary_packaging_type.get() == "JAR" else num_strips
                    secondary_key = f"{self.secondary_packaging_method.get()}_{self.material_type.get()} {self.secondary_size.get()}"
                    if self.secondary_packaging_method.get() == "Box in Box":
                        boxes_needed = math.ceil(units_needed / 10)
                        secondary_packaging_cost = boxes_needed * secondary_cost_per_unit.get(secondary_key, 1.00)
                    else:
                        secondary_packaging_cost = units_needed * secondary_cost_per_unit.get(secondary_key, 3.00)
                    calculation_details += f"Secondary Packaging Cost: ₹{secondary_packaging_cost:.2f}\n"

                if self.include_tertiary_var.get():
                    tertiary_cost_per_unit = {"5 PLY": 0.30, "7 PLY": 0.40}
                    units_needed = num_jars if self.primary_packaging_type.get() == "JAR" else num_strips
                    tertiary_packaging_cost = units_needed * tertiary_cost_per_unit.get(self.tertiary_packaging_type.get(), 0.30)
                    calculation_details += f"Tertiary Packaging Cost: ₹{tertiary_packaging_cost:.2f}\n"

                if self.include_cellotape_var.get():
                    cellotape_wrapping_cost_per_unit = 0.50
                    units_needed = num_jars if self.primary_packaging_type.get() == "JAR" else num_strips
                    cellotape_wrapping_cost = units_needed * cellotape_wrapping_cost_per_unit
                    calculation_details += f"Cellotape and Wrapping Cost: ₹{cellotape_wrapping_cost:.2f}\n"

                total_packaging_cost = total_primary_packaging_cost + secondary_packaging_cost + tertiary_packaging_cost + cellotape_wrapping_cost

            self.show_output_window(
                total_packaging_cost, total_primary_packaging_cost, secondary_packaging_cost,
                tertiary_packaging_cost, cellotape_wrapping_cost, calculation_details,
                num_jars, num_strips, cost_per_strip, bottle_cost, ropp_cost,
                measuring_cup_cost, carton_cost, label_cost, shipper_cost, accessories_cost, num_shippers
            )

        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred during calculation: {str(e)}")

    def show_output_window(self, total_packaging_cost, total_primary_packaging_cost, secondary_packaging_cost, tertiary_packaging_cost, cellotape_wrapping_cost, calculation_details, num_jars, num_strips, cost_per_strip, bottle_cost, ropp_cost, measuring_cup_cost, carton_cost, label_cost, shipper_cost, accessories_cost, num_shippers):
        self.clear_frame()
        self.current_step = "output"

        canvas = tk.Canvas(self.main_frame, bg="#f5f5f5")
        scrollbar_y = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.main_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        ttk.Button(self.main_frame, text="Back", command=self.go_back).place(x=10, y=10)

        header_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        header_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(header_frame, text="BATCH MASTER CARD", font=("Segoe UI", 18, "bold"), bg="#f5f5f5").pack()

        info_frame = tk.Frame(header_frame, bg="#f5f5f5")
        info_frame.pack(fill="x", pady=10)
        if self.product_type == "Tablet":
            tk.Label(info_frame, text=f"Tablet Size: {self.size_or_capsule} mg", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left")
        elif self.product_type == "Liquid":
            tk.Label(info_frame, text=f"Product Type: Liquid", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left")
            tk.Label(info_frame, text=f"Bottle Size: {self.size_or_capsule}", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left", padx=20)
            tk.Label(info_frame, text=f"Number of Bottles: {self.quantity}", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left", padx=20)
            tk.Label(info_frame, text=f"Serving Size: {self.serving_size}", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left", padx=20)
        else:
            tk.Label(info_frame, text=f"Capsule Size: {self.size_or_capsule}", font=("Segoe UI", 12), bg="#f5f5f5").pack(side="left")

        tree_frame = tk.Frame(scrollable_frame)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Sr No", "Ingredient", "Other Name", "Type", "Qty (Kg)", "Qty (g)", "Qty (mg)", "Qty per Unit", "Rate", "Cost", "Active Ingredient Cost")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=30)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        row_index = 1
        total_cost = 0
        total_qty_kg = 0
        active_ingredients_cost = 0
        other_ingredients_cost = 0

        try:
            tree.insert("", "end", values=("", "A. ACTIVE INGREDIENTS", "", "", "", "", "", "", "", "", ""), tags=("group",))

            if self.product_type == "Liquid":
                scale_factor_liquid = self.quantity / 1000
                for item in self.custom_ingredients:
                    name = item['name']
                    qty_kg = item['qty']
                    qty_g = qty_kg * 1000
                    qty_mg = qty_kg * 1000000
                    rate = self.rate_dict.get(name, 0)
                    cost = qty_kg * rate

                    try:
                        serving_ml = float(self.serving_size.replace(" ml", ""))
                        bottle_ml = float(self.size_or_capsule.replace(" ml", ""))
                        total_servings = self.quantity * (bottle_ml / serving_ml) if serving_ml > 0 else 0
                        qty_per_serving_mg = (qty_mg / total_servings) if total_servings > 0 else 0
                        qty_per_unit_display = f"{qty_per_serving_mg:.2f} mg"
                        per_bottle_cost = (cost / self.quantity) if self.quantity > 0 else 0
                        per_serving_cost = (cost / total_servings) if total_servings > 0 else 0
                    except (ValueError, IndexError, ZeroDivisionError):
                        qty_per_unit_display = ""
                        per_bottle_cost = 0
                        per_serving_cost = 0

                    active_ingredient_cost_display = f"₹{per_bottle_cost:.2f} per bottle / ₹{per_serving_cost:.2f} per serving"
                    tree.insert("", "end", values=(row_index, name, name, "Extract", f"{qty_kg:.6f}", f"{qty_g:.3f}", f"{qty_mg:.2f}", qty_per_unit_display, rate, f"{cost:.2f}", active_ingredient_cost_display))
                    total_cost += cost
                    total_qty_kg += qty_kg
                    active_ingredients_cost += cost
                    row_index += 1

                tree.insert("", "end", values=("", "B. OTHER INGREDIENTS", "", "", "", "", "", "", "", "", ""), tags=("group",))
                for ingredient in self.predefined_liquid_other_ingredients:
                    name = ingredient["name"]
                    qty_per_1000 = ingredient["qty_per_1000_bottles_kg"]
                    rate = ingredient["rate"]
                    qty_kg = qty_per_1000 * scale_factor_liquid
                    qty_g = qty_kg * 1000
                    qty_mg = qty_g * 1000

                    cost = qty_kg * rate

                    try:
                        serving_ml = float(self.serving_size.replace(" ml", ""))
                        bottle_ml = float(self.size_or_capsule.replace(" ml", ""))
                        total_servings = self.quantity * (bottle_ml / serving_ml) if serving_ml > 0 else 0
                        qty_per_serving_mg = (qty_mg / total_servings) if total_servings > 0 else 0
                        qty_per_unit_display = f"{qty_per_serving_mg:.2f} mg"
                    except (ValueError, IndexError, ZeroDivisionError):
                        qty_per_unit_display = ""

                    tree.insert("", "end", values=(row_index, name, ingredient['other'], ingredient['type'], f"{qty_kg:.6f}", f"{qty_g:.3f}", f"{qty_mg:.2f}", qty_per_unit_display, rate, f"{cost:.2f}", ""))
                    total_cost += cost
                    other_ingredients_cost += cost
                    total_qty_kg += qty_kg
                    row_index += 1

                # DM Water calculation and display
                try:
                    bottle_ml = float(self.size_or_capsule.replace(" ml", ""))
                    total_volume_L = (self.quantity * bottle_ml) / 1000
                    dm_water_cost = total_volume_L * 1.00 # ₹1 per liter

                    tree.insert("", "end", values=(
                        row_index, "D.M. Water", "D.M. Water", "Liquid",
                        f"{total_volume_L:.3f}", f"{total_volume_L*1000:.1f}", f"{total_volume_L*1000000:.0f}",
                        "", 1.00, f"{dm_water_cost:.2f}", "DM Water Cost (₹1/L)"
                    ))
                    total_cost += dm_water_cost
                    other_ingredients_cost += dm_water_cost
                    total_qty_kg += total_volume_L
                    row_index += 1
                except (ValueError, IndexError):
                    pass

            else: # Tablet or Capsule
                scale_factor = self.quantity / 100

                added_groups = set()
                for name, other, typ, qty_per_100, rate, group in self.selected_excipients:
                    if group not in added_groups:
                        tree.insert("", "end", values=("", group, "", "", "", "", "", "", "", "", ""), tags=("group",))
                        added_groups.add(group)

                    qty_kg = qty_per_100 * scale_factor
                    qty_g = qty_kg * 1000
                    qty_mg = qty_kg * 1000000
                    cost = qty_kg * rate
                    qty_per_unit_display = f"{qty_mg / self.quantity:.2f} mg" if self.quantity > 0 else "0.00 mg"
                    tree.insert("", "end", values=(row_index, name, other, typ, f"{qty_kg:.6f}", f"{qty_g:.3f}", f"{qty_mg:.2f}", qty_per_unit_display, rate, f"{cost:.2f}", ""))
                    total_cost += cost
                    total_qty_kg += qty_kg
                    other_ingredients_cost += cost
                    row_index += 1

                for idx, item in enumerate(self.custom_ingredients, start=row_index):
                    name = item['name']
                    qty_kg = item['qty']
                    qty_g = qty_kg * 1000
                    qty_mg = qty_kg * 1000000
                    rate = self.rate_dict.get(name, 0)
                    cost = qty_kg * rate
                    qty_per_unit_display = f"{qty_mg / self.quantity:.2f} mg" if self.quantity > 0 else "0.00 mg"
                    active_ingredient_cost_display = f"₹{cost / self.quantity:.2f} per {self.product_type}" if self.quantity > 0 else "0.00 per unit"
                    tree.insert("", "end", values=(idx, name, name, "Extract", f"{qty_kg:.6f}", f"{qty_g:.3f}", f"{qty_mg:.2f}", qty_per_unit_display, rate, f"{cost:.2f}", active_ingredient_cost_display))
                    total_cost += cost
                    total_qty_kg += qty_kg
                    active_ingredients_cost += cost
                    row_index += 1

            sugar_cost = 0
            sorbitol_cost = 0
            if self.product_type == "Liquid":
                if self.sugar_type == "Sugar" and self.sugar_percent:
                    sugar_cost = self.sugar_cost_mapping.get(self.sugar_percent, 0) * (self.quantity / 100)
                    tree.insert("", "end", values=(row_index, "Sugar", "Sugar", "Powder", "0", "0", "0", f"{self.sugar_percent} per bottle", f"{self.sugar_cost_mapping.get(self.sugar_percent, 0)}", f"{sugar_cost:.2f}", ""))
                    total_cost += sugar_cost
                    other_ingredients_cost += sugar_cost
                    row_index += 1
                if self.sugar_type == "Sorbitol" and self.sugar_percent:
                    sorbitol_cost = self.sorbitol_cost_mapping.get(self.sugar_percent, 0) * (self.quantity / 100)
                    tree.insert("", "end", values=(row_index, "Sorbitol", "Sorbitol", "Powder", "0", "0", "0", f"{self.sugar_percent} per bottle", f"{self.sorbitol_cost_mapping.get(self.sugar_percent, 0)}", f"{sorbitol_cost:.2f}", ""))
                    total_cost += sorbitol_cost
                    other_ingredients_cost += sorbitol_cost
                    row_index += 1

            capsule_cost = 0.0
            if self.product_type == "Capsule" and self.capsule_types:
                if self.capsule_types == "DR":
                    capsule_unit_cost = self.capsule_pricing.get("DR", 0.0)
                else:
                    capsule_unit_cost = self.capsule_pricing.get(self.size_or_capsule, {}).get(self.capsule_types, 0.0)
                capsule_cost = self.quantity * capsule_unit_cost
                tree.insert("", "end", values=(row_index, "Capsule Shell", "Capsule", "Veg/Non-Veg", "0", "0", "0", f"1 per {self.product_type}", capsule_unit_cost, f"{capsule_cost:.2f}", "Capsule Cost"))
                total_cost += capsule_cost
                other_ingredients_cost += capsule_cost
                row_index += 1

            total_mg = total_qty_kg * 1000000
            tree.insert("", "end", values=("", "TOTAL", "", "", f"{total_qty_kg:.6f}", f"{total_qty_kg*1000:.1f}", f"{total_mg:.2f}", "", "", f"{total_cost:.2f}", ""), tags=("total",))
            tree.tag_configure("group", background="#e0e0e0", font=("Segoe UI", 10, "bold"))
            tree.tag_configure("total", background="#d0f0d0", font=("Segoe UI", 10, "bold"))

            cost_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
            cost_frame.pack(fill="x", padx=20, pady=10)
            left_frame = tk.Frame(cost_frame, bg="#f5f5f5")
            left_frame.pack(side="left", fill="y", padx=20, pady=10)
            cost_details_frame = tk.Frame(cost_frame, bg="#f5f5f5")
            cost_details_frame.pack(side="right")

            conversion_cost = (self.quantity / 10) * 2.5
            total_cost_with_packaging = total_cost + total_packaging_cost
            total_cost_with_conversion = total_cost_with_packaging + conversion_cost
            profit_margin = 0.20 * total_cost_with_conversion
            total_cost_with_profit = total_cost_with_conversion + profit_margin

            if num_strips > 0:
                profit_per_strip = total_cost_with_profit / num_strips if num_strips > 0 else 0
                tk.Label(left_frame, text=f"Final price per Strip: ₹{profit_per_strip:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="red").pack(anchor="w")
            if num_jars > 0:
                profit_per_jar = total_cost_with_profit / num_jars if num_jars > 0 else 0
                tk.Label(left_frame, text=f"Final price per Jar: ₹{profit_per_jar:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="red").pack(anchor="w")
            if self.product_type == "Liquid" and self.quantity > 0:
                cost_per_bottle = total_cost_with_profit / self.quantity
                tk.Label(left_frame, text=f"Cost per Bottle: ₹{cost_per_bottle:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="red").pack(anchor="w")

            tk.Label(cost_details_frame, text=f"Active Ingredients Cost: ₹{active_ingredients_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="blue").pack(anchor="e")
            tk.Label(cost_details_frame, text=f"Other Ingredients Cost: ₹{other_ingredients_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="orange").pack(anchor="e")

            if self.product_type == "Liquid" and self.size_or_capsule in ["100 ml", "200 ml"]:
                tk.Label(cost_details_frame, text=f"Total Packaging Cost: ₹{total_packaging_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="purple").pack(anchor="e")
                tk.Label(cost_details_frame, text=f"Bottle Cost: ₹{self.quantity * bottle_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"ROPP Cost: ₹{self.quantity * ropp_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"Measuring Cup Cost: ₹{self.quantity * measuring_cup_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"Carton Cost: ₹{self.quantity * carton_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"Label Cost: ₹{self.quantity * label_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"Shipper Cost: ₹{num_shippers * shipper_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
                tk.Label(cost_details_frame, text=f"Accessories Cost: ₹{num_shippers * accessories_cost:.2f}", font=("Segoe UI", 10), bg="#f5f5f5", fg="purple").pack(anchor="e", padx=20)
            elif self.product_type == "Liquid" and self.size_or_capsule not in ["100 ml", "200 ml"]:
                tk.Label(cost_details_frame, text="Packaging costs not calculated for this bottle size.", font=("Segoe UI", 10, "italic"), bg="#f5f5f5", fg="gray").pack(anchor="e", pady=10)
            else:
                tk.Label(cost_details_frame, text=f"Primary Packaging Cost: ₹{total_primary_packaging_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="purple").pack(anchor="e")
                tk.Label(cost_details_frame, text=f"Secondary Packaging Cost: ₹{secondary_packaging_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="purple").pack(anchor="e")
                tk.Label(cost_details_frame, text=f"Tertiary Packaging Cost: ₹{tertiary_packaging_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="purple").pack(anchor="e")
                tk.Label(cost_details_frame, text=f"Cellotape and Wrapping Cost: ₹{cellotape_wrapping_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="purple").pack(anchor="e")

            if self.product_type == "Capsule" and capsule_cost > 0:
                tk.Label(cost_details_frame, text=f"Capsule Cost: ₹{capsule_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
            if self.product_type == "Liquid":
                if self.sugar_type == "Sugar" and sugar_cost > 0:
                    tk.Label(cost_details_frame, text=f"Sugar Cost: ₹{sugar_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
                if self.sugar_type == "Sorbitol" and sorbitol_cost > 0:
                    tk.Label(cost_details_frame, text=f"Sorbitol Cost: ₹{sorbitol_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")

            tk.Label(cost_details_frame, text=f"Conversion: ₹{conversion_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
            tk.Label(cost_details_frame, text=f"Total Ingredient Cost: ₹{total_cost:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
            tk.Label(cost_details_frame, text=f"Total Cost (Incl. Packaging & Conversion): ₹{total_cost_with_conversion:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
            tk.Label(cost_details_frame, text=f"Profit Margin (20%): ₹{profit_margin:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")
            tk.Label(cost_details_frame, text=f"Total Batch Cost with Profit: ₹{total_cost_with_profit:.2f}", font=("Segoe UI", 14, "bold"), bg="#f5f5f5", fg="green").pack(anchor="e")

            if self.product_type == "Liquid":
                liquid_cost_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
                liquid_cost_frame.pack(fill="x", padx=20, pady=5)
                if self.quantity > 0:
                    cost_per_bottle = total_cost_with_profit / self.quantity
                    tk.Label(liquid_cost_frame, text=f"Cost per Bottle: ₹{cost_per_bottle:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="red").pack(anchor="w")
                try:
                    serving_ml = float(self.serving_size.replace(" ml", ""))
                    bottle_ml = float(self.size_or_capsule.replace(" ml", ""))
                    total_servings = self.quantity * (bottle_ml / serving_ml)
                    if total_servings > 0:
                        cost_per_serving = total_cost_with_profit / total_servings
                        tk.Label(liquid_cost_frame, text=f"Cost per Serving ({self.serving_size}): ₹{cost_per_serving:.2f}", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="red").pack(anchor="w")
                except (ValueError, IndexError, ZeroDivisionError):
                    pass

            if self.product_type == "Liquid":
                other_ingredients_label_text = "Other Ingredients (Excipients + Water) Cost:"
                other_ingredients_cost_display = f"₹{other_ingredients_cost:.2f}"
                tk.Label(cost_details_frame, text=other_ingredients_label_text, font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="orange").pack(anchor="e", pady=(10, 0))
                tk.Label(cost_details_frame, text=other_ingredients_cost_display, font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="orange").pack(anchor="e", padx=20)

            calc_frame = tk.LabelFrame(scrollable_frame, text="Detailed Calculations", bg="#f5f5f5", font=("Segoe UI", 12, "bold"))
            calc_frame.pack(fill="both", expand=True, padx=20, pady=10)
            calc_text = tk.Text(calc_frame, height=15, width=100, wrap=tk.WORD, font=("Segoe UI", 12))
            calc_text.pack(fill="both", expand=True, padx=10, pady=10)
            calc_text.insert(tk.END, calculation_details)
            calc_text.config(state=tk.DISABLED)

            def download_excel():
                try:
                    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                    if not file_path:
                        return
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Batch Master Card"
                    headers = ["Sr No", "Ingredient", "Other Name", "Type", "Qty (Kg)", "Qty (g)", "Qty (mg)", "Qty per Unit", "Rate", "Cost", "Active Ingredient Cost"]
                    for col_num, header in enumerate(headers, 1):
                        cell = ws.cell(row=1, column=col_num, value=header)
                        cell.font = Font(bold=True)
                        cell.alignment = Alignment(horizontal="center")
                        cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                    row_num = 2
                    for item in tree.get_children():
                        values = tree.item(item, 'values')
                        if values and values[0] != "":
                            for col_num, value in enumerate(values, 1):
                                cell = ws.cell(row=row_num, column=col_num, value=value)
                                cell.alignment = Alignment(horizontal="center")
                                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                            row_num += 1
                    summary_data = [
                        ["", "", "", "", "", "", "", "", "", "", ""],
                        ["Active Ingredients Cost:", f"₹{active_ingredients_cost:.2f}"],
                        ["Other Ingredients Cost:", f"₹{other_ingredients_cost:.2f}"],
                        ["Conversion Cost:", f"₹{conversion_cost:.2f}"],
                        ["Total Cost with Conversion:", f"₹{total_cost_with_conversion:.2f}"],
                        ["Profit Margin (20%):", f"₹{profit_margin:.2f}"],
                        ["Total Batch Cost with Profit:", f"₹{total_cost_with_profit:.2f}"],
                    ]
                    if self.product_type == "Liquid" and self.size_or_capsule in ["100 ml", "200 ml"]:
                        summary_data.extend([
                            ["Bottle Cost:", f"₹{self.quantity * bottle_cost:.2f}"],
                            ["ROPP Cost:", f"₹{self.quantity * ropp_cost:.2f}"],
                            ["Measuring Cup Cost:", f"₹{self.quantity * measuring_cup_cost:.2f}"],
                            ["Carton Cost:", f"₹{self.quantity * carton_cost:.2f}"],
                            ["Label Cost:", f"₹{self.quantity * label_cost:.2f}"],
                            ["Shipper Cost:", f"₹{num_shippers * shipper_cost:.2f}"],
                            ["Accessories Cost:", f"₹{num_shippers * accessories_cost:.2f}"]
                        ])
                        try:
                            bottle_ml = float(self.size_or_capsule.replace(" ml", ""))
                            serving_ml = float(self.serving_size.replace(" ml", ""))
                            servings_per_bottle = bottle_ml / serving_ml
                            total_servings = self.quantity * servings_per_bottle
                            summary_data.extend([
                                ["Bottle Size:", self.size_or_capsule],
                                ["Number of Bottles:", str(self.quantity)],
                                ["Serving Size:", self.serving_size],
                                ["Total Servings:", f"{total_servings:.0f}"],
                                ["Cost per Bottle:", f"₹{total_cost_with_profit/self.quantity:.2f}"],
                                ["Cost per Serving:", f"₹{total_cost_with_profit/total_servings:.2f}"]
                            ])
                        except (ValueError, IndexError, ZeroDivisionError):
                            pass
                    else:
                        summary_data.extend([
                            ["Primary Packaging Cost:", f"₹{total_primary_packaging_cost:.2f}"],
                            ["Secondary Packaging Cost:", f"₹{secondary_packaging_cost:.2f}"],
                            ["Tertiary Packaging Cost:", f"₹{tertiary_packaging_cost:.2f}"],
                            ["Cellotape and Wrapping Cost:", f"₹{cellotape_wrapping_cost:.2f}"],
                        ])
                        if num_strips > 0:
                            summary_data.append(["Profit per Strip:", f"₹{total_cost_with_profit / num_strips:.2f}"])
                        if num_jars > 0:
                            summary_data.append(["Profit per Jar:", f"₹{total_cost_with_profit / num_jars:.2f}"])
                        if self.product_type == "Capsule":
                            summary_data.append(["Capsule Cost:", f"₹{capsule_cost:.2f}"])

                    for row in summary_data:
                        ws.append(row)

                    wb.save(file_path)
                    messagebox.showinfo("Download Complete", f"Excel file saved as {file_path}")
                except Exception as e:
                    messagebox.showerror("Download Error", f"Failed to save Excel file: {str(e)}")

            def restart_app():
                self.product_type = None
                self.quantity = 0
                self.size_or_capsule = None
                self.capsule_types = None
                self.serving_size = None
                self.sugar_type = None
                self.sugar_percent = None
                self.custom_ingredients = []
                self.selected_excipients = []
                self.current_step = None
                self.show_login_window()

            button_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
            button_frame.pack(fill="x", padx=20, pady=10)
            ttk.Button(button_frame, text="Download as Excel", command=download_excel, width=20).pack(side="left", padx=5)
            ttk.Button(button_frame, text="New Calculation", command=restart_app, width=20).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Close", command=self.root.destroy, width=20).pack(side="left", padx=5)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar_y.pack(side="right", fill="y")
            scrollbar_x.pack(side="bottom", fill="x")
            self.bind_mousewheel(canvas)

        except Exception as e:
            messagebox.showerror("Display Error", f"An error occurred while displaying results: {str(e)}")

def main():
    try:
        root = tk.Tk()

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            error_msg = f"An unexpected error occurred:\n{exc_type.__name__}: {exc_value}"
            messagebox.showerror("Application Error", error_msg)

        sys.excepthook = handle_exception

        app = BatchMasterCardApp(root)

        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.bind('<Escape>', lambda e: on_closing())
        root.bind('<F11>', lambda e: root.attributes('-fullscreen', not root.attributes('-fullscreen')))

        root.mainloop()

    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main()
