def format_time(ms: int, show_ms: bool = False) -> str:
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, milliseconds = divmod(rem, 1_000)

    if hours:
        base = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        base = f"{minutes:02d}:{seconds:02d}"

    if show_ms:
        return f"{base}:{milliseconds:03d}"

    return base
