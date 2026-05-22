"""
Método Húngaro (Munkres) para el Problema de Asignación Óptima.

A diferencia de los métodos de transporte (Esquina Noroeste, Costo Mínimo, Vogel),
el Método Húngaro resuelve problemas de ASIGNACIÓN: dado N agentes y N tareas,
asignar exactamente 1 tarea a cada agente minimizando el costo total.

Requiere matriz cuadrada (N×N). Si la matriz no es cuadrada, se rellena con ceros
(filas/columnas ficticias) para hacerla cuadrada antes de resolver.

Reutiliza TransportResult como estructura de salida para compatibilidad con la GUI,
reportes y análisis IA.
"""

from typing import List, Optional, Tuple
from copy import deepcopy
from dataclasses import field

from munkres import Munkres

from core.base_solver import BaseTransportSolver, TransportResult


class HungarianSolver:
    """
    Resuelve problemas de asignación óptima mediante el Algoritmo Húngaro (Munkres).

    Interfaz compatible con los solvers de transporte (misma firma de solve()),
    pero NO hereda de BaseTransportSolver porque el problema de asignación no
    usa balanceo oferta/demanda.
    """

    METHOD_NAME = "Método Húngaro (Asignación)"

    def __init__(self, costs: List[List[float]]) -> None:
        """
        Args:
            costs: Matriz de costos (no necesita ser cuadrada, se cuadra automáticamente).

        Raises:
            ValueError: Si la matriz está vacía o tiene costos negativos.
        """
        self._validate(costs)
        self._original_costs = deepcopy(costs)
        self._original_rows = len(costs)
        self._original_cols = len(costs[0])

    # ──────────────────────────── Validación ────────────────────────────────────

    @staticmethod
    def _validate(costs: List[List[float]]) -> None:
        if not costs or not costs[0]:
            raise ValueError("La matriz de costos no puede estar vacía.")

        num_cols = len(costs[0])
        for i, row in enumerate(costs):
            if len(row) != num_cols:
                raise ValueError(f"La fila {i} tiene longitud inconsistente ({len(row)} vs {num_cols}).")
            for j, val in enumerate(row):
                if val < 0:
                    raise ValueError(f"Costo negativo en ({i},{j}): {val}.")

    # ──────────────────────────── Cuadrar matriz ───────────────────────────────

    def _square_matrix(self) -> Tuple[List[List[float]], Optional[str]]:
        """
        Si la matriz no es cuadrada, agrega filas/columnas ficticias con costo 0.

        Returns:
            (costs_cuadrada, dummy_type): dummy_type = "row", "column" o None.
        """
        costs = deepcopy(self._original_costs)
        m, n = self._original_rows, self._original_cols

        if m == n:
            return costs, None

        if m < n:
            # Faltan filas → agregar agentes ficticios
            for _ in range(n - m):
                costs.append([0.0] * n)
            return costs, "row"

        # Faltan columnas → agregar tareas ficticias
        for row in costs:
            row.extend([0.0] * (m - n))
        return costs, "column"

    # ──────────────────────────── Resolver ──────────────────────────────────────

    def solve(
        self,
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
    ) -> TransportResult:
        """
        Ejecuta el Método Húngaro.

        Args:
            row_labels: Etiquetas de agentes/trabajadores.
            col_labels: Etiquetas de tareas/trabajos.

        Returns:
            TransportResult compatible con la GUI existente.
        """
        costs_sq, dummy_type = self._square_matrix()
        n = len(costs_sq)

        # ── Etiquetas ──
        if row_labels is None:
            row_labels = [f"Agente {i+1}" for i in range(self._original_rows)]
        if col_labels is None:
            col_labels = [f"Tarea {j+1}" for j in range(self._original_cols)]

        final_row = list(row_labels)
        final_col = list(col_labels)

        if dummy_type == "row":
            for k in range(n - self._original_rows):
                final_row.append(f"Agente Ficticio {k+1}")
        elif dummy_type == "column":
            for k in range(n - self._original_cols):
                final_col.append(f"Tarea Ficticia {k+1}")

        # ── Pasos descriptivos ──
        steps: List[str] = []

        if dummy_type is None:
            steps.append(f"La matriz es cuadrada ({n}×{n}). No se requieren ficticios.")
        elif dummy_type == "row":
            steps.append(
                f"Matriz original {self._original_rows}×{self._original_cols}. "
                f"Se agregaron {n - self._original_rows} agente(s) ficticio(s) con costo 0."
            )
        else:
            steps.append(
                f"Matriz original {self._original_rows}×{self._original_cols}. "
                f"Se agregaron {n - self._original_cols} tarea(s) ficticia(s) con costo 0."
            )

        # ── Paso 1: Reducción por filas ──
        reduced = deepcopy(costs_sq)
        steps.append("\nPaso 1 — Reducción por filas (restar mínimo de cada fila):")
        for i in range(n):
            row_min = min(reduced[i])
            steps.append(f"  Fila {i} ({final_row[i]}): mínimo = {row_min:.2f}")
            for j in range(n):
                reduced[i][j] -= row_min
        steps.append("  Matriz reducida por filas:")
        steps.append(BaseTransportSolver.format_matrix(reduced, final_row, final_col))

        # ── Paso 2: Reducción por columnas ──
        steps.append("\nPaso 2 — Reducción por columnas (restar mínimo de cada columna):")
        for j in range(n):
            col_min = min(reduced[i][j] for i in range(n))
            steps.append(f"  Columna {j} ({final_col[j]}): mínimo = {col_min:.2f}")
            for i in range(n):
                reduced[i][j] -= col_min
        steps.append("  Matriz reducida por filas y columnas:")
        steps.append(BaseTransportSolver.format_matrix(reduced, final_row, final_col))

        # ── Paso 3: Asignación óptima con Munkres ──
        steps.append("\nPaso 3 — Asignación óptima (Algoritmo Húngaro / Munkres):")

        munkres = Munkres()
        # Munkres modifica la matriz internamente, pasamos copia
        indices = munkres.compute(deepcopy(costs_sq))

        # Construir matriz de asignación (1.0 en celda asignada, 0.0 resto)
        allocation = [[0.0] * n for _ in range(n)]
        total_cost = 0.0

        for row_idx, col_idx in indices:
            cost_val = costs_sq[row_idx][col_idx]
            allocation[row_idx][col_idx] = cost_val
            total_cost += cost_val

            # Solo reportar asignaciones reales (no ficticias)
            is_dummy_row = dummy_type == "row" and row_idx >= self._original_rows
            is_dummy_col = dummy_type == "column" and col_idx >= self._original_cols

            if is_dummy_row or is_dummy_col:
                steps.append(
                    f"  {final_row[row_idx]} → {final_col[col_idx]}: "
                    f"costo = {cost_val:.2f} (FICTICIO — no se ejecuta)"
                )
            else:
                steps.append(
                    f"  {final_row[row_idx]} → {final_col[col_idx]}: "
                    f"costo = {cost_val:.2f}"
                )

        steps.append("\n  Matriz de asignaciones:")
        steps.append(BaseTransportSolver.format_matrix(allocation, final_row, final_col))

        # ── Costo total real (excluir ficticios) ──
        real_cost = sum(
            costs_sq[r][c]
            for r, c in indices
            if not (dummy_type == "row" and r >= self._original_rows)
            and not (dummy_type == "column" and c >= self._original_cols)
        )

        steps.append(f"\n  Costo total de asignación: {real_cost:.2f}")

        # ── Supply/demand ficticios para compatibilidad con TransportResult ──
        fake_supply = [1.0] * n
        fake_demand = [1.0] * n

        return TransportResult(
            method_name=self.METHOD_NAME,
            allocation_matrix=allocation,
            total_cost=real_cost,
            balanced=dummy_type is None,
            dummy_type=dummy_type,
            original_supply=fake_supply[:self._original_rows],
            original_demand=fake_demand[:self._original_cols],
            balanced_supply=fake_supply,
            balanced_demand=fake_demand,
            cost_matrix_used=costs_sq,
            row_labels=final_row,
            col_labels=final_col,
            steps=steps,
        )
