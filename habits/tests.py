from django.test import TestCase
from django.db import IntegrityError

from habits.models import Goal, InvalidInput, ScheduledInstance
from django.contrib.auth.models import User
import datetime

class GoalTest(TestCase):
    def setUp(self):
        self.user = User(username="foo", password="blah1234")
        self.user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.user = self.user
        self.simple_goal.save()

        byday_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        self.byday_goal = Goal()
        self.byday_goal.parse(byday_text)
        self.byday_goal.user = self.user
        self.byday_goal.save()

        self.today = datetime.date.today()
        self.yesterday = datetime.date.today() - datetime.timedelta(days=1)
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.day_after_tomorrow = self.today + datetime.timedelta(days=2)

    def test_parse_goal(self):
        """
        Tests that we can parse a goal from text input.
        """

        self.assertEqual(self.simple_goal.creation_text, "Go for a walk every day")
        self.assertEqual(self.simple_goal.description, "Go for a walk")
        self.assertEqual(self.simple_goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(self.simple_goal.dtstart, datetime.date.today())
        self.assertEqual(self.simple_goal.freq, "daily")
        self.assertEqual(self.simple_goal.byday, None)


    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """

        self.assertEqual(self.byday_goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(self.byday_goal.description, "Go to the gym")
        self.assertEqual(self.byday_goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(self.byday_goal.dtstart, datetime.date(2013, 1, 7))
        self.assertEqual(self.byday_goal.freq, "weekly")
        self.assertEqual(self.byday_goal.byday, "MO,WE,FR")

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, "Herp a derp on Monday")

        self.assertRaises(InvalidInput, goal.parse, "Do something every hour")
        self.assertRaises(InvalidInput, goal.parse, "Do something every minute")
        self.assertRaises(InvalidInput, goal.parse, "Do something every second")

    def test_splitting_input(self):

        goal = Goal()

        goal.parse("2 hours of studying every day")

        self.assertEqual(goal.creation_text, "2 hours of studying every day")
        self.assertEqual(goal.description, "2 hours of studying")
        self.assertEqual(goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(goal.dtstart, datetime.date.today())
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

        self.assertEqual(self.byday_goal.generate_next_scheduled_instances(datetime.date(2013, 1, 9), 3),
            [datetime.date(2013, 1, 9), datetime.date(2013, 1, 11), datetime.date(2013, 1, 14)])

    def test_generating_all_scheduled_instances(self):
        """
        Tests generating scheduled instances for all goals.
        """

        five_days_ago = self.today - datetime.timedelta(days=5)
        four_days_ago = self.today - datetime.timedelta(days=4)

        old_goal = Goal()
        old_goal.user = self.user
        old_goal.created_at = five_days_ago
        old_goal.creation_text = "foo"
        old_goal.description = "foo"
        old_goal.dtstart = five_days_ago
        old_goal.rrule = 'DTSTART:' + old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1'
        old_goal.save()

        self.byday_goal.delete()

        self.assertEquals(Goal.objects.count(), 2)

        Goal.create_all_scheduled_instances(five_days_ago, 5)

        # 5*2 = 10
        self.assertEquals(ScheduledInstance.objects.count(), 10)

        Goal.create_all_scheduled_instances(four_days_ago, 4)

        self.assertEquals(ScheduledInstance.objects.count(), 10)

        Goal.create_all_scheduled_instances(four_days_ago, 5)

        # one for the newer goal already exists
        self.assertEquals(ScheduledInstance.objects.count(), 11)

    def test_getting_todays_goals(self):
        self.byday_goal.delete()

        self.assertEquals(Goal.objects.count(), 1)

        self.simple_goal.create_scheduled_instances(self.today, 5)

        first_instance = self.simple_goal.scheduledinstance_set.all()[0]

        self.assertEquals(Goal.goals_for_today(self.user), [first_instance])

        first_instance.completed = True
        first_instance.save()

        self.assertEquals(Goal.goals_for_today(self.user), [])

    def test_streak_calculation(self):
        five_days_ago = self.today - datetime.timedelta(days=5)
        four_days_ago = self.today - datetime.timedelta(days=4)

        old_goal = Goal()
        old_goal.user = self.user
        old_goal.created_at = five_days_ago
        old_goal.creation_text = "foo"
        old_goal.description = "foo"
        old_goal.dtstart = five_days_ago
        old_goal.rrule = 'DTSTART:' + old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1'
        old_goal.save()

        self.byday_goal.delete()

        self.assertEquals(Goal.objects.count(), 2)

        old_goal.create_scheduled_instances(five_days_ago, 10)

        self.assertEquals(old_goal.current_streak(), 0)

        for instance in old_goal.scheduledinstance_set.filter(date__lt=self.today):
            instance.completed = True
            instance.save()

        self.assertEquals(old_goal.current_streak(), 5)

        yesterday_instance = old_goal.scheduledinstance_set.get(date=self.yesterday)
        today_instance = old_goal.scheduledinstance_set.get(date=self.today)

        yesterday_instance.completed = False
        yesterday_instance.save()

        self.assertEquals(old_goal.current_streak(), 0)

        today_instance.completed = True
        today_instance.save()

        self.assertEquals(old_goal.current_streak(), 1)

    def test_day_string(self):
        # TODO handle interval=2 as "every other day", interval=3 as "every 3 days"
        
        self.assertEquals(self.simple_goal.day_string(), "All")

        weekday_goal = Goal()
        weekday_goal.parse("Pet a kitty every weekday")

        self.assertEquals(weekday_goal.day_string(), "Weekdays")

        self.assertEquals(self.byday_goal.day_string(), "Monday, Wednesday, Friday")

class ScheduledInstanceTest(TestCase):
    def test_scheduled_instance_uniqueness(self):
        user = User(username="foo", password="blah1234")
        user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.user = user
        self.simple_goal.save()

        self.today = datetime.date.today()

        i1 = ScheduledInstance(goal=self.simple_goal, date=self.today)
        i1.save()

        dup = ScheduledInstance(goal=self.simple_goal, date=self.today)

        self.assertRaises(IntegrityError, dup.save)