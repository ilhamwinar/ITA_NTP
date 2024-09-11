#!/bin/bash

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install ffmpeg first."
    exit 1
fi

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 input_file.mp4 [output_file.webm]"
    exit 1
fi

# Input file
input_file="$1"

# Output file
output_file="${2:-${input_file%.mp4}.webm}"

# Perform the conversion
ffmpeg -i "$input_file" -c:v libvpx -crf 10 -b:v 1M -c:a libvorbis "$output_file"

echo "Conversion completed: $input_file -> $output_file"
