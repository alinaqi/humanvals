"""FizzBuzz implementation.

Provides a single function ``fizzbuzz`` that returns a list of strings
representing the classic FizzBuzz sequence for numbers ``1`` through ``n``.

The function is pure and side‑effect‑free, making it easy to import and test.
"""



def fizzbuzz(n: int) -> list[str]:
    """Return the FizzBuzz sequence from 1 to ``n``.

    Args:
        n: The inclusive upper bound of the sequence. If ``n`` is less than ``1``
           an empty list is returned.

    Returns:
        A list of strings where each element is:
        * ``"FizzBuzz"`` if the index is divisible by both 3 and 5,
        * ``"Fizz"`` if the index is divisible by 3 only,
        * ``"Buzz"`` if the index is divisible by 5 only,
        * otherwise the number itself as a string.
    """
    if n < 1:
        return []

    result: list[str] = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result
