# your_app/middleware.py
from django.http import JsonResponse

class CheckUserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_response(self, request, response):
        if request.user:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            if not request.user.status:  
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", request.user.response)
                return JsonResponse(
                    {'detail': 'Your account is blocked.'},
                    status=403
                )
        return response
