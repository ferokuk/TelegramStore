# Generated by Django 5.2.3 on 2025-06-20 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_faq'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='faq',
            options={'verbose_name': 'Часто задаваемый вопрос', 'verbose_name_plural': 'Часто задаваемые вопросы'},
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена, руб.'),
        ),
    ]
