import sqlite3
from typing import List
import DatabaseFunctions as dbf


def process_list(all_list: list, white: list = None, black: list = None) -> List[str]:
    if black is None:
        black = []
    if white is None or white == []:
        white = list(set(all_list) - set(black))
    return white


def process_record(cur: sqlite3.Cursor, data_list: list, flag: bool) -> list | None:
    ter_id = data_list[0]
    proc = data_list[1]
    name = data_list[2]

    if proc == 3 or not flag:
        if '-' in name:
            name = name.replace('-', '')
        return [[name]]

    wpt_ids = dbf.search_in(cur, "TerminalLegs", ["WptID"], {"TerminalID": ter_id})

    if wpt_ids is None:
        return None
    wpt_id = 0

    if proc == 2:
        wpt_id = wpt_ids[-1][0]

    if proc == 1:
        wpt_id = wpt_ids[0][0]

    result = dbf.search_in(cur, "Waypoints", ["Ident"], {"ID": wpt_id})
    return result
