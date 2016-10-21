#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    Created By qianlitp 24/9/2016

    filePath参数没有完成，功能不完全
--------------------------------------------
    Revised By qianlitp 21/10/2016

    添加filePath功能，完善文件传输
"""
import os
import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0
bufferSize = 4096
filePath = ""


# print the usage
def usage():
    print("""

                PyShell   Created By qianlitp   24/09/2016

            """)
    print(" Usage: PyShell.py -t target_host -p port")
    print()
    print(" Server:")
    print("     -l --listen                  - listen on [host]:[port] for incoming connection.")
    print("     -e --execute=file_to_run     - execute the given file upon receiving a connection.")
    print("     -c --command                 - initialize a command shell")
    print("     -u --upload=destination      - upon receiving connection upload a file and write to [destination], "
          "you must use '-f' to load a file at Client.")
    print()
    print(" Client:")
    print("     -b --bufferSize=size         - the bufferSize of receiving output.When you receiving the incomplete "
          "result, trying to increase it. default=4096.")
    print("     -f --file=filePath           - the path of file you want to load")
    print()
    print(" Examples: ")
    print("     PyShell.py -p 2222 -l -c (server) | PyShell.py -t 10.10.139.59 -p 2222 (client)")
    print("     PyShell.py -p 2222 -l -u=/usr/local/target.bak (server) | "
          "PyShell.py -t 10.10.139.59 -p 2222 -f /usr/lcoal/myFile (client)")
    # print("     PyShell.py -t 192.168.0.1 -p 2222 -l -e=\"cat /etc/passwd\"")
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    global bufferSize
    global filePath
    if not len(sys.argv[1:]):
        usage()

    # deal the args
    try:
        options, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:b:f:", ["help", "listen", "execute=", "target", "port",
                                                                        "command", "upload=", "bufferSize", "filePath"])
    except getopt.GetoptError as error:
        print(str(error))
        usage()
    for opt, arg in options:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-l", "--listen"):
            listen = True
        elif opt in ("-e", "--execute"):
            execute = arg
        elif opt in ("-c", "--command"):
            command = True
        elif opt in ("-u", "--upload"):
            upload_destination = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-b", "--bufferSize"):
            bufferSize = int(arg)
        elif opt in ("-f", "--filePath"):
            filePath = arg
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        client_sender()
    if listen:
        server_loop()


# the client
def client_sender():
    global bufferSize
    global filePath
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # try:
    client.connect((target, port))

    if len(filePath):
        file_uploader = open(filePath, 'r')
        try:
            file_content = file_uploader.read()
        finally:
            file_uploader.close()
        client.send(bytes(file_content, 'utf-8'))

    while True:
        recv_len = 1
        response = ""

        while recv_len:
            data = client.recv(bufferSize)
            try:
                data = data.decode('utf-8')
            except:
                data = data.decode('gbk')
            recv_len = len(data)
            response += data

            if recv_len < bufferSize:
                break

        print(response+'>', end="")

        buffer = input()
        client.send(bytes(buffer, 'utf-8'))

    # except:
    #     print("[*] Exception! Exiting...")
    #     client.close()


# the server
def server_loop():
    global target

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        client_thread = threading.Thread(target=client_hander, args=(client_socket,))
        client_thread.start()


# run the command
def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"
    return output


def client_hander(client_socket):
    global upload
    global execute
    global command
    global bufferSize
    global upload_destination

    # receive the file and save it
    if len(upload_destination):
        data_len = bufferSize
        file_buffer = ""
        while data_len == bufferSize:
            data = client_socket.recv(bufferSize).decode('utf-8')
            data_len = len(data)
            file_buffer += data
        try:
            file_descriptor = open(upload_destination, "w")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            client_socket.send(bytes("Successfully saved file to %s\r\n" % upload_destination, 'utf-8'))
        except:
            client_socket.send(bytes("Failed to save file to %s\r\n" % upload_destination, 'utf-8'))
    # execute the given command
    if len(execute):
        output = run_command(execute)
        try:
            client_socket.send(output)
        except:
            client_socket.send(bytes(output, 'utf-8'))
    # command shell
    if command:
        client_socket.send(bytes("Connect Successful, input your command \n"
                                 + os.path.abspath('.'), 'utf-8'))
        while True:
            cmd_buffer = client_socket.recv(1024).decode('utf-8')
            response = run_command(cmd_buffer)
            try:
                response += bytes('\r\n', 'utf-8')
                response += bytes(os.path.abspath('.'), 'utf-8')
                client_socket.send(response)
            except:
                response += '\r\n'
                response += os.path.abspath('.')
                client_socket.send(bytes(response, 'utf-8'))


if __name__ == '__main__':
    main()
