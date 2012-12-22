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


        # TODO complain if shorter than daily, catch ValueError

    def last_completion(self):
        last = None

        try:
            return self.instance_set.order_by('created_at')[0]
        except IndexError:
            return None

    def next_datetime(self):
        last = self.last_completion()

        if not last:
            return Instance(goal=self, created_at=self.dtstart)
        else:
            rr = rrule.rrulestr(self.rrule)
            dt = datetime.datetime(last.created_at.year,
                                    last.created_at.month,
                                    last.created_at.day)

            after = rr.after(dt).date()
            return Instance(goal=self, created_at=after)


    def __unicode__(self):
        return self.creation_text

class Instance(models.Model):
    goal = models.ForeignKey(Goal)
    created_at = models.DateField()

    def __unicode__(self):
        return str(self.created_at)

