import math
from typing import Union
from 公共函数 import *
import pandas as pd
from colorama import Fore, init


def file_process(input_path: str, output_path: str, mode: str):
    def la_process(string: str) -> str:
        # N334736
        string = [string[1:3], string[3:5], string[5:7]]
        string = [int(i) for i in string]
        num = (string[0] / (60 ** 0)) + (string[1] / (60 ** 1)) + (string[2] / (60 ** 2))
        num = str(round(num, 8))
        return num

    def lon_process(string: str) -> str:
        # E1054319
        string = [string[1:4], string[4:6], string[6:8]]
        string = [int(i) for i in string]
        num = string[0] / (60 ** 0) + string[1] / (60 ** 1) + string[2] / (60 ** 2)
        num = str(round(num, 8))
        return num

    def fir_code(string: str) -> str:
        if "乌鲁木齐" in string:
            return "ZW"
        elif "兰州" in string:
            return "ZL"
        elif "北京" in string:
            return "ZB"
        elif "沈阳" in string:
            return "ZY"
        elif "武汉" in string:
            return "ZH"
        elif "上海" in string:
            return "ZS"
        elif "广州" in string:
            return "ZG"
        elif "三亚" in string:
            return "ZJ"
        elif "昆明" in string:
            return "ZU"
        elif "未知" in string:
            return "UN"
        else:
            printf("情报区{}不对啊".format(string), 1)

    df = pd.read_csv(input_path, encoding="gbk")
    output_file = open(output_path, mode, encoding="utf-8")
    save = ("VOR/DME", "NDB", "五字代码点", "P字点", "航路PBN点")
    df = df[df["CODE_TYPE"].isin(save)]
    fir = df["CODE_FIR"].tolist()
    name = df["CODE_ID"].tolist()
    latitude = df["GEO_LAT_ACCURACY"].tolist()
    longitude = df["GEO_LONG_ACCURACY"].tolist()
    if "DESIGNATED" in input_path:
        for eachWaypoint in [["广州", "AIWD5", "N213118", "E1133200"]]:
            fir.append(eachWaypoint[0])
            name.append(eachWaypoint[1])
            latitude.append(eachWaypoint[2])
            longitude.append(eachWaypoint[3])
    for i_fir in range(len(fir)):
        try:
            if '，' in fir[i_fir]:
                fir[i_fir] = fir[i_fir].split('，')[-1]
        except TypeError:
            pass
    print(len(fir), len(name), len(latitude), len(longitude))
    for ii in range(len(name)):
        if type(fir[ii]) == float:  # nan是float，不是numpy里面那个
            fir[ii] = "未知"
        output_file.write("{} {} {} {}\n". \
                          format(name[ii], la_process(latitude[ii]), lon_process(longitude[ii]), fir_code(fir[ii])))


# 提醒 备忘
# 1. 若FIR为空或者为NAN 忽略这个点
# 2. 若为多个FIR 取最后一个FIR
# 程序本质为提升航路点精度
init(autoreset=True)
design = r"D:\naip\input\DESIGNATED_POINT.csv"
vor = r"D:\naip\input\VOR.csv"
ndb = r"D:\naip\input\NDB.csv"
output = r"F:\PDF初提取\lunatic.txt"
file_process(design, output, 'w')
file_process(vor, output, "a+")
file_process(ndb, output, "a+")
