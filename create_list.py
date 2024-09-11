import os
import requests
import logging
import mysql.connector

delay=20

def make_word(script_path,script_content):
    with open("myscript.sh", "w") as script_path:
        script_path.write(script_content)

def add_newline(script_path,line_to_add):
    try:
        with open(script_path, "a") as script_file:
            script_file.write("\n" + line_to_add)
        print(f"Line has been successfully added to '{script_path}'.")
    except FileNotFoundError:
        print(f"Script '{script_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def delete_word(script_path,word_to_remove):
    try:
        with open(script_path, "r") as script_file:
            lines = script_file.readlines()

        # Remove lines containing the specified text
        modified_lines = [line.replace(word_to_remove, "") for line in lines]

        with open(script_path, "w") as script_file:
            script_file.writelines(modified_lines)

        print(f"Text '{word_to_remove}' has been successfully removed from '{script_path}'.")
    except FileNotFoundError:
        print(f"Script '{script_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_lines_and_following(file_path, target_word, lines_to_delete=5):
    # Read the contents of the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find lines containing the target word and delete them along with the following lines
    modified_lines = []
    skip_next_lines = 0
    for line in lines:
        if target_word in line:
            # Skip this line and the following lines_to_delete lines
            skip_next_lines = lines_to_delete
        elif skip_next_lines > 0:
            # Skip this line
            skip_next_lines -= 1
        else:
            modified_lines.append(line)

    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

    print(f"Lines containing '{target_word}' and the next {lines_to_delete} lines deleted successfully.")

if __name__ == '__main__':
    ## Inisialisasi mysql
    try:
        cnx=mysql.connector.connect(
            user="ntp",
            password="@jmt02023",
            host="10.6.105.35",
            database="ntp"
        )

        logging.info("DATABASE CONNECTED TO NTP")
        if cnx.is_connected():
            logging.info("DATABASE CONNECTED TO NTP")
        cursor = cnx.cursor()

    except:
        logging.info("DATABASE NOT CONNEDTED TO NTP")


    # Execute a SELECT query
    query = "select * from cctv"
    cursor.execute(query)

    # Fetch all the rows as a list of tuples
    rows = cursor.fetchall()

    ## Make file and create header
    try:
        os.remove("./myscript.sh")
    except:
        pass
    os.system("touch myscript.sh")
    header_script = """
#!/bin/bash
#!/usr/bin/env python3

export DISPLAY=:0 #needed if you are running a simple gui app.

cd "$(dirname "$0")"

process=script_ntp
while true
do"""    
    add_newline("myscript.sh",header_script)

    ## Process the data and write to file
    for row in rows:
        print(row)
        print(row[0]) #nomercctv
        print(row[1]) #titikCCTV
        print(row[2]) #IP_CU
        print(row[6]) #RTSP

        delete_word("myscript.sh","sleep 10")
        delete_word("myscript.sh","done")
        delete_word("myscript.sh","exit")

        ## Define Variable
        input_titik = row[1]
        rtsp=row[12] #streaming main
        nocctv=str(row[0])
        masking=row[11]
        endpoint="http://"+row[2]+":8200/status_auto"

        if "@" in rtsp: 
            rtsp2=rtsp.split("@")
            print(rtsp2)
            rtsp=rtsp2[0]
            rtsp2="@"+rtsp2[1]
        elif "@" not in rtsp:
            rtsp=rtsp
            rtsp2="null"

        script_content = """
    if ! ps aux | grep -v grep | grep 'python3 main1_new.py --rtsp {} --rtsp2 {} --delay {} --nocctv {}' > /dev/null
    then #{}
        python3 main1_new.py --rtsp {} --rtsp2 {} --delay {} --nocctv {} --masking "{}" --input_titik {} --endpoint {} &
        sleep 30 #{}
    fi #{}
sleep 10
done
exit
        """.format(rtsp,rtsp2,delay,nocctv,("--nocctv "+str(nocctv)),rtsp,rtsp2,delay,str(nocctv),masking,input_titik,endpoint,("--nocctv "+str(nocctv)),("--nocctv "+str(nocctv)))
        add_newline("myscript.sh",script_content)
            
    os.system("chmod +x myscript.sh;")
    # # Close the cursor and connection
    cursor.close()
    cnx.close()

