from typing import List
import os
import sys
import pandas as pd

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\runways", "")

project_path = code_path.replace("\\programs", "")

PATH_addon = project_path + '\\input\\runwayAddon.xlsx'

PATH_RWY = project_path + '\\input\\RWY.csv'
PATH_RWY_DIRECTION = project_path + '\\input\\RWY_DIRECTION.csv'

RWY_csv = pd.read_csv(PATH_RWY, encoding='gbk')
RWY_DIRECTION_csv = pd.read_csv(PATH_RWY_DIRECTION, encoding='gbk')


def get_data(airport_code: str, ident: str) -> List[str]:
    if RWY_csv['CODE_AIRPORT'].isin([airport_code]).any():
        information = RWY_csv[RWY_csv['CODE_AIRPORT'] == airport_code]

        for index, element in information.iterrows():
            txt_desig = str(element['TXT_DESIG']).replace(' ','')
            idents = txt_desig.split('/')
            if idents[0] == ident:
                rwy_id = str(element['RWY_ID'])
                val_len = element['VAL_LEN']
                val_wld = element['VAL_WID']
                if RWY_DIRECTION_csv['RWY_ID'].isin([rwy_id]).any():
                    information__ = RWY_DIRECTION_csv[RWY_DIRECTION_csv['RWY_ID'] == rwy_id]

                    for index__, element__ in information__.iterrows():
                        txt_desig__ = str(element__['TXT_DESIG']).replace(' ','')
                        val_true_brg = str(element__['VAL_TRUE_BRG'])
                        if txt_desig__ == idents[0]:
                            val_len = str(round(val_len * 3.28, 0))
                            val_wld = str(round(val_wld * 3.28, 0))
                            return ["'" + ident + "'", val_true_brg, val_len, val_wld]

            elif idents[1] == ident:
                rwy_id = str(element['RWY_ID'])
                val_len = element['VAL_LEN']
                val_wld = element['VAL_WID']
                if RWY_DIRECTION_csv['RWY_ID'].isin([rwy_id]).any():
                    information__ = RWY_DIRECTION_csv[RWY_DIRECTION_csv['RWY_ID'] == rwy_id]

                    for index__, element__ in information__.iterrows():
                        txt_desig__ = str(element__['TXT_DESIG']).replace(' ', '')
                        val_true_brg = str(element__['VAL_TRUE_BRG'])
                        if txt_desig__ == idents[1]:
                            val_len = str(round(val_len * 3.28, 0))
                            val_wld = str(round(val_wld * 3.28, 0))
                            return ["'" + ident + "'", val_true_brg, val_len, val_wld]
