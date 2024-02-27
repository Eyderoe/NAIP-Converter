import os.path
import pandas as pd
from typing import Union
from 公共函数 import *


class WaypointSystem:
    def __init__(self):
        self.base = dict()

    def add_point(self, point: Waypoint):
        if point.ident not in self.base:
            self.base[point.ident] = [point]
        else:
            self.base[point.ident].append(point)

    def query(self, submit: Union[str, Waypoint]) -> Union[int, Waypoint]:
        """
        在数据库中查询一个航点
        :param submit: 识别符:str(主用于单机场) 航点类:Waypoint(主用于总数据库)
        :return: 未找到返回-1 找到返回航点
        """
        if type(submit) == str:
            if submit in self.base:
                return self.base[submit][0]
            else:
                return -1
        elif type(submit) == Waypoint:
            if submit.ident in self.base:
                for iPoint in self.base[submit.ident]:
                    if iPoint.is_same(submit):
                        return iPoint
                else:
                    return -1
            else:
                return -1
        else:
            printf("提交表单内容出错", 2)

    def __del__(self):
        self.base.clear()


def location_process(location: str) -> float:
    first = location[1:3] if 'N' in location else location[1:4]
    second = location[3:5] if 'N' in location else location[4:6]
    third = location[5:] if 'N' in location else location[6:]
    return round(int(first) / 1 + int(second) / 60 + int(third) / 3600, 9)


class Info:  # 一个航段的基础信息
    def __init__(self, information: List[str]):
        self.base = '*'.join(information[:4])  # 基础信息
        self.airway = information[4]  # 航路


class AirwaySystem:  # 一堆航路
    def __init__(self):
        self.base = dict()  # [from/to]:List[Info]

    def add_exist_record(self, record: str):
        """将xp数据库里面的东西写进去"""
        record = record.split()
        head = '*'.join(record[:6])
        if head not in self.base:
            self.base[head] = [Info(record[6:])]
        else:
            self.base[head].append(Info(record[6:]))

    def add_naip_record(self, point1: Waypoint, point2: Waypoint, ident: str):
        def in_database(head: str, awy: str) -> int:
            if head not in self.base:
                return 1  # 航段不存在
            else:
                for iInfo in self.base[head]:
                    if awy in iInfo.airway.split('-'):
                        return 2  # 航段存在 航线存在
                else:
                    return 3  # 航段存在 航线不存在

        from_point = "{}*{}*{}".format(point1.ident, point1.area, point1.cat)
        to_point = "{}*{}*{}".format(point2.ident, point2.area, point2.cat)
        forward = from_point + '*' + to_point
        backward = to_point + '*' + from_point
        # 存在
        forward_result = in_database(forward, ident)
        backward_result = in_database(backward, ident)
        if (forward_result == 2) or (backward_result == 2):
            return
        # 不存在 先这样写看能不能读 从这里往后可以重构 好的 重构次数：1
        empty_seg = True if forward_result + backward_result < 3 else False
        if forward_result == 3:
            master = forward
        elif backward_result == 3:
            master = backward
        else:
            master = forward

        if empty_seg:
            self.base[master] = [Info(['N', '1', '0', '0', ident])]
        else:
            for iInfoLoc in range(len(self.base[master])):  # 唉 python总是搞不懂这一坨
                if self.base[master][iInfoLoc].base.startswith('N'):  # 假如这是一个双向线段
                    self.base[master][iInfoLoc].airway += ("-{}".format(ident))
                    break
            else:  # 没有找到双向线段
                self.base[master].append(Info(['N', '1', '0', '0', ident]))

    def output(self) -> str:
        text = []
        keys = self.base.keys()
        for iKey in keys:
            for iInfo in self.base[iKey]:
                i_key = iKey
                i_key += ('*' + iInfo.base)
                i_key += ('*' + iInfo.airway)
                text.append(i_key.replace('*', ' '))
        return '\n'.join(text)


def read_points(folder: str):
    """
    读取xp原始航点数据
    :param folder: xp数据文件夹路径
    """
    global waypoints
    with open(os.path.join(folder, "earth_fix.dat"), 'r', encoding="utf-8") as f:
        f = f.readlines()
        f = f[3:-1]
        for iLine in f:
            i_point = iLine.split()
            i_point = Waypoint(float(i_point[0]), float(i_point[1]), i_point[2], 11, i_point[3], i_point[4])
            waypoints.add_point(i_point)
    with open(os.path.join(folder, "earth_nav.dat"), 'r', encoding="utf-8") as f:
        f = f.readlines()
        f = f[3:-1]
        for iLine in f:
            i_point = iLine.split()
            if "NDB" in i_point[11]:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 2, i_point[8], i_point[9])
            else:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 3, i_point[8], i_point[9])
            waypoints.add_point(i_point)


xplanePath = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data"
csvPath = r"F:\航图\中国民航国内航空资料汇编 NAIP 2312\DataFile\RTE_SEG.csv"
# 建立xp航点库
waypoints = WaypointSystem()
read_points(xplanePath)
# xp原始航路
airwayFile = open(os.path.join(xplanePath, "earth_awy.dat"), 'r', encoding="utf-8")
airwayText = airwayFile.readlines()
airwayFile.close()
airwayText = airwayText[3:-1]
airways = AirwaySystem()
for iLine in airwayText:
    airways.add_exist_record(iLine)
# naip航路
df = pd.read_csv(csvPath, encoding="gbk", dtype=str)
for iLoc in range(df.shape[0]):
    fromPoint = Waypoint(location_process(df.iloc[iLoc, 9]), location_process(df.iloc[iLoc, 8]), df.iloc[iLoc, 5], -1)
    toPoint = Waypoint(location_process(df.iloc[iLoc, 18]), location_process(df.iloc[iLoc, 17]), df.iloc[iLoc, 14], -1)
    airwayIdent = df.iloc[iLoc, 36]
    # 跳过情况
    if airwayIdent.startswith("XX"):  # 好像是直升机目视航向
        continue
    if ('*' in fromPoint.ident) or ('*' in toPoint.ident):  # M771 ****
        continue
    # 修正情况
    airwayIdent = airwayIdent.replace('-', '')  # FANS-1
    if len(fromPoint.ident) > 5:  # AIWD50/CH
        fromPoint.ident = fromPoint.ident[:5]
    if len(toPoint.ident) > 5:
        toPoint.ident = toPoint.ident[:5]
    # 写入数据库
    fromPoint = waypoints.query(fromPoint)
    toPoint = waypoints.query(toPoint)
    if (fromPoint == -1) or (toPoint == -1):
        printf("未知点出现在{}行".format(iLoc), 2)
    airways.add_naip_record(fromPoint, toPoint, airwayIdent)
# 写入文件
addon = airways.output()
airwayFile = open(os.path.join(xplanePath, "earth_awy.dat"), 'r', encoding="utf-8")
airwayText = airwayFile.readlines()
airwayFile.close()
airwayText = airwayText[:3]
airwayText += addon
airwayText.append("\n99\n")
airwayFile = open(r".\output\awy.dat", 'w', encoding="utf-8")
airwayFile.writelines(airwayText)
airwayFile.close()
