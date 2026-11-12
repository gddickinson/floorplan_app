"""
Length formatting and unit conversion (inches are the model unit; no GUI dependencies).
"""


def format_dimension(inches: float, unit: str = "ft") -> str:
    """
    Format a dimension in inches to a readable string.
    
    Args:
        inches: Dimension in inches
        unit: Target unit ('ft', 'in', or 'auto')
    
    Returns:
        Formatted string (e.g., "10' 6\"" or "126\"")
    """
    if unit == "in":
        return f'{inches:.1f}"'
    elif unit == "ft" or (unit == "auto" and abs(inches) >= 12):
        sign = "-" if inches < 0 else ""
        size = abs(inches)
        feet = int(size // 12)
        remaining_inches = size % 12
        if remaining_inches >= 11.95:  # would print as 12.0": carry into the feet
            feet += 1
            remaining_inches = 0.0
        if remaining_inches < 0.1:
            return f"{sign if feet else ''}{feet}'"
        else:
            return f"{sign}{feet}' {remaining_inches:.1f}\""
    else:
        return f'{inches:.1f}"'


def inches_to_feet(inches: float) -> float:
    """Convert inches to feet."""
    return inches / 12.0


def feet_to_inches(feet: float) -> float:
    """Convert feet to inches."""
    return feet * 12.0
