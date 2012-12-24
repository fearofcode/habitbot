from django.db import models

import datetime
from dateutil import rrule
from recurrent import RecurringEvent

class InvalidInput(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Goal(models.Model):
    EVERY = "every"

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

    def last_completion(self):
        last = None

        try:
            return self.instance_set.order_by('created_at')[0]
        except IndexError:
            return None

    def next_instance_after_date(self, last):
        rr = rrule.rrulestr(self.rrule)
        dt = datetime.datetime(last.year, last.month, last.day)
        return rr.after(dt).date()

    def next_date(self):
        last = self.last_completion()

        today = datetime.date.today()

        if not last:
            return max(self.dtstart, today)
        else:
            return max(self.next_instance_after_date(last.created_at), today)

    @classmethod
    def get_current_goals(self, goals):
        today = datetime.date.today()
        return filter(lambda goal: goal.next_date() == today, goals)

    def __unicode__(self):
        return ", ".join(["creation_text=" + self.creation_text, "created_at=" + str(self.created_at),
                "description=" + self.description, "rrule=" + self.rrule, "dtstart=" + str(self.dtstart)])

class Instance(models.Model):
    goal = models.ForeignKey(Goal)
    created_at = models.DateField()
    done = models.BooleanField(default=False)

    def compute_due_at(self):
        return self.goal.next_instance_after_date(self.created_at)

    def __unicode__(self):
        return ", ".join(["goal=<" + str(self.goal) + ">", "created_at=" + str(self.created_at)])

    @classmethod
    def get_completed_goals(self):
        return Instance.objects.filter(done=True, created_at=datetime.date.today())

