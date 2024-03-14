import pandas as pd
import pinyin
from 公共函数 import *


def location_process(location: str) -> float:
    first = location[1:3] if 'N' in location else location[1:4]
    second = location[3:5] if 'N' in location else location[4:6]
    third = location[5:] if 'N' in location else location[6:]
    return round(int(first) / 1 + int(second) / 60 + int(third) / 3600, 9)


def area(string: str) -> str:
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
    else:
        return "UN"


navPath = r"E:\steampower\steamapps\common\X-Plane 11\Custom Data\earth_nav.dat"
navFile = open(navPath, 'r', encoding="utf-8")
navText = navFile.readlines()
navFile.close()
navText = navText[3:-1]
navaids = [(lambda x: Waypoint(float(x.split()[1]), float(x.split()[2]), x.split()[7], -1,' '))(i) for i in navText]

vor = r"F:\航图\中国民航国内航空资料汇编 NAIP 2312\DataFile\VOR.csv"
vor = pd.read_csv(vor, encoding="gbk")
vor.fillna('0', inplace=True)
vorText = []
for iLoc in range(vor.shape[0]):
    station = Waypoint(location_process(vor.iloc[iLoc, 7]), location_process(vor.iloc[iLoc, 8]), vor.iloc[iLoc, 3],-1)
    isFind = False
    for iNav in navaids:
        if iNav.is_same(station):
            isFind = True
            break
    if isFind:
        continue

    stationText = "3 {} {} {} {} {} {} {} {} {} {} {} \n".format(station.latitude, station.longitude,
                                                                  int(int(vor.iloc[iLoc, 12]) * 3.28),
                                                                  int(float(vor.iloc[iLoc, 9]) * 100), 130,
                                                                  float(vor.iloc[iLoc, 11]), station.ident, "ENRT",
                                                                  area(vor.iloc[iLoc, 1]),
                                                                  pinyin.get(vor.iloc[iLoc, 5], format='strip',
                                                                             delimiter='').upper(), "VOR/DME")
    vorText.append(stationText)
    stationText = "12 {} {} {} {} {} {} {} {} {} {} {} \n".format(station.latitude, station.longitude,
                                                                   int(int(vor.iloc[iLoc, 12]) * 3.28),
                                                                   int(float(vor.iloc[iLoc, 9]) * 100), 130,
                                                                   0, station.ident, "ENRT", area(vor.iloc[iLoc, 1]),
                                                                   pinyin.get(vor.iloc[iLoc, 5], format='strip',
                                                                              delimiter='').upper(), "VOR/DME")
    vorText.append(stationText)

ndb = r"F:\航图\中国民航国内航空资料汇编 NAIP 2312\DataFile\NDB.csv"
ndb = pd.read_csv(ndb, encoding="gbk")
ndb.fillna('0', inplace=True)
ndbText = []
for iLoc in range(ndb.shape[0]):
    station = Waypoint(location_process(ndb.iloc[iLoc, 7]), location_process(ndb.iloc[iLoc, 8]), ndb.iloc[iLoc, 3],-1)
    isFind = False
    for iNav in navaids:
        if iNav.is_same(station):
            isFind = True
            break
    if isFind:
        continue

    stationText = "2 {} {} {} {} {} {} {} {} {} {} {} \n".format(station.latitude, station.longitude,
                                                                  int(int(ndb.iloc[iLoc, 12]) * 3.28),
                                                                  int(float(ndb.iloc[iLoc, 9]) * 1), 50,
                                                                  0.0, station.ident, "ENRT",
                                                                  area(ndb.iloc[iLoc, 1]),
                                                                  pinyin.get(ndb.iloc[iLoc, 5], format='strip',
                                                                             delimiter='').upper(), "NDB")
    ndbText.append(stationText)
navFile = open(navPath, 'r', encoding="utf-8")
navText = navFile.readlines()[:-1]
navFile.close()
navText += vorText
navText += ndbText
navText.append("99\n")
navFile = open(r".\output\nav.dat", 'w', encoding="utf-8")
navFile.writelines(navText)
navFile.close()
