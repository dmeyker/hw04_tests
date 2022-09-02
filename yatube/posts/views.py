from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from .utils import paginate_page

def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author", "group")
    page_obj = paginate_page(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author')
    page_obj = paginate_page(request, posts)
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'author': author,
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    context = {
        'is_edit': False,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {
        'is_edit': True,
        'form': form,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def delete_post(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.user == post.author:
        post.delete()
    return redirect('posts:index')


# КОММЕНТАРИИ


@login_required
def add_comment(request, post_id):
    """Создание комментария."""
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# ПОДПИСКА-ОТПИСКА


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    title = "Страница постов с подписками"
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, posts)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    """Функция подписки на автора."""
    author = get_object_or_404(User, username=username)
    check_follow = Follow.objects.filter(
        author=author, user=request.user
    ).exists()
    if not check_follow and request.user != author:
        request.user.follower.create(author=author)
    return redirect('posts:follow_index')

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(
        Follow,
        author=author.id,
        user=request.user.id
    )
    follow.delete()
    return redirect('posts:profile', username=username)
