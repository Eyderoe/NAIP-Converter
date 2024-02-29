import sqlite3


def get_freq(path: str, num: int, cursor: sqlite3.Cursor) -> int | None:

    # 打开路径
    with open(path) as file:
        datalines = file.readlines()

        for line in datalines:
            data = line.split()
            val = int(data[4])
            if num == val:
                latitude = float(data[1])
                longtitude = float(data[2])
                name = data[7]
                navaids_query_sentence = ("SELECT `Freq`, `Latitude`, `Longtitude`"
                                          "FROM `Navaids` "
                                          f"WHERE `Ident` = '{name}'")
                cursor.execute(navaids_query_sentence)
                results = cursor.fetchall()

                for result in results:
                    latitude_from_dat = float(result[1])
                    longtitude_from_dat = float(result[2])
                    freq = int(result[0])
                    if -1 < latitude - latitude_from_dat < 1 and -1 < longtitude - longtitude_from_dat < 1:
                        return freq

                return None
