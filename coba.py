import subprocess
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", type=str,required=True,
	help="name of the user")

ap.add_argument("-o", "--output", type=str,required=True,
	help="name of the user")


args = vars(ap.parse_args())

def convert_mp4_to_webm(input_file, output_file):
    # FFmpeg command to convert MP4 to WebM
    cmd = [
        'ffmpeg',
        '-i', input_file,     # Input MP4 file
        '-c:v', 'libvpx',     # Video codec for WebM
        '-b:v', '1M',         # Video bitrate
        '-c:a', 'libvorbis',  # Audio codec for WebM
        '-b:a', '192k',       # Audio bitrate
        output_file           # Output WebM file
    ]

    # Run FFmpeg command
    subprocess.run(cmd)

input_file= args["input"]
output_file= args["output"]
convert_mp4_to_webm(input_file, output_file)
