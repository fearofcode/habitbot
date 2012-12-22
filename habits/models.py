from django.db import models

from recurrent import RecurringEvent

class Goal(models.Model):
    EVERY = "every"

    created_at = models.DateField(auto_now_add=True)

    creation_text = models.CharField(max_length=200) # for debugging in case i fuck this up

    description = models.CharField(max_length=50)
    recurring = models.BooleanField(default=True)
    rrule = models.CharField(max_length=200, null=True, blank=True)
    dtstart = models.DateField()
    frequency = models.CharField(max_length=50, null=True, blank=True)

    def parse(self, goal_text):
        index = goal_text.find(self.EVERY)

        self.description = goal_text[:index].strip()

    def __unicode__(self):
        return self.creation_text

