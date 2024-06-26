from django.shortcuts import (
    render, get_object_or_404, reverse, redirect, HttpResponseRedirect
)
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Thread, TOPICS, Comment
from .forms import CommentForm, ThreadForm


# This function requires the user to be logged in.
# It retrieves a list of threads followed by the current user.
# It renders a template displaying the profile page,
# and the list of followed threads.
@login_required
def follow_list(request):
    new = Thread.objects.filter(follow=request.user)
    return render(
        request,
        "forum/profile.html",
        {"new": new},
    )


# This function requires the user to be logged in.
# It allows users to add or remove threads from their followed list.
# It redirects the user back to previous page after the action is completed.
@login_required
def follow_add(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    if thread.follow.filter(id=request.user.pk).exists():
        thread.follow.remove(request.user)
        messages.add_message(request, messages.SUCCESS, 'Unfollowed thread!')
    else:
        thread.follow.add(request.user)
        messages.add_message(request, messages.SUCCESS, 'Followed thread!')
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


# This class-based view displays a list of threads based on the selected topic,
# or all threads if no topic is selected.
class ThreadList(generic.ListView):
    template_name = "forum/index.html"

    def get_queryset(self):
        topic_id = self.request.GET.get('topic', None)
        if topic_id is not None and topic_id != "":
            queryset = Thread.objects.filter(topic=topic_id)
        else:
            queryset = Thread.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = TOPICS
        context['thread_form'] = ThreadForm()
        return context


# This function requires the user to be logged in.
# It allows users to create a new thread.
# It renders the index page with a form to create a new thread.
@login_required
def create_thread(request):
    if request.method == "POST":
        thread_form = ThreadForm(data=request.POST)
        if thread_form.is_valid():
            thread = thread_form.save(commit=False)
            thread.author = request.user
            thread.save()
            messages.add_message(request, messages.SUCCESS,
                                 'YAY! You posted a new thread!')
            return redirect('thread_detail', slug=thread.slug)
        else:
            messages.info(request,
                          "There is some error with the details you provided. "
                          "Please retry.")

    else:  # For GET requests or invalid POST data
        thread_form = ThreadForm()

    return render(
        request,
        "forum/index.html",
        {
            'thread_form': thread_form,
            'topics': TOPICS,
            'thread_list': Thread.objects.all()
        },
    )


# This function displays details of a specific thread, including its comments.
# It also allows users to add comments to the thread.
def thread_detail(request, slug):
    queryset = Thread.objects.all()
    thread = get_object_or_404(queryset, slug=slug)
    comments = thread.comments.all().order_by("-created_on")
    comment_count = thread.comments.count()

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.thread = thread
            comment.save()
            messages.success(request,
                             f"Comment '{comment.body}' created successfully!")
            return redirect('thread_detail', slug=comment.thread.slug)
        else:
            messages.error(request,
                           "Failed to create comment. Please try again!")

    comment_form = CommentForm()

    return render(
        request,
        "forum/thread_detail.html",
        {
            "thread": thread,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
        },
    )


# This function allows users to edit their comments on a thread.
def comment_edit(request, slug, comment_id):
    if request.method == "POST":
        queryset = Thread.objects.all()
        thread = get_object_or_404(queryset, slug=slug)
        comment = get_object_or_404(Comment, comment_id=comment_id)
        comment_form = CommentForm(data=request.POST, instance=comment)

        if comment_form.is_valid() and comment.author == request.user:
            comment = comment_form.save(commit=False)
            comment.thread = thread
            comment.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Comment updated!')
        else:
            messages.add_message(request, messages.ERROR,
                                 'Error updating comment!')

    return HttpResponseRedirect(reverse('thread_detail', args=[slug]))


# This function allows users to delete their comments on a thread.
def comment_delete(request, slug, comment_id):
    queryset = Thread.objects.all()
    thread = get_object_or_404(queryset, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(request, messages.ERROR,
                             'You can only delete your own comments!')

    return redirect('thread_detail', slug=thread.slug)
