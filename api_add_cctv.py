from fastapi import FastAPI,Form
import uvicorn
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import sys
from datetime import datetime
import mysql.connector


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"])

#inisialisasi logging
file_handler = logging.FileHandler(filename="./log_server_api.log")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=handlers,
    datefmt="%m/%d/%Y %H:%M:%S",
)
logger = logging.getLogger('LOGGER_NAME')

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

@app.get("/reboot")
async def reboot_pc():
    os.system("reboot")
    return {"message": "berhasil perintah restart service cctv"}


@app.get("/create_cctv")
async def create_cctv():
    os.system("python3 create_list.py;")
    return {"message": "berhasil menambah cctv"}


@app.delete("/delete_cctv")
async def delete_cctv(id_cctv: str = Form()):
    # target_word_to_delete = "--nocctv "+nocctv
    # lines_to_delete = 0
    # delete_lines_and_following('myscript.sh', target_word_to_delete, lines_to_delete)

    try:
        cnx=mysql.connector.connect(
            user="ntp",
            password="@jmt02023",
            host="10.6.105.35",
            database="ntp"
        )

    
        if cnx.is_connected():
            logging.info("DATABASE CONNECTED TO NTP")
        cursor = cnx.cursor()

    except:
        logging.info("DATABASE NOT CONNEDTED TO NTP")

    #logging.info(nocctv)
    table_name = 'cctv_copy1'
    condition_column = 'id'
    condition_value = id_cctv

    delete_query = f"DELETE FROM {table_name} WHERE {condition_column} = %s"

    #logging.info(delete_query)
    cursor.execute(delete_query, (condition_value,))

    # Commit the changes and close the connection
    cnx.commit()
    cursor.close()
    cnx.close()
    return {"message": "berhasil delete cctv"}


def convert_mp4_to_webm(input_vid,output_vid):
    sintax="python3 coba.py --input "+str(input_vid)+" --output "+str(output_vid)
    os.system(sintax+";")

@app.post("/convert_to_webm")
async def convert_vid(id_cctv: str = Form(),waktu:str=Form()):

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
    query = "select no_cctv from cctv where id= "+id_cctv
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        logging.info(row[0])
        nocctv=str(row[0])

    # convert to webm
    logging.info("STARTING TO CONVERT TO webm")
    #logging.info(waktu)
    waktu=waktu.split("-")
    #logging.info(waktu)
    waktu2=waktu[2].split("_")
    #logging.info(waktu2)
    waktu_str=waktu2[0]+waktu[1]+waktu[0]+"_"+waktu2[1]

    #logging.info(waktu_str)

    waktufile = waktu2[0]+waktu[1]+waktu[0]

    #logging.info(waktufile)
    #logging.info(nocctv)

    dirvidlog = f"video_mp4/{nocctv}/{waktufile}"
    #logging.info(dirvidlog)



    #dir_vid_org="./video_mp4/VID_"+str(nocctv)+"_"+str(waktu_str)+".mp4"
    dir_vid_org="./"+dirvidlog+"/VID"+"_"+str(nocctv)+"_"+str(waktu_str)+".mp4"
    logging.info(dir_vid_org)
    dir_vid_org_webm="./video/VID_"+str(nocctv)+"_"+str(waktu_str)+".webm"
    
    logging.info(dir_vid_org)
    logging.info(dir_vid_org_webm)


    try:
        convert_mp4_to_webm(dir_vid_org, dir_vid_org_webm)
        pesan="berhasil convert CCTV"
    except:
        logging.error("ERROR")
        pesan="gagal convert"
        pass

    return {"message": pesan}




if __name__ == "__main__":
    uvicorn.run("api_add_cctv:app",host="0.0.0.0",port=8300,reload=True)