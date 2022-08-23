from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={
                'slug': PostPagesTests.group.slug})):
            'posts/group_list.html',
            (reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username})):
            'posts/profile.html',
            (reverse('posts:post_detail',
             kwargs={'post_id': PostPagesTests.post.id})):
            'posts/post_detail.html',
            (reverse('posts:post_edit',
             kwargs={'post_id': PostPagesTests.post.id})):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class ContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.user2)

        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст1',
            author=cls.user2,
            group=cls.group,
        )

    def test_correct_context_index(self):
        """Проверка index."""
        response = self.authorized_client_author.get(reverse('posts:index'))
        self.assertIsInstance(response.context['page_obj'][0], Post)

    def test_correct_context_group_list(self):
        """Проверка group_list."""
        response = self.authorized_client_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)

    def test_correct_context_profile(self):
        """Проверка profile."""
        response = self.authorized_client_author.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user2.username}
            )
        )
        self.assertEqual(response.context['user'], self.user2)

    def test_correct_context_post_detail(self):
        """Проверка post_detail."""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, self.post.text)

    def test_correct_context_post_edit(self):
        """Проверка post_edit."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context['form'].initial['text'],
            self.post.text
        )

    def test_correct_context_post_create(self):
        """Проверка post_create."""
        response = self.authorized_client_author.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(response.context['form'], PostForm)


class CreatePostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_test')
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
        )

    def test_correct_post_create_index(self):
        """После создания появился на главной, в группе и профиле."""
        pages_names = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
        )

        for name_page in pages_names:
            with self.subTest(name_page=name_page):
                response = self.authorized_client_author.get(name_page)
                self.assertTrue(
                    response.context['page_obj'][0]
                )
