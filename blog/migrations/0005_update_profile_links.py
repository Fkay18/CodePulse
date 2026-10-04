from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_expand_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='github_url',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='website_url',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='x_url',
            field=models.URLField(blank=True, max_length=300),
        ),
    ]