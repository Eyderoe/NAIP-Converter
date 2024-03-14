import pdfplumber
from pdfplumber.page import CroppedPage
from typing import List, Union
import os
from 公共函数 import *


class Line:
    def __init__(self, line: dict):
        self.is_horizontal = True if line["width"] > 5 else False  # 水平 / 竖直
        self.top = line["top"]  # 上边距
        self.left = line["x0"]  # 左侧边距
        self.length = line["width"] if self.is_horizontal else line["height"]  # 长度


class Word:
    def __init__(self, info: dict):
        self.content = info["text"]
        self.center = ((info["x0"] + info["x1"]) / 2, (info["top"] + info["bottom"]) / 2)
        self.top = info["top"]
        self.down = info["bottom"]


class Unit:
    def __init__(self):
        self.words = []
        self.lines = []  # 下划线

    def add_element(self, element: Union[Word, Line]):
        """向单元格中添加文本或下划线"""
        if type(element) == Word:
            self.words.append(element)
        else:
            self.lines.append(element)

    def match_underline(self):
        """下划线匹配 加入对应文本"""
        if len(self.lines) == 0:
            return
        for iLine in self.lines:
            for iWord in self.words:
                if any(char.isdigit() for char in iWord.content):  # 含有数字
                    top_distance = abs(iLine.top - iWord.top)
                    down_distance = abs(iLine.top - iWord.down)
                    alt_limit = " _AltL_ " if down_distance < top_distance else " _AltH_ "
                    iWord.content += alt_limit
                    break
            else:
                printf("下划线未找到归属", 2)

    def get_unit_text(self) -> str:
        """获取单元格文本"""
        self.words.sort(key=lambda x: x.center[0])
        text = ' '.join([i.content for i in self.words])
        return text if len(text) != 0 else ' '


class Row:
    def __init__(self, top: float, bottom: float):  # 均相对于上边界
        self.top = top
        self.bottom = bottom
        self.separations = []
        self.units = []

    def add_sep(self, left: float):
        """确定每个单元格的横向范围 分隔"""
        if (len(self.separations) >= 1) and (left - self.separations[-1] < 1):  # 考虑到可能没有合并线段
            return
        else:
            self.separations.append(left)

    def add_unit(self):
        """确定分隔后 添加对应数量单元格"""
        for iSepCount in range(len(self.separations) - 1):
            self.units.append(Unit())

    def add_element(self, element: Union[Word, Line]):
        """向这行中添加文本或者下划线"""
        x = element.center[0] if type(element) == Word else element.left
        loc = -1
        for iSepLoc in range(len(self.separations) - 1):
            if self.separations[iSepLoc] <= x <= self.separations[iSepLoc + 1]:
                loc = iSepLoc
                break
        else:
            # ZSPD ZUAL ZUUU
            if type(element) == Word:
                printf("未找到单词{}所属列".format(element.content), 2)
            else:
                printf("未找到下划线所属列", 2)
        self.units[loc].add_element(element)

    def in_row(self, y: float) -> bool:
        """y值是否在此行中"""
        if self.top <= y <= self.bottom:
            return True
        else:
            return False

    def get_row_text(self) -> str:
        """获得这行的文本"""
        return '^'.join([i.get_unit_text() for i in self.units])


class Table:
    def __init__(self):
        self.vertical_lines = []  # 水平分割线
        self.horizontal_lines = []  # 竖直分割线
        self.under_lines = []  # 下滑线
        self.rows = []

    def add_line(self, line: dict):
        """将线条加入表格"""
        if (line["width"] < 20) and (line["width"] > 5):
            self.under_lines.append(Line(line))
        elif line["width"] > 30:
            self.horizontal_lines.append(Line(line))
        elif line["height"] > 5:
            self.vertical_lines.append(Line(line))

    def add_word(self, word: Word):
        """将线条放入对应单元格"""
        for iRowLoc in range(len(self.rows)):
            if self.rows[iRowLoc].in_row(word.center[1]):
                self.rows[iRowLoc].add_element(word)
                break
        else:
            printf("未找到单词所属行", 1)

    def establish_unit(self):
        """建立单元格"""
        self.vertical_lines.sort(key=lambda x: x.left)
        self.horizontal_lines.sort(key=lambda x: x.top)
        for iLevelLineLoc in range(len(self.horizontal_lines) - 1):
            # 创建一行
            up_line = self.horizontal_lines[iLevelLineLoc]
            down_line = self.horizontal_lines[iLevelLineLoc + 1]
            if abs(up_line.top - down_line.top) < 2:  # 应该是库的bug没有合并线段
                continue
            self.rows.append(Row(up_line.top, down_line.top))
            # 创建一行的间隔
            for iLine in self.vertical_lines:
                middle_top = (up_line.top + down_line.top) / 2  # 中间点上边距
                if iLine.top <= middle_top <= iLine.top + iLine.length:
                    self.rows[-1].add_sep(iLine.left)
            if len(self.rows[-1].separations) not in (2, 9, 10):
                # 2312: ZLHB ZPBS ZWTK
                printf("单行分隔符数量{},不符合预期".format(len(self.rows[-1].separations)), 2)
        seps = [len(i.separations) for i in self.rows]
        # 对分隔符采取修正 采取多数正确的策略
        # if len(set(seps)) > 2:
        #     printf("表格分隔符数量不一致", 2)
        #     standard = [[2, seps.count(2)], [9, seps.count(9)], [10, seps.count(10)]]  # 2 9 10 是标准模型
        #     standard.sort(key=lambda x: x[1], reverse=True)
        #     standard.pop(2)
        #     standard.sort(key=lambda x: x[0])
        #     standard_title = self.rows[seps.index(standard[0][0])].separations
        #     standard_content = self.rows[seps.index(standard[1][0])].separations
        #     standard = [i[0] for i in standard]
        #     for iRowLoc in range(len(self.rows)):
        #         i_row_sep = self.rows[iRowLoc].separations
        #         if len(i_row_sep) not in standard:
        #             title_distance = abs(len(i_row_sep) - 2)
        #             content_distance = abs(len(i_row_sep) - 9)
        #             if title_distance < content_distance:
        #                 self.rows[iRowLoc].separations = standard_title.copy()
        #             else:
        #                 self.rows[iRowLoc].separations = standard_content.copy()
        # 有正常的内容被识别为标题的可能，不知道为什么。直接默认为内容，后面encode的时候再删
        standard = [[9, seps.count(9)], [10, seps.count(10)]]  # 9 10 是标准模型
        standard.sort(key=lambda x: x[1], reverse=True)
        standard_content = self.rows[seps.index(standard[0][0])].separations
        for iRowLoc in range(len(self.rows)):
            if seps[iRowLoc] != standard[0][0]:
                self.rows[iRowLoc].separations = standard_content.copy()
        # 添加单元格
        for iRow in self.rows:
            iRow.add_unit()

    def match_underline(self):
        """发布下划线匹配指令"""
        for iLine in self.under_lines:
            for iRow in self.rows:
                if iRow.in_row(iLine.top):
                    iRow.add_element(iLine)
                    break
            else:
                printf("未找到单词所属行", 1)
        for iRow in self.rows:
            for iUnit in iRow.units:
                iUnit.match_underline()

    def get_table_text(self) -> str:
        """获取表格文本"""
        return '\n'.join([i.get_row_text() for i in self.rows])


def process(cut_page: CroppedPage) -> str:
    """
    提取单张表格内容
    :param cut_page: 分页后的页面 确保了只有一张表格
    :return: 表格提取出的文本
    """
    # 总体思路：提取线条组成单元格，将文本放入单元格，加入下划线进行匹配
    # 提取所有线，建立表格
    lines = cut_page.lines
    coding_table = Table()
    for i_line in lines:
        coding_table.add_line(i_line)
    coding_table.establish_unit()
    # 提取文本，加入表格
    words = cut_page.extract_words()
    for iWord in words:  # iWord这里没问题
        coding_table.add_word(Word(iWord))
    # 下划线
    coding_table.match_underline()
    return coding_table.get_table_text() + "\n"


def extract_table(pdf: pdfplumber.PDF) -> str:
    """
    提取一个pdf文件中的表格文本 对多表格的文件进行分发
    :param pdf: pdf文件
    :return: 表格文本
    """
    first_page = pdf.pages[0]  # 把唯一的一页拿出来
    scale = first_page.height / first_page.width
    text = ''
    if abs(scale - 1.47) < 0.1:  # 单张表格的情况
        print("单表\n")
        table_1 = first_page.within_bbox((26, 49, 410, 577))
        text_1 = process(table_1)
        text += text_1
    elif abs(scale - 0.76) < 0.1:  # 双张表格的情况
        print("双表\n")
        table_1 = first_page.within_bbox((26, 49, 410, 577))
        table_2 = first_page.within_bbox((410, 49, 805, 577))
        text_1 = process(table_1)
        text_2 = process(table_2)
        text += text_1
        text += text_2
    elif abs(scale - 0.51) < 0.1:  # 三张表格的情况 2307还有 2312好像就没了
        print("三表\n")
        table_1 = first_page.within_bbox((26, 49, 410, 577))
        table_2 = first_page.within_bbox((410, 49, 805, 577))
        table_3 = first_page.within_bbox((805, 49, 1200, 577))
        text_1 = process(table_1)
        text_2 = process(table_2)
        text_3 = process(table_3)
        text += text_1
        text += text_2
        text += text_3
    else:
        printf("pdf页面尺寸存在问题", 1)
    return text


# 文件路径设置
outputFolder = r"F:\PDF初提取"
inputFolder = r"F:\航图\中国民航国内航空资料汇编 NAIP 2402\terminals"
csvFolder = r"D:\naip\input"
# 获取文件
file_list = []
walking(inputFolder, file_list)
file_list = [i for i in file_list if ".pdf" in i]
file_list.sort(key=extract_name)
# 获取可用文件列表
chartName, runways = get_info(csvFolder, "数据库")
# 断点续读
crash_airport = None
crash_airport_only = True
if crash_airport is not None:
    temp_path = []
    for i_file in file_list:
        if crash_airport in i_file:
            break
        else:
            temp_path.append(i_file)
    for i_file in temp_path:
        file_list.remove(i_file)
# 正文开始
meetAirport = []  # 读取到的机场
for iPath in file_list:
    chartNow = extract_name(iPath)
    if chartNow not in chartName:
        continue
    print(chartNow)
    airportNow = chartNow[:chartNow.index('-')]
    if airportNow not in meetAirport:
        if len(meetAirport) == 1:  # 用于对单一机场进行建图
            if crash_airport is not None and crash_airport_only:
                exit(932)
        outputFile = open(os.path.join(outputFolder, airportNow + "_procedure.txt"), 'w', encoding="utf-8")
        outputFile.close()
        meetAirport.append(airportNow)

    # 正文部分
    pdfNow = pdfplumber.open(iPath)
    pdfText = extract_table(pdfNow)
    outputFile = open(os.path.join(outputFolder, airportNow + "_procedure.txt"), 'a+', encoding="utf-8")
    outputFile.write(pdfText)
    outputFile.close()
    pdfNow.close()
