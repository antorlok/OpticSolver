import tkinter as tk
from tkinter import ttk, messagebox

from solvers.transport_solver import TransportSolver
from solvers.northwest_solver import NorthwestCornerSolver
from solvers.vogel_solver import VogelSolver
from solvers.hungarian_solver import HungarianSolver
from services.groq_client import GroqClient

class CalculadoraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpticSolver - Optimización de Transporte")
        self.root.geometry("950x700")
        
        # Colores principales (Dark Theme Comercial)
        self.bg_color = "#0F172A"        # Slate 900 (Fondo principal)
        self.card_color = "#1E293B"      # Slate 800 (Fondo de tarjetas)
        self.text_color = "#F8FAFC"      # Slate 50 (Texto principal)
        self.secondary_text = "#94A3B8"  # Slate 400 (Texto secundario)
        self.primary_color = "#3B82F6"   # Blue 500 (Color primario)
        self.primary_hover = "#2563EB"   # Blue 600 (Hover primario)
        self.header_bg = "#0B1120"       # Color ultra oscuro para header
        self.accent_color = "#334155"    # Slate 700 (Bordes y elementos)
        self.entry_bg = "#0F172A"        # Slate 900 (Inputs fondo)
        
        self.root.configure(bg=self.bg_color)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configuración de estilos
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.card_color)
        self.style.configure("Header.TFrame", background=self.header_bg)
        
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 11))
        self.style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 11))
        self.style.configure("Title.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 20, "bold"))
        self.style.configure("Subtitle.TLabel", background=self.card_color, foreground=self.secondary_text, font=("Segoe UI", 10))
        self.style.configure("MatrixHeader.TLabel", background=self.card_color, foreground=self.secondary_text, font=("Segoe UI", 10, "bold"))
        
        # Estilos tipográficos para el Logo
        self.style.configure("Logo1.TLabel", background=self.header_bg, foreground=self.text_color, font=("Segoe UI", 22, "bold"))
        self.style.configure("Logo2.TLabel", background=self.header_bg, foreground=self.primary_color, font=("Segoe UI", 22, "bold"))
        
        # Botones
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="white", borderwidth=0, padding=10)
        self.style.map("Primary.TButton", background=[("active", self.primary_hover)])
        
        self.style.configure("Secondary.TButton", font=("Segoe UI", 11), background=self.accent_color, foreground=self.text_color, borderwidth=0, padding=10)
        self.style.map("Secondary.TButton", background=[("active", "#475569")]) # Slate 600
        
        # Entradas
        self.style.configure("TEntry", fieldbackground=self.entry_bg, borderwidth=0, padding=8, foreground=self.text_color)
        self.style.configure("TCombobox", fieldbackground=self.entry_bg, background=self.accent_color, borderwidth=0, padding=8, foreground=self.text_color, arrowcolor=self.text_color)
        self.style.map("TCombobox", 
            fieldbackground=[("readonly", self.entry_bg)], 
            background=[("readonly", self.accent_color)], 
            foreground=[("readonly", self.text_color)],
            selectbackground=[("readonly", self.primary_color)],
            selectforeground=[("readonly", "white")]
        )
        
        # Estilo para la lista desplegable del Combobox
        self.root.option_add('*TCombobox*Listbox.background', self.entry_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', self.text_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.primary_color)
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        
        # Solvers de transporte (requieren oferta/demanda)
        self.transport_solvers = {
            "Costo Mínimo": TransportSolver,
            "Esquina Noroeste": NorthwestCornerSolver,
            "Método de Vogel": VogelSolver,
        }
        # Solvers de asignación (solo matriz cuadrada de costos)
        self.assignment_solvers = {
            "Método Húngaro": HungarianSolver,
        }
        # Todos los métodos disponibles para el combobox
        self.all_methods = list(self.transport_solvers.keys()) + list(self.assignment_solvers.keys())
        
        # Header Superior (Logotipo Tipográfico)
        self.header_frame = ttk.Frame(self.root, style="Header.TFrame")
        self.header_frame.pack(fill="x", side="top")
        
        logo_frame = tk.Frame(self.header_frame, bg=self.header_bg)
        logo_frame.pack(side="left", padx=25, pady=15)
        ttk.Label(logo_frame, text="Optic", style="Logo1.TLabel").pack(side="left")
        ttk.Label(logo_frame, text="Solver", style="Logo2.TLabel").pack(side="left")
        
        # Contenedor principal
        self.main_container = ttk.Frame(self.root, style="TFrame")
        self.main_container.pack(fill="both", expand=True, padx=30, pady=20)
        
        self.current_frame = None
        self.create_setup_frame()

    def switch_frame(self, new_frame_func, *args):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = ttk.Frame(self.main_container, style="TFrame")
        self.current_frame.pack(fill="both", expand=True)
        new_frame_func(self.current_frame, *args)

    # ─── Pantalla 1: Configuración Inicial ─────────────────────────────────────
    def create_setup_frame(self, frame=None):
        if frame is None:
            self.switch_frame(self._build_setup_frame)
        else:
            self._build_setup_frame(frame)

    def _build_setup_frame(self, frame):
        # Tarjeta centrada
        card = tk.Frame(frame, bg=self.card_color, padx=40, pady=40, highlightbackground=self.accent_color, highlightthickness=1)
        card.place(relx=0.5, rely=0.4, anchor="center")
        
        ttk.Label(card, text="Configuración del Problema", style="Title.TLabel").pack(pady=(0, 5))
        ttk.Label(card, text="Define las dimensiones y el método a utilizar", style="Subtitle.TLabel").pack(pady=(0, 30))
        
        form_frame = ttk.Frame(card, style="Card.TFrame")
        form_frame.pack(fill="x")
        
        # ── Método (primero, para reaccionar al cambio) ──
        ttk.Label(form_frame, text="Método de Resolución:", style="Card.TLabel").grid(row=0, column=0, padx=5, pady=15, sticky="w")
        self.method_var = tk.StringVar(value="Costo Mínimo")
        method_cb = ttk.Combobox(form_frame, textvariable=self.method_var, values=self.all_methods, state="readonly", font=("Segoe UI", 11), width=18)
        method_cb.grid(row=0, column=1, padx=5, pady=15)
        
        # ── Labels dinámicas (cambian según el método) ──
        self._lbl_dim1 = ttk.Label(form_frame, text="Número de Plantas (Orígenes):", style="Card.TLabel")
        self._lbl_dim1.grid(row=1, column=0, padx=5, pady=15, sticky="w")
        self.plants_var = tk.StringVar(value="3")
        plant_entry = ttk.Entry(form_frame, textvariable=self.plants_var, width=15, font=("Segoe UI", 11))
        plant_entry.grid(row=1, column=1, padx=5, pady=15)
        
        self._lbl_dim2 = ttk.Label(form_frame, text="Número de Ciudades (Destinos):", style="Card.TLabel")
        self._lbl_dim2.grid(row=2, column=0, padx=5, pady=15, sticky="w")
        self.cities_var = tk.StringVar(value="4")
        city_entry = ttk.Entry(form_frame, textvariable=self.cities_var, width=15, font=("Segoe UI", 11))
        city_entry.grid(row=2, column=1, padx=5, pady=15)
        
        # Callback para actualizar labels según método
        def _on_method_change(*_):
            if self.method_var.get() in self.assignment_solvers:
                self._lbl_dim1.config(text="Número de Agentes (Filas):")
                self._lbl_dim2.config(text="Número de Tareas (Columnas):")
            else:
                self._lbl_dim1.config(text="Número de Plantas (Orígenes):")
                self._lbl_dim2.config(text="Número de Ciudades (Destinos):")

        self.method_var.trace_add("write", _on_method_change)
        
        # Botón
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(30, 0))
        ttk.Button(btn_frame, text="Siguiente ➔", style="Primary.TButton", command=self.go_to_matrix).pack(side="right")

    def _is_hungarian(self) -> bool:
        return self.method_var.get() in self.assignment_solvers

    def go_to_matrix(self):
        try:
            num_rows = int(self.plants_var.get())
            num_cols = int(self.cities_var.get())
            if num_rows <= 0 or num_cols <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese números enteros mayores a 0.")
            return

        if self._is_hungarian():
            self.switch_frame(self._build_hungarian_matrix_frame, num_rows, num_cols)
        else:
            self.switch_frame(self._build_matrix_frame, num_rows, num_cols)

    # ─── Pantalla 2a: Ingreso de Datos (Húngaro — solo costos) ─────────────────
    def _build_hungarian_matrix_frame(self, frame, num_agents, num_tasks):
        top_frame = ttk.Frame(frame, style="TFrame")
        top_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(top_frame, text="Ingreso de Datos — Asignación", style="Title.TLabel", background=self.bg_color).pack(side="left")
        ttk.Label(top_frame, text="Completa la matriz de costos (Agente → Tarea)", style="Subtitle.TLabel", background=self.bg_color).pack(side="left", padx=15)

        # ── Selector Objetivo (Minimizar / Maximizar) con un Combobox Estilizado ──
        opt_frame = ttk.Frame(frame, style="TFrame")
        opt_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(opt_frame, text="Objetivo del Problema:", style="TLabel").pack(side="left", padx=(0, 10))
        self.objective_var = tk.StringVar(value="Minimizar")
        objective_cb = ttk.Combobox(
            opt_frame, 
            textvariable=self.objective_var, 
            values=["Minimizar", "Maximizar"], 
            state="readonly", 
            font=("Segoe UI", 11), 
            width=15
        )
        objective_cb.pack(side="left")

        card = tk.Frame(frame, bg=self.card_color, highlightbackground=self.accent_color, highlightthickness=1)
        card.pack(fill="both", expand=True)

        canvas = tk.Canvas(card, bg=self.card_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(card, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=scroll_x.set)

        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        self.cost_entries = []
        self.agent_name_entries = []
        self.task_name_entries = []

        # Cabecera: nombres de tareas
        ttk.Label(scrollable_frame, text="Agentes \\ Tareas", style="MatrixHeader.TLabel", background=self.card_color).grid(row=0, column=0, padx=10, pady=10)
        for j in range(num_tasks):
            entry = ttk.Entry(scrollable_frame, width=12, font=("Segoe UI", 10), justify="center")
            entry.insert(0, f"Tarea {j+1}")
            entry.grid(row=0, column=j+1, padx=5, pady=10)
            self.task_name_entries.append(entry)

        # Filas: nombres de agentes + costos
        for i in range(num_agents):
            name_entry = ttk.Entry(scrollable_frame, width=12, font=("Segoe UI", 10), justify="center")
            name_entry.insert(0, f"Agente {i+1}")
            name_entry.grid(row=i+1, column=0, padx=10, pady=5)
            self.agent_name_entries.append(name_entry)

            row_entries = []
            for j in range(num_tasks):
                entry = ttk.Entry(scrollable_frame, width=10, font=("Segoe UI", 11), justify="center")
                entry.grid(row=i+1, column=j+1, padx=5, pady=5)
                row_entries.append(entry)
            self.cost_entries.append(row_entries)

        btn_frame = ttk.Frame(frame, style="TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_frame, text="🡨 Volver", style="Secondary.TButton", command=self.create_setup_frame).pack(side="left")
        ttk.Button(btn_frame, text="Resolver Problema ➔", style="Primary.TButton", command=self.solve_hungarian).pack(side="right")

    def solve_hungarian(self):
        """Recolecta datos de la tabla de asignación y resuelve con Método Húngaro."""
        try:
            agent_names = [e.get().strip() for e in self.agent_name_entries]
            task_names = [e.get().strip() for e in self.task_name_entries]

            costs = []
            for row in self.cost_entries:
                costs.append([float(e.get()) for e in row])
        except ValueError:
            messagebox.showerror("Error de Datos", "Todos los costos deben ser numéricos.")
            return

        try:
            is_max = self.objective_var.get() == "Maximizar"
            solver = HungarianSolver(costs, is_maximization=is_max)
            result = solver.solve(row_labels=agent_names, col_labels=task_names)
            # Guardar flag para el reporte
            result._is_maximization = is_max
            self.switch_frame(self._build_results_frame, result)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al resolver:\n{str(e)}")

    # ─── Pantalla 2b: Ingreso de Datos (Transporte — costos + oferta/demanda) ──
    def _build_matrix_frame(self, frame, num_plants, num_cities):
        top_frame = ttk.Frame(frame, style="TFrame")
        top_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(top_frame, text="Ingreso de Datos", style="Title.TLabel", background=self.bg_color).pack(side="left")
        ttk.Label(top_frame, text="Completa los costos, oferta y demanda", style="Subtitle.TLabel", background=self.bg_color).pack(side="left", padx=15)
        
        # Contenedor de la tabla (Card)
        card = tk.Frame(frame, bg=self.card_color, highlightbackground=self.accent_color, highlightthickness=1)
        card.pack(fill="both", expand=True)
        
        # Frame scrollable para matrices grandes
        canvas = tk.Canvas(card, bg=self.card_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(card, orient="horizontal", command=canvas.xview)
        
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=scroll_x.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        
        self.cost_entries = []
        self.supply_entries = []
        self.demand_entries = []
        self.plant_name_entries = []
        self.city_name_entries = []
        
        # Cabeceras Ciudades
        ttk.Label(scrollable_frame, text="Plantas \\ Ciudades", style="MatrixHeader.TLabel", background=self.card_color).grid(row=0, column=0, padx=10, pady=10)
        for j in range(num_cities):
            entry = ttk.Entry(scrollable_frame, width=12, font=("Segoe UI", 10), justify="center")
            entry.insert(0, f"Ciudad {j+1}")
            entry.grid(row=0, column=j+1, padx=5, pady=10)
            self.city_name_entries.append(entry)
            
        ttk.Label(scrollable_frame, text="Oferta", style="MatrixHeader.TLabel", background=self.card_color).grid(row=0, column=num_cities+1, padx=10, pady=10)
        
        # Filas: Nombres de plantas, matriz de costos y oferta
        for i in range(num_plants):
            name_entry = ttk.Entry(scrollable_frame, width=12, font=("Segoe UI", 10), justify="center")
            name_entry.insert(0, f"Planta {i+1}")
            name_entry.grid(row=i+1, column=0, padx=10, pady=5)
            self.plant_name_entries.append(name_entry)
            
            row_entries = []
            for j in range(num_cities):
                entry = ttk.Entry(scrollable_frame, width=10, font=("Segoe UI", 11), justify="center")
                entry.grid(row=i+1, column=j+1, padx=5, pady=5)
                row_entries.append(entry)
            self.cost_entries.append(row_entries)
            
            sup_entry = ttk.Entry(scrollable_frame, width=10, font=("Segoe UI", 11, "bold"), justify="center")
            sup_entry.grid(row=i+1, column=num_cities+1, padx=10, pady=5)
            self.supply_entries.append(sup_entry)
            
        # Fila Demanda
        ttk.Label(scrollable_frame, text="Demanda", style="MatrixHeader.TLabel", background=self.card_color).grid(row=num_plants+1, column=0, padx=10, pady=10)
        for j in range(num_cities):
            dem_entry = ttk.Entry(scrollable_frame, width=10, font=("Segoe UI", 11, "bold"), justify="center")
            dem_entry.grid(row=num_plants+1, column=j+1, padx=5, pady=10)
            self.demand_entries.append(dem_entry)
            
        btn_frame = ttk.Frame(frame, style="TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_frame, text="🡨 Volver", style="Secondary.TButton", command=self.create_setup_frame).pack(side="left")
        ttk.Button(btn_frame, text="Resolver Problema ➔", style="Primary.TButton", command=self.solve_problem).pack(side="right")

    def solve_problem(self):
        """Recolecta datos de la tabla de transporte y resuelve."""
        try:
            plant_names = [e.get().strip() for e in self.plant_name_entries]
            city_names = [e.get().strip() for e in self.city_name_entries]
            
            costs = []
            for row in self.cost_entries:
                costs.append([float(e.get()) for e in row])
                
            supply = [float(e.get()) for e in self.supply_entries]
            demand = [float(e.get()) for e in self.demand_entries]
        except ValueError:
            messagebox.showerror("Error de Datos", "Por favor, asegúrese de que todos los costos, ofertas y demandas sean numéricos.")
            return

        method_name = self.method_var.get()
        solver_class = self.transport_solvers.get(method_name)
        if solver_class is None:
            messagebox.showerror("Error", f"Método '{method_name}' no encontrado.")
            return
        
        try:
            solver = solver_class(costs, supply, demand)
            result = solver.solve(row_labels=plant_names, col_labels=city_names)
            
            self.switch_frame(self._build_results_frame, result)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al resolver:\n{str(e)}")

    # ─── Pantalla 3: Resultados ────────────────────────────────────────────────
    def _build_results_frame(self, frame, result):
        top_frame = ttk.Frame(frame, style="TFrame")
        top_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(top_frame, text="Resultados del Análisis", style="Title.TLabel", background=self.bg_color).pack(side="left")
        ttk.Label(top_frame, text=f"Método: {result.method_name}", style="Subtitle.TLabel", background=self.bg_color).pack(side="left", padx=15)
        
        # Tarjeta para el reporte
        card = tk.Frame(frame, bg=self.card_color, highlightbackground=self.accent_color, highlightthickness=1)
        card.pack(fill="both", expand=True)
        
        # Area de texto estilizada
        text_area = tk.Text(card, wrap="word", bg=self.entry_bg, fg=self.text_color, font=("Consolas", 11), state="normal", relief="flat", padx=20, pady=20, insertbackground=self.text_color)
        
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        report_content = self.generate_report_content(result)
        text_area.insert("1.0", report_content)
        text_area.configure(state="disabled")
        
        # Guardar archivo automáticamente
        self.save_to_txt(report_content)
        
        # Solicitar IA en segundo plano
        text_area.configure(state="normal")
        text_area.insert("end", "\n\n🤖 Generando análisis de IA, por favor espere...\n")
        text_area.configure(state="disabled")
        text_area.see("end")
        
        # Ejecutar llamada a Groq
        self.root.after(100, lambda: self.fetch_ai_analysis(result, text_area, report_content))
        
        btn_frame = ttk.Frame(frame, style="TFrame")
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_frame, text="🡨 Nuevo Problema", style="Secondary.TButton", command=self.create_setup_frame).pack(side="left")

    def generate_report_content(self, result):
        content = []
        content.append("="*70)
        content.append(f"REPORTE DE OPTIMIZACIÓN - {result.method_name.upper()}")
        content.append("="*70)
        
        content.append("\n📋 ITERACIONES Y PROCEDIMIENTOS:")
        for step in result.steps:
            content.append(f"  • {step}")
            
        content.append("\n📊 MATRIZ DE ASIGNACIONES FINALES:")
        content.append(result.formatted_allocation_matrix)
        
        # Ajustar etiqueta según modo (maximización vs minimización)
        is_max = getattr(result, '_is_maximization', False)
        if is_max:
            content.append(f"\n💰 BENEFICIO TOTAL MÁXIMO: {result.total_cost:.2f}")
        else:
            content.append(f"\n💰 COSTO TOTAL MÍNIMO: {result.total_cost:.2f}")
        return "\n".join(content)

    def save_to_txt(self, content, filename="reporte_transporte.txt"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo {filename}: {e}")

    def fetch_ai_analysis(self, result, text_area, report_content):
        try:
            client = GroqClient()
            
            balance_info = result.balance_info
            cost_table = result.formatted_cost_matrix
            allocation_table = result.formatted_allocation_matrix
            
            conclusion = client.generate_conclusion(
                cost_table=cost_table,
                supply=str(result.original_supply),
                demand=str(result.original_demand),
                balance_info=balance_info,
                allocation_table=allocation_table,
                total_cost=result.total_cost,
                steps="\n".join(result.steps),
                method_name=result.method_name
            )
            
            ai_text = "\n\n" + "="*70 + "\n  ANÁLISIS ESTRATÉGICO (IA)\n" + "="*70 + f"\n\n{conclusion}"
            
            text_area.configure(state="normal")
            text_area.delete("end-2l", "end")
            text_area.insert("end", ai_text)
            text_area.configure(state="disabled")
            text_area.see("end")
            
            with open("reporte_transporte.txt", "a", encoding="utf-8") as f:
                f.write(ai_text)
                
        except Exception as e:
            text_area.configure(state="normal")
            text_area.insert("end", f"\n❌ Error al obtener análisis IA: {e}")
            text_area.configure(state="disabled")
            text_area.see("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraGUI(root)
    root.mainloop()
