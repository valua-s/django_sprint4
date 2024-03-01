from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from blog.models import Post, Comment
from blog.forms import PostForm, CommentForm


class PostMixin(LoginRequiredMixin):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'


class PostChangeMixin():

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect(
                'blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentMixin(LoginRequiredMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.object.post.id})


class CommentChangeMixin():

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment,
                                     id=self.kwargs['comment_id'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
