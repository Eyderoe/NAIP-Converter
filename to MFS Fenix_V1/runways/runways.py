import sqlite3
import pandas as pd
import csvFunction as cf
import DatabaseFunction as dbf
import handle as hd
import os
import sys
import time

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\runways", "")

project_path = code_path.replace("\\programs", "")

PATH_addon = project_path + '\\input\\runwayAddon.xlsx'

db3_path = project_path + "\\input\\raw.db3"

xlsx_res = pd.read_excel(PATH_addon)

# 获取csv表格内容数据
LENGTH = xlsx_res.shape[0]
airport_code_list = xlsx_res['AirportCode'].to_list()
ident_list = xlsx_res['Ident'].to_list()
true_heading_list = xlsx_res['TrueHeading'].to_list()
length_list = xlsx_res['Length'].to_list()
width_list = xlsx_res['Width'].to_list()
surface_list = xlsx_res['Surface'].to_list()
latitude_list = xlsx_res['Latitude'].to_list()
longtitude_list = xlsx_res['Longtitude'].to_list()
elevation_list = xlsx_res['Elevation'].to_list()

conn = sqlite3.connect(db3_path)
cur = conn.cursor()


def format1(index: int):
    runway_id = str(dbf.get_runway_id(cur) + 1)
    airport_id = str(dbf.get_airports_id(cur, "'" + airport_code_list[index] + "'"))
    if airport_id == 'None':
        return
    str_ident = str(ident_list[index])
    ident = "'" + hd.handle_ident(str_ident) + "'"
    true_heading = str(true_heading_list[index])
    length = str(length_list[index])
    width = str(width_list[index])
    surface = "'" + str(surface_list[index]) + "'"
    latitude = str(latitude_list[index])
    longtitude = str(longtitude_list[index])
    elevation = str(elevation_list[index])
    data_list = [runway_id, airport_id, ident, true_heading,
                 length, width, surface, latitude, longtitude, elevation]
    dbf.insert_into_runway(cur, data_list)


def format2(index: int):
    runway_id = str(dbf.get_runway_id(cur) + 1)
    airport_id = str(dbf.get_airports_id(cur, "'" + airport_code_list[index] + "'"))
    if airport_id == "None":
        return
    ident = hd.handle_ident(str(ident_list[index]).replace(' ', ''))
    surface = "'ASP'"
    latitude = str(latitude_list[index])
    longtitude = str(longtitude_list[index])
    elevation = str(elevation_list[index])
    airport_code = str(airport_code_list[index])
    data_list = ([runway_id, airport_id] + cf.get_data(airport_code, ident)
                 + [surface, latitude, longtitude, elevation])
    dbf.insert_into_runway(cur, data_list)


print("\n\n")
progress = 0


for i in range(LENGTH):
    if i in range(0, LENGTH, int(LENGTH / 100)):
        print("\r", end="")
        print(f"\tProgress: {progress}% :", "█" * (progress // 2), end="")
        progress += 1
        sys.stdout.flush()
        time.sleep(0.05)

    if str(surface_list[i]) == 'nan':
        format2(i)
    else:
        format1(i)

conn.commit()
cur.close()
conn.close()

input("\n\tPress any key to cancel.")
