from django.db import models as django_models
from djongo import models as djongo_models


class DriveFileId(djongo_models.Model):
    file_id = djongo_models.URLField()

    class Meta:
        abstract = True


class SourceDrive(djongo_models.Model):
    userId = djongo_models.EmailField()
    password = djongo_models.CharField(max_length=500)
    fileIds = djongo_models.ArrayModelField(
        model_container=DriveFileId
    )

    objects = djongo_models.DjongoManager()

    def __str__(self):
        return "drive_source" + '_' + str(self.id) + '_' + self.userId


class SourceRemote(djongo_models.Model):
    systemIP = djongo_models.GenericIPAddressField()
    username = djongo_models.CharField(max_length=100)
    password = djongo_models.CharField(max_length=500)
    file_path = djongo_models.CharField(max_length=200)

    objects = djongo_models.DjongoManager()

    def __str__(self):
        return "remote_source" + '_' + str(self.id) + '_' + self.username


class DocumentType(djongo_models.Model):
    doc_type = djongo_models.CharField(max_length=100)
    parent_id = djongo_models.CharField(max_length=10)
    multi_template_doc = djongo_models.BooleanField(default=False)
    label = djongo_models.BooleanField(default=False)
    creation_date = djongo_models.DateTimeField(auto_now_add=True)
    last_update = djongo_models.DateTimeField(auto_now=True)

    objects = djongo_models.DjongoManager()

    def __str__(self):
        return "Doc_type" + '_' + self.doc_type


class TemplateMetadata(djongo_models.Model):
    key = djongo_models.CharField(max_length=50)
    value_data_type = djongo_models.CharField(max_length=50)

    class Meta:
        abstract = True


class DocumentTemplate(djongo_models.Model):
    doc_type = djongo_models.ForeignKey(DocumentType, on_delete=djongo_models.CASCADE)
    template_name = djongo_models.CharField(max_length=50, default=None)
    creation_date = djongo_models.DateTimeField(auto_now_add=True)
    last_update = djongo_models.DateTimeField(auto_now=True)
    fields = djongo_models.ArrayModelField(
        model_container=TemplateMetadata
    )

    objects = djongo_models.DjongoManager()

    def __str__(self):
        return "Template_Id" + '_' + str(self.id)


class CaptureTrigger(djongo_models.Model):
    ONES = "ones"
    DAILY = "daily"
    WEEK = "weekly"
    MONTH = "monthly"
    ANNUAL = "annually"
    FREQUENCY_CHOICE = (
        (ONES, "Ones"),
        (DAILY, "Daily"),
        (WEEK, "Weekly"),
        (MONTH, "Monthly"),
        (ANNUAL, "Annually")
    )

    start_date = djongo_models.DateField(blank=True)
    time = djongo_models.TimeField(blank=True)
    frequency = djongo_models.CharField(max_length=10, choices=FREQUENCY_CHOICE, default=DAILY, blank=True)

    class Meta:
        abstract = True


class DocTypeFields(djongo_models.Model):
    doc_field = djongo_models.ForeignKey(DocumentType, on_delete=djongo_models.CASCADE)

    class Meta:
        abstract = True


class Capture(djongo_models.Model):
    LOCAL = 'local'
    DRIVE = 'drive'
    REMOTE = 'remote'
    FILE_LOCATION = (
        (LOCAL, 'Local'),
        (DRIVE, 'Drive'),
        (REMOTE, 'Remote')
    )

    SCHEDULED = "S"
    MANUAL = "M"

    source_type = djongo_models.CharField(max_length=10, choices=FILE_LOCATION, default=LOCAL)
    file_source = djongo_models.CharField(max_length=10)
    document_type = djongo_models.ArrayModelField(
        model_container=DocTypeFields
    )
    target_type = djongo_models.CharField(max_length=10, choices=FILE_LOCATION, default=DRIVE)
    file_target = djongo_models.CharField(max_length=10)
    created = djongo_models.DateTimeField(auto_now_add=True)
    last_update = djongo_models.DateTimeField(auto_now=True)
    status = djongo_models.CharField(max_length=1, editable=False, default=MANUAL)
    trigger = djongo_models.EmbeddedModelField(
        model_container=CaptureTrigger,
        blank=True
    )

    def __str__(self):
        return f'CaptureID {self.id}'





