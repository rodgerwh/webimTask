import random
import string


def generate_data(length: int) -> str:
    data = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
    return data
