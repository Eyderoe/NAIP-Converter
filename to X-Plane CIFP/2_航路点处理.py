from colorama import init

from 公共函数 import *


def read_xp_file(file_path: str, source: int, point_list: List[Waypoint]) -> List[str]:
    """
    读取xp原文件
    :param file_path: 文件路径
    :param source: 文件类型
    :param point_list: 航点列表
    :return: 表头内容
    """
    with open(file_path, 'r', encoding="utf-8") as f:
        header = f.readlines(2)
        f.readline()
        f = f.readlines()[:-1]
        for iLine in f:
            i_line = iLine.split()
            if source == 1:  # 航点
                la = float(i_line[0])
                long = float(i_line[1])
                ident = i_line[2]
                airport = i_line[3]
                area = i_line[4]
            else:  # 导航台
                la = float(i_line[1])
                long = float(i_line[2])
                ident = i_line[7]
                airport = i_line[8]
                area = i_line[9]
            point_list.append(Waypoint(la, long, ident, -1, airport, area))
    return header


def read_naip_file(file_path: str) -> List[Waypoint]:
    global iNaipFile
    points = []
    with open(file_path, 'r', encoding="utf-8") as naip_file:
        naip_file = naip_file.readlines()
        naip_file = [i for i in naip_file if not empty(i, 4)]
        for i_line in naip_file:
            i_line = i_line.split()
            la = float(i_line[1])
            long = float(i_line[2])
            ident = i_line[0]
            if "lunatic" in file_path:
                airport = "ENRT"
                area = i_line[3]
            else:
                airport = extract_name(iNaipFile)[:4]
                area = airport[:2]
            points.append(Waypoint(la, long, ident, -1, airport, area))
    return points


def waypoint_type(ident: str) -> int:
    """根据ARINC424 5.42和XPlane FIX1101初略计算"""
    coding = "W  "  # 默认RNAV航路点
    return ord(coding[0]) * (2 ** 0) + ord(coding[1]) * (2 ** 8)+ ord(coding[2]) * (2 ** 16)


# 突然想写cpp了 艹
init(autoreset=True)
forXp11 = True
naipPath = r"F:\PDF初提取"
earth_nav = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data\earth_nav.dat"
earth_fix = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data\earth_fix.dat"
terminal = []
navigation = []
naip = []

fix_head = read_xp_file(earth_fix, 1, terminal)
read_xp_file(earth_nav, 2, navigation)
terminalName = tuple(i.ident for i in terminal)
navigationName = tuple(i.ident for i in navigation)
naipName = dict()
printf("XP原文件读取完毕", 3)
naipFiles = []
walking(naipPath, naipFiles)
naipFiles = [i for i in naipFiles if ("_waypoint" in i) or ("lunatic" in i)]
naipFiles.sort()
for iNaipFile in naipFiles:
    printf(extract_name(iNaipFile), 3)
    naipWaypoints = read_naip_file(iNaipFile)
    for iNaipPoint in naipWaypoints:  # 对于每一个naip点
        isFind = False
        # 导航库
        if iNaipPoint.ident in navigationName:
            for iNavaidPoint in navigation:
                if iNavaidPoint.is_same(iNaipPoint, False):
                    isFind = True
                    break
            if isFind:
                continue
        # 终端库
        if iNaipPoint.ident in terminalName:
            for iTerminalPoint in terminal:
                if iTerminalPoint.is_same(iNaipPoint, False):
                    isFind = True
                    break
            if isFind:
                continue
        # NAIP库
        if iNaipPoint.ident in naipName:
            for iPassPoint in naip:
                if iPassPoint.is_same(iNaipPoint, True):
                    isFind = True
                    break
            if isFind:
                continue
        # 写入naip库
        naip.append(iNaipPoint)
        naipName[iNaipPoint.ident] = 0

with open(earth_fix, 'r') as file:
    file = file.readlines()[:-1]
if forXp11:
    file += [(lambda x: "{} {} {} {} {} {}\n".format(x.latitude, x.longitude, x.ident, x.airport, x.area,
                                                     waypoint_type(x.ident)))(i) for i in naip]
else:
    file += [(lambda x: "{} {} {} {} {} {} {}\n".format(x.latitude, x.longitude, x.ident, x.airport, x.area,
                                                        waypoint_type(x.ident), x.ident))(i) for i in naip]
file += ["99\n"]
with open(r".\output\fix.dat", 'w') as f:
    f.writelines(file)
