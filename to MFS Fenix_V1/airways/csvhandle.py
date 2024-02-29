from typing import List, Dict
import pandas as pd
import sqlite3
import DatabaseFunctions as dbf
import handle as hd
import os
import sys

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\airways", "")

project_path = code_path.replace("\\programs", "")

exec_path = project_path + "\\error\\Airway_exception.txt"


csv_file_path = project_path + '\\input\\RTE_SEG.csv'
csvPD = pd.read_csv(csv_file_path, encoding='gbk')
SPC = csvPD['CODE_POINT_START'].tolist()  # 起始点名称列表
SLA = csvPD['GEO_LAT_START_ACCURACY'].tolist()  # 起始点纬度列表
SLO = csvPD['GEO_LONG_START_ACCURACY'].tolist()  # 起始点经度列表
EPC = csvPD['CODE_POINT_END'].tolist()  # 结束点名称列表
ELA = csvPD['GEO_LAT_END_ACCURACY'].tolist()  # 结束点纬度列表
ELO = csvPD['GEO_LONG_END_ACCURACY'].tolist()  # 结束点经度列表
TD = csvPD['TXT_DESIG'].tolist()  # AirID的列表

two_sides_flag = 1


def csv_handle(cursor: sqlite3.Cursor, dict_airway: dict[str: List[List[str]]],
               dict_waypoint: dict[int: List[str | float]]):
    # cursor：主函数使用的数据库游标
    # 这两个Dist都是空的，用来存储真实的airway和从csv读取的数据

    # 开始遍历csv表格
    # pre_airway_ident用来对比分块

    shape = csvPD.shape[0]
    cur_airway_ident = ''
    pre_airway_ident = cur_airway_ident
    cur_end_point_id = -1
    pre_end_point_id = cur_end_point_id
    current_line = []
    for i in range(shape):
        pre_airway_ident = cur_airway_ident
        pre_end_point_id = cur_end_point_id
        # 获取airway_id并判读
        airway_ident = hd.handle_airway_ident(TD[i])
        # 如果airway id不是XX开头

        if airway_ident is not None:

            if '-' in airway_ident:
                airway_ident = airway_ident.replace('-', '')

            cur_airway_ident = airway_ident
            # 获取起始点的名称经纬度，用来获取WaypointID
            start_point = SPC[i]
            start_point_latitude = hd.handle_num(SLA[i])
            start_point_longitude = hd.handle_num(SLO[i])

            # 获取结束点的名称经纬度，用来获取WaypointID
            end_point = EPC[i]
            end_point_latitude = hd.handle_num(ELA[i])
            end_point_longitude = hd.handle_num(ELO[i])

            if '/' in start_point:
                new_name = ''
                for j in range(5):
                    new_name += start_point[j]
                start_point = new_name
            if '/' in end_point:
                new_name = ''
                for j in range(5):
                    new_name += end_point[j]
                end_point = new_name

            wpt_id_s = dbf.found_point_id(cursor, start_point, start_point_latitude, start_point_longitude)
            spl = [start_point, start_point_latitude, start_point_longitude]

            wpt_id_e = dbf.found_point_id(cursor, end_point, end_point_latitude, end_point_longitude)
            epl = [end_point, end_point_latitude, end_point_longitude]
            cur_end_point_id = wpt_id_e

            # 三种对 current line的操作
            # 1.创建新的current line
            # 2.结束current line
            # 3.继续存储current line

            # 上一条线段的结束以及存入
            # 存入后应立马开始存当前行读取的数据
            # 存入的情况分析：
            # 1.读取到错误行且上一条线段不是错误线段应该立刻结束上一条线段并读取
            # 如果是错误线段 则创建新的current line
            # 2.如果读取的值不是错误的，但是发现是新的线段，则应该立刻结束并存储
            if wpt_id_s is None or wpt_id_e is None:
                # 读取到错误线段了

                #  报错
                inform = (f"Error: In database don't found data:\n"
                          f"{spl}\n"
                          f"{epl}\n")

                with open(exec_path, "a") as file:
                    file.write(inform)

                if None not in current_line:
                    # 判断发现上一条数据无误
                    # 开始存入
                    if pre_airway_ident in dict_airway.keys():
                        dict_airway[pre_airway_ident].append(current_line)
                    else:
                        dict_airway[pre_airway_ident] = [current_line]
                else:
                    # 发现上一条数据有误
                    # 直接跳过
                    pass
                # 无论怎么样 创建新的current line
                current_line = [wpt_id_s, wpt_id_e]
            else:
                # 如果发现仍然是当前线段并且没有读取错误，则继续记入当前行并循环
                if None not in current_line:
                    # 判断发现上一条数据无误
                    # 开始判断
                    if pre_airway_ident == airway_ident and pre_end_point_id == wpt_id_s:
                        # 说明还是着一块的, 按照原来操作
                        current_line.append(cur_end_point_id)

                    elif pre_airway_ident in dict_airway.keys():
                        # 已经不是一条线段了
                        # 此处发现并没有存入
                        dict_airway[pre_airway_ident].append(current_line)
                        current_line = [wpt_id_s, wpt_id_e]
                    else:
                        dict_airway[pre_airway_ident] = [current_line]
                        current_line = [wpt_id_s, wpt_id_e]

                else:
                    # 发现上一条数据有误
                    # 创建新的
                    current_line = [wpt_id_s, wpt_id_e]
                    pass

    # 最后一条current line 还需要存一次
    if None not in current_line:
        # 判断发现上一条数据无误
        # 开始存入
        if cur_airway_ident in dict_airway.keys():
            dict_airway[cur_airway_ident].append(current_line)
        else:
            dict_airway[cur_airway_ident] = [current_line]
    else:
        # 发现上一条数据有误
        # 直接跳过
        pass

    del dict_airway['']
