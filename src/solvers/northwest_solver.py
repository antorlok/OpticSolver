"""
Método de la Esquina Noroeste para el Problema de Transporte.

Hereda de BaseTransportSolver la validación, balanceo y formateo.
Solo implementa la lógica de asignación específica del método.
"""

from typing import List
from core.base_solver import BaseTransportSolver


class NorthwestCornerSolver(BaseTransportSolver):
    """
    Resuelve el problema de transporte usando el Método de la Esquina Noroeste.

    Estrategia: comienza en la celda (0,0) —esquina noroeste— y asigna la mayor
    cantidad posible. Luego avanza hacia la derecha (si la demanda se agotó) o
    hacia abajo (si la oferta se agotó) hasta cubrir toda la matriz.
    """

    METHOD_NAME = "Método de la Esquina Noroeste"

    def _allocate(
        self,
        costs: List[List[float]],
        supply: List[float],
        demand: List[float],
        m: int,
        n: int,
        steps: List[str],
        row_labels: List[str],
        col_labels: List[str],
    ) -> List[List[float]]:
        """Ejecuta la asignación por esquina noroeste recorriendo la diagonal."""
        allocation = [[0.0] * n for _ in range(m)]

        i, j = 0, 0
        iteration = 0

        while i < m and j < n:
            alloc = min(supply[i], demand[j])
            allocation[i][j] = alloc
            supply[i] -= alloc
            demand[j] -= alloc
            iteration += 1

            steps.append(
                f"Iteración {iteration}: Esquina ({i},{j}) con costo {costs[i][j]:.2f} → "
                f"Asignación = {alloc:.2f}. Oferta restante fila {i} = {supply[i]:.2f}, "
                f"Demanda restante col {j} = {demand[j]:.2f}."
            )

            # ── Manejo de degeneración ──
            if supply[i] == 0 and demand[j] == 0:
                # Agotamiento simultáneo: avanzar en diagonal, registrar degeneración
                steps.append(
                    f"  → Degeneración: oferta y demanda se agotaron simultáneamente en ({i},{j})."
                )
                i += 1
                j += 1
            elif supply[i] == 0:
                # Oferta agotada: avanzar a la siguiente fila
                i += 1
            else:
                # Demanda agotada: avanzar a la siguiente columna
                j += 1
            
            self._add_allocation_step(
                steps, allocation, row_labels, col_labels,
                supply_remaining=list(supply),
                demand_remaining=list(demand),
            )

        return allocation
