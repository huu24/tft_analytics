def calc_win_rate(wins, total_games):
    return wins / total_games if total_games > 0 else 0.0


def calc_top4_rate(top4s, total_games):
    return top4s / total_games if total_games > 0 else 0.0


def calc_avg_placement(placements, total_games):
    return sum(placements) / total_games if total_games > 0 else 0.0


def calc_pick_rate(games_with, total_games):
    return games_with / total_games if total_games > 0 else 0.0


def calc_meta_score(win_rate, top4_rate, avg_placement, pick_rate):
    if avg_placement <= 0:
        return 0.0
    inv_placement = 1.0 / avg_placement
    return 0.4 * win_rate + 0.3 * top4_rate + 0.2 * inv_placement + 0.1 * pick_rate


def calc_flex_score(compositions, total_games):
    if not compositions or total_games <= 0:
        return 0.0
    max_count = max(compositions.values())
    return 1.0 - (max_count / total_games)


def calc_item_accuracy(player_items, recommended_items):
    p_set = set(player_items)
    r_set = set(recommended_items)
    union = p_set | r_set
    return len(p_set & r_set) / len(union) if union else 0.0


def identify_core_units(comp_units, threshold=0.6):
    return [unit for unit, freq in comp_units.items() if freq >= threshold]
