"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from habits.models import Goal, InvalidInput
import datetime

class GoalTest(TestCase):
    def setUp(self):
        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)

        byday_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        self.byday_goal = Goal()
        self.byday_goal.parse(byday_text)

    def test_parse_goal(self):
        """
        Tests that we can parse a goal from text input.
        """

        self.assertEqual(self.simple_goal.creation_text, "Go for a walk every day")
        self.assertEqual(self.simple_goal.description, "Go for a walk")
        self.assertEqual(self.simple_goal.rrule, 'RRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(self.simple_goal.dtstart, datetime.date.today())
        self.assertEqual(self.simple_goal.frequency, "daily")
        self.assertEqual(self.simple_goal.interval, 1)

    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """

        self.assertEqual(self.byday_goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(self.byday_goal.description, "Go to the gym")
        self.assertEqual(self.byday_goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(self.byday_goal.dtstart, datetime.date(2013, 1, 7))
        self.assertEqual(self.byday_goal.frequency, "weekly")
        self.assertEqual(self.byday_goal.byday, 'MO,WE,FR')
        self.assertEqual(self.byday_goal.interval, 1)

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        bad_input = "Herp a derp on Monday"

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, bad_input)