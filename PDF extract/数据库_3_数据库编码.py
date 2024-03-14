import os
from typing import Union
import string
from colorama import Fore, init
from 公共函数 import *


def read_procedure(file_path: str) -> Tuple[List[List[str]], List[List[str]], List[List[str]]]:
    """
    读取encode文本，将不同程序分类并返回
    :param file_path: encode文本路径
    :return: 程序列表
    """
    departures = []
    arrivals = []
    approaches = []
    with open(file_path, 'r', encoding="utf-8") as txt:
        txt = txt.readlines()
        txt = [i for i in txt if not i.startswith("PS")]  # 不读取这玩意了 改到2.5 读取PS和修改单位
        for iLineLoc in range(len(txt)):  # 去除NN413(P20)那种情况
            if txt[iLineLoc][:2] not in ("HE", "PS"):
                if "(" in txt[iLineLoc]:
                    temp_list = txt[iLineLoc].split(',')
                    temp_list[1] = temp_list[1][:temp_list[1].index('(')]
                    txt[iLineLoc] = ','.join(temp_list)
                    continue
                elif "（" in txt[iLineLoc]:
                    temp_list = txt[iLineLoc].split(',')
                    temp_list[1] = temp_list[1][:temp_list[1].index('（')]
                    txt[iLineLoc] = ','.join(temp_list)
                    continue
                else:
                    continue
        txt.append("HE,99,99,RWY99 文本停止符")
        procedure = []
        p_type = 0
        for iLine in txt:
            if iLine.startswith("HE"):
                if p_type:
                    if p_type == 1:
                        departures.append(procedure.copy())
                    elif p_type == 2:
                        arrivals.append(procedure.copy())
                    elif p_type == 3:
                        approaches.append(procedure.copy())
                    elif p_type == -1:
                        pass
                    else:
                        printf("goto值错误", 1)
                procedure.clear()
                if (iLine[3:5] == "03") or (iLine[3:5] == "02"):  # 离场
                    p_type = 1
                elif iLine[3:5] == "04":  # 进场
                    p_type = 2
                elif (iLine[3:5] == "00") and (("离场" in iLine) or ("进场" in iLine)):  # 离场等待 进场等待 不用
                    p_type = -1
                else:  # 进近
                    p_type = 3
            procedure.append(iLine)
    return departures.copy(), arrivals.copy(), approaches.copy()


def get_waypoint(procedure: List[str], is_head: bool) -> str:
    """
    获取程序的头部或尾部航点
    :param procedure: 程序
    :param is_head: 是：头部航点 否：尾部航点
    :return: 航点名称
    """
    procedure = [j for j in procedure if not empty(j, 4)]
    if is_head:
        temp = procedure[1].split(',')[1]
    else:
        temp = procedure[-1].split(',')[1]
    if empty(temp, 4):
        return ' '
    else:
        return temp


def procedure_info(procedure: List[str], category: int) -> Union[int, str, Tuple[int, str], Tuple[str, str]]:
    """
    返回该程序信息
    :param category: 1类型 2跑道 3程序编号 4(类型,跑道) 5首尾航点
    :param procedure: 程序
    :return: 1int 2str 3lower 4(int,str) 5(str,str)
    """
    global iFile
    if category == 1:
        # return int(procedure[0].split(',')[1])
        return int(procedure[0][3:5])
    elif category == 2:
        return procedure[0].split(',')[2]
    elif category == 3:
        temp_string = procedure[0]
        if iFile[:4] == "ZUAL":  # RWY15 进近、复飞 Z
            temp_string = temp_string.split(',')[3]
            temp_string = temp_string.replace("RWY", '')
            for iChar in temp_string:
                if iChar in string.ascii_uppercase:
                    return iChar
            else:
                return ''
        temp_string = temp_string.replace("via", ' ')
        temp_string = temp_string.replace("MAPt", ' ')
        temp_string = temp_string.replace("MAPTt", ' ')
        for iChar in temp_string:
            if iChar in string.ascii_lowercase:
                # print(procedure[0])
                return iChar
        else:
            return ''
    elif category == 4:
        return int(procedure[0].split(',')[1]), procedure[0].split(',')[2]
    elif category == 5:
        return procedure[1].split(',')[1], procedure[-1].split(',')[1]
    else:
        printf("get_info形参错误", 1)


def procedure_combine(first_proc: List[str], second_proc: List[str], pattern: int):
    """
    合并两个程序，直接对第二个程序进行修改
    :param first_proc: 内容添加至第二个程序
    :param second_proc: 被添加程序
    :param pattern: 模式
    """
    # 什么傻逼 为了写函数而写函数 真没必要 感觉
    if pattern == 1:  # 离场 跑道过渡-离场
        second_proc.pop(1)  # 因为第二个程序第一个点一般是IF 先不管限制取舍的情况
        for iLoc in range(len(first_proc) - 1, 0, -1):
            second_proc.insert(1, first_proc[iLoc])
    elif pattern == 2:  # 进近 进近过渡-进近 / 进近过渡-进近复飞
        for iLoc in range(1, len(first_proc)):
            second_proc.insert(iLoc, first_proc[iLoc])
    elif pattern == 3:  # 进近 进近-复飞
        second_proc.extend(first_proc[1:])
    else:
        printf("程序黏合剂形参错误", 1)


def get_proc_name(proc: List[str]) -> str:
    """
    返回一个程序的名称
    :param proc: 程序
    :return: 程序名
    """
    global iFile
    allow_char = string.ascii_uppercase + string.digits
    # 离场
    if (procedure_info(proc, 1) == 2) or (procedure_info(proc, 1) == 3):
        header = proc[0].split(',')[3]
        if header.count('-') == 1:  # 正常情况
            header = empty(header, 5)
            sep_loc = header.index('-')
            l_loc = sep_loc - 1
            r_loc = sep_loc + 1
            waypoint_name = ''
            waypoint_id = ''
            while (r_loc <= len(header) - 1) and (header[r_loc] in allow_char):
                waypoint_id += header[r_loc]
                r_loc += 1
            while header[l_loc] in allow_char:
                waypoint_name = header[l_loc] + waypoint_name
                l_loc -= 1
            if iFile[:4] == "ZPDQ":  # HE,04,06,RWY06 进场 NP900-NP508
                return waypoint_id
            else:
                return waypoint_name[:6 - len(waypoint_id)] + waypoint_id
        elif ("失效" in header) or ("EO" in header):
            for iAlfa in ('A', 'B', 'C'):
                if iAlfa in header:
                    return "EO" + procedure_info(proc, 2) + iAlfa
            else:
                return "EO" + procedure_info(proc, 2)
        elif len(header.split()) == 3:
            if len(header.split()[2]) > 6:
                printf("离场程序:>{}< 名称过长".format(header), 1)
            return header.split()[2]
        else:
            printf("异常离场程序名 {} {}".format(header, iFile), 1)
    # 进场
    if procedure_info(proc, 1) == 4:
        header = proc[0].split(',')[3]
        if header.count('-') == 1:  # 正常情况
            header = empty(header, 5)
            sep_loc = header.index('-')
            l_loc = sep_loc - 1
            r_loc = sep_loc + 1
            waypoint_name = ''
            waypoint_id = ''
            while (r_loc <= len(header) - 1) and (header[r_loc] in allow_char):
                waypoint_id += header[r_loc]
                r_loc += 1
            while header[l_loc] in allow_char:
                waypoint_name = header[l_loc] + waypoint_name
                l_loc -= 1
            if iFile[:4] == "ZUNP":  # HE,04,06,RWY06 进场 NP900-NP508
                return waypoint_name
            elif iFile[:4] == "ZPDQ":
                return waypoint_id
            else:
                return waypoint_name[:6 - len(waypoint_id)] + waypoint_id
        elif len(header.split()) == 3:
            if '.' in header:
                temp_name = header[header.index('.') + 1:].replace('-', '')  # OS-89A.IUO-92A
                if len(temp_name) > 6:
                    printf("离场程序:>{}< 名称过长".format(header), 1)
                return temp_name
            if len(header.split()[2]) > 6:
                printf("离场程序:>{}< 名称过长".format(header), 1)
            return header.split()[2]
        else:
            printf("异常进场程序名 {} {}".format(header, iFile), 1)


def change_code(encode: str, loc: int, char: str, replace: bool = True) -> str:
    """
    修改字符串对应位置上的字符
    :param encode: 字符串
    :param loc: 位置
    :param char: 字符
    :param replace: 假如原有位置不为空的话, 是否替换
    :return: 修改后的字符串
    """
    encode = list(encode)
    if replace:
        encode[loc] = char
    return ''.join(encode)


def description_code(procedure: List[str], cat: int):
    """
    对程序进行编码
    :param procedure: 程序
    :param cat: 1进离场
    """
    # 很奇怪 这里没有编码Y 但ZWKN的EO30A的HM还是有Y (虽然这个code好像不是太重要
    code = "    "
    if cat == 1:
        for iPointLoc in range(1, len(procedure)):
            if iPointLoc != len(procedure) - 1:
                if procedure[iPointLoc][:2] not in ("CA", "VA"):  # CA VA没这个code
                    code = change_code(code, 0, 'E')
                else:
                    procedure[iPointLoc] += ", "
            else:  # CA VA 应该不在终止符范围内
                code = change_code(code, 0, 'E')
                code = change_code(code, 1, 'E')
            if procedure[iPointLoc][:2] in ("HF", "HM"):
                code = change_code(code, 3, 'H')
            procedure[iPointLoc] += (',' + code)
    else:
        printf("5.17类型代码出错", 1)


def departure_process(procedures: List[List[str]], runway: list):
    """
    将离场程序按跑道展开，然后拼起来
    :param procedures: 离场程序03 离场过渡程序02
    :param hold_point: 等待程序 有一个HF要进行编码
    :param runway: 跑道
    :return: 修改过后的离场程序
    """
    for iProcLoc in range(len(procedures)):
        procedures[iProcLoc] = [empty(each, 2) for each in procedures[iProcLoc]]
    # 校验跑道
    for i_proc in procedures:
        proc_rwy = procedure_info(i_proc, 2)  # 16L/17L
        proc_rwy = proc_rwy.split('/') if '/' in proc_rwy else [proc_rwy]  # ["16L", "17L"]
        for i_read_runway in proc_rwy:  # 16L
            if i_read_runway not in runway:
                print('-----\n')
                print(i_proc)
                printf("{}跑道{}不匹配: {}".format(iFile[:4], i_read_runway, runway), 1)
    # 多跑道展开
    multi_runway = []
    for i_pro_loc in range(len(procedures)):
        temp_proc = procedures[i_pro_loc].copy()  # ['HE,03,35L/35R,RWY35L/R 离场 SUR-91D\n', 'IF,PD501, ,250, ,-1,-
        temp_head = temp_proc[0].split(',')  # ['HE', '03', '35L/35R', 'RWY35L/R 离场 SUR-91D\n']
        temp_rwy = temp_head[2].split('/')  # ['35L', '35R']
        if len(temp_rwy) > 1:
            multi_runway.append(i_pro_loc)
            for i_rwy in temp_rwy:
                temp_head[2] = i_rwy
                temp_proc[0] = ','.join(temp_head)
                procedures.append(temp_proc.copy())
    # 删除多跑道程序
    for i_multi_loc in range(len(multi_runway) - 1, -1, -1):
        procedures.pop(multi_runway[i_multi_loc])
    # 合并过渡段
    trans_proc_loc_list = []
    for iProcLoc in range(len(procedures)):  # 先假设这是过渡程序
        trans_proc = procedures[iProcLoc]
        if procedure_info(trans_proc, 1) == 2:  # 如果这是过渡段
            trans_proc_loc_list.append(iProcLoc)
            trans_end = get_waypoint(trans_proc, False)  # 过渡段终止点

            for jProcLoc in range(len(procedures)):
                if iProcLoc == jProcLoc:
                    continue
                common_proc = procedures[jProcLoc]  # 先假设他是一个正常程序
                common_start = get_waypoint(common_proc, True)
                if common_start == trans_end:
                    procedure_combine(trans_proc, common_proc, 1)
    trans_proc_loc_list.sort(reverse=True)
    for i_tans_proc in trans_proc_loc_list:
        procedures.pop(i_tans_proc)
    # 提取程序名称
    for iPocLoc in range(len(procedures)):
        procedures[iPocLoc][0] += (',' + get_proc_name(procedures[iPocLoc]))
    # 5.17 Waypoint Description Code (DESC CODE)
    for iProc in procedures:
        description_code(iProc, 1)


def arrival_process(procedures: List[List[str]], runway: list):
    """
    将离场程序按跑道展开，然后拼起来
    :param procedures: 离场程序03 离场过渡程序02
    :param hold_point: 等待程序 有一个HF要进行编码
    :param runway: 跑道
    :return: 修改过后的进场程序
    """
    for iProcLoc in range(len(procedures)):
        procedures[iProcLoc] = [empty(each, 2) for each in procedures[iProcLoc]]
    # 校验跑道
    for i_proc in procedures:
        proc_rwy = procedure_info(i_proc, 2)  # 16L/17L
        proc_rwy = proc_rwy.replace("//", '/')  # 没有害处的 (
        proc_rwy = proc_rwy.split('/') if '/' in proc_rwy else [proc_rwy]  # ["16L", "17L"]
        for i_read_runway in proc_rwy:  # 16L
            if i_read_runway not in runway:
                print('-----\n')
                print(i_proc)
                printf("{}跑道{}不匹配: {}".format(iFile[:4], i_read_runway, runway), 1)
    # 多跑道展开
    multi_runway = []
    for i_pro_loc in range(len(procedures)):
        temp_proc = procedures[i_pro_loc].copy()  # ['HE,03,35L/35R,RWY35L/R 离场 SUR-91D\n', 'IF,PD501, ,250, ,-1,-
        temp_head = temp_proc[0].split(',')  # ['HE', '03', '35L/35R', 'RWY35L/R 离场 SUR-91D\n']
        temp_rwy = temp_head[2].split('/')  # ['35L', '35R']
        if len(temp_rwy) > 1:
            multi_runway.append(i_pro_loc)
            for i_rwy in temp_rwy:
                temp_head[2] = i_rwy
                temp_proc[0] = ','.join(temp_head)
                procedures.append(temp_proc.copy())
    # 删除多跑道程序
    for i_multi_loc in range(len(multi_runway) - 1, -1, -1):
        procedures.pop(multi_runway[i_multi_loc])
    # 提取程序名称
    for iPocLoc in range(len(procedures)):
        procedures[iPocLoc][0] += (',' + get_proc_name(procedures[iPocLoc]))
    # 5.17 Waypoint Description Code (DESC CODE)
    for iProc in procedures:
        description_code(iProc, 1)


def approach_process(procedures: List[List[str]], runway: list) -> str:
    """
    独立的处理程序，因为进近比较复杂
    基于相同跑道的程序放在一起
    :param procedures: 进近过渡01 进近06 等待00 进近复飞05 复飞07
    :param hold_point: 复飞等待点
    :param runway: 跑道
    :return: 修改过后的进近程序
    """

    # 进近处理规则杂谈
    # 1. 过渡程序是可以信任的 他们绝对是进近过渡程序
    # 2. 复飞等待程序可能是复飞等待程序
    # 3. 等待程序一定是等待程序
    # 4. 你是程序员 用手拿着电脑 用手触摸键盘 的人
    # 5. 没有标题同时含有进近复飞等待

    def combine_trans_app(trans: List[str], app: List[str]):
        """合并进近和过渡"""
        for iWptLoc in range(1, len(trans)):
            app.insert(iWptLoc, trans[iWptLoc])

    def redirect(procs: List[List[str]]):
        """重定向等待和复飞程序"""
        for iProLoc in range(len(procs)):
            if procedure_info(procs[iProLoc], 1) == 1:  # 过渡程序没问题
                continue
            if procs[iProLoc][1].startswith("HM"):  # 第一个点就是HM的话,肯定就是等待程序
                header = procs[iProLoc][0].split(',')
                header[1] = "00"
                procs[iProLoc][0] = ','.join(header)
                continue
            if (procedure_info(procs[iProLoc], 1) == 0) and ("复飞" in procs[iProLoc][0]):
                header = procs[iProLoc][0].split(',')
                header[1] = "07"
                procs[iProLoc][0] = ','.join(header)
                continue
            if procedure_info(procs[iProLoc], 1) == 0:
                printf("这里怎么还有等待", 1)

    def combine_app_ga(app: List[str], ga: List[str]):
        """合并进近和复飞"""
        for iGaLoc in range(1, len(ga)):
            app.append(ga[iGaLoc])

    global iFile
    redirect(procedures)
    # 位置-跑道 ['01', '01', '01', '19', '19']
    runway_ident = [procedure_info(i, 2) for i in procedures]
    # 校验跑道
    runway_ident_set = set(runway_ident)
    for iRunway in runway_ident_set:
        i_runway = iRunway.replace("//", '/')
        i_runway = i_runway.split('/')
        for single_runway in i_runway:
            if single_runway not in runway:  # 可能存在等待程序没有标明跑道
                printf("{}:runway disagree!\n   {} -> {}".format(iFile[:4], single_runway, str(runway)), 2)
    # 顺序-长度 {0:[0,3,"01"], 1:[3,2,"19"]} 计数器:[起始,长度,跑道]
    runways = dict()
    proc_timer = 0
    proc_loc = 0
    last_runway = None
    for each in runway_ident:  # 好困 不想写 写到十.45好了
        if last_runway is None:
            last_runway = each
            runways[proc_timer] = [proc_loc, 1, each]
            proc_loc += 1
            continue
        if each == last_runway:
            runways[proc_timer][1] += 1
        else:
            last_runway = each
            proc_timer += 1
            runways[proc_timer] = [proc_loc, 1, each]
        proc_loc += 1
    # 开始取程序 只合并一个record里面的 HM点可以去其他record里面找
    for iKey in runways.keys():
        record = procedures[runways[iKey][0]:runways[iKey][0] + runways[iKey][1]]
        # 拿出一个进近6 / 进近复飞5
        for iProc in record:
            if (procedure_info(iProc, 1) != 6) and (procedure_info(iProc, 1) != 5):
                continue
            start_point = procedure_info(iProc, 5)[0]
            # 进近/进近复飞 寻找 进近过渡
            for jProc in record:
                if procedure_info(jProc, 1) != 1:
                    continue
                end_loc = procedure_info(jProc, 5)[1]
                if start_point == end_loc:
                    combine_trans_app(jProc, iProc)
            # 进近 寻找 复飞
            if procedure_info(iProc, 1) == 6:
                i_proc_loc = record.index(iProc)
                for jProcLoc in range(i_proc_loc, len(record)):
                    if procedure_info(record[jProcLoc], 1) == 7:
                        combine_app_ga(iProc, record[jProcLoc])
                        break
                else:
                    printf("未找到复飞段 -> {}\n{}".format(iFile[:4], iProc), 2)
            # 寻找等待 (这里可能还有点问题)
            has_find = False
            last_waypoint = procedure_info(iProc, 5)[1]
            if iProc[-1].startswith("HM"):
                has_find = True
            for iHold in procedures:
                if has_find:
                    break
                if procedure_info(iHold, 1) != 0:
                    continue
                proc_runway = procedure_info(iProc, 2)
                hold_runway = procedure_info(iProc, 2)
                if (proc_runway not in hold_runway) and (hold_runway != "-1"):  # 睡完觉起来把这个加了 好像感觉又没必要
                    continue
                for iWptLoc in range(1, len(iHold)):
                    hold_waypoint = iHold[iWptLoc].split(',')[1]
                    if last_waypoint == hold_waypoint:
                        iProc.append(iHold[iWptLoc])
                        has_find = True
                        break
    # 删除一些不需要的东西
    for iProcLoc in range(len(procedures)):
        temp_proc = procedures[iProcLoc]
        temp_proc = [empty(i, 2) + ",INOP" for i in temp_proc]
        procedures[iProcLoc] = temp_proc
    procedures = [i for i in procedures if procedure_info(i, 1) in (5, 6)]
    # 编码
    appr_text = []
    for iProc in procedures:
        # 先把东西扔过去 回来再改
        rough_encode = database_encode(iProc)
        rough_encode = rough_encode.split('\n')
        # 确定IF点 下滑道 位置
        if_fix = []
        faf_loc, mapt_loc = -1, -1
        for iLineLoc in range(2, len(rough_encode)):
            i_line = rough_encode[iLineLoc].split(',')
            if i_line[3] == "IF":
                if_fix.append(iLineLoc)
            vnav = i_line[9]
            if not empty(vnav, 4):
                mapt_loc = iLineLoc
            if mapt_loc == -1:
                faf_loc = iLineLoc
        if mapt_loc == -1:
            faf_loc = -1
        # 对每一个过渡段 describe 编码
        for iIfLoc in range(len(if_fix) - 1):
            start_loc = if_fix[iIfLoc]
            end_loc = if_fix[iIfLoc + 1]
            for iWptLoc in range(start_loc, end_loc):  # 过渡只有IF TF RF
                temp_proc = rough_encode[iWptLoc].split(',')
                # if temp_proc[3] not in ("IF", "TF", "RF"):
                #     printf("{}进近过渡航点类型错误\n{}".format(iFile[:4], rough_encode[iWptLoc]), 1)
                if iWptLoc == end_loc - 1:
                    temp_proc[11] = "EE B"  # B标识中间进近
                elif iWptLoc == start_loc:
                    temp_proc[11] = "E  A"  # A标识起始进近
                else:
                    temp_proc[11] = "E   "
                if temp_proc[12] == '1':
                    temp_proc[11] = change_code(temp_proc[11], 1, 'Y', False)
                rough_encode[iWptLoc] = ','.join(temp_proc)
        # 对主进近段编码 顺便修改MAP点高度限制
        for iLoc in range(if_fix[-1], len(rough_encode)):
            temp_proc = rough_encode[iLoc].split(',')
            if iLoc == faf_loc:
                temp_proc[11] = "E  F"  # F代表Published Final Approach Fix
            elif iLoc == mapt_loc:
                if temp_proc[4] == "RW" + procedure_info(iProc, 2):  # 规避了RW04C的问题
                    temp_proc[11] = "GY M"
                    temp_proc[4] = ' '
                else:
                    temp_proc[11] = "EY M"
                temp_proc[8] = "MAP"
            elif iLoc == mapt_loc + 1:
                if temp_proc[3] in ("CA", "VA"):
                    temp_proc[11] = "  M "  # 不知道这里对不对
                else:
                    temp_proc[11] = "E M "
            elif temp_proc[3] in ("CA", "VA"):
                temp_proc[11] = "    "
            elif iLoc == len(rough_encode) - 1:
                if temp_proc[3] == "HM":
                    temp_proc[11] = "EE H"
                else:
                    temp_proc[11] = "EE  "
            else:
                temp_proc[11] = "E   "
            if temp_proc[12] == '1':
                temp_proc[11] = change_code(temp_proc[11], 1, 'Y', False)
            rough_encode[iLoc] = ','.join(temp_proc)
        # 修改Type和Transition
        proc_type = proc_trans = ''
        for iLoc in range(2, len(rough_encode)):
            temp_proc = rough_encode[iLoc].split(',')
            if iLoc in if_fix:
                proc_type = 'A'
                proc_trans = temp_proc[4]
                if if_fix.index(iLoc) == len(if_fix) - 1:
                    proc_type = 'R'
                    proc_trans = ' '
            temp_proc[1] = proc_type
            temp_proc[2] = proc_trans
            rough_encode[iLoc] = ','.join(temp_proc)
        # 修正ZUAL和ZUDR的名称
        appr_text.append('\n'.join(rough_encode))
    return "\n---\n".join(appr_text) + "\n---\n"


def database_encode(procedure: List[str]) -> str:
    """
    编码为数据库接受格式
    :param procedure:
    :return:
    """

    def alt_encode(low: str, high: str) -> str:
        """编码高度"""
        low = int(low)
        high = int(high)
        if (low == high) and (high == -1):
            return ' '
        elif low == high:
            return '0' * (5 - len(str(low))) + str(low)
        else:
            temp_str = ''
            if high != -1:
                temp_str += ((5 - len(str(high))) * '0' + str(high) + 'B')
            if low != -1:
                temp_str += ((5 - len(str(low))) * '0' + str(low) + 'A')
            return temp_str

    # (0)类型 航点 (2)飞越 航向 (4)转向 高度L (6)高度H 速度 (8)下滑道 中心点 (10)半径 性能 (12)描述
    global procCount, iFile
    proc_type = procedure_info(procedure, 1)
    single_proc = []
    simple_name = ''
    if proc_type == 3:
        single_proc.append("{},{}".format("Departure", procedure[-1].split(',')[1]))
    elif proc_type == 4:
        single_proc.append("{},{}".format("Arrival", procedure[1].split(',')[1]))
    elif (proc_type == 5) or (proc_type == 6):
        simple_name = "R{}-{}".format(procedure_info(procedure, 2), procedure_info(procedure, 3).upper())
        if len(simple_name) > 5:
            simple_name = simple_name.replace('-', '')
        if procedure_info(procedure, 3) == '':
            simple_name = simple_name.replace('-', '')
        single_proc.append("{},{}".format("Approach", simple_name))
    procCount += 1
    # 程序全名 和 简称 和 机场 和 跑道
    if (proc_type == 3) or (proc_type == 4):
        complex_name = procedure[0].split(',')[4]
        simple_name = procedure[0].split(',')[4]
        single_proc.append("{},{},{},{}".format(complex_name, simple_name, iFile[:4], procedure[0].split(',')[2]))
    elif (proc_type == 5) or (proc_type == 6):
        full_name = "{} {} {}".format(simple_name, "RNAV", procedure_info(procedure, 2))
        single_proc.append("{},{},{},{}".format(full_name, simple_name, iFile[:4], procedure[0].split(',')[2]))
    else:
        printf("程序名称 类型错误", 1)
    # 单航点编码
    for eachSegLoc in range(len(procedure)):
        segment = procedure[eachSegLoc].split(',')  # 每一个小航点
        if (segment[0] == "HE") or (segment[0] == "PS"):
            continue
        # 程序编号 0
        db_list = [str(procCount)]
        # 航段类型
        if proc_type == 3:  # 单发0 跑道过渡4 离场5 离场过渡6 (有笨蛋才发现有跑道过渡)
            db_list.append('5')
        elif proc_type == 4:  # 航路过渡4 进场5 进场过渡6
            db_list.append('5')
        elif (proc_type == 5) or (proc_type == 6):
            db_list.append("INOP")
        else:
            printf("航段类型 类型错误", 1)
        # 过渡 2
        if (proc_type == 3) or (proc_type == 4):
            db_list.append("RW" + procedure[0].split(',')[2])
        elif (proc_type == 5) or (proc_type == 6):
            db_list.append("INOP")
        else:
            printf("航段类型 类型错误", 1)
        # 航段类型
        db_list.append(segment[0])
        # 航点 4
        db_list.append(segment[1])
        # 转向
        db_list.append(segment[4])
        # 航向 6
        db_list.append(segment[3])
        # 距离
        if segment[0] in ("HF", "HM"):
            segment[10] = '4'
        elif segment[0] == "RF":
            segment[10] = ' '
        db_list.append(segment[10])  # 注意 芝士距离 但用的是半径 艹 hmmm... Fenix 好像可以不编码这个
        # 高度 8
        db_list.append(alt_encode(segment[5], segment[6]))
        # 下滑道
        db_list.append(segment[8])
        # 中心点 10
        db_list.append(segment[9])
        # 描述
        db_list.append(segment[12])
        # 飞跃 12
        db_list.append('1' if segment[2] == '1' else '0')
        if db_list[-1] == '1':
            db_list[-2] = change_code(db_list[-2], 1, 'Y')
        # 速度
        db_list.append(segment[7])
        single_proc.append(','.join(db_list))
    return '\n'.join(single_proc)


# 重写了read_procedure和approach_process 采取了分区的理念
init(autoreset=True)
procCount = 0
inputFolder = r"F:\PDF初提取"
outputFolder = r"F:\PDF初提取"
csvFolder = r"D:\naip\input"
fileList = os.listdir(inputFolder)
information = get_info(csvFolder, "数据库")
information[1]["ZULS"] = ["10L", "10R", "28L", "28R"]
information[1]["ZBXT"] = ["17", "35"]
information[1]["ZUPL"] = ["15", "33"]
information[1]["ZWTN"] = ["11L", "11R","29L","29R"]
for iFile in fileList:
    if "encode" not in iFile:
        continue
    # 先将程序分类
    departure, arrival, approach = read_procedure(os.path.join(inputFolder, iFile))
    # 然后分批处理
    runway_list = information[1][iFile[:4]]
    runway_list = [empty(i, 5) for i in runway_list]
    departure_process(departure, runway_list)
    arrival_process(arrival, runway_list)

    sid_text = ''
    for singleSID in departure:
        sid_text += (database_encode(singleSID) + "\n---\n")
    star_text = ''
    for singleSTAR in arrival:
        star_text += (database_encode(singleSTAR) + "\n---\n")
    appr_text = approach_process(approach, runway_list)

    outFile = open(os.path.join(outputFolder, iFile[:4] + "_db.txt"), 'w', encoding="utf-8")
    outFile.write(sid_text)
    outFile.write(star_text)
    outFile.write(appr_text)
    outFile.close()
