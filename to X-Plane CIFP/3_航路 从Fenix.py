import sqlite3

import pandas as pd

from 公共函数 import *

# 读取数据库内容
databasePath = r"E:\Python项目\Fenix 数据库\raw.db3"
conn = sqlite3.connect(databasePath)
airways = pd.read_sql_query("select * from Airways", conn)
airwayLegs = pd.read_sql_query("select * from AirwayLegs", conn)
waypoints = pd.read_sql_query("select * from Waypoints", conn)
waypointsLook = pd.read_sql_query("select * from WaypointLookup", conn)
navaid = pd.read_sql_query("select * from Navaids", conn)
conn.close()
printf("读取完成", 3)
# 航路
airwayLegs = pd.merge(airwayLegs, airways, left_on="AirwayID", right_on="ID", how="right")
airwayLegs = airwayLegs.drop(["ID_x", "AirwayID", "IsStart", "IsEnd", "ID_y"], axis=1)
printf("航路修改完毕", 3)
# 航点
waypoints = pd.merge(waypoints, waypointsLook, left_on="ID", right_on="ID", how="right")
waypoints = waypoints.drop(["Collocated", "Ident_y", "Name", "Latitude", "Longtitude"], axis=1)
printf("航路点修改完毕", 3)
# 导航台
navaid = navaid[["ID", "Type"]]
navaid.loc[navaid.shape[0]] = {"ID": navaid.shape[0] + 1, "Type": 11}  # 给普通航点预留
printf("导航台修改完毕", 3)
# 合并航点 导航台
waypoints.fillna(navaid.shape[0], inplace=True)
waypoints = pd.merge(waypoints, navaid, left_on="NavaidID", right_on="ID", how="left")
waypoints = waypoints.drop(["NavaidID", "ID_y"], axis=1)
printf("航路 导航台 合并完成", 3)
# 合并航路 航点
airwayLegs = pd.merge(airwayLegs, waypoints, left_on="Waypoint1ID", right_on="ID_x", how="left")
airwayLegs = airwayLegs.drop(["Waypoint1ID", "ID_x"], axis=1)
airwayLegs = airwayLegs.rename(columns={"Ident_x": "fromIdent", "Country": "fromArea", "Type": "fromType"})
airwayLegs = pd.merge(airwayLegs, waypoints, left_on="Waypoint2ID", right_on="ID_x", how="left")
airwayLegs = airwayLegs.drop(["Waypoint2ID", "ID_x"], axis=1)
airwayLegs = airwayLegs.rename(columns={"Ident_x": "toIdent", "Country": "toArea", "Type": "toType"})
printf("航点 航路 合并完成", 3)
# 开写
master = []
for i in range(airwayLegs.shape[0]):
    i = airwayLegs.iloc[i, :].tolist()
    # Level Ident fromIdent fromArea  fromType toIdent toArea  toType
    i = i[2:] + ['F', i[0], 0, 0, i[1]]
    i = [str(j) for j in i]
    if "nan" in i:
        continue
    # 修正类型
    for loc in (2, 5):
        i[loc] = int(float(i[loc]))
        if i[loc] == 11:
            i[loc] = "11"
        elif i[loc] == 5:
            i[loc] = '2'
        elif i[loc] in (1, 2, 3, 4, 9):
            i[loc] = '3'
        else:
            printf("奇异类型:{}".format(i[loc]), 2)
    # 高低航路
    if i[7] == 'B':
        i[7] = '1'
        master.append(' '.join(i))
        i[7] = '2'
        master.append(' '.join(i))
    elif i[7] == 'L':
        i[7] = '1'
        master.append(' '.join(i))
    elif i[7] == 'H':
        i[7] = '2'
        master.append(' '.join(i))
# 写入到文件
master = [i + '\n' for i in master]
file = open(r"E:\Python项目\Fenix 重构\X-Plane\output\awy.dat", 'w', encoding="utf-8")
file.writelines(master)
file.close()
