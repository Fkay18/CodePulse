import re
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from .forms import BlogForm, ClientSignUpForm, ProjectForm, UserProfileForm
from .models import Blog, Project, Unit, UserFollow, UserProfile


class PublicPageContentTests(TestCase):
    def test_about_page_describes_community_and_project_showcase(self):
        response = self.client.get(reverse('about'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meet your community')
        self.assertContains(response, 'Show what you build')
        self.assertContains(response, reverse('community'))
        self.assertContains(response, 'GitHub and live-demo links')

    def test_contact_page_links_to_instagram_and_x(self):
        response = self.client.get(reverse('contact'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://www.instagram.com/Fkay_18/')
        self.assertContains(response, '@Fkay_18')
        self.assertContains(response, 'https://x.com/Fikky04')
        self.assertContains(response, '@Fikky04')
        self.assertContains(response, 'site-footer__social-icon')


class BlogCrudTests(TestCase):
    def test_blog_form_is_available(self):
        self.assertIsNotNone(BlogForm)

    def test_manage_article_routes_exist(self):
        self.assertTrue(reverse('manage_articles').endswith('/manage_articles/'))
        self.assertTrue(reverse('add_articles').endswith('/add_articles/'))
        self.assertTrue(reverse('edit_article_list').endswith('/edit_article_list/'))
        self.assertTrue(reverse('delete_article_list').endswith('/delete_article_list/'))


class BlogCrudPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='crud-permission-user',
            password='Secure-test-password!746',
        )
        self.crud_urls = {
            'view': [
                reverse('manage_articles'),
            ],
            'add': [
                reverse('add_articles'),
            ],
            'change': [
                reverse('edit_article_list'),
                reverse('edit_article', kwargs={'slug': 'missing-article'}),
            ],
            'delete': [
                reverse('delete_article_list'),
                reverse('delete_article', kwargs={'slug': 'missing-article'}),
            ],
        }

    def test_anonymous_users_are_redirected_from_every_crud_view(self):
        all_urls = [url for urls in self.crud_urls.values() for url in urls]

        for url in all_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('login')))

    def test_authenticated_users_without_permissions_receive_forbidden(self):
        self.client.force_login(self.user)
        all_urls = [url for urls in self.crud_urls.values() for url in urls]

        for url in all_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_model_permissions_grant_only_their_crud_access(self):
        self.client.force_login(self.user)
        permission_sets = {
            'view_blog': {'view_blog'},
            'add_blog': {'add_blog'},
            'change_blog': {'view_blog', 'change_blog'},
            'delete_blog': {'view_blog', 'delete_blog'},
        }

        for permission_name, codenames in permission_sets.items():
            with self.subTest(permission=permission_name):
                permissions = Permission.objects.filter(
                    content_type__app_label='blog',
                    codename__in=codenames,
                )
                self.user.user_permissions.set(permissions)

                for category, urls in self.crud_urls.items():
                    required = {
                        'view': {'view_blog'},
                        'add': {'add_blog'},
                        'change': {'view_blog', 'change_blog'},
                        'delete': {'view_blog', 'delete_blog'},
                    }[category]
                    expected_statuses = (200, 404) if required.issubset(codenames) else (403,)

                    for url in urls:
                        with self.subTest(url=url):
                            self.assertIn(self.client.get(url).status_code, expected_statuses)


class ClientSignupTests(TestCase):
    def test_signup_creates_and_logs_in_an_unprivileged_client(self):
        response = self.client.post(
            reverse('client_signup'),
            {
                'username': 'new-client',
                'email': 'new-client@example.test',
                'password1': 'Long-secure-client-pass!837',
                'password2': 'Long-secure-client-pass!837',
                'is_staff': 'on',
                'is_superuser': 'on',
            },
        )

        self.assertRedirects(response, reverse('home'))
        user = get_user_model().objects.get(username='new-client')
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perms(['blog.view_blog', 'blog.add_blog']))
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(self.client.get(reverse('manage_articles')).status_code, 403)

    def test_signup_requires_a_unique_email_address(self):
        get_user_model().objects.create_user(
            username='existing-client',
            email='existing@example.test',
            password='Existing-secure-password!928',
        )

        response = self.client.post(
            reverse('client_signup'),
            {
                'username': 'second-client',
                'email': 'EXISTING@example.test',
                'password1': 'Long-secure-client-pass!837',
                'password2': 'Long-secure-client-pass!837',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ClientSignUpForm)
        self.assertIn('email', response.context['form'].errors)


class UserProfileTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.user = get_user_model().objects.create_user(
            username='profile-user',
            email='profile@example.test',
            password='Profile-secure-password!928',
        )
        self.profile_url = reverse('profile')

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(self.profile_url)

        self.assertRedirects(response, f'{reverse("login")}?next={self.profile_url}')

    def test_new_accounts_receive_a_profile_automatically(self):
        user = get_user_model().objects.create_user(
            username='profile-signal-user',
            password='Profile-signal-password!928',
        )

        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_page_creates_profile_for_existing_users(self):
        self.client.force_login(self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/profile.html')
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertIsInstance(response.context['form'], UserProfileForm)

    def test_profile_updates_details_and_account_email_without_changing_username(self):
        self.client.force_login(self.user)

        response = self.client.post(self.profile_url, {
            'display_name': 'Code Learner',
            'bio': 'Building with Django.',
            'phone_number': '+1 555 010 2026',
            'instagram_url': 'https://instagram.com/codelearner',
            'linkedin_url': 'https://linkedin.com/in/codelearner',
            'x_url': 'https://x.com/codelearner',
            'receive_newsletter': 'on',
            'username': 'changed-user',
            'email': 'changed@example.test',
        })

        self.assertRedirects(response, self.profile_url)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, 'Code Learner')
        self.assertEqual(profile.bio, 'Building with Django.')
        self.assertEqual(profile.phone_number, '+1 555 010 2026')
        self.assertEqual(profile.instagram_url, 'https://instagram.com/codelearner')
        self.assertEqual(profile.linkedin_url, 'https://linkedin.com/in/codelearner')
        self.assertEqual(profile.x_url, 'https://x.com/codelearner')
        self.assertTrue(profile.receive_newsletter)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'profile-user')
        self.assertEqual(self.user.email, 'changed@example.test')

    def test_profile_rejects_an_email_used_by_another_account(self):
        get_user_model().objects.create_user(
            username='email-owner',
            email='already-used@example.test',
            password='Email-owner-password!928',
        )
        self.client.force_login(self.user)

        response = self.client.post(self.profile_url, {
            'display_name': 'Code Learner',
            'bio': '',
            'phone_number': '',
            'instagram_url': '',
            'linkedin_url': '',
            'x_url': '',
            'email': 'already-used@example.test',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'profile@example.test')

    def test_profile_picture_upload_is_saved(self):
        image_data = BytesIO()
        Image.new('RGB', (4, 4), color='firebrick').save(image_data, format='JPEG')
        image = SimpleUploadedFile('portrait.jpg', image_data.getvalue(), content_type='image/jpeg')
        self.client.force_login(self.user)

        response = self.client.post(self.profile_url, {
            'display_name': 'Photo Profile',
            'bio': 'A profile with a photo.',
            'phone_number': '',
            'instagram_url': '',
            'linkedin_url': '',
            'x_url': '',
            'email': 'profile@example.test',
            'profile_picture': image,
        })

        self.assertRedirects(response, self.profile_url)
        profile = UserProfile.objects.get(user=self.user)
        self.assertTrue(profile.profile_picture.name.startswith('profiles/'))
        self.assertTrue(profile.profile_picture.storage.exists(profile.profile_picture.name))


class ProjectShowcaseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='project-owner',
            email='project-owner@example.test',
            password='Project-owner-password!928',
        )
        self.other_user = get_user_model().objects.create_user(
            username='other-owner',
            email='other-owner@example.test',
            password='Other-owner-password!928',
        )
        self.profile, _ = UserProfile.objects.update_or_create(
            user=self.user,
            defaults={'display_name': 'Project Owner'},
        )
        self.profile_url = reverse('profile')

    def project_data(self, name='InstaLab'):
        return {
            'action': 'add_project',
            'name': name,
            'description': 'A healthcare technology platform.',
            'technologies': 'Python, Django, DRF, MySQL',
            'github_url': 'https://github.com/project-owner/instalab',
            'live_url': 'https://instalab.example.test',
        }

    def test_owner_can_add_project_and_it_is_shown_publicly(self):
        self.client.force_login(self.user)

        response = self.client.post(self.profile_url, self.project_data())

        self.assertRedirects(response, f'{self.profile_url}#projects')
        project = Project.objects.get(profile=self.profile)
        self.assertEqual(project.name, 'InstaLab')
        public_response = self.client.get(reverse('member_profile', kwargs={'username': self.user.username}))
        self.assertContains(public_response, 'InstaLab')
        self.assertContains(public_response, 'Python, Django, DRF, MySQL')

    def test_profile_allows_at_most_five_projects(self):
        Project.objects.bulk_create([
            Project(
                profile=self.profile,
                name=f'Project {index}',
                description='A project description.',
                technologies='Python',
            )
            for index in range(5)
        ])
        self.client.force_login(self.user)

        response = self.client.post(self.profile_url, self.project_data('Sixth project'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You’ve reached the five-project showcase limit.')
        self.assertEqual(Project.objects.filter(profile=self.profile).count(), 5)

    def test_project_removal_is_limited_to_the_owner(self):
        project = Project.objects.create(
            profile=self.profile,
            name='Owner project',
            description='A project description.',
            technologies='Python',
        )
        remove_url = reverse('remove_project', kwargs={'project_id': project.pk})
        self.client.force_login(self.other_user)

        forbidden_response = self.client.post(remove_url)

        self.assertEqual(forbidden_response.status_code, 404)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

        self.client.force_login(self.user)
        response = self.client.post(remove_url)

        self.assertRedirects(response, f'{self.profile_url}#projects')
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_profile_editor_renders_project_form(self):
        self.client.force_login(self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['project_form'], ProjectForm)
        self.assertContains(response, 'My projects')


class CommunityPaginationTests(TestCase):
    def test_directory_displays_twenty_profiles_per_page(self):
        user_model = get_user_model()
        users = [
            user_model(username=f'directory-{index:02}', email=f'directory-{index}@example.test')
            for index in range(25)
        ]
        user_model.objects.bulk_create(users)
        saved_users = user_model.objects.filter(username__startswith='directory-')
        UserProfile.objects.bulk_create([UserProfile(user=user) for user in saved_users])
        viewer = user_model.objects.create_user(
            username='directory-viewer',
            password='Directory-viewer-password!928',
        )
        self.client.force_login(viewer)

        first_page = self.client.get(reverse('community'))
        second_page = self.client.get(reverse('community'), {'page': 2})

        self.assertEqual(len(first_page.context['page_obj'].object_list), 20)
        self.assertEqual(len(second_page.context['page_obj'].object_list), 5)
        self.assertContains(first_page, 'Next')
        self.assertContains(second_page, 'Previous')


class MemberConnectionListTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.member = user_model.objects.create_user(username='list-member', password='List-member-password!928')
        self.follower = user_model.objects.create_user(username='list-follower', password='List-follower-password!928')
        self.following = user_model.objects.create_user(username='list-following', password='List-following-password!928')
        UserProfile.objects.update_or_create(user=self.member, defaults={'display_name': 'List Member'})
        UserProfile.objects.update_or_create(user=self.follower, defaults={'display_name': 'Member Follower'})
        UserProfile.objects.update_or_create(user=self.following, defaults={'display_name': 'Member Following'})
        UserFollow.objects.create(follower=self.follower, followed=self.member)
        UserFollow.objects.create(follower=self.member, followed=self.following)

    def test_followers_and_following_pages_list_the_correct_people(self):
        self.client.force_login(self.member)

        followers_response = self.client.get(reverse('member_followers', kwargs={'username': self.member.username}))
        following_response = self.client.get(reverse('member_following', kwargs={'username': self.member.username}))

        self.assertContains(followers_response, 'Member Follower')
        self.assertNotContains(followers_response, 'Member Following')
        self.assertContains(following_response, 'Member Following')
        self.assertNotContains(following_response, 'Member Follower')


class CommunityTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(
            username='community-viewer',
            email='viewer@example.test',
            password='Community-viewer-password!928',
        )
        self.member = user_model.objects.create_user(
            username='community-member',
            email='member@example.test',
            password='Community-member-password!928',
        )
        self.viewer_profile, _ = UserProfile.objects.update_or_create(
            user=self.viewer,
            defaults={'display_name': 'Community Viewer'},
        )
        self.member_profile, _ = UserProfile.objects.update_or_create(
            user=self.member,
            defaults={
                'display_name': 'Django Developer',
                'bio': 'Building useful software with Python.',
                'phone_number': '+1 555 010 2121',
                'show_email': True,
            },
        )
        self.member_url = reverse('member_profile', kwargs={'username': self.member.username})
        self.follow_url = reverse('toggle_follow', kwargs={'username': self.member.username})

    def test_authenticated_member_profile_shows_opted_in_email_but_not_phone(self):
        self.client.force_login(self.viewer)

        response = self.client.get(self.member_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Developer')
        self.assertContains(response, 'mailto:member@example.test')
        self.assertNotContains(response, '+1 555 010 2121')

    def test_authenticated_member_profile_hides_email_without_opt_in(self):
        self.member_profile.show_email = False
        self.member_profile.save(update_fields=['show_email'])
        self.client.force_login(self.viewer)

        response = self.client.get(self.member_url)

        self.assertNotContains(response, 'mailto:member@example.test')

    def test_community_search_finds_member_by_profile_name(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse('community'), {'q': 'Django Developer'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Developer')
        self.assertNotContains(response, 'Community Viewer')

    def test_anonymous_visitors_cannot_view_community_profiles_or_connections(self):
        urls = [
            reverse('community'),
            self.member_url,
            reverse('member_followers', kwargs={'username': self.member.username}),
            reverse('member_following', kwargs={'username': self.member.username}),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('login')))

    def test_follow_and_unfollow_toggle_the_relationship(self):
        self.client.force_login(self.viewer)

        follow_response = self.client.post(self.follow_url)

        self.assertRedirects(follow_response, self.member_url)
        self.assertTrue(UserFollow.objects.filter(follower=self.viewer, followed=self.member).exists())
        self.assertContains(self.client.get(self.member_url), 'Following · Unfollow')

        unfollow_response = self.client.post(self.follow_url)

        self.assertRedirects(unfollow_response, self.member_url)
        self.assertFalse(UserFollow.objects.filter(follower=self.viewer, followed=self.member).exists())

    def test_users_cannot_follow_themselves(self):
        self.client.force_login(self.viewer)
        own_follow_url = reverse('toggle_follow', kwargs={'username': self.viewer.username})

        response = self.client.post(own_follow_url)

        self.assertRedirects(response, reverse('member_profile', kwargs={'username': self.viewer.username}))
        self.assertFalse(UserFollow.objects.filter(follower=self.viewer, followed=self.viewer).exists())

    def test_follow_action_requires_login_and_post(self):
        anonymous_response = self.client.post(self.follow_url)
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.follow_url).status_code, 405)


class BlogApiAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='api-client',
            password='API-client-password!927',
        )
        self.client = APIClient()
        self.blog_list_url = reverse('blog_api:blog-list')

    def create_blog(self):
        unit = Unit.objects.create(name='API Testing', slug='api-testing')
        blog = Blog.objects.create(
            unit=unit,
            title='Original API title',
            slug='original-api-title',
            content='Original API content',
            image_url='articles/original.jpg',
            author='API Tester',
        )
        return blog, reverse('blog_api:blog-detail', kwargs={'pk': blog.pk})

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label='blog',
            codename__in=codenames,
        )
        self.user.user_permissions.set(permissions)

    def test_blog_api_allows_public_reads(self):
        response = self.client.get(self.blog_list_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)

    def test_api_schema_and_docs_are_available(self):
        schema_response = self.client.get(reverse('api_schema'))
        docs_response = self.client.get(reverse('api_docs'))

        self.assertEqual(schema_response.status_code, 200)
        self.assertIn(b'CodePulse API', schema_response.content)
        self.assertEqual(docs_response.status_code, 200)

    def test_anonymous_users_cannot_write_to_the_api(self):
        response = self.client.post(
            self.blog_list_url,
            {'title': 'Unauthorized'},
            format='json',
        )

        self.assertIn(response.status_code, (401, 403))

    def test_invalid_jwt_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')

        response = self.client.get(self.blog_list_url)

        self.assertIn(response.status_code, (401, 403))

    def test_search_and_ordering_filter_blog_results(self):
        blog, _ = self.create_blog()
        Blog.objects.create(
            unit=blog.unit,
            title='Searchable API article',
            slug='searchable-api-article',
            content='A searchable article.',
            image_url='articles/searchable.jpg',
            author='Another Author',
        )

        search_response = self.client.get(self.blog_list_url, {'search': 'Searchable'})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.data['count'], 1)
        self.assertEqual(search_response.data['results'][0]['title'], 'Searchable API article')

        ordering_response = self.client.get(self.blog_list_url, {'ordering': 'title'})
        self.assertEqual(ordering_response.status_code, 200)
        titles = [result['title'] for result in ordering_response.data['results']]
        self.assertEqual(titles, sorted(titles))

    def test_session_auth_requires_add_permission_for_writes(self):
        self.assertTrue(self.client.login(username='api-client', password='API-client-password!927'))
        response = self.client.post(self.blog_list_url, {'title': 'Incomplete'}, format='json')
        self.assertEqual(response.status_code, 403)

        add_permission = Permission.objects.get(
            content_type__app_label='blog',
            codename='add_blog',
        )
        self.user.user_permissions.add(add_permission)
        response = self.client.post(self.blog_list_url, {'title': 'Incomplete'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_jwt_auth_requires_and_accepts_model_permissions(self):
        token_response = self.client.post(
            reverse('blog_api:token_obtain_pair'),
            {'username': 'api-client', 'password': 'API-client-password!927'},
            format='json',
        )
        self.assertEqual(token_response.status_code, 200)

        access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.blog_list_url, {'title': 'Incomplete'}, format='json')
        self.assertEqual(response.status_code, 403)

        add_permission = Permission.objects.get(
            content_type__app_label='blog',
            codename='add_blog',
        )
        self.user.user_permissions.add(add_permission)
        response = self.client.post(self.blog_list_url, {'title': 'Incomplete'}, format='json')
        self.assertEqual(response.status_code, 400)

        refresh_response = self.client.post(
            reverse('blog_api:token_refresh'),
            {'refresh': token_response.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, 200)

    def test_session_auth_can_update_with_change_permission(self):
        blog, detail_url = self.create_blog()
        self.assertTrue(self.client.login(username='api-client', password='API-client-password!927'))

        response = self.client.patch(
            detail_url,
            {'title': 'Updated through the API'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        self.grant_permissions('view_blog', 'change_blog')
        response = self.client.patch(
            detail_url,
            {'title': 'Updated through the API'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        blog.refresh_from_db()
        self.assertEqual(blog.title, 'Updated through the API')

        invalid_response = self.client.patch(
            detail_url,
            {'title': ''},
            format='json',
        )
        self.assertEqual(invalid_response.status_code, 400)

    def test_jwt_auth_can_delete_with_delete_permission(self):
        blog, detail_url = self.create_blog()
        token_response = self.client.post(
            reverse('blog_api:token_obtain_pair'),
            {'username': 'api-client', 'password': 'API-client-password!927'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 403)

        self.grant_permissions('view_blog', 'delete_blog')
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Blog.objects.filter(pk=blog.pk).exists())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='password-reset-user',
            email='password-reset@example.test',
            password='Original-secure-password!928',
        )

    def test_password_reset_email_can_change_password(self):
        form_response = self.client.get(reverse('password_reset'))
        self.assertTemplateUsed(form_response, 'blog/auth/password_reset_form.html')

        response = self.client.post(
            reverse('password_reset'),
            {'email': self.user.email},
        )
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        reset_match = re.search(r'(/blog/reset/[^/\s]+/[^/\s]+/)', mail.outbox[0].body)
        self.assertIsNotNone(reset_match)
        reset_path = reset_match.group(1)

        confirm_response = self.client.get(reset_path, follow=True)
        self.assertTemplateUsed(confirm_response, 'blog/auth/password_reset_confirm.html')
        confirm_path = confirm_response.request['PATH_INFO']
        new_password = 'Orbit-Birch-764!Saffron'
        response = self.client.post(
            confirm_path,
            {
                'new_password1': new_password,
                'new_password2': new_password,
            },
        )

        self.assertRedirects(response, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_unknown_email_gets_same_confirmation_response(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'not-registered@example.test'},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)
