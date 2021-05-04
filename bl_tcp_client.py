import socket
import sys

def client(ip, port, message):
    # It seems with-statement of `socket` has not been supported in Python
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        print('Sent: {}'.format(repr(message)))
        # sock.sendall(bytes(message, 'ascii'))
        sock.sendall(message.encode('ascii'))
        # response = str(sock.recv(1024), 'ascii')
        response = sock.recv(1024).decode('ascii')
        print('Received: {}'.format(repr(response)))
    finally:
        sock.close()

if __name__ == '__main__':
    """Usage: ./bl_tcp_client.py PORT MESSAGE...
    """

    if len(sys.argv) < 3:
        print('Invalid arguments.\nUsage: ./bl_tcp_client.py PORT MESSAGE...')
        sys.exit()

    client('127.0.0.1', int(sys.argv[1]), ' '.join(sys.argv[2:]) + '\n')
