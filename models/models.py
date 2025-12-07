import uuid
from django.db import models
from django.contrib.auth.models import User

# Model representing a group of audio transcriptions associated with a user
class TranscriptionGroup(models.Model):
    # Status options for the transcription group
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Group is waiting for processing
        ('in_process', 'In Process'),  # At least one audio is being processed
        ('processed', 'Processed'),  # All audios have been successfully processed
        ('failed', 'Failed'),  # At least one audio failed to process
        ('cancelled', 'Cancelled'),  # Processing was cancelled
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Unique identifier for the group
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # User who owns this group
    group_name = models.CharField(max_length=100, null=False, blank=False)  # Name of the group
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current status of the group
    creation_date = models.DateTimeField(auto_now_add=True)  # Timestamp when the group was created
    completion_date = models.DateTimeField(null=True, blank=True)  # Optional timestamp when processing completed
    # Campos para almacenar información de validación
    validation_date = models.DateTimeField(null=True, blank=True)  # Timestamp when validation was completed
    validation_status = models.CharField(max_length=20, null=True, blank=True)  # Success or error status
    validation_result = models.JSONField(null=True, blank=True)  # Detailed validation results
    validation_score = models.FloatField(null=True, blank=True)  # Global validation score from 0 to 5
    validation_calification = models.FloatField(null=True, blank=True) # Feedback score from 0 to 5
    validation_comment = models.TextField(null=True, blank=True) # Feedback comment

    def __str__(self):
        # Human-readable representation of the transcription group
        return f"{self.group_name} ({self.id})"

    def update_status(self):
        # Updates the status of the group based on the statuses of associated audios
        audios = self.audios.all()  # Retrieve all audio files linked to this group

        # Check the statuses of the associated audios and update group status accordingly
        if all(audio.status == 'processed' for audio in audios):
            self.status = 'processed'
        elif any(audio.status == 'in_process' for audio in audios):
            self.status = 'in_process'
        elif any(audio.status == 'failed' for audio in audios):
            self.status = 'failed'
        elif all(audio.status == 'cancelled' for audio in audios):
            self.status = 'cancelled'
        else:
            self.status = 'pending'

        self.save()  # Save the updated status to the database

# Model representing an individual audio transcription
class AudioTranscription(models.Model):
    # Status options for the audio transcription
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Audio is waiting for processing
        ('in_process', 'In Process'),  # Audio is currently being processed
        ('processed', 'Processed'),  # Audio has been successfully processed
        ('failed', 'Failed'),  # Audio processing failed
        ('cancelled', 'Cancelled'),  # Processing was cancelled
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Unique identifier for the audio
    transcription_group = models.ForeignKey(
        TranscriptionGroup, 
        related_name='audios',  # Enables reverse lookup from group to audios
        on_delete=models.SET_NULL,  # Allows group deletion without deleting the audios
        null=True
    )
    order = models.PositiveIntegerField(default=0) # Order for the audio in the group
    file = models.FileField(upload_to='audios/')  # Field to store the audio file
    file_name = models.CharField(max_length=255, blank=True)  # Optional field to store a custom file name
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current status of the audio
    upload_date = models.DateTimeField(auto_now_add=True)  # Timestamp when the audio was uploaded
    transcription_date = models.DateTimeField(null=True, blank=True)  # Optional timestamp when transcription completed
    task_id = models.CharField(max_length=255, null=True, blank=True)  # id tarea Celery que transcribe este segmento

    class Meta:
        ordering = ['order']

    def __str__(self):
        # Human-readable representation of the audio transcription
        return f"Audio {self.file_name} ({self.status})"

class SpeechSegment(models.Model):
    SPEAKER_TYPE_CHOICES = [
        ('atco', 'ATCO'),
        ('pilot', 'Pilot'),
        ('', 'Unspecified'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio = models.ForeignKey(
        AudioTranscription,
        related_name='segments',
        on_delete=models.CASCADE
    )
    segment_file = models.FileField(upload_to='segments/', null=True, blank=True)
    speaker_type = models.CharField(max_length=10, choices=SPEAKER_TYPE_CHOICES, default='', blank=True)
    text = models.TextField(null=True, blank=True)
    modified_text = models.TextField(null=True, blank=True)
    start_time = models.FloatField(null=True, blank=True)
    end_time = models.FloatField(null=True, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.audio.file_name} - {self.order}"
