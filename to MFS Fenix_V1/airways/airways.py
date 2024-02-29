import sqlite3
import DatabaseFunctions as dbf
import handle as hd
import os
import sys

Fake_airway_id = 20000000

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\airways", "")

project_path = code_path.replace("\\programs", "")

db3_path = project_path + "\\input\\raw.db3"

exec_path = project_path + "\\error\\Airway_exception.txt"

conn = sqlite3.connect(db3_path)
cur = conn.cursor()

dict_airway = dict()
dict_waypoint = dict()

new_airways = dict()

# get_from_csv可以直接从csv中读取并保存在data_airway.txt中
# get_from_txt则是从data_airway.txt中读取
# 先用get_from_csv可以保存之后一直使用data_airway.txt中debug了

with open(exec_path, 'w') as file:
    file.write('')

hd.get_from_csv(cur, dict_airway, dict_waypoint)

with open(exec_path, 'a') as file:
    for airway_name in dict_airway:

        if '-' in airway_name:
            with open(exec_path,"a") as file:
                file.write(f"'-' in {airway_name}\n")
            airway_name = airway_name.replace('-', '')

        # 分别按照键值来获取线段
        lines = dict_airway[airway_name]

        for line in lines:

            # 遍历分条处理线段
            airway_id = dbf.search_in(cur, 'Airways', ['ID'], {'Ident': airway_name})

            if airway_id is None:

                # 如果在数据库里未找到 则直接添加
                airway_id_new = dbf.get_id(cur, 'Airways') + 1

                # 向Airway表格添加
                dbf.insert_into(cur, 'Airways', [airway_id_new, airway_name])

                # 向AirwayLegs表格添加
                # 正向添加
                hd.insert_into_airway(cur, airway_id_new, line)
                # 反向添加
                hd.insert_into_airway(cur, airway_id_new, line[::-1])

            else:

                # 如果在数据库里找到了对应的Airway ID
                airway_id = airway_id[0][0]
                results_for_same_airway = dbf.search_in(cur, 'AirwayLegs',
                                                        ['Waypoint1ID', 'Waypoint2ID', 'IsStart', 'IsEnd'],
                                                        {'AirwayID': airway_id})

                # 发现数据库中没有Airway对应的线段
                if results_for_same_airway is None:

                    # 向AirwayLegs表格里添加
                    # 正向添加
                    hd.insert_into_airway(cur, airway_id, line)
                    # 反向添加
                    hd.insert_into_airway(cur, airway_id, line[::-1])

                else:

                    # 找到了相应的线段集
                    lines_in_database = hd.get_lines_from_database(results_for_same_airway)

                    # 从csv获取的线段就是 line
                    line_in_csv = line
                    find_flag = 0

                    for line_in_database in lines_in_database:
                        # 遍历查找 看遍历的线段是否和其存在相同点

                        new_line = hd.handle_line(line_in_database, line_in_csv)

                        if new_line == lines_in_database:
                            # 说明没有改变
                            find_flag = 1
                            pass

                        elif new_line is None:
                            # 说明不存在相同点
                            pass

                        elif new_line == -1:
                            # 说明出现了分支
                            file.write(f'Error: Multi-branch\n{str(line_in_csv)}\n{line_in_database}')

                        elif new_line == 0:
                            file.write(f'Error: No end line\n{str(line_in_csv)}\n{line_in_database}')

                        else:
                            # 说明正常合成了线段
                            # 删除原有数据
                            find_flag = 1
                            hd.del_lines_in_database(cur, line_in_database, airway_id)
                            # 插入新的数据
                            # hd.insert_into_airway(cur, airway_id, new_line)

                            if airway_id in new_airways.keys():
                                new_airways[airway_id].append(new_line)
                            else:
                                new_airways[airway_id] = [new_line]

                    if find_flag == 0:
                        # 没有找到 则直接插入数据
                        # 正向添加
                        hd.insert_into_airway(cur, airway_id, line)
                        # 反向添加
                        hd.insert_into_airway(cur, airway_id, line[::-1])

for airway_id in new_airways.keys():
    for new_line in new_airways[airway_id]:
        hd.insert_into_airway(cur, airway_id, new_line)

# 重置所有的ID
dbf.reset_id(cur, 'AirwayLegs')

conn.commit()
cur.close()
conn.close()

input("\n\tPress any key to cancel.")

