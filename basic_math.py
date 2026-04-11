# basic_math.py
"""
Utility module for solving basic arithmetic problems.
Provides simple functions for addition, subtraction, multiplication, and division.
All functions accept numbers (int or float) and return the result.
Division by zero raises a ZeroDivisionError.
"""

def add(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract(a, b):
    """Return the difference of a and b (a - b)."""
    return a - b


def multiply(a, b):
    """Return the product of a and b."""
    return a * b


def divide(a, b):
    """Return the quotient of a divided by b.

    Raises:
        ZeroDivisionError: If b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    return a / b

# Optional helper to evaluate a simple expression string like "2 + 3 * 4"
import operator
import re

_operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}

def evaluate_expression(expr: str) -> float:
    """Evaluate a very simple arithmetic expression.

    Supports +, -, *, / and respects left‑to‑right evaluation without
    operator precedence. Spaces are optional.
    Example: evaluate_expression("2+3*4") returns 20 (since we evaluate left to right).
    """
    # Tokenize numbers and operators
    tokens = re.findall(r"\d+\.?\d*|[+\-*/]", expr.replace(' ', ''))
    if not tokens:
        raise ValueError("Empty expression")
    # Start with the first number
    result = float(tokens[0])
    i = 1
    while i < len(tokens):
        op = tokens[i]
        nxt = float(tokens[i + 1])
        result = _operators[op](result, nxt)
        i += 2
    return result

if __name__ == "__main__":
    # Simple demo when run directly
    print("Add 2 + 3 =>", add(2, 3))
    print("Subtract 5 - 2 =>", subtract(5, 2))
    print("Multiply 4 * 3 =>", multiply(4, 3))
    print("Divide 10 / 2 =>", divide(10, 2))
    print('Evaluate "2+3*4" =>', evaluate_expression('2+3*4'))
