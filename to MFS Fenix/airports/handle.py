def handle_num(string: str) -> float:
    str_list = list(string)
    str_list.pop(0)
    second_str = str_list.pop(-2) + str_list.pop(-1)
    minute_str = str_list.pop(-2) + str_list.pop(-1)
    angle_str = ''.join(str_list)
    result = round(float(angle_str) + float(minute_str)/60 + float(second_str)/3600, 8)
    return result


def handle_trs(num: int) -> int:
    num *= 3.28
    num0 = num % 100
    num1 = (num // 100) * 100
    if num0 < 50:
        num0 = 0
    else:
        num0 = 100
    num1 += num0
    return int(num1)
