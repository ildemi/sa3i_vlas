from django.contrib import admin
from .models import AudioTranscription, TranscriptionGroup, SpeechSegment, Airline

# Register your models here.
admin.site.register(TranscriptionGroup)
admin.site.register(AudioTranscription)
admin.site.register(SpeechSegment)

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'icao_code', 'iata_code', 'callsign')
    search_fields = ('name', 'icao_code', 'iata_code', 'callsign')