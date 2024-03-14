import os.path
from typing import Dict
import shutil

aptPath = r"apt.dat"
processFolder = r"output"
# 读取xp内部id和icao
table: Dict[str, str] = dict()
with open(aptPath, 'r', encoding="utf-8") as f:
    f = f.readlines()
    innerCode = ''
    icaoCode = ''
    for iLine in f:
        if iLine.startswith("1 "):
            innerCode = iLine.split()[4]
        elif iLine.startswith("1302 icao"):
            icaoCode = iLine.split()[2]
            if icaoCode != innerCode:
                table[icaoCode] = innerCode
# 增殖
files = os.listdir(processFolder)
absProcessPath = os.path.abspath(processFolder)
for iKey in table:
    if "{}.dat".format(iKey) in files:
        source = os.path.join(absProcessPath, "{}.dat".format(iKey))
        dest = os.path.join(absProcessPath, "{}.dat".format(table[iKey]))
        shutil.copy(source, dest)
