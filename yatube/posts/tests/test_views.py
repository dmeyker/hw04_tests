from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from posts.forms import PostForm
from posts.models import Group, Post, Comment, Follow

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


class TestPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test_user')
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.user2)

        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user2,
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user2,
            post=cls.post,
            text='Тестовый комментарий',
        )

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, TestPosts.user2)
        self.assertEqual(post.pub_date, TestPosts.post.pub_date)
        self.assertEqual(post.text, TestPosts.post.text)
        self.assertEqual(post.group, TestPosts.post.group)
        self.assertEqual(post.image, TestPosts.post.image)

    def test_correct_context_index(self):
        """Проверка index."""
        response = self.auth_client_author.get(reverse('posts:index'))
        self.check_context_contains_page_or_post(response.context)

    def test_correct_context_group_list(self):
        """Проверка group_list."""
        response = self.auth_client_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.check_context_contains_page_or_post(response.context)

        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, TestPosts.group.title)
        self.assertEqual(group.description, TestPosts.group.description)

    def test_correct_context_profile(self):
        """Проверка profile."""
        response = self.auth_client_author.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user2.username}
            )
        )
        self.check_context_contains_page_or_post(response.context)

        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], TestPosts.user2)

    def test_correct_context_post_detail(self):
        """Проверка post_detail."""
        response = self.auth_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id},)
        )
        self.check_context_contains_page_or_post(response.context, post=True)

        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], TestPosts.user2)

    def test_correct_context_post_edit_create(self):
        """Проверка post_edit и create."""
        urls = {
            'edit': reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}),
            'create': reverse('posts:post_create'),
        }
        for name, url in urls.items():
            response = self.auth_client_author.get(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)
            self.assertIn('is_edit', response.context)
            is_edit = response.context['is_edit']
            self.assertIsInstance(is_edit, bool)
            self.assertEqual(is_edit, bool(name == 'edit'))

    def test_paginator_in_pages_with_posts(self):
        """Тест, проверяющий работу пагинатора
        на страницах индекс, групп и профиль."""
        post_count = Post.objects.count()
        paginator_amount = 10
        second_page_amount = post_count + 4

        posts = [
            Post(
                text=f'text {num}', author=TestPosts.user2,
                group=TestPosts.group
            ) for num in range(1, paginator_amount + second_page_amount)
        ]
        Post.objects.bulk_create(posts)
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': TestPosts.group.slug}),
            reverse('posts:profile', kwargs={
                'username': TestPosts.user2.username})
        )
        for url in urls:
            pages = (
                (1, paginator_amount),
                (2, second_page_amount)
            )
            for page, count in pages:
                with self.subTest(page=page):
                    response = self.auth_client_author.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context
                            .get('page_obj').object_list), count)

    def test_comments_checking_add_by_authorized_user(self):
        """Проверка возможности комментировать посты
         авторизованным пользователем."""
        comment_count = Comment.objects.count()
        form_data = {
            'author': self.user2,
            'post': self.post,
            'text': 'Тестовый комментарий',
        }
        response_authorized = self.auth_client_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK)

    def test_comments_checking_add_by_guest_user(self):
        """Проверка возможности комментировать посты
         анонимным пользователем."""
        comment_count = Comment.objects.count()
        form_data = {
            'author': self.user,
            'post': self.post,
            'text': 'Тестовый комментарий',
        }
        response_guest = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response_guest.status_code, HTTPStatus.OK)

    def test_comments_checking_render_on_page(self):
        """Проверка комментариев на странице post_detail."""
        response_authorized = self.auth_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        response_guest = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response_authorized.context['comments'][0],
            self.comment
        )
        self.assertEqual(
            response_guest.context['comments'][0],
            self.comment
        )

    def test_index_page_cache(self):
        """Проверка кеширования главной страницы."""
        post = Post.objects.create(
            author=TestPosts.user,
            group=TestPosts.group,
            text='Кеширский пост',
        )
        first_response = self.auth_client_author.get(
            reverse(f'{"posts:index"}')
        )
        Post.objects.filter(id=post.id).delete()
        response_cached = self.auth_client_author.get(
            reverse(f'{"posts:index"}')
        )
        self.assertEqual(first_response.content, response_cached.content)
        cache.clear()
        second_response = self.auth_client_author.get(
            reverse(f'{"posts:index"}')
        )
        self.assertNotEqual(second_response.content, response_cached.content)

    def test_page_not_found(self):
        """Сервер возвращает код 404, если страница не найдена."""
        page_not_found = self.guest_client.get('/test_url/')
        self.assertEqual(page_not_found.status_code, 404)

    def follow_unfollow(self):
        """Проверка подписки/отписки и появление/отсутствия постов"""
        followes_count = Follow.objects.count()
        self.auth_client_author.get(
            reverse("posts:profile_follow", args=[TestPosts.user.username]))
        self.assertEqual(followes_count + 1, Follow.objects.count())
        self.assertTrue(self.user2.follower.filter(author=self.user))
        # Создаем пост и проверяем появление поста на странице follow
        post = Post.objects.create(
            author=self.user,
            text='Проверочный пост'
        )
        response = self.auth_client_author.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)
        # Отписываемся от пользователя и проверяем
        self.auth_client_author.get(reverse(
            "posts:profile_unfollow", args=[TestPosts.user.username]))
        self.assertEqual(followes_count - 1, Follow.objects.count())
        self.assertFalse(self.user2.follower.filter(author=self.user))
        # Создаем еще один пост и проверяем отсутствие поста на странице
        post = Post.objects.create(
            author=self.user,
            text='Еще один проверочный пост'
        )
        response = self.auth_client_author.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
