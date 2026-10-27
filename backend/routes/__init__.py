"""Core API Route Blueprints for uploads, image/fusion processing, results, and chat."""

try:
    from backend.routes.upload_routes import upload_bp
    from backend.routes.processing_routes import processing_bp
    from backend.routes.results_routes import results_bp
except ImportError:
    from routes.upload_routes import upload_bp
    from routes.processing_routes import processing_bp
    from routes.results_routes import results_bp

__all__ = ["upload_bp", "processing_bp", "results_bp"]
