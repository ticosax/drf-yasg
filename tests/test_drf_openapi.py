from drf_yasg.codecs import yaml_sane_load


def test_versioned_endpoints(client):
    response = client.get('/versioned/v2.0/swagger.yaml')
    assert response.status_code == 200
    swagger = yaml_sane_load(response.content.decode('utf-8'))
    assert '/versioned/v2.0/snippets/' in swagger['paths']
    versioned_get = swagger['paths']['/versioned/v2.0/snippets/']['get']
    assert 'v2field' in versioned_get['responses']['200']['schema']['properties']


def test_response_validation(client):
    response = client.get('/versioned/v2.0/snippets/')
    assert response.status_code == 400
