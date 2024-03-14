import os
from typing import List, Union, Tuple

import pandas as pd
from colorama import Fore


class Waypoint:
    def __init__(self, la: float, long: float, ident: str, cat: int, airport: str = '', area: str = ''):
        self.latitude = la
        self.longitude = long
        self.ident = ident
        self.cat = cat  # 建议:-1状态不可用 1航点 2VHF 3NDB
        self.airport = airport
        self.area = area

    def is_same(self, fix: "Waypoint", change: bool = False) -> bool:
        """
        判断是否是一个航路点
        :param fix: Waypoint对象
        :param change: 是的话,会将airport属性转换为ENRT
        :return: 是否可认为相同
        """
        if fix.ident != self.ident:
            return False
        la_error = abs(self.latitude - fix.latitude)
        long_error = abs(self.longitude - fix.longitude)
        if la_error > 0.2 or long_error > 0.2:
            return False
        if change:
            self.airport = "ENRT"
        return True


def get_info(folder: str, aim: str) -> Tuple[List[str], dict]:
    """
    "寻找 1.某编码的文件名 2.跑道
    :param folder: 文件夹
    :param aim: 目标 数据库 / 航路点
    :return:
    """
    rw_path = os.path.join(folder, "RWY.csv")
    rw_file = pd.read_csv(rw_path, encoding="gbk")
    airport_rw = rw_file["CODE_AIRPORT"].tolist()
    runway_rw = rw_file["TXT_DESIG"].tolist()
    runway_dict = dict()
    for i in range(len(airport_rw)):
        key_airport = airport_rw[i]
        if key_airport in runway_dict:
            runway_dict[key_airport] += runway_rw[i].split('/')
        else:
            runway_dict[key_airport] = runway_rw[i].split('/')

    code_path = os.path.join(folder, "Charts.csv")
    code_file = pd.read_csv(code_path, encoding="gbk")
    code_file["combine"] = code_file["AirportIcao"] + "-" + code_file["PAGE_NUMBER"]
    code_file = code_file[code_file["ChartName"].str.contains(aim)]
    combine = code_file["combine"].tolist()
    combine.sort()
    return combine, runway_dict


def printf(string: str, mode: int):
    """
    输出信息
    :param string: 内容
    :param mode: 1警告 2警戒 3进程 4什么都不干
    """
    if mode == 4:
        return
    if mode == 1:
        print(Fore.RED + "<警告!!>" + Fore.RESET, end=' ')
        print(string)
        input()
        exit()
    elif mode == 2:
        print(Fore.YELLOW + "<警戒!>" + Fore.RESET, end=' ')
        print(string)
    elif mode == 3:
        print(Fore.GREEN + "<进程>" + Fore.RESET, end=' ')
        print(string)
    else:
        printf("未知模式", 1)


def empty(string: str, mode: int) -> Union[str, bool]:
    """
    :param string: 待处理字符串
    :param mode: 1清除头部 2清除尾部 3清除头部尾部 4为空 5清除所有空白
    """
    empty_list = ('\n', ' ', '\t')
    if mode == 1:
        while string[0] in empty_list:
            string = string[1:]
        return string
    elif mode == 2:
        while string[-1] in empty_list:
            string = string[:-1]
        return string
    elif mode == 3:
        a = empty(string, 1)
        return empty(a, 2)
    elif mode == 4:
        for iChar in string:
            if iChar not in empty_list:
                return False
        else:
            return True
    elif mode == 5:
        for empty_char in empty_list:
            while empty_char in string:
                loc = string.index(empty_char)
                string = string[:loc] + string[loc + 1:]
        return string
    else:
        printf("代码写错了吧 ♥ 杂鱼~", 1)


def walking(fold: str, file_list: List[str]):
    """
    遍历目录 将所有文件的绝对路径放在列表中
    :param fold: 目录路径
    :param file_list: 列表
    """
    a = os.listdir(fold)
    for j in a:
        j = os.path.join(fold, j)
        if os.path.isfile(j):
            file_list.append(j)
        else:
            walking(j, file_list)


def extract_name(path: str) -> str:
    """
    提取绝对路径中的文件名
    :param path: 绝对路径
    :return: 文件名
    """
    path = os.path.basename(path)
    try:
        return path[:path.index('.')]
    except IndexError:
        printf("文件不存在后缀", 2)
        return path
