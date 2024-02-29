import sqlite3
import os
import sys
import glob
import pandas as pd
import handle as hd
import DatabaseFunctions as dbf

# debug模式切换
# 0是忽略输出日志并且不打印
# 1是输出到屏幕
# 2是输出到指定文件
# 3是混合输出

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\terminals", "")

project_path = code_path.replace("\\programs", "")

DEBUG_PRINT_FLAG = 0

EXCEPTION_LINE_FILE = project_path + "\\error\\Terminal_exception.txt"

approach = project_path + "\\error\\Terminal_Approach.txt"

# 白名单\黑名单\绿名单
White_List = []
Black_List = []
Green_List = []

# 标识符
Flag = True

# 路径列表指定
ZXXX_path = project_path + "\\output"  # 航路点数据文件的绝对路径
lunatic_path = ZXXX_path + "\\lunatic.txt"
prefix = ZXXX_path + '\\'
original_txt_file_list = glob.glob(os.path.join(ZXXX_path, 'Z*_db.txt'))
name_list = []
for original_txt_file in original_txt_file_list:
    name = (original_txt_file.split('\\')[len(original_txt_file.split('\\')) - 1]).replace('_db.txt', '')
    name_list.append(name)
list_process = hd.process_list(name_list, White_List, Black_List)
txt_file_list = []
for name in list_process:
    txt_file_list.append(prefix + name + "_db.txt")
processed_file_list = []

db3_path = project_path + "\\input\\raw.db3"

# 数据库的连接
con = sqlite3.connect(db3_path)
cur = con.cursor()


def exception_print(thing):
    with open(EXCEPTION_LINE_FILE, 'a') as EXCEPTION_FILE:
        EXCEPTION_FILE.write(str(thing) + '\n\n')


with open(EXCEPTION_LINE_FILE, 'w') as fe:
    fe.write('')
with open(approach, 'w') as a_f:
    a_f.write('')

# 依次获取txt文件
for file_path in txt_file_list:
    with (open(file_path, 'r') as file):

        # 获取txt文件的名称并判断是否在白名单
        # 文件名为File_Chars
        # 第一个是获取要处理的文件名列表
        ap_flag = 0
        process_flag = 0
        File_Chars = file.name.split('\\')[len(file.name.split('\\')) - 1]
        File_Chars = File_Chars.replace('_db.txt', '')
        if File_Chars in list_process:
            process_flag = 1
        all_file_num = len(txt_file_list)
        processed_file_num = len(processed_file_list)
        print(f"{File_Chars} {str(processed_file_num)} / {str(all_file_num)} \n")

        if process_flag:

            # 读文件看是否为空，为空就跳过
            all_datas = file.read()
            judge1 = all_datas.replace(' ', '')
            judge2 = judge1.replace('\n', '')
            with open(prefix + File_Chars + '_waypoint.txt', 'r') as wf:
                judge3 = wf.read()
            if len(judge2) == 0 or len(judge3) == 0:
                continue

            # 读取所有数据并按照‘---’来分成每个段落
            # paragraph_process_flag代表着如何处理段落，当为1时，该文件所有段落均盲目处理，为0时，需要针对情况进行判断
            paragraph_process_flag = 0
            paragraphs = all_datas.split('---\n')
            try:
                paragraphs.remove('\n')
                paragraphs.remove('')
            except:
                pass

            # 开始判断是否能在Terminals表格中的ICAO中找到
            results = dbf.search_in(cur, "Terminals", ['ID', 'Proc', 'Name'], {'ICAO': File_Chars})

            # 记录表格
            record_list = []

            if results is None:
                paragraph_process_flag = 1
            elif File_Chars in Green_List:
                paragraph_process_flag = 1

            if paragraph_process_flag == 0:
                for result in results:
                    try:
                        #
                        record = hd.process_record(cur, result, Flag)[0][0]
                        if record not in record_list:
                            record_list.append(record)
                    except TypeError:
                        exception_print(f'ICAO: {File_Chars}\n'
                                        f'exception: No data.\n'
                                        f"Original datas:\n"
                                        f"{str(result)}")

            if not paragraphs:
                continue
            # 挑选需要使用的段落
            # ppf = 1时 直接把所有段落读入
            process_paragraphs = []
            if paragraph_process_flag == 1:
                process_paragraphs = all_datas.split('---\n')
                try:
                    process_paragraphs.remove('\n')
                except:
                    pass
                if process_paragraphs[len(process_paragraphs) - 1] == '':
                    process_paragraphs.pop(-1)

            # ppf = 0时 对比段落的标识符
            elif paragraph_process_flag == 0:
                mid_process_paragraphs = all_datas.split('---\n')
                if mid_process_paragraphs[len(mid_process_paragraphs) - 1] == '':
                    mid_process_paragraphs.pop(-1)
                try:
                    mid_process_paragraphs.remove('\n')
                except:
                    pass
                for mid_process_paragraph in mid_process_paragraphs:
                    lines = mid_process_paragraph.split('\n')
                    words_in_line0 = lines[0].split(',')
                    remark = words_in_line0[1]
                    if remark not in record_list:
                        process_paragraphs.append(mid_process_paragraph)

            # 读取每一个待处理段落
            for process_paragraph in process_paragraphs:
                lines = process_paragraph.split('\n')
                words_in_line0 = lines[0].split(',')
                paragraph_type = words_in_line0[0]
                if paragraph_type == 'Approach':
                    ap_flag = 1
                words_in_line1 = lines[1].split(',')
                full_name = words_in_line1[0]
                name = words_in_line1[1]
                icao = words_in_line1[2]
                rwy = words_in_line1[3]
                terminal_id = dbf.get_id(cur, "Terminals") + 1
                airport_id = dbf.search_in(cur, "Airports", ["ID"], {"ICAO": icao})[0][0]
                proc_type = {'Arrival': 1, 'Departure': 2, 'Approach': 3}
                try:
                    rwy_id = dbf.search_in(cur, "Runways", ["ID"], {"AirportID": airport_id, "Ident": rwy})[0][0]
                except TypeError:
                    exception_print('ICAO: ' + icao + '\n' +
                                    'exception: empty Runway.')

                # 插入到表格Terminals中
                try:
                    data_list = [terminal_id, airport_id, proc_type[paragraph_type],
                                 icao, full_name, name, rwy, rwy_id, 'NULL']
                    dbf.insert_into(cur, "Terminals", data_list)

                except Exception as e:
                    error_message = str(e)

                # 读取waypoint.txt
                txt_read = pd.read_csv(prefix + File_Chars + '_waypoint.txt', sep=' ', header=None)
                lunatic_read = pd.read_csv(lunatic_path, sep=' ', header=None)

                # 开始处理第三行之后的数据
                length = len(lines)
                for i in range(2, length):
                    line = lines[i]
                    if line == '':
                        continue
                    legs_id = dbf.get_id(cur, 'TerminalLegs') + 1
                    words = line.split(',')
                    type_code = words[1]
                    transition = words[2]
                    track_code = words[3]
                    wpt_ident = words[4]
                    wpt_id = ''
                    wpt_lat = ''
                    wpt_lon = ''
                    wpt_turn_dir = words[5]
                    nav_id = ''
                    nav_lat = ''
                    nav_lon = ''
                    nav_bear = ''
                    nav_dist = ''
                    course = words[6]
                    distance = words[7]
                    alt = words[8]
                    vnav = words[9]
                    center_ident = words[10]
                    center_id = ''
                    center_lat = ''
                    center_lon = ''
                    wpt_desc_code = words[11]
                    is_fly_over = words[12]
                    speed_limit = words[13]
                    speed_limit_desc = ''

                    center_flag = 1
                    wpt_flag = 1

                    if wpt_ident == '' or wpt_ident == ' ':
                        wpt_flag = 0

                    if center_ident == '' or center_ident == ' ':
                        center_flag = 0

                    if speed_limit != '' and speed_limit != ' ':
                        speed_limit_desc = 'B'

                    # 先在icao_db.找，0代表发现找不到
                    if wpt_flag == 0:
                        pass
                    # 先在icao_db.找，1代表找到了
                    else:
                        try:
                            # 获取wpt_id的lat和lon
                            df_data_read = txt_read[txt_read[0] == wpt_ident].to_dict()
                            wpt_lat_l = list(df_data_read[1].values())
                            wpt_lon_l = list(df_data_read[2].values())
                            if len(wpt_lat_l) == 0:
                                df_lunatic_read = lunatic_read[lunatic_read[0] == wpt_ident].to_dict()
                                wpt_lat = list(df_lunatic_read[1].values())[0]
                                wpt_lon = list(df_lunatic_read[2].values())[0]
                            else:
                                wpt_lat = wpt_lat_l[0]
                                wpt_lon = wpt_lon_l[0]

                        except IndexError:
                            # 越界说明waypoint里不存在这样的数据

                            exception_print(f'ICAO: {icao}\n'
                                            f'Way point Ident: {wpt_ident}\n'
                                            f"exception:in _waypoint.txt and lunatic.txt it doesn't exist.\n"
                                            f"Original information: \n"
                                            f"{line}")

                            exception_print('ICAO: ' + icao + '\n' +
                                            'Waypoint Ident: ' + wpt_ident + '\n' +
                                            "exception: in _waypoint.txt and lunatic.txt it doesn't exist\n" +
                                            ' \n' + line)
                        except Exception as e:
                            error_message = str(e)
                            # 未知情况
                            exception_print(f'ICAO: {icao}\n'
                                            f'Waypoint Ident: {wpt_ident}\n'
                                            f"exception:Python exception:\n"
                                            f"{error_message}\n"
                                            f"Original information: \n"
                                            f"{line}")

                        try:
                            wpt_datas = dbf.search_in(cur, 'Waypoints', ['ID', 'Latitude', 'Longtitude'],
                                                      {'Ident': wpt_ident})
                            found_flag = 0
                            for wpt_data in wpt_datas:
                                if -0.4 < wpt_data[1] - wpt_lat < 0.4 and -0.4 < wpt_data[2] - wpt_lon < 0.4:
                                    wpt_id = wpt_data[0]
                                    found_flag = 1
                                    break

                            if found_flag == 0:
                                exception_print(f'ICAO: {icao}\n'
                                                f'Waypoint Ident: {wpt_ident}\n'
                                                f"exception:in database not exist data : \n"
                                                f"{wpt_ident} {str(wpt_lat)} {str(wpt_lon)}\n"
                                                f"Original information: \n"
                                                f"{line}")

                        except TypeError:
                            # None不可迭代，即上述data直接不存在。
                            exception_print(f'ICAO: {icao}\n'
                                            f'Waypoint Ident: {wpt_ident}\n'
                                            f"exception:in database not exist data : \n"
                                            f"{wpt_ident} {str(wpt_lat)} {str(wpt_lon)}\n"
                                            f"Original information: \n"
                                            f"{line}")

                        except Exception as e:
                            error_message = str(e)
                            # 未知情况
                            exception_print(f'ICAO: {icao}\n'
                                            f'Waypoint Ident: {wpt_ident}\n'
                                            f"exception:Python exception:\n"
                                            f"{error_message}\n"
                                            f"Original information: \n"
                                            f"{line}")

                    if center_flag == 0:
                        pass
                    else:
                        try:
                            # 获取center_id和lat和lon
                            df_center_read = txt_read[txt_read[0] == center_ident].to_dict()
                            center_lat_l = list(df_center_read[1].values())
                            center_lon_l = list(df_center_read[2].values())
                            if len(center_lat_l) == 0:
                                df_lunatic_read = lunatic_read[lunatic_read[0] == center_ident].to_dict()
                                center_lat = list(df_lunatic_read[1].values())[0]
                                center_lon = list(df_lunatic_read[2].values())[0]
                            else:
                                center_lat = center_lat_l[0]
                                center_lon = center_lon_l[0]

                        except IndexError:
                            # 越界说明waypoint里不存在这样的数据

                            exception_print(f'ICAO: {icao}\n'
                                            f'Center point Ident: {center_ident}\n'
                                            f"exception:in _waypoint.txt and lunatic.txt it doesn't exist.\n"
                                            f"Original information: \n"
                                            f"{line}")


                        except Exception as e:
                            error_message = str(e)
                            # 未知情况
                            exception_print(f'ICAO: {icao}\n'
                                            f'Waypoint Ident: {center_ident}\n'
                                            f"exception:Python exception:\n"
                                            f"{error_message}\n"
                                            f"Original information: \n"
                                            f"{line}")

                        try:
                            center_datas = dbf.search_in(cur, 'Waypoints', ['ID', 'Latitude', 'Longtitude'],
                                                         {'Ident': center_ident})
                            found_flag = 0
                            for center_data in center_datas:
                                if -0.4 < center_data[1] - center_lat < 0.4 and -0.4 < center_data[
                                    2] - center_lon < 0.4:
                                    center_id = center_data[0]
                                    found_flag = 1
                                    break

                            if found_flag == 0:
                                exception_print(f'ICAO: {icao}\n'
                                                f'Center point Ident: {center_ident}\n'
                                                f"exception:in database not exist data : \n"
                                                f"{center_ident} {str(center_lat)} {str(center_lon)}\n"
                                                f"Original information: \n"
                                                f"{line}")

                        except TypeError:
                            # None不可迭代，即上述data直接不存在。
                            exception_print(f'ICAO: {icao}\n'
                                            f'Center point Ident: {center_ident}\n'
                                            f"exception:in database not exist data : \n"
                                            f"{center_ident} {str(center_lat)} {str(center_lon)}\n"
                                            f"Original information: \n"
                                            f"{line}")

                        except Exception as e:
                            error_message = str(e)
                            # 未知情况

                            exception_print(f'ICAO: {icao}\n'
                                            f'Waypoint Ident: {center_ident}\n'
                                            f"exception:Python exception:\n"
                                            f"{error_message}\n"
                                            f"Original information: \n"
                                            f"{line}")


                    leg_data_list = [legs_id, terminal_id, type_code,
                                     transition, track_code, wpt_id, wpt_lat,
                                     wpt_lon, wpt_turn_dir, nav_id,
                                     nav_lat, nav_lon, nav_bear,
                                     nav_dist, course, distance,
                                     alt, vnav, center_id,
                                     center_lat, center_lon, wpt_desc_code]

                    ex_data_list = [legs_id, is_fly_over, speed_limit, speed_limit_desc]

                    try:
                        dbf.insert_into(cur, 'TerminalLegs', leg_data_list)

                    except Exception as e:
                        error_message = str(e)

                    try:
                        dbf.insert_into(cur, 'TerminalLegsEx', ex_data_list)

                    except Exception as e:
                        error_message = str(e)

        else:
            pass

        processed_file_list.append(File_Chars)

        if ap_flag == 0:
            with open(approach, 'a') as ap_file:
                ap_file.write(f'{File_Chars}\n')

con.commit()
cur.close()
con.close()

input("\n\tPress any key to cancel.")
