"""
Cliente de integración con la API de Groq para generación de conclusiones logísticas.

Utiliza la librería oficial `groq` para comunicarse con modelos LLM.
La clave de API se lee exclusivamente de variables de entorno.
"""

import os
from typing import Optional
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

try:
    # pyrefly: ignore [missing-import]
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False


# ──────────────────────────── Prompts ──────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = (
    "Eres un Consultor Senior en Cadena de Suministro y Logística. "
    "Analiza los resultados de un problema de transporte resuelto con el {method_name}. "
    "Redacta una conclusión ejecutiva breve (máximo 2 párrafos) en español. "
    "Evalúa la eficiencia de las rutas seleccionadas, el impacto del balanceo "
    "(filas/columnas ficticias) en la logística real, y sugiere posibles mejoras operativas."
)

USER_PROMPT_TEMPLATE = """Se resolvió el siguiente problema de transporte:

### Tabla de Costos Unitarios (Original)
{cost_table}

### Oferta Original: {supply}
### Demanda Original: {demand}

### Estado de Balanceo
{balance_info}

### Matriz de Distribución (Asignaciones)
{allocation_table}

### Costo Total Mínimo: {total_cost:.2f}

### Pasos del Algoritmo
{steps}

Por favor, redacta una conclusión ejecutiva analizando:
1. La eficiencia de las rutas escogidas por el algoritmo.
2. Si el balanceo con ficticios afectó la logística real y cómo interpretarlo.
3. Recomendaciones operativas breves."""


class GroqClient:
    """
    Cliente para generar conclusiones logísticas usando la API de Groq.

    La clave de API se obtiene de la variable de entorno GROQ_API_KEY.
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        api_key: Optional[str] = None
    ) -> None:
        """
        Inicializa el cliente Groq.

        Args:
            model: Identificador del modelo LLM a utilizar.
            api_key: Clave de API de Groq. Si es None, busca en la variable de entorno GROQ_API_KEY.

        Raises:
            EnvironmentError: Si no se encuentra una clave de API.
            ImportError: Si la librería groq no está instalada.
        """
        if not _GROQ_AVAILABLE:
            raise ImportError(
                "La librería 'groq' no está instalada. Ejecuta: pip install groq"
            )

        final_key = api_key or os.environ.get("GROQ_API_KEY")
        if not final_key:
            raise EnvironmentError(
                "No se encontró la clave de API (GROQ_API_KEY)."
            )

        self._client = Groq(api_key=final_key)
        self._model = model

    def generate_conclusion(
        self,
        cost_table: str,
        supply: str,
        demand: str,
        balance_info: str,
        allocation_table: str,
        total_cost: float,
        steps: str,
        method_name: str = "Método del Costo Mínimo",
    ) -> str:
        """
        Envía los resultados del transporte a Groq y devuelve la conclusión ejecutiva.

        Args:
            cost_table: Tabla de costos formateada.
            supply: Representación textual de la oferta original.
            demand: Representación textual de la demanda original.
            balance_info: Descripción del estado de balanceo.
            allocation_table: Tabla de asignaciones formateada.
            total_cost: Costo total mínimo calculado.
            steps: Pasos del algoritmo formateados.

        Returns:
            Texto con la conclusión generada por el modelo.
        """
        user_content = USER_PROMPT_TEMPLATE.format(
            cost_table=cost_table,
            supply=supply,
            demand=demand,
            balance_info=balance_info,
            allocation_table=allocation_table,
            total_cost=total_cost,
            steps=steps,
        )

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(method_name=method_name)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=1024,
        )

        return response.choices[0].message.content or "(Sin respuesta del modelo)"
