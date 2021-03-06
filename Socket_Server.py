import socket
import sys
import os.path
import threading
import signal
import time

class UDPServerConnection:

    def __init__(self, host = '127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.content_dir = os.path.dirname(os.path.abspath(__file__)) #Directory where webpage files are stored

    def run(self):

		#Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #Attempts to bind a socket to launch the server
        self._bindSocket()

	    #Start listening for connections
        self._listen()

    def _bindSocket(self):
        #Bind on self.host and self.port
        try:
            print("Starting server on {host}:{port}".format(host=self.host, port=self.port))
            self.sock.bind((self.host, self.port))
            print("Server started on port {port}.".format(port=self.port))

        except socket.error as e:
            print ('Bind failed:' + str(e[0]) + 'Message ' + e[1])
            self.shutDown()
            sys.exit(1)

    def _listen(self):

		#LIsten on self.port for any incoming connections
        self.sock.listen(5)

        while True:
            (client, address) = self.sock.accept()
            client.settimeout(60)
            print("Client connected from {addr}".format(addr=address))
            threading.Thread(target=self._headleToClient, args=(client, address)).start()

    def _generateHeaders(self, code, filePath):
        """
		Generate HTTP response headers.
		Parameters:
			- response_code: HTTP response code to add to the header.
		"""
        headerCode = ''

        if (code == 200):
            headerCode += 'HTTP/1.1 200 OK\n'
        elif(code == 404):
            headerCode += 'HTTP/1.1 404 Not Fund\n'

        current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())

        headerCode += 'Date: ' + current_date + '\n'
        headerCode += 'Server: HTTP-Server\n'
        headerCode += 'Connection: close\n'

        return headerCode

    def shutDown(self):
        try:
            print("Shutting down the server")
            s.socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("Warning could not shut down the socket. Maybe it was already closed? " + e)

    def _headleToClient(self, client, address):
        """
		Intructions that will handle the incoming connections and send the requrested file from content_dir
		Parameters:
			- client: socket client from accept()
			- address: socket address from accept()
		"""
        while True:
            data = client.makefile()

            if not data: break

            firstLine = data.readline()

            request_method = firstLine.split(' ')[0]
            print("Method: {m}".format(m=request_method))
            print("Request Body: {b}".format(b=firstLine))

            response = ''

            if request_method == "GET" or request_method == "HEAD":
				#Ex.: "GET /index.html" split on space
                file_requested = firstLine.split(' ')[1]

				#if get has parameters ('?'), ignore them
                file_requested = file_requested.split('?')[0]

                if  file_requested == "/":
                    file_requested = "/teste"

                filepath_to_send = self.content_dir + file_requested
                print("Sending web page [{wp}]".format(wp=filepath_to_send))

                contentSize = 0

                secondLine = data.readline()

				#Load and Send files content
                try:
                    f = open(filepath_to_send, 'rb')
                    if request_method == "GET": #Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self._generateHeaders(200, filepath_to_send)
                    contentSize = os.stat(filepath_to_send).st_size

                except Exception as e:
                    print("File not found. Sending 404 page.")
                    response_header = self._generateHeaders(404, filepath_to_send)

                    if request_method == "GET": #Temporary 404 response Page
                        response_data = b"<html><body><center><h1>Error 404: FIle not found</h1></center></body></html>"
                        contentSize = str(sys.getsizeof(response_data))

            response = response_header.encode()
            response += 'Content Length: {fileSize}\n\n'.format(fileSize=contentSize)

            if request_method == "GET":
                response += response_data

            client.send(response)
            client.close()
            break
        else:
            print("Unknown HTTP request method: {method}".format(method=request_method))

if __name__ == '__main__':
	server = UDPServerConnection()
	server.run()
