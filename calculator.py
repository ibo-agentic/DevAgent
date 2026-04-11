# calculator.py
"""
A simple command-line calculator.

Usage:
    python calculator.py <operation> <num1> <num2>

Supported operations:
    add (+)      - addition
    sub (-)      - subtraction
    mul (*)      - multiplication
    div (/)      - division

Examples:
    python calculator.py add 3 5   # prints 8
    python calculator.py / 10 2   # prints 5.0
"""
import sys

def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def div(a, b):
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    return a / b

operations = {
    'add': add,
    '+': add,
    'sub': sub,
    '-': sub,
    'mul': mul,
    '*': mul,
    'div': div,
    '/': div,
}

def main():
    if len(sys.argv) != 4:
        print("Usage: python calculator.py <operation> <num1> <num2>")
        sys.exit(1)
    op, a_str, b_str = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        a = float(a_str)
        b = float(b_str)
    except ValueError:
        print("Both numbers must be valid numeric values.")
        sys.exit(1)
    func = operations.get(op.lower())
    if func is None:
        print(f"Unsupported operation '{op}'. Supported: {', '.join(sorted(set(operations.keys())))}")
        sys.exit(1)
    try:
        result = func(a, b)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    # Print integer if result is whole number
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    print(result)

if __name__ == "__main__":
    main()
