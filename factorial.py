def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

# Calling the factorial function and printing the result for 7
result = factorial(7)
print(result)