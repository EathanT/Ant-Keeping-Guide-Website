from django.contrib import admin
from django.urls import path, include
from guide import views as guide_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("server_info/", guide_views.server_info, name="server_info"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include(("guide.urls", "guide"), namespace="guide")),
]
