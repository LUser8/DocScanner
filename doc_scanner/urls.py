from django.urls import path
from . import views
from.views import (FileAddressListView, FileAddressCreateView, SourceCreateView, SourceListView, SourceDetailView,
                   SourceUpdateView, SourceDeleteView)


urlpatterns = [
    path("admin/", views.dashboard_view, name="doc-scanner-dashboard"),
    path("scan/", views.elibot_scan, name="elibot-scanner"),
    path("scan/files/", FileAddressListView.as_view(), name="elibot-scanner-files-list"),
    path("scan/create/", FileAddressCreateView.as_view(), name="elibot-scanner-file-create"),
    path("scan/source/", SourceListView.as_view(), name="elibot-scanner-source-list"),
    path("scan/source/create/", views.source_select, name="elibot-scanner-source-select"),
    # path("scan/source/create/", SourceCreateView.as_view(), name="elibot-scanner-source-create"),
    path("scan/source/update/<int:pk>/", SourceUpdateView.as_view(), name="elibot-scanner-source-update"),
    path("scan/source/<int:pk>/", SourceDetailView.as_view(), name="elibot-scanner-source-detail"),
    path("scan/source/delete/<int:pk>/", SourceDeleteView.as_view(), name="elibot-scanner-source-delete"),
    path("help/", views.help_view, name="doc-scanner-help")
]
