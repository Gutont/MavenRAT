from django.contrib import admin
from django.urls import path
from .views import Builder, Delivery, builder_download

urlpatterns = [
    path('admin/', admin.site.urls),
    path('builder/', Builder, name='builder'),
    path('delivery/', Delivery, name='delivery'),
    path('download/', builder_download, name='builder_download'),
]
