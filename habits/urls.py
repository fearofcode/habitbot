from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'habits.views.main'),
    url(r'new_goal/$', 'habits.views.new_goal'),
    url(r'delete_goal/(?P<goal_id>\d+)/$', 'habits.views.delete_goal'),
)
