from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.utils import timezone
from django.urls import reverse

from blog.mixins import (
    PostMixin, CommentMixin, CommentChangeMixin, PostChangeMixin
)
from blog.models import Post, Category
from blog.forms import CommentForm, PostForm
from blog.constants import Constants

User = get_user_model()


def make_base_post_list():
    return Post.objects.select_related(
        'category', 'author', 'location').annotate(
        comment_count=Count('comment'))


def base_post_list_filter():
    return make_base_post_list().filter(
        is_published=True,
        pub_date__lte=(timezone.now()),
        category__is_published=True,)


def paginator(base_list, quantity_per_page, request):
    paginator = Paginator(base_list, quantity_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


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
    page_obj = paginator(post_list, Constants.QUANTITY_OF_PAGINATE, request)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, 'blog/category.html', context)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            try:
                post = base_post_list_filter().get(pk=self.kwargs['post_id'])
            except post.DoesNotExist:
                raise Http404()
        comments = post.comment.all()
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
        return reverse(
            'blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(PostMixin, PostChangeMixin, UpdateView):

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(PostMixin, PostChangeMixin, DeleteView):

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        context['form'] = PostForm(instance=instance)
        return context


class CommentCreateView(CommentMixin, CreateView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form, **kwargs):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.save()
        return super().form_valid(form)


class CommentUpdateView(CommentMixin, CommentChangeMixin, UpdateView):
    pass


class CommentDeleteView(CommentMixin, CommentChangeMixin, DeleteView):
    pass


class ProfileDetailView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = Constants.QUANTITY_OF_PAGINATE

    def get_queryset(self):
        self.profile = get_object_or_404(User,
                                         username=self.kwargs['username'])
        page_obj = make_base_post_list().filter(author=self.profile
                                                ).order_by('-pub_date')

        if self.request.user != self.profile:
            return page_obj.filter(
                is_published=True,
                pub_date__lte=(timezone.now()),
                category__is_published=True,)
        return page_obj

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

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.object.username})
