from itertools import accumulate


def split_path(path: str) -> list[str]:
    return list(
        accumulate(
            path.split(":"),
            lambda x, y: f"{x}:{y}",
        )
    )
