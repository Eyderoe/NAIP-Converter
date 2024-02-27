import os

from colorama import init

from 公共函数 import *


class Procedure:
    def __init__(self, head: str):
        self.head = head
        if extract_name(iFile)[:4] in ("ZUAL", "ZUDR"):
            self.ident = head.split()[-1]
        else:  # ZLGL
            if '(' in head:
                left = head.index('(')
                right = head.index(')')
            else:
                left = 1
                right = 3
            self.ident = head[left + 1:right]
        self.legs = []

    def add_leg(self, leg: str):
        self.legs.append(leg.split(',')[1])

    def is_meet(self) -> bool:
        if not self.head.startswith("HE,01"):
            return True

        if extract_name(iFile)[:4] in ("ZUAL", "ZUDR"):
            if self.legs[0] in self.head:
                return True
            else:
                print(self.head, self.legs, self.ident)
                return False
        else:  # ZLGL
            if '(' in self.head:
                print(self.head, self.legs, self.ident)
                return False
            else:
                return True


init(autoreset=True)
inputFolder = r"F:\PDF初提取"
files = []
walking(inputFolder, files)
for iFile in files:
    if "encode" not in iFile:
        continue
    if extract_name(iFile)[:4] not in ("ZUAL", "ZUDR", "ZLGL"):
        continue
    printf("读取文件: {}".format(extract_name(iFile)[:4]), 3)
    fileText = open(iFile, 'r', encoding="utf-8")
    fileText = fileText.readlines()
    procedures = []
    for iLine in fileText:  # 只对进近过渡处理 这样就行了
        if iLine.startswith("HE"):
            procedures.append(Procedure(iLine))
        else:
            procedures[-1].add_leg(iLine)
    procedures = [i for i in procedures if not i.is_meet()]

    dbRaw = open(os.path.join(inputFolder, extract_name(iFile)[:4] + "_db.txt"), 'r', encoding="utf-8")
    dbRaw = dbRaw.readlines()
    for iProc in procedures:
        ident = iProc.ident
        waypoints = iProc.legs
        for iLineLoc in range(len(dbRaw)):
            isMatch = True
            for iWaypointLoc in range(len(waypoints)):
                if waypoints[iWaypointLoc] in dbRaw[iLineLoc + iWaypointLoc]:
                    continue
                else:
                    isMatch = False
                    continue
            if isMatch:
                print(iLineLoc + 1, ident)
                for jLineLoc in range(iLineLoc, iLineLoc + len(waypoints)):
                    temp = dbRaw[jLineLoc].split(',')
                    temp[2] = ident
                    dbRaw[jLineLoc] = ','.join(temp)
                break
    db = open(os.path.join(inputFolder, extract_name(iFile)[:4] + "_db.txt"), 'w', encoding="utf-8")
    db.writelines(dbRaw)
    db.close()
