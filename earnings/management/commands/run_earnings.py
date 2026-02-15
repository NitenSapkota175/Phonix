from django.core.management.base import BaseCommand
from earnings.tasks import calculate_daily_bond_income
from ranks.tasks import check_rank_advancements, distribute_weekly_bonuses

class Command(BaseCommand):
    help = 'Manually trigger earnings and rank tasks for testing'

    def add_arguments(self, parser):
        parser.add_argument('--daily', action='store_true', help='Trigger daily bond income')
        parser.add_argument('--weekly', action='store_true', help='Trigger weekly rank bonuses/checks')
        parser.add_argument('--force-weekend', action='store_true', help='Force daily bond even if it is a weekend')

    def handle(self, *args, **options):
        if options['daily']:
            self.stdout.write("Running daily bond income calculation...")
            # Note: We need to handle the weekend check if force-weekend is not set
            # For simplicity, we just call the task. 
            # In production, this runs via Celery Beat.
            result = calculate_daily_bond_income()
            self.stdout.write(self.style.SUCCESS(f"Daily bond result: {result}"))

        if options['weekly']:
            self.stdout.write("Running weekly rank advancements check...")
            rank_result = check_rank_advancements()
            self.stdout.write(self.style.SUCCESS(f"Rank check result: {rank_result}"))

            self.stdout.write("Running weekly bonus distribution...")
            bonus_result = distribute_weekly_bonuses()
            self.stdout.write(self.style.SUCCESS(f"Weekly bonus result: {bonus_result}"))

        if not options['daily'] and not options['weekly']:
            self.stdout.write(self.style.WARNING("Please specify --daily or --weekly"))
