"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from habits.models import Goal

class GoalTest(TestCase):
    def test_parsing(self):
        """
        Tests that we can parse a goal from text input.
        """
        goal_text = "Go for a walk every day"

        goal = Goal()
        goal.parse(goal_text)
        self.assertEqual(goal.description, "Go for a walk")
