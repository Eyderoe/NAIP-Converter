import sqlite3
import csv

con = sqlite3.connect(r'E:\Python项目\Fenix 数据库\raw.db3')
cur = con.cursor()

sql_Query_1 = ('SELECT '
               '`Terminals`.`ICAO`,'
               '`TerminalLegs`.`TerminalID`,'
               '`Terminals`.`FullName`,'
               '`Terminals`.`Name`,'
               '`Terminals`.`Rwy`,'
               '`TerminalLegs`.`Type`,'
               '`TerminalLegs`.`Transition`,'
               '`TerminalLegs`.`TrackCode`,'
               '`Waypoints`.`Ident`,'
               '`TerminalLegs`.`TurnDir`,'
               '`TerminalLegs`.`NavID`,'
               '`TerminalLegs`.`NavBear`,'
               '`TerminalLegs`.`NavDist`,'
               '`TerminalLegs`.`Course`,'
               '`TerminalLegs`.`Distance`,'
               '`TerminalLegs`.`Alt`,'
               '`TerminalLegs`.`Vnav`,'
               '`TerminalLegs`.`CenterID`,'
               '`TerminalLegs`.`WptDescCode`'
               'FROM `TerminalLegs`'
               'LEFT JOIN `Waypoints` ON `Waypoints`.`ID` = `TerminalLegs`.`WptID`'
               'INNER JOIN `Terminals` ON `Terminals`.`ID` = `TerminalLegs`.`TerminalID`'
               'INNER JOIN `TerminalLegsEx` ON `TerminalLegsEx`.`ID` = `TerminalLegs`.`ID`')

cur.execute(sql_Query_1)

results = cur.fetchall()
header = [i[0] for i in cur.description]

csv_data = [header]
for row in results:
    csv_row = []
    for value in row:
        if isinstance(value, str) and ',' in value:
            value = '"' + value + '"'
        elif value is None:
            value = ''
        csv_row.append(str(value))
    csv_data.append(csv_row)

with open('程序.csv', 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerows(csv_data)

cur.close()  # 关闭游标
con.close()  # 关闭数据库连接
