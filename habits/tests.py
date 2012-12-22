"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from habits.models import Goal, InvalidInput, Instance
import datetime

class GoalTest(TestCase):
    def setUp(self):
        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.save()

        byday_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        self.byday_goal = Goal()
        self.byday_goal.parse(byday_text)
        self.byday_goal.save()

        self.today = datetime.date.today()

    def test_parse_goal(self):
        """
        Tests that we can parse a goal from text input.
        """

        self.assertEqual(self.simple_goal.creation_text, "Go for a walk every day")
        self.assertEqual(self.simple_goal.description, "Go for a walk")
        self.assertEqual(self.simple_goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(self.simple_goal.dtstart, datetime.date.today())


    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """

        self.assertEqual(self.byday_goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(self.byday_goal.description, "Go to the gym")
        self.assertEqual(self.byday_goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(self.byday_goal.dtstart, datetime.date(2013, 1, 7))

    def test_get_next_datetime(self):
        self.assertEqual(self.simple_goal.next_datetime().created_at, self.today)
        self.assertEqual(self.byday_goal.next_datetime().created_at, datetime.date(2013, 1, 7))

        tomorrow = self.today + datetime.timedelta(days=1)

        self.simple_goal.instance_set.create(created_at=self.today)

        self.assertEqual(self.simple_goal.next_datetime().created_at, tomorrow)

        self.byday_goal.instance_set.create(created_at=datetime.date(2013, 1, 7))
        self.assertEqual(self.byday_goal.next_datetime().created_at, datetime.date(2013, 1, 9))

    def test_weekly_goals(self):
        goal_text = "Do a timed mile run every other week"

        goal = Goal()
        goal.parse(goal_text)
        goal.save()

        self.assertEqual(goal.creation_text, "Do a timed mile run every other week")
        self.assertEqual(goal.description, "Do a timed mile run")
        self.assertEqual(goal.rrule,
            'DTSTART:' + self.today.strftime("%Y%m%d") + '\nRRULE:FREQ=WEEKLY;INTERVAL=2')
        self.assertEqual(self.simple_goal.dtstart, datetime.date.today())

        #self.assertEqual(self.simple_goal.next_datetime().created_at, self.today)
        #self.assertEqual(self.simple_goal.next_datetime().created_at, self.today)

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, "Herp a derp on Monday")

        self.assertRaises(InvalidInput, goal.parse, "Do something every hour")
        self.assertRaises(InvalidInput, goal.parse, "Do something every minute")
        self.assertRaises(InvalidInput, goal.parse, "Do something every second")