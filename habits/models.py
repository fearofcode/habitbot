from django.db import models
from django.utils import timezone

import itertools
import datetime
import sys
import re
import string
import pytz

from dateutil import rrule
from recurrent import RecurringEvent
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models.signals import post_save

from habits.ordereddict import OrderedDict

class InvalidInput(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class UserProfile(models.Model):  
    user = models.OneToOneField(User)  
    timezone = models.CharField(max_length=100, default="America/Los_Angeles")

    @classmethod
    def readable_tz(self, tzstr):
        if '/' in tzstr:
            city = '/'.join(tzstr.split('/')[1:])
            return city.replace('_', ' ')
        else:
            return tzstr

    @classmethod
    def pretty_timezone_choices(self):
        ALL_TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
        COMMON_TIMEZONE_CHOICES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
        PRETTY_TIMEZONE_CHOICES = []

        for tz in pytz.common_timezones:
            now = datetime.datetime.now(pytz.timezone(tz))
            ofs = now.strftime("%z")
            PRETTY_TIMEZONE_CHOICES.append((int(ofs), tz, "(GMT%s) %s" % (ofs, UserProfile.readable_tz(tz))))
    
        PRETTY_TIMEZONE_CHOICES.sort()
    
        for i in xrange(len(PRETTY_TIMEZONE_CHOICES)):
            PRETTY_TIMEZONE_CHOICES[i] = PRETTY_TIMEZONE_CHOICES[i][1:]
    
        return PRETTY_TIMEZONE_CHOICES

    @classmethod
    def pretty_timezone_dict(self):
        choices = UserProfile.pretty_timezone_choices()

        choice_dict = {}

        for choice in choices:
            choice_dict[choice[0]] = choice[1]
        
        return choice_dict

    def readable(self):
        return UserProfile.pretty_timezone_dict()[self.timezone]

    def __str__(self):  
          return "%s's profile" % self.user  

def create_user_profile(sender, instance, created, **kwargs):
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  

post_save.connect(create_user_profile, sender=User)

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
    created_at = models.DateTimeField(auto_now_add=True)

    creation_text = models.CharField(max_length=200) # for debugging in case i fuck this up
    description = models.CharField(max_length=50)
    rrule = models.CharField(max_length=200)
    dtstart = models.DateTimeField()
    freq = models.CharField(max_length=100, null=True, blank=True)
    byday = models.CharField(max_length=100, null=True, blank=True)

    incremental = models.BooleanField(default=False)
    goal_amount = models.IntegerField(default=0)

    @classmethod
    def beginning_today(self, user):
        local_tz = pytz.timezone(user.userprofile.timezone)

        now_utc = timezone.now()
        now_local = now_utc.astimezone(local_tz)
        local_midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        local_midnight_utc = local_midnight.astimezone(pytz.utc)

        return local_midnight_utc

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

    @classmethod
    def user_tz(self, user):
        return pytz.timezone(user.userprofile.timezone)

    def parse(self, goal_text):
        goal_text = goal_text.rstrip(string.punctuation)

        self.creation_text = goal_text

        index = goal_text.lower().find(self.EVERY)

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

        
        if params.has_key('dtstart'):
            naive = datetime.datetime.strptime(params['dtstart'], "%Y%m%d") 

            user_tz = pytz.timezone(self.user.userprofile.timezone)

            local_dt = user_tz.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone (pytz.utc)
            
            self.dtstart = utc_dt
        else:
            self.dtstart = Goal.beginning_today(self.user)

        self.rrule = recurring_event.get_RFC_rrule()

        if not self.rrule.startswith("DTSTART:"):
            self.rrule = "DTSTART:" + self.dtstart.strftime("%Y%m%d") + "\n" + self.rrule

        if params.get('freq', None):
            self.freq = params['freq']

        if params.get('byday', None):
            self.byday = params['byday']

    def next_date(self, last_date):
        rr = rrule.rrulestr(self.rrule)
        
        user_tz = pytz.timezone(self.user.userprofile.timezone)
        last_date_local = last_date.astimezone(user_tz)
        last_date_naive = last_date_local.replace(tzinfo=None)
        next_date_naive = rr.after(last_date_naive)

        next_date_aware = timezone.make_aware(next_date_naive, user_tz)

        next_date_utc = next_date_aware.astimezone(pytz.utc)


        return next_date_utc

    def generate_next_scheduled_instances(self, start, n):

        datetimes = []

        for i in range(0, n):
            if len(datetimes) == 0:
                last_date = start - datetime.timedelta(days=1)
            else:
                last_date = datetimes[-1]

            datetimes.append(self.next_date(last_date))

        return [dt for dt in datetimes]

    def create_scheduled_instances(self, start, n):
        dates = self.generate_next_scheduled_instances(start, n)
        instances = [ScheduledInstance(goal=self, date=d) for d in dates]

        for instance in instances:
            try:
                instance.due_date = instance.compute_due_date()
                instance.save()
            except IntegrityError:
                pass

    @classmethod
    def create_all_scheduled_instances(self, start, n):
        for goal in Goal.objects.all():
            goal.create_scheduled_instances(start, n)

    @classmethod
    def skipped_goals_for_today(self, user):
        today = Goal.beginning_today(user)

        instances = [goal.scheduledinstance_set.filter(date__lte=today,
            due_date__gt=today,
            skipped=True) for
                     goal in Goal.objects.filter(user=user)]
        return list(itertools.chain.from_iterable(instances))

    @classmethod
    def get_first(self, lst):
        r = list(lst[:1])
        
        if r:
            return r[0]
        
        return None

    @classmethod
    def goals_for_today_by_type(self, user, completed):
        today = Goal.beginning_today(user)

        instances = [Goal.get_first(goal.scheduledinstance_set.filter(date__lte=today,
                                                        due_date__gt=today,
                                                    completed=completed,
                                                    skipped=False).order_by('-due_date')) for
                     goal in Goal.objects.filter(user=user)]
        return [i for i in instances if i is not None]

    @classmethod
    def completed_goals_for_today(self, user):
        return self.goals_for_today_by_type(user, True)

    @classmethod
    def goals_for_today(self, user):
        return self.goals_for_today_by_type(user, False)

    def current_streak(self):
        today = Goal.beginning_today(self.user)

        previous_instances = self.past_instances()

        streak = 0

        for instance in previous_instances:
            if instance.completed:
                streak += 1
            elif instance.skipped:
                continue
            elif instance.date < today:
                break

        return streak

    def past_instances(self):
        today = Goal.beginning_today(self.user)

        return self.scheduledinstance_set.filter(date__lte=today).order_by('-date')

    def missed_instances(self):
        today = Goal.beginning_today(self.user)

        # last 7 instances of the goal
        return self.scheduledinstance_set.filter(due_date__lte=today).order_by('-due_date')[:7]

    @classmethod
    def past_instances_by_day(self, user):
        user_goals = Goal.objects.filter(user=user).select_related('scheduledinstances')
        missed_instances = [goal.missed_instances() for goal in user_goals] 
        flattened = list(itertools.chain.from_iterable(missed_instances))

        by_date = {}

        for i in flattened:
            if not by_date.get(i.due_date, None):
                by_date[i.due_date] = []

            by_date[i.due_date].append(i)

        od = list(OrderedDict(sorted(by_date.items())).iteritems())

        od.reverse()
        return od
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
    date = models.DateTimeField(db_index=True)
    completed = models.BooleanField(default=False)
    due_date = models.DateTimeField(db_index=True, null=True, blank=True)
    current_progress = models.IntegerField(default=0)
    skipped = models.BooleanField(db_index=True, default=False)

    def compute_due_date(self):
        if ("BYDAY=" in self.goal.rrule and "FREQ=WEEKLY" in self.goal.rrule) or \
        ("BYMONTHDAY=" in self.goal.rrule and "FREQ=MONTHLY" in self.goal.rrule):
            return self.date + datetime.timedelta(days=1)

        return self.goal.next_date(self.date)
    
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
                          "current_progress = " + str(self.current_progress),
                          "skipped = " + str(self.skipped)],
                          )

    class Meta:
        unique_together = (("goal", "date"),)
