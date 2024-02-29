import sqlite3
import pandas as pd
import os
import glob
import pinyin
import DatabaseFunctions as df
import handle as hd
import sys

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\waypoints-navaids", "")

project_path = code_path.replace("\\programs", "")

# 航路点信息文件的绝对路径
ZXXX_Waypoint_path = project_path + "\\output"
lunatic_path = ZXXX_Waypoint_path + '\\lunatic.txt'

# earth_nav.dat的路径
dat_path = project_path + "\\input\\earth_nav.dat"

# 报错输出文件的绝对路径
exception_log_path = project_path + '\\error\\Waypoints_exception.txt'

# csv表格（VOR VDB）文件的绝对路径
VOR_path = project_path + "\\input\\VOR.csv"
NDB_path = project_path + "\\input\\NDB.csv"

# 数据库文件
db3_path = project_path + "\\input\\raw.db3"

# 数据库的连接
con = sqlite3.connect(db3_path)
cur = con.cursor()

# 路径列表指定
txt_file_list = glob.glob(os.path.join(ZXXX_Waypoint_path, 'Z*_waypoint.txt'))
txt_file_list.append(lunatic_path)

# 报错函数
def exception_output(inform: str):
    with open(exception_log_path, 'a') as e_f:
        e_f.write(inform + '\n')


# 初始化报错文件
with open(exception_log_path, 'w') as e:
    e.write('')

VOR_read = pd.read_csv(VOR_path, encoding='gbk')
NDB_read = pd.read_csv(NDB_path, encoding='gbk')

file_len = len(txt_file_list)
# 依次获取航路点文件的txt文件
for file_path in txt_file_list:
    # 读取文件
    file_num = txt_file_list.index(file_path) + 1

    with open(file_path, 'r') as file:

        # 初始化国家
        Country_Chars = ''
        file_Flag = 0

        # 获取txt文件的名称
        File_Chars = file.name.split('\\')[len(file.name.split('\\')) - 1]

        # 打印处理的文件名
        print(f"Processing {File_Chars} ({file_num}/{file_len}) \n")

        # 如果是lunatic.txt
        if File_Chars == 'lunatic.txt':
            file_Flag = 1

        # 如果是普通的ZXXX_Waypoints文件
        if file_Flag == 0:
            Country_Chars = '' + File_Chars[0] + File_Chars[1]

        # 访问从txt中获取的每一行数据
        DataLines = file.readlines()
        for Data in DataLines:

            Ident_Flag = 0  # 标记是否在这些行找到数据存在

            # 将读取的行数据分开得到 名称 纬度 经度，如果是从lunatic.txt获得，还有第四个数据。
            data = Data.split()
            ident = data[0]
            Latitude_from_txt = float(data[1])
            Longtitude_from_txt = float(data[2])
            if file_Flag == 1:
                Country_Chars = data[3]

            # 判断是不是RWXX，Valve是阈值
            RW_Flag = 0
            Valve = 0
            ident_length = len(ident)
            if ident_length > 3:
                if ident[0] + ident[1] == 'RW':
                    if ident[2].isdigit() and ident[3].isdigit():
                        RW_Flag = 1

            if RW_Flag == 1:
                Valve = 0.1
            else:
                Valve = 0.4

            # SQL操作，查询对应名称的数据
            results = df.search_in(cur, 'Waypoints', ['Latitude', 'Longtitude', 'NavaidID'], {'Ident': ident})

            # 如果在Waypoint表李查询到了同字段的Ident
            if results:

                # 打印找到的结果
                results_len = len(results)
                for result in results:

                    num = results.index(result) + 1
                    Latitude = result[0]
                    Longtitude = result[1]
                    NavaidID = result[2]

                    # 在阈值之内，找到同一点
                    if -Valve < Latitude - Latitude_from_txt < Valve:
                        if -Valve < Longtitude - Longtitude_from_txt < Valve:

                            # SQL更新操作
                            df.update_data(cur, 'Waypoints',
                                           {'Latitude': Latitude, 'Longtitude': Longtitude},
                                           {'Ident': ident, 'Latitude': Latitude, 'Longtitude': Longtitude})

                            # 标记为1
                            Ident_Flag = 1

                            # 如果发现 NavaidID 不为空
                            if NavaidID is not None:
                                df.update_data(cur, 'Navaids',
                                               {'Latitude': Latitude, 'Longtitude': Longtitude},
                                               {'Ident': ident, 'Latitude': Latitude, 'Longtitude': Longtitude})

                    # 发现不是同一点
                    else:
                        pass

            # 没有找到相同点
            if Ident_Flag == 0 or results is None:

                # 标记是否在两个csv文件中找到，如果都没找到，则标记为0,若找到至少一条记录，则标记为1
                flag_csv = 0

                # 初始化一些Navaids表格的数据
                NType = 0  # 确定Type，在VOR中找到为4,NDB中找到为5
                USAGE_TAG = ''  # 确定Usage,VOR中找到为B，NDB中找到为H
                Elevation = 0  # 确定Elevation，找到是对应值乘以3.28，没找到则为0
                SLV_TAG = 0  # 确定SlavedVar，在VOR中找到为B，NDB中找到为H
                MGV_TAG = 0  # 确定MagneticVariation是否存在，若在VOR中则为对应值，NDB中为空值
                RG_TAG = 0  # 确定Range，VOR中为130,NDB中为空
                FREQ_VAL = 0  # 确定Freq，需要进行运算，有默认值
                Name = ''  # 节点名称
                MagneticVariation = 'NULL'
                Range = 'NULL'

                csvPD = None

                if VOR_read['CODE_ID'].isin([ident]).any():
                    NType = 4
                    USAGE_TAG = 'B'
                    SLV_TAG = 0
                    MGV_TAG = 0
                    RG_TAG = 0
                    flag_csv = 1
                    csvPD = VOR_read

                elif NDB_read['CODE_ID'].isin([ident]).any():
                    NType = 5
                    USAGE_TAG = 'H'
                    SLV_TAG = -1
                    MGV_TAG = 1
                    RG_TAG = 1
                    flag_csv = 1
                    csvPD = NDB_read

                else:
                    pass
                # 如果在csv里找到了 则开始寻找数据
                if flag_csv == 1:

                    information = csvPD[csvPD['CODE_ID'] == data[0]]

                    # 分数据
                    TXT_NAME = information['TXT_NAME'].values[0]
                    FREQ_VAL = information['VAL_FREQ'].values[0]
                    ELEV_VAL = information['VAL_ELEV'].values[0]
                    Elevation = 0
                    MagneticVariation = 'NULL'
                    Range = 'NULL'

                    # 按照上述进行属性赋值
                    if pd.isna(ELEV_VAL):
                        Elevation = 0
                    else:
                        Elevation = ELEV_VAL * 3.28
                    if NType == 4:
                        FREQ_VAL *= 100
                    elif NType == 5:
                        FREQ_VAL *= 1
                    FREQ_VAL = hd.get_freq(dat_path, FREQ_VAL, cur)
                    if FREQ_VAL is None:
                        if NType == 4:
                            FREQ_VAL = 18046976
                        elif NType == 5:
                            FREQ_VAL = 37814272
                    Name = pinyin.get(TXT_NAME, format='strip', delimiter='').upper()
                    if MGV_TAG == 0:
                        MGV_VAL = information['VAL_MAG_VAR'].values[0]
                        MagneticVariation = MGV_VAL
                    else:
                        MagneticVariation = 'NULL'
                    if RG_TAG == 0:
                        Range = '130'
                    else:
                        Range = 'NULL'
                    flag_csv = 1  # 已找到csv数据

                    # SQL操作

                    # 获取两个表格的ID
                    Navaid = df.get_id(cur, 'Navaids') + 1

                    WayPointID = df.get_id(cur, 'Waypoints') + 1

                    # 往Navaids表格插入
                    data_list_1 = [Navaid, ident, NType, Name, FREQ_VAL, '',
                                   USAGE_TAG, Latitude_from_txt, Longtitude_from_txt,
                                   Elevation, SLV_TAG, MagneticVariation, Range]

                    df.insert_into(cur, 'Navaids', data_list_1)

                    # 往Navaid_Lookup表格插入

                    data_list_2 = [ident, NType, Country_Chars, 1, Navaid]

                    df.insert_into(cur, 'NavaidLookup', data_list_2)

                    # 往waypoints表格插入

                    data_list_3 = [WayPointID, ident, 1, Name, Latitude_from_txt, Longtitude_from_txt, Navaid]

                    df.insert_into(cur, 'Waypoints', data_list_3)

                    # 往waypoint_Lookup表格插入

                    data_list_4 = [ident, Country_Chars, WayPointID]

                    df.insert_into(cur, 'WaypointLookup', data_list_4)

                # 没有在WayPoint里找到，也没有在CSV里找到
                else:

                    with open(exception_log_path, 'a') as f1:
                        f1.write(f'{Data} not in csv\n')

                    WayPointID = df.get_id(cur, 'Waypoints') + 1

                    # 往waypoints表格插入

                    data_list_1 = [WayPointID, ident, 0, ident, Latitude_from_txt, Longtitude_from_txt, '']

                    df.insert_into(cur, 'Waypoints', data_list_1)

                    # 往waypoint_Lookup表格插入

                    data_list_2 = [ident, Country_Chars, WayPointID]

                    df.insert_into(cur, 'WaypointLookup', data_list_2)






cur.close()
con.commit()
con.close()

input("\n\tPress enter to cancel.")
