import gamelib

def is_all_filled(game_state, points):
    """
    Checks if every point in points is filled by a stationary unit
    """
    contains = 0
    for location in points:
        if game_state.contains_stationary_unit(location):
            contains += 1

    return contains == len(points)

def is_all_upgraded(game_state, points):
    """
    Checks if every point in points has an upgraded
    """
    num_of_upgraded = 0
    for location in points:
        for unit in game_state.game_map[location]:
            if unit.upgraded:
                num_of_upgraded += 1

    return num_of_upgraded == len(points)
