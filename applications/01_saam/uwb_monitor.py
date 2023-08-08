import logging
import sys, os
import multiprocessing
from datetime import datetime
from timeit import default_timer as timer

import lib.uwb_device as uwb_device
import lib.uwb_parser as uwb_parser


LOG_LEVEL = logging.DEBUG
LOGGING_FILENAME = "uwb_monitor"
RESULTS_FILENAME = "results"

try:
    LGTC_ID = sys.argv[1]
    LGTC_ID = LGTC_ID.replace(" ", "")
except:
    print("No device name was given...going with default")
    LGTC_ID = "xy"

LGTC_NAME = "LGTC" + LGTC_ID
RESULTS_FILENAME += ("_" + LGTC_ID + ".txt")
LOGGING_FILENAME += ("_" + LGTC_ID + ".log")

try:
    APP_DUR = int(sys.argv[2])
except:
    print("No app duration was defined...going with default 10 min")
    APP_DUR = 10



logging.basicConfig(format="%(asctime)s [%(levelname)7s]:%(module)15s > %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
log = logging.getLogger("Monitor")
log.setLevel(LOG_LEVEL)   

file = open(RESULTS_FILENAME, mode="a+")
file.write("----------------------------------------------------------------------------------------------- \n")
file.write(" Measurements made on: " + str(datetime.now())+ "\n")
file.write("----------------------------------------------------------------------------------------------- \n")

if __name__ == "__main__" :

    #q_uwb = multiprocessing.JoinableQueue(128)
    q_uwb = multiprocessing.Queue()
    
    log.info('Starting UWB node UART process')
    p_uart = uwb_device.Node(q_uwb, '/dev/ttyS2', 921600, LOG_LEVEL)
    p_uart.start()

    log.info("Starting monitor proccess")
    _start_time = timer()

    _get_id = True


    settings = {'channel': 2, 'prfr': 64, 'datarate': 110, 'plen': 1024, 'pcode': 9,
                'pacsize': 32, 'nssfd': True, 'cir': True, 'sfdto': 1057, 'rfpow': 50}




    ###############################################################3
    log.info("Sending SETUP settings")
    p_uart.sendSettings(settings)
    while(True):
        try:
            if not q_uwb.empty():
                line = q_uwb.get()
                if 0 <= response[1].find(b'AT+SETUP:OK'):
                    log.info("AT+SETUP:OK")
                    break
        except:
            log.debug("Exception in SETUP")
            pass
    ###############################################################
    log.info("Sending START command")
    p_uart.sendSTART()
    while(True):
        try:
            if not q_uwb.empty():
                line = q_uwb.get()
                if 0 <= response[1].find(b'AT+START:OK'):
                    log.info("AT+START:OK")
                    break
                else:
                    p_uart.sendSTART()
        except:
            log.debug("Exception in START")
            pass
    ###############################################################


    while(True):
        
        try:
            # Get line from the serial process
            if not q_uwb.empty():
                line = q_uwb.get()
                file.write("[" + str(datetime.now().time())+"] > ")
                file.write(line)
                file.write("\n")

                frame = uwb_parser.parse(line)
                log.info(frame.type())

                if(len(line) > 2):
                    if(line[0] == "I" and line[1] == "D"):
                        _get_id = False
                
                #if (frame.type() == "ActiveDevices"):
                #    file.write("Devices table: ")
                #    for d in frame.devices():
                #        file.write(d)

        except Exception as e:
            log.exception("Exception --> probably empty Queue")
            pass

        # Temp solution for time measuring
        if((timer() - _start_time) > (APP_DUR * 60) ):
            log.info("Application time (" + str(APP_DUR) + ") elapsed ...")
            break

        if _get_id:
            p_uart.sendNodeIDRequest()

    file.close()
    p_uart.close()
    p_uart.terminate()
    p_uart.join()
    log.info("Exiting monitor app!")
