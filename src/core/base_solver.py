"""
Módulo base con lógica compartida entre todos los métodos de transporte.

Contiene: validación de entrada, balanceo de matriz, cálculo de costo total,
formateo de matrices y la estructura de resultados (TransportResult).
"""

from typing import List, Tuple, Optional
from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class TransportResult:
    """Estructura con los resultados de cualquier algoritmo de transporte."""

    method_name: str
    allocation_matrix: List[List[float]]
    total_cost: float
    balanced: bool
    dummy_type: Optional[str]  # "row", "column" o None
    original_supply: List[float]
    original_demand: List[float]
    balanced_supply: List[float]
    balanced_demand: List[float]
    cost_matrix_used: List[List[float]]
    row_labels: List[str] = field(default_factory=list)
    col_labels: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    @property
    def balance_info(self) -> str:
        """Construye la descripción textual del estado de balanceo (DRY)."""
        if self.balanced:
            return "El problema estaba balanceado (Oferta == Demanda). No se agregaron ficticios."

        if self.dummy_type == "column":
            return (
                f"Oferta ({sum(self.original_supply):.2f}) > Demanda ({sum(self.original_demand):.2f}). "
                f"Se agregó una CIUDAD FICTICIA (columna) con costo 0 para absorber el excedente."
            )

        return (
            f"Demanda ({sum(self.original_demand):.2f}) > Oferta ({sum(self.original_supply):.2f}). "
            f"Se agregó una PLANTA FICTICIA (fila) con costo 0 para cubrir el déficit."
        )

    @property
    def formatted_allocation_matrix(self) -> str:
        """Retorna la representación tabular de la matriz de asignación."""
        return BaseTransportSolver.format_matrix(
            self.allocation_matrix,
            row_labels=self.row_labels,
            col_labels=self.col_labels
        )

    @property
    def formatted_cost_matrix(self) -> str:
        """Retorna la representación tabular de la matriz de costos utilizada."""
        return BaseTransportSolver.format_matrix(
            self.cost_matrix_used,
            row_labels=self.row_labels,
            col_labels=self.col_labels
        )


class BaseTransportSolver:
    """
    Clase base con lógica compartida: validación, balanceo, costo total y formateo.

    Las subclases solo deben implementar el método _allocate() con su algoritmo específico.
    """

    METHOD_NAME: str = "Base"

    def __init__(
        self,
        costs: List[List[float]],
        supply: List[float],
        demand: List[float],
    ) -> None:
        """
        Inicializa el solver validando los datos de entrada.

        Args:
            costs: Matriz m×n de costos unitarios.
            supply: Vector de m ofertas.
            demand: Vector de n demandas.

        Raises:
            ValueError: Si las dimensiones no coinciden o hay valores negativos.
        """
        self._validate_inputs(costs, supply, demand)
        self._original_costs = deepcopy(costs)
        self._original_supply = list(supply)
        self._original_demand = list(demand)

    # ──────────────────────────── Validación (Guard Clauses) ────────────────────

    @staticmethod
    def _validate_inputs(
        costs: List[List[float]],
        supply: List[float],
        demand: List[float],
    ) -> None:
        """Valida dimensiones, tipos y valores no negativos."""
        if not costs or not supply or not demand:
            raise ValueError("La matriz de costos, oferta y demanda no pueden estar vacías.")

        num_rows = len(costs)
        num_cols = len(costs[0])

        if len(supply) != num_rows:
            raise ValueError(
                f"El vector de oferta ({len(supply)}) no coincide con las filas de la matriz ({num_rows})."
            )
        if len(demand) != num_cols:
            raise ValueError(
                f"El vector de demanda ({len(demand)}) no coincide con las columnas de la matriz ({num_cols})."
            )

        for i, row in enumerate(costs):
            if len(row) != num_cols:
                raise ValueError(f"La fila {i} de la matriz tiene longitud inconsistente.")
            for j, val in enumerate(row):
                if val < 0:
                    raise ValueError(f"Costo negativo en ({i},{j}): {val}.")

        if any(s < 0 for s in supply):
            raise ValueError("La oferta no puede contener valores negativos.")
        if any(d < 0 for d in demand):
            raise ValueError("La demanda no puede contener valores negativos.")

    # ──────────────────────────── Balanceo ──────────────────────────────────────

    def _balance(self) -> Tuple[List[List[float]], List[float], List[float], Optional[str]]:
        """
        Balancea la matriz agregando filas/columnas ficticias si es necesario.

        Returns:
            Tupla (costs, supply, demand, dummy_type) donde dummy_type indica
            si se agregó "row", "column" o None.
        """
        costs = deepcopy(self._original_costs)
        supply = list(self._original_supply)
        demand = list(self._original_demand)

        total_supply = sum(supply)
        total_demand = sum(demand)

        if total_supply == total_demand:
            return costs, supply, demand, None

        # Oferta > Demanda → columna ficticia con costo 0
        if total_supply > total_demand:
            diff = total_supply - total_demand
            for row in costs:
                row.append(0.0)
            demand.append(diff)
            return costs, supply, demand, "column"

        # Demanda > Oferta → fila ficticia con costo 0
        diff = total_demand - total_supply
        num_cols = len(demand)
        costs.append([0.0] * num_cols)
        supply.append(diff)
        return costs, supply, demand, "row"

    # ──────────────────────────── Preparación de etiquetas ─────────────────────

    def _prepare_labels(
        self,
        dummy_type: Optional[str],
        row_labels: Optional[List[str]],
        col_labels: Optional[List[str]],
    ) -> Tuple[List[str], List[str]]:
        """Genera etiquetas finales ajustadas al balanceo."""
        if row_labels is None:
            row_labels = [f"Planta {i+1}" for i in range(len(self._original_supply))]
        if col_labels is None:
            col_labels = [f"Ciudad {j+1}" for j in range(len(self._original_demand))]

        final_row = list(row_labels)
        final_col = list(col_labels)

        if dummy_type == "row":
            final_row.append("Planta Ficticia")
        elif dummy_type == "column":
            final_col.append("Ciudad Ficticia")

        return final_row, final_col

    # ──────────────────────────── Pasos de balanceo ────────────────────────────

    def _balance_steps(self, dummy_type: Optional[str]) -> List[str]:
        """Genera los pasos descriptivos del balanceo."""
        total_s = sum(self._original_supply)
        total_d = sum(self._original_demand)
        steps: List[str] = []

        if dummy_type == "column":
            diff = total_s - total_d
            steps.append(
                f"Oferta ({total_s:.0f}) > Demanda ({total_d:.0f}). "
                f"Se agregó destino ficticio con demanda = {diff:.2f}."
            )
        elif dummy_type == "row":
            diff = total_d - total_s
            steps.append(
                f"Demanda ({total_d:.0f}) > Oferta ({total_s:.0f}). "
                f"Se agregó origen ficticio con oferta = {diff:.2f}."
            )
        else:
            steps.append("La oferta y demanda están balanceadas. No se requieren ficticios.")

        return steps

    # ──────────────────────────── Costo total ──────────────────────────────────

    @staticmethod
    def compute_total_cost(
        allocation: List[List[float]],
        costs: List[List[float]],
    ) -> float:
        """Calcula Σ(asignación_ij × costo_ij) para toda la matriz."""
        return sum(
            allocation[i][j] * costs[i][j]
            for i in range(len(allocation))
            for j in range(len(allocation[0]))
        )

    # ──────────────────────────── Solve (Template Method) ──────────────────────

    def solve(
        self,
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
    ) -> TransportResult:
        """
        Ejecuta el algoritmo de transporte (Template Method).

        Args:
            row_labels: Nombres personalizados para las filas (plantas).
            col_labels: Nombres personalizados para las columnas (ciudades).

        Returns:
            TransportResult con la matriz de asignaciones, costo total y metadata.
        """
        costs, supply, demand, dummy_type = self._balance()
        m, n = len(supply), len(demand)

        final_row_labels, final_col_labels = self._prepare_labels(
            dummy_type, row_labels, col_labels
        )

        steps = self._balance_steps(dummy_type)

        # Delegado a la subclase
        allocation = self._allocate(costs, supply, demand, m, n, steps, final_row_labels, final_col_labels)

        total_cost = self.compute_total_cost(allocation, costs)

        return TransportResult(
            method_name=self.METHOD_NAME,
            allocation_matrix=allocation,
            total_cost=total_cost,
            balanced=dummy_type is None,
            dummy_type=dummy_type,
            original_supply=list(self._original_supply),
            original_demand=list(self._original_demand),
            balanced_supply=supply,
            balanced_demand=demand,
            cost_matrix_used=costs,
            row_labels=final_row_labels,
            col_labels=final_col_labels,
            steps=steps,
        )

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
        """
        Método abstracto: cada subclase implementa su estrategia de asignación.

        Raises:
            NotImplementedError: Si no es sobreescrito por la subclase.
        """
        raise NotImplementedError("Las subclases deben implementar _allocate()")

    def _add_allocation_step(
        self,
        steps: List[str],
        allocation: List[List[float]],
        row_labels: List[str],
        col_labels: List[str],
        supply_remaining: Optional[List[float]] = None,
        demand_remaining: Optional[List[float]] = None,
        row_penalties: Optional[List[Optional[float]]] = None,
        col_penalties: Optional[List[Optional[float]]] = None,
    ) -> None:
        """Registra la matriz de asignaciones actual en los pasos del algoritmo (DRY)."""
        steps.append("  Matriz de asignaciones actual:")
        steps.append(self.format_matrix(
            allocation, row_labels, col_labels,
            supply_remaining=supply_remaining,
            demand_remaining=demand_remaining,
            row_penalties=row_penalties,
            col_penalties=col_penalties,
        ))

    # ──────────────────────────── Formateo ─────────────────────────────────────

    @staticmethod
    def format_matrix(
        matrix: List[List[float]],
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
        supply_remaining: Optional[List[float]] = None,
        demand_remaining: Optional[List[float]] = None,
        row_penalties: Optional[List[Optional[float]]] = None,
        col_penalties: Optional[List[Optional[float]]] = None,
    ) -> str:
        """
        Genera una representación tabular legible de una matriz.

        Parámetros opcionales para mostrar contexto completo de cada iteración:
        - supply_remaining: vector de oferta restante (columna "Oferta" a la derecha).
        - demand_remaining: vector de demanda restante (fila "Demanda" al fondo).
        - row_penalties: penalizaciones por fila (columna "Pen.F", solo Vogel).
        - col_penalties: penalizaciones por columna (fila "Pen.C", solo Vogel).
        """
        m = len(matrix)
        n = len(matrix[0]) if m else 0

        if row_labels is None:
            row_labels = [f"O{i+1}" for i in range(m)]
        if col_labels is None:
            col_labels = [f"D{j+1}" for j in range(n)]

        # ── Helpers para formatear valores opcionales ──
        def _fmt(val: Optional[float]) -> str:
            return "—" if val is None else f"{val:.2f}"

        # ── Calcular ancho de columna considerando todas las piezas ──
        extra_vals: List[str] = []
        if supply_remaining:
            extra_vals += [_fmt(v) for v in supply_remaining]
        if demand_remaining:
            extra_vals += [_fmt(v) for v in demand_remaining]
        if row_penalties:
            extra_vals += [_fmt(v) for v in row_penalties]
        if col_penalties:
            extra_vals += [_fmt(v) for v in col_penalties]

        extra_labels = []
        if supply_remaining is not None:
            extra_labels.append("Oferta")
        if row_penalties is not None:
            extra_labels.append("Pen.F")

        col_width = max(
            max((len(f"{matrix[i][j]:.2f}") for i in range(m) for j in range(n)), default=6),
            max((len(lbl) for lbl in col_labels), default=4),
            max((len(lbl) for lbl in row_labels), default=4),
            max((len(s) for s in extra_vals), default=0),
            max((len(s) for s in extra_labels), default=0),
            len("Demanda"), len("Pen.C"),
        )

        # ── Cabecera ──
        header_parts = [lbl.rjust(col_width) for lbl in col_labels]
        if supply_remaining is not None:
            header_parts.append("Oferta".rjust(col_width))
        if row_penalties is not None:
            header_parts.append("Pen.F".rjust(col_width))
        header = " " * (col_width + 2) + "  ".join(header_parts)

        lines = [header]

        # ── Filas de datos ──
        for i, row in enumerate(matrix):
            parts = [f"{v:.2f}".rjust(col_width) for v in row]
            if supply_remaining is not None:
                parts.append(_fmt(supply_remaining[i]).rjust(col_width))
            if row_penalties is not None:
                parts.append(_fmt(row_penalties[i]).rjust(col_width))
            lines.append(f"{row_labels[i].rjust(col_width)}  {'  '.join(parts)}")

        # ── Fila de demanda ──
        if demand_remaining is not None:
            dem_parts = [_fmt(demand_remaining[j]).rjust(col_width) for j in range(n)]
            # Celdas vacías para las columnas extra (Oferta, Pen.F)
            if supply_remaining is not None:
                dem_parts.append(" " * col_width)
            if row_penalties is not None:
                dem_parts.append(" " * col_width)
            lines.append(f"{'Demanda'.rjust(col_width)}  {'  '.join(dem_parts)}")

        # ── Fila de penalizaciones de columna ──
        if col_penalties is not None:
            pen_parts = [_fmt(col_penalties[j]).rjust(col_width) for j in range(n)]
            if supply_remaining is not None:
                pen_parts.append(" " * col_width)
            if row_penalties is not None:
                pen_parts.append(" " * col_width)
            lines.append(f"{'Pen.C'.rjust(col_width)}  {'  '.join(pen_parts)}")

        return "\n".join(lines)
