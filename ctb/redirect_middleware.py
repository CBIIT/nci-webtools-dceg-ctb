from os import getenv
from socket import gethostname, gethostbyname
from django.shortcuts import redirect

class RedirectMiddleware:
    """Middleware to redirect to the correct host"""

    def __init__(self, get_response):
        self.get_response = get_response
        # Define the allowed host and excluded hosts
        self.target_host = getenv("ALLOWED_HOST", "").split(",")[0]
        self.excluded_hosts = {
            "localhost",
            "127.0.0.1",
            "[::1]",
            gethostname(),
            gethostbyname(gethostname),
        }

    def __call__(self, request):
        # Extract host without port
        current_host = request.get_host().split(":")[0]

        # Determine the protocol based on the request
        protocol = "https" if request.is_secure() else "http"

        # Redirect if the host is incorrect and not in excluded hosts
        if current_host != self.target_host and current_host not in self.excluded_hosts:
            original_path = request.get_full_path()
            return redirect(f"{protocol}://{self.target_host}{original_path}")

        # Otherwise, continue with the request
        return self.get_response(request)
