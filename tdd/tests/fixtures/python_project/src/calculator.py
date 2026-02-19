"""Calculator module for arithmetic operations."""


class Calculator:
    """A simple calculator with basic arithmetic.

    Supports add, subtract, multiply, divide with
    error handling for division by zero.
    """

    def add(self, a: float, b: float) -> float:
        """Add two numbers and return the result."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b.

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def factorial(n: int) -> int:
    """Compute factorial of n.

    Args:
        n: Non-negative integer.

    Returns:
        n! as an integer.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def _internal_helper():
    """This is private and should not appear in API surface."""
    pass
