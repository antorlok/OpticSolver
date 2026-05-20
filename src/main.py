"""
Orquestador principal de la aplicación OpticSolver.
Inicia la interfaz gráfica de usuario para resolver problemas de transporte.

Uso:
    python src/main.py
"""

import tkinter as tk
from presentation.gui import CalculadoraGUI

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CalculadoraGUI(root)
        root.mainloop()
    except ImportError as e:
        # Registrar y reportar en consola fallos de dependencias o de inicio de Tkinter
        print(f"❌ Error al iniciar la interfaz gráfica: {e}")