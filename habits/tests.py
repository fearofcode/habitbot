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

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        bad_input = "Herp a derp all day"

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, bad_input)