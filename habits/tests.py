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

    def test_parsing_incremental_string(self):
        incremental_goal = Goal()

        self.assertEqual(incremental_goal.incremental_parse("Go to the gym 3 times every week"), 3)
        self.assertEqual(incremental_goal.incremental_parse("Go to the gym 3x every week"), 3)
        self.assertEqual(incremental_goal.incremental_parse("read the new york times every week"), None)
        self.assertEqual(incremental_goal.incremental_parse("go for a walk every day"), None)

        self.assertRaises(InvalidInput, incremental_goal.incremental_parse, "go to the gym 0 times every week")


    def test_parse_incremental_goal(self):
        """
        Tests parsing goals like 'go to the gym 3 times every week'.
        """

        incremental_goal = Goal()
        incremental_goal.user = self.user
        incremental_goal.parse("Go to the gym 3 times every week")

        self.assertEqual(incremental_goal.creation_text, "Go to the gym 3 times every week")
        self.assertEqual(incremental_goal.description, "Go to the gym 3 times")
        self.assertEqual(incremental_goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=WEEKLY;INTERVAL=1')
        self.assertEqual(incremental_goal.dtstart, datetime.date.today())
        self.assertEqual(incremental_goal.freq, "weekly")
        self.assertEqual(incremental_goal.byday, None)

        self.assertEqual(incremental_goal.incremental, True)

        self.assertEqual(incremental_goal.goal_amount, 3)

#        incremental_goal.create_scheduled_instances(self.today, 1)
#
#        instance = incremental_goal.scheduledinstance_set.all()[0]
#        self.assertEqual(instance.current_progress, 0)
#        self.assertEqual(instance.goal_amount, 3)
#        self.assertEqual(instance.completed, False)
#
#        # TODO add this for regular goals as well so that .progress on a non-incremental goal completes it
#        # but on an incremental goal it advances the goal amount by 1
#
#        instance.progress()
#
#        self.assertEqual(instance.current_progress, 1)
#
#        instance.progress()
#        instance.progress()
#
#        self.assertEqual(instance.current_progress, 3)
#        self.assertEqual(instance.completed, True)

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

        self.assertRaises(InvalidInput, goal.parse, "Go to the doctor once a decade")

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

        five_days_ago = self.today - datetime.timedelta(days=5)

        old_goal = Goal()
        old_goal.user = self.user
        old_goal.created_at = five_days_ago
        old_goal.creation_text = "foo"
        old_goal.description = "foo"
        old_goal.dtstart = five_days_ago
        old_goal.rrule = 'DTSTART:' + old_goal.dtstart.strftime("%Y%m%d") + '\nRRULE:FREQ=WEEKLY;INTERVAL=1'
        old_goal.save()

        old_goal.create_scheduled_instances(five_days_ago, 5)

        instance = old_goal.scheduledinstance_set.all()[0]

        self.assertEquals(Goal.goals_for_today(self.user), [instance])

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

        self.assertEquals(self.simple_goal.day_string(), "Every day")

        weekday_goal = Goal()
        weekday_goal.parse("Pet a kitty every weekday")

        self.assertEquals(weekday_goal.day_string(), "Weekdays")

        self.assertEquals(self.byday_goal.day_string(), "Monday, Wednesday, Friday")

        interval_goal = Goal()
        interval_goal.user = self.user
        interval_goal.parse("Pet a kitty every other day")

        self.assertEquals(interval_goal.day_string(), "Every other day")

        interval_goal2 = Goal()
        interval_goal2.parse("Pet a kitty every 3 days")

        self.assertEquals(interval_goal2.day_string(), "Every 3 days")

        weekly_goal = Goal()
        weekly_goal.user = self.user
        weekly_goal.parse("do a thing every week")

        self.assertEquals(weekly_goal.day_string(), "Every week")
class ScheduledInstanceTest(TestCase):
    def setUp(self):
        self.user = User(username="foo", password="blah1234")
        self.user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.user = self.user
        self.simple_goal.save()

        self.today = datetime.date.today()

        self.i1 = ScheduledInstance(goal=self.simple_goal, date=self.today)
        self.i1.save()

    def test_scheduled_instance_uniqueness(self):
        dup = ScheduledInstance(goal=self.simple_goal, date=self.today)

        self.assertRaises(IntegrityError, dup.save)

    def test_due_date(self):
        #self.assertEquals(self.i1.compute_due_date(), self.today + datetime.timedelta(days=1))

        weekly_goal_text = "Do a timed mile run every week"

        weekly_goal = Goal()
        weekly_goal.parse(weekly_goal_text)
        weekly_goal.user = self.user
        weekly_goal.save()

        instance = ScheduledInstance(goal=weekly_goal, date=self.today)
        #self.assertEquals(instance.compute_due_date(), self.today + datetime.timedelta(weeks=1))

        byday_goal_text = "Do something every tuesday and thursday"
        byday_goal = Goal()
        byday_goal.parse(byday_goal_text)
        byday_goal.user = self.user
        byday_goal.save()
        byday_goal.create_scheduled_instances(self.today - datetime.timedelta(weeks=1), 5)

        byday_instance = byday_goal.scheduledinstance_set.all()[0]
        self.assertEquals(byday_instance.compute_due_date(), byday_instance.date + datetime.timedelta(days=1))
