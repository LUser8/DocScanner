from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import FilesAddress, Source
from django.urls import reverse_lazy


@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        context = {
            "title": "Admin Dashboard"
        }
        return render(request, "elibot_app_admin/admin_dashboard.html", context)
    else:
        context = {
            "title": "Dashboard"
        }
        return render(request, "elibot_app_user/user_dashboard.html", context)


@login_required
def help_view(request):
    context = {
        "title": "Help"
    }
    return render(request, "elibot_app_user/help.html", context)


def elibot_scan(request):
    context = {
        "title": "Elibot Scanner"
    }
    return render(request, "doc_scanner_admin/scan_index.html", context)


class FileAddressListView(LoginRequiredMixin, ListView):
    model = FilesAddress
    template_name = "doc_scanner_admin/file_address_list.html"


class FileAddressCreateView(LoginRequiredMixin, CreateView):
    model = FilesAddress
    fields = ['source', 'file_list']
    template_name = "doc_scanner_admin/file_address_create.html"

    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     # Add in a QuerySet of all the books
    #     context['source'] = Source.objects.all()
    #
    #     return context


class SourceListView(LoginRequiredMixin, ListView):
    model = Source
    template_name = "doc_scanner_admin/source_list.html"


class SourceDetailView(LoginRequiredMixin, DetailView):
    model = Source
    template_name = "doc_scanner_admin/source_detail.html"


class SourceCreateView(LoginRequiredMixin, CreateView):
    model = Source
    fields = ['source_type', 'source_name', 'drive_userId', 'remote_systemIP', 'remote_username', 'remote_password']

    template_name = 'doc_scanner_admin/source_form.html'


class SourceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Source
    fields = ['source_type', 'source_name', 'drive_userId', 'remote_systemIP', 'remote_username', 'remote_password']
    template_name = 'doc_scanner_admin/source_form.html'

    def test_func(self):
        return self.request.user.is_superuser


class SourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Source
    template_name = 'doc_scanner_admin/source_delete_confirm.html'
    success_url = reverse_lazy('elibot-scanner-source-list')

    def test_func(self):
        return self.request.user.is_superuser
