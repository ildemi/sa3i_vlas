from django.conf import settings
from rest_framework import serializers
from models.models import TranscriptionGroup, AudioTranscription, SpeechSegment

class TranscriptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptionGroup
        fields = ['id', 'status', 'creation_date', 'completion_date', 'user', 'group_name', 'validation_status', 'validation_date', 'validation_result', 'validation_score', 'validation_calification', 'validation_comment']

class SpeechSegmentSerializer(serializers.ModelSerializer):
    segment_file_url = serializers.SerializerMethodField()
    audio = serializers.PrimaryKeyRelatedField(queryset=AudioTranscription.objects.all())

    class Meta:
        model = SpeechSegment
        fields = ['id', 'audio', 'speaker_type', 'text', 'modified_text', 'order', 'segment_file', 'segment_file_url']
        read_only_fields = ['segment_file_url']

    def get_segment_file_url(self, obj):
        if obj.segment_file and hasattr(obj.segment_file, 'url'):
            return settings.SITE_URL + obj.segment_file.url
        return None

class AudioTranscriptionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    transcription_group = serializers.PrimaryKeyRelatedField(queryset=TranscriptionGroup.objects.all(), required=False)
    speech_segments = SpeechSegmentSerializer(many=True, read_only=True, source='segments')

    class Meta:
        model = AudioTranscription
        fields = ['id', 'file', 'file_name', 'file_url', 'status', 'upload_date', 'transcription_date', 'transcription_group', 'speech_segments', 'order']

    def get_file_url(self, obj):
        file_path = obj.file.url
        return settings.SITE_URL + file_path
