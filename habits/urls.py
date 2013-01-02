from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'habits.views.main'),
    url(r'edit_description/(?P<goal_id>\d+)/$', 'habits.views.edit_description'),
    url(r'completed/$', 'habits.views.completed'),
    url(r'^streaks/$', 'habits.views.streaks'),
    url(r'edit_streaks/$', 'habits.views.edit_streaks'),
    url(r'skip/(?P<instance_id>\d+)/$', 'habits.views.skip_instance'),
    url(r'goals/$', 'habits.views.goals'),
    url(r'new_goal/$', 'habits.views.new_goal'),
    url(r'delete_goal/(?P<goal_id>\d+)/$', 'habits.views.delete_goal'),
)
