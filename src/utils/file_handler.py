import json
from typing import Any


def write_data(data: dict, filename: str) -> None:
    """Write data to json"""
    with open(filename, "w") as file:
        json.dump(data, file, sort_keys=True, indent=4, separators=(',', ': '))


def read_data(filename: str) -> Any | None:
    """Read data from json"""
    try:
        with open(filename, 'r') as file:
            file = json.load(file)
        return file
    except FileNotFoundError:
        return None
