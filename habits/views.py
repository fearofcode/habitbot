from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from habits.models import Goal, Instance
import datetime

def home(request):
    return render_to_response("home.html")

def main(request):
    goals = Goal.objects.all()

    instances = Goal.get_current_goals(goals)
    completed_goals = Instance.get_completed_goals()

    return render_to_response("main.html", {'goals': goals,
                                            'instances': instances,
                                            'completed_goals': completed_goals},
                                context_instance=RequestContext(request))

def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk = goal_id)
    goal.delete()

    return HttpResponseRedirect(reverse("habits.views.main"))

def completed(request):
    goals = Goal.objects.all()
    instances = Goal.get_current_goals(goals)
    completed_goals = Instance.get_completed_goals()

    try:
        goal_id = request.POST['goal']

        goal = get_object_or_404(Goal, pk = goal_id)

        goal.instance_set.create(created_at=datetime.date.today(), done=True)

        return HttpResponseRedirect(reverse("habits.views.main"))

    except KeyError:

        return render_to_response("main.html", {'goals': goals,
                                                'instances': instances,
                                                'completed_goals': completed_goals,
                                                'error_message': 'Please select a valid goal to complete'},
            context_instance=RequestContext(request))

def new_goal(request):
    error_message = None
    goals = Goal.objects.all()
    instances = Goal.get_current_goals(goals)
    completed_goals = Instance.get_completed_goals()
    
    try:
        goal_text = request.POST['goal_text']

        g = Goal()

        try:
            g.parse(goal_text)

        except Exception:
            error_message = "Invalid goal. Please enter a correctly formatted goal."
            return render_to_response("main.html", {'goals': goals, 'error_message': error_message},
                context_instance=RequestContext(request))

        g.save()

        return HttpResponseRedirect(reverse("habits.views.main"))

    except KeyError:
        error_message = "Please enter a valid goal"
        return render_to_response("main.html", {'goals': goals, 'error_message': error_message},
            context_instance=RequestContext(request))