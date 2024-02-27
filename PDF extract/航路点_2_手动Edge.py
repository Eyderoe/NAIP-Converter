from colorama import Fore, init
from 公共函数 import *

init(autoreset=True)
inputPath = r".\input\zhqq.txt"
outputPath = r".\output\zhqq.txt"
inputFile = open(inputPath, 'r', encoding="utf-8")
outputFile = open(outputPath, 'w', encoding="utf-8")
inputLines = inputFile.readlines()
inputFile.close()
inputLines = [i for i in inputLines if "修改" not in i]
inputLines = [i for i in inputLines if not empty(i, 4)]
inputLines = [empty(i, 2) for i in inputLines]

name = inputLines[:len(inputLines) // 2]
location = inputLines[len(inputLines) // 2:]
with open(outputPath+"check",'w',encoding="utf-8") as f:
    f.writelines(["{} {}\n".format(name[i],location[i]) for i in range(len(name))])
newLocation = []
print(len(name), len(location))
for i in range(len(location)):
    location[i] = location[i].replace("¡ã", '°')
    for iChar in ('N', 'E', '\'', '\"', '°'):
        while iChar in location[i]:
            loc = location[i].index(iChar)
            location[i] = location[i][:loc] + ' ' + location[i][loc + 1:]
    location[i] = location[i].split()
    if len(location[i]) not in (4, 6):
        printf("航点坐标错误", 1)
    numCount = len(location[i])  # 4或6
    judge = numCount // 2  # 2或3 (晚上写，脑壳有点旷)
    location[i] = [float(i) for i in location[i]]
    # location大概这样[[36.0, 14.0, 20.9, 113.0, 7.0, 28.7], [36.0, 7.0, 20.8, 113.0,...],...]
    for ii in range(numCount):
        if ii % judge == 0:
            newLocation.append(float(location[i][ii]) / (60 ** (ii % judge)))  # 应该是误标黄 hmm...改成
        else:
            newLocation[-1] += float(location[i][ii]) / (60 ** (ii % judge))
newLocation = [round(i, 10) for i in newLocation]
newLocation = [str(i) for i in newLocation]
for i in range(len(name)):
    outputFile.write(name[i] + ' ' + newLocation[i * 2 + 0] + ' ' + newLocation[i * 2 + 1] + '\n')
outputFile.close()
