import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login(client):
    response = client.post('/login', data={
        'username': 'cicada',
        'password': '57sfafgh@As6t'
    })
    assert response.status_code == 302