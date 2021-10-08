#!/bin/sh /etc/rc.common
#
# Startup/shutdown script for wifood
#
USE_PROCD=1
START=95
PORT=80 
SCRIPT=/usr/bin/wifood

start_service() {
    procd_open_instance
    procd_set_param command $SCRIPT
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
reload_service(){
    stop_service
    start_service
}
stop_service() {
  #Cierra el proceso asociado al puerto del servicio
  kill $(lsof -t -i:$PORT) 2>/dev/null
  return 0
}
shutdown() {
    stop_service
}