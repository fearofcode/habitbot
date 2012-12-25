from django.db import models

import itertools
import datetime
from dateutil import rrule
from recurrent import RecurringEvent
from django.contrib.auth.models import User

from django.db import IntegrityError

class InvalidInput(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Goal(models.Model):
    EVERY = "every"

    user = models.ForeignKey(User)
    created_at = models.DateField(auto_now_add=True)

    creation_text = models.CharField(max_length=200) # for debugging in case i fuck this up
    description = models.CharField(max_length=50)
    rrule = models.CharField(max_length=200)
    dtstart = models.DateField()

    def parse(self, goal_text):
        self.creation_text = goal_text

        index = goal_text.find(self.EVERY)

        if index == -1:
            raise InvalidInput("Could not find the word '%s' in input" % self.EVERY)

        self.description = goal_text[:index].strip()

        recurring_event = RecurringEvent()

        result = None

        try:
            result = recurring_event.parse(self.creation_text)
        except ValueError:
            raise InvalidInput("Not a recurring rule or not valid input")

        if type(result) != type('str'):
            raise InvalidInput("Not a recurring rule or not valid input")

        params = recurring_event.get_params()

        if params['freq'] in ['hourly', 'minutely', 'secondly']:
            raise InvalidInput("Not a recurring rule or not valid input")

        self.dtstart = datetime.datetime.strptime(params['dtstart'], "%Y%m%d").date() if params.has_key('dtstart')\
            else datetime.date.today()

        self.rrule = recurring_event.get_RFC_rrule()

        if not self.rrule.startswith("DTSTART:"):
            self.rrule = "DTSTART:" + self.dtstart.strftime("%Y%m%d") + "\n" + self.rrule

    def generate_next_scheduled_instances(self, start, n):
        rr = rrule.rrulestr(self.rrule)

        datetimes = []

        for i in range(0, n):
            if len(datetimes) == 0:
                last_date = datetime.datetime(start.year, start.month, start.day) - datetime.timedelta(days=1)
            else:
                last_date = datetimes[-1]

            datetimes.append(rr.after(last_date))

        return [dt.date() for dt in datetimes]

    def create_scheduled_instances(self, start, n):
        dates = self.generate_next_scheduled_instances(start, n)
        instances = [ScheduledInstance(goal=self, date=d) for d in dates]

        for instance in instances:
            try:
                instance.save()
            except IntegrityError:
                pass

    @classmethod
    def create_all_scheduled_instances(self, start, n):
        for goal in Goal.objects.all():
            goal.create_scheduled_instances(start, n)

    @classmethod
    def completed_goals_for_today_by_type(self, user, completed):
        instances = [goal.scheduledinstance_set.filter(date=datetime.date.today(), completed=completed) for
                     goal in Goal.objects.filter(user=user)]
        return list(itertools.chain.from_iterable(instances))

    @classmethod
    def completed_goals_for_today(self, user):
        return self.completed_goals_for_today_by_type(user, True)

    @classmethod
    def goals_for_today(self, user):
        return self.completed_goals_for_today_by_type(user, False)

    def current_streak(self):
        today = datetime.date.today()

        previous_instances = self.scheduledinstance_set.filter(date__lte=today).order_by('-date')

        streak = 0

        for instance in previous_instances:
            if instance.completed:
                streak += 1
            elif instance.date != today:
                break

        return streak

    def __unicode__(self):
        return ", ".join(["creation_text=" + self.creation_text,
                            "created_at=" + str(self.created_at),
                            "description=" + self.description,
                            "rrule=" + self.rrule,
                            "dtstart=" + str(self.dtstart),
                            "user=" + str(self.user)],
                        )

class ScheduledInstance(models.Model):
    goal = models.ForeignKey(Goal)
    date = models.DateField()
    completed = models.BooleanField(default=False)

    def __unicode__(self):
        return ", ".join(["goal = " + self.goal.creation_text,
                          "date = " + str(self.date),
                          "completed = " + str(self.completed)])

    class Meta:
        unique_together = (("goal", "date"),)