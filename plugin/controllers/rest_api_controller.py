# -*- coding: utf-8 -*-
import urlparse
import copy

from twisted.web import http, resource

from web import WebController
from rest import json_response, CORS_ALLOWED_METHODS_DEFAULT, CORS_DEFAULT
from rest import CORS_DEFAULT_ALLOW_ORIGIN


class ApiController(resource.Resource):
	isLeaf = True

	def __init__(self, session, path="", *args, **kwargs):
		self.webcrap = WebController(session, path)
		self._resource_prefix = kwargs.get("resource_prefix", '/api')
		self._cors_header = copy.copy(CORS_DEFAULT)
		http_verbs = []

		for verb in CORS_ALLOWED_METHODS_DEFAULT:
			method_name = 'render_{:s}'.format(verb)
			if hasattr(self, method_name):
				http_verbs.append(verb)
		self._cors_header['Access-Control-Allow-Methods'] = ','.join(http_verbs)

	def render_OPTIONS(self, request):
		"""
		Render response for an HTTP OPTIONS request.

		Args:
			request (twisted.web.server.Request): HTTP request object
		Returns:
			HTTP response with headers
		"""
		for key in self._cors_header:
			request.setHeader(key, self._cors_header[key])

		return ''

	def render_GET(self, request):
		# as implemented in BaseController --v
		request.path = request.path.replace('signal', 'tunersignal')
		rq_path = urlparse.unquote(request.path)

		if not rq_path.startswith(self._resource_prefix):
			raise ValueError("Invalid Request Path {!r}".format(request.path))

		request.setHeader(
			'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

		# as implemented in BaseController -----------------v
		func_path = rq_path[len(self._resource_prefix) + 1:].replace(".", "")

		func = getattr(self.webcrap, "P_" + func_path, None)
		if func is None:
			request.setResponseCode(http.NOT_FOUND)
			data = {
				"method": repr(func_path),
				"success": False
			}
			return json_response(request, data)

		try:
			request.setResponseCode(http.OK)
			data = func(request)
			return json_response(data=data, request=request)
		except Exception as exc:
			request.setResponseCode(http.INTERNAL_SERVER_ERROR)
			data = {
				"exception": repr(exc),
				"success": False
			}
			return json_response(request, data)
