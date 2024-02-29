import sqlite3
import math
from typing import List, Dict, Any


def empty(data, null_val=None) -> bool:
    if null_val is None:
        null_val = ['NULL', 'nan', ' ', '']
    try:
        if data is None:
            return True
        if math.isnan(data):
            return True
        else:
            return False
    except TypeError:
        if data in null_val:
            return True
    return False


def insert_into(cur: sqlite3.Cursor, table: str, data_list: list) -> bool:
    data_str = '('
    length = len(data_list)
    for i, data in enumerate(data_list):
        if empty(data):
            data = 'NULL'
        if type(data) is str:
            if data == 'NULL':
                pass
            else:
                data = "'" + data + "'"
        if type(data) is int or type(data) is float:
            data = str(data)
        if i < length - 1:
            data_str += data + ', '
        else:
            data_str += data + ')'

    sentence = ("INSERT INTO " + "`" + table + "` "
                + "VALUES " + data_str)
    try:
        cur.execute(sentence)
        return True
    except sqlite3.Error:
        print('Insert into ERROR:\n' + data_str + '\n\n')
        return False


# 条件数据的列表格式:
# ['ID':23, 'Ident':'UI88']
# 得到数据的列表格式:
# ['Latitude', 'Longitude']
def search_in(cur: sqlite3.Cursor, table: str, get_col_list: list, conditions_dict: dict) -> List | None:
    conditions_str = ""
    dict_length = len(conditions_dict)
    i = 0
    for index in conditions_dict:
        data = conditions_dict[index]
        index = "`" + index + "`"
        if empty(data):
            data = 'NULL'
        if type(data) is str:
            if data == 'NULL':
                pass
            else:
                data = "'" + data + "'"
        if type(data) is int or type(data) is float:
            data = str(data)
        if i < dict_length - 1:
            single_str = index + " = " + data + " AND "
            conditions_str += single_str
        else:
            single_str = index + " = " + data
            conditions_str += single_str
        i += 1

    list_length = len(get_col_list)
    get_col_str = ""
    for i, col in enumerate(get_col_list):
        if col != '*':
            col = "`" + col + "`"
        if i < list_length - 1:
            get_col_str += col + ', '
        else:
            get_col_str += col + ' '

    sentence = ("SELECT " + get_col_str +
                "FROM `" + table + "` "
                "WHERE " + conditions_str)

    try:
        cur.execute(sentence)
        results = cur.fetchall()
        if len(results) == 0:
            return None
        else:
            return results
    except sqlite3.Error:
        print('Search ERROR:\n' + conditions_str + '\n\n')
        return None


def get_id(cur: sqlite3.Cursor, table:str) -> int:
    sentence = ("SELECT COUNT(`ID`) "
                "FROM `" + table + "`")
    cur.execute(sentence)
    result = cur.fetchall()[0][0]
    return result


def found_point_id(cur: sqlite3.Cursor, ident: str, lat: float, lon: float, valve: float = None) -> int | None:
    if valve is None:
        valve = 0.4
    sentence = ("SELECT `Latitude`, `Longtitude`, `ID`"
                "FROM `Waypoints` "
                "WHERE `Ident` = '" + ident + "'")
    cur.execute(sentence)
    results = cur.fetchall()
    if results is None:
        return -1
    else:
        point_id = None
        for result in results:
            get_lat = result[0]
            get_lon = result[1]
            if -valve < get_lat - lat < valve and -valve < get_lon - lon < valve:
                point_id = result[2]
            else:
                pass

    return point_id


def delete_data(cursor: sqlite3.Cursor, table: str, conditions_dict: Dict):
    conditions_str = ""
    dict_length = len(conditions_dict)
    i = 0
    for index in conditions_dict:
        data = conditions_dict[index]
        index = "`" + index + "`"
        if empty(data):
            data = 'NULL'
        if type(data) is str:
            if data == 'NULL':
                pass
            else:
                data = "'" + data + "'"
        if type(data) is int or type(data) is float:
            data = str(data)
        if i < dict_length - 1:
            single_str = index + " = " + data + " AND "
            conditions_str += single_str
        else:
            single_str = index + " = " + data
            conditions_str += single_str
        i += 1
    sentence = "DELETE FROM " + f'`{table}` WHERE' + conditions_str
    cursor.execute(sentence)


def reset_id(cursor: sqlite3.Cursor, table: str):
    sentence_get = f"SELECT * FROM {table} "
    sentence_del = f"DELETE FROM {table}"
    cursor.execute(sentence_get)
    results = cursor.fetchall()
    cursor.execute(sentence_del)
    length = len(results)
    for i in range(length):
        results[i][0] = i + 1
        insert_into(cursor, table, results[i])
