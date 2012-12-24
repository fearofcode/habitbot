from django.test import TestCase
from habits.models import Goal, InvalidInput
from django.contrib.auth.models import User
import datetime

class GoalTest(TestCase):
    def setUp(self):
        user = User(username="foo", password="blah1234")
        user.save()

        simple_goal_text = "Go for a walk every day"

        self.simple_goal = Goal()
        self.simple_goal.parse(simple_goal_text)
        self.simple_goal.user = user
        self.simple_goal.save()

        byday_text = "Go to the gym every mon wed and fri starting jan 7 2013"

        self.byday_goal = Goal()
        self.byday_goal.parse(byday_text)
        self.byday_goal.user = user
        self.byday_goal.save()

        self.today = datetime.date.today()
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


    def test_parse_goal_with_start_date_and_by_date(self):
        """
        Tests that we can parse a goal from text input with different kinds of input.
        """

        self.assertEqual(self.byday_goal.creation_text, "Go to the gym every mon wed and fri starting jan 7 2013")
        self.assertEqual(self.byday_goal.description, "Go to the gym")
        self.assertEqual(self.byday_goal.rrule, 'DTSTART:20130107\nRRULE:BYDAY=MO,WE,FR;INTERVAL=1;FREQ=WEEKLY')
        self.assertEqual(self.byday_goal.dtstart, datetime.date(2013, 1, 7))

    def test_complain_invalid_input(self):
        """
        Tests that parsing complains on invalid input.
        """

        goal = Goal()

        self.assertRaises(InvalidInput, goal.parse, "Herp a derp on Monday")

        self.assertRaises(InvalidInput, goal.parse, "Do something every hour")
        self.assertRaises(InvalidInput, goal.parse, "Do something every minute")
        self.assertRaises(InvalidInput, goal.parse, "Do something every second")

    def test_generating_scheduled_instances(self):
        """
        Tests generating additional times to complete a goal after it's entered.
        """

        #print self.simple_goal.generate_next_scheduled_instances(self.today, 3)
        #print [self.today, self.tomorrow, self.day_after_tomorrow]

        self.assertEqual(self.simple_goal.generate_next_scheduled_instances(self.today, 3),
            [self.today, self.tomorrow, self.day_after_tomorrow])

        self.assertEqual(self.simple_goal.generate_next_scheduled_instances(self.tomorrow, 3),
            [self.tomorrow, self.day_after_tomorrow, self.today + datetime.timedelta(days=3)])

        self.assertEqual(self.byday_goal.generate_next_scheduled_instances(datetime.date(2013, 1, 9), 3),
            [datetime.date(2013, 1, 9), datetime.date(2013, 1, 11), datetime.date(2013, 1, 14)])
