import string
from 公共函数 import *

inputFolder = r"F:\PDF初提取"
files = os.listdir(inputFolder)
allow = string.ascii_uppercase + string.digits
nameFatal = []
locationFatal = []
for iFile in files:
    if "waypoint" not in iFile:
        continue
    printf(iFile[:4], 3)
    with open(os.path.join(inputFolder, iFile), 'r', encoding="utf-8") as f:
        f = f.readlines()
        f = [i for i in f if not empty(i, 4)]
        f = [empty(i, 2) for i in f]
        for i in f:
            i = i.split()
            for iChar in i[0]:
                if iChar not in allow:
                    nameFatal.append(iFile[:4])
            try:
                assert 15 <= float(i[1]) <= 55
                assert 70 <= float(i[2]) <= 140
            except AssertionError:
                locationFatal.append(iFile[:4])
nameFatal = list(set(nameFatal))
nameFatal.sort()
locationFatal = list(set(locationFatal))
locationFatal.sort()
printf("名称错误: {}".format(str(nameFatal)), 2)
printf("坐标错误: {}".format(str(locationFatal)), 2)
