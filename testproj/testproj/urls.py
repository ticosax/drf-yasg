from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import permissions, versioning
from rest_framework.decorators import api_view

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

SchemaView = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    validators=['ssv', 'flex'],
    public=True,
    permission_classes=(permissions.AllowAny,),
)


@api_view(['GET'])
def plain_view(request):
    pass


VERSION_PREFIX = r"^versioned/v(?P<version>1.0|2.0)/"


class VersionedSchemaView(SchemaView):
    versioning_class = versioning.URLPathVersioning


urlpatterns = [
    url(r'^swagger(?P<format>.json|.yaml)$', SchemaView.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', SchemaView.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', SchemaView.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^cached/swagger(?P<format>.json|.yaml)$', SchemaView.without_ui(cache_timeout=None), name='cschema-json'),
    url(r'^cached/swagger/$', SchemaView.with_ui('swagger', cache_timeout=None), name='cschema-swagger-ui'),
    url(r'^cached/redoc/$', SchemaView.with_ui('redoc', cache_timeout=None), name='cschema-redoc'),

    url(r'^admin/', admin.site.urls),
    url(r'^snippets/', include('snippets.urls')),
    url(r'^articles/', include('articles.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^plain/', plain_view),

    url(VERSION_PREFIX + 'snippets/', include('snippets.drf_openapi_urls')),
    url(VERSION_PREFIX + r'swagger(?P<format>.json|.yaml)$', VersionedSchemaView.without_ui(), name='vschema-json'),
    url(VERSION_PREFIX + r'swagger/$', VersionedSchemaView.with_ui('swagger'), name='vschema-swagger-ui'),
    url(VERSION_PREFIX + r'redoc/$', VersionedSchemaView.with_ui('redoc'), name='vschema-redoc'),
]
