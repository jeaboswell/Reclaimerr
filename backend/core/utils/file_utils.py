def bytes_to_gb(bytes_size: float | int) -> float | int:
    """
    Convert bytes to gigabytes (GB).
    Uses the binary definition (1 GB = 1024^3 bytes).
    """
    gb_size = bytes_size / (1024**3)
    return gb_size
