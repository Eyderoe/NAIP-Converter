import sqlite3


def ICAO_exist(cursor: sqlite3.Cursor, code_id: str) -> bool:
    query_sentence = ("SELECT * "
                      "FROM `Airports` "
                      "WHERE `ICAO` = '") + code_id + "'"
    cursor.execute(query_sentence)
    result = cursor.fetchall()
    if len(result) == 0:
        return False
    else:
        return True


def inset_into_airports(cursor: sqlite3.Cursor, data_list: list[str]):
    data_str = '('
    length = len(data_list)
    for i, data in enumerate(data_list):
        if i != length-1:
            data_str += data + ', '
        else:
            data_str += data + ')'
    insert_into_sentence = ("INSERT INTO `Airports`"
                            "VALUES ") + data_str
    cursor.execute(insert_into_sentence)


def query_in_lookup(cursor: sqlite3.Cursor, ext_id: str) -> bool:
    query_sentence = ("SELECT *"
                      "FROM `AirportLookup`"
                      "WHERE `extID` = ") + ext_id
    cursor.execute(query_sentence)
    result = cursor.fetchall()
    if len(result) == 0:
        return False
    else:
        return True


def insert_into_lookup(cursor: sqlite3.Cursor, data_list: list[str]):
    data_str = '('
    length = len(data_list)
    for i, data in enumerate(data_list):
        if i != length - 1:
            data_str += data + ', '
        else:
            data_str += data + ')'
    insert_into_sentence = ("INSERT INTO `AirportLookup`"
                            "VALUES ") + data_str
    cursor.execute(insert_into_sentence)


def get_airports_id(cursor: sqlite3.Cursor) -> int:
    query_sentence = ("SELECT COUNT(`ID`)"
                      "FROM `Airports` ")
    cursor.execute(query_sentence)
    result = cursor.fetchall()[0][0]
    return result
