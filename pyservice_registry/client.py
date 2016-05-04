import json
import sys
import socket
import logging
import argparse
from urllib.parse import urljoin

import hashlib
import requests


logging.basicConfig(level=logging.INFO, format='[ Service Register client] %(asctime)s - %(message)s')
log = logging.getLogger(__name__)


def get_hardware_id():
	"""
	Get an unique hardware ID, based on CPU info. All the times called, the value will be the same.

	>>> get_hardware_id()
	'f8ef57d64aae6f3c45200b39di422bd6ca625d9a79655cb3aa6e171ef6f93013aa16c2df2f2b0359dfaf1782ba6fda94300506cdd9b21fdaf1264fbd0e47abb89'

	:return: string with the hardware ID
	:rtype: str
	"""
	import cpuinfo

	_ci = cpuinfo.get_cpu_info()

	cpu_inf = ("%s%s%s%s" % (_ci['hz_actual'],
	                         _ci['brand'],
	                         "".join(_ci['flags']),
	                         _ci['arch'])).replace(" ", "")

	d = hashlib.sha512()
	d.update(cpu_inf.encode(errors="ignore"))

	return d.hexdigest()


class RegisterClient(object):

	route_register = "/v1/catalog/register"
	route_deregister = "/v1/catalog/deregister"
	route_services_list = "/v1/catalog/services"
	route_details = "/v1/catalog/service/"

	def __init__(self, host, port, https=False):

		if not isinstance(host, str):
			raise TypeError("Expected str, got '%s' instead" % type(host))
		if not isinstance(port, int):
			raise TypeError("Expected int, got '%s' instead" % type(port))

		self.port = port
		self.host = host
		self.https = https

	def _build_url(self, uri, https=False):

		return urljoin("%s://%s:%s" % ("https" if self.https else "http",
		                               self.host,
		                               self.port),
		               uri)

	def register(self, service_name, service_port=8080, service_description=None, node_id=None, service_address=None):
		"""
		:param service_name:
		:type service_name:

		:param service_port:
		:type service_port:

		:param service_description:
		:type service_description:

		:param node_id:
		:type node_id:

		:param service_address:
		:type service_address:

		:return: None: all is oks. string: an error was raised
		:rtype: None|str
		"""

		if not isinstance(service_name, str):
			raise TypeError("Expected str, got '%s' instead" % type(service_name))

		if not service_port:
			_service_port = 8080
		else:
			_service_port = service_port

		# Service ID
		if not node_id:
			if sys.platform.startswith("win"):
				raise ValueError("In Windows systems, 'node_id' couldn't be generated automatically")
			else:
				# Generate Unique Machine ID
				_service_id = get_hardware_id()
		else:
			_service_id = node_id

		# Local IP
		if not service_address:
			_service_address = socket.gethostbyname(socket.gethostname())
		else:
			_service_address = socket.gethostbyname(service_address)

		ret = requests.post(self._build_url(self.route_register),
		                    data=json.dumps(dict(
			                    name=service_name,
			                    description=service_description,
			                    address=_service_address,
			                    service_port=_service_port,
			                    node_id=_service_id
		                    )).encode(errors="ignore"), headers = {'content-type': 'application/json'})

		if ret.status_code == 200:
			return None
		else:
			return ret.text

	def deregister(self, service_name, node_id=None):
		if not isinstance(service_name, str):
			raise TypeError("Expected str, got '%s' instead" % type(service_name))

		if not node_id:
			_node_id = get_hardware_id()
		else:
			_node_id = node_id

		ret = requests.post(self._build_url(self.route_deregister),
		                    data=json.dumps(dict(
			                    name=service_name,
			                    node_id=_node_id
		                    )).encode(errors="ignore"))

		if ret.status_code == 200:
			return None
		elif ret.status_code == 404:
			return "Service '%s' is not registered in server" % service_name
		else:
			return ret.text

	def list_services(self):
		ret = requests.get(self._build_url(self.route_services_list))

		return json.loads(ret.text)

	def service_details(self, name):
		if not isinstance(name, str):
			raise TypeError("Expected str, got '%s' instead" % type(name))

		ret = requests.get("%s%s" % (self._build_url(self.route_details), name))

		if ret.status_code == 200:
			return json.loads(ret.text)
		elif ret.status_code == 404:
			return "Service '%s' is not registered in server" % name
		else:
			return ret.text


def cmd_run(args):

	client = RegisterClient(host=args.HOST, port=args.PORT)

	if args.action == "register":
		log.critical("Registering service '%s'..." % args.SERVICE_NAME)
		ret = client.register(service_name=args.SERVICE_NAME,
		                      service_port=args.SERVICE_PORT,
		                      node_id=args.NODE_ID,
		                      service_description=args.SERVICE_DESCRIPTION,
		                      service_address=args.SERVICE_ADDRESS)
		if ret:
			log.critical("Error: %s" % ret)
		log.critical("Done!")

	elif args.action == "deregister":
		log.critical("De-registering service '%s'..." % args.SERVICE_NAME)
		ret = client.deregister(args.SERVICE_NAME, args.NODE_ID)

		if ret:
			log.critical("Error: %s" % ret)

		log.critical("Done!")

	elif args.action == "list":
		log.critical("Listing registered services...")
		log.critical("Services:")
		log.critical("Services:")

		for n in client.list_services():
			log.critical("|__ Name: '%s' # Description: '%s'" % (n['name'], n['description']))

	elif args.action == "details":
		log.critical("Getting details of services '%s'..." % args.SERVICE_NAME)

		for n in client.service_details(args.SERVICE_NAME):
			log.critical("|__ Name: '%s' # Description: '%s'" % (n['name'], n['description']))

			if n['nodes']:
				# log.critical("    \__ Nodes: ")

				for i, node in enumerate(n['nodes']):
					log.critical("    \_ Node-%s " % i)
					log.critical("       * Address: %s" % node['address'])
					log.critical("       * Port: %s" % node['service_port'])

	else:
		raise ValueError("Action '%s' unrecognised" % args.action)


def main():
	parser = argparse.ArgumentParser(description='Service Discovery Client',
	                                 formatter_class=argparse.RawTextHelpFormatter)

	# Main options
	parser.add_argument('-H', '--host', dest="HOST", help="host address", required=True)
	parser.add_argument('-p', '--port', dest="PORT", type=int, help="server port", default=8080)
	parser.add_argument("-v", "--verbosity", dest="VERBOSE", action="count", help="verbosity level: -v, -vv, -vvv.",
	                    default=2)

	subparser = parser.add_subparsers(dest="action")

	# Register options
	parser_register = subparser.add_parser('register', help='register a service')
	parser_register.add_argument("-n", "--service-name", dest="SERVICE_NAME", required=True)
	parser_register.add_argument("-I", "--service-id", dest="NODE_ID")
	parser_register.add_argument("-A", "--service-address", dest="SERVICE_ADDRESS")
	parser_register.add_argument("-P", "--service-port", type=int, dest="SERVICE_PORT")
	parser_register.add_argument("-D", "--service-description", dest="SERVICE_DESCRIPTION")

	# Deregister options
	parser_deregister = subparser.add_parser('deregister', help='deregister a service')
	parser_deregister.add_argument("-n", "--name", dest="SERVICE_NAME", required=True)
	parser_deregister.add_argument("-I", "--id", dest="NODE_ID")

	# List options
	subparser.add_parser('list', help='list services')

	# Details options
	parser_details = subparser.add_parser('details', help='show service details')
	parser_details.add_argument("-n", "--service-name", dest="SERVICE_NAME", required=True)

	parsed_args = parser.parse_args()

	# Setting
	log.setLevel(50 - (parsed_args.VERBOSE * 10))

	cmd_run(parsed_args)


if __name__ == '__main__':
	main()
