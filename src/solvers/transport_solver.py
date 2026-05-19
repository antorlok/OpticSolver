"""
Método del Costo Mínimo para el Problema de Transporte.

Hereda de BaseTransportSolver la validación, balanceo y formateo.
Solo implementa la lógica de asignación específica del método.
"""

from typing import List, Tuple, Optional
from core.base_solver import BaseTransportSolver


class TransportSolver(BaseTransportSolver):
    """
    Resuelve el problema de transporte usando el Método del Costo Mínimo.

    Estrategia: en cada iteración, localiza la celda con el menor costo
    unitario y le asigna la mayor cantidad posible.
    """

    METHOD_NAME = "Método del Costo Mínimo"

    # ──────────────────────────── Celda de costo mínimo ────────────────────────

    @staticmethod
    def _find_min_cost_cell(
        costs: List[List[float]],
        supply: List[float],
        demand: List[float],
        cancelled_rows: List[bool],
        cancelled_cols: List[bool],
    ) -> Optional[Tuple[int, int]]:
        """
        Localiza la celda activa con costo mínimo.

        Regla de desempate determinista: ante costos iguales, se escoge la celda
        que permita la mayor asignación. Si persiste el empate, se toma la
        primera en orden de recorrido (fila→columna).

        Returns:
            Tupla (i, j) de la celda elegida, o None si no quedan celdas activas.
        """
        best: Optional[Tuple[float, float, int, int]] = None

        for i in range(len(supply)):
            if cancelled_rows[i]:
                continue
            for j in range(len(demand)):
                if cancelled_cols[j]:
                    continue

                cost = costs[i][j]
                max_alloc = min(supply[i], demand[j])
                # Criterio: menor costo → mayor asignación → menor índice
                candidate = (cost, -max_alloc, i, j)

                if best is None or candidate < best:
                    best = candidate

        return (best[2], best[3]) if best else None

    # ──────────────────────────── Asignación ───────────────────────────────────

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
        """Ejecuta la asignación iterativa por costo mínimo."""
        allocation = [[0.0] * n for _ in range(m)]
        cancelled_rows = [False] * m
        cancelled_cols = [False] * n

        iteration = 0
        while True:
            cell = self._find_min_cost_cell(costs, supply, demand, cancelled_rows, cancelled_cols)
            if cell is None:
                break

            i, j = cell
            alloc = min(supply[i], demand[j])
            allocation[i][j] = alloc
            supply[i] -= alloc
            demand[j] -= alloc
            iteration += 1

            steps.append(
                f"Iteración {iteration}: Celda ({i},{j}) con costo {costs[i][j]:.2f} → "
                f"Asignación = {alloc:.2f}. Oferta restante fila {i} = {supply[i]:.2f}, "
                f"Demanda restante col {j} = {demand[j]:.2f}."
            )

            # ── Manejo de degeneración ──
            if supply[i] == 0 and demand[j] == 0:
                cancelled_rows[i] = True
                steps.append(
                    f"  → Degeneración: oferta y demanda se agotaron simultáneamente. "
                    f"Se cancela fila {i}; columna {j} permanece activa con demanda 0."
                )
            elif supply[i] == 0:
                cancelled_rows[i] = True
            elif demand[j] == 0:
                cancelled_cols[j] = True
            
            steps.append("  Matriz de asignaciones actual:")
            steps.append(self.format_matrix(allocation, row_labels, col_labels))

        return allocation
