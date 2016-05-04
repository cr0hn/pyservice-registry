import logging
import argparse
import os

from aiohttp import web
from blitzdb import FileBackend, MongoBackend

from pyservice_registry.models import Service
from pyservice_registry.routes.catalog import routes_catalog

logging.basicConfig(level=logging.ERROR, format='[ %(levelname)-5s - Service Register ] %(asctime)s - %(message)s')
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Start app
# --------------------------------------------------------------------------
def start(args):
	"""
	Start the app

	:param args: input parameters
	:type args: Namespace

	"""
	# --------------------------------------------------------------------------
	# Set Database connection
	# --------------------------------------------------------------------------
	if args.DB_TYPE == "file":
		# File oriented DB
		if not args.FILE_DB_PATH:
			_path = os.path.join(os.getcwd(), "service_db")
		else:
			_path = os.path.join(args.FILE_DB_PATH, "service_db")

		backend = FileBackend(_path, {'serializer_class': 'pickle'})
		backend.create_index(Service, 'name', ephemeral=False, fields=["name"])
	else:
		import socket
		from pymongo import MongoClient, DESCENDING

		if not args.MONGODB_HOST:
			raise ValueError("You must specify a MongoDB host")

		_mongo_password = "" if not args.MONGODB_PASSWORD else args.MONGODB_PASSWORD
		_mongo_user = "" if not args.MONGODB_USER else args.MONGODB_USER
		_mongo_port = 27018 if not args.MONGODB_PORT else args.MONGODB_PORT

		_mongo_uri = 'mongodb://%(user)s%(sep)s%(password)s%(arr)s%(host)s' % dict(
			user=_mongo_user,
			sep=":" if _mongo_user else "",
			arr="@" if _mongo_user else "",
			password=_mongo_password,
			host=args.MONGODB_HOST
		)

		# PyMongo doesn't check socket timeout -> test manually
		try:
			sock = socket.socket()
			sock.connect((args.MONGODB_HOST, _mongo_port))
		except socket.error:
			raise ConnectionError("Can't connect to MongoDB host")

		# MongoDB
		c = MongoClient(_mongo_uri, port=_mongo_port, connectTimeoutMS=5000)

		# Get database and scheme
		db = c["pyregister" if not args.MONGODB_DB else args.MONGODB_DB]
		col = db["services" if not args.MONGODB_SCHEME else args.MONGODB_SCHEME]

		# Create index
		col.create_index([("name", DESCENDING)])

		# create a new BlitzDB backend using a MongoDB database
		backend = MongoBackend(col)

	#
	# Link backend to web-server property
	#
	backend.autocommit = True
	# app = web.Application(debug=args.DEBUG)
	app = web.Application(debug=True)

	# --------------------------------------------------------------------------
	# Routes
	# --------------------------------------------------------------------------
	# Catalog
	routes_catalog(app)

	app['APP_DB'] = backend

	web.run_app(app,
	            host=args.IP,
	            port=args.PORT)


# --------------------------------------------------------------------------
# Main entry
# --------------------------------------------------------------------------
def main():

	example = """
Examples:

	Increase verbosity:
	%(name)s -vvv

	""" % dict(name="pyservice-register")

	parser = argparse.ArgumentParser(description='Register Service Server',
	                                 formatter_class=argparse.RawTextHelpFormatter, epilog=example)

	# Main options
	parser.add_argument('-p', '--port', dest="PORT", type=int, help="listen port. Default 50000", default=8000)
	parser.add_argument('-l', '--listen', dest="IP", help="listen IP. Default 0.0.0.0", default="0.0.0.0")
	parser.add_argument("-v", "--verbosity", dest="VERBOSE", action="count", help="verbosity level: -v, -vv, -vvv.",
	                    default=3)
	parser.add_argument('-t', '--db-type', dest="DB_TYPE", help="database type. Default: file", default="file",
	                    choices=["file", "mongodb"])
	parser.add_argument('-d', '--debug', dest="DEBUG", action="store_true", help="enable debug mode", default=False)

	# Scanner options
	gr_file_db = parser.add_argument_group("File database options")
	gr_file_db.add_argument("--path", dest="FILE_DB_PATH", help="path to file database", default=None)

	gr_mongo_db = parser.add_argument_group("MongoDB database options")
	gr_mongo_db.add_argument("-H", "--mongo-host", dest="MONGODB_HOST", help="mongoDB host", default=None)
	gr_mongo_db.add_argument("-P", "--mongo-port", dest="MONGODB_PORT", help="mongoDB port", type=int, default=27018)
	gr_mongo_db.add_argument("-U", "--mongo-user", dest="MONGODB_USER", help="mongoDB user", default=None)
	gr_mongo_db.add_argument("-C", "--mongo-password", dest="MONGODB_PASSWORD", help="mongoDB password", default=None)
	gr_mongo_db.add_argument("-B", "--mongo-db", dest="MONGODB_DB", help="mongoDB database", default="pyregister")
	gr_mongo_db.add_argument("-S", "--mongo-scheme", dest="MONGODB_SCHEME", help="mongoDB scheme", default="services")

	parsed_args = parser.parse_args()

	# Setting
	log.setLevel(50 - (parsed_args.VERBOSE * 10))

	try:
		start(parsed_args)
	except Exception as e:
		log.critical(e)

		log.info(e, exc_info=True)


if __name__ == '__main__':
	main()
