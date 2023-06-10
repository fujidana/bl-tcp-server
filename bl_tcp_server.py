"""Abstract superclass of socketserver.BaseRequestHandler,
used by socketserver.TCPServer to communcate with SPEC software.

The basic rules of a command set this request handler handles are:

* Each statement is separated by new line (LF or CR+LF).
* Each statement consists of one command and optional arguments, separated by a white space.
* "QUIT" is a special command that terminates the server.
"""

# Import statement for Python 2.7 code more compatible with Python 3.x.
# Commented out due to inconpatibility with Pixet Pro for Advacam TimePIX3 control.
# from __future__ import division, print_function, unicode_literals, absolute_import

# `SocketServer` in Python 2.7 has been renamed to `socketserver` in Python 3.
# However, in Python 2.7, it looks `socketserver` can be used as an alias to `SocketServer`.
import socketserver

from threading import Thread

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
        Subclasses must overwrite this method.
        """

        if params:
            self.send_text_response(cmd.upper() + ' ' + ' '.join([param.upper() for param in params]))
        else:
            self.send_text_response(cmd.upper())

    def send_text_response(self, response):
        self.request.sendall((response + '\n').encode('ascii'))


def shutdown_server(server):
    server.shutdown()
    # server.server_close()

# # main code to test this TCP server, 
# # which simply returns the input text after capitalization.
# if __name__ == '__main__':
#    # create server and run it
#    SERVER = socketserver.TCPServer(('', 10000), BLRequestHandler)
#    SERVER.serve_forever()
#    SERVER.server_close()
