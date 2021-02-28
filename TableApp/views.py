from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic

from datetime import datetime, timedelta

import os
import sqlite3
import logging
# Create your views here.


def get_settings(request):
    print(os.listdir(path="."))
    print(os.path.abspath(__file__))

    con = sqlite3.connect("main.db")
    cur = con.cursor()

    table_name = "history"

    try:
        print("Trying")
        cur.execute(f"select * from {table_name}")
    except:
        print("Creating")
        # if does not exist
        logging.info(f"Created new `{table_name}` table")
        cur.execute(f"""CREATE TABLE {table_name} (
            "tg_id" INTEGER, 
            "event" TEXT,
            "time" TEXT
        );""")
    else:
        logging.info(f"There is `{table_name}` table")

    cur.execute(f"""select * from {"history"}""")
    data = cur.fetchall()
    print("DATA FROM VIEWS")
    print(data)

    notes = []
    for i in range(24):
        try:
            print(f"HEERE #{i}")
            from_time = datetime.now() - timedelta(hours=i)

            # date_time_str = '2018-06-29 08:15:27.243860'
            time_str = from_time.strftime("%d-%b-%Y %H")
            # date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
            cur.execute(f"""select * from {"history"} where time like '%{time_str}%'""")
            data = cur.fetchall()
        except:
            logging.warning(f"Error with getting info")
        else:
            notes.append({"time": time_str, "checked_users": []})
            for note in data:
                if notes[-1]["checked_users"].count(note[0]) == 0:
                    notes[-1]["checked_users"].append(note[0])

    time_array = []
    count_users = []
    for i in notes:
        count_users.append(len(i["checked_users"]))
        time_array.append(i["time"])

    cur.close()
    con.close()
    return render(request, 'TableApp/index.html', {
        "notes": zip(count_users, time_array)
     })
