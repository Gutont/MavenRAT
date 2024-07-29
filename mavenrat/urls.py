from django.contrib import admin
from django.urls import path
from .views import Builder, Delivery, builder_download
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('builder/', Builder, name='builder'),
    path('delivery/', Delivery, name='delivery'),
    path('download/', builder_download, name='builder_download'),
]


urlpatterns += staticfiles_urlpatterns()