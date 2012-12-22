from django.db import models

import datetime
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
    frequency = models.CharField(max_length=50)
    byday = models.CharField(max_length=50, null=True, blank=true)
    interval = models.IntegerField()

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

        self.rrule = recurring_event.get_RFC_rrule()

        params = recurring_event.get_params()

        self.dtstart = params['dtstart'] if params.has_key('dtstart') else datetime.date.today()
        self.frequency = params['freq']
        self.byday = params['byday'] if params.has_key('byday') else None
        self.interval = params['interval']

    def __unicode__(self):
        return self.creation_text

