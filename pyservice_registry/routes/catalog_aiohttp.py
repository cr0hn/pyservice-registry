import json
import asyncio

import aiohttp
from aiohttp import web

from pyservice_registry.models import Service


def _check_input_params(input_vars):
	"""
	Check all input values are filled
	"""
	for name, value in input_vars.items():
		if not value:
			return web.HTTPBadRequest(body=json.dumps(dict(error="'%s' can't be null" % name)).encode(errors="ignore"),
			                          content_type="application/json")
	return None


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------
@asyncio.coroutine
def register(request):
	"""
	Register a new service
	"""
	post_data = yield from request.json()

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

	# Get DB instance
	db = request.app['APP_DB']

	# Try to find in database
	try:
		db.get(Service, {
			"name"               : input_vars.get("service_name"),
			"nodes": {
				"address"        : input_vars.get("address"),
				"service_port"   : input_vars.get("service_port"),
				"node_id"        : input_vars.get("node_id"),
			}
		})

		response = web.HTTPConflict(body=json.dumps({"warn": "service already exits"}).encode(errors="ignore"), content_type="application/json")
	except Service.DoesNotExist:
		# Service not in database -> store it
		db.save(Service({
			"name"                   : input_vars.get("service_name"),
			"description"            : post_data.get('description', None),
			"nodes": [
				{
					"address"        : input_vars.get("address"),
					"service_port"   : input_vars.get("service_port"),
					"node_id"        : input_vars.get("node_id"),
				}
			]
		}))

		response = web.HTTPOk(body=json.dumps({"ok": "service added"}).encode(errors="ignore"),
		                      content_type="application/json")

	return response


@asyncio.coroutine
def deregister(request):
	"""
	De-register a new service
	"""
	post_data = yield from request.json()

	input_vars = dict(
		service_name=post_data.get('name', None),
		node_id=post_data.get('node_id', None)
	)

	# Check all input values are filled
	in_check = _check_input_params(input_vars)
	if in_check:
		return in_check

	# Get DB instance
	db = request.app['APP_DB']

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

		response = web.HTTPOk(body=json.dumps({"ok": "service removed"}).encode(errors="ignore"),
		                      content_type="application/json")
	except Service.DoesNotExist:
		response = web.HTTPNotFound(body=json.dumps({"error": "service not found"}).encode(errors="ignore"),
		                            content_type="application/json")

	return response


@asyncio.coroutine
def services(request):
	"""
	List available services by their name and description
	"""

	# Get DB instance
	db = request.app['APP_DB']

	response = []

	# Get all services
	for s in db.filter(Service, {}):
		response.append({
			"name": s.get("name"),
			"description": s.get("description")
		})

	return web.HTTPOk(body=json.dumps(response).encode(errors="ignore"), content_type="application/json")


@asyncio.coroutine
def service(request):
	"""
	Get service details
	"""
	service_name = request.match_info.get('service', None)

	# Check all input values are filled
	if not service_name:
		return web.HTTPBadRequest(body=json.dumps({'error': 'service name is required'}),
		                          content_type="application/json")

	# Get DB instance
	db = request.app['APP_DB']

	# Try to find in database
	try:
		db.get(Service, {"name": service_name})

		response_data = []

		# Get all services
		for s in db.filter(Service, {}):

			# Basic info
			info = {
				"name": s.get("name"),
				"description": s.get("description"),
				"nodes": []
			}

			# Get node info, removing private data
			for node in s.get("nodes", []):

				node_info = {}

				for n_name, n_data in node.items():
					if n_name != "node_id":
						node_info[n_name] = n_data

				# Append to service nodes
				info['nodes'].append(node_info)

			# Append to response
			response_data.append(info)

		response = web.HTTPOk(body=json.dumps(response_data).encode(errors="ignore"),
		                      content_type="application/json")

	except Service.DoesNotExist:
		response = web.HTTPNotFound(body=json.dumps({"error": "service not found"}).encode(errors="ignore"),
		                            content_type="application/json")

	return response


def routes_catalog(app):
	"""
	Add catalog end-points to the app

	:param app: Application instance from asyncio module
	:type app: `asyncio.web.Application`
	"""
	app.router.add_route("POST", "/v1/catalog/register", register, expect_handler=aiohttp.web.Request.json)
	app.router.add_route("POST", "/v1/catalog/deregister", deregister, expect_handler=aiohttp.web.Request.json)
	app.router.add_route("GET", "/v1/catalog/services", services)
	app.router.add_route("GET", "/v1/catalog/service/{service}", service)
