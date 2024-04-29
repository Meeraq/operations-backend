# Generated by Django 4.1.7 on 2024-04-26 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0053_hr_profile_pic_pmo_profile_pic_sales_business_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CTTPmo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=25)),
                ('active_inactive', models.BooleanField(default=True)),
                ('user', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile')),
            ],
        ),
    ]