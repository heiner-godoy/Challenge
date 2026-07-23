"""
Registro central de categorías, carpetas y aliases (Etapa 1: organización).
Unifica nombres de carpetas, etiquetas de negocio, IDs del frontend y filtros de búsqueda.
"""
from typing import Dict, List, Optional, Set, Tuple

# slug de carpeta bajo DATA_DIR -> (etiqueta de negocio, responsable)
FOLDER_CATEGORY_OWNERS: Dict[str, Tuple[str, str]] = {
    "rh": ("Recursos Humanos", "rh@aluratech.com"),
    "recursos_humanos": ("Recursos Humanos", "rh@aluratech.com"),
    "rrhh": ("Recursos Humanos", "rh@aluratech.com"),
    "financiero": ("Finanzas y Presupuestos", "finanzas@aluratech.com"),
    "finanzas": ("Finanzas y Presupuestos", "finanzas@aluratech.com"),
    "juridico": ("Legal y Compliance", "legal@aluratech.com"),
    "legal": ("Legal y Compliance", "legal@aluratech.com"),
    "operaciones": ("Operaciones y Procesos", "operaciones@aluratech.com"),
    "operacional": ("Operaciones y Procesos", "operaciones@aluratech.com"),
    "logistica": ("Logística y Envíos", "logistica@aluratech.com"),
    "tecnologia": ("Tecnología y Ciberseguridad", "it@aluratech.com"),
    "it": ("Tecnología y Ciberseguridad", "it@aluratech.com"),
    "datos": ("Tecnología y Ciberseguridad", "it@aluratech.com"),
    "comunicacion": ("Comunicación Corporativa", "comunicacion@aluratech.com"),
    "marketing": ("Marketing", "marketing@aluratech.com"),
    "calidad": ("Calidad", "calidad@aluratech.com"),
    "estrategico": ("Estratégico", "estrategia@aluratech.com"),
    "id": ("Investigación y Desarrollo", "id@aluratech.com"),
    "general": ("General Corporativo", "soporte@aluratech.com"),
}

DEFAULT_CATEGORY = ("General Corporativo", "soporte@aluratech.com")

# IDs del frontend Angular -> slug de carpeta recomendado para uploads
FRONTEND_AREA_TO_FOLDER: Dict[str, str] = {
    "rrhh": "rh",
    "financiero": "financiero",
    "legal": "juridico",
    "operacional": "operaciones",
    "logistica": "logistica",
    "datos": "tecnologia",
    "comunicacion": "comunicacion",
    "marketing": "marketing",
    "calidad": "calidad",
    "estrategico": "estrategico",
    "id": "id",
}


def resolve_folder_metadata(folder_slug: str) -> Tuple[str, str]:
    key = (folder_slug or "").strip().lower()
    return FOLDER_CATEGORY_OWNERS.get(key, DEFAULT_CATEGORY)


def list_business_categories() -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for label, _ in FOLDER_CATEGORY_OWNERS.values():
        if label not in seen:
            seen.add(label)
            out.append(label)
    return sorted(out)


def expand_category_filter(filter_input: Optional[str]) -> Optional[Set[str]]:
    """
    Convierte un filtro (ID frontend, slug de carpeta o etiqueta parcial) en tokens
    comparables contra chunk.category.
    """
    if not filter_input or not filter_input.strip():
        return None

    raw = filter_input.strip().lower()
    tokens: Set[str] = {raw}

    folder = FRONTEND_AREA_TO_FOLDER.get(raw, raw)
    tokens.add(folder)

    if folder in FOLDER_CATEGORY_OWNERS:
        label, _ = FOLDER_CATEGORY_OWNERS[folder]
        tokens.add(label.lower())
        for part in label.lower().replace(" y ", " ").split():
            if len(part) > 3:
                tokens.add(part)

    for slug, (label, _) in FOLDER_CATEGORY_OWNERS.items():
        if raw == slug or raw in label.lower():
            tokens.add(label.lower())
            tokens.add(slug)

    return tokens


def category_matches(chunk_category: str, filter_input: Optional[str]) -> bool:
    if not filter_input or not filter_input.strip():
        return True

    cc = chunk_category.lower()
    tokens = expand_category_filter(filter_input)
    if not tokens:
        return True

    for token in tokens:
        if token in cc or cc in token:
            return True
    return False
