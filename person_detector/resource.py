from .models import DetectedFace
from import_export import resources
from import_export.fields import Field

# Untuk download face detected record
class DetectedFaceResource(resources.ModelResource):
    name = Field(attribute='name', column_name='Detected Name')
    detected_time = Field(attribute='detected_time', column_name='Time Detected')
    class Meta:
        model = DetectedFace
        fields = [
            'name',
            'detected_time'
        ]