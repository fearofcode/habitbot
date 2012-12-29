from django.db import models

import itertools
import datetime
import sys
import re
import string

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

    number_words = { 'one':   1, 'eleven':     11,
                 'two':   2, 'twelve':     12,
                 'three': 3, 'thirteen':   13,
                 'four':  4, 'fourteen':   14,
                 'five':  5, 'fifteen':    15,
                 'six':   6, 'sixteen':    16,
                 'seven': 7, 'seventeen':  17,
                 'eight': 8, 'eighteen':   18,
                 'nine':  9, 'nineteen':   19,
                 'ten':     10,
                 'twenty':  20,
                 'thirty':  30,
                 'forty':   40,
                 'fifty':   50,
                 'sixty':   60,
                 'seventy': 70,
                 'eighty':  80,
                 'ninety':  90 }

    user = models.ForeignKey(User)
    created_at = models.DateField(auto_now_add=True)

    creation_text = models.CharField(max_length=200) # for debugging in case i fuck this up
    description = models.CharField(max_length=50)
    rrule = models.CharField(max_length=200)
    dtstart = models.DateField()
    freq = models.CharField(max_length=100, null=True, blank=True)
    byday = models.CharField(max_length=100, null=True, blank=True)

    incremental = models.BooleanField(default=False)
    goal_amount = models.IntegerField(default=0)

    def incremental_parse(self, description):
        description_words = description.split()

        last_word = description_words[-1]

        num = None

        if re.match("(\d+)x", last_word):
            num = int(re.match("(\d+)x", last_word).groups(0)[0])
        elif len(description_words) >= 2 and last_word == "times":
            next_to_last_word = description_words[-2]
            if re.match("\d+" , next_to_last_word):
                num = int(re.match("(\d+)" , next_to_last_word).groups(0)[0])
            elif next_to_last_word in self.number_words.keys():
                num = self.number_words[next_to_last_word]
                
        if num is not None and num < 1:
            raise InvalidInput("Cannot do something 0 times")

        return num

    def parse(self, goal_text):
        goal_text = goal_text.rstrip(string.punctuation)

        self.creation_text = goal_text

        index = goal_text.find(self.EVERY)

        if index == -1:
            raise InvalidInput("Could not find the word '%s' in input" % self.EVERY)

        self.description = goal_text[:index].strip()

        try:
            goal_amount = self.incremental_parse(self.description)

            if goal_amount:
                self.incremental = True
                self.goal_amount = goal_amount
        except InvalidInput as i:
            raise i

        recurring_text = goal_text[index:].strip()

        recurring_event = RecurringEvent()

        result = None

        try:
            result = recurring_event.parse(recurring_text)
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

        if params.get('freq', None):
            self.freq = params['freq']

        if params.get('byday', None):
            self.byday = params['byday']

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
                instance.due_date = instance.compute_due_date()
                instance.save()
            except IntegrityError:
                pass
            else:
                print >>sys.stderr, "Created scheduled instance: " + str(instance)

    @classmethod
    def create_all_scheduled_instances(self, start, n):
        for goal in Goal.objects.all():
            goal.create_scheduled_instances(start, n)

    @classmethod
    def goals_for_today_by_type(self, user, completed):
        instances = [goal.scheduledinstance_set.filter(date__lte=datetime.date.today(),
                                                        due_date__gt=datetime.date.today(),
                                                    completed=completed) for
                     goal in Goal.objects.filter(user=user)]
        return list(itertools.chain.from_iterable(instances))

    @classmethod
    def completed_goals_for_today(self, user):
        return self.goals_for_today_by_type(user, True)

    @classmethod
    def goals_for_today(self, user):
        return self.goals_for_today_by_type(user, False)

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

    def day_string(self):
        unit_types = {"daily": "day",
                      "weekly": "week",
                      "monthly": "month",
                      "yearly": "year"}
        readable_days = {"MO": "Monday",
                         "TU": "Tuesday",
                         "WE": "Wednesday",
                         "TH": "Thursday",
                         "FR": "Friday",
                         "SA": "Saturday",
                         "SU": "Sunday"}

        if "BYMONTHDAY=" in self.rrule:
            try:
                print "in the right branch"
                bymonthday = int(re.search("BYMONTHDAY=(\d+)", self.rrule).groups(0)[0])

                return "Every month (day %d)" % bymonthday
            except Exception:
                return ""
        elif self.freq and not self.byday and (self.freq in unit_types.keys()):
            try:
                type = unit_types[self.freq]

                interval = int(re.search("INTERVAL=(\d+)", self.rrule).groups(0)[0])

                if interval == 1:
                    return "Every %s" % type
                elif interval == 2:
                    return "Every other %s" % type
                else:
                    return "Every %d %ss" % (interval, type)
            except Exception:
                return ""

        elif self.byday:
            if self.byday == "MO,TU,WE,TH,FR":
                return "Weekdays"

            days = self.byday.split(",")

            try:
                return ", ".join(map(lambda day: readable_days[day], days))

            except KeyError:
                return ""
        else:
            return ""


    def __unicode__(self):
        return ", ".join(["creation_text=" + self.creation_text,
                            "created_at=" + str(self.created_at),
                            "description=" + self.description,
                            "rrule=" + self.rrule,
                            "dtstart=" + str(self.dtstart),
                            "freq=" + str(self.freq),
                            "byday=" + str(self.byday),
                            "user=" + str(self.user),
                            "incremental=" + str(self.incremental),
                            "goal_amount=" + str(self.goal_amount)]
                        )

class ScheduledInstance(models.Model):
    goal = models.ForeignKey(Goal)
    date = models.DateField(db_index=True)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(db_index=True, null=True, blank=True)
    current_progress = models.IntegerField(default=0)

    def compute_due_date(self):
        if ("BYDAY=" in self.goal.rrule and "FREQ=WEEKLY" in self.goal.rrule) or \
        ("BYMONTHDAY=" in self.goal.rrule and "FREQ=MONTHLY" in self.goal.rrule):
            return self.date + datetime.timedelta(days=1)

        rr = rrule.rrulestr(self.goal.rrule)

        dt = datetime.datetime(self.date.year, self.date.month, self.date.day)

        return rr.after(dt).date()

    def progress(self):
        if self.goal.incremental:
            self.current_progress += 1

            if self.current_progress == self.goal.goal_amount:
                self.completed = True
        else:
            self.completed = True

    def __unicode__(self):
        return ", ".join(["goal = " + self.goal.creation_text,
                          "date = " + str(self.date),
                          "completed = " + str(self.completed),
                          "due_date = " + str(self.due_date),
                          "current_progress = " + str(self.current_progress)],
                          )

    class Meta:
        unique_together = (("goal", "date"),)