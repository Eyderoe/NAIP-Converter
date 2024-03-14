import os.path
import string

import pandas as pd
from colorama import init
from 公共函数 import *


def rough_process(text: List[str]) -> List[str]:
    """
    对读取到的文本进行初略整理
    :param text: 文本
    :return: 整理后的文本
    """

    def table_head_process(content: str) -> str:
        """表格头处理"""
        if "描述" not in content:
            return content
        else:
            alt_correct = speed_correct = "1"
            if "(m)" in content:
                alt_correct = "3.28084"
            elif "(ft)" in content:
                alt_correct = "1"
            else:
                printf("未找到高度单位", 1)
            if "(kt)" in content:
                speed_correct = "1"
            elif "(km/h)" in content:
                speed_correct = "0.5399568"
            else:
                printf("未找到速度单位", 1)
            return "unit,{},{}".format(alt_correct, speed_correct)

    def head_rough(content: str) -> str:
        """
        将标题的逗号删掉。后面加的 所以看起来很突兀
        :param content: 行文本
        :return: 对应处理后的文本
        """
        temp_str = content.replace(' ', '')
        temp_str = temp_str.replace('^', '')
        if temp_str.startswith("RWY") or ("等待" in temp_str):
            temp_str = empty(content.replace('^', ' '), 1)
            temp_str = temp_str.replace("(by ATC)", '')
            return temp_str
        else:
            return content

    text = [i for i in text if not all(char in (' ', '\n', '^') for char in i)]  # 删除空行
    text = [i for i in text if ("修改" not in i) and ("注" not in i)]  # 删除注释
    text = [empty(i, 2) for i in text]  # 删除末尾换行空格
    text = [head_rough(i) for i in text]  # 使用强还原剂还原标题
    text = [table_head_process(i) for i in text]  # 生成单位修正
    return text.copy()


class Procedure:
    def __init__(self, name: str):
        self.type = ""
        self.name = name
        self.content = []
        self.runway = []

    def output(self) -> List[str]:
        """打包程序"""
        self.content.insert(0, "HE,{},{},{}".format(self.type, '/'.join(self.runway), self.name))
        self.content[0] = self.content[0].replace("//", '/')
        return [i + '\n' for i in self.content]

    def find_runway(self):
        """确定跑道"""
        chinese_loc = -1
        temp_name = self.name
        for i_char_loc in range(len(temp_name)):
            if '\u4e00' <= temp_name[i_char_loc] <= '\u9fff':
                chinese_loc = i_char_loc
                break
        if chinese_loc < 5:
            if chinese_loc == 0:
                temp_name = "RWY-1 " + temp_name
            chinese_loc = temp_name.index(' ')
        temp_name = temp_name[:chinese_loc]
        temp_name = temp_name.replace('、', ' ')
        delete_list = ["RNP", "R NP", "AR", "XN"] + list(string.ascii_lowercase)
        for i_delete in delete_list:
            if i_delete in temp_name:
                temp_name = temp_name[:temp_name.index(i_delete)]
        if temp_name.count("RWY") > 1:
            temp_name = temp_name[:temp_name.index(" RWY")]
        temp_name = temp_name[3:]
        # 这里重写一次 艹 当前进度
        temp_name = temp_name.split()
        for iRwyLoc in range(len(temp_name)):
            # 21 21L 21L/21R 21L/R
            if '/' in temp_name[iRwyLoc]:
                if (len(temp_name[iRwyLoc]) == 5) and ('L' in temp_name[iRwyLoc]):
                    temp_name.extend([temp_name[iRwyLoc][:3], temp_name[iRwyLoc][:2] + temp_name[iRwyLoc][-1]])
                elif len(temp_name[iRwyLoc]) == 5:  # 存在343/5情况
                    temp_temp = temp_name[iRwyLoc].replace('/', '')
                    temp_name.extend([temp_temp[:2], temp_temp[2:]])
                else:
                    temp_name.extend(temp_name[iRwyLoc].split('/'))
        for iRwyLoc in range(len(temp_name) - 1, -1, -1):
            if '/' in temp_name[iRwyLoc]:
                temp_name.pop(iRwyLoc)
        self.runway = temp_name.copy()

    def set_type(self):
        """确定程序类型"""
        pn = self.name
        # 首先把等待的都给拿掉
        if "等待" in pn:
            self.type = "00"

        # 然后是进近过渡 注意没有进场过渡
        elif (("进近" in pn) and ("过渡" in pn)) or (("过渡" in pn) and ("方向" in pn)) \
                or ("进 近过渡" in pn) or (("IAF" in pn) and ("IF" in pn)) or ("至FAP" in pn) \
                or ("-FAF" in pn) or ("起始进近" in pn):
            self.type = "01"
        elif (("离场" in pn) and ("过渡" in pn)) or (("离场" in pn) and ("公共段" in pn)) or\
                (("SHGRL1" in pn) and ('-' not in pn)) or (("DEQIN1" in pn) and ('-' not in pn)):
            self.type = "02"
        elif "过渡" in pn:
            self.type = "01"
            # if "进场" in pn:  # 信息过多 可能造成丢失重要信息
            #     printf("注意进场过渡程序: {}".format(pn), 2)

        # 然后就是这些正常的程序
        elif ("离场" in pn) or ("失效" in pn) or ("EO" in pn):
            self.type = "03"
        elif ("进场" in pn) or ("进 场" in pn):
            self.type = "04"
        elif "进近" in pn and "复飞" in pn:
            self.type = "05"
        elif "进 近" in pn and "复飞" in pn:
            self.type = "05"
        elif "进近" in pn:
            self.type = "06"
        elif "复飞" in pn:
            self.type = "07"
        else:
            printf("未知程序类型：{}".format(pn), 1)

    def add_leg(self, leg: str):
        """添加一个航点描述"""
        self.content.append(leg)

    def is_rubbish(self) -> bool:
        """程序应该保留吗"""
        if "ILS" in self.name or "调机" in self.name:
            if self.name.count("RNP") == 2:  # 出现在ZPPP: AR和ILS过渡段相同
                self.set_type()
                return False
            else:
                return True
        else:
            self.set_type()
            return False

    def encode(self):
        """对程序进行编码"""
        if len(self.content) == 0:
            printf("程序怎么是空的", 1)
        for iWptLoc in range(len(self.content)):
            temp_str = self.content[iWptLoc]
            temp_str = temp_str.split('^')
            # (0)类型 航点 (2)飞越 航向 (4)转向 高度L (6)高度H 速度 (8)下滑道 中心点 (10)距离 性能
            describe = [None, None, None, None, None, None, None, None, None, None, None, None]
            # 类型
            i_type = temp_str[0][:2]
            if temp_str[0][:2] in ("CA", "CF", "FA", "DF", "VA", "IF", "TF", "RF", "HM", "HF", "PS"):
                describe[0] = i_type
            else:
                printf("未知航路点类型: {}".format(temp_str), 1)
            # 航点
            describe[1] = empty(temp_str[1], 5)
            if describe[1] == '':
                describe[1] = ' '
            # 中心点和距离
            center = distance = ' '
            if describe[0] == "RF":
                rf = empty(temp_str[0], 5)
                rf = rf[rf.index('[') + 1:][:-1]
                center = rf.split(',')[0]
                distance = rf.split(',')[1]  # 距离没用 fenix自己算 toLiss要求半径精准
            describe[9] = center
            describe[10] = distance
            # 飞跃
            overfly = temp_str[2]
            describe[2] = '1' if not empty(overfly, 4) else ' '
            # 航向
            heading = temp_str[3]
            describe[3] = str(int(heading)) if not empty(heading, 4) else ' '
            # 转向
            describe[4] = temp_str[4]
            # 下滑道
            describe[8] = ' '
            if (len(temp_str) == 9) and (not empty(temp_str[7], 4)):  # 带有下滑道的表格
                gs = temp_str[7]
                if '/' in gs:
                    gs = gs[:gs.index('/')]
                elif 'ã' in gs:
                    gs = gs[:gs.index('ã')]
                for iRubbish in ('-', '﹣', '¡', 'ã'):
                    gs = gs.replace(iRubbish, '')
                try:
                    float(gs)
                except ValueError:
                    if '%' in temp_str[7]:
                        printf("出现离场梯度要求: {}".format(temp_str[7]), 2)
                    else:
                        printf("下滑道错误: {}".format(temp_str[7]), 2)
                    gs = ''
                describe[8] = gs
            # RNP值 感觉没什么用 保持一致性 还是保留了
            describe[11] = "-1"
            # 确定速度
            describe[7] = ' '
            if not empty(temp_str[6], 4):
                describe[7] = (temp_str[6])
            # 确定高度限制
            describe[5] = describe[6] = "-1"
            if (not empty(temp_str[5], 4)) and (i_type not in ("HF", "HM")):  # 等待就不管了
                alt = temp_str[5].split()
                speed = []
                for iAlt in alt:
                    try:
                        speed.append(str(int(iAlt)))
                    except ValueError:
                        pass
                speed.sort(key=lambda x: int(x))
                if "_AltL_" in alt:
                    describe[5] = speed[0]
                if "_AltH_" in alt:
                    describe[6] = speed[-1]
            describe = [str(i) if (i is not None) else " " for i in describe]
            self.content[iWptLoc] = ','.join(describe)

    def vpa_encode(self, table: pd.DataFrame):
        """编码AR的VPA"""
        if (self.type != "05") and (self.type != "06"):
            return
        for iLine in self.content:
            i_line = iLine.split(',')
            if not empty(i_line[8], 4):
                return
        global iFile
        airport = iFile[:4]
        runway = self.runway[0]  # 进近肯定只有一个跑道 (
        table = table[table["Airport"] == airport]
        table = table[table["heading"] == runway]
        vip = table["VIP"].tolist()
        mapt = table["MAPt"].tolist()
        vpa = table["VPA"].tolist()
        ident = table["ident"].tolist()
        waypoint_list = [i.split(',')[1] for i in self.content]
        for iRecordLoc in range(len(vip)):
            if (ident[iRecordLoc] not in self.name) and (ident[iRecordLoc].upper() not in self.name) \
                    and (ident[iRecordLoc] != '*'):
                continue
            if (vip[iRecordLoc] not in waypoint_list) or (mapt[iRecordLoc] not in waypoint_list):
                continue
            vip_loc = waypoint_list.index(vip[iRecordLoc]) + 1
            mapt_loc = waypoint_list.index(mapt[iRecordLoc]) + 1
            vpa_value = vpa[iRecordLoc]
            for iLoc in range(vip_loc, mapt_loc):
                temp = self.content[iLoc].split(',')
                temp[8] = vpa_value
                self.content[iLoc] = ','.join(temp)
            break
        else:
            printf("程序: {}\n未能找到相应下滑道".format(self.name), 2)
            print(table)
            print(waypoint_list)


def revise(text: List[str]):
    """
    修正高度 速度 航点
    :param text: 文本
    :return: 修正后的文本
    """

    def alt_process(height: float) -> str:
        """对修正后的高度 四舍五入"""
        height = str(int(height))
        tail = int(height[-2:])
        height = height[:-2] + "00"
        return str(int(height) + (0 if tail <= 49 else 100))

    def speed_process(mach: float) -> str:
        """对修正后的高度 四舍五入"""
        mach = str(int(mach))
        tail = int(mach[0])
        mach = int(mach[:2] + '0')
        if tail <= 2:
            tail = 0
        elif tail <= 6:
            tail = 5
        else:
            tail = 10
        return str(mach + tail)

    speed = 1
    altitude = 1
    for iLineLoc in range(len(text)):
        line = text[iLineLoc]
        if line.startswith("unit"):  # 修正
            altitude = float(line.split(',')[1])
            speed = float(line.split(',')[2])
            continue
        elif line.count('^') == 0:  # 程序名
            continue
        else:
            line = line.split('^')

        # 描述
        line[0] = empty(line[0], 5)
        # 航点
        waypoint = line[1]
        if not empty(waypoint, 4):
            waypoint = empty(waypoint, 5)  # 对ZSGZ的CF 15修正
            if "(" in waypoint:  # 对ZGNN的NN413(P20)修正
                waypoint = waypoint[:waypoint.index('(')]
            line[1] = waypoint
        # 高度
        alt = line[5]
        if not empty(alt, 4):
            alt = alt.split()
            alt = [empty(i, 5) for i in alt]
            number = 0
            limit_l = limit_h = 0

            for iRubbish in ("or", "by", "ALT", "ATC", "Alt"):  # 删除一些奇奇怪怪的
                while iRubbish in alt:
                    alt.remove(iRubbish)
            for iElementLoc in range(len(alt)):  # 针对900or1200这种情况
                if ("or" in alt[iElementLoc]) and (alt[iElementLoc][0].isdigit()):
                    mix_alt = alt[iElementLoc]
                    alt.append(mix_alt[:mix_alt.index('o')])
                    alt.append(mix_alt[mix_alt.index('r') + 1:])
                    alt.pop(iElementLoc)
                    break
            for iElementLoc in range(len(alt)):  # 1800、2100
                if '、' in alt[iElementLoc]:
                    alt[iElementLoc] = alt[iElementLoc][:alt[iElementLoc].index('、')]
            for iElementLoc in range(len(alt)):  # 统计
                try:
                    alt[iElementLoc] = alt_process(round(int(alt[iElementLoc]) * altitude, 0))
                    number += 1
                except ValueError:
                    if alt[iElementLoc] == "_AltL_":
                        limit_l += 1
                    elif alt[iElementLoc] == "_AltH_":
                        limit_h += 1
                    else:
                        printf("未能识别的字符串{}".format(alt[iElementLoc]), 2)
            limit = limit_h + limit_l
            if len(alt) == 0:  # 全文字描述
                alt.clear()
                alt.append(' ')
            elif (number == 1) and (limit == 0) and (line[0] in ("CA", "VA", "FA")):  # CA VA FA
                alt.append("_AltL_")
            elif (number == 1) and (limit == 0):  # 建议高度
                alt.append("_AltL_ _AltH_")
            elif (number == 1) and (1 <= limit <= 2):  # 单一高度
                pass
            elif (number == 2) and (limit_h == limit_h) and (limit_h == 1):  # 高低限制
                pass
            elif (number == 2) and (limit == 0):  # 双建议高度
                alt.pop(1)
                alt.append("_AltL_ _AltH_")
            elif (number == 2) and (limit_l == 2):  # 双最低限制
                alt.pop(3)
                alt.pop(1)
            elif (number == 2) and (limit_l == 1):  # 最低和建议限制
                alt.pop(2)
            else:
                printf("未知高度格式: {}".format(alt), 2)
            line[5] = ' '.join(alt)
        # 速度
        velocity = line[6]
        if not empty(velocity, 4):
            velocity = velocity.replace("MAX", '')
            velocity = velocity.replace("AT", '')
            try:
                velocity = speed_process(round(int(velocity) * speed, 0))
            except ValueError:
                printf("未知速度限制: {}".format(velocity), 2)
                velocity = ' '
            line[6] = velocity
        # 结束
        text[iLineLoc] = '^'.join(line)


def read_procedures(lines: List[str]) -> List[Procedure]:
    """
    将连续的文本行转换为离散的程序
    :param lines: 文本行
    :return: 程序列表
    """
    procedure_list = []
    for i_line in lines:
        if (i_line.startswith("RWY")) or ("等待" in i_line):
            procedure_list.append(Procedure(i_line))
        else:
            procedure_list[-1].add_leg(i_line)
    return procedure_list.copy()


init(autoreset=True)
inputFolder = r"F:\PDF初提取"
outputFolder = r"F:\PDF初提取"
vpaFile = pd.read_excel(r"E:\Python项目\Fenix 重构\VPA.xlsx", dtype=str)
vpaFile["heading"] = vpaFile["Runway"].apply(lambda x: x if x[-1] in string.digits + "LCR" else x[:-1])
vpaFile["ident"] = vpaFile["Runway"].apply(lambda x: x[-1].lower() if x[-1] not in string.digits + "LCR" else '*')
fileList = os.listdir(inputFolder)
for iFile in fileList:
    if "procedure" not in iFile:
        continue
    printf(iFile[:4], 3)
    txtFile = open(os.path.join(inputFolder, iFile), 'r', encoding="utf-8")
    txt = txtFile.readlines()
    txtFile.close()
    # 简单修正
    txt = rough_process(txt)
    revise(txt)
    txt = [i for i in txt if not i.startswith("unit")]
    # 单程序处理
    procedures = read_procedures(txt)
    procedures = [i for i in procedures if not i.is_rubbish()]
    [i.encode() for i in procedures]
    [i.find_runway() for i in procedures]
    [i.vpa_encode(vpaFile) for i in procedures]
    # 输出
    outputFile = open(os.path.join(outputFolder, iFile[:-14]) + "_encode.txt", 'w', encoding="utf-8")
    for iProc in procedures:
        outputFile.writelines(iProc.output())
    outputFile.close()
