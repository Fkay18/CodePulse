import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .forms import BlogForm, ClientSignUpForm
from .models import Blog, Unit


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
