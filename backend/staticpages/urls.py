from django.urls import path

from staticpages.views import about, technologies

urlpatterns = [
    path('about/', about, name='about'),
    path('technologies/', technologies, name='technologies'),
]
