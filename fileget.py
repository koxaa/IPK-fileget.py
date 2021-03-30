import sys, socket, os, re, time
from urllib.parse import urlparse
from optparse import OptionParser

def get_file(tail: str, head: str, domain: str, ALL_FLAG: bool = False):
	tcp_message = create_tcp_msg(tail,head,domain)
	s 			= init_stream_socket(tcp_ip, tcp_port)
	s.send(tcp_message.encode('utf-8'))
	data 		= recieve_data(s)
	s.shutdown(socket.SHUT_RDWR)
	s.close()
	if data == False:
		return False
	else:
		if ALL_FLAG:
			write_out_data(tail[len(filepath):], head, data) # want to write out only subdirectories
		else:
			write_out_data('',head,data)
		return True

def get_index(domain: str):
	tcp_message = create_tcp_msg('', 'index', domain)
	s.send(tcp_message.encode('utf-8'))
	indexfile = recieve_data(s).encode('utf-8')
	s.shutdown(socket.SHUT_RDWR)
	s.close()
	if indexfile == False:
		return False
	else:
		return indexfile.split('\r\n')

def init_stream_socket(tcp_ip: str, tcp_port: int):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(5.0)
	s.connect((tcp_ip, tcp_port))
	return s

def recieve_data(s: socket.socket):
	if re.search(r"^FSP/1.0 Not Found", s.recv(4096).decode('utf-8')):
		return False
	result = bytes()
	while True:
		data = s.recv(4096)
		if not data:
			break
		result += data
	return result

def write_out_data(filepath: str, filename: str, data: bytes):
	if filepath != '':
		if filepath[0] == '/':
			filepath = filepath[1:]
	if not os.path.exists('./'+filepath):
		os.makedirs(filepath)
	f = open(os.path.join(filepath,filename), "wb")
	f.write(data)
	f.close()

def create_tcp_msg(filepath: str, filename: str, domain: str):
	return 'GET '+ os.path.join(filepath,filename) + ' FSP/1.0\r\nHostname: '+domain+'\r\nAgent: xkrukh00\r\n\r\n'

def create_udp_msg(domain: str):
	return 'WHEREIS ' + domain


# Oprions parsing
optparser = OptionParser(usage="Usage: fileget.py -n <NAMESERVER> -f <SURL>")
optparser.add_option('-f', nargs=1, type="string", dest="SURL")
optparser.add_option('-n', nargs=1, type="string", dest="NAMESERVER")
(options, args) = optparser.parse_args()

if options.SURL == None or options.NAMESERVER == None: optparser.error("Too few options or arguments")
surl = urlparse(options.SURL)
nameserver = str(options.NAMESERVER).split(':')

udp_ip 		= nameserver[0]
udp_port 	= int(nameserver[1])
udp_addr	= (udp_ip, udp_port)
domain 		= surl.netloc

(filepath, filename) = os.path.split(surl.path)
filepath = re.sub(r"^/", "", filepath)			#remove first slash

s 			= socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.settimeout(5.0)
s.sendto(create_udp_msg(domain).encode('utf-8'), udp_addr)

try:
	(rcv_data, rcv_adress) = s.recvfrom(4096)
except socket.timeout:
	raise SystemExit('Timeout. Server does not responding')

if rcv_data == b'ERR Not Found':
	raise SystemExit('File Server was not found')
else:
	fileservername = rcv_data.decode('utf-8').strip('OK ')
	(tcp_ip, tcp_port) = fileservername.split(':')
	tcp_port = int(tcp_port)
s.close()

if filename != '*':
	if not get_file(filepath, filename, domain):
		raise SystemExit("File was not downloaded")
else:
	indexfile = get_index(domain)
	indexfile.pop()
	for f in indexfile:
		(tail, head) = os.path.split(f)
		if filepath in tail:
			if not get_file(tail, head, domain,True):
				print("Couldn`t load file: ",os.path.join(tail,head))