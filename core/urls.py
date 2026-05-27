from django.urls import path
from .views import test_api, signup, login_view, logout_view, regenerate_api_key, upgrade_plan

urlpatterns = [
    path('test/', test_api),
    path('signup/', signup),
    path('login/', login_view),
    path('logout/', logout_view),
    path('upgrade-plan/', upgrade_plan),
    path('regenerate-key/', regenerate_api_key),
]