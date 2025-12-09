from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('profile/', user_profile, name='get_user_profile'),
    path('change-password/', change_password, name='change_password'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('token/refresh/', refresh_token, name='refresh_token'),
    path('transcribe/<uuid:audio_id>/', TranscribeAudioRetryView.as_view(), name='retry_transcription'),
    path('audios/delete/<uuid:audio_id>/', AudioDeleteView.as_view(), name='delete_audio'),
    path('create-transcription-group/', create_transcription_group, name='create_transcription_group'),
    path('transcription-group/<uuid:group_id>/', get_transcription_group, name='get_transcription_group'),
    path('transcription-group/<uuid:group_id>/delete/', delete_transcription_group, name='delete-transcription-group'),
    path('transcription-group/<uuid:group_id>/download-pdf/', generate_pdf, name='download_pdf'),
    path('transcription-groups/', get_transcription_groups, name='get_transcription_groups'),
    path('transcription-group/<uuid:group_id>/cancel/', cancel_group_transcriptions, name='cancel_group_transcriptions'),
    path('add-audio-to-group/<uuid:group_id>/', add_audio_to_group, name='add-audio-to-group'),
    path('update-audio-order/<uuid:group_id>/', update_audio_order, name='update-audio-order'),
    path('reset-password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset-password-done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset-password-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset-password-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('transcription-group/<uuid:group_id>/calification/', submit_calification, name='submit_calification'),
    path('wer/', get_wer_global, name='get_wer_global'),
    path('segments/update/<uuid:segment_id>/', UpdateSegmentView.as_view(), name='update-segment'),
    path('segments/delete/<uuid:segment_id>/', DeleteSegmentView.as_view(), name='delete-segment'),

    # Login sin autenticación para pruebas
    path('login-test/', test_login, name='test_login'),
]

# Endpoints relacionados con la validación
urlpatterns += [
    path('validate-transcription-group/<uuid:group_id>/', validate_transcription_group, name='validate_transcription_group'),
    path('group-validation-results/<uuid:group_id>', get_group_validation_results, name='get_group_validation_results'),
]

# Endpoints de sistema
urlpatterns += [
    path('system/initialize/', initialize_system, name='initialize_system'),
    path('system/status/', get_system_status, name='get_system_status'),
]
