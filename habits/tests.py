"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from habits.models import Goal, InvalidInput
import datetime

class GoalTest(TestCase):
    def test_parse_goal(self):
        """
        Tests that we can parse a goal from text input.
        """
        goal_text = "Go for a walk every day"

        goal = Goal()
        goal.parse(goal_text)
        self.assertEqual(goal.creation_text, "Go for a walk every day")
        self.assertEqual(goal.description, "Go for a walk")
        self.assertEqual(goal.rrule, 'RRULE:FREQ=DAILY;INTERVAL=1')
        self.assertEqual(goal.dtstart, datetime.date.today())
        self.assertEqual(goal.frequency, "daily")
        self.assertEqual(goal.interval, 1)

    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """
        goal_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        goal = Goal()
        goal.parse(goal_text)
        self.assertEqual(goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(goal.description, "Go to the gym")
        self.assertEqual(goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(goal.dtstart, datetime.date(2013, 1, 7))
        self.assertEqual(goal.frequency, "weekly")
        self.assertEqual(goal.byday, 'MO,WE,FR')
        self.assertEqual(goal.interval, 1)
    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        bad_input = "Herp a derp all day"

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, bad_input)