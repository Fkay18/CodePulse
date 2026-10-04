from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, upload_to='profiles/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='instagram_url',
            field=models.URLField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='linkedin_url',
            field=models.URLField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='github_url',
            field=models.URLField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='website_url',
            field=models.URLField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='receive_newsletter',
            field=models.BooleanField(default=False),
        ),
    ]