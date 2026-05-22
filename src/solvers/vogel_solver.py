"""
Método de Aproximación de Vogel para el Problema de Transporte.

Hereda de BaseTransportSolver la validación, balanceo y formateo.
Implementa la lógica de asignación utilizando penalizaciones.
"""

from typing import List, Optional
from core.base_solver import BaseTransportSolver


class VogelSolver(BaseTransportSolver):
    """
    Resuelve el problema de transporte usando el Método de Aproximación de Vogel.

    Estrategia: Calcula la penalización para cada fila y columna activa (diferencia 
    entre los dos costos menores). Selecciona la fila/columna con la mayor penalización 
    y asigna la máxima cantidad posible a la celda de menor costo de esa fila/columna.
    """

    METHOD_NAME = "Método de Vogel"

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
        """Ejecuta la asignación por el método de Vogel."""
        allocation = [[0.0] * n for _ in range(m)]

        active_rows = [True] * m
        active_cols = [True] * n

        iteration = 0

        while any(active_rows) and any(active_cols):
            # Si solo queda una fila activa, asignar por menor costo en esa fila
            if sum(active_rows) == 1:
                i = active_rows.index(True)
                cols = [(costs[i][j], j) for j in range(n) if active_cols[j]]
                cols.sort()  # Ordenar por costo
                for cost, j in cols:
                    if supply[i] > 0 and demand[j] > 0:
                        alloc = min(supply[i], demand[j])
                        allocation[i][j] += alloc
                        supply[i] -= alloc
                        demand[j] -= alloc
                        iteration += 1
                        steps.append(
                            f"Iteración {iteration}: Última fila {i}, celda ({i},{j}) con costo {cost:.2f} → "
                            f"Asignación = {alloc:.2f}. Oferta restante = {supply[i]:.2f}, "
                            f"Demanda restante = {demand[j]:.2f}."
                        )
                        self._add_allocation_step(
                            steps, allocation, row_labels, col_labels,
                            supply_remaining=list(supply),
                            demand_remaining=list(demand),
                        )
                break

            # Si solo queda una columna activa, asignar por menor costo en esa columna
            if sum(active_cols) == 1:
                j = active_cols.index(True)
                rows = [(costs[i][j], i) for i in range(m) if active_rows[i]]
                rows.sort()  # Ordenar por costo
                for cost, i in rows:
                    if supply[i] > 0 and demand[j] > 0:
                        alloc = min(supply[i], demand[j])
                        allocation[i][j] += alloc
                        supply[i] -= alloc
                        demand[j] -= alloc
                        iteration += 1
                        steps.append(
                            f"Iteración {iteration}: Última columna {j}, celda ({i},{j}) con costo {cost:.2f} → "
                            f"Asignación = {alloc:.2f}. Oferta restante = {supply[i]:.2f}, "
                            f"Demanda restante = {demand[j]:.2f}."
                        )
                        self._add_allocation_step(
                            steps, allocation, row_labels, col_labels,
                            supply_remaining=list(supply),
                            demand_remaining=list(demand),
                        )
                break

            # Calcular penalizaciones de filas
            row_penalties = []
            for i in range(m):
                if active_rows[i]:
                    row_costs = [costs[i][j] for j in range(n) if active_cols[j]]
                    if len(row_costs) >= 2:
                        sorted_costs = sorted(row_costs)
                        row_penalties.append((sorted_costs[1] - sorted_costs[0], i))
                    else:
                        row_penalties.append((0.0, i))
                else:
                    row_penalties.append((-1.0, i))

            # Calcular penalizaciones de columnas
            col_penalties = []
            for j in range(n):
                if active_cols[j]:
                    col_costs = [costs[i][j] for i in range(m) if active_rows[i]]
                    if len(col_costs) >= 2:
                        sorted_costs = sorted(col_costs)
                        col_penalties.append((sorted_costs[1] - sorted_costs[0], j))
                    else:
                        col_penalties.append((0.0, j))
                else:
                    col_penalties.append((-1.0, j))

            # Encontrar máxima penalización
            max_row_pen = max(row_penalties, key=lambda x: x[0]) if row_penalties else (-1.0, -1)
            max_col_pen = max(col_penalties, key=lambda x: x[0]) if col_penalties else (-1.0, -1)

            is_row = max_row_pen[0] >= max_col_pen[0]

            if is_row:
                i = max_row_pen[1]
                # Encontrar menor costo en esta fila
                min_cost = float('inf')
                min_j = -1
                for j in range(n):
                    if active_cols[j] and costs[i][j] < min_cost:
                        min_cost = costs[i][j]
                        min_j = j
                j = min_j
            else:
                j = max_col_pen[1]
                # Encontrar menor costo en esta columna
                min_cost = float('inf')
                min_i = -1
                for i in range(m):
                    if active_rows[i] and costs[i][j] < min_cost:
                        min_cost = costs[i][j]
                        min_i = i
                i = min_i

            alloc = min(supply[i], demand[j])
            allocation[i][j] += alloc
            supply[i] -= alloc
            demand[j] -= alloc
            iteration += 1

            pen_type = "Fila" if is_row else "Columna"
            pen_idx = i if is_row else j
            pen_val = max_row_pen[0] if is_row else max_col_pen[0]

            steps.append(
                f"Iteración {iteration}: Max penalización en {pen_type} {pen_idx} (Valor: {pen_val:.2f}). "
                f"Asignando en celda ({i},{j}) con costo {costs[i][j]:.2f} → "
                f"Asignación = {alloc:.2f}. Oferta restante = {supply[i]:.2f}, "
                f"Demanda restante = {demand[j]:.2f}."
            )

            # Manejo de eliminación
            if supply[i] == 0 and demand[j] == 0:
                # Degeneración: se tacha la fila (arbitrario), la demanda queda en 0 para ser tachada en la prox
                active_rows[i] = False
                steps.append(f"  → Degeneración: se agotaron simultáneamente. Se tachó la fila {i}.")
            elif supply[i] == 0:
                active_rows[i] = False
                steps.append(f"  → Se tachó la fila {i}.")
            else:
                active_cols[j] = False
                steps.append(f"  → Se tachó la columna {j}.")
            
            # Construir vectores de penalización para la tabla (None = fila/col inactiva)
            rp_display: List[Optional[float]] = [
                pen_val if active_rows[idx] else None
                for pen_val, idx in row_penalties
            ]
            cp_display: List[Optional[float]] = [
                pen_val if active_cols[idx] else None
                for pen_val, idx in col_penalties
            ]

            self._add_allocation_step(
                steps, allocation, row_labels, col_labels,
                supply_remaining=list(supply),
                demand_remaining=list(demand),
                row_penalties=rp_display,
                col_penalties=cp_display,
            )

        return allocation
