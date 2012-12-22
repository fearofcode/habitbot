from django.shortcuts import render_to_response
from habits.models import Goal

def home(request):
    return render_to_response("home.html")

def main(request):
    goals = Goal.objects.all()

    return render_to_response("main.html", {'goals': goals})

def new_goal(request):
    try:
        goal_text = request.POST['goal_text']
        from recurrent import RecurringEvent

        r = RecurringEvent()

        r.parse(goal_text)

        # TODO
    except KeyError:
        error = "Please enter a valid goal"