from django.conf.urls import patterns, include, url
from habits.views import home, done, logout, error

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from habits.models import Goal

admin.site.register(Goal)

urlpatterns = patterns('',
    url(r'', include('social_auth.urls')),
    url(r'^$', home, name='home'),
    url(r'^done/$', done, name='done'),
    url(r'^error/$', error, name='error'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^habits/', include('habits.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
