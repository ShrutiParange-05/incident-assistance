from src.error_classifier import classify


def test_connection_pool_exhaustion():
    result = classify("Database connection timeout - connection pool exhausted", 500)
    assert result.error_type == "Database Connectivity"
    assert result.probable_cause == "Connection pool exhaustion"
    assert result.severity == "High"


def test_generic_db_timeout():
    result = classify("Query timed out after 30s", 504)
    assert result.error_type == "Database Connectivity"
    assert result.severity == "High"


def test_auth_failure():
    result = classify("Invalid or expired token", 401)
    assert result.error_type == "Authentication/Authorization"
    assert result.severity == "Medium"


def test_rate_limit():
    result = classify("Too many requests from client", 429)
    assert result.error_type == "Rate Limiting"
    assert result.severity == "Low"


def test_validation_error():
    result = classify("Missing required field 'email' in request body", 422)
    assert result.error_type == "Input Validation"


def test_not_found():
    result = classify("User does not exist", 404)
    assert result.error_type == "Resource Not Found"


def test_memory_exhaustion_is_critical():
    result = classify("Process killed: out of memory", 503)
    assert result.error_type == "Resource Exhaustion"
    assert result.severity == "Critical"


def test_unknown_5xx_falls_back_to_server_error():
    result = classify("Something completely unrecognized happened", 500)
    assert result.error_type == "Server Error"


def test_unknown_4xx_falls_back_to_client_error():
    result = classify("Something completely unrecognized happened", 418)
    assert result.error_type == "Client Error"
