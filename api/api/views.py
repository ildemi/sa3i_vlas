import evaluate, re
from weasyprint import HTML
from .tasks import process_audio_task, cancel_group_tasks, validate_conversation_task
from models.models import TranscriptionGroup, AudioTranscription, SpeechSegment
from .serializers import TranscriptionGroupSerializer, AudioTranscriptionSerializer
from pathlib import Path
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .diarizer import AudioDiarization


def extract_timestamp_from_filename(filename):
    match = re.search(r"(\d{6})", filename)
    if not match:
        return 0
    time_str = match.group(1)
    try:
        hours = int(time_str[0:2])
        minutes = int(time_str[2:4])
        seconds = int(time_str[4:6])
        return (hours * 3600 + minutes * 60 + seconds) * 1000
    except:
        return 0

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_audio_order(request, group_id):
    try:
        # Verificar que el grupo de transcripción existe y pertenece al usuario autenticado
        group = TranscriptionGroup.objects.get(id=group_id, user=request.user)
    except TranscriptionGroup.DoesNotExist:
        return Response({'detail': 'Transcription group not found.'}, status=status.HTTP_404_NOT_FOUND)

    audios_order = request.data.get('audios', [])
    for item in audios_order:
        audio_id = item.get('id')
        order = item.get('order')
        AudioTranscription.objects.filter(id=audio_id, transcription_group_id=group_id).update(order=order)
    return Response({'detail': 'Order updated'}, status=200)


# Vista para obtener todos los grupos de transcripción del usuario autenticado
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transcription_groups(request):
    groups = TranscriptionGroup.objects.filter(user=request.user)
    serializer = TranscriptionGroupSerializer(groups, many=True)
    return Response(serializer.data)


# Vista para obtener un grupo específico de transcripción y sus audios
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transcription_group(request, group_id):
    try:
        # Obtener el grupo de transcripción por su ID y asegurarnos de que pertenece al usuario autenticado
        group = TranscriptionGroup.objects.get(id=group_id, user=request.user)
        
        # Obtener todos los audios asociados a este grupo de transcripción
        audios = AudioTranscription.objects.filter(transcription_group=group)
        
        # Serializar el grupo y los audios relacionados
        group_serializer = TranscriptionGroupSerializer(group)
        audio_serializer = AudioTranscriptionSerializer(audios, many=True)

        # Agregar los audios a la respuesta
        response_data = group_serializer.data
        response_data['audios'] = audio_serializer.data

        # Devolver la respuesta con los datos del grupo y sus audios asociados
        return Response(response_data)
        
    except TranscriptionGroup.DoesNotExist:
        # Si no se encuentra el grupo, retornar un error 404
        return Response({'detail': 'Transcription group not found.'}, status=status.HTTP_404_NOT_FOUND)


class TranscribeAudioRetryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, audio_id):
        try:
            audio = AudioTranscription.objects.get(id=audio_id)

            # Verificar que el usuario es el dueño del audio
            if audio.transcription_group.user != request.user:
                return Response(
                    {'detail': 'You do not have permission to retry transcription for this audio file.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 1. Eliminar todos los SpeechSegment asociados
            audio.segments.all().delete()

            # 2. Reinvocar el diarizador sobre el audio original
            diarizer = AudioDiarization()
            diarized_segments = diarizer.invoke(audio.file.path)

            # 3. Crear nuevos objetos SpeechSegment
            for idx, seg in enumerate(diarized_segments, start=1):
                abs_path = Path(seg['path'])
                relative_path = abs_path.relative_to(settings.MEDIA_ROOT)
                with open(abs_path, 'rb') as f:
                    segment = SpeechSegment(
                        audio=audio,
                        speaker_type='',
                        text=None,
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        order=idx,
                    )
                    segment.segment_file.name = str(relative_path)
                    segment.save()

            # 4. Reiniciar estado del audio
            audio.status = 'pending'
            audio.transcription_date = None
            audio.task_id = None
            audio.save()

            # 5. Actualizar estado del grupo
            audio.transcription_group.update_status()

            # 6. Lanzar tarea asíncrona para transcripción
            task = process_audio_task.delay(audio.id)
            audio.task_id = task.id
            audio.save()

            return Response(
                {'detail': 'Transcription retry (with diarization) initiated successfully.'},
                status=status.HTTP_202_ACCEPTED
            )

        except AudioTranscription.DoesNotExist:
            return Response({'detail': 'Audio file not found.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'detail': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_FILES = 10  # Límite de archivos por solicitud

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transcription_group(request):   
    data = request.data
    data['user'] = request.user.id

    audios = request.FILES.getlist('file')
    media_root = Path(settings.MEDIA_ROOT)

    if len(audios) > MAX_FILES:
        return Response({"error": f"Too many files. Maximum allowed is {MAX_FILES}."}, status=status.HTTP_400_BAD_REQUEST)
    
    for audio in audios:
        if not is_allowed_file(audio.name):
            return Response({"error": f"File type not allowed: {audio.name}"}, status=status.HTTP_400_BAD_REQUEST)       
        if audio.size > MAX_FILE_SIZE:
            return Response({"error": f"File too large: {audio.name}"}, status=status.HTTP_400_BAD_REQUEST)

    group_serializer = TranscriptionGroupSerializer(data=data)

    try:
        diarizer = AudioDiarization()
        if group_serializer.is_valid():
            group = group_serializer.save()     
            created_audios = []

            audios = sorted(audios, key=lambda audio: extract_timestamp_from_filename(audio.name))
            for idx, audio in enumerate(audios, start=1):
                audio_data = {
                    'file': audio,
                    'file_name': audio.name,
                    'status': 'pending',
                    'transcription_group': group.id,
                    'order': idx,
                }
                audio_serializer = AudioTranscriptionSerializer(data=audio_data)
                if audio_serializer.is_valid():
                    audio_instance = audio_serializer.save()
                    created_audios.append(audio_instance)

                    # Ejecutamos el diarizador sobre el archivo guardado
                    audio_path = audio_instance.file.path
                    diarized_segments = diarizer.invoke(audio_path)

                    for idx, seg in enumerate(diarized_segments, start=1):
                        abs_path = Path(seg['path'])
                        # Obtenemos la ruta relativa a MEDIA_ROOT para FileField
                        relative_path = abs_path.relative_to(media_root)

                        # Abrimos el archivo para pasarlo al FileField
                        with open(abs_path, 'rb') as f:
                            segment = SpeechSegment(
                                audio=audio_instance,
                                speaker_type='',
                                text=None,
                                start_time=seg['start_time'],
                                end_time=seg['end_time'],
                                order=idx,
                            )
                            segment.segment_file.name = str(relative_path)
                            segment.save()

                else:
                    # Si error, limpiar todo lo creado
                    for created_audio in created_audios:
                        created_audio.delete()
                    group.delete()
                    return Response(audio_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Lanzar tareas para transcribir cada audio completo o cada segmento
            try:
                for audio_instance in created_audios:
                    task = process_audio_task.delay(audio_instance.id)
                    audio_instance.task_id = task.id
                    audio_instance.save()
            except Exception as e:
                for created_audio in created_audios:
                    created_audio.delete()
                group.delete()
                return Response({"error": "Error al iniciar el procesamiento de audio"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(group_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(group_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(e)
        if 'group' in locals():
            for created_audio in created_audios:
                created_audio.delete()
            group.delete()
        return Response({"error": "Error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_transcription_group(request, group_id):
    try:
        # Intentamos obtener el grupo con el ID proporcionado
        group = TranscriptionGroup.objects.get(id=group_id)
        
        # Verificamos que el usuario es el propietario del grupo o tiene permisos para eliminar
        if group.user != request.user:
            return Response({'detail': 'You do not have permission to delete this group.'}, status=status.HTTP_403_FORBIDDEN)

        # Desvinculamos los audios del grupo, poniendo transcription_group en NULL
        group.audios.update(transcription_group=None)

        # Eliminamos el grupo
        group.delete()

        return Response({'detail': 'Group and its audio files deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    except TranscriptionGroup.DoesNotExist:
        return Response({'detail': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_audio_to_group(request, group_id):
    try:
        group = TranscriptionGroup.objects.get(id=group_id)
        if group.user != request.user:
            return Response({'detail': 'You do not have permission to modify this group.'}, status=status.HTTP_403_FORBIDDEN)
    except TranscriptionGroup.DoesNotExist:
        return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    audios = request.FILES.getlist('file')

    if len(audios) > MAX_FILES:
        return Response({"error": f"Too many files. Maximum allowed is {MAX_FILES}."}, status=status.HTTP_400_BAD_REQUEST)

    for audio in audios:
        if not is_allowed_file(audio.name):
            return Response({"error": f"File type not allowed: {audio.name}"}, status=status.HTTP_400_BAD_REQUEST)
        if audio.size > MAX_FILE_SIZE:
            return Response({"error": f"File too large: {audio.name}"}, status=status.HTTP_400_BAD_REQUEST)

    created_audios = []
    diarizer = AudioDiarization()
    media_root = Path(settings.MEDIA_ROOT)

    try:
        # Obtener los audios existentes
        existing_audios = list(AudioTranscription.objects.filter(transcription_group=group))

        # Preparar los nuevos audios para ser ordenados también
        new_audio_wrappers = [
            {"file": audio, "file_name": audio.name}
            for audio in audios
        ]

        # Combinar todos los audios con su timestamp
        combined = [
            {"instance": audio, "timestamp": extract_timestamp_from_filename(audio.file_name)}
            for audio in existing_audios
        ] + [
            {"file": a["file"], "file_name": a["file_name"], "timestamp": extract_timestamp_from_filename(a["file_name"])}
            for a in new_audio_wrappers
        ]

        # Ordenar por timestamp
        combined_sorted = sorted(combined, key=lambda x: x["timestamp"])

        # Reasignar order y crear los nuevos audios
        for idx, item in enumerate(combined_sorted, start=1):
            if "instance" in item:
                # Audio existente
                instance = item["instance"]
                if instance.order != idx:
                    instance.order = idx
                    instance.save()
            else:
                # Audio nuevo
                audio_instance = AudioTranscription.objects.create(
                    file=item["file"],
                    file_name=item["file_name"],
                    transcription_group=group,
                    status='pending',
                    order=idx,
                )
                created_audios.append(audio_instance)

        # Diarizar y crear segmentos
        for audio_instance in created_audios:
            audio_path = audio_instance.file.path
            diarized_segments = diarizer.invoke(audio_path)

            for idx, seg in enumerate(diarized_segments, start=1):
                abs_path = Path(seg['path'])
                relative_path = abs_path.relative_to(media_root)

                with open(abs_path, 'rb') as f:
                    segment = SpeechSegment(
                        audio=audio_instance,
                        speaker_type='',
                        text=None,
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        order=idx,
                    )
                    segment.segment_file.name = str(relative_path)
                    segment.save()

        # Iniciar tareas de transcripción
        for audio_instance in created_audios:
            task = process_audio_task.delay(audio_instance.id)
            audio_instance.task_id = task.id
            audio_instance.save()

        return Response({"message": "Audios added and reordered successfully."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        for created_audio in created_audios:
            created_audio.delete()
        return Response({"error": "Error processing audios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AudioDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, audio_id):
        try:
            audio = AudioTranscription.objects.get(id=audio_id)

            # Verificar si el usuario es el propietario del audio
            if audio.transcription_group.user != request.user:
                return Response({'detail': 'You do not have permission to delete this audio file.'}, status=status.HTTP_403_FORBIDDEN)

            # Eliminar el archivo
            group = audio.transcription_group  # Obtenemos el grupo asociado al audio
            audio.delete()  # Eliminamos el audio

            # Verificamos si quedan audios asociados al grupo
            if group.audios.count() == 0:
                group.delete()  # Si no quedan audios, eliminamos el grupo
            else:
                group.update_status()

            return Response({'detail': 'Audio file deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

        except AudioTranscription.DoesNotExist:
            return Response({'detail': 'Audio file not found.'}, status=status.HTTP_404_NOT_FOUND)

        except TranscriptionGroup.DoesNotExist:
            return Response({'detail': 'Transcription group not found.'}, status=status.HTTP_404_NOT_FOUND)


class DeleteSegmentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, segment_id):
        try:
            segment = SpeechSegment.objects.get(id=segment_id)

            # Verifica que el usuario es el propietario del grupo
            if segment.audio.transcription_group.user != request.user:
                return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

            segment.delete()
            return Response({"message": "Segment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except SpeechSegment.DoesNotExist:
            return Response({"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)


class UpdateSegmentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, segment_id):
        try:
            segment = SpeechSegment.objects.get(id=segment_id)

            # Verifica que el usuario es el propietario del audio
            if segment.audio.transcription_group.user != request.user:
                return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

            modified_text = request.data.get("modified_text")
            speaker_type = request.data.get("speaker_type")

            # Validaciones
            if modified_text is not None:
                if len(modified_text) > 5000:
                    return Response({"error": "Modified text is too long."}, status=status.HTTP_400_BAD_REQUEST)
                segment.modified_text = modified_text

            if speaker_type is not None:
                if speaker_type not in ['atco', 'pilot', '', 'other']:
                    return Response({"error": "Invalid speaker type. Must be 'atco', 'pilot', or empty."}, status=status.HTTP_400_BAD_REQUEST)
                segment.speaker_type = speaker_type

            segment.save()

            return Response({"message": "Segment updated successfully."}, status=status.HTTP_200_OK)

        except SpeechSegment.DoesNotExist:
            return Response({"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_pdf(request, group_id):
    # Obtener el grupo de transcripción
    group = get_object_or_404(TranscriptionGroup, id=group_id, user=request.user)

    # Obtener los audios asociados al grupo
    audios = group.audios.all()

    # Renderizar la plantilla HTML con el contexto
    html_string = render(request, 'pdf_report.html', {'group': group, 'audios': audios}).content

    # Generar el PDF
    pdf = HTML(string=html_string).write_pdf()

    # Devolver el archivo PDF como respuesta HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={group.group_name.replace(" ", "_")}_report.pdf'
    return response


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    if request.method == 'GET':
        user_data = {
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'lastLogin': request.user.last_login.strftime('%H:%M:%S %d-%m-%Y') if request.user.last_login else 'Never',
        }
        return Response(user_data)

    elif request.method == 'PUT':
        data = request.data
        user = request.user

        # Validar y actualizar el nombre de usuario
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username and new_username != user.username:
                # Verificar si el nombre de usuario ya está en uso
                if User.objects.filter(username=new_username).exists():
                    return Response({'detail': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
                user.username = new_username

        # Validar y actualizar el nombre
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()

        if 'last_name' in data:
            user.last_name = data['last_name'].strip()

        # Validar y actualizar el correo electrónico
        if 'email' in data:
            new_email = data['email'].strip()
            try:
                validate_email(new_email)
                if new_email != user.email:
                    # Verificar si el correo electrónico ya está en uso
                    if User.objects.filter(email=new_email).exists():
                        return Response({'detail': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
                    user.email = new_email
            except ValidationError:
                return Response({'detail': 'Invalid email address'}, status=status.HTTP_400_BAD_REQUEST)

        # Guardar los cambios en el usuario
        try:
            user.save()
            return Response({'detail': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    data = request.data

    # Validar que las contraseñas estén presentes
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not old_password or not new_password or not confirm_password:
        return Response({'detail': 'All password fields are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Verificar la contraseña actual
    if not user.check_password(old_password):
        return Response({'detail': 'Invalid current password'}, status=status.HTTP_400_BAD_REQUEST)

    # Verificar que las nuevas contraseñas coincidan
    if new_password != confirm_password:
        return Response({'detail': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar la fuerza de la nueva contraseña
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    # Cambiar la contraseña
    user.set_password(new_password)
    user.save()

    return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'detail': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user:
        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({'access': access_token, 'refresh': str(refresh)}, status=status.HTTP_200_OK)

    return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_login(request):
    # Puedes usar un usuario existente o uno de pruebas
    user, _ = User.objects.get_or_create(username='usuario_pruebas', defaults={
        'email': 'pruebas@example.com'
    })

    user.last_login = timezone.now()
    user.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({'access': access_token, 'refresh': str(refresh)}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Endpoint para refrescar el token usando un refresh token válido.
    """
    if request.method == 'POST':
        # Extraer el refresh token del cuerpo de la solicitud
        refresh_token = request.data.get('refresh', '')

        if not refresh_token:
            # Si no se proporciona el refresh token
            return Response({'error': 'El refresh token es necesario'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verificar el refresh token y generar un nuevo access token
            refresh = RefreshToken(refresh_token)

            # Obtener un nuevo access token
            access_token = str(refresh.access_token)

            # Devolver la respuesta con el access y refresh token
            return Response({'access': access_token, 'refresh': str(refresh)}, status=status.HTTP_200_OK)

        except Exception as e:
            # Si hay algún problema con el refresh token
            return Response({'error': 'Error al renovar el token'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'error': 'Método no permitido'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class VerifyTokenView(APIView):
    """
    Verifica si un token JWT es válido.
    Si es válido, retorna un estado 200 OK. Si no lo es, retorna un error 401 Unauthorized.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Verifica que el token es válido.
        """
        return Response({"message": "Token is valid."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_group_transcriptions(request, group_id):
    try:
        # Verificar que el grupo existe y pertenece al usuario
        group = get_object_or_404(TranscriptionGroup, id=group_id, user=request.user)
        
        # Llamar a la función que cancela las tareas
        success = cancel_group_tasks(group_id)
        
        if success:
            return Response({
                'detail': 'Las tareas de transcripción han sido canceladas exitosamente.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'detail': 'Hubo un error al cancelar las tareas de transcripción.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except TranscriptionGroup.DoesNotExist:
        return Response({
            'detail': 'Grupo de transcripción no encontrado.'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    data = request.data
    
    # Validar que todos los campos requeridos estén presentes
    required_fields = ['username', 'email', 'password', 'confirm_password']
    for field in required_fields:
        if not data.get(field):
            return Response({'detail': f'El campo {field} es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que las contraseñas coincidan
    if data['password'] != data['confirm_password']:
        return Response({'detail': 'Las contraseñas no coinciden'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Validar el email
        validate_email(data['email'])
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=data['username']).exists():
            return Response({'detail': 'El nombre de usuario ya está en uso'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=data['email']).exists():
            return Response({'detail': 'El email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar la contraseña
        validate_password(data['password'])
        
        # Crear el usuario
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        if data.get('first_name'):
            user.first_name = data['first_name']
        if data.get('last_name'):
            user.last_name = data['last_name']
            
        # Actualizar last_login al momento del registro
        user.last_login = timezone.now()
        user.save()
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'detail': 'Usuario registrado exitosamente',
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_transcription_group(request, group_id):
    """
    Endpoint para validar un grupo de transcripciones con segmentos de habla.
    
    Verifica que todos los audios del grupo tengan segmentos con tipo de hablante asignado 
    y que estén procesados correctamente. Luego envía la conversación al validador.
    """
    try:
        group = get_object_or_404(TranscriptionGroup, id=group_id, user=request.user)

        # Obtener todos los audios asociados al grupo
        audios = AudioTranscription.objects.filter(transcription_group=group).order_by('order')

        if not audios.exists():
            return Response({
                'detail': 'El grupo no contiene audios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar que todos los audios estén procesados
        if not all(audio.status == 'processed' for audio in audios):
            return Response({
                'detail': 'No se puede validar el grupo porque no todos los audios están procesados.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Construir la conversación a partir de los segmentos de cada audio
        conversation_data = []
        for audio in audios:
            segments = audio.segments.all().order_by('order')
            for segment in segments:
                # Verificar que el segmento tenga rol y texto
                if not segment.speaker_type:
                    return Response({
                        'detail': f'El segmento {segment.id} no tiene rol asignado.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                text = segment.modified_text if segment.modified_text else segment.text

                conversation_data.append((segment.speaker_type, text))

        if not conversation_data:
            return Response({
                'detail': 'No hay segmentos válidos con texto para validar.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ejecutar la tarea de validación de forma asíncrona
        task = validate_conversation_task.delay(conversation_data, settings.OLLAMA_MODEL, str(group_id))

        return Response({
            'detail': 'Validación iniciada correctamente',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            'detail': f'Error al procesar la solicitud: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_group_validation_results(request, group_id):
    """
    Endpoint para obtener los resultados de validación de un grupo de transcripciones.
    
    Retorna los resultados almacenados de la validación si existen, incluyendo la puntuación global
    y el análisis detallado de cada frase.
    """
    try:
        # Verificar que el grupo existe y pertenece al usuario
        group = get_object_or_404(TranscriptionGroup, id=group_id, user=request.user)
        
        # Verificar si el grupo tiene resultados de validación
        if not group.validation_result:
            return Response({
                'detail': 'Este grupo no tiene resultados de validación.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Devolver los resultados almacenados
        return Response({
            'validation_date': group.validation_date,
            'validation_status': group.validation_status,
            'validation_result': group.validation_result,
            'validation_score': group.validation_score,
            'validation_calification': group.validation_calification,
            'validation_comment': group.validation_comment,
            'model': group.validation_result.get('model', 'No especificado')
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'detail': f'Error al obtener los resultados: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_calification(request, group_id):
    try:
        group = TranscriptionGroup.objects.get(id=group_id, user=request.user)
    except TranscriptionGroup.DoesNotExist:
        return Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

    score = request.data.get('validation_calification')
    comment = request.data.get('validation_comment')

    if score is None:
        return Response({"detail": "Validation score is required"}, status=status.HTTP_400_BAD_REQUEST)

    group.validation_calification = score
    group.validation_comment = comment
    group.save()

    return Response({"detail": "Calification saved successfully"}, status=status.HTTP_200_OK)


wer_metric = evaluate.load("wer")

def calculate_wer(reference: str, hypothesis: str) -> float:
    return wer_metric.compute(predictions=[hypothesis], references=[reference])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wer_global(request):
    all_audios = []
    groups = TranscriptionGroup.objects.exclude(user__username="adrimartbay")

    for group in groups:
        all_audios.extend(group.audios.all())

    references = []
    hypotheses = []

    for audio in all_audios:
        if audio.original_text and audio.modified_text:
            references.append(audio.original_text)
            hypotheses.append(audio.modified_text)

    if not references or not hypotheses:
        return Response({
            'detail': 'No audios found to compute the WER.'
        }, status=status.HTTP_400_BAD_REQUEST)

    global_wer = wer_metric.compute(predictions=hypotheses, references=references)

    return Response({'global_average_wer': global_wer}, status=status.HTTP_200_OK)
