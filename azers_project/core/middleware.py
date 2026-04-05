# middleware.py
from django.shortcuts import redirect
from django.contrib import messages

class ApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.is_approved:
                allowed_urls = ['/logout/', '/profile/']  # they can only see profile/logout
                if request.path not in allowed_urls:
                    messages.warning(request, "Your account is awaiting admin approval.")
                    return redirect('profile')
        return self.get_response(request)
