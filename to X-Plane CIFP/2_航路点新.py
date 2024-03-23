import os.path
from colorama import init
from 公共函数 import *


def read_raw_points(database: WaypointSystem, path: str):
    earth_fix = os.path.join(path, "earth_fix.dat")
    earth_fix = open(earth_fix, 'r', encoding="utf-8")
    fixes = earth_fix.readlines()[3:-1]
    earth_fix.close()
    for iFix in fixes:
        i_fix = iFix.split()
        i_fix = Waypoint(float(i_fix[0]), float(i_fix[1]), i_fix[2], -1)
        database.add_point(i_fix)

    earth_nav = os.path.join(path, "earth_nav.dat")
    earth_nav = open(earth_nav, 'r', encoding="utf-8")
    navaids = earth_nav.readlines()[3:-1]
    earth_nav.close()
    for iNav in navaids:
        i_nav = iNav.split()
        i_nav = Waypoint(float(i_nav[1]), float(i_nav[2]), i_nav[7], -1)
        database.add_point(i_nav)


def read_naip_points(db_raw: WaypointSystem, db_new: WaypointSystem, path: str):
    files = []
    walking(path, files)
    files = [i for i in files if ("waypoint" in i) or ("lunatic" in i)]
    for iFile in files:
        name = extract_name(iFile)
        printf(name, 3)
        file = open(iFile, 'r', encoding="utf-8")
        lines = file.readlines()
        file.close()
        lines = [i for i in lines if not empty(i, 4)]
        for iLine in lines:
            i_point = iLine.split()
            if "lunatic" in name:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[0], -1, "ENRT", i_point[3])
            else:
                i_point = Waypoint(float(i_point[1]), float(i_point[2]), i_point[0], -1, name[:4], name[:2])
            # 在xp原本的数据库里面查找
            result = db_raw.query(i_point)
            if result != -1:
                continue
            # 在naip数据库里面查找
            result = db_new.query(i_point, True)
            if result == -1:
                db_new.add_point(i_point)


def output_points(version: bool, out_path: str, xp_path, database: WaypointSystem):
    def waypoint_type() -> int:
        """根据ARINC424 5.42和XPlane FIX1101计算。技术储备 无意"""
        coding = "W  "  # 默认RNAV航路点
        return ord(coding[0]) * (2 ** 0) + ord(coding[1]) * (2 ** 8) + ord(coding[2]) * (2 ** 16)

    idents = database.base.keys()
    texts = []
    for iIdent in idents:
        for iPoint in database.base[iIdent]:
            if version:
                text = "{} {} {} {} {} {}\n".format(iPoint.latitude, iPoint.longitude, iPoint.ident, iPoint.airport,
                                                    iPoint.area, waypoint_type())
            else:
                text = "{} {} {} {} {} {} {}\n".format(iPoint.latitude, iPoint.longitude, iPoint.ident, iPoint.airport,
                                                       iPoint.area, waypoint_type(), iPoint.ident)
            texts.append(text)
    with open(os.path.join(xp_path,"earth_fix.dat"), 'r', encoding="utf-8") as f:
        f = f.readlines()[:-1]
    with open(out_path, 'w', encoding="utf-8") as fo:
        fo.writelines(f)
        fo.writelines(texts)
        fo.write("99\n")


init(autoreset=True)
naipPath = r"F:\PDF初提取"
xplanePath = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data"
outputPath = r".\output\fix.dat"
init(autoreset=True)
forXp11 = True if "X-Plane 11" in xplanePath else False
rawWaypoints = WaypointSystem()
naipWaypoints = WaypointSystem()
read_raw_points(rawWaypoints, xplanePath)
read_naip_points(rawWaypoints, naipWaypoints, naipPath)
output_points(forXp11, outputPath, xplanePath, naipWaypoints)
