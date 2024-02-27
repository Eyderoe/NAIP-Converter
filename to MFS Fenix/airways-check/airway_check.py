import sqlite3
import DatabaseFunctions as dbf
import handle as hd
import os
import sys
import time

code_path = os.path.abspath(os.path.dirname(os.path.realpath(sys.executable)))

code_path = code_path.replace("\\code\\airways-check", "")

project_path = code_path.replace("\\programs", "")

db3_path = project_path + "\\input\\raw.db3"

check_path = project_path + "\\error\\airway_check.txt"

conn = sqlite3.connect(db3_path)
cur = conn.cursor()

with open(check_path, 'w') as f:
    f.write('')

airway_id_max = dbf.get_id(cur, 'Airways')

print("\n\n")
with open(check_path, 'a') as f:
    progress = 0
    for i in range(airway_id_max):

        if i in range(1, airway_id_max, int(airway_id_max/100)):
            print("\r", end="")
            print(f"\tProgress: {progress}% :", "█" * (progress // 2), end="")
            progress += 1
            sys.stdout.flush()
            time.sleep(0.05)

        airway_ident = dbf.search_in(cur, 'Airways', ['Ident'], {'ID': i + 1})[0][0]
        results_for_same_airway = dbf.search_in(cur, 'AirwayLegs',
                                                ['Waypoint1ID', 'Waypoint2ID', 'IsStart', 'IsEnd'],
                                                {'AirwayID': i + 1})
        if not results_for_same_airway:
            f.write(f'{airway_ident}:\n Empty\n')
            continue
        lines_id_format = hd.get_lines_from_database(results_for_same_airway)
        f.write(f'{airway_ident}:\n')
        if lines_id_format:
            for line_id_format in lines_id_format:
                line_ident_format = []
                for line_id in line_id_format:
                    line_ident = dbf.search_in(cur, 'Waypoints', ['Ident'], {'ID': line_id})[0][0]
                    line_ident_format.append(line_ident)
                f.write(f'{line_ident_format}\n')

input("\n\tPress any key to cancel.")
