_DB: dict[str, list[dict]] = {"items": [], "workouts": []}


def get_db() -> dict[str, list[dict]]:
    return _DB
