# Generated by Django 3.2.20 on 2023-10-29 22:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20231030_0313'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ingredient',
            name='unique_ingredients',
        ),
    ]
