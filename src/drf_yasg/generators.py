import re
from collections import defaultdict, OrderedDict

import django.db.models
import uritemplate
from coreapi.compat import force_text
from rest_framework import versioning
from rest_framework.schemas.generators import SchemaGenerator, EndpointEnumerator as _EndpointEnumerator
from rest_framework.schemas.inspectors import get_pk_description

from . import openapi
from .inspectors import SwaggerAutoSchema
from .openapi import ReferenceResolver

PATH_PARAMETER_RE = re.compile(r'{(?P<parameter>\w+)}')


class EndpointEnumerator(_EndpointEnumerator):
    def get_path_from_regex(self, path_regex):
        return self.unescape_path(super(EndpointEnumerator, self).get_path_from_regex(path_regex))

    def unescape(self, s):
        """Unescape all backslash escapes from `s`.

        :param str s: string with backslash escapes
        :rtype: str
        """
        # unlike .replace('\\', ''), this corectly transforms a double backslash into a single backslash
        return re.sub(r'\\(.)', r'\1', s)

    def unescape_path(self, path):
        """Remove backslashes from all path components outside {parameters}. This is needed because
        Django>=2.0 ``path()``/``RoutePattern`` aggresively escapes all non-parameter path components.

        **NOTE:** this might destructively affect some url regex patterns that contain metacharacters (e.g. \w, \d)
        outside path parameter groups; if you are in this category, God help you

        :param str path: path possibly containing
        :return: the unescaped path
        :rtype: str
        """
        clean_path = ''
        while path:
            match = PATH_PARAMETER_RE.search(path)
            if not match:
                clean_path += self.unescape(path)
                break
            clean_path += self.unescape(path[:match.start()])
            clean_path += match.group()
            path = path[match.end():]

        return clean_path


class OpenAPISchemaGenerator(object):
    """
    This class iterates over all registered API endpoints and returns an appropriate OpenAPI 2.0 compliant schema.
    Method implementations shamelessly stolen and adapted from rest_framework SchemaGenerator.
    """
    endpoint_enumerator_class = EndpointEnumerator

    def __init__(self, info, version, url=None, patterns=None, urlconf=None):
        """

        :param .Info info: information about the API
        :param str version: API version string, takes preedence over the version in `info`
        :param str url: API
        :param patterns: if given, only these patterns will be enumerated for inclusion in the API spec
        :param urlconf: if patterns is not given, use this urlconf to enumerate patterns;
            if not given, the default urlconf is used
        """
        self._gen = SchemaGenerator(info.title, url, info.get('description', ''), patterns, urlconf)
        self.info = info
        self.version = version

    def get_schema(self, request, public=False):
        """Generate an :class:`.Swagger` representing the API schema.

        :param rest_framework.request.Request request: the request used for filtering
            accesible endpoints and finding the spec URI
        :param bool public: if True, all endpoints are included regardless of access through `request`

        :return: the generated Swagger specification
        :rtype: openapi.Swagger
        """
        endpoints = self.get_endpoints(None if public else request)
        endpoints = self.replace_version(endpoints, request)
        components = ReferenceResolver(openapi.SCHEMA_DEFINITIONS)
        paths = self.get_paths(endpoints, components, request)

        url = self._gen.url
        if not url and request is not None:
            url = request.build_absolute_uri()

        return openapi.Swagger(
            info=self.info, paths=paths,
            _url=url, _version=self.version, **dict(components)
        )

    def create_view(self, callback, method, request=None):
        """Create a view instance from a view callback as registered in urlpatterns.

        :param callable callback: view callback registered in urlpatterns
        :param str method: HTTP method
        :param rest_framework.request.Request request: request to bind to the view
        :return: the view instance
        """
        view = self._gen.create_view(callback, method, request)
        overrides = getattr(callback, 'swagger_auto_schema', None)
        if overrides is not None:
            # decorated function based view must have its decorator information passed on to the re-instantiated view
            for method, _ in overrides.items():
                view_method = getattr(view, method, None)
                if view_method is not None:  # pragma: no cover
                    setattr(view_method.__func__, 'swagger_auto_schema', overrides)
        return view

    def replace_version(self, endpoints, request):
        """If ``request.version`` is not ``None``, replace the version parameter in the path of any endpoints using
        ``URLPathVersioning`` as a versioning class.

        :param dict endpoints: endpoints as returned by :meth:`.get_endpoints`
        :param Request request: the request made against the schema view
        :return: endpoints with modified paths
        """
        version = getattr(request, 'version', None)
        if version is None:
            return endpoints

        new_endpoints = {}
        for path, endpoint in endpoints.items():
            view_cls = endpoint[0]
            versioning_class = getattr(view_cls, 'versioning_class', None)
            version_param = getattr(versioning_class, 'version_param', 'version')
            if versioning_class is not None and issubclass(versioning_class, versioning.URLPathVersioning):
                path = path.replace('{%s}' % version_param, version)

            new_endpoints[path] = endpoint

        return new_endpoints

    def get_endpoints(self, request=None):
        """Iterate over all the registered endpoints in the API.

        :param rest_framework.request.Request request: used for returning only endpoints available to the given request
        :return: {path: (view_class, list[(http_method, view_instance)])
        :rtype: dict
        """
        enumerator = self.endpoint_enumerator_class(self._gen.patterns, self._gen.urlconf)
        endpoints = enumerator.get_api_endpoints()

        view_paths = defaultdict(list)
        view_cls = {}
        for path, method, callback in endpoints:
            view = self.create_view(callback, method, request)
            path = self._gen.coerce_path(path, method, view)
            view_paths[path].append((method, view))
            view_cls[path] = callback.cls
        return {path: (view_cls[path], methods) for path, methods in view_paths.items()}

    def get_operation_keys(self, subpath, method, view):
        """Return a list of keys that should be used to group an operation within the specification.

        ::

          /users/                   ("users", "list"), ("users", "create")
          /users/{pk}/              ("users", "read"), ("users", "update"), ("users", "delete")
          /users/enabled/           ("users", "enabled")  # custom viewset list action
          /users/{pk}/star/         ("users", "star")     # custom viewset detail action
          /users/{pk}/groups/       ("users", "groups", "list"), ("users", "groups", "create")
          /users/{pk}/groups/{pk}/  ("users", "groups", "read"), ("users", "groups", "update")

        :param str subpath: path to the operation with any common prefix/base path removed
        :param str method: HTTP method
        :param view: the view associated with the operation
        :rtype: tuple
        """
        return self._gen.get_keys(subpath, method, view)

    def get_paths(self, endpoints, components, request=None):
        """Generate the Swagger Paths for the API from the given endpoints.

        :param dict endpoints: endpoints as returned by get_endpoints
        :param ReferenceResolver components: resolver/container for Swagger References
        :param Request request: the request made against the schema view; can be None
        :rtype: openapi.Paths
        """
        if not endpoints:
            return openapi.Paths(paths={})

        prefix = self._gen.determine_path_prefix(endpoints.keys())
        paths = OrderedDict()

        default_schema_cls = SwaggerAutoSchema
        for path, (view_cls, methods) in sorted(endpoints.items()):
            path_parameters = self.get_path_parameters(path, view_cls)
            operations = {}
            for method, view in methods:
                if not self._gen.has_view_permissions(path, method, view):
                    continue

                operation_keys = self.get_operation_keys(path[len(prefix):], method, view)
                overrides = self.get_overrides(view, method)
                auto_schema_cls = overrides.get('auto_schema', default_schema_cls)
                schema = auto_schema_cls(view, path, method, overrides, components, request)
                operations[method.lower()] = schema.get_operation(operation_keys)

            if operations:
                paths[path] = openapi.PathItem(parameters=path_parameters, **operations)

        return openapi.Paths(paths=paths)

    def get_overrides(self, view, method):
        """Get overrides specified for a given operation.

        :param view: the view associated with the operation
        :param str method: HTTP method
        :return: a dictionary containing any overrides set by :func:`@swagger_auto_schema <.swagger_auto_schema>`
        :rtype: dict
        """
        method = method.lower()
        action = getattr(view, 'action', method)
        action_method = getattr(view, action, None)
        overrides = getattr(action_method, 'swagger_auto_schema', {})
        if method in overrides:
            overrides = overrides[method]

        return overrides

    def get_path_parameters(self, path, view_cls):
        """Return a list of Parameter instances corresponding to any templated path variables.

        :param str path: templated request path
        :param type view_cls: the view class associated with the path
        :return: path parameters
        :rtype: list[openapi.Parameter]
        """
        parameters = []
        model = getattr(getattr(view_cls, 'queryset', None), 'model', None)

        for variable in uritemplate.variables(path):
            pattern = None
            type = openapi.TYPE_STRING
            description = None
            if model is not None:
                # Attempt to infer a field description if possible.
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:  # pragma: no cover
                    model_field = None

                if model_field is not None and model_field.help_text:
                    description = force_text(model_field.help_text)
                elif model_field is not None and model_field.primary_key:
                    description = get_pk_description(model, model_field)

                if hasattr(view_cls, 'lookup_value_regex') and getattr(view_cls, 'lookup_field', None) == variable:
                    pattern = view_cls.lookup_value_regex
                elif isinstance(model_field, django.db.models.AutoField):
                    type = openapi.TYPE_INTEGER

            field = openapi.Parameter(
                name=variable,
                required=True,
                in_=openapi.IN_PATH,
                type=type,
                pattern=pattern,
                description=description,
            )
            parameters.append(field)

        return parameters
