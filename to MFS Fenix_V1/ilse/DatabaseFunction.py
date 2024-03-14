import sqlite3
import os
import sys

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\ilse", "")

project_path = code_path.replace("\\programs", "")

exec_path = project_path + "\\error\\ilse_exception.txt"

with open(exec_path, 'w') as file:
    file.writelines('')


def get_airports_id(cursor: sqlite3.Cursor, airport_code: str) -> int | None:
    query_sentence = ("SELECT `ID`"
                      "FROM `Airports` "
                      "WHERE `ICAO` = ") + airport_code
    cursor.execute(query_sentence)
    results = cursor.fetchall()
    if len(results) == 0:
        with open(exec_path, 'a') as file:
            inform = f"Error: Don't find {airport_code}\n"
            file.write(inform)
        return None
    result = results[0][0]
    return result


def get_ilses_id(cursor: sqlite3.Cursor) -> int:
    query_sentence = ("SELECT COUNT(`ID`)"
                      "FROM `ILSes`")
    cursor.execute(query_sentence)
    result = cursor.fetchall()[0][0]
    return result


def insert_into_ilses(cursor: sqlite3.Cursor, data_list:list[str]):
    data_str = '('
    length = len(data_list)
    for i, data in enumerate(data_list):
        if data == 'nan' or data == "'nan'":
            data = 'NULL'
        if i != length - 1:
            data_str += data + ', '
        else:
            data_str += data + ')'
    insert_sentence = ("INSERT INTO `ilses`"
                       "VALUES ") + data_str

    cursor.execute(insert_sentence)


def get_runway_id(cursor: sqlite3.Cursor, airport_id, runway_ident):
    sentence = (f"SELECT `ID`"
                f"FROM `Runways`"
                f"WHERE AirportID = {airport_id}"
                f" AND Ident = {runway_ident}")
    cursor.execute(sentence)
    result = cursor.fetchall()
    if not result:
        return None
    else:
        return result[0][0]