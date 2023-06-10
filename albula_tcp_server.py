"""Albula TCP server.

Commands available:

* frame [frame_number]
* image frame_index [filename]
* test frame_index [test_index]
* rect frame_index [left top width height]
* limit frame_index [lower_count_limit upper_count_limit]
* count frame_index
* quit

The following code in Command Prompt launches the server 
with its port 10001 and Pilatus server sharing point "W:/".

```
@REM Uncomment below if Anaconda is installed in a user domain
@REM call %HOMEPATH%\Anaconda3\Scripts\activate.bat py27

@REM Uncomment below if Anaconda is installed in the system domain
@REM call %PROGRAMDATA%\Anaconda3\Scripts\activate.bat py27

python albula_tcp_server.py 10001 W:/
```
"""

from __future__ import division, print_function, unicode_literals

import sys
import os
import re
import socket
from socketserver import TCPServer
from bl_tcp_server import BLRequestHandler

albula_base_dir = ''
if (os.name == 'nt'):
    # os.environ['PROGRAMFILES'] indicates the path to "Program Files (x86)" folder if python is 32-bit.
    albula_base_dir = os.path.join(os.environ['PROGRAMFILES'], 'DECTRIS', 'ALBULA', 'ALBULA_3.3.3')
elif (os.name == 'posix'):
    albula_base_dir = '/opt/dectris/albula/4.0'

sys.path.insert(0, os.path.join(albula_base_dir, 'bin'))
sys.path.insert(0, os.path.join(albula_base_dir, 'python'))

import dectris.albula


# constants

ACTIVE_COLOR = (0, 128, 0)
NON_ACTIVE_COLOR = (0, 64, 0)


#  class definision

class AlbulaTCPServer(TCPServer, object):
    """Albula TCP server class.
    """

    def __init__(self, server_address, requestHandlerClass, bind_and_activate=True, base_dir = './', det_num = 0):
        super(AlbulaTCPServer, self).__init__(server_address, requestHandlerClass, bind_and_activate)

        self.main_frame = dectris.albula.openMainFrame(disableClose = True)
        self.base_dir = base_dir
        self.sub_frames = []
        self.images = []
        self.image_paths = []
        self.rects = []
        self.count_limits = []

        self.set_albula_frame_number(det_num)
        
    # def show_subframes(self):
    #     shown_sub_frames = self.main_frame.subFrames()
    #     for i in range(len(self.sub_frames)):
    #         registered_sub_frame = self.sub_frames[i]
    #         if registered_sub_frame is None or registered_sub_frame not in shown_sub_frames:
    #             sub_frame = self.main_frame.openSubFrame()
    #             sub_frame.setActiveColor(*ACTIVE_COLOR)
    #             sub_frame.setNonActiveColor(*NON_ACTIVE_COLOR)
    #             self.sub_frames[i] = sub_frame

    def server_close(self):
        super(AlbulaTCPServer, self).server_close()
        self.close_albula()

    def close_albula(self):
        if self.main_frame is not None:
            self.main_frame.close()
            self.main_frame = None

    def set_albula_frame_number(self, det_num):
        # close all preexisting subframes
        for sub_frame in self.sub_frames:
            sub_frame.close()
        self.sub_frames = []
        self.images = []
        self.image_paths = []
        self.rects = []
        self.count_limits = []

        # create new subframes and register them
        for _ in range(det_num):
            sub_frame = self.main_frame.openSubFrame()
            sub_frame.setActiveColor(*ACTIVE_COLOR)
            sub_frame.setNonActiveColor(*NON_ACTIVE_COLOR)
            self.sub_frames.append(sub_frame)
            self.images.append(None)
            self.image_paths.append(None)
            self.rects.append(None)
            self.count_limits.append({})

    def get_albula_frame_number(self):
        return len(self.sub_frames)

        # dectris_image = dectris.albula.readImage(r"C:\Program Files (x86)\DECTRIS\ALBULA\ALBULA_3.3.0\testData\in16c_010001.cbf")
        # main_frame, sub_frame = dectris.albula.display(dectris_image)

    def show_albula_test_image(self, frame_index, image_index):
        image_path = os.path.join(albula_base_dir, 'testData', 'in16c_{:0>6}.cbf'.format(image_index + 10001))
        return self.set_albula_image_file(frame_index, image_path)

    def set_albula_image_file(self, frame_index, image_path):
        # check if the frame exists
        if frame_index >= len(self.sub_frames):
            return 1

        try:
            image = dectris.albula.readImage(os.path.join(self.base_dir, image_path), -1) # timeout < 0: wait forever
        except dectris.albula.DNoFileAccessException:
            return 2
        # self.sub_frames[frame_index].loadImage(image)

        try:
            self.sub_frames[frame_index].loadImage(image)
            # self.sub_frames[frame_index].loadFile(image_path)
        except dectris.albula.DNoObject:
            sub_frame = self.main_frame.openSubFrame()
            sub_frame.setActiveColor(*ACTIVE_COLOR)
            sub_frame.setNonActiveColor(*NON_ACTIVE_COLOR)
            sub_frame.loadImage(image)
            # sub_frame.loadFile(image_path)
            self.sub_frames[frame_index] = sub_frame

        self.images[frame_index] = image
        self.image_paths[frame_index] = image_path
        return 0

    def get_albula_image_file(self, frame_index = -1):
        if frame_index < 0:
            return self.image_paths
        else:
            return self.image_paths[frame_index]

    def set_albula_rect(self, frame_index, left=-1, top=-1, width=-1, height=-1):
        if left == -1 and top == -1 and width == -1 and height == -1:
            self.rects[frame_index] = None
        else:
            self.rects[frame_index] = dectris.albula.DRect(left, top, width, height)
        return 0

    def get_albula_rect(self, frame_index = -1):
        if frame_index < 0:
            return self.rects
        else:
            rect = self.rects[frame_index]
            if rect == None:
                return None
            else:
                return {'left': rect.left(), 'top': rect.top(), 'width': rect.width(), 'right': rect.height()}

    def set_albula_count_limit(self, frame_index, lower_count_limit, upper_count_limit):
        self.count_limits[frame_index] = { 'lowerCountLimit': lower_count_limit, 'upperCountLimit': upper_count_limit }
        return 0

    def get_albula_count_limit(self, frame_index = -1):
        if frame_index < 0:
            return self.count_limits
        else:
            return self.count_limits[frame_index]

    def get_albula_count(self, frame_index):
        image = self.images[frame_index]
        rect = self.rects[frame_index]
        count_limits = self.count_limits[frame_index]
        return image.mean(rect, **count_limits)


class AlbulaRequestHandler(BLRequestHandler):
    """Concrete subclass of an abstract request handler.
    """

    def process_command(self, cmd, params):
        """Processing command received from client
        """

        cmd = cmd.upper()
        if cmd == 'FRAME':
            if len(params) == 1:
                frame_number = int(params[0])
                self.server.set_albula_frame_number(frame_number)
                self.send_text_response('OK set_frame {}'.format(frame_number))
            elif len(params) == 0:
                frame_number = self.server.get_albula_frame_number()
                self.send_text_response('OK get_frame {}'.format(frame_number))
            else:
                self.send_text_response('ERROR:102 frame illegal_arguments')
        elif cmd == 'TEST':
            if len(params) == 2:
                frame_index = int(params[0])
                image_index = int(params[1])
                errno = self.server.show_albula_test_image(frame_index, image_index)
                if errno:
                    self.send_text_response('ERROR:{} set_test {} {}'.format(errno, frame_index, image_index))
                else:
                    self.send_text_response('OK set_test {} {}'.format(frame_index, image_index))
            elif len(params) == 1:
                frame_index = int(params[0])
                image_path = self.server.get_albula_image_file(frame_index)
                self.send_text_response('OK get_test {} {}'.format(frame_index, image_path))
            else:
                self.send_text_response('ERROR:102 test illegal_arguments')
        elif cmd == 'IMAGE':
            if len(params) > 1:
                frame_index = int(params[0])
                image_path = " ".join(params[1:])
                errno = self.server.set_albula_image_file(frame_index, image_path)
                if errno:
                    self.send_text_response('ERROR:{} set_image {} {}'.format(errno, frame_index, image_path))
                else:
                    self.send_text_response('OK set_image {} {}'.format(frame_index, image_path))
            elif len(params) == 1:
                frame_index = int(params[0])
                image_path = self.server.get_albula_image_file(frame_index)
                self.send_text_response('OK get_image {} {}'.format(frame_index, image_path))
            else:
                self.send_text_response('ERROR:102 image illegal_arguments')
        elif cmd == 'RECT':
            if len(params) == 5:
                frame_index = int(params[0])
                left = int(params[1])
                top = int(params[2])
                width = int(params[3])
                height = int(params[4])
                errno = self.server.set_albula_rect(frame_index, left, top, width, height)
                if errno:
                    self.send_text_response('ERROR:{} set_rect {} {} {} {} {}'.format(errno, frame_index, left, top, width, height))
                else:
                    self.send_text_response('OK set_rect {} {} {} {} {}'.format(frame_index, left, top, width, height))
            elif len(params) == 1:
                frame_index = int(params[0])
                rect = self.server.get_albula_rect(frame_index)
                if rect != None:
                    self.send_text_response('OK get_rect {} {} {} {} {}'.format(frame_index, rect.left, rect.top, rect.width, rect.height))
                else:
                    self.send_text_response('OK get_rect {} {} {} {} {}'.format(frame_index, -1, -1, -1, -1))
            else:
                self.send_text_response('ERROR:102 rect illegal_arguments')
        elif cmd == 'LIMIT':
            if len(params) == 3:
                frame_index = int(params[0])
                lower_limit = float(params[1])
                upper_limit = float(params[2])
                errno = self.server.set_albula_count_limit(frame_index, lower_limit, upper_limit)
                if errno:
                    self.send_text_response('ERROR:{} set_limit {} {} {}'.format(errno, frame_index, lower_limit, upper_limit))
                else:
                    self.send_text_response('OK set_limit {} {} {}'.format(frame_index, lower_limit, upper_limit))
            elif len(params) == 1:
                frame_index = int(params[0])
                count_limit = self.server.get_albula_count_limit(frame_index)
                if (count_limit != None):
                    self.send_text_response('OK get_limit {} {} {}'.format(frame_index, count_limit["lowerCountLimit"], count_limit["upperCountLimit"]))
                else:
                    self.send_text_response('OK get_limit {} {} {}'.format(frame_index, None, None))
            else:
                self.send_text_response('ERROR:102 limit illegal_arguments')
        elif cmd == 'COUNT':
            if len(params) == 1:
                frame_index = int(params[0])
                count = self.server.get_albula_count(frame_index)
                self.send_text_response('OK get_count {} {}'.format(frame_index, count))
            else:
                self.send_text_response('ERROR:102 count illegal_arguments')
        else:
            self.send_text_response('ERROR:101 {} unknown_command'.format(cmd))


if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Invalid arguments.\nUsage: python albula_tcp_server.py ADDRESS_OR_PORT [BASE_DIR]")
        sys.exit()

    if re.match(r'^[0-9]+$', sys.argv[1]):
        # first argument consists of digits, e.g., "10001"
        server_address = socket.gethostname(), int(sys.argv[1])
    else:
        matched = re.match(r'^([0-9a-zA-Z.]+):([0-9]+)$', sys.argv[1])
        if matched:
            # first argument consists of address and port, e.g., "127.0.0.1:10001"
            server_address = matched.group(1), int(matched.group(2))
        else:
            print("Invalid ADDRESS_OR_PORT.\nUsage: python albula_tcp_server.py ADDRESS_OR_PORT [BASE_DIR]")
            sys.exit()

    image_base_dir = sys.argv[2] if len(sys.argv) == 3 else './'

    # print(server_address, image_base_dir)

    # initialize a server.
    server = AlbulaTCPServer(server_address, AlbulaRequestHandler, base_dir=sys.argv[2])

    # show an Albula window with a single subframe.
    server.set_albula_frame_number(1)

    # run the server.
    server.serve_forever()

    # close the server after the service is stopped (by server.shutdown() from another thread, for example).
    server.server_close()
