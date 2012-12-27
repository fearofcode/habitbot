from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages

from habits.models import Goal, ScheduledInstance
import datetime


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
    goals = Goal.objects.filter(user=request.user)
    todo = Goal.goals_for_today(request.user)
    completed = Goal.completed_goals_for_today(request.user)

    return render_to_response("main.html", {'goals': goals,
                                            'todo': todo,
                                            'completed': completed},
                                context_instance=RequestContext(request))

@login_required
def completed(request):
    goals = Goal.objects.all()
    todo = Goal.goals_for_today(request.user)
    completed = Goal.completed_goals_for_today(request.user)

    try:
        instance_ids = request.POST.getlist('instance[]')

        for instance_id in instance_ids:
            instance = get_object_or_404(ScheduledInstance, pk = instance_id)

            instance.completed=True

            instance.save()

        return HttpResponseRedirect(reverse("habits.views.main"))

    except Exception:
        messages.error(request, "Please choose a goal to complete.")

        return HttpResponseRedirect(reverse("habits.views.main"))
    
@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk = goal_id)
    goal.delete()

    return HttpResponseRedirect(reverse("habits.views.main"))

@login_required
def new_goal(request):
    error_message = None
    goals = Goal.objects.filter(user=request.user)
    todo = Goal.goals_for_today(request.user)
    completed = Goal.completed_goals_for_today(request.user)

    try:
        goal_text = request.POST['goal_text']

        g = Goal()

        try:
            g.parse(goal_text)

        except Exception:
            messages.error(request, "Invalid goal. Please enter a correctly formatted goal.")

            return HttpResponseRedirect(reverse("habits.views.main"))

        g.user = request.user
        g.save()
        g.create_scheduled_instances(datetime.date.today(), 5)

        return HttpResponseRedirect(reverse("habits.views.main"))

    except KeyError:
        error_message = "Please enter a valid goal"
        return render_to_response("main.html", {'goals': goals,
                                                'todo': todo,
                                                'completed': completed,
                                                'error_message': error_message},
            context_instance=RequestContext(request))