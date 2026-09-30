from unittest import mock

import pytest
from django.db.utils import OperationalError


@pytest.mark.django_db
def test_health_ok(client):
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'database': 'ok'}


@pytest.mark.django_db
def test_health_database_unavailable(client):
    with mock.patch('gutenberg.views.connection.cursor', side_effect=OperationalError):
        response = client.get('/health/')
    assert response.status_code == 503
    assert response.json()['status'] == 'error'
