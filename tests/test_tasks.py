def register_and_login(client, username):
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        data={
            "username": username,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_task(client):
    # ARRANGE
    headers = register_and_login(
        client,
        "alice"
    )

    # ACT
    response = client.post(
        "/tasks/",
        json={
            "title": "Write tests",
            "description": "Test the task API",
            "completed": False,
        },
        headers=headers,
    )

    # ASSERT
    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Write tests"
    assert data["description"] == "Test the task API"
    assert data["completed"] is False
    assert "id" in data


def test_list_tasks(client):
    # ARRANGE
    headers = register_and_login(
        client,
        "alice"
    )

    client.post(
        "/tasks/",
        json={
            "title": "Task one"
        },
        headers=headers,
    )

    # ACT
    response = client.get(
        "/tasks/",
        headers=headers,
    )

    # ASSERT
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Task one"


def test_get_task(client):
    # ARRANGE
    headers = register_and_login(
        client,
        "alice"
    )

    created = client.post(
        "/tasks/",
        json={
            "title": "Private task"
        },
        headers=headers,
    )

    task_id = created.json()["id"]

    # ACT
    response = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    # ASSERT
    assert response.status_code == 200
    assert response.json()["title"] == "Private task"


def test_authentication_required(client):
    # ACT
    response = client.get(
        "/tasks/"
    )

    # ASSERT
    assert response.status_code == 401


def test_task_ownership(client):
    # ARRANGE
    alice_headers = register_and_login(
        client,
        "alice"
    )

    bob_headers = register_and_login(
        client,
        "bobby"
    )

    created = client.post(
        "/tasks/",
        json={
            "title": "Alice private task"
        },
        headers=alice_headers,
    )

    task_id = created.json()["id"]

    # ACT + ASSERT
    alice_response = client.get(
        f"/tasks/{task_id}",
        headers=alice_headers,
    )

    assert alice_response.status_code == 200

    bob_response = client.get(
        f"/tasks/{task_id}",
        headers=bob_headers,
    )

    assert bob_response.status_code == 404

    bob_patch = client.patch(
        f"/tasks/{task_id}",
        json={
            "title": "Changed"
        },
        headers=bob_headers,
    )

    assert bob_patch.status_code == 404

    bob_delete = client.delete(
        f"/tasks/{task_id}",
        headers=bob_headers,
    )

    assert bob_delete.status_code == 404


def test_duplicate_username_returns_409(client):
    # ARRANGE
    first = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
        },
    )

    assert first.status_code == 201

    # ACT
    second = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "different@example.com",
            "password": "password123",
        },
    )

    # ASSERT
    assert second.status_code == 409


def test_task_notification(client, capsys):
    # ARRANGE
    headers = register_and_login(
        client,
        "notifyuser"
    )

    # ACT
    response = client.post(
        "/tasks/",
        json={
            "title": "Write tests"
        },
        headers=headers,
    )

    # ASSERT
    assert response.status_code == 201

    task = response.json()

    output = capsys.readouterr().out

    assert (
        f"Task {task['id']} created: Write tests"
        in output
    )