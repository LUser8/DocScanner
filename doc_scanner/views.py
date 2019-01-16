from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from .models import FilesAddress, Source, DriveUserInfo, FileLoc
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
from .py_codes.api.google.drive.GoogleDriveOperation import GoogleDriveOperation
from django.http.response import HttpResponseBadRequest, HttpResponse
from flask import send_file

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
def file_operations(request, pk, operation):
    src = Source.objects.get(id=pk)

    if not operation:
        return HttpResponseBadRequest(400, "Operation type not given")

    if src.source_type == 'google_drive':
        drive = GoogleDriveOperation(CLIENT_ID, CLIENT_SECRET, src)

        if drive.notlinked:
            return HttpResponseBadRequest("Account not linked!")

        if operation == 'get_all_file_info':
            return JsonResponse(drive.get_all_files_info())

        if operation == 'download':
            try:
                print(operation)
                file_id = request.POST.get("file_id")
                print("Post Data", request.POST.get("file_id"))
                file_info = drive.get_file_info(file_id)

                print("file_info:", file_info)
                # TODO: check permissions

                if request.POST.get("export_to") == 'application/vnd.google-apps.spreadsheet':
                    fp = drive.download(file_id, file_info, export_to=request.POST.get("export_to"))
                else:
                    fp = drive.download(file_id, file_info)
                messages.success(request, "File downloaded successfully")
                print("success")
                # return HttpResponse("Hello")
                return redirect("elibot-scanner-files-detail", pk=request.POST.get("addr_id"))

            except Exception as e:
                print(e)
                return HttpResponseBadRequest(400, str(e))

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


def func_redirect_logic(request):
    context = {
        'request': request
    }
    return render(request, "doc_scanner_admin/test.html", context)


class FileAddressCreateView(LoginRequiredMixin, CreateView):
    model = FilesAddress
    fields = ['source', 'file_list']
    template_name = "doc_scanner_admin/file_address_create.html"

    def form_valid(self, form):
        # print("length:", self.request.POST.getlist("file_list-file_address"))
        file_loc_data = zip(
            self.request.POST.getlist("file_list-file_address"),
            self.request.POST.getlist("file_list-file_name"),
            self.request.POST.getlist("file_list-file_mime_type"),
        )
        file_loc_obj = []
        for file in file_loc_data:
            obj = FileLoc(file_address=file[0], file_mime_type=file[2], file_name=file[1])
            file_loc_obj.append(obj)
        FilesAddress.objects.create(
            source=form.cleaned_data.get("source"),
            file_list=file_loc_obj
        )

        return redirect('elibot-scanner-files-list')

    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     # Add in a QuerySet of all the books
    #     context['source'] = Source.objects.all()
    #
    #     return context


class FileAddressDetailView(LoginRequiredMixin, DetailView):
    model = FilesAddress
    template_name = "doc_scanner_admin/file_address_detail.html"


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
