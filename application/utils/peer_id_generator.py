import random


def generate_peer_id():
    """Генерирует уникальный peer_id."""
    return "-PC0001-" + "".join([str(random.randint(0, 9)) for _ in range(12)])