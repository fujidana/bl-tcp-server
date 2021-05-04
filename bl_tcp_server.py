"""Abstract superclass of TCP-IP server request handlers,
 developed for the purpose of responding a command from SPEC servers via TCP-IP socket communication.

Acceptable command format is as follows:

* Each statement is separated by new line (LF or CR+LF).
* Each statement consist of one command and optional arguments, separated by a white space.
* "QUIT" is a special command that terminates the server.
"""

# import statement for Python 2.7. This line is Harmless to Python 3.
from __future__ import division, print_function, unicode_literals, absolute_import

# `SocketServer` in Python 2.x is renamed `socketserver` in Python 3.x.
# However, in Python 2.7, it looks `socketserver` can be used as an alias to `SocketServer` .
import socketserver

from threading import Thread

# SocketServer.StreamRequestHandler allows one to use a file-like
# object to handle the communication contents; e.g., one can use
# readline() instead of raw recv() calls.
# However, this class seems incompatible with spec software.
# Therefore, we use a bit abstract class: socketserver.BaseRequestHandler.
class BLRequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        """Called when a new client connects.
        """

        print("Client {}:{} connected.".format(self.client_address[0], self.client_address[1]))

    def handle(self):
        """Main loop for TCP/IP communication with the client.
        """

        data = 'dummy'
        while data:

            data = self.request.recv(1024).decode('ascii')
            # print(data)
            lines = data.splitlines()

            for line in lines:
                line = line.strip()

                if len(line) == 0:
                    continue
                elif line.upper() == 'QUIT':
                    self.send_text_response('OK quit')
                    Thread(target=shutdown_server, args=(self.server,)).start()
                    print("Quited")
                    return
                else:
                    words = line.split(' ')
                    self.process_command(words[0], words[1:])

    def finish(self):
        """Called when the client closes the connection.
        """

        print('Client {}:{} disconnected.'.format(self.client_address[0],  self.client_address[1]))

    def process_command(self, cmd, params):
        """Dummy implementation that returns capitalized input command and parameters.
        Subclasses must overwrite it.
        """

        if params:
            self.send_text_response(cmd.upper() + ' ' + ' '.join([param.upper() for param in params]))
        else:
            self.send_text_response(cmd.upper())

    def send_text_response(self, response):
        self.request.sendall((response + '\n').encode('ascii'))


def shutdown_server(server):
    server.shutdown()
    server.server_close()

if __name__ == '__main__':
    # create server and run it
    SERVER = socketserver.TCPServer(('', 10000), BLRequestHandler)
    SERVER.serve_forever()
    SERVER.server_close()
