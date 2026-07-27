"""
Curaduría de calidad en ingesta (Etapa 1): exclusiones, borradores y deduplicación.
"""
import hashlib
import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".odt", ".pptx", ".xlsx", ".xls", ".csv", ".json", ".html", ".htm", ".md", ".txt",
}

SKIP_DIR_NAMES = {".rag_cache", "__pycache__", ".git", "node_modules"}

DRAFT_PATTERN = re.compile(
    r"(?i)(^|[\s_\-])(borrador|draft|tmp|temp|copia|copy|old|backup)([\s_\-]|\.|$)"
)

IGNORE_FILENAMES = {".ds_store", "thumbs.db", "desktop.ini"}


@dataclass
class CurationStats:
    scanned: int = 0
    accepted: int = 0
    skipped_unsupported: int = 0
    skipped_draft: int = 0
    skipped_duplicate: int = 0
    skipped_hidden: int = 0


def file_content_hash(path: str, block_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def should_skip_file(file_path: str) -> Tuple[bool, str]:
    name = os.path.basename(file_path)
    lower = name.lower()

    if lower in IGNORE_FILENAMES or name.startswith("."):
        return True, "hidden"

    ext = os.path.splitext(name)[1].lower()
    if DRAFT_PATTERN.search(name):
        return True, "draft"

    # Se permiten todos los formatos de archivo en la carga;
    # la indexación intentará extraer texto de formatos conocidos o texto plano.
    return False, ""


def curate_file_paths(all_paths: Iterable[str]) -> Tuple[List[str], CurationStats]:
    """
    Ordena rutas, descarta borradores/no soportados y deduplica por hash de contenido
    conservando el archivo con fecha de modificación más reciente.
    """
    stats = CurationStats()
    candidates: List[str] = []

    for path in sorted(set(all_paths)):
        stats.scanned += 1
        skip, reason = should_skip_file(path)
        if skip:
            if reason == "unsupported":
                stats.skipped_unsupported += 1
            elif reason == "draft":
                stats.skipped_draft += 1
            elif reason == "hidden":
                stats.skipped_hidden += 1
            continue
        candidates.append(path)

    hash_to_best: Dict[str, str] = {}
    for path in candidates:
        try:
            digest = file_content_hash(path)
        except OSError:
            stats.skipped_unsupported += 1
            continue

        if digest in hash_to_best:
            stats.skipped_duplicate += 1
            previous = hash_to_best[digest]
            if os.path.getmtime(path) > os.path.getmtime(previous):
                hash_to_best[digest] = path
        else:
            hash_to_best[digest] = path

    accepted = sorted(hash_to_best.values())
    stats.accepted = len(accepted)
    return accepted, stats
