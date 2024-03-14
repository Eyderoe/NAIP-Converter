from typing import Set, Tuple, Dict

from colorama import init
import pandas as pd
from 公共函数 import *


class Segment:
    def __init__(self, from_point: List[str], to_point: List[str], info: List[str]):
        self.from_point = from_point  # From
        self.to_point = to_point  # To
        self.dir = info[0]  # 方向限制
        self.alt = info[1]  # 高低空
        self.limit = (info[2], info[3])  # 航路最低最高高度
        self.names = info[4].split('-')  # 参与航路

    def get_ident(self) -> str:
        """返回航段标识"""
        return "{}*{}".format('*'.join(self.from_point), '*'.join(self.to_point))

    def get_point_ident(self) -> Tuple[str, str]:
        """返回始终航点名称"""
        return self.from_point[0], self.to_point[0]

    def output(self) -> str:
        info = self.from_point + self.to_point + [self.dir, self.alt, self.limit[0], self.limit[1],
                                                  '-'.join(self.names)]
        return ' '.join(info)


class Airways:
    def __init__(self):
        self.base: List[Segment] = []
        self.index: Dict[str, List[int]] = dict()  # 根据from to索引
        self.name_index: Dict[str, List[int]] = dict()  # 根据航路名称索引

    def output(self) -> List[str]:
        all_seg = []
        for iSeg in self.base:
            if len(iSeg.names) > 0:
                all_seg.append(iSeg.output())
        return all_seg

    def add_segment(self, seg: Segment):
        """
        添加一个航段至系统
        :param seg: 航段
        :param ignore: 是否直接添加
        """
        ident = seg.get_ident()
        if ident in self.index:
            self.index[ident].append(len(self.base))
        else:
            self.index[ident] = [len(self.base)]
        for iName in seg.names:
            if iName in self.name_index:
                self.name_index[iName].append(len(self.base))
            else:
                self.name_index[iName] = [len(self.base)]
        self.base.append(seg)

    def try_add_seg(self, point1: Waypoint, point2: Waypoint, awy_name: str):
        """添加两个点进去"""
        ident = [point1.ident, point1.area, str(point1.cat), point2.ident, point2.area, str(point2.cat)]
        forward = '*'.join(ident[:3] + ident[3:])
        backward = '*'.join(ident[3:] + ident[:3])
        # 前向通路有 就写前向
        if forward in self.index:
            for jLoc in self.index[forward]:
                if self.base[jLoc].dir == 'N':
                    self.base[jLoc].names.append(awy_name)
                    return
        # 反馈回路有 就写反馈
        if backward in self.index:
            for jLoc in self.index[backward]:
                if self.base[jLoc].dir == 'N':
                    self.base[jLoc].names.append(awy_name)
                    return
        # 都没有 就按前向写
        self.add_segment(Segment(forward.split('*')[:3], forward.split('*')[3:], ['N', '1', '0', '0', awy_name]))

    def del_segment(self, name: str, point_set: Set[str]):
        """
        删除包含在point_set中且航路名为name的航段
        :param name: 航路名
        :param point_set: 航点集合
        """
        # 对于单一航路 判断航点名称应该就行了 删除不删除本体 不然索引就要重写
        if name not in self.name_index:
            return
        else:
            for iLoc in self.name_index[name]:
                from_point, to_point = self.base[iLoc].get_point_ident()
                if (from_point in point_set) and (to_point in point_set):
                    self.base[iLoc].names.remove(name)


def read_points(folder: str):
    """
    读取xp原始航点数据
    :param folder: xp数据文件夹路径
    """
    global waypoints
    # earth_awy中 11航点 2无向信标 3甚高频
    with open(os.path.join(folder, "earth_fix.dat"), 'r', encoding="utf-8") as f:  # 添加航点
        f = f.readlines()
        f = f[3:-1]
        for iLine in f:
            i_point = iLine.split()
            i_point = Waypoint(float(i_point[0]), float(i_point[1]), i_point[2], 11, i_point[3], i_point[4])
            waypoints.add_point(i_point)
    with open(os.path.join(folder, "earth_nav.dat"), 'r', encoding="utf-8") as f:  # 添加导航台
        f = f.readlines()
        f = f[3:-1]
        for iLine in f:
            i_point = iLine.split()
            if i_point[0] == '2':  # NDB台
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 2, i_point[8], i_point[9])
            elif (i_point[0] == '3') or (i_point[0] == "13"):  # VHF台
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 3, i_point[8], i_point[9])
            else:
                continue
            waypoints.add_point(i_point)


def spawn_points(loc: int, table: pd.DataFrame) -> Tuple[Waypoint, Waypoint]:
    """生成from和to两点"""

    def location_process(location: str) -> float:
        """计算经纬度"""
        first = location[1:3] if 'N' in location else location[1:4]
        second = location[3:5] if 'N' in location else location[4:6]
        third = location[5:] if 'N' in location else location[6:]
        return round(int(first) / 1 + int(second) / 60 + int(third) / 3600, 9)

    from_ident = table.iloc[loc, 5]
    if len(from_ident) > 5:
        from_ident = from_ident[:5]
    from_la = table.iloc[loc, 9]
    from_long = table.iloc[loc, 8]
    from_point = Waypoint(location_process(from_la), location_process(from_long), from_ident, -1)
    to_ident = table.iloc[loc, 14]
    if len(to_ident) > 5:
        to_ident = to_ident[:5]
    to_la = table.iloc[loc, 18]
    to_long = table.iloc[loc, 17]
    to_point = Waypoint(location_process(to_la), location_process(to_long), to_ident, -1)
    return from_point, to_point


counter = 0
init(autoreset=True)
xplanePath = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data"
csvPath = r"F:\航图\中国民航国内航空资料汇编 NAIP 2312\DataFile\RTE_SEG.csv"
# 建立航点库
waypoints = WaypointSystem()
read_points(xplanePath)
printf("航点库建立完毕", 3)
# 添加已有航段
airway = Airways()
with open(os.path.join(xplanePath, "earth_awy.dat"), 'r', encoding="utf-8") as f:
    f = f.readlines()
    f = f[3:-1]
    for iLine in f:
        iLine = iLine.split()
        iSegment = Segment(iLine[0:3], iLine[3:6], iLine[6:])
        airway.add_segment(iSegment)
printf("已有航段添加完毕", 3)
# 删除国区航路 丢失所有信息 悲
naip = pd.read_csv(csvPath, encoding="gbk")
airwayNames = set(naip["TXT_DESIG"].tolist())
for iWayName in airwayNames:
    result = naip[naip["TXT_DESIG"] == iWayName]
    points = set(result["CODE_POINT_START"].tolist() + result["CODE_POINT_END"].tolist())
    airway.del_segment(iWayName, points)
printf("线段删除完毕", 3)
# 重新添加进去
for iWayName in airwayNames:
    result = naip[naip["TXT_DESIG"] == iWayName]
    if iWayName.startswith("XX"):
        continue
    if '-' in iWayName:
        iWayName = iWayName.replace('-', '')
    for iLoc in range(result.shape[0]):
        fromPoint, toPoint = spawn_points(iLoc, result)
        fromPoint = waypoints.query(fromPoint)
        toPoint = waypoints.query(toPoint)
        if (fromPoint == -1) or (toPoint == -1):
            printf("出现未知点 {}".format(iWayName), 2)
            continue
        airway.try_add_seg(fromPoint, toPoint, iWayName)
printf("线段添加完毕", 3)
# 导出
with open(r"E:\steampower\steamapps\common\X-Plane 11\Custom Data\earth_awy.dat", 'r', encoding="utf-8") as f:
    f = f.readlines()
    f = f[:3]
segments = airway.output()
segments = [i + '\n' for i in segments]
with open(r".\output\awy.dat", 'w', encoding="utf-8") as file:
    file.writelines(f)
    file.writelines(segments)
    file.write("99\n")
