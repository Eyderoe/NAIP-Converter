import pdfplumber
from colorama import Fore, init
from pdfplumber.page import CroppedPage
from typing import List, Union
import pandas as pd
import string
import os
from 公共函数 import *


def extract(pdf: pdfplumber.PDF) -> List[str]:
    """md 直接处理好算了"""

    def insert_sep(cstring: str) -> str:
        """分割多个航路点"""
        dewpoint = []
        for iii in range(len(cstring)):  # 经度°的位置
            if (cstring[iii] == '°') and (cstring[iii - 3] != 'N'):
                dewpoint.append(iii)
        for iii in range(len(dewpoint) - 1):  # °后面字母的位置，最后一个不管
            loc = dewpoint[iii]
            while True:
                if cstring[loc] in string.ascii_uppercase:
                    dewpoint[iii] = loc
                    break
                loc += 1
        for i_loc in range(len(dewpoint) - 1, -1, -1):
            loc = dewpoint[i_loc]
            cstring = cstring[:loc] + "*" + cstring[loc:]
        last_star = cstring.rfind('*')
        cstring = cstring[:last_star] + '°' + cstring[last_star + 1:]
        return cstring

    def calculation(fstring: str) -> str:
        loc = fstring.rfind('E')
        fstring = fstring[:loc] + ' ' + fstring[loc + 1:]
        loc = fstring.rfind('N')
        fstring = fstring[:loc] + ' ' + fstring[loc + 1:]
        fstring = fstring.replace('°', ' ')
        fstring = fstring.replace('\'', ' ')
        fstring = fstring.replace('\"', ' ')
        fstring = fstring.split()
        precise = (len(fstring) - 1) // 2  # 有几位小数
        name = fstring[0]
        i_latitude = 0
        i_longitude = 0
        for ij in range(1, len(fstring)):
            if ij <= precise:
                i_latitude += float(fstring[ij]) / (60 ** ((ij - 1) % precise))
            else:
                i_longitude += float(fstring[ij]) / (60 ** ((ij - 1) % precise))
        i_latitude = str(round(i_latitude, 8))
        i_longitude = str(round(i_longitude, 8))
        return "{} {} {}".format(name, i_latitude, i_longitude)

    def exchange(cstring: str) -> str:
        # 针对的是 12.34AB"CDE的情况，从"往前找大写字母
        for ii in range(len(cstring)):
            if cstring[ii] == '\"':
                jj = ii - 1
                while cstring[jj] in string.ascii_uppercase:
                    jj -= 1
                cstring = cstring[:jj + 1] + '\"' + cstring[jj + 1:ii] + cstring[ii + 1:]
        # 针对的是 12A.3"BCDE
        return cstring

    def process(cut_page: CroppedPage) -> List[str]:
        """对单页面进行处理，返回初步处理后的List[str]"""
        # 返璞归真 再次改为读取行然后扔掉空格 然后算
        # 读取行 扔掉空白
        waypoint_list = []
        text_lines = cut_page.extract_text_lines()
        text_lines = [i["text"] for i in text_lines]
        text_lines = [empty(i, 5) for i in text_lines]
        text_lines = [exchange(i) for i in text_lines]
        text_lines = [i.replace("¡ã", '°') for i in text_lines]
        for iiiii in text_lines:
            print(iiiii)
        input("确定下一步：")
        text_lines = open(os.path.join(inputFolder,"waypoint.txt"),'r',encoding="utf-8")
        text_lines = text_lines.readlines()
        text_lines=[i for  i in text_lines if not empty(i,4)]
        text_lines = [empty(i, 2) for i in text_lines]
        # 把航点分割开来
        text_lines = list(map(insert_sep, text_lines))
        text_lines = list(map(lambda x: x.split('*'), text_lines))
        for i_line in text_lines:
            for i_waypoint in i_line:
                waypoint_list.append(calculation(i_waypoint))
        return waypoint_list.copy()

    first_page = pdf.pages[0]  # 把唯一的一页拿出来
    page_width = first_page.width
    page_height = first_page.height
    scale = page_height / page_width
    all_text = []
    if abs(scale - 1.47) < 0.1:  # 单张表格的情况
        # print("单页\n")
        table_1 = first_page.within_bbox((26, 67, 410, 560))  # 表头都给去掉，但这样线就没了，把这个加上
        text_1 = process(table_1)
        all_text = text_1
    elif abs(scale - 0.76) < 0.1:  # 双张表格的情况
        # print("双页\n")
        table_1 = first_page.crop((26, 67, 410, 560))
        table_2 = first_page.crop((410, 67, 805, 560))
        text_1 = process(table_1)
        text_2 = process(table_2)
        all_text = text_1
        all_text += text_2
    elif abs(scale - 0.51) < 0.1:  # 双张表格的情况
        # print("三页\n")
        table_1 = first_page.crop((26, 67, 410, 560))
        table_2 = first_page.crop((410, 67, 805, 560))
        table_3 = first_page.crop((805, 67, 1200, 560))
        text_1 = process(table_1)
        text_2 = process(table_2)
        text_3 = process(table_3)
        all_text = text_1
        all_text += text_2
        all_text += text_3
    else:
        printf("比例有点问题", 0)
    return all_text.copy()


def walking(fold: str):
    """遍历目录 并将文件的绝对路径放在(global)file_list里面"""
    a = os.listdir(fold)
    global file_list
    for j in a:
        j = os.path.join(fold, j)
        if os.path.isfile(j):
            file_list.append(j)
        else:
            walking(j)


def extract_name(path: str):
    """路径中提取文件名"""
    path = os.path.basename(path)
    return path[:path.index('.')]


init(autoreset=True)
# 文件路径设置
outputFolder = r"E:\Python项目\Fenix 重构\output"
inputFolder = r"E:\Python项目\Fenix 重构\input"
aimport = "ZLXY"
# 获取文件
file_list = []
walking(inputFolder)
file_list = [i for i in file_list if ".pdf" in i]
file_list.sort(key=extract_name)
# 不能自动读取的文件
fatal_list = []
# 断点续读
crash_airport = None
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
    if aimport not in chartNow:
        continue
    printf(chartNow, 3)
    airportNow = chartNow[:chartNow.index('-')]
    if airportNow not in meetAirport:
        outputFile = open(os.path.join(outputFolder, airportNow + "_waypoint.txt"), 'w', encoding="utf-8")
        outputFile.close()
        meetAirport.append(airportNow)
    # 正文小字部分
    pdfNow = pdfplumber.open(iPath)
    textList = []
    textList = extract(pdfNow)
    pdfNow.close()
    outputFile = open(os.path.join(outputFolder, airportNow + "_waypoint.txt"), 'a+', encoding="utf-8")
    textList = [i + '\n' for i in textList]
    outputFile.writelines(textList)
    outputFile.close()
fatal_list = list(set(fatal_list))
fatal_list.sort()
# 这里10 ['ZBCZ', 'ZGNN', 'ZLJC', 'ZLXY', 'ZLZY', 'ZSGZ', 'ZUJZ', 'ZWBL', 'ZYDD']
# 检查1  ['ZLHB']
# 问题文件不一致 注意核对
printf("需手动完成{}:\n>>> ".format(len(fatal_list)) + str(fatal_list), 2)
