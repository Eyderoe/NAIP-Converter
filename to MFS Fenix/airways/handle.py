from typing import List, Dict
import csvhandle as csvh
import DatabaseFunctions as dbf
import sqlite3

Fake_id = 20000000


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


def find_same(line1: list, line2: list) -> List[int]:
    result = []
    for point in line2:
        if point in line1:
            result.append(point)
    return result


def handle_line(line1: list, line2: list) -> List[int] | None | int:

    # 先找到相同点
    same_points = find_same(line1, line2)
    len1 = len(line1)
    len2 = len(line2)

    if len(same_points) == 0:

        # 情况1 ： 如果没有相同点就返回错误值
        return None

    if len(same_points) == len2:

        # 情况2 ： 说明是大嵌小
        return line1

    if len(same_points) == 1:

        # 情况3 ： 发现只有一个相同点
        # 若发现都是边界点, 则说明是边界添加
        same_point = same_points.pop()
        flag1 = 0
        flag2 = 0
        loc1 = line1.index(same_point)
        loc2 = line2.index(same_point)

        line1_new = []
        line2_new = []

        if loc1 == 0:
            flag1 = 1
            line1_new = line1

        if loc1 == len1 - 1:
            flag1 = 1
            line1_new = line1[::-1]

        if loc2 == 0:
            flag2 = 1
            line2_new = line2[::-1]

        if loc2 == len2 - 1:
            flag2 = 1
            line2_new = line2

        if flag1 == 1 and flag2 == 1:
            line2_new.pop()
            line_new = line2_new + line1_new
            return line_new

        else:

            # 说明线段不能完结
            return 0

    else:

        back_flag = 0
        # 情况4 ： 一般线段
        # 保存位置
        loc_in_1 = []
        loc_in_2 = []
        for same_point in same_points:
            loc_in_1.append(line1.index(same_point))
            loc_in_2.append(line2.index(same_point))

        # 开始正序
        if loc_in_1[0] > loc_in_1[-1]:
            back_flag = 1
            line1 = line1[::-1]
            loc_in_1.clear()
            for same_point in same_points:
                loc_in_1.append(line1.index(same_point))

        if loc_in_2[0] > loc_in_2[-1]:
            line2 = line2[::-1]
            loc_in_2.clear()
            for same_point in same_points:
                loc_in_2.append(line2.index(same_point))

        flag1 = 0
        flag2 = 0

        if loc_in_1[0] == 0:
            flag1 = 1

        if loc_in_2[0] == 0:
            flag2 = 1

        if flag1 == 1 or flag2 == 1:
            loc_in_1 = [0] + loc_in_1 + [len1 - 1]
            loc_in_2 = [0] + loc_in_2 + [len2 - 1]
            spl = len(loc_in_1) - 1

            line_new = []

            for i in range(spl):
                para1 = line1[loc_in_1[i]: loc_in_1[i + 1]]
                para2 = line2[loc_in_2[i]: loc_in_2[i + 1]]
                para = []
                if i == 0:
                    para = para1 + para2
                elif i == spl - 1:
                    para1.append(line1[-1])
                    para2.append(line2[-1])
                    para1.pop(0)
                    para2.pop(0)
                    para = [line1[loc_in_1[i]]] + para1 + para2
                else:
                    para1.pop(0)
                    para2.pop(0)
                    para = [line1[loc_in_1[i]]] + para1 + para2
                line_new += para

            if back_flag == 0:
                return line_new
            else:
                return line_new[::-1]
        else:
            # 情况5 ： 分支
            return -1


def get_from_csv(cursor: sqlite3.Cursor, dict_airway: dict[str: List[List[str]]],
                 dict_waypoint: dict[int: List[str | float]]):
    csvh.csv_handle(cursor, dict_airway, dict_waypoint)


def insert_into_airway(cursor: sqlite3.Cursor, airway_id: int, line: List):
    global Fake_id
    line_length = len(line)
    # 依次读入点来插入
    for i in range(line_length - 1):
        is_start_insert = 0
        is_end_insert = 0
        if i == 0:
            is_start_insert = 1
        if i == line_length - 2:
            is_end_insert = 1
        start_point_insert = line[i]
        end_point_insert = line[i + 1]
        Fake_id += 1
        data_list = [Fake_id, airway_id, 'B', start_point_insert,
                     end_point_insert, is_start_insert, is_end_insert]
        val = dbf.insert_into(cursor, 'AirwayLegs', data_list)
        if not val:
            print('Error!\n')


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
    line_length = len(line)
    for i in range(line_length - 1):
        w1p = line[i]
        w2p = line[i + 1]
        dbf.delete_data(cursor, 'AirwayLegs', {'AirwayID': airway_id, 'Waypoint1ID': w1p, 'Waypoint2ID': w2p})