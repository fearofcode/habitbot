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
        result = recurring_event.parse(self.creation_text)

        if type(result) != type('str'):
            raise InvalidInput("Not a recurring rule or not valid input")

        params = recurring_event.get_params()
        self.dtstart = datetime.datetime.strptime(params['dtstart'], "%Y%m%d").date() if params.has_key('dtstart')\
            else datetime.date.today()

        self.rrule = recurring_event.get_RFC_rrule()

        if not self.rrule.startswith("DTSTART:"):
            self.rrule = "DTSTART:" + self.dtstart.strftime("%Y%m%d") + "\n" + self.rrule


        # TODO complain if shorter than daily, catch ValueError

    def next_datetime(self):
        last_completion = None

        try:
            last_completion = self.completion_set.order_by('created_at')[0]
            print "last_completion = ", last_completion
        except IndexError:
            return self.dtstart

        if not last_completion:
            return self.dtstart
        else:
            rr = rrule.rrulestr(self.rrule)
            dt = datetime.datetime(last_completion.created_at.year,
                                    last_completion.created_at.month,
                                    last_completion.created_at.day)

            print "rrule = ", self.rrule
            print "dt = ", dt
            print "rr.after(dt)", rr.after(dt)

            return rr.after(dt).date()


    def __unicode__(self):
        return self.creation_text

class Completion(models.Model):
    goal = models.ForeignKey(Goal)
    created_at = models.DateField()

    def __unicode__(self):
        return str(self.created_at)

