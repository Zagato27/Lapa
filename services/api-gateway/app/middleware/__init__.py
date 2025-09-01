"""
Middleware для API Gateway
"""

from .auth import AuthMiddleware
__all__ = ["AuthMiddleware"]
