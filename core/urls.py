from django.urls import path
from .views import test_api, signup, login_view, logout_view, regenerate_api_key

urlpatterns = [
    path('test/', test_api),
    path('signup/', signup),
    path('login/', login_view),
    path('logout/', logout_view),
    path('regenerate-key/', regenerate_api_key),
]