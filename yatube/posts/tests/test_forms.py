from http import HTTPStatus
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
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.user = User.objects.create_user(username='user_test')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Test post', 'group': PostFormTests.group.id},
            follow=True
)

        self.assertEqual(response.status_code, HTTPStatus.OK) 
        self.assertEqual(Post.objects.count(), 1) 
        post = Post.objects.first()
        self.assertEqual(post.text, 'Test post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, PostFormTests.group) 
 

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        post = Post.objects.create(
            text='test',
            author=self.user,
            group=PostFormTests.group
)
        new_post_text = 'new text'
        new_group = Group.objects.create(
            title='New Test group',
            slug='new-test-group',
            description='new test description'
)       
        self.authorized_client.post(
            reverse('posts:post_edit', args=[post.id,]),
            data={'text': new_post_text, 'group': new_group.id},
            follow=True,
) 
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, new_post_text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, new_group) 
        """Проверка, что поста нет в прошлой группе"""
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug,])
)

        self.assertEqual(old_group_response.context['page_obj'].paginator.count, 0)

    def test_unauth_user_cant_publish_post(self):
        """Неавторизованный юзер при попытке создать запись
        направляется на страницу авторизации
        """
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(posts_count, Post.objects.count())