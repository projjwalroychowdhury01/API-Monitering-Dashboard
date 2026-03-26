from app.db.clickhouse_client import get_client

def get_endpoint_metrics(endpoint_id: str, time_range_minutes: int) -> dict:
    client = get_client()
    
    query = """
        SELECT 
            avg(p50) as p50,
            avg(p95) as p95,
            avg(p99) as p99,
            sum(request_count) as request_count,
            avg(error_rate) as error_rate
        FROM metrics_1m
        WHERE endpoint_id = %(endpoint_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
    """
    
    params = {
        'endpoint_id': endpoint_id,
        'minutes': time_range_minutes
    }
    
    result = client.execute(query, params)
    
    if result and result[0]:
        row = result[0]
        return {
            "p50": float(row[0] or 0.0),
            "p95": float(row[1] or 0.0),
            "p99": float(row[2] or 0.0),
            "request_count": int(row[3] or 0),
            "error_rate": float(row[4] or 0.0)
        }
        
    return {
        "p50": 0.0,
        "p95": 0.0,
        "p99": 0.0,
        "request_count": 0,
        "error_rate": 0.0
    }
