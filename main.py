def hello(name):
    return f'Hello, {name}!'


def test_hello():
    name = 'John'
    assert hello(name) == 'Hello, John!'


if __name__ == '__main__':
    print(hello('John'))

    test_hello()
