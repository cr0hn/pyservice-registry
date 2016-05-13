try:
	import ujson as json
except ImportError:
	import json

from uuid import UUID
from flask import Response, request

from pyservice_registry.models import Service
from pyservice_registry.helpers import crossdomain


def _check_input_params(input_vars):
	"""
	Check all input values are filled
	"""
	for name, value in input_vars.items():
		if not value:
			return Response(json.dumps(dict(message="'%s' can't be null" % name)).encode(errors="ignore"),
			                content_type="application/json",
			                status=400)
	return None


def routes_catalog(app):
	"""
	Add catalog end-points to the app

	:param app: Application instance from asyncio module
	:type app: `asyncio.web.Application`
	"""

	# --------------------------------------------------------------------------
	# Entry points
	# --------------------------------------------------------------------------
	@app.route("/api/v1/catalog/register", methods=["POST"])
	@crossdomain("*")
	def register():
		"""
	    This call register a new service in database
	    ---
	    tags:
	      - Catalog
	    parameters:
	      - name: name
	        in: post
	        type: string
	        required: true
	        description: the service name
	      - name: address
	        in: post
	        type: string
	        required: true
	        description: service address (IP or domain name)
	      - name: service_port
	        in: post
	        type: string
	        required: true
	        description: service port for communicate to with
	      - name: node_id
	        in: post
	        type: string
	        required: true
	        description: unique node ID. Must be in UUID format.
	    responses:
	      201:
	        description: service added
	        schema:
	          type: object
	        examples:
		      application/json:
		        message: MESSAGE TEXT
	      400:
	        description: some error in input format of data
	      409:
	        description: service already exits
	    """
		post_data = json.loads(request.data.decode(errors="ignore"))

		input_vars = dict(
			service_name=post_data.get('name', None),
			address=post_data.get('address', None),
			service_port=post_data.get('service_port', None),
			node_id=post_data.get('node_id', None)
		)

		# Check all input values are filled
		in_check = _check_input_params(input_vars)
		if in_check:
			return in_check

		try:
			UUID(input_vars.get("node_id"))
		except ValueError as e:
			Response(json.dumps({"message": e}).encode(errors="ignore"),
			         content_type="application/json",
			         status=400)

		# Get DB instance
		db = app.config['APP_DB']

		# Try to find in database
		try:
			db.get(Service, {
				"name" : input_vars.get("service_name"),
				"nodes": {
					"address"     : input_vars.get("address"),
					"service_port": input_vars.get("service_port"),
					"node_id"     : input_vars.get("node_id"),
				}
			})

			response = Response(json.dumps({"warn": "service already exits"}).encode(errors="ignore"),
			                    content_type="application/json",
			                    status=409)
		except Service.DoesNotExist:
			# Service not in database -> store it
			db.save(Service({
				"name"       : input_vars.get("service_name"),
				"description": post_data.get('description', None),
				"nodes"      : [
					{
						"address"     : input_vars.get("address"),
						"service_port": input_vars.get("service_port"),
						"node_id"     : input_vars.get("node_id"),
					}
				]
			}))

			response = Response(json.dumps({"message": "service added"}).encode(errors="ignore"),
			                    content_type="application/json",
			                    status=201)

		return response

	@app.route("/api/v1/catalog/deregister", methods=["POST"])
	@crossdomain("*")
	def deregister():
		"""
		This call de-register a new service in database
	    ---
	    tags:
	      - Catalog
	    parameters:
	      - name: name
	        in: post
	        type: string
	        required: true
	        description: the service name
	      - name: node_id
	        in: post
	        type: string
	        required: true
	        description: unique node ID. Must be in UUID format.
	    responses:
	      200:
	        description: service de-registered
	        schema:
	          type: object
	        examples:
		      application/json:
		        message: MESSAGE TEXT
	      400:
	        description: some error in input format of data
	      404:
	        description: service not found
		"""

		post_data = json.loads(request.data.decode(errors="ignore"))

		input_vars = dict(
			service_name=post_data.get('name', None),
			node_id=post_data.get('node_id', None)
		)

		# Check all input values are filled
		in_check = _check_input_params(input_vars)
		if in_check:
			return in_check

		# Get DB instance
		db = app.config['APP_DB']

		# Try to find in database
		try:
			res = db.get(Service, {"name": input_vars.get("service_name")})

			# Try to find the service with node_id
			post_to_remove = None
			for i, node in enumerate(res['nodes']):
				if node.get("node_id", None) == input_vars.get("node_id"):
					post_to_remove = i

			# Found element?
			if post_to_remove is not None:
				res['nodes'].pop(post_to_remove)

				# If this is the unique existing node, remove it
				if not res['nodes']:
					res.delete()

			response = Response(json.dumps({"message": "service removed"}).encode(errors="ignore"),
			                    content_type="application/json")
		except Service.DoesNotExist:
			response = Response(json.dumps({"message": "service not found"}).encode(errors="ignore"),
			                    content_type="application/json",
			                    status=404)

		return response

	@app.route("/api/v1/catalog/services", methods=["GET"])
	@crossdomain("*")
	def services():
		"""
		This call List available services by their name and description
	    ---
	    tags:
	      - Catalog
	    parameters:
	      - name: service_name
	        in: path
	        type: string
	        required: true
	        description: name of service
	    responses:
	      200:
	        description: listed available services
	        schema:
	          type: object
	        examples:
		      application/json: |-
		        [
		            {
		                "name": "SERVICE NAME",
		                "description": "SERVICE DESCRIPTION"
		            }
		        ]

		"""

		# Get DB instance
		db = app.config['APP_DB']

		response = []

		# Get all services
		for s in db.filter(Service, {}):
			response.append({
				"name"       : s.get("name"),
				"description": s.get("description")
			})

		return Response(json.dumps(response).encode(errors="ignore"),
		                content_type="application/json")

	@app.route("/api/v1/catalog/service/<sevice_name>", methods=["GET"])
	@crossdomain("*")
	def service(service_name=None):
		"""
		This call get service_name details
	    ---
	    tags:
	      - Catalog
	    parameters:
	      - name: service_name
	        in: path
	        type: string
	        required: true
	        description: name of service which we want the details
	    responses:
	      200:
	        description: everything was good
	        schema:
	          type: object
	        examples:
		      application/json: |-
		        [
		            {
		                "name": "SERVICE NAME",
		                "description": "SERVICE DESCRIPTION",
		                "nodes":
		                    [
			                    {
			                        "address": "IP OR DOMAIN_NAME",
			                        "service_port": "PORT"
			                    }
			                ]
		            }
		        ]
	      204:
	        description: service name not found
		"""

		# Check all input values are filled
		if not service_name:
			return Response(json.dumps({'error': 'service_name name is required'}),
			                content_type="application/json",
			                status=204)

		# Get DB instance
		db = app.config['APP_DB']

		# Try to find in database
		try:
			service_info = db.get(Service, {"name": service_name})

			response_data = []

			# Get all services
			if service_info:

				# Basic info
				info = {
					"name"       : service_info.get("name"),
					"description": service_info.get("description"),
					"nodes"      : []
				}

				# Get node info, removing private data
				for node in service_info.get("nodes", []):

					node_info = {}

					for n_name, n_data in node.items():
						if n_name != "node_id":
							node_info[n_name] = n_data

					# Append to service_name nodes
					info['nodes'].append(node_info)

				# Append to response
				response_data.append(info)

			response = Response(json.dumps(response_data).encode(errors="ignore"),
			                    content_type="application/json")

		except Service.DoesNotExist:
			response = Response(json.dumps({"message": "service name not found"}).encode(errors="ignore"),
			                    content_type="application/json",
			                    status=204)

		return response

		# app.add_url_rule("/api/v1/catalog/register")
		# app.add_url_route("/api/v1/catalog/deregister")