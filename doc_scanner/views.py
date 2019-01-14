from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import FilesAddress, Source, DriveUserInfo
from django.urls import reverse_lazy
from .models import GoogleAppConfiguration
import socket
from oauth2client.client import OAuth2WebServerFlow
from .forms import SourceRemoteForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from googleapiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from httplib2 import Http
from django.http import JsonResponse


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
    print("Auth Code:", auth_code)
    credentials = flow.step2_exchange(auth_code)
    print("Credential:", credentials.__dict__)
    print("Credential user email id: ", credentials.id_token['email'])
    source_name = f'google_drive_{credentials.id_token["email"]}'
    src = Source.objects.create(source_type='google_drive',
                                source_name=source_name,
                                drive_userId=credentials.id_token['email'],
                                drive_auth_token=auth_code,
                                drive_refresh_token=credentials.refresh_token,
                                drive_access_token=credentials.access_token,
                                drive_token_expiry=credentials.token_expiry
                                )
    src.save()

    drive_user = DriveUserInfo.objects.create(user_source=src,
                                              user_name=credentials.id_token['name'],
                                              user_img_url=credentials.id_token['picture'],
                                              user_email=credentials.id_token['email'])
    drive_user.save()

    return redirect('elibot-scanner-files-list')


@login_required
def file_list(request, pk):
    src = Source.objects.get(id=pk)

    if src.source_type == 'google_drive':
        _creds = OAuth2Credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            refresh_token=src.drive_refresh_token,
            access_token=src.drive_access_token,
            token_expiry=src.drive_token_expiry,
            token_uri="https://oauth2.googleapis.com/token",
            user_agent=None
        )
        service = build('drive', 'v3', http=_creds.authorize(Http()))
        return JsonResponse(service.files().list().execute())
    elif src.source_type == 'remote_system':
        pass


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
                source_name = f'{request.POST["source_type"]}_{form.cleaned_data.get("remote_systemIP")}_' \
                              f'{form.cleaned_data.get("remote_username")}'
                src = Source.objects.create(source_type=request.POST['source_type'],
                                            source_name=source_name,
                                            remote_systemIP=form.cleaned_data.get('remote_systemIP'),
                                            remote_username=form.cleaned_data.get('remote_username'),
                                            remote_password=make_password(form.cleaned_data.get('remote_password'))
                                            )
                src.save()
                messages.success(request, f'Remote Source Created Successfully')
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


# def file_address_create_view(request):
#     return render(request, "doc_scanner_admin/file_address_create.html")


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
