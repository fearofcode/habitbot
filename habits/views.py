from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import F

from django.utils import timezone

from habits.models import Goal, ScheduledInstance, UserProfile
import datetime
import sys


def standard_data(request, error_message=None):
    todo = Goal.goals_for_today(request.user)
    completed = Goal.completed_goals_for_today(request.user)
    tomorrow = Goal.beginning_today(request.user) + datetime.timedelta(days=1)

    return {'skipped': Goal.skipped_goals_for_today(request.user),
            'goals': Goal.objects.filter(user=request.user).select_related('scheduledinstances'),
            'todo': todo,
             'completed': completed,
             'tomorrow': tomorrow,
             'user_tz': request.user.userprofile.timezone,
              'readable_tz': request.user.userprofile.readable(),
             'error_message': error_message}

def home(request):
    """Home view, displays login mechanism"""
    if request.user.is_authenticated():
        return HttpResponseRedirect('done')
    else:
        return render_to_response('home.html', RequestContext(request))


@login_required
def done(request):
    return HttpResponseRedirect('/habits/')

def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'messages': messages},
        RequestContext(request))


def login(request):
    if request.user is not None and request.user.is_active:
        return HttpResponseRedirect('/habits/')
    else:
        return HttpResponseRedirect('/')

def logout(request):
    """Logs out user"""
    auth_logout(request)
    return HttpResponseRedirect('/')


@login_required
def main(request):
    return render_to_response("main.html", standard_data(request),
                                context_instance=RequestContext(request))

@login_required
def completed(request):
    try:
        instance_ids = request.POST.getlist('instance[]')

        for instance_id in instance_ids:
            instance = get_object_or_404(ScheduledInstance, pk = instance_id)

            instance.progress()

            instance.save()

        return HttpResponseRedirect(reverse("habits.views.main"))

    except Exception:
        messages.error(request, "Please choose a goal to complete.")

        return HttpResponseRedirect(reverse("habits.views.main"))

@login_required
def streaks(request):
    print >>sys.stderr, "in streaks"

    return render_to_response("streaks.html", {'goals': Goal.objects.filter(user=request.user).select_related('scheduledinstances'),
                                                'readable_tz': request.user.userprofile.readable()},
        context_instance=RequestContext(request))

@login_required
def edit_streaks(request):
    try:
        instance_ids = request.POST.getlist('complete[]')

        instances = ScheduledInstance.objects.filter(id__in=instance_ids)

        for instance in instances:
            instance.completed = True

            if instance.goal.incremental:
                instance.current_progress = instance.goal.goal_amount

            instance.save()

        instance_ids = request.POST.getlist('skip[]')

        instances = ScheduledInstance.objects.filter(id__in=instance_ids).update(skipped=True)

        return HttpResponseRedirect(reverse("habits.views.streaks"))

    except Exception:
        return HttpResponseRedirect(reverse("habits.views.streaks"))

@login_required
def skip_instance(request, instance_id):
    ScheduledInstance.objects.filter(id=instance_id).update(skipped=True)

    return HttpResponseRedirect(reverse("habits.views.main"))

@login_required
def goals(request):
    return render_to_response("goals.html", {'goals': Goal.objects.filter(user=request.user), 
                                            'user_tz': request.user.userprofile.timezone, 
                                            'readable_tz': request.user.userprofile.readable()},
        context_instance=RequestContext(request))

@login_required
def edit_description(request, goal_id):
    try:
        goal = get_object_or_404(Goal, pk = goal_id)

        goal.description = request.POST['description']
        goal.save()
    except Exception:
        messages.error(request, "Please choose a goal and a new description to update to.")

    return HttpResponseRedirect(reverse("habits.views.main"))

@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk = goal_id)
    goal.delete()

    return HttpResponseRedirect(reverse("habits.views.goals"))

@login_required
def new_goal(request):
    error_message = None

    try:
        goal_text = request.POST['goal_text']

        g = Goal()

        g.user = request.user

        try:
            g.parse(goal_text)

        except Exception:
            messages.error(request, "Invalid goal. Please enter a correctly formatted goal.")

            return HttpResponseRedirect(reverse("habits.views.main"))

        g.save()
        g.create_scheduled_instances(timezone.now(), 5)

        return HttpResponseRedirect(reverse("habits.views.main"))

    except KeyError:
        error_message = "Please enter a valid goal"
        return render_to_response("main.html", standard_data(request, error_message),
            context_instance=RequestContext(request))
