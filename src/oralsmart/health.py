from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
@csrf_exempt
def health_check(request):
    """
    Health check endpoint for Docker containers and load balancers.
    Returns JSON response with service status.
    """
    try:
        # Check database connection
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check rule-based risk calculation system
    try:
        from assessments.risk_calculator import get_risk_prediction
        # Test with None values to ensure system works without data
        test_result = get_risk_prediction(None, None)
        risk_system_status = "available" if test_result.get('available', False) else "unavailable"
    except Exception as e:
        logger.error(f"Risk calculation system health check failed: {e}")
        risk_system_status = "error"

    # Check static files directory
    static_status = "available" if os.path.exists('/app/staticfiles') else "unavailable"

    # Check media directory
    media_status = "available" if os.path.exists('/app/media') else "unavailable"

    health_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": "2025-08-27T12:00:00Z",  # You can use timezone.now().isoformat()
        "services": {
            "database": db_status,
            "risk_calculator": risk_system_status,
            "static_files": static_status,
            "media_files": media_status
        }
    }

    status_code = 200 if health_data["status"] == "healthy" else 503
    return JsonResponse(health_data, status=status_code)
