# chatbot/middleware.py

import sentry_sdk

class SentryErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request normally
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Automatically catch ANY error and send to Sentry"""
        
        # Send error to Sentry
        sentry_sdk.capture_exception(exception)
        
        # Add context to help debugging
        sentry_sdk.set_context("request_details", {
            "method": request.method,
            "path": request.path,
            "user": str(request.user) if request.user.is_authenticated else "Anonymous",
            "GET_params": dict(request.GET),
            "POST_params": dict(request.POST) if request.method == "POST" else {},
        })
        
        # Don't modify the response - let Django handle it
        return None