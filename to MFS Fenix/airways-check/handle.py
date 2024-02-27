from typing import List, Dict
import DatabaseFunctions as dbf
import sqlite3


def handle_airway_ident(string: str) -> str | None:
    if string[0] == '-':
        result = str(list(string).pop(0))
        return result

    elif string[0] + string[1] == 'XX':
        return None

    result = string
    return result


def handle_num(string: str) -> float:
    str_list = list(string)
    str_list.pop(0)
    second_str = str_list.pop(-2) + str_list.pop(-1)
    minute_str = str_list.pop(-2) + str_list.pop(-1)
    angle_str = ''.join(str_list)
    result = round(float(angle_str) + float(minute_str)/60 + float(second_str)/3600, 8)
    return result


def get_lines_from_database(results_for_same_airway) -> List[List[int]]:

    current_line = []
    lines_in_database = []

    for result_for_same_airway in results_for_same_airway:
        wpt1_id = result_for_same_airway[0]
        wpt2_id = result_for_same_airway[1]
        is_start = result_for_same_airway[2]
        is_end = result_for_same_airway[3]
        if is_start == 1:
            current_line = [wpt1_id, wpt2_id]
        if is_end == 1:
            if wpt2_id not in current_line:
                current_line.append(wpt2_id)
            lines_in_database.append(current_line)

        if is_start == 0 and is_end == 0:
            current_line.append(wpt2_id)

    return lines_in_database


def del_lines_in_database(cursor: sqlite3.Cursor, line: List[int], airway_id: int):
    for point in line:
        dbf.delete_data(cursor, 'AirwayLegs', {'AirwayID': airway_id, 'Waypoint1ID': point})

