from django.core.management.base import BaseCommand, CommandError
import datetime
import logging

from habits.models import Goal
import sys

class Command(BaseCommand):
    args = '(none)'
    help = 'Generates additional scheduled instances of goals'

    def handle(self, *args, **options):
        print >>sys.stderr, "Generating additional scheduled instances..."

        today = Goal.beginning_today()

        Goal.create_all_scheduled_instances(today, 5)

        print >>sys.stderr, "Done generating scheduled instances."

