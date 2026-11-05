def like_pattern(text: str) -> str:
    """Escapa %, _ y \\ para que el texto buscado se trate de forma literal."""
    escaped = text.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
