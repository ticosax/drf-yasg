import inspect
from functools import wraps

from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from drf_yasg.inspectors import InlineSerializerInspector, SwaggerAutoSchema, force_serializer_instance
from .utils import swagger_auto_schema


def get_meta_responses(serializer):
    """Get responses declared in a serializer's ``Meta`` nested class.

    :param type[VersionedSerializers],type[BaseSerializer] serializer: serializer class
    :rtype: dict
    """
    Meta = getattr(serializer, 'Meta', None)
    return getattr(Meta, 'error_status_codes', {})


def get_versioned(serializer, version):
    """Resolve ``VersionedSerializers`` to a regular serializer according to `version`.

    :param type[VersionedSerializers],type[BaseSerializer] serializer: serializer class
    :param str version: the version to check against
    :rtype: type[BaseSerializer]
    """
    if serializer is not None and hasattr(serializer, 'VERSION_MAP'):
        # drf_openapi VersionedSerializer
        serializer = serializer.get(version)

    return serializer


def get_serializer_doc(serializer):
    """Copied from ``drf_openapi``. Get the docstring from a serializer class.

    :param type serializer:
    :rtype: str
    """
    if serializer is None or serializer.__doc__ is None:
        return ''

    doc = []
    for line in serializer.__doc__.splitlines():
        doc.append(line.strip())
    return '\n'.join(doc)


def inherit_base_serializer(serializer_class):
    """Ensure that the given serializer type inherits from ``BaseSerializer``; if it does not, create and return
    a new type inheriting from `serializer_class` and ``BaseSerializer``.

    :param type serializer_class: the serializer class
    :rtype: type[BaseSerializer]
    """
    if serializer_class is None:
        return None
    if not issubclass(serializer_class, BaseSerializer):
        serializer_class = type(serializer_class.__name__, (serializer_class, BaseSerializer), {
            '__doc__': serializer_class.__doc__
        })
    return serializer_class


def view_config(request_serializer=None, response_serializer=None, validate_response=False):
    """``view_config`` decorator from ``drf_openapi`` implemented with a ``drf_yasg`` backend.

    :param type request_serializer: request serializer as expected by ``drf_openapi``
    :param type response_serializer: response serializer as expected by ``drf_openapi``
    :param bool validate_response: whether to validate the response returned by the decorated view
        against ``response_serializer``
    """
    if request_serializer is not None:  # pragma: no cover
        assert inspect.isclass(request_serializer), "request_serializer must be a serializer class, not an instance"
    if response_serializer is not None:  # pragma: no cover
        assert inspect.isclass(response_serializer), "response_serializer must be a serializer class, not an instance"
    request_serializer = inherit_base_serializer(request_serializer)
    response_serializer = inherit_base_serializer(response_serializer)

    def decorator(view_method):
        responses = {200: response_serializer}

        request_doc = get_serializer_doc(request_serializer)
        response_doc = get_serializer_doc(response_serializer)
        description = ''
        if request_doc:
            description += '\n\n**Request Description:**\n' + request_doc
        if response_doc:
            description += '\n\n**Response Description:**\n' + response_doc

        sas_decorator = swagger_auto_schema(
            request_body=request_serializer,
            responses=responses,
            drf_openapi_description=description,
            drf_openapi_response_serializer=response_serializer,
        )

        @wraps(view_method)
        def wrapper(self, request, version='', *args, **kwargs):
            self.request_serializer = get_versioned(request_serializer, version)
            self.response_serializer = get_versioned(response_serializer, version)

            kwargs.update({'version': version})
            response = view_method(self, request, *args, **kwargs)

            if validate_response:
                many = isinstance(response.data, (list, tuple))
                response_validator = self.response_serializer(data=response.data, many=many)
                response_validator.is_valid(raise_exception=True)
                response = Response(response_validator.validated_data, status=response.status_code)

            del self.request_serializer
            del self.response_serializer
            return response

        wrapper = sas_decorator(wrapper)
        return wrapper

    return decorator


class DrfOpenAPICompatInspector(InlineSerializerInspector):
    """Provides conversions for ``drf_openapi`` ``VersionedSerializers``."""

    def get_versioned_instance(self, serializer):
        serializer = get_versioned(serializer, getattr(self.request, 'version', '') or '')
        return force_serializer_instance(serializer)

    def get_request_parameters(self, serializer, in_):
        if not hasattr(serializer, 'VERSION_MAP'):
            return None

        serializer = self.get_versioned_instance(serializer)
        return super(DrfOpenAPICompatInspector, self).get_request_parameters(serializer, in_)

    def get_schema(self, serializer):
        if not hasattr(serializer, 'VERSION_MAP'):
            return None

        serializer = self.get_versioned_instance(serializer)
        return super(DrfOpenAPICompatInspector, self).get_schema(serializer)


SwaggerAutoSchema.serializer_inspectors.insert(0, DrfOpenAPICompatInspector)

# implement the following methods as monkey patches in order to disturb the rest of the code as little as possible
_real_get_description = SwaggerAutoSchema.get_description
_real_get_response_serializers = SwaggerAutoSchema.get_response_serializers


def _append_openapi_description(self):
    description = _real_get_description(self)
    drf_openapi_description = self.overrides.get('drf_openapi_description', '')
    if drf_openapi_description:
        description += drf_openapi_description

    return description


def _add_meta_responses(self):
    response_serializers = _real_get_response_serializers(self)
    drf_openapi_response_serializer = self.overrides.get('drf_openapi_response_serializer', None)
    if drf_openapi_response_serializer:
        real_serializer = get_versioned(drf_openapi_response_serializer, getattr(self.request, 'version', '') or '')
        response_serializers.update(get_meta_responses(real_serializer))

    return response_serializers


SwaggerAutoSchema.get_description = _append_openapi_description
SwaggerAutoSchema.get_response_serializers = _add_meta_responses
