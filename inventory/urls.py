from django.conf.urls import url

from inventory import views

urlpatterns = [
    url(r'^$', views.grid, name='grid'),
    url(r'^grid/$', views.grid, name='grid'),
    url(r'^rename/$', views.rename, name='rename'),
    url(r'^photos/$', views.photos, name='photos'),
    #url(r'^create_init_component_breadcrumbs/$', views.create_init_component_breadcrumbs, name='create_init_component_breadcrumbs'),
    #url(r'^create_init_computer_breadcrumbs/$', views.create_init_computer_breadcrumbs, name='create_init_computer_breadcrumbs'),
]
