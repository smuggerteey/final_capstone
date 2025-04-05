def test_login(client):
    response = client.post('/login', data={
        'username': 'test',
        'password': 'test'
    })
    assert response.status_code == 302