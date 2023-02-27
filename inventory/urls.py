from django.conf.urls import url

from inventory import views

urlpatterns = [
    url(r'^$', views.grid, name='grid'),
    url(r'^grid/$', views.grid, name='grid'),
    url(r'^rename/$', views.rename, name='rename'),
]
