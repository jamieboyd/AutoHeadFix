raspivid -o - -t 0 -hf -w 640 -h 480 -fps 25 | cvlc -vv stream:///dev/stdin --sout '#rtp{sdp=rtsp://:8554}' :demux=h264
