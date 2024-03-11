import os.path
from geopy.distance import distance
from geopy.point import Point
from 公共函数 import *


class Procedure:
    def __init__(self, ptype: int):
        self.length = None
        self.airport = None
        self.area = None
        self.runway = None
        self.name = None
        self.legs = []
        self.encode_legs = []
        self.number = []
        if ptype == 1:  # 1离场 2进场 3进近
            self.ptype = "SID"
        elif ptype == 2:
            self.ptype = "STAR"
        elif ptype == 3:
            self.ptype = "APPCH"
        else:
            printf("程序类型错误", 1)

    def add_info(self, info: str):
        self.name = info.split(',')[1]
        self.airport = info.split(',')[2]
        self.area = info.split(',')[2][:2]
        self.runway = info.split(',')[3]

    def add_leg(self, leg: str):
        self.legs.append(leg)

    def create_number(self):
        if (self.ptype == "SID") or (self.ptype == "STAR"):
            self.number = list(range(1, len(self.legs) + 1))
        else:
            codes = [i.split(',')[3] for i in self.legs]
            if_location = []
            for iCodeLoc in range(len(codes)):
                if codes[iCodeLoc] == "IF":
                    if_location.append(iCodeLoc)
            number_list = []
            # 进近过渡
            now = 1
            for iLoc in range(len(codes)):
                if iLoc in if_location:
                    now = 1
                number_list.append(now)
                now += 1
            # 主进近
            for iLegLoc in range(len(self.legs)):
                if self.legs[iLegLoc].split(',')[8] == "MAP":
                    mapt = iLegLoc
                    break
            else:
                mapt = -1
            if mapt != -1:  # 下滑道处于可用状态
                start = if_location[-1]
                end = len(codes)
                seps = int(10 / (mapt - start)) * 0.1
                for iLoc in range(start, mapt):
                    number_list[iLoc] = 2 + (iLoc - start) * seps
                for iLoc in range(mapt, end):
                    number_list[iLoc] = 3 + iLoc - mapt
            self.number = number_list.copy()

    def encode(self):
        """由db转换为CIFP"""

        def waypoint_info(ident: str) -> List[str]:
            if empty(ident, 4):
                return [' ', ' ', ' ']
            else:
                default = [self.area, 'P', 'C']
                result = airportPoints.query(ident)
                if result != -1:
                    result = waypoints.query(result)
                if result != -1:
                    default[0] = result.area
                    if (result.ident == "RW" + self.runway) and (self.ptype == "APPCH"):
                        # 满足条件 1.RW+跑道 3.该航点处于进近程序中
                        default[2] = 'G'
                    if result.cat == 3:
                        default[1] = 'D'
                        default[2] = 'B'
                    elif result.cat == 2:
                        default[1] = 'D'
                        default[2] = ' '
                    elif result.airport == "ENRT":
                        default[1] = 'E'
                        default[2] = 'A'
                return default

        def alt_process(alt: str) -> List[str]:
            if empty(alt, 4):
                return [' ', "     ", "     "]
            elif "MAP" in alt:
                alt = 0
                if airportNow in altitudeDict:
                    alt = altitudeDict[airportNow]
                if "{}_{}".format(airportNow, self.runway) in altitudeDict:
                    alt = altitudeDict["{}_{}".format(airportNow, self.runway)]
                return [' ', digit_process(str(alt + 50), 5, 0), "     "]  # TCH统一50
            elif ('B' in alt) and ('A' in alt):
                alt = alt.replace('A', '')
                alt = alt.split('B')
                return ['B', alt[0], alt[1]]
            elif 'B' in alt:
                alt = alt.split('B')
                return ['-', alt[0], "     "]
            elif 'A' in alt:
                alt = alt.split('A')
                return ['+', alt[0], "     "]
            else:
                return [' ', alt, "     "]

        global transHeight, airportNow, altitudeDict
        self.create_number()
        self.length = len(self.legs)
        final_app = False
        already_encode = False
        for iLegLoc in range(len(self.legs)):
            i_leg = self.legs[iLegLoc].split(',')
            text = list()
            # 程序类型和编号 0
            text.append(self.ptype + ':' + digit_process(str(self.number[iLegLoc]), 2, 1))
            # 程序类型
            text.append(i_leg[1])
            if i_leg[1] == 'R':
                final_app = True
            # 程序名 2
            text.append(self.name)
            # 过渡
            text.append(i_leg[2])
            # 航路点 4
            if (i_leg[8] == "MAP") and empty(i_leg[4], 4):
                i_leg[4] = "RW" + self.runway
            text.append(i_leg[4])
            point_info = waypoint_info(i_leg[4])
            text += point_info
            # 描述 8
            if point_info[1:] == ['D', ' ']:  # VHF作为航点
                i_leg[11] = 'V' + i_leg[11][1:]
            elif point_info[1:] == ['D', 'B']:  # NDB作为航点
                i_leg[11] = 'N' + i_leg[11][1:]
            text.append(i_leg[11])
            # 转向
            text.append(i_leg[5])
            # RNP值 10 不想改前面的代码了 默认0.3
            if (self.ptype == "APPCH") and (i_leg[3] == "IF"):
                text.append("   ")
            else:
                text.append("302")
            # 航段类型
            text.append(i_leg[3])
            # 一坨没用的 12
            text += [' ', ' ', ' ', ' ', ' ']
            # RF半径 17 还是算一算好 不然会吞点
            if text[11] != "RF":
                text.append(digit_process('-', 3, 3))
            else:
                side_point = airportPoints.query(i_leg[4])
                center_point = airportPoints.query(i_leg[10])
                if (side_point != -1) and (center_point != -1):
                    dist = get_distance(side_point, center_point)
                    text.append(digit_process(str(dist), 3, 3))
                else:
                    text.append(digit_process('-', 3, 3))
            # 两个没用的
            text += ["    ", "    "]
            # 航向 20
            if empty(i_leg[6], 4):
                text.append("    ")
            else:
                text.append(digit_process(i_leg[6], 3, 1))
            # 距离
            if text[11] in ("HF", "HM"):
                text.append("T010")  # 虽然也有1.5分钟的 但不想动了
            else:
                text.append("    ")
            # 高度 22
            text += alt_process(i_leg[8])
            # TA 25
            if (iLegLoc == 0) and ((self.ptype == "STAR") or (self.ptype == "APPCH")):
                text.append(digit_process(str(transHeight[self.airport][1]), 5, 0))
            else:
                text.append("     ")
            # 速度
            if empty(i_leg[13], 4):
                text += [' ', "   "]
            else:
                text += ['-', i_leg[13]]
            # 下滑道
            if empty(i_leg[9], 4):
                text += ["    ", "   "]
            else:
                text += ['-' + str(int(float(i_leg[9]) * 100)), "   "]
            # 中心点 30
            use_airport = False
            if (iLegLoc == 0) and (self.ptype == "SID" or self.ptype == "STAR"):
                use_airport = True
            if final_app and (not already_encode):
                use_airport = True
                already_encode = True
            if use_airport:
                text += [airportNow, airportNow[:2], 'P', 'A']
            else:
                text.append(i_leg[10])
                text += waypoint_info(i_leg[10])
            # 杂
            text.append(' ')
            if self.ptype == "APPCH":
                text += ['B', 'P', "S;"]
            else:
                text += [' ', ' ', " ;"]
            self.encode_legs.append(','.join(text))

    def output(self) -> str:
        return '\n'.join(self.encode_legs)

    def __del__(self):
        self.legs.clear()


def change_code(encode: str, loc: int, char: str, replace: bool = True) -> str:
    """
    修改字符串对应位置上的字符
    :param encode: 字符串
    :param loc: 位置
    :param char: 字符
    :param replace: 假如原有位置不为空的话, 是否替换
    :return: 修改后的字符串
    """
    encode = list(encode)
    if replace:
        encode[loc] = char
    return ''.join(encode)


def read_procedures(file_text: List[str]) -> List[Procedure]:
    """
    提取txt文件中的程序
    :param file_text: 文件readlines后
    :return: 程序列表
    """
    file_text = [i for i in file_text if (not empty(i, 4)) and ("---" not in i)]
    file_text = [empty(i, 2) for i in file_text]
    procs = []
    start_mark = False
    for iLine in file_text:
        # 程序第一行
        if iLine.startswith("Departure"):
            procs.append(Procedure(1))
            start_mark = True
        elif iLine.startswith("Arrival"):
            procs.append(Procedure(2))
            start_mark = True
        elif iLine.startswith("Approach"):
            procs.append(Procedure(3))
            start_mark = True
        else:
            # 程序第二行
            if start_mark:
                procs[-1].add_info(iLine)
                start_mark = False
            else:
                procs[-1].add_leg(iLine)
    return procs


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
            i_point = Waypoint(float(i_point[0]), float(i_point[1]), i_point[2], 1, i_point[3], i_point[4])
            waypoints.add_point(i_point)
    with open(os.path.join(folder, "earth_nav.dat"), 'r', encoding="utf-8") as f:
        f = f.readlines()
        f = f[3:-1]
        for iLine in f:
            i_point = iLine.split()
            if "NDB" in i_point[11]:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 3, i_point[8], i_point[9])
            else:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[7], 2, i_point[8], i_point[9])
            waypoints.add_point(i_point)


def read_terminal_points(db_path: str):
    """
    建立单机场航点文件 外加lunatic
    :param db_path: db文件的路径
    """
    global airportPoints, waypoints, inputPath
    with open(db_path[:-7] + "_waypoint.txt", 'r', encoding="utf-8") as f:
        f = f.readlines()
        f = [i for i in f if not empty(i, 4)]
        for iLine in f:
            i_point = iLine.split()
            i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[0], -1)
            result = waypoints.query(i_point)
            if result != -1:
                airportPoints.add_point(result)
    with open(os.path.join(inputPath, "lunatic.txt"), 'r', encoding="utf-8") as f:  # 感觉不是很有必要
        f = f.readlines()
        f = [i for i in f if not empty(i, 4)]
        for iLine in f:
            i_point = iLine.split()
            i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[0], -1)
            result = waypoints.query(i_point)
            if result != -1:
                airportPoints.add_point(result)


def get_distance(first: Waypoint, second: Waypoint) -> float:
    """
    计算两个点之间的距离
    :param first: 第一个点
    :param second: 第二个点
    :return: 距离
    """
    first = Point(first.latitude, first.longitude)
    second = Point(second.latitude, second.longitude)
    dist = distance(first, second).nautical
    dist = int(dist * 1000) + 2  # xplane最高支持三位小数
    return dist * 0.001


def digit_process(x: str, front: int, back: int, fla: bool = False) -> str:
    """
    返回对应字符串
    :param x: 字符串形式的数字
    :param front: 整数部分位数
    :param back: 小数部分位数
    :param fla: 以纯数字形式返回带FL的高度
    :return: 字符串
    """
    if x == "-" or x == "-1":
        return " " * (front + back)
    if "FL" in x:  # 高度限制可以用高度层
        if fla:
            return digit_process(str(int(x[2:]) * 100), 3, 0)
        return "FL" + digit_process(x[2:], 3, 0)
    x = str(float(x))
    for o in range(front - len(x[:x.index('.')])):
        x = '0' + x
    for o in range(back - len(x[x.index('.') + 1:])):
        x += '0'
    x = x[:x.index('.')] + x[x.index('.') + 1:]
    if len(x) > (front + back):
        x = x[:-(len(x) - (front + back))]
    return x


def read_csv_trans(csv_path: str) -> dict:
    """读取Trans Level"""

    def alt_change(alt: str) -> int:
        alt = str(int(int(alt) * 3.28))
        tail = int(alt[-2:])
        alt = alt[:-2] + "00"
        if tail <= 49:
            return int(alt) + 0
        else:
            return int(alt) + 100

    table = dict()
    df = pd.read_csv(csv_path, encoding="gbk")
    df.fillna('0', inplace=True)
    for iLoc in range(df.shape[0]):
        table[df.iloc[iLoc, 4]] = (alt_change(df.iloc[iLoc, 15]), alt_change(df.iloc[iLoc, 17]))
    return table


def procedure_mix(airport_name: str, cifp_path: str):
    global procedures
    raw_path = os.path.join(cifp_path, airport_name + ".dat")
    raw_file = open(raw_path, 'r', encoding="utf-8")
    raw_text = raw_file.readlines()
    raw_file.close()
    raw_text = [i for i in raw_text if not empty(i, 4)]
    raw_text = [empty(i, 2) for i in raw_text]
    procs_name = set([i.split(',')[2] for i in raw_text if not i.startswith("RWY")])
    sid_loc = star_loc = app_loc = -1
    for iLineLoc in range(len(raw_text)):
        if raw_text[iLineLoc].startswith("SID"):
            sid_loc = iLineLoc
        elif raw_text[iLineLoc].startswith("STAR"):
            star_loc = iLineLoc
        elif raw_text[iLineLoc].startswith("APPCH"):
            app_loc = iLineLoc
        else:
            continue
    sid_loc += 1
    star_loc += 1
    app_loc += 1
    if sid_loc * star_loc * app_loc == 0:
        printf("程序类型未找齐", 1)
    for iProce in procedures:
        if iProce.name in procs_name:
            continue
        if iProce.ptype == "SID":
            raw_text = raw_text[:sid_loc] + iProce.encode_legs + raw_text[sid_loc:]
            sid_loc += iProce.length
            star_loc += iProce.length
            app_loc += iProce.length
        elif iProce.ptype == "STAR":
            raw_text = raw_text[:star_loc] + iProce.encode_legs + raw_text[star_loc:]
            star_loc += iProce.length
            app_loc += iProce.length
        else:
            raw_text = raw_text[:app_loc] + iProce.encode_legs + raw_text[app_loc:]
            app_loc += iProce.length
    raw_text = [i + '\n' for i in raw_text]
    edit_file = open(r".\output\{}.dat".format(airport_name), 'w', encoding="utf-8")
    edit_file.writelines(raw_text)
    edit_file.close()


def altitude_database(csv_folder: str) -> dict:
    """返回一个包含机场和跑道高度的字典"""
    database = dict()

    port_df = pd.read_csv(os.path.join(csv_folder, "AD_HP.csv"), encoding="gbk")
    port_df.fillna('0', inplace=True)
    for iLoc in range(port_df.shape[0]):
        database[port_df.iloc[iLoc, 4]] = float(port_df.iloc[iLoc, 10]) * 3.28

    rwy_df = pd.read_csv(os.path.join(csv_folder, "RWY.csv"), encoding="gbk")
    rwy_df.fillna('0', inplace=True)
    rwy_dir_df = pd.read_csv(os.path.join(csv_folder, "RWY_DIRECTION.csv"), encoding="gbk")
    rwy_dir_df.fillna('0', inplace=True)
    for iLoc in range(port_df.shape[0]):
        icao = rwy_df.iloc[iLoc, 2]
        rwy_id = rwy_df.iloc[iLoc, 0]
        results = rwy_dir_df[rwy_dir_df["RWY_ID"] == rwy_id]
        for jLoc in range(results.shape[0]):
            rwy_ident = results.iloc[jLoc, 2]
            if len(rwy_ident) == 1:
                rwy_ident = '0' + rwy_ident
            database["{}_{}".format(icao, rwy_ident)] = float(results.iloc[jLoc, 4]) * 3.28
    return database


def runway_info(proces: List[str], alt_info: dict) -> str:
    """
    返回跑道信息行
    :param proces: 进近程序
    :param alt_info: 高度信息
    :return: 处理好的跑道信息
    """
    global airportPoints, airportNow
    proces = [i.split(',')[2:9] for i in proces]
    der = dict()
    for iPoint in proces:
        describe = iPoint[6]
        # 确定点类型
        if describe == "GY M":
            check = 2
        elif describe == "EY M":
            check = 1
        else:
            continue
        # 小处理一下
        runway = iPoint[0][1:]
        for iElement in ('-', 'X', 'Y', 'Z'):
            runway = runway.replace(iElement, '')
        ident = iPoint[2]
        point = airportPoints.query(ident)
        if point == -1:
            continue
        if (check == 1) and (runway not in der):  # 跑道点优先级最高
            der[runway] = point
        elif check == 2:
            der[runway] = point
    # 编码
    runways = []
    for iDer in der.keys():
        point = der[iDer]
        # 头部
        runway = "RWY:RW"
        # 跑道
        runway += (iDer + (3 - len(iDer)) * ' ')
        # 跑道坡度 大地高程
        runway += ",     ,      ,"
        # 高度
        runway_alt = 0
        if airportNow in alt_info:
            runway_alt = alt_info[airportNow]
        if (airportNow + '_' + iDer) in alt_info:
            runway_alt = alt_info[airportNow + '_' + iDer]
        runway += digit_process(str(runway_alt), 5, 0)
        # TCH ILS
        runway += ", ,    , ,   ;"
        # 经纬度
        point = str(Point(point.latitude, point.longitude))
        for iElement in ('m', 's', ',', 'N', 'E'):
            point = point.replace(iElement, '')
        point = point.split()
        point = "N{}{}{},E{}{}{}".format(digit_process(point[0], 2, 0), digit_process(point[1], 2, 0),
                                         digit_process(point[2], 2, 2), digit_process(point[3], 3, 0),
                                         digit_process(point[4], 2, 0), digit_process(point[5], 2, 2))
        runway += point
        # 跑道内移
        runway += ",0000;"
        runways.append(runway)
    return "\n{}\n".format('\n'.join(runways))


inputPath = r"F:\PDF初提取"
xplanePath = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data"
csvFolder = r"F:\航图\中国民航国内航空资料汇编 NAIP 2312\DataFile"
inputFiles = []
walking(inputPath, inputFiles)
# 建立xp航点库
waypoints = WaypointSystem()
read_points(xplanePath)
# ta tl
transHeight = read_csv_trans(os.path.join(csvFolder, "AD_HP.csv"))
# 建立跑道高度
altitudeDict = altitude_database(csvFolder)
# 处理程序
xplanePath = os.path.join(xplanePath, "CIFP")
for iFilePath in inputFiles:
    if "_db" not in iFilePath:
        continue
    airportNow = extract_name(iFilePath)[:4]
    printf(airportNow, 3)
    # 建立单机场航点库
    airportPoints = WaypointSystem()
    read_terminal_points(iFilePath)
    # 判断是否是新机场
    existAirport = os.path.exists(os.path.join(xplanePath, airportNow + ".dat"))
    # 处理程序
    with open(iFilePath, 'r', encoding="utf-8") as file:
        file = file.readlines()
        procedures = read_procedures(file)
        for iProc in procedures:
            iProc.encode()
    # 写入
    if not existAirport:  # 假如机场不存在程序
        procText = []
        for iProc in procedures:
            procText.append(iProc.output())
        cifpFile = open(r".\output\{}.dat".format(airportNow), 'w', encoding="utf-8")
        procText = '\n'.join(procText)
        cifpFile.write(procText)
        procText = procText.split('\n')
        cifpFile.write(runway_info([i for i in procText if i.startswith("APPCH")], altitudeDict))
        cifpFile.close()
    else:
        procedure_mix(airportNow, xplanePath)
