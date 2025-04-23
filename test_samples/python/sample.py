"""Sample Python file for testing the Python analyzer."""

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    result = calculate_fibonacci(10)
    print(f"The 10th Fibonacci number is: {result}")
    
    user_input = input("Enter a command: ")
    import os
    os.system(user_input)  # Bandit should flag this

if __name__ == "__main__":
    main()
