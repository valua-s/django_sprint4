from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.utils import timezone
from django.urls import reverse_lazy

from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm
from blog.constants import Constants

User = get_user_model()

pub_date__lte = (timezone.now()),


def make_base_post_list():
    return Post.objects.select_related(
        'category', 'author', 'location').annotate(
        comment_count=Count('comment'))


def base_post_list_filter():
    return make_base_post_list().filter(
        is_published=True,
        pub_date__lte=(timezone.now()),
        category__is_published=True,)


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = base_post_list_filter()
    paginate_by = Constants.QUANTITY_OF_PAGINATE
    ordering = '-pub_date'


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, is_published=True, slug=category_slug)
    post_list = base_post_list_filter().filter(
        category=category).order_by(
        '-pub_date')
    paginator = Paginator(post_list, Constants.QUANTITY_OF_PAGINATE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, 'blog/category.html', context)


class PostMixin(LoginRequiredMixin):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'


class PostChangeMixin(PostMixin):

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect(
                'blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            post = get_object_or_404(Post, pk=self.kwargs['post_id'],
                                     is_published=True,
                                     pub_date__lte=(timezone.now()),
                                     category__is_published=True,)
        comments = Comment.objects.filter(post=self.object)
        context.update({
            'post': post,
            'form': CommentForm(),
            'comments': comments
        })
        return context


class PostCreateView(PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(PostChangeMixin, UpdateView):

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(PostChangeMixin, DeleteView):

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user})


class CommentMixin(LoginRequiredMixin):
    model = Comment
    form_class = CommentForm

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.post.id})


class ChangeCommentMixin(CommentMixin):
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment,
                                     id=self.kwargs['comment_id'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(CommentMixin, CreateView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form, **kwargs):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.save()
        return super().form_valid(form)


class CommentUpdateView(ChangeCommentMixin, UpdateView):
    pass


class CommentDeleteView(ChangeCommentMixin, DeleteView):
    pass


class ProfileDetailView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = Constants.QUANTITY_OF_PAGINATE

    def get_queryset(self):
        self.profile = get_object_or_404(User,
                                         username=self.kwargs['username'])
        self.page_obj = make_base_post_list().filter(author=self.profile
                                                     ).order_by('-pub_date')

        if self.request.user != self.profile:
            return self.page_obj.filter(
                is_published=True,
                pub_date__lte=(timezone.now()),
                category__is_published=True,)
        return self.page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'profile': self.profile,
        })
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ('first_name', 'last_name', 'username', 'email')

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.object.username})
