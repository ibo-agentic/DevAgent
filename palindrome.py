def is_palindrome(s):
    return s == s[::-1]

# Test the function
result = is_palindrome('racecar')
print(result)