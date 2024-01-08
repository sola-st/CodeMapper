def get_a():
    a = "this is a test"
    return a

if __name__ == "__main__":
    result = get_a()
    print("hello.py was run directly. Result:", result)
else:
    print("hello.py was imported as a module.")
