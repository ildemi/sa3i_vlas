from django.contrib import admin
from .models import AudioTranscription, TranscriptionGroup, SpeechSegment

# Register your models here.
admin.site.register(TranscriptionGroup)
admin.site.register(AudioTranscription)
admin.site.register(SpeechSegment)