"""TCP server that controls an Advacam TimePIX3 device in compliance
with a message from SPEC software.

The following commands are available:

* IS_CONNECTED
* RECONNECT
* INFO
* CONFIG
* ACQUIRE acq_count acq_time [filename]
* ACQUIRE_NOWAIT acq_count acq_time [filename]
* IS_RUNNING
* ABORT
* LAST_FRAME
* KILL : close both Pixet Pro and this server
* QUIT : close this server. (implemented by the parent class)

tcp_server_example.py in Pixet Pro sample script was used as a reference.
"""

import socketserver
from threading import Thread
# from bl_tcp_server import BLRequestHandler

import sys
import os
import os.path
import array

PORT = 59876
DATA_DIR = 'D:\\PIXet Pro'


class TPX3RequestHandler(BLRequestHandler):
    """Concrete subclass of an abstract request handler."""

    def process_command(self, cmd, params):
        """Processing command received from client
        """

        global TPX3
        # tpx3 = pixet.devicesTpx3()[0]

        cmd = cmd.upper()
        if cmd == 'IS_CONNECTED':
            self.send_text_response('OK is_connected {:d}'.format(TPX3.isConnected()))
        elif cmd == 'RECONNECT':
            self.send_text_response('OK reconnect {:d}'.format(TPX3.reconnect()))
        elif cmd == 'INFO':
            self.send_text_response('OK info {} {} {}'.format(TPX3.width(), TPX3.height(), TPX3.dataType()))
        elif cmd == 'CONFIG':
            TPX3.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)
            self.send_text_response('OK config')
        elif cmd == 'ACQUIRE':
            # This command waits until the acquisition is completed.
            if len(params) == 2:
                # acquire data without file output
                errno = TPX3.doSimpleAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")
                # errno = TPX3.doSimpleIntegralAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")
                if errno:
                    self.send_text_response('ERROR:{} acquire'.format(errno))
                else:
                    self.send_text_response('OK acquire')
            elif len(params) == 3:
                # acquire data with file output
                # pixet.PX_FTYPE_AUTODETECT
                errno = TPX3.doSimpleAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_PNG, os.path.join(DATA_DIR, params[2]))
                # errno = TPX3.doSimpleIntegralAcquisition(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")
                if errno:
                    self.send_text_response('ERROR:{} acquire'.format(errno))
                else:
                    self.send_text_response('OK acquire')
            else:
                self.send_text_response('ERROR:102 illegal_arguments')
        elif cmd == 'ACQUIRE_NOWAIT':
            # This command does until the acquisition is completed.
            if len(params) == 2:
                # acquire data without file output
                Thread(target=TPX3.doSimpleAcquisition, args=(int(params[0]), float(params[1]), pixet.PX_FTYPE_NONE, "")).start()
                self.send_text_response('UNKNOWN acquire_nowait')
            elif len(params) == 3:
                # acquire data with file output
                Thread(target=TPX3.doSimpleAcquisition, args=(int(params[0]), float(params[1]), pixet.PX_FTYPE_PNG, os.path.join(DATA_DIR, params[2]))).start()
                self.send_text_response('UNKNOWN acquire_nowait')
            else:
                self.send_text_response('ERROR:102 illegal_arguments')
        elif cmd == 'IS_RUNNING':
            self.send_text_response('OK is_running {:d}'.format(TPX3.isAcquisitionRunning()))
        elif cmd == 'ABORT':
            errno = TPX3.abortOperation()
            if errno:
                self.send_text_response('ERROR:{} abort'.format(errno))
            else:
                self.send_text_response('OK abort')
        elif cmd == 'LAST_FRAME':
            frame = TPX3.lastAcqFrameRefInc()
            if not frame:
                self.send_text_response('ERROR:103 no_last_frame')
            else:
                # subframes[0]: iTOT, subframes[1]: EVENT.
                subframes = frame.subFrames()

                # send header text and binary data
                self.send_text_response('OK last_frame int16 {}'.format(subframes[1].size()))
                self.request.sendall(array.array('h', subframes[1].data()))

                # release the frame
                frame.destroy()
                # gc.collect()
        elif cmd == 'KILL':
            # It looks the server is closed by exitCallback, and so,
            # it is not neccessary to call `shutdown_server` here.
            self.send_text_response('UNKNOWN kill')
            pixet.exitPixet()
        else:
            self.send_text_response('ERROR:101 unknown_command')


# kill the server
def exitCallback(value):
    global SERVER
    print("Exit")
    SERVER.server_close()

# Stop the server when "abort" button is pressed
def onAbort():
    global SERVER

    def abort_server(server):
        server.shutdown()
        server.server_close()

    Thread(target=abort_server, args=(SERVER,)).start()
    print("Aborted")

# main
if __name__ == '__main__':
    devices = pixet.devicesTpx3()
    if len(devices) == 0:
        print("No TPX3 device found. Exit.")
        sys.exit()

    # set the operation mode EVENT+iTOT
    TPX3 = devices[0]
    TPX3.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)
    del devices

    # initialize a server.
    SERVER = socketserver.ThreadingTCPServer(('', PORT), TPX3RequestHandler)
    pixet.registerEvent("Exit", exitCallback, exitCallback)

    # run the server.
    SERVER.serve_forever()

    # close the server after the service is stopped (by server.shutdown() from another thread, for example).
    SERVER.server_close()
