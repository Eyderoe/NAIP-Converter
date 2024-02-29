import sqlite3
import sys
import time
import pandas as pd
import DatabaseFunction as dbf
import handle as hd
import os

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\ilse", "")

project_path = code_path.replace("\\programs", "")

PATH_addon = project_path + "\\input\\IlsAddon.xlsx"

xlsx_res = pd.read_excel(PATH_addon)

db3_path = project_path + "\\input\\raw.db3"

exec_path = project_path + "\\error\\Runway_exception.txt"

with open(exec_path, "w") as f:
    f.write("")

# 获取csv表格内容数据
LENGTH = xlsx_res.shape[0]
freq_list = xlsx_res['Freq'].to_list()
gs_angle_list = xlsx_res['GsAngle'].to_list()
latitude_list = xlsx_res['Latitude'].to_list()
longtitude_list = xlsx_res['Longtitude'].to_list()
category_list = xlsx_res['Category'].to_list()
ident_list = xlsx_res['Ident'].to_list()
loc_course_list = xlsx_res['LocCourse'].to_list()
crossing_height_list = xlsx_res['CrossingHeight'].to_list()
has_dme_list = xlsx_res['HasDme'].to_list()
elevation_list = xlsx_res['Elevation'].to_list()
runway_ident_list = xlsx_res['RunwayIdent'].to_list()
airport_code_list = xlsx_res['AirportCode'].to_list()

conn = sqlite3.connect(db3_path)
cur = conn.cursor()

print("\n\n")
progress = 0

for i in range(LENGTH):
    if i in range(0, LENGTH, int(LENGTH/100)):
        print("\r", end="")
        print(f"\tProgress: {progress}% :", "█" * (progress // 2), end="")
        progress += 1
        sys.stdout.flush()
        time.sleep(0.05)

    runway_ident = hd.handle_ident(str(runway_ident_list[i]))
    airport_code = airport_code_list[i]
    airport_id = str(dbf.get_airports_id(cur, "'" + airport_code + "'"))

    if airport_id == "None":
        with open(exec_path, "a") as file:
            file.write(f"Don't find datas:\n"
                       f"airportCode:{airport_code}\n")
        continue

    runway_id = dbf.get_runway_id(cur, airport_id, "'" + runway_ident + "'")
    if runway_id is None:
        with open(exec_path, "a") as file:
            file.write(f"Don't find datas:\n"
                       f"airportID:{airport_id}, runwayIdent:{runway_ident}\n")
        continue
    runway_id = str(runway_id)
    ilses_id = str(dbf.get_ilses_id(cur) + 1)
    freq = str(freq_list[i])
    gs_angle = str(gs_angle_list[i])
    latitude = str(latitude_list[i])
    longtitude = str(longtitude_list[i])
    category = str(category_list[i])

    ident = "'" + str(ident_list[i]) + "'"
    loc_course = str(loc_course_list[i])
    crossing_height = str(crossing_height_list[i])
    has_dme = str(has_dme_list[i])
    elevation = str(elevation_list[i])
    dbf.insert_into_ilses(cur, [ilses_id, runway_id, freq,
                                gs_angle, latitude, longtitude,
                                category, ident, loc_course,
                                crossing_height, has_dme, elevation])

conn.commit()
cur.close()
conn.close()

input("\n\tPress any key to cancel.")
