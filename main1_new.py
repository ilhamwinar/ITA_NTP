import cv2
from ultralytics import YOLO
import threading
import time
from datetime import datetime
import os
import numpy as np
import requests
import mysql.connector
import sys
import ast
import argparse
from pathlib import Path
from requests_toolbelt import MultipartEncoder

## FUNGSI UNTUK READ LOG
def write_log(lokasi_log, datalog):
    waktulog = datetime.now()
    dirpathlog = f"Log/{lokasi_log}"
    os.makedirs(dirpathlog, exist_ok=True)
    pathlog = f"{waktulog.strftime('%d%m%Y')}.log"
    file_path = Path(f"{dirpathlog}/{pathlog}")
    datalog = "[INFO] - " + datalog
    if not file_path.is_file():
        file_path.write_text(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}\n")
    else :
        fb = open(f"{dirpathlog}/{pathlog}", "a")
        fb.write(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}\n")
        fb.close
    
    print(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}")

def write_log_error(lokasi_log, datalog):
    waktulog = datetime.now()
    dirpathlog = f"Log/{lokasi_log}"
    os.makedirs(dirpathlog, exist_ok=True)
    pathlog = f"{waktulog.strftime('%d%m%Y')}.log"
    file_path = Path(f"{dirpathlog}/{pathlog}")
    datalog = "[ERROR] - " + datalog
    if not file_path.is_file():
        file_path.write_text(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}\n")
    else :
        fb = open(f"{dirpathlog}/{pathlog}", "a")
        fb.write(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}\n")
        fb.close
    
    print(f"{waktulog.strftime('%d-%m-%Y %H:%M:%S')} - {datalog}")



## ARGUMENT PARSER PARAMETER
##--------------------------------------------------------------------------------------------------##

ap = argparse.ArgumentParser()
ap.add_argument("-r", "--location", type=str,required=True,
	help="location")

args = vars(ap.parse_args())
location = args["location"]

####connect to db 
user_db = os.getenv("USER_DB", "aicctv")
password_db = os.getenv("PASSWORD_DB", "Jmt02022!")
host_db  = os.getenv("HOST_DB", "127.0.0.1")
database_db  = os.getenv("DATABASE", "intan")
cur_dir = os.getcwd()

cnx=mysql.connector.connect(
    user=user_db,
    password=password_db,
    host=host_db,
    database=database_db
)

if cnx.is_connected():
    write_log(location,"DATABASE CONNECTED TO LOCAL SERVER")
    cursor = cnx.cursor(buffered=True)
else:
    write_log_error(location,"DATABASE NOT CONNEDTED TO LOCAL SERVER")
    time.sleep(180)
    exit()

##--------------------------------------------------------------------------------------------------##

#GET PARAMETER 
m = MultipartEncoder(fields={'location': str(location)})

# Define the URL for the API endpoint
try:
    url = "http://127.0.0.1:8200/get_motor_config"
    response = requests.post(url, data=m,headers={'Content-Type': m.content_type}).json()
    response_code=response["status"]
except:
    response_code=500
    pass

##--------------------------------------------------------------------------------------------------##
if response_code==200:
    write_log(location,"SUCCESSED GET DATA TO API INTAN SERVER ")
    input_titik= response["id_cctv"]
    RTSP_CCTV=response["rtsp"]
    DELAY_DETECTION=response["delay"]
    DELAY_DETECTION=int(DELAY_DETECTION)
    masking=response["masking"]
    endpoint=response["endpoint"]
    model=response["model"]
    write_log(location,"SUCCESSED PARSING DATA AND GET FROM INTAN SERVER") 

elif response_code==404:
    write_log_error(location,"DATA NOT FOUND AT INTAN SERVER ")
    time.sleep(180)
    exit()

elif response_code==500:
    try:
        query = "SELECT id_cctv,rtsp,delay,masking,endpoint,model FROM ntp_config WHERE location = %s;"
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        cursor.execute(query, (location,))
        result_query = cursor.fetchall()    
        write_log(location,"OUTPUT QUERY RESULT: "+str(result_query)) 

        input_titik=result_query[0][0]
        RTSP_CCTV=result_query[0][1]
        DELAY_DETECTION=result_query[0][2]
        DELAY_DETECTION=int(DELAY_DETECTION)
        masking=result_query[0][3]
        endpoint=result_query[0][4]
        model=result_query[0][5]
        write_log(location,"SUCCESSED PARSING DATA AND GET FROM DB LOCAL SERVER") 
    except:
        write_log_error(location,"FAILED TO GET DATA NTP CONFIG AT LOCAL SERVER ")
        time.sleep(180)
        exit()


# ERROR HANDLING RTSP
if "null" in RTSP_CCTV:
    RTSP_CCTV= RTSP_CCTV

## Masking
try:
    masking = ast.literal_eval(masking)
except (SyntaxError, ValueError) as e:
    print(f"Error: {e}")

##--------------------------------------------------------------------------------------------------

def play_sound():
    global endpoint
    write_log(location,"START TO VOICE OUTPUT NTP")
    try:
        #ENDPOINT=os.getenv("ENDPOINT", "http://172.16.12.114:8200/status_auto")
        r = requests.get(url = endpoint)
        write_log(location,"SUCCESSED TO VOICE OUTPUT NTP")
        data = r.json()
        pesan=data['status']
        write_log(location,"SUCCESSED TO VOICE OUTPUT NTP")
    except:
        write_log(location,"NOT CONNETED RASPBERRY PI")
        pass


def post_to_dev(id_cctv,url_image,url_video,class_detection,detection_object,waktu_deteksi):
    #GET PARAMETER 
    # m = MultipartEncoder(fields={'location': str(location)})

    # # Define the URL for the API endpoint
    # url = "http://127.0.0.1:8200/get_motor_config"
    # response = requests.post(url, data=m,headers={'Content-Type': m.content_type}).json()
    url = 'http://175.10.1.14:8083/api/create-event/ntp'
    id_cctv=str(id_cctv)
    url_image=str(url_image)
    url_video=str(url_video)
    class_detection=str(class_detection)
    detection_object=str(detection_object)
    waktu_deteksi=str(waktu_deteksi)
    try:
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"} 

        # Data form yang ingin dikirim
        form_data = {
            'id_cctv': id_cctv,
            'url_image': url_image,
            'url_video': url_video,
            "class_":class_detection,
            "detection_object":detection_object,
            "waktu_deteksi":waktu_deteksi
        }

        # Mengirim POST request dengan form data
        response = requests.post(url, headers=headers, data=form_data)
        write_log(location,"BERHASIL SEND TO DEV")
    except :
        write_log_error(location,"Send Data - Internal Server Error")

## -----------------------------------------MAIN PROGRAM -------------------------------------------------
sebelum_hour=datetime.now().hour

if __name__ == '__main__':

        temp_id=0
        temp_id_bis=0
        flag=1
        flag_bis=1

        write_log(location,"START PROGRAM NAIK TURUN PENUMPANG V2 FROM API")

        ## Inisialisasi cctv
        cap = cv2.VideoCapture(RTSP_CCTV)
        cur_dir = os.getcwd()

        model=YOLO(model)
        get_fps = True
        get_fps_bis = True

        #GANTI CLASS
        bus=1 
        person=0
        
        while cap.isOpened():
            success, frame_main = cap.read()
            masking_frame=frame_main.copy()
            frame_main2=frame_main.copy()
            frame_dataset=frame_main.copy()

            if success:
                #sound_thread = threading.Thread(target=play_sound)
                now_hour = datetime.now().hour
            
                if now_hour != sebelum_hour:
                    write_log(location,"PROGRAM RUNNING SETIAP JAM "+str(now_hour))
            
                sebelum_hour=now_hour
                
                ## Resize File save to 640,480
                save_vid=frame_main.copy()
                cv2.resize(save_vid, (640, 480), interpolation = cv2.INTER_LINEAR)

                ## masking
                MaskCoord=np.array((masking))
                try:
                    cv2.fillPoly(masking_frame, pts=[MaskCoord], color=(0, 0, 0))
                except:
                    write_log_error(location,"TIDAK ADA MASKING")
                    pass
                
                ## mode max detection banyak
                results = model.track(masking_frame, persist=True, conf=0.5 , classes=[0,5], verbose=False, agnostic_nms=False)
                
                
                if len(results[0].boxes.cls) > 0 :
                    for i in results[0].boxes :
                        xyxy = i.xyxy
                        name_clas = int(i.cls.item())
                        if name_clas == bus:
                            name_clas="Bus"
                        elif name_clas == person:
                            name_clas="Orang"

                        conf = float(i.conf.item())
                        conf = round(conf, 2)
                        frame_kotak = cv2.rectangle(frame_main2, (int(xyxy[0][0]), int(xyxy[0][1])), (int(xyxy[0][2]), int(xyxy[0][3])), (255,255,255), 1)
                        frame_kotak = cv2.putText(frame_kotak,str(conf)+" - "+str(name_clas),(int(xyxy[0][0]), int(xyxy[0][1]) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.15, (255,255,255), 1, cv2.LINE_AA)
                    
                    ## DETEKSI BUS
                    if bus in results[0].boxes.cls.tolist():
                        deteksi_bis=0
                        id_box_bis=results[0].boxes.data.tolist()[0][4]

                        if flag_bis==1 and id_box_bis!= temp_id_bis:
                            write_log(location,"ADA DETEKSI BUS")
                            start_time_bis = time.time()
                            flag_bis=0
                            for i in results[0].boxes.cls.tolist():
                                if i == bus:
                                    deteksi_bis=deteksi_bis+1

                            ntp_count=len(results[0].boxes.cls.tolist())-deteksi_bis
                            
                            ## PROSES INSERT TO DATABASE 
                            class_deteksi="bis"
                            file_name = datetime.now().strftime("%d%m%Y_%H:%M:%S")
                            waktufile = datetime.now().strftime("%d%m%Y")
                            waktu_deteksi = datetime.now().strftime("%d%m%Y_%H_%M_%S")
                            # Format the datetime
                            formatted_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

                            #save pict
                            dir_pict_org=str(cur_dir)+"/image/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            #cv2.imwrite(dir_pict_org, frame_main)
                            cv2.imwrite(dir_pict_org, frame_kotak)

                            ##save pict storage
                            dirpathlog = f"image_storage/{input_titik}/{waktufile}"
                            os.makedirs(dirpathlog, exist_ok=True)
                            dir_pict_org=str(cur_dir)+"/"+dirpathlog+"/IMG"+"_"+input_titik+"_"+file_name+".jpg"

                            #cv2.imwrite(dir_pict_org, masking_frame)
                            cv2.imwrite(dir_pict_org, frame_dataset)
                            write_log(location,"PICTURE BIS CAPTURED")

                            ## directory gambar
                            dir_pict_org="/image/IMG"+"_"+str(input_titik)+"_"+file_name+".jpg"

                            ## directory video
                            dir_vid_org="/video/VID"+"_"+str(input_titik)+"_"+file_name+".webm"

                            ## insert mysql
                            sql_insert="""INSERT INTO ntp_event (id_cctv,url_image,url_video,class,detection_object,waktu_deteksi) VALUES(%s,%s,%s,%s,%s,%s);"""
                            query_insert=(input_titik,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,waktu_deteksi)

                            #POST TO DEV
                            try:
                                post_to_dev(location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,formatted_datetime)
                            except:
                                write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO DEV SERVER")
                                break

                            try:
                                #cursor=cnx.cursor()
                                write_log(location,"START INSERTING TO MOTOR EVENT LOCAL SERVER")
                                cursor.execute(sql_insert,query_insert)
                                cnx.commit()
                                write_log(location,"SUCCESSED INSERTING TO MOTOR EVENT LOCAL SERVER")
                                # cnx.close()
                            except:
                                write_log_error(location,"NOT INSERTED TO MOTOR EVENT LOCAL SERVER")
                                pass
                            
                            write_log(location,"END TO INSERT MYSQL TO MOTOR EVENT LOCAL SERVER")

                        if int(time.time() - start_time_bis) > DELAY_DETECTION:
                            flag_bis=1
                            get_fps_bis = True
                            
                            #write_log(location,"END PROCESS RECORDING FRAME BIS")
                            write_log(location,"FLAG BIS SUDAH MENJADI 1 KEMBALI")

                        temp_id_bis=id_box_bis

                    ## DETEKSI ORANG
                    if person in results[0].boxes.cls.tolist():
                        deteksi_bis=0
                        if bus in results[0].boxes.cls.tolist():
                            for i in results[0].boxes.cls.tolist():
                                if i == bus:
                                    deteksi_bis=deteksi_bis+1

                            ntp_count=len(results[0].boxes.cls.tolist())-deteksi_bis

                        elif bus not in results[0].boxes.cls.tolist():
                            ntp_count=len(results[0].boxes.cls.tolist())


                        id_box=results[0].boxes.data.tolist()[0][4]

                        if id_box!= temp_id and flag==1: 

                            write_log(location,"ADA DETEKSI ORANG")
                            
                            ## play sound untuk mode automatic
                            #sound_thread.start()     

                            flag=0
                            start_time = time.time()
                            class_deteksi="orang"

                            ## PROSES INSERT TO DATABASE & Format the datetime
                            file_name = datetime.now().strftime("%d%m%Y_%H:%M:%S")
                            waktufile = datetime.now().strftime("%d%m%Y")
                            waktu_deteksi = datetime.now().strftime("%d%m%Y_%H_%M_%S")
                            formatted_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

                        

                            #save pict
                            dir_pict_org=str(cur_dir)+"/image/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            #cv2.imwrite(dir_pict_org, frame_main)
                            cv2.imwrite(dir_pict_org, frame_kotak)

                            ##save pict folder
                            dirpathlog = f"image_storage/{input_titik}/{waktufile}"
                            os.makedirs(dirpathlog, exist_ok=True)
                            dir_pict_org=str(cur_dir)+"/"+dirpathlog+"/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            
                            #cv2.imwrite(dir_pict_org, masking_frame)
                            cv2.imwrite(dir_pict_org, frame_dataset)
                            write_log(location,"PICTURE ORANG CAPTURED")
                            
                            ## directory gambar
                            dir_pict_org="/image/IMG"+"_"+str(input_titik)+"_"+file_name+".jpg"

                            ## directory video
                            dir_vid_org="/video/VID"+"_"+str(input_titik)+"_"+file_name+".webm"

                            ## insert mysql
                            sql_insert="""INSERT INTO ntp_event (id_cctv,url_image,url_video,class,detection_object,waktu_deteksi) VALUES(%s,%s,%s,%s,%s,%s);"""
                            query_insert=(input_titik,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,waktu_deteksi)

                            #POST TO DEV
                            try:
                                post_to_dev(location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,formatted_datetime)
                            except:
                                write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO DEV SERVER")
                                break

                            try:
                                #cursor=cnx.cursor()
                                write_log(location,"START INSERTING TO MOTOR EVENT LOCAL SERVER")
                                cursor.execute(sql_insert,query_insert)
                                cnx.commit()
                                write_log(location,"SUCCESSED INSERTING TO MOTOR EVENT LOCAL SERVER")
                                # cnx.close()
                            except:
                                write_log_error(location,"NOT INSERTED TO MOTOR EVENT LOCAL SERVER")
                                pass
                            
                            write_log(location,"END TO INSERT MYSQL TO MOTOR EVENT LOCAL SERVER")


                        if int(time.time() - start_time) > DELAY_DETECTION:
                            flag=1
                            get_fps = True
                            write_log(location,"FLAG ORANG SUDAH MENJADI 1 KEMBALI")

                        temp_id=id_box

                ## RECORDING ORANG
                try:    
                    if flag==0 and int(time.time() - start_time) <= DELAY_DETECTION:
                        if get_fps == True:

                            ## Make folder sesuai waktu
                            waktufile = datetime.now().strftime("%d%m%Y")
                            dirvidlog = f"video_mp4/{input_titik}/{waktufile}"
                            os.makedirs(dirvidlog, exist_ok=True)

                            write_log(location,"STARTING TO CAPTURE PROGRAM FRAME ORANG")
                            get_fps = False

                            ## get fps dan resolusi video bis
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            h, w, c = save_vid.shape
                            
                            ## starting to vid bener
                            #dir_vid_org="./video_mp4/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"

                            dir_vid_org="./"+dirvidlog+"/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"

                            ## bener
                            vid_writer = cv2.VideoWriter(dir_vid_org, cv2.VideoWriter_fourcc('D','I','V','X'), fps, (w, h))
                            write_log(location,dir_vid_org)

                            write_log(location,"GET RECORDING FRAME ORANG")
                            
                        ## save vid output
                        try:
                            vid_writer.write(save_vid)
                        except:
                            write_log_error(input_titik,"FAILED GET RECORDING FRAME ORANG")
                            pass

                        if int(time.time() - start_time) == DELAY_DETECTION:
                            flag=1
                            vid_writer.release()
                            get_fps = True

                            write_log(location,"END PROCESS RECORDING FRAME ORANG")
                            write_log(location,"FLAG ORANG SUDAH MENJADI 1 KEMBALI")
                except:
                    pass

                ## RECORDING BIS
                try:        
                    if flag_bis==0 and int(time.time() - start_time_bis) <= DELAY_DETECTION:
                        if get_fps_bis == True :

                            ## Make folder sesuai waktu
                            waktufile = datetime.now().strftime("%d%m%Y")
                            dirvidlog = f"video_mp4/{input_titik}/{waktufile}"
                            os.makedirs(dirvidlog, exist_ok=True)

                            write_log(location,"STARTING TO CAPTURE PROGRAM FRAME BIS")
                            get_fps_bis = False

                            ## get fps dan resolusi video bis
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            h, w, c = save_vid.shape

                            ## starting to vid bener
                            #dir_vid_org="./video_mp4/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"
                            
                            dir_vid_org="./"+dirvidlog+"/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"
                            write_log(location,dir_vid_org)

                            ## bener
                            vid_writer_bis = cv2.VideoWriter(dir_vid_org, cv2.VideoWriter_fourcc('D','I','V','X'), fps, (w, h))

                            ##try
                            #vid_writer_bis = cv2.VideoWriter(dir_vid_org, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

                            write_log(location,"GET RECORDING FRAME BIS")

                        ## output.write(frame)
                        try:
                            vid_writer_bis.write(save_vid)
                        except:
                            write_log_error(input_titik,"FAILED GET RECORDING FRAME BIS")
                            pass

                        if int(time.time() - start_time_bis) == DELAY_DETECTION:
                            flag_bis=1
                            vid_writer_bis.release()
                            get_fps_bis = True

                            write_log(location,"END PROCESS RECORDING FRAME BIS")
                            write_log(location,"FLAG BIS SUDAH MENJADI 1 KEMBALI")
                except:
                    pass

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if not success:
                write_log_error(location,"FRAME 1 ERROR CANNOT GET FRAME")
                write_log_error(location,"PYTHON CRASHED")
                pid = os.getpid()
                write_log_error(location,"PID: "+str(pid))
                break

        cap.release()
        cv2.destroyAllWindows()
        
        try:
            write_log_error(location,"FORCED CLOSE APP")
            os.kill(pid, 9)
            write_log_error(location,"PID KILL: "+str(pid))
        except:
            pid = os.getpid()
            write_log_error(location,"PID: "+str(pid))
            os.kill(pid, 9)
            write_log_error(location,"PID KILL: "+str(pid))
        
