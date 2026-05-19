"""
Orquestador principal: resuelve el problema de transporte con el método elegido
y genera una conclusión ejecutiva mediante la API de Groq.

Uso:
    python main.py
"""
import tkinter as tk
from presentation.gui import CalculadoraGUI
from core.base_solver import BaseTransportSolver, TransportResult
from solvers.transport_solver import TransportSolver
from solvers.northwest_solver import NorthwestCornerSolver
from solvers.vogel_solver import VogelSolver
from services.groq_client import GroqClient


# ──────────────────────────── Selección de método ──────────────────────────────

SOLVERS = {
    "1": ("Método del Costo Mínimo", TransportSolver),
    "2": ("Método de la Esquina Noroeste", NorthwestCornerSolver),
    "3": ("Método de Vogel", VogelSolver),
}


def select_method() -> type:
    """Muestra menú de métodos y retorna la clase solver elegida."""
    print("\n📐 Seleccione el método de resolución:")
    for key, (name, _) in SOLVERS.items():
        print(f"   {key}. {name}")

    while True:
        choice = input("\nOpción: ").strip()
        if choice in SOLVERS:
            print(f"\n✅ Método seleccionado: {SOLVERS[choice][0]}")
            return SOLVERS[choice][1]
        print("❌ Opción inválida. Intente de nuevo.")


# ──────────────────────────── Presentación de resultados ───────────────────────

def print_result(result: TransportResult) -> None:
    """Imprime en consola los resultados del solver de forma estructurada."""
    separator = "=" * 70

    print(f"\n{separator}")
    print(f"  RESULTADO — {result.method_name.upper()}")
    print(separator)

    print("\n📋 Pasos del algoritmo:")
    for step in result.steps:
        print(f"   • {step}")

    print(f"\n📊 Matriz de Costos Utilizada:")
    print(BaseTransportSolver.format_matrix(
        result.cost_matrix_used,
        row_labels=result.row_labels,
        col_labels=result.col_labels
    ))

    print(f"\n📦 Matriz de Asignaciones:")
    print(BaseTransportSolver.format_matrix(
        result.allocation_matrix,
        row_labels=result.row_labels,
        col_labels=result.col_labels
    ))

    print(f"\n💰 Costo Total Mínimo: {result.total_cost:.2f}")
    print(separator)


def build_balance_info(result: TransportResult) -> str:
    """Construye la descripción textual del estado de balanceo."""
    if result.balanced:
        return "El problema estaba balanceado (Oferta == Demanda). No se agregaron ficticios."

    if result.dummy_type == "column":
        return (
            f"Oferta ({sum(result.original_supply):.2f}) > Demanda ({sum(result.original_demand):.2f}). "
            f"Se agregó una CIUDAD FICTICIA (columna) con costo 0 para absorber el excedente."
        )

    return (
        f"Demanda ({sum(result.original_demand):.2f}) > Oferta ({sum(result.original_supply):.2f}). "
        f"Se agregó una PLANTA FICTICIA (fila) con costo 0 para cubrir el déficit."
    )


def generate_groq_conclusion(result: TransportResult) -> None:
    """Envía los resultados a Groq e imprime la conclusión ejecutiva."""
    try:
        client = GroqClient()
    except (ImportError, EnvironmentError) as e:
        print(f"\n⚠️  No se pudo conectar con Groq: {e}")
        return

    cost_table = BaseTransportSolver.format_matrix(
        result.cost_matrix_used,
        row_labels=result.row_labels,
        col_labels=result.col_labels
    )

    allocation_table = BaseTransportSolver.format_matrix(
        result.allocation_matrix,
        row_labels=result.row_labels,
        col_labels=result.col_labels
    )

    balance_info = build_balance_info(result)
    steps_text = "\n".join(f"  {s}" for s in result.steps)

    print("\n🤖 Generando conclusión ejecutiva con Groq...")

    conclusion = client.generate_conclusion(
        cost_table=cost_table,
        supply=str(result.original_supply),
        demand=str(result.original_demand),
        balance_info=balance_info,
        allocation_table=allocation_table,
        total_cost=result.total_cost,
        steps=steps_text,
        method_name=result.method_name,
    )

    print("\n" + "=" * 70)
    print("  CONCLUSIÓN EJECUTIVA (Generada por IA)")
    print("=" * 70)
    print(f"\n{conclusion}\n")


# ──────────────────────────── Utilidades de entrada ────────────────────────────

def get_float_input(prompt: str) -> float:
    """Solicita un valor numérico por consola con validación básica."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("❌ Entrada inválida. Por favor, ingrese un número.")


# ──────────────────────────── Modos de ejecución ──────────────────────────────

def interactive_run() -> None:
    """Captura datos del problema de transporte desde la consola."""
    print("\n" + "═" * 50)
    print("      CONFIGURACIÓN PERSONALIZADA (Plantas y Ciudades)")
    print("═" * 50)

    num_plants = int(get_float_input("Número de Plantas (Orígenes): "))
    num_cities = int(get_float_input("Número de Ciudades (Destinos): "))

    plant_names = []
    for i in range(num_plants):
        name = input(f"  Nombre de la Planta {i+1}: ")
        plant_names.append(name or f"Planta {i+1}")

    city_names = []
    for j in range(num_cities):
        name = input(f"  Nombre de la Ciudad {j+1}: ")
        city_names.append(name or f"Ciudad {j+1}")

    print("\n--- Ingrese la Matriz de Costos ---")
    costs = []
    for i in range(num_plants):
        row = []
        for j in range(num_cities):
            cost = get_float_input(f"  Costo {plant_names[i]} ➔ {city_names[j]}: ")
            row.append(cost)
        costs.append(row)

    print("\n--- Ingrese los Vectores de Oferta ---")
    supply = []
    for i in range(num_plants):
        s = get_float_input(f"  Oferta disponible en {plant_names[i]}: ")
        supply.append(s)

    print("\n--- Ingrese los Vectores de Demanda ---")
    demand = []
    for j in range(num_cities):
        d = get_float_input(f"  Demanda requerida en {city_names[j]}: ")
        demand.append(d)

    # Seleccionar método de resolución
    solver_class = select_method()

    print("\n🚀 Procesando problema...")
    solver = solver_class(costs, supply, demand)
    result = solver.solve(row_labels=plant_names, col_labels=city_names)

    print_result(result)
    generate_groq_conclusion(result)


def run_demo() -> None:
    """Ejecuta el caso de ejemplo de Ingeniería Industrial Online."""
    costs = [
        [10, 2, 20, 11],
        [12, 7, 9, 20],
        [4, 14, 16, 18],
    ]
    supply = [15, 25, 10]
    demand = [5, 15, 15, 15]

    plant_names = ["Planta A", "Planta B", "Planta C"]
    city_names = ["Ciudad 1", "Ciudad 2", "Ciudad 3", "Ciudad 4"]

    # Seleccionar método de resolución
    solver_class = select_method()

    print("\n╔══════════════════════════════════════════════════════════════════════╗")
    print("║  DEMO: EJEMPLO INGENIERÍA INDUSTRIAL ONLINE                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    solver = solver_class(costs, supply, demand)
    result = solver.solve(row_labels=plant_names, col_labels=city_names)
    print_result(result)
    generate_groq_conclusion(result)

'''
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  📊 CALCULADORA MODULAR DE TRANSPORTE                             ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("\n1. Ejecutar Demo (Problema 3x4)")
    print("2. Ingresar datos manualmente")
    print("3. Iniciar Interfaz Gráfica (GUI)")

    opcion = input("\nSeleccione una opción (1-3): ")
    if opcion == "3":
        try:
            import tkinter as tk
            from gui import CalculadoraGUI
            root = tk.Tk()
            app = CalculadoraGUI(root)
            root.mainloop()
        except ImportError as e:
            print(f"❌ Error al iniciar la interfaz gráfica: {e}")
    elif opcion == "2":
        interactive_run()
    else:
        run_demo()
'''

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CalculadoraGUI(root)
        root.mainloop()
    except ImportError as e:
        print(f"❌ Error al iniciar la interfaz gráfica: {e}")