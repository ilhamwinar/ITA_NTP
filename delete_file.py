from pathlib import Path
import datetime as dt
from time import ctime
import mysql.connector
import os


remove_before = dt.datetime.now()-dt.timedelta(days=3) #files older than 10 days
print(remove_before.strftime("%d%m%Y"))
waktufile=remove_before.strftime("%d%m%Y")

## Inisialisasi mysql
try:
    cnx=mysql.connector.connect(
        user="ntp",
        password="@jmt02023",
        host="10.6.105.35",
        database="ntp"
    )

    print("DATABASE CONNECTED TO NTP")
    if cnx.is_connected():
        print("DATABASE CONNECTED TO NTP")
    cursor = cnx.cursor()

except:
    print("DATABASE NOT CONNEDTED TO NTP")

query = "select no_cctv from cctv"
cursor.execute(query)
rows = cursor.fetchall()
for row in rows:
    print(row[0])
    nocctv=str(row[0])
    try:
        sintax="rm -r /home/aicctv/Music/video_mp4/"+ nocctv +"/"+ waktufile
        sintax2="rm -r /home/aicctv/Music/image_storage/"+nocctv +"/"+ waktufile
    except:
        pass
    print(sintax)
    print(sintax2)
    os.system(sintax+";")
    os.system(sintax2+";")








