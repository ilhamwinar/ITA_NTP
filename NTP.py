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
from requests.exceptions import HTTPError
import time
import base64
import subprocess

#INISIALISASI ENDPOINT
# ipendpoint = '127.0.0.1' #103.145.177.171
# portendpoint = '8200' #8844
ipendpoint_local="127.0.0.1:8200"
ipendpoint_prod="175.10.1.14:8310"

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

# FUNGSI FILESTREAM
def open_ffmpeg_stream_process(idstream):
    args = (f"ffmpeg -re -stream_loop -1 -f rawvideo -pix_fmt bgr24 -s 640x480 -r 15 -i pipe:0 -pix_fmt yuv420p -b:v 1M -hide_banner -loglevel error -f rtsp rtsp://localhost:8554/ntp/stream/{idstream}"
    ).split()
    # args = ("ffmpeg -re -stream_loop -1 -f rawvideo -pix_fmt bgr24 -s 640x480 -i pipe:0 -pix_fmt yuv420p  -c:v libx264 -b:v 1M -c:a aac -b:a 160k -f rtsp rtsp://localhost:8554/mystream").split()
    return subprocess.Popen(args, stdin=subprocess.PIPE)

# FUNGSI UPDATE CONFIG KE API PUSAT
def update_config(id_cctv,location,address,rtsp,is_active):
    url = 'http://'+ipendpoint_prod+'/set_config_ntp'
    try :
        headers = {"Content-Type": "application/x-www-form-urlencoded"} 
        myobj = {
            "location": location,
            "address": address,
            "rtsp": rtsp,
            "is_active": is_active,
            "stream_hls": f"rtsp://{address}:8554/ntp/stream/{id_cctv}",
            "filestream": f"/hls/ntp/{id_cctv}/index.m3u8"
        }
        response = requests.put(url, headers=headers, data=myobj)
        write_log(location, "SUCESSED UPDATE DATA IS ACTIVE")

    except ValueError as e:
        write_log(location, f"Error: {e}")
        write_log(location, "Send Data - Internal Server Error")
        time.sleep(180)
        exit()

## ARGUMENT PARSER PARAMETER
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--location", type=str,required=True,
	help="location")

args = vars(ap.parse_args())
location = args["location"]

## connect to db local
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

try:
    url_get_config =f'http://{ipendpoint_local}/get_ntp_config'
    response = requests.post(url_get_config, data=m,headers={'Content-Type': m.content_type}).json()
    response_code=response["status"]
except:
    response_code=500
    pass

##--------------------------------------------------------------------------------------------------##
if response_code==200:
    write_log(location,"SUCCESSED GET DATA TO API INTAN SERVER ")
    input_titik= response["id_cctv"]
    input_titik=str(input_titik)
    RTSP_CCTV=response["rtsp"]
    DELAY_DETECTION=response["delay"]
    DELAY_DETECTION=int(DELAY_DETECTION)
    masking=response["masking"]
    img_masking=str(response["masking"])
    endpoint=response["endpoint"]
    model=response["model"]
    latitude=response['latitude']
    longitude=response['longitude']
    region_id=response["region_id"]
    ruas_id=response["ruas_id"]
    address=response["address"]
    write_log(location,"SUCCESSED PARSING DATA AND GET FROM INTAN SERVER") 

elif response_code==404:
    write_log_error(location,"DATA NOT FOUND AT INTAN SERVER ")
    time.sleep(180)
    exit()

elif response_code==500:
    try:
        query = "SELECT id_cctv,rtsp,delay,masking,endpoint,model,latitude,longitude,region_id,ruas_id,address FROM ntp_config WHERE location = %s;"
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        cursor.execute(query, (location,))
        result_query = cursor.fetchall()    
        write_log(location,"OUTPUT QUERY RESULT: "+str(result_query)) 
        input_titik=result_query[0][0]
        input_titik=str(input_titik)
        RTSP_CCTV=result_query[0][1]
        DELAY_DETECTION=result_query[0][2]
        DELAY_DETECTION=int(DELAY_DETECTION)
        masking=result_query[0][3]
        img_masking=str(result_query[0][3])
        endpoint=result_query[0][4]
        model=result_query[0][5]
        latitude=result_query[0][6]
        longitude=result_query[0][7]
        region_id=result_query[0][8]
        ruas_id=result_query[0][9]
        address=result_query[0][10]
        write_log(location,"SUCCESSED PARSING DATA AND GET FROM DB LOCAL SERVER") 
        cnx.close()
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

## UPDATE IS_ACTIVE 0 UNTUK STARTING
try:
    update_config(input_titik,location,address,RTSP_CCTV,"0")
    write_log(location, f"BERHASIL UPDATE IS ACTIVE 0 SAAT PROGRAM STARTING ")
except ValueError as e:
    write_log_error(location, f"Error update is_active 0 and {e}")
    pass

##--------------------------------------------------------------------------------------------------

def play_sound():
    global endpoint
    write_log(location,"START TO VOICE OUTPUT NTP")
    try:
        r = requests.get(url = endpoint)
        write_log(location,"SUCCESSED TO VOICE OUTPUT NTP")
        data = r.json()
        pesan=data['status']
        write_log(location,"SUCCESSED TO VOICE OUTPUT NTP")
    except:
        write_log(location,"NOT CONNETED RASPBERRY PI")
        pass


def post_to_dev(id_cctv,url_image,url_video,class_detection,detection_object,waktu_deteksi):
    url = 'http://'+ipendpoint_prod+'/api/create-event/ntp'
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
        write_log(location,"BERHASIL SEND TO DEV: "+str(response))
    except ValueError as e:
        write_log(lokasi_data, f"Error: {e}")
        write_log_error(location,"Send Data - Internal Server Error")

def send_data_local(pathimg, lokasi_data, url_image, url_video, class_object, deteksi_object, waktu_object, latitude, longitude, region_id, ruas_id):
    url = f'http://{ipendpoint_local}/create_event_ntp'
    try :
        # with open(pathimg, 'rb') as f:
        #     img64 = base64.b64encode(f.read())
        img64=pathimg
        headers = {"Content-Type": "application/x-www-form-urlencoded"} 
        myobj = {
            "base64_event": img64,
            "location": lokasi_data,
            "url_image": url_image,
            "url_video": url_video,
            "class_object": class_object,
            "deteksi_object": deteksi_object,
            "waktu_object": waktu_object,
            "latitude": str(latitude),  
            "longitude": str(longitude),
            "region_id": str(region_id), 
            "ruas_id": str(ruas_id)
        }
        response = requests.post(url, headers=headers, data=myobj)
        write_log(lokasi_data, "RESPONSE DARI SEND DATA LOCAL: " +str(response))

    except ValueError as e:
        write_log(lokasi_data, f"Error: {e}")
        write_log(lokasi_data, "Send Data - Internal Server Error")

def masking_img(rtsp,img_masking,tipe_ai,id_cctv,location):
    url = f'http://{ipendpoint_local}/masking'

    try:
        headers = {"Content-Type": "application/x-www-form-urlencoded"} 
        myobj = {
            "rtsp": rtsp,
            "masking": img_masking,
            "tipe_ai": tipe_ai,
            "id_cctv": id_cctv,
            "location": location
        }
        response = requests.post(url, headers=headers, data=myobj)
        write_log(location, "RESPONSE DARI API MASKING: " +str(response))

    except ValueError as e:
        write_log(location, f"Error: {e}")
        write_log(location, "Send Data - Internal Server Error")

def frame_to_base64(frame, format='.jpg'):
    retval, buffer = cv2.imencode(format, frame)
    if retval:
        jpg_as_text = base64.b64encode(buffer)
        return jpg_as_text.decode('utf-8')
    else:
        return None

## -----------------------------------------MAIN PROGRAM -------------------------------------------------

flag_is_active=0

#FFMPEG PROCESSED OPEN
ffmpeg_process = open_ffmpeg_stream_process(input_titik)

sebelum_minute = None

if __name__ == '__main__':
        temp_id=0
        temp_id_bis=0
        flag=1
        flag_bis=1

        ## Inisialisasi cctv
        cap = cv2.VideoCapture(RTSP_CCTV)
        cur_dir = os.getcwd()
        model=YOLO(model)
        get_fps = True
        get_fps_bis = True

        #GANTI CLASS
        bus=1 
        person=0

        write_log(location,"START PROGRAM NAIK TURUN PENUMPANG V3.3 FROM MASKING, API AND HLS")

        if flag_is_active == 0 and cap.isOpened():
            try:
                update_config(input_titik,location,address,RTSP_CCTV,"1")
                write_log(location, f"BERHASIL UPDATE IS ACTIVE 1 DAN STREAM HLS SAAT PROGRAM STARTING ")
            except ValueError as e:
                write_log_error(location, f"Error update is_active 1 and {e}")
                pass

        flag_is_active == 1

        while cap.isOpened():

            success, frame_main = cap.read()
            # Program Run every 15 minutesS

            if success:   
                now = datetime.now()
                now_minute = now.minute
                if sebelum_minute is None or (now_minute % 5 == 0 and now_minute != sebelum_minute):
                    write_log(location, f"PROGRAM RUNNING SETIAP 5 MENIT {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    base64_pict_masking = frame_to_base64(frame_main)
                    #write_log(location,str(base64_pict_masking))
                    masking_img(base64_pict_masking,img_masking,"2",input_titik, location)
                    sebelum_minute = now_minute
                    
                ## COPY FRAME UNTUK STREAMING    
                #frame_main=frame_main.copy()
                masking_frame=frame_main.copy()
                #frame_dataset=frame_main1.copy()
                frame_main2=frame_main.copy()      

                ## Resize File save to 640,480 to make video
                #save_vid=frame_main.copy()
                #cv2.resize(save_vid, (640, 480), interpolation = cv2.INTER_LINEAR)

                ## masking
                MaskCoord=np.array((masking))
                try:
                    cv2.fillPoly(masking_frame, pts=[MaskCoord], color=(0, 0, 0))
                except:
                    write_log_error(location,"TIDAK ADA MASKING")
                    pass
                
                ## mode max detection banyak
                results = model.track(masking_frame, persist=True, conf=0.5 , classes=[bus,person], verbose=False, agnostic_nms=False)
                
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

                        frame_main = cv2.rectangle(frame_main, (int(xyxy[0][0]), int(xyxy[0][1])), (int(xyxy[0][2]), int(xyxy[0][3])), (255,255,255), 1)
                        frame_main = cv2.putText(frame_main,str(conf)+" - "+str(name_clas),(int(xyxy[0][0]), int(xyxy[0][1]) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)

                        frame_kotak = cv2.rectangle(frame_main2, (int(xyxy[0][0]), int(xyxy[0][1])), (int(xyxy[0][2]), int(xyxy[0][3])), (255,255,255), 1)
                        frame_kotak = cv2.putText(frame_kotak,str(conf)+" - "+str(name_clas),(int(xyxy[0][0]), int(xyxy[0][1]) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)

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
                            #waktu_deteksi = datetime.now().strftime("%d%m%Y_%H_%M_%S")
                            # Format the datetime
                            formatted_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

                            # #save pict
                            # dir_pict_org=str(cur_dir)+"/image/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            # #cv2.imwrite(dir_pict_org, frame_main)
                            # cv2.imwrite(dir_pict_org, frame_kotak)

                            # ##save pict storage
                            # dirpathlog = f"image_storage/{input_titik}/{waktufile}"
                            # os.makedirs(dirpathlog, exist_ok=True)
                            # dir_pict_org=str(cur_dir)+"/"+dirpathlog+"/IMG"+"_"+input_titik+"_"+file_name+".jpg"

                            # #cv2.imwrite(dir_pict_org, masking_frame)
                            # cv2.imwrite(dir_pict_org, frame_dataset)
                            # write_log(location,"PICTURE BIS CAPTURED")

                            # ## directory gambar
                            dir_pict_org="/image/IMG"+"_"+str(input_titik)+"_"+file_name+".jpg"

                            ## directory video
                            dir_vid_org="/video/VID"+"_"+str(input_titik)+"_"+file_name+".webm"

                            #POST TO DEV
                            # try:
                            #     post_to_dev(location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,formatted_datetime)
                            # except:
                            #     write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO DEV SERVER")
                            #     break

                            #POST TO DB LOCAL
                            try:
                                write_log(location,"START INSERT MYSQL TO NTP EVENT LOCAL SERVER")
                                base64_pict = frame_to_base64(frame_kotak)
                                send_data_local(base64_pict,location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,file_name,latitude,longitude,region_id,ruas_id)
                                write_log(location,"END TO INSERT MYSQL TO NTP EVENT LOCAL SERVER")
                            except ValueError as e:
                                write_log(lokasi_data, f"Error: {e}")
                                write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO LOCAL SERVER")
                                pass

                        if int(time.time() - start_time_bis) > DELAY_DETECTION:
                            flag_bis=1
                            #temp_id_bis=0
                            get_fps_bis = True
                            
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
                            #sound_thread = threading.Thread(target=play_sound)
                            #sound_thread.start()     

                            flag=0
                            start_time = time.time()
                            class_deteksi="orang"

                            ## PROSES INSERT TO DATABASE & Format the datetime
                            file_name = datetime.now().strftime("%d%m%Y_%H:%M:%S")
                            waktufile = datetime.now().strftime("%d%m%Y")
                            #waktu_deteksi = datetime.now().strftime("%d%m%Y_%H_%M_%S")
                            formatted_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

                            #save pict
                            # dir_pict_org=str(cur_dir)+"/image/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            # #cv2.imwrite(dir_pict_org, frame_main)
                            # cv2.imwrite(dir_pict_org, frame_kotak)

                            # ##save pict folder
                            # dirpathlog = f"image_storage/{input_titik}/{waktufile}"
                            # os.makedirs(dirpathlog, exist_ok=True)
                            # dir_pict_org=str(cur_dir)+"/"+dirpathlog+"/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                            
                            # #cv2.imwrite(dir_pict_org, masking_frame)
                            # cv2.imwrite(dir_pict_org, frame_dataset)
                            # write_log(location,"PICTURE ORANG CAPTURED")
                            
                            # ## directory gambar
                            dir_pict_org="/image/IMG"+"_"+str(input_titik)+"_"+file_name+".jpg"

                            ## directory video
                            dir_vid_org="/video/VID"+"_"+str(input_titik)+"_"+file_name+".webm"

                            #POST TO DEV
                            # try:
                            #     post_to_dev(location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,formatted_datetime)
                            # except:
                            #     write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO DEV SERVER")
                            #     break

                            #POST TO DB LOCAL
                            try:
                                write_log(location,"START INSERT MYSQL TO NTP EVENT LOCAL SERVER")
                                #base64_pict=str(cur_dir)+"/image/IMG"+"_"+input_titik+"_"+file_name+".jpg"
                                base64_pict = frame_to_base64(frame_kotak)
                                send_data_local(base64_pict,location,dir_pict_org,dir_vid_org,class_deteksi,ntp_count,file_name,latitude,longitude,region_id,ruas_id)
                                write_log(location,"END TO INSERT MYSQL TO NTP EVENT LOCAL SERVER")
                            except ValueError as e:
                                write_log(lokasi_data, f"Error: {e}")
                                write_log_error(location,"NOT CONNECT AND FAILED TO INSERT TO LOCAL SERVER")
                                pass

                            write_log(location,"END TO INSERT MYSQL TO NTP EVENT LOCAL SERVER")

                        if int(time.time() - start_time) > DELAY_DETECTION:
                            flag=1
                            #temp_id=0
                            get_fps = True
                            
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
                            # fps = cap.get(cv2.CAP_PROP_FPS)
                            # h, w, c = save_vid.shape

                            dir_vid_org="./"+dirvidlog+"/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"

                            ## bener
                            # vid_writer = cv2.VideoWriter(dir_vid_org, cv2.VideoWriter_fourcc('D','I','V','X'), fps, (w, h))
                            # write_log(location,"GET RECORDING FRAME ORANG")
                            
                        ## save vid output
                        # try:
                        #     vid_writer.write(save_vid)
                        # except:
                        #     write_log_error(location,"FAILED GET RECORDING FRAME ORANG")
                        #     pass

                        if int(time.time() - start_time) == DELAY_DETECTION:
                            flag=1
                            # vid_writer.release()

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
                            # fps = cap.get(cv2.CAP_PROP_FPS)
                            # h, w, c = save_vid.shape
                            
                            dir_vid_org="./"+dirvidlog+"/VID"+"_"+str(input_titik)+"_"+file_name+".mp4"
                            write_log(location,dir_vid_org)

                            ## bener
                            # vid_writer_bis = cv2.VideoWriter(dir_vid_org, cv2.VideoWriter_fourcc('D','I','V','X'), fps, (w, h))
                            # write_log(location,"GET RECORDING FRAME BIS")

                        ## output.write(frame)
                        # try:
                        #     vid_writer_bis.write(save_vid)
                        # except:
                        #     write_log_error(input_titik,"FAILED GET RECORDING FRAME BIS")
                        #     pass

                        if int(time.time() - start_time_bis) == DELAY_DETECTION:
                            flag_bis=1
                            # vid_writer_bis.release()
                            get_fps_bis = True

                            write_log(location,"END PROCESS RECORDING FRAME BIS")
                            write_log(location,"FLAG BIS SUDAH MENJADI 1 KEMBALI")

                except:
                    pass

                # BROADCAST TO HLS SERVICE
                frame_main = cv2.resize(frame_main, (640, 480))
                ffmpeg_process.stdin.write(frame_main.astype(np.uint8).tobytes())

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if not success:
                write_log_error(location,"FRAME 1 ERROR CANNOT GET FRAME")
                write_log_error(location,"PYTHON CRASHED")
                pid = os.getpid()
                write_log_error(location,"PID: "+str(pid))
                break

        #KILL OPENCV
        cap.release()
        cv2.destroyAllWindows()
        #KILL FFMPEG
        ffmpeg_process.stdin.close()
        ffmpeg_process.kill()

        ## UPDATE IS_ACTIVE 0 UNTUK STARTING
        try:
            update_config(input_titik,location,address,RTSP_CCTV,"0")
            write_log(location, f"BERHASIL UPDATE IS ACTIVE 0 SAAT PROGRAM STARTING ")
        except ValueError as e:
            write_log_error(location, f"Error update is_active 0 and {e}")
            pass

        try:
            write_log_error(location,"FORCED CLOSE APP")
            os.kill(pid, 9)
            write_log_error(location,"PID KILL: "+str(pid))
        except:
            pid = os.getpid()
            write_log_error(location,"PID: "+str(pid))
            os.kill(pid, 9)
            write_log_error(location,"PID KILL: "+str(pid))
        
