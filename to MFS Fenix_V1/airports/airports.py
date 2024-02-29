import sqlite3
import pandas as pd
import pinyin
import DatabaseFunction as dbf
import handle as hd
import os
import sys
import time

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\airports", "")

project_path = code_path.replace("\\programs", "")

PATH_AD_HP = project_path + '\\input\\AD_HP.csv'

db3_path = project_path + "\\input\\raw.db3"

csv_res = pd.read_csv(PATH_AD_HP, encoding='gbk')

# 获取csv表格内容数据
length = csv_res.shape[0]
name_list = csv_res['TXT_NAME'].to_list()
icao_list = csv_res['CODE_ID'].to_list()
latitude_list = csv_res['GEO_LAT_ACCURACY'].to_list()
longtitude_list = csv_res['GEO_LONG_ACCURACY'].to_list()
elevation_list = csv_res['VAL_ELEV'].to_list()
transition_altitude_list = csv_res['VAL_TRANSITION_ALT'].to_list()
transition_level_list = csv_res['VAL_TRANSITION_LEVEL'].to_list()

conn = sqlite3.connect(db3_path)
cur = conn.cursor()

print("\n\n")
progress = 0

for i in range(length):
    if i in range(0, length, int(length / 100)):

        print("\r", end="")
        print(f"\tProgress: {progress}% :", "█" * (progress // 2), end="")
        progress += 1
        sys.stdout.flush()
        time.sleep(0.05)

    # 获取code_id并判断
    icao = str(icao_list[i])
    if dbf.ICAO_exist(cur, icao) or icao == "nan":
        continue
    else:

        # 从csv中获取并处理
        airport_id = str(dbf.get_airports_id(cur) + 1)
        txt_name = str(name_list[i])
        name_cn = txt_name.split('/')
        name = "'" + pinyin.get(name_cn[-1], format='strip', delimiter='').upper() + "'"
        icao = str(icao)
        ext_id = "'" + icao[0] + icao[1] + icao + "'"
        icao = "'" + icao + "'"
        primary_id = 'NULL'
        latitude = str(hd.handle_num(latitude_list[i]))
        longtitude = str(hd.handle_num(longtitude_list[i]))
        elevation = str(round(elevation_list[i] * 3.28, 0))
        transition_altitude = str(hd.handle_trs(transition_altitude_list[i]))
        transition_level = str(hd.handle_trs(transition_level_list[i]))
        speed_limit = '250'
        speed_limit_altitude = '10000'

        data_list = [airport_id, name,
                     icao, primary_id, latitude,
                     longtitude, elevation, transition_altitude,
                     transition_level, speed_limit, speed_limit_altitude]

        dbf.inset_into_airports(cur, data_list)
        if dbf.query_in_lookup(cur, ext_id):
            pass
        else:
            dbf.insert_into_lookup(cur, [ext_id, airport_id])

conn.commit()
cur.close()
conn.close()

input("\n\tPress any key to cancel.")

