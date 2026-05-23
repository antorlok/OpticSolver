"""
Método Húngaro (Munkres) — Implementación Manual Paso a Paso.

Pasos del algoritmo:
  1. Balanceo (ficticios) → cuadrar matriz NxN.
  2. Transformación para maximización (V_max - X_ij).
  3. Reducción por filas.
  4. Reducción por columnas.
  5. Cobertura de ceros (mínimo de líneas).
  6. Prueba de optimalidad y ajuste iterativo.
  7. Asignación final.

No depende de la librería `munkres`; todo el algoritmo está aquí.
"""

from typing import List, Optional, Tuple, Set
from copy import deepcopy

from core.base_solver import BaseTransportSolver, TransportResult


class HungarianSolver:
    """
    Resuelve problemas de asignación óptima mediante el Algoritmo Húngaro.

    Soporta:
      - Matrices no cuadradas (se cuadran con ficticios de costo 0).
      - Minimización (por defecto) y maximización (is_maximization=True).
    """

    METHOD_NAME = "Método Húngaro (Asignación)"

    def __init__(
        self,
        costs: List[List[float]],
        is_maximization: bool = False,
    ) -> None:
        """
        Args:
            costs: Matriz de costos/beneficios (no necesita ser cuadrada).
            is_maximization: True → maximizar beneficio; False → minimizar costo.
        """
        self._validate(costs)
        self._original_costs = deepcopy(costs)
        self._original_rows = len(costs)
        self._original_cols = len(costs[0])
        self._is_maximization = is_maximization

    # ──────────────────────────── Validación ────────────────────────────────────

    @staticmethod
    def _validate(costs: List[List[float]]) -> None:
        if not costs or not costs[0]:
            raise ValueError("La matriz de costos no puede estar vacía.")

        num_cols = len(costs[0])
        for i, row in enumerate(costs):
            if len(row) != num_cols:
                raise ValueError(
                    f"La fila {i} tiene longitud inconsistente ({len(row)} vs {num_cols})."
                )
            for j, val in enumerate(row):
                if val < 0:
                    raise ValueError(f"Costo negativo en ({i},{j}): {val}.")

    # ──────────────────────────── Paso 1: Balanceo ─────────────────────────────

    def _square_matrix(
        self, steps: List[str]
    ) -> Tuple[List[List[float]], Optional[str]]:
        """Cuadra la matriz con filas/columnas ficticias de costo 0."""
        costs = deepcopy(self._original_costs)
        m, n = self._original_rows, self._original_cols

        if m == n:
            steps.append(
                f"Paso 1 — Balanceo: La matriz es cuadrada ({n}×{n}). "
                "No se requieren ficticios."
            )
            return costs, None

        if m < n:
            for _ in range(n - m):
                costs.append([0.0] * n)
            steps.append(
                f"Paso 1 — Balanceo: Matriz original {m}×{n}. "
                f"Se agregaron {n - m} agente(s) ficticio(s) (filas con costo 0) "
                f"→ matriz {n}×{n}."
            )
            return costs, "row"

        # m > n
        for row in costs:
            row.extend([0.0] * (m - n))
        steps.append(
            f"Paso 1 — Balanceo: Matriz original {m}×{n}. "
            f"Se agregaron {m - n} tarea(s) ficticia(s) (columnas con costo 0) "
            f"→ matriz {m}×{m}."
        )
        return costs, "column"

    # ──────────────────────────── Paso 2: Transformación Max ────────────────────

    @staticmethod
    def _transform_for_maximization(
        matrix: List[List[float]], steps: List[str]
    ) -> None:
        """Aplica X_ij = V_max - X_ij in-place para convertir max → min."""
        n = len(matrix)
        v_max = max(matrix[i][j] for i in range(n) for j in range(n))
        steps.append(
            f"\nPaso 2 — Transformación para maximización: "
            f"V_max = {v_max:.2f}. Se aplica X_ij = {v_max:.2f} - X_ij."
        )
        for i in range(n):
            for j in range(n):
                matrix[i][j] = v_max - matrix[i][j]

    # ──────────────────────────── Paso 3: Reducción filas ──────────────────────

    @staticmethod
    def _reduce_rows(
        matrix: List[List[float]],
        n: int,
        row_labels: List[str],
        col_labels: List[str],
        steps: List[str],
    ) -> None:
        """Resta el mínimo de cada fila a toda la fila (in-place)."""
        steps.append("\nPaso 3 — Reducción por filas (restar mínimo de cada fila):")
        for i in range(n):
            row_min = min(matrix[i])
            steps.append(f"  Fila {i} ({row_labels[i]}): mínimo = {row_min:.2f}")
            for j in range(n):
                matrix[i][j] -= row_min
        steps.append("  Matriz reducida por filas:")
        steps.append(BaseTransportSolver.format_matrix(matrix, row_labels, col_labels))

    # ──────────────────────────── Paso 4: Reducción columnas ───────────────────

    @staticmethod
    def _reduce_cols(
        matrix: List[List[float]],
        n: int,
        row_labels: List[str],
        col_labels: List[str],
        steps: List[str],
    ) -> None:
        """Resta el mínimo de cada columna a toda la columna (in-place)."""
        steps.append(
            "\nPaso 4 — Reducción por columnas (restar mínimo de cada columna):"
        )
        for j in range(n):
            col_min = min(matrix[i][j] for i in range(n))
            steps.append(f"  Columna {j} ({col_labels[j]}): mínimo = {col_min:.2f}")
            for i in range(n):
                matrix[i][j] -= col_min
        steps.append("  Matriz reducida por filas y columnas:")
        steps.append(BaseTransportSolver.format_matrix(matrix, row_labels, col_labels))

    # ──────────────────────────── Paso 5: Cobertura de ceros ───────────────────

    @staticmethod
    def _find_min_lines(
        matrix: List[List[float]], n: int
    ) -> Tuple[Set[int], Set[int]]:
        """
        Encuentra el mínimo conjunto de líneas horizontales y verticales
        que cubren todos los ceros (König / método de marcado).

        Retorna (covered_rows, covered_cols).
        """
        # --- Asignación parcial con ceros para guiar el marcado ---
        row_assignment = [-1] * n  # row_assignment[i] = columna asignada a fila i
        col_assignment = [-1] * n  # col_assignment[j] = fila asignada a columna j

        for i in range(n):
            for j in range(n):
                if matrix[i][j] == 0 and row_assignment[i] == -1 and col_assignment[j] == -1:
                    row_assignment[i] = j
                    col_assignment[j] = i

        # --- Marcado (König) ---
        # 1. Marcar filas sin asignación
        marked_rows: Set[int] = set()
        marked_cols: Set[int] = set()

        unmarked_assigned_rows = set()
        for i in range(n):
            if row_assignment[i] == -1:
                marked_rows.add(i)
            else:
                unmarked_assigned_rows.add(i)

        # 2. Iterar hasta convergencia
        changed = True
        while changed:
            changed = False
            # Marcar columnas que tienen un cero en una fila marcada
            for i in marked_rows:
                for j in range(n):
                    if matrix[i][j] == 0 and j not in marked_cols:
                        marked_cols.add(j)
                        changed = True
            # Marcar filas que tienen asignación en una columna marcada
            for j in marked_cols:
                i = col_assignment[j]
                if i != -1 and i not in marked_rows:
                    marked_rows.add(i)
                    changed = True

        # 3. Líneas = filas NO marcadas ∪ columnas marcadas
        covered_rows = set(range(n)) - marked_rows
        covered_cols = set(marked_cols)
        return covered_rows, covered_cols

    # ──────────────────────────── Paso 6: Ajuste iterativo ─────────────────────

    @staticmethod
    def _adjust_matrix(
        matrix: List[List[float]],
        n: int,
        covered_rows: Set[int],
        covered_cols: Set[int],
    ) -> None:
        """
        Encuentra el menor elemento no cubierto, lo resta a los no cubiertos
        y lo suma a las intersecciones. Modifica la matriz in-place.
        """
        # Menor valor no cubierto
        min_uncovered = float("inf")
        for i in range(n):
            if i in covered_rows:
                continue
            for j in range(n):
                if j in covered_cols:
                    continue
                if matrix[i][j] < min_uncovered:
                    min_uncovered = matrix[i][j]

        # Aplicar ajuste
        for i in range(n):
            for j in range(n):
                if i not in covered_rows and j not in covered_cols:
                    matrix[i][j] -= min_uncovered
                elif i in covered_rows and j in covered_cols:
                    matrix[i][j] += min_uncovered

    # ──────────────────────────── Paso 7: Asignación final ─────────────────────

    @staticmethod
    def _optimal_assignment(
        matrix: List[List[float]], n: int
    ) -> List[Tuple[int, int]]:
        """
        Selecciona ceros para la asignación óptima 1-a-1.
        Prioriza filas/columnas con menor cantidad de ceros disponibles.
        Usa backtracking si la heurística greedy falla.
        """
        assignments: List[Tuple[int, int]] = []
        assigned_rows: Set[int] = set()
        assigned_cols: Set[int] = set()

        # Iterar priorizando filas/columnas con menos ceros
        while len(assignments) < n:
            best = None  # (count, is_row, index, zero_positions)

            # Evaluar filas no asignadas
            for i in range(n):
                if i in assigned_rows:
                    continue
                zeros = [
                    j for j in range(n)
                    if j not in assigned_cols and matrix[i][j] == 0
                ]
                if not zeros:
                    continue
                if best is None or len(zeros) < best[0]:
                    best = (len(zeros), True, i, zeros)

            # Evaluar columnas no asignadas
            for j in range(n):
                if j in assigned_cols:
                    continue
                zeros = [
                    i for i in range(n)
                    if i not in assigned_rows and matrix[i][j] == 0
                ]
                if not zeros:
                    continue
                if best is None or len(zeros) < best[0]:
                    best = (len(zeros), False, j, zeros)

            if best is None:
                # Fallback: si no quedan ceros, algo salió mal → intentar backtracking
                break

            _, is_row, idx, positions = best
            if is_row:
                j = positions[0]
                assignments.append((idx, j))
                assigned_rows.add(idx)
                assigned_cols.add(j)
            else:
                i = positions[0]
                assignments.append((i, idx))
                assigned_rows.add(i)
                assigned_cols.add(idx)

        # Si la heurística no logró n asignaciones, intentar backtracking completo
        if len(assignments) < n:
            result = HungarianSolver._backtrack_assign(matrix, n)
            if result:
                return result

        return assignments

    @staticmethod
    def _backtrack_assign(
        matrix: List[List[float]], n: int
    ) -> Optional[List[Tuple[int, int]]]:
        """Backtracking completo para encontrar asignación de n ceros independientes."""
        assigned_cols: List[int] = []

        def _solve(row: int) -> bool:
            if row == n:
                return True
            for j in range(n):
                if matrix[row][j] == 0 and j not in assigned_cols:
                    assigned_cols.append(j)
                    if _solve(row + 1):
                        return True
                    assigned_cols.pop()
            return False

        if _solve(0):
            return [(i, assigned_cols[i]) for i in range(n)]
        return None

    # ──────────────────────────── Resolver ──────────────────────────────────────

    def solve(
        self,
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
    ) -> TransportResult:
        """
        Ejecuta el Método Húngaro completo paso a paso.

        Returns:
            TransportResult compatible con la GUI existente.
        """
        steps: List[str] = []

        # ── Paso 1: Balanceo ──
        costs_sq, dummy_type = self._square_matrix(steps)
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

        # Mostrar la matriz balanceada
        steps.append("  Matriz balanceada:")
        steps.append(
            BaseTransportSolver.format_matrix(costs_sq, final_row, final_col)
        )

        # ── Paso 2: Transformación para maximización ──
        # Trabajamos sobre una copia para preservar la matriz de costos original (balanceada)
        working = deepcopy(costs_sq)

        if self._is_maximization:
            self._transform_for_maximization(working, steps)
            steps.append("  Matriz transformada (costos de oportunidad):")
            steps.append(
                BaseTransportSolver.format_matrix(working, final_row, final_col)
            )
        else:
            steps.append(
                "\nPaso 2 — Transformación para maximización: "
                "No aplica (modo minimización)."
            )

        # ── Paso 3: Reducción filas ──
        self._reduce_rows(working, n, final_row, final_col, steps)

        # ── Paso 4: Reducción columnas ──
        self._reduce_cols(working, n, final_row, final_col, steps)

        # ── Pasos 5-6: Cobertura de ceros + ajuste iterativo ──
        iteration = 0
        max_iterations = n * n  # Seguro contra loops infinitos
        while iteration < max_iterations:
            iteration += 1
            covered_rows, covered_cols = self._find_min_lines(working, n)
            num_lines = len(covered_rows) + len(covered_cols)

            # Formatear cuáles líneas se trazaron
            line_desc = []
            if covered_rows:
                line_desc.append(
                    "filas: " + ", ".join(
                        f"{i} ({final_row[i]})" for i in sorted(covered_rows)
                    )
                )
            if covered_cols:
                line_desc.append(
                    "columnas: " + ", ".join(
                        f"{j} ({final_col[j]})" for j in sorted(covered_cols)
                    )
                )

            steps.append(
                f"\nPaso 5 (iteración {iteration}) — Cobertura de ceros: "
                f"{num_lines} línea(s) trazan: {'; '.join(line_desc)}."
            )

            if num_lines >= n:
                steps.append(
                    f"  ✓ Número de líneas ({num_lines}) = n ({n}). "
                    "La solución es óptima."
                )
                break

            # Calcular el menor no cubierto para documentar
            min_unc = float("inf")
            for i in range(n):
                if i in covered_rows:
                    continue
                for j in range(n):
                    if j in covered_cols:
                        continue
                    if working[i][j] < min_unc:
                        min_unc = working[i][j]

            steps.append(
                f"  Número de líneas ({num_lines}) < n ({n}). "
                f"Menor elemento no cubierto = {min_unc:.2f}."
            )
            steps.append(
                f"\nPaso 6 (iteración {iteration}) — Ajuste: "
                f"Restar {min_unc:.2f} a no cubiertos, sumar a intersecciones."
            )

            self._adjust_matrix(working, n, covered_rows, covered_cols)

            steps.append("  Matriz ajustada:")
            steps.append(
                BaseTransportSolver.format_matrix(working, final_row, final_col)
            )

        # ── Paso 7: Asignación final ──
        steps.append("\nPaso 7 — Asignación final:")

        indices = self._optimal_assignment(working, n)

        allocation = [[0.0] * n for _ in range(n)]
        total_cost = 0.0

        for row_idx, col_idx in indices:
            # El costo real viene de la matriz balanceada original, NO de la working
            cost_val = costs_sq[row_idx][col_idx]
            allocation[row_idx][col_idx] = cost_val
            total_cost += cost_val

            is_dummy_row = dummy_type == "row" and row_idx >= self._original_rows
            is_dummy_col = dummy_type == "column" and col_idx >= self._original_cols

            tag = " (FICTICIO — no se ejecuta)" if (is_dummy_row or is_dummy_col) else ""
            steps.append(
                f"  {final_row[row_idx]} → {final_col[col_idx]}: "
                f"costo = {cost_val:.2f}{tag}"
            )

        steps.append("\n  Matriz de asignaciones:")
        steps.append(
            BaseTransportSolver.format_matrix(allocation, final_row, final_col)
        )

        # ── Costo real (excluir ficticios) ──
        real_cost = sum(
            costs_sq[r][c]
            for r, c in indices
            if not (dummy_type == "row" and r >= self._original_rows)
            and not (dummy_type == "column" and c >= self._original_cols)
        )

        obj_label = "beneficio" if self._is_maximization else "costo"
        steps.append(f"\n  {obj_label.capitalize()} total de asignación: {real_cost:.2f}")

        # ── Supply/demand ficticios para compatibilidad con TransportResult ──
        fake_supply = [1.0] * n
        fake_demand = [1.0] * n

        return TransportResult(
            method_name=self.METHOD_NAME,
            allocation_matrix=allocation,
            total_cost=real_cost,
            balanced=dummy_type is None,
            dummy_type=dummy_type,
            original_supply=fake_supply[: self._original_rows],
            original_demand=fake_demand[: self._original_cols],
            balanced_supply=fake_supply,
            balanced_demand=fake_demand,
            cost_matrix_used=costs_sq,
            row_labels=final_row,
            col_labels=final_col,
            steps=steps,
        )
