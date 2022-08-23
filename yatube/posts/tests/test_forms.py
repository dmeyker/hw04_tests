import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.user = User.objects.create_user(username='user_test')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()

        form_fields = {
            'text': PostCreateFormTests.post.text,
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_fields,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group.pk,
                text=PostCreateFormTests.post.text,
            ).exists()
        )

    def test_cant_create_post_without_text(self):
        """Форма не создает запись в Post без текста."""
        post_count = Post.objects.count()
        form_fields = {
            'text': '',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )

    def test_edit_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_fields = {
            'text': 'Тестовый текст изм',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_fields,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id}))

        self.assertEqual(Post.objects.count(), post_count)

        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group.pk,
                text=form_fields['text'],
                id=PostCreateFormTests.post.id,
            ).exists()
        )
