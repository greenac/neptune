# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BanterUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_updated', models.DateTimeField()),
                ('type', models.CharField(max_length=100)),
                ('profile_id', models.CharField(max_length=200)),
                ('notification_token', models.CharField(max_length=200)),
                ('profile_url', models.URLField()),
                ('pic', models.CharField(max_length=200)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField()),
                ('date', models.DateTimeField()),
                ('commenter', models.ForeignKey(to='data_models.BanterUser')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Decoder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range', models.IntegerField()),
                ('name', models.TextField()),
                ('field', models.TextField()),
                ('value', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
                ('recurring_start', models.TimeField(null=True)),
                ('recurring_end', models.TimeField(null=True)),
                ('ends_next_day', models.BooleanField(default=False)),
                ('description1', models.TextField()),
                ('description2', models.TextField()),
                ('type', models.CharField(max_length=200)),
                ('type_ext', models.CharField(max_length=2)),
                ('message', models.TextField()),
                ('exact_address', models.CharField(max_length=50)),
                ('recurring_weekly', models.CharField(max_length=50)),
                ('location_description', models.CharField(max_length=300)),
                ('address', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=200)),
                ('state', models.CharField(max_length=100)),
                ('zip', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('latitude', models.CharField(max_length=200)),
                ('longitude', models.CharField(max_length=200)),
                ('monday', models.CharField(max_length=200)),
                ('tuesday', models.CharField(max_length=200)),
                ('wednesday', models.CharField(max_length=200)),
                ('thursday', models.CharField(max_length=200)),
                ('friday', models.CharField(max_length=200)),
                ('saturday', models.CharField(max_length=200)),
                ('sunday', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Friend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('friend_user_id', models.IntegerField()),
                ('email', models.EmailField(max_length=200)),
                ('banter_user', models.ForeignKey(to='data_models.BanterUser')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.TextField()),
                ('function', models.TextField()),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Scene',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('contact', models.CharField(max_length=200)),
                ('logo_path', models.CharField(max_length=200)),
                ('phone_number', models.CharField(max_length=200)),
                ('email', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('website_url', models.URLField(max_length=255)),
                ('facebook_url', models.URLField(max_length=255)),
                ('yelp_url', models.URLField(max_length=255)),
                ('twitter_url', models.URLField(max_length=255)),
                ('open_table_url', models.URLField(max_length=255)),
                ('instagram_url', models.URLField(max_length=255)),
                ('yelp_image_url', models.URLField(max_length=255)),
                ('yelp_price_url', models.URLField(max_length=255)),
                ('message', models.TextField()),
                ('time_offset', models.IntegerField()),
                ('address', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=200)),
                ('state', models.CharField(max_length=100)),
                ('zip', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('latitude', models.CharField(max_length=200)),
                ('longitude', models.CharField(max_length=200)),
                ('monday', models.CharField(max_length=200)),
                ('tuesday', models.CharField(max_length=200)),
                ('wednesday', models.CharField(max_length=200)),
                ('thursday', models.CharField(max_length=200)),
                ('friday', models.CharField(max_length=200)),
                ('saturday', models.CharField(max_length=200)),
                ('sunday', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='scene',
            field=models.ForeignKey(to='data_models.Scene'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='scene',
            field=models.ForeignKey(to='data_models.Scene'),
            preserve_default=True,
        ),
    ]
