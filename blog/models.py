from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    instagram_url = models.URLField(max_length=300, blank=True)
    linkedin_url = models.URLField(max_length=300, blank=True)
    x_url = models.URLField(max_length=300, blank=True)
    receive_newsletter = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} profile'


class UserFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_relationships',
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_relationships',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('follower', 'followed'),
                name='unique_user_follow',
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('followed')),
                name='prevent_self_follow',
            ),
        ]


class Project(models.Model):
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=1000)
    technologies = models.CharField(max_length=300)
    github_url = models.URLField(max_length=300, blank=True)
    live_url = models.URLField(max_length=300, blank=True)
    image = models.ImageField(upload_to='projects/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')

    def __str__(self):
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Blog(models.Model):
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        related_name='articles',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    content = models.TextField()
    image_url = models.ImageField()
    author = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


