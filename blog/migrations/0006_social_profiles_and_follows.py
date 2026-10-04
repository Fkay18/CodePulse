from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_missing_profiles(apps, schema_editor):
    UserProfile = apps.get_model('blog', 'UserProfile')
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)
    database = schema_editor.connection.alias

    for user in User.objects.using(database).only('pk').iterator():
        UserProfile.objects.using(database).get_or_create(user_id=user.pk)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0005_update_profile_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='show_email',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='UserFollow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('followed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower_relationships', to=settings.AUTH_USER_MODEL)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_relationships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('follower', 'followed'), name='unique_user_follow'),
                    models.CheckConstraint(condition=models.Q(('follower', models.F('followed')), _negated=True), name='prevent_self_follow'),
                ],
            },
        ),
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]