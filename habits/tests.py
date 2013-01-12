from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone

from habits.models import Goal, InvalidInput, ScheduledInstance, UserProfile
from django.contrib.auth.models import User
import datetime
import pytz

class GoalTest(TestCase):
    def setUp(self):
        self.user = User(username="foo", password="blah1234")
        self.user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.user = self.user        
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.save()

        byday_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        self.byday_goal = Goal()
        self.byday_goal.user = self.user
        self.byday_goal.parse(byday_text)
        self.byday_goal.save()
        
        self.today = Goal.beginning_today(self.user)
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.day_after_tomorrow = self.today + datetime.timedelta(days=2)

        self.five_days_ago = self.today - datetime.timedelta(days=5)
        self.four_days_ago = self.today - datetime.timedelta(days=4)

        self.old_goal = Goal()
        self.old_goal.user = self.user
        self.old_goal.created_at = self.five_days_ago
        self.old_goal.creation_text = "foo"
        self.old_goal.description = "foo"
        self.old_goal.dtstart = self.five_days_ago
        self.old_goal.rrule = 'DTSTART:' + self.old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1'
        self.old_goal.save()

    def test_international_user_goal_creation(self):
        intl_user = User(username="intlfoo", password="blah1234")
        intl_user.save()
        profile = intl_user.userprofile

        profile.timezone = 'Europe/London'
        profile.save()

        intl_goal_text = "Do a thing every day"
        intl_goal = Goal()
        intl_goal.user = intl_user
        intl_goal.parse(intl_goal_text)
        intl_goal.save()

        intl_goal.create_scheduled_instances(timezone.now(), 5)

        print "intl_goal due_date =", intl_goal.scheduledinstance_set.all()[0].due_date
        self.assertEquals(intl_goal.scheduledinstance_set.all()[0].due_date.hour, 0)
    
    def test_parse_goal(self):
        """
        Tests that we can parse a goal from text input.
        """

        self.assertEqual(self.simple_goal.creation_text, "Go for a walk every day")
        self.assertEqual(self.simple_goal.description, "Go for a walk")
        self.assertEqual(self.simple_goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(self.simple_goal.dtstart, self.today)
        self.assertEqual(self.simple_goal.freq, "daily")
        self.assertEqual(self.simple_goal.byday, None)
    
    def test_parsing_incremental_string(self):
        incremental_goal = Goal()

        self.assertEqual(incremental_goal.incremental_parse("Go to the gym 3 times"), 3)
        self.assertEqual(incremental_goal.incremental_parse("Go to the gym 3x"), 3)
        self.assertEqual(incremental_goal.incremental_parse("Go to the gym three times"), 3)

        self.assertEqual(incremental_goal.incremental_parse("read the new york times"), None)
        self.assertEqual(incremental_goal.incremental_parse("go for a walk"), None)

        self.assertRaises(InvalidInput, incremental_goal.incremental_parse, "go to the gym 0 times")


    def test_parse_incremental_goal(self):
        """
        Tests parsing goals like 'go to the gym 3 times every week'.
        """

        incremental_goal = Goal()
        incremental_goal.user = self.user
        incremental_goal.parse("Go to the gym 3 times every week")
        incremental_goal.save()

        self.assertEqual(incremental_goal.creation_text, "Go to the gym 3 times every week")
        self.assertEqual(incremental_goal.description, "Go to the gym 3 times")
        self.assertEqual(incremental_goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=WEEKLY;INTERVAL=1')
        self.assertEqual(incremental_goal.dtstart, self.today)
        self.assertEqual(incremental_goal.freq, "weekly")
        self.assertEqual(incremental_goal.byday, None)

        self.assertEqual(incremental_goal.incremental, True)

        self.assertEqual(incremental_goal.goal_amount, 3)

        incremental_goal.create_scheduled_instances(self.today, 1)

        instance = incremental_goal.scheduledinstance_set.all()[0]
        self.assertEqual(instance.current_progress, 0)
        self.assertEqual(instance.completed, False)

        instance.progress()

        self.assertEqual(instance.current_progress, 1)

        instance.progress()
        instance.progress()

        self.assertEqual(instance.current_progress, 3)
        self.assertEqual(instance.completed, True)

    def test_progress(self):
        self.simple_goal.create_scheduled_instances(self.today, 1)
        instance = self.simple_goal.scheduledinstance_set.all()[0]

        self.assertEqual(instance.completed, False)

        instance.progress()

        self.assertEqual(instance.completed, True)

    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """

        self.assertEqual(self.byday_goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(self.byday_goal.description, "Go to the gym")
        self.assertEqual(self.byday_goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(self.byday_goal.dtstart, datetime.datetime(2013, 1, 7, 8).replace(tzinfo=pytz.utc))
        self.assertEqual(self.byday_goal.freq, "weekly")
        self.assertEqual(self.byday_goal.byday, "MO,WE,FR")

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        goal = Goal()
        goal.user = self.user

        self.assertRaises(InvalidInput, goal.parse, "Herp a derp on Monday")

        self.assertRaises(InvalidInput, goal.parse, "Do something every hour")
        self.assertRaises(InvalidInput, goal.parse, "Do something every minute")
        self.assertRaises(InvalidInput, goal.parse, "Do something every second")

        self.assertRaises(InvalidInput, goal.parse, "Go to the doctor once a decade")

    def test_splitting_input(self):

        goal = Goal()
        goal.user = self.user

        goal.parse("2 hours of studying every day")

        self.assertEqual(goal.creation_text, "2 hours of studying every day")
        self.assertEqual(goal.description, "2 hours of studying")
        self.assertEqual(goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(goal.dtstart, Goal.beginning_today(self.user))
        self.assertEqual(goal.freq, "daily")
        self.assertEqual(goal.byday, None)

    def test_generating_scheduled_instances(self):
        """
        Tests generating additional times to complete a goal after it's entered.
        """

        self.assertEqual(self.simple_goal.generate_next_scheduled_instances(self.today, 3),
            [self.today, self.tomorrow, self.day_after_tomorrow])

        self.assertEqual(self.simple_goal.generate_next_scheduled_instances(self.tomorrow, 3),
            [self.tomorrow, self.day_after_tomorrow, self.today + datetime.timedelta(days=3)])

        self.assertEqual(self.byday_goal.generate_next_scheduled_instances(datetime.datetime(2013, 1, 9, 8).replace(tzinfo=pytz.utc), 3),
            [datetime.datetime(2013, 1, 9, 8).replace(tzinfo=pytz.utc), datetime.datetime(2013, 1, 11, 8).replace(tzinfo=pytz.utc), datetime.datetime(2013, 1, 14, 8).replace(tzinfo=pytz.utc)])

    def test_generating_all_scheduled_instances(self):
        """
        Tests generating scheduled instances for all goals.
        """

        self.byday_goal.delete()

        self.assertEquals(Goal.objects.count(), 2)

        Goal.create_all_scheduled_instances(self.five_days_ago, 5)

        # 5*2 = 10
        self.assertEquals(ScheduledInstance.objects.count(), 10)

        Goal.create_all_scheduled_instances(self.four_days_ago, 4)

        self.assertEquals(ScheduledInstance.objects.count(), 10)

        Goal.create_all_scheduled_instances(self.four_days_ago, 5)

        # one for the newer goal already exists
        self.assertEquals(ScheduledInstance.objects.count(), 11)

    def test_getting_todays_goals(self):
        self.byday_goal.delete()

        self.simple_goal.create_scheduled_instances(self.today, 5)

        first_instance = self.simple_goal.scheduledinstance_set.all()[0]

        self.assertEquals(Goal.goals_for_today(self.user), [first_instance])

        first_instance.completed = True
        first_instance.save()

        self.assertEquals(Goal.goals_for_today(self.user), [])

        self.old_goal.rrule = 'DTSTART:' + self.old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=WEEKLY;INTERVAL=1'
        self.old_goal.save()

        self.old_goal.create_scheduled_instances(self.five_days_ago, 5)

        print "*** today = ", Goal.beginning_today(self.user)


        instance = self.old_goal.scheduledinstance_set.all()[0]

        print "*** expected instance = ", instance

        self.assertEquals(Goal.goals_for_today(self.user), [instance])

    def test_streak_calculation(self):
        self.old_goal.rrule = 'DTSTART:' + self.old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1'
        self.old_goal.save()

        self.byday_goal.delete()

        self.assertEquals(Goal.objects.count(), 2)

        self.old_goal.create_scheduled_instances(self.five_days_ago, 10)

        self.assertEquals(self.old_goal.current_streak(), 0)

        self.old_goal.scheduledinstance_set.filter(date__lt=self.today).update(completed=True)

        self.assertEquals(self.old_goal.current_streak(), 5)

        yesterday_instance = self.old_goal.scheduledinstance_set.get(date=self.yesterday)
        today_instance = self.old_goal.scheduledinstance_set.get(date=self.today)

        yesterday_instance.completed = False
        yesterday_instance.save()

        self.assertEquals(self.old_goal.current_streak(), 0)

        today_instance.completed = True
        today_instance.save()

        self.assertEquals(self.old_goal.current_streak(), 1)

    def test_streak_calculation_with_skipped_goals(self):
        self.byday_goal.delete()

        self.old_goal.create_scheduled_instances(self.five_days_ago, 10)

        for instance in self.old_goal.scheduledinstance_set.filter(date__lt=self.today):
            if instance.date != self.four_days_ago:
                instance.completed = True
                instance.save()
            else:
                instance.skipped = True
                instance.save()

        self.assertEquals(self.old_goal.current_streak(), 4)

    def test_day_string(self):

        self.assertEquals(self.simple_goal.day_string(), "Every day")

        weekday_goal = Goal()
        weekday_goal.user = self.user
        weekday_goal.parse("Pet a kitty every weekday")

        self.assertEquals(weekday_goal.day_string(), "Weekdays")

        self.assertEquals(self.byday_goal.day_string(), "Monday, Wednesday, Friday")

        interval_goal = Goal()
        interval_goal.user = self.user
        interval_goal.user = self.user
        interval_goal.parse("Pet a kitty every other day")

        self.assertEquals(interval_goal.day_string(), "Every other day")

        interval_goal2 = Goal()
        interval_goal2.user = self.user
        interval_goal2.parse("Pet a kitty every 3 days")

        self.assertEquals(interval_goal2.day_string(), "Every 3 days")

        weekly_goal = Goal()
        weekly_goal.user = self.user
        weekly_goal.parse("do a thing every week")

        self.assertEquals(weekly_goal.day_string(), "Every week")

        bymonthday_goal_text = "Pay rent every first of the month"
        bymonth_goal = Goal()
        bymonth_goal.user = self.user
        bymonth_goal.parse(bymonthday_goal_text)

        self.assertEquals(bymonth_goal.day_string(), "Every month (day 1)")

class ScheduledInstanceTest(TestCase):
    def setUp(self):
        self.user = User(username="foo", password="blah1234")
        self.user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.user = self.user
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.save()

        self.today = Goal.beginning_today(self.user)

        self.i1 = ScheduledInstance(goal=self.simple_goal, date=self.today)
        self.i1.save()

    def test_scheduled_instance_uniqueness(self):
        dup = ScheduledInstance(goal=self.simple_goal, date=self.today)

        self.assertRaises(IntegrityError, dup.save)

    def test_due_date(self):
        self.assertEquals(self.i1.compute_due_date(), self.today + datetime.timedelta(days=1))

        weekly_goal_text = "Do a timed mile run every week"

        weekly_goal = Goal()
        weekly_goal.user = self.user
        weekly_goal.parse(weekly_goal_text)
        weekly_goal.save()

        instance = ScheduledInstance(goal=weekly_goal, date=self.today)
        self.assertEquals(instance.compute_due_date(), self.today + datetime.timedelta(weeks=1))

        byday_goal_text = "Do something every tuesday and thursday"
        byday_goal = Goal()
        byday_goal.user = self.user
        byday_goal.parse(byday_goal_text)
        byday_goal.save()
        byday_goal.create_scheduled_instances(self.today - datetime.timedelta(weeks=1), 5)

        byday_instance = byday_goal.scheduledinstance_set.all()[0]
        self.assertEquals(byday_instance.compute_due_date(), byday_instance.date + datetime.timedelta(days=1))

        bymonthday_goal_text = "Pay rent every first of the month"
        bymonth_goal = Goal()
        bymonth_goal.user = self.user
        bymonth_goal.parse(bymonthday_goal_text)
        bymonth_goal.save()

        bymonth_goal.create_scheduled_instances(self.today, 5)

        bymonth_instance = bymonth_goal.scheduledinstance_set.all()[0]
        self.assertEquals(bymonth_instance.compute_due_date(), bymonth_instance.date + datetime.timedelta(days=1))
