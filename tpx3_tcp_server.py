"""TCP server of Advacam TimePIX3 device to communicate with SPEC software.

* IS_CONNECTED
* INFO
* CONFIG
* ACQUIRE acq_count acq_time
* IS_RUNNING
* ABORT
* LAST_FRAME
"""

import socketserver
from threading import Thread
#from bl_tcp_server import BLRequestHandler

import sys
import array

PORT = 59876

# dev = pixet.devices()[0]  # get first device
class TPX3RequestHandler(BLRequestHandler):
    """Concrete subclass of an abstract request handler."""

    def process_command(self, cmd, params):
        """Processing command received from client
        """

        global dev
        cmd = cmd.upper()
        if cmd == 'IS_CONNECTED':
            self.send_text_response('OK is_connected {:d}'.format(dev.isConnected()))
        elif cmd == 'INFO':
            self.send_text_response('OK info {} {} {}'.format(dev.width(), dev.height(), dev.dataType()))
        elif cmd == 'CONFIG':
            dev.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)
            self.send_text_response('OK config')
        elif cmd == 'ACQUIRE':
            if len(params) == 2:
                # acquire data without file output
                # this method returns after the acquisition is completed
                errno = dev.doSimpleAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")
                # errno = dev.doSimpleIntegralAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")
                if errno:
                    self.send_text_response('ERROR:{} acquire.'.format(errno))
                else:
                    self.send_text_response('OK acquire')
            else:
                self.send_text_response('ERROR:102 illegal_arguments')
        elif cmd == 'ACQUIRE_NOWAIT':
            if len(params) == 2:
                Thread(target=dev.doSimpleAcquisition, args=(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")).start()
                self.send_text_response('UNKNOWN acquire_nowait')
            else:
                self.send_text_response('ERROR:102 illegal_arguments')
        elif cmd == 'IS_RUNNING':
            self.send_text_response('OK is_running {:d}'.format(dev.isAcquisitionRunning()))
        elif cmd == 'ABORT':
            errno = dev.abortOperation()
            if errno:
                self.send_text_response('ERROR:{} abort'.format(errno))
            else:
                self.send_text_response('OK abort')
        elif cmd == 'LAST_FRAME':
            if not dev.lastAcqFrameRefInc():
                self.send_text_response('ERROR:103 no_last_frame')
            else:
                _, frame_event = dev.lastAcqFrameRefInc().subFrames()
                
                self.send_text_response('OK last_frame int16 {}'.format(frame_event.size()))
                # send binary data
                self.request.sendall(array.array('h', frame_event.data()))
        else:
            self.send_text_response('ERROR:101 unknown_command')


def shutdown_server(server):
    server.shutdown()
    server.server_close()

# kill the server
def exitCallback(value):
    global SERVER
    print("Exit")
    SERVER.server_close()

# when abort pressed stop the server
def onAbort():
    global SERVER
    Thread(target=shutdown_server, args=(SERVER,)).start()
    print("Aborted")


devices = pixet.devicesTpx3()
if len(devices) == 0:
    print("No TPX3 device found. Exit.")
    sys.exit()

dev = devices[0]

# initialize a server.
SERVER = socketserver.ThreadingTCPServer(('', PORT), TPX3RequestHandler)
pixet.registerEvent("Exit", exitCallback, exitCallback)

# set the operation mode EVENT+iTOT
dev.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)

# run the server.
SERVER.serve_forever()
SERVER.server_close()
