import sqlite3
import os
import sys

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\runways", "")

project_path = code_path.replace("\\programs", "")

exec_path = project_path + "\\error\\Runway_exception.txt"

with open(exec_path, 'w') as file:
    file.writelines('')


def get_airports_id(cursor: sqlite3.Cursor, airport_code: str) -> int | None:
    query_sentence = ("SELECT `ID`"
                      "FROM `Airports` "
                      "WHERE `ICAO` = ") + airport_code
    cursor.execute(query_sentence)
    results = cursor.fetchall()
    if len(results) == 0:
        with open(exec_path, 'a') as f:
            f.writelines(airport_code)
        return None
    result = results[0][0]
    return result


def get_runway_id(cursor: sqlite3.Cursor) -> int:
    query_sentence = ("SELECT COUNT(`ID`)"
                      "FROM `Runways`")
    cursor.execute(query_sentence)
    result = cursor.fetchall()[0][0]
    return result


def insert_into_runway(cursor: sqlite3.Cursor, data_list: list[str]):
    data_str = '('
    length = len(data_list)
    for i, data in enumerate(data_list):
        if i != length - 1:
            data_str += data + ', '
        else:
            data_str += data + ')'
    insert_sentence = ("INSERT INTO `Runways`"
                       "VALUES ") + data_str

    cursor.execute(insert_sentence)

