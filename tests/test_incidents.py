def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_incident(client):
    payload = {
        "service": "payment-api",
        "error_code": 500,
        "message": "Database connection timeout",
    }
    resp = client.post("/incidents", json=payload)
    assert resp.status_code == 201

    body = resp.json()
    assert body["service"] == "payment-api"
    assert body["error_code"] == 500
    assert body["error_type"] == "Database Connectivity"
    assert body["severity"] in {"High", "Critical"}
    assert body["recommended_action"]  # non-empty
    assert "id" in body


def test_create_incident_missing_field_returns_422(client):
    resp = client.post("/incidents", json={"service": "payment-api"})
    assert resp.status_code == 422


def test_list_incidents(client):
    client.post(
        "/incidents",
        json={"service": "auth-service", "error_code": 401, "message": "Invalid token"},
    )
    client.post(
        "/incidents",
        json={"service": "payment-api", "error_code": 500, "message": "connection pool exhausted"},
    )

    resp = client.get("/incidents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_incidents_filter_by_service(client):
    client.post(
        "/incidents",
        json={"service": "auth-service", "error_code": 401, "message": "Invalid token"},
    )
    client.post(
        "/incidents",
        json={"service": "payment-api", "error_code": 500, "message": "timeout"},
    )

    resp = client.get("/incidents", params={"service": "auth-service"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["service"] == "auth-service"


def test_get_single_incident(client):
    create_resp = client.post(
        "/incidents",
        json={"service": "orders-api", "error_code": 404, "message": "Order not found"},
    )
    incident_id = create_resp.json()["id"]

    resp = client.get(f"/incidents/{incident_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == incident_id


def test_get_nonexistent_incident_returns_404(client):
    resp = client.get("/incidents/999999")
    assert resp.status_code == 404


def test_dashboard_summary(client):
    client.post(
        "/incidents",
        json={"service": "payment-api", "error_code": 500, "message": "connection pool exhausted"},
    )
    resp = client.get("/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_incidents"] >= 1
    assert "by_severity" in body
    assert "recent" in body
