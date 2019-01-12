from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import FilesAddress, Source
from django.urls import reverse_lazy
from .models import GoogleAppConfiguration
import socket
from oauth2client.client import OAuth2WebServerFlow
from .forms import SourceRemoteForm
from django.contrib import messages


CLIENT_ID = ''
CLIENT_SECRET = ''


def set_app_credential():
    global CLIENT_ID, CLIENT_SECRET, flow
    SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/userinfo.profile",
              "https://www.googleapis.com/auth/userinfo.email"]
    redirect_uri = 'http://{}:{}/google/login/save'
    redirect_uri = redirect_uri.format("localhost" or socket.gethostbyname(socket.gethostname()), 8000)

    google_config = GoogleAppConfiguration.objects.all().first()
    CLIENT_ID = google_config.client_id
    CLIENT_SECRET = google_config.client_secret

    flow = OAuth2WebServerFlow(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope=SCOPES,
        prompt='consent',
        redirect_uri=redirect_uri
    )


def login_uri(request):
    auth_uri = flow.step1_get_authorize_url()
    return redirect(auth_uri)


def auth_code_handler(request):
    auth_code = request.GET.get('code')
    # print(auth_code)

    credentials = flow.step2_exchange(auth_code)
    print(credentials.__dict__)
    return redirect('elibot-scanner-files-list')


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
def source_select(request):
    if request.method == 'POST':

        if request.POST['source_type'] == 'google_drive':
            print("In Drive")
            return redirect('google-login')
        elif request.POST['source_type'] == 'remote_system':
            form = SourceRemoteForm(request.POST)
            if form.is_valid():
                form.save()
                messages.SUCCESS(request, f'Remote Source Created Successfully')
                return redirect('elibot-scanner-source-list')
    form = SourceRemoteForm()
    context = {
        'form': form
    }
    return render(request, 'doc_scanner_admin/source_select_list.html', context)


@login_required
def help_view(request):
    context = {
        "title": "Help"
    }
    return render(request, "elibot_app_user/help.html", context)


def elibot_scan(request):
    context = {
        "title": "Elibot Scanner",
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
    ordering = "-last_updated_date"


class SourceDetailView(LoginRequiredMixin, DetailView):
    model = Source
    template_name = "doc_scanner_admin/source_detail.html"


class SourceCreateView(LoginRequiredMixin, CreateView):
    model = Source
    fields = ['source_name', 'source_type', 'drive_userId', 'remote_systemIP', 'remote_username', 'remote_password']
    success_url = reverse_lazy('google-login')

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
