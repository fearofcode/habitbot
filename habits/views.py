from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from habits.models import Goal

def home(request):
    return render_to_response("home.html")

def main(request):
    goals = Goal.objects.all()

    instances = Goal.get_current_instances(goals)

    return render_to_response("main.html", {'goals': goals, 'instances': instances}, context_instance=RequestContext(request))

def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk = goal_id)
    goal.delete()

    return HttpResponseRedirect(reverse("habits.views.main"))

def new_goal(request):
    error_message = None
    goals = Goal.objects.all()

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