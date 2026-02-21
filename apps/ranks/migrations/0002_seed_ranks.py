"""
Data migration to seed the 10 ranks for the Phonix MLM platform.

Ranks (Connector → Chief):
  1. Connector     — L:1,000   R:1,000   $75/week
  2. Starter       — L:5,000   R:5,000   $125/week
  3. Builder       — L:15,000  R:15,000  $250/week
  4. Achiever      — L:50,000  R:50,000  $500/week
  5. Executive     — Asymmetric (L≥500k AND R≥100k) OR vice versa  $1,000/week
  6. Sapphire      — L:250,000 R:250,000 $1,500/week
  7. Ruby          — L:500,000 R:500,000 $2,000/week
  8. Diamond       — L:1M      R:1M      $2,500/week
  9. Crown         — L:5M      R:5M      $3,500/week
  10. Chief        — L:10M     R:10M     $5,000/week
"""
from decimal import Decimal
from django.db import migrations


RANKS = [
    {
        'name': 'Connector',
        'level': 1,
        'left_target': Decimal('1000.00'),
        'right_target': Decimal('1000.00'),
        'weekly_bonus': Decimal('75.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Starter',
        'level': 2,
        'left_target': Decimal('5000.00'),
        'right_target': Decimal('5000.00'),
        'weekly_bonus': Decimal('125.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Builder',
        'level': 3,
        'left_target': Decimal('15000.00'),
        'right_target': Decimal('15000.00'),
        'weekly_bonus': Decimal('250.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Achiever',
        'level': 4,
        'left_target': Decimal('50000.00'),
        'right_target': Decimal('50000.00'),
        'weekly_bonus': Decimal('500.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Executive',
        'level': 5,
        'left_target': Decimal('500000.00'),
        'right_target': Decimal('100000.00'),
        'weekly_bonus': Decimal('1000.00'),
        'duration_weeks': 52,
        'is_asymmetric': True,
    },
    {
        'name': 'Sapphire',
        'level': 6,
        'left_target': Decimal('250000.00'),
        'right_target': Decimal('250000.00'),
        'weekly_bonus': Decimal('1500.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Ruby',
        'level': 7,
        'left_target': Decimal('500000.00'),
        'right_target': Decimal('500000.00'),
        'weekly_bonus': Decimal('2000.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Diamond',
        'level': 8,
        'left_target': Decimal('1000000.00'),
        'right_target': Decimal('1000000.00'),
        'weekly_bonus': Decimal('2500.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Crown',
        'level': 9,
        'left_target': Decimal('5000000.00'),
        'right_target': Decimal('5000000.00'),
        'weekly_bonus': Decimal('3500.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
    {
        'name': 'Chief',
        'level': 10,
        'left_target': Decimal('10000000.00'),
        'right_target': Decimal('10000000.00'),
        'weekly_bonus': Decimal('5000.00'),
        'duration_weeks': 52,
        'is_asymmetric': False,
    },
]


def seed_ranks(apps, schema_editor):
    Rank = apps.get_model('ranks', 'Rank')
    for rank_data in RANKS:
        Rank.objects.update_or_create(
            level=rank_data['level'],
            defaults=rank_data,
        )


def remove_ranks(apps, schema_editor):
    Rank = apps.get_model('ranks', 'Rank')
    Rank.objects.filter(level__in=[r['level'] for r in RANKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ranks', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_ranks, remove_ranks),
    ]
