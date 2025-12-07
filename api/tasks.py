from celery import shared_task, current_app
from django.db import transaction
from django.utils import timezone
import os

from .transcriber.transcriber import transcriber_instance
from .validator.validation import Validator
from models.models import AudioTranscription, TranscriptionGroup, SpeechSegment
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_audio_task(audio_file_id):
    try:
        with transaction.atomic():
            audio_file = AudioTranscription.objects.select_for_update().get(id=audio_file_id)
            
            if audio_file.status == 'cancelled':
                print(f"Transcripción {audio_file_id} está cancelada, no se procesará.")
                return None
            
            if audio_file.status not in ['pending', 'in_process']:
                print(f"Transcripción {audio_file_id} en estado {audio_file.status}, no se procesa.")
                return None
            
            audio_file.status = 'in_process'
            audio_file.save()
            audio_file.transcription_group.update_status()
        
        # Verificamos que el archivo exista
        file_path = audio_file.file.path if audio_file.file else None
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo de audio: {file_path}")
        
        # Obtenemos todos los segmentos ordenados por orden
        segments = SpeechSegment.objects.filter(audio=audio_file).order_by('order')
        
        # Transcribir segmento a segmento
        for segment in segments:
            seg_file_path = segment.segment_file.path
            if not os.path.exists(seg_file_path):
                raise FileNotFoundError(f"No se encontró el archivo de segmento: {seg_file_path}")
            
            # Aquí llamas a la función real que transcribe el segmento (debes implementar esta función)
            text = transcriber_instance.invoke(audio_path=seg_file_path, normalize=True)
            
            # Guardamos texto en el segmento
            segment.text = text
            if not segment.modified_text:
                segment.modified_text = text
            segment.save()
        
        with transaction.atomic():
            audio_file = AudioTranscription.objects.select_for_update().get(id=audio_file_id)
            
            if audio_file.status == 'cancelled':
                print(f"Transcripción {audio_file_id} cancelada después del procesamiento.")
                return None
            
            audio_file.status = 'processed'
            audio_file.transcription_date = timezone.now()
            audio_file.save()
            audio_file.transcription_group.update_status()
        

    except Exception as error:
        try:
            with transaction.atomic():
                audio_file = AudioTranscription.objects.select_for_update().get(id=audio_file_id)
                if audio_file.status != 'cancelled':
                    audio_file.status = 'failed'
                    audio_file.save()
                    audio_file.transcription_group.update_status()
        except:
            pass
        
        raise error


def cancel_group_tasks(group_id):
    """
    Cancela todas las tareas de transcripción pendientes o en proceso
    para un grupo específico.
    """
    try:
        from models.models import TranscriptionGroup
        group = TranscriptionGroup.objects.get(id=group_id)

        # Para mayor consistencia, puedes usar transacción
        with transaction.atomic():
            # Bloqueamos el grupo mientras lo actualizamos
            group = TranscriptionGroup.objects.select_for_update().get(id=group_id)
            
            # Obtenemos los audios que están pendientes o en proceso
            audios = AudioTranscription.objects.select_for_update().filter(
                transcription_group_id=group_id,
                status__in=['pending', 'in_process']
            )
            
            for audio in audios:
                # Revocar la tarea en Celery (terminate=False evita matar el proceso brutalmente)
                # Si quisieras forzar la detención inmediata, usarías terminate=True 
                current_app.control.revoke(audio.task_id, terminate=False)
                
                # Marcar como cancelado en BD
                audio.status = 'cancelled'
                audio.save()

            # Ahora, según los audios que tenga el grupo, re-evaluamos el status general
            if audios.exists():
                group.status = 'cancelled'
            else:
                # Si no hay audios pendientes/en proceso, ver estado global
                all_audios = AudioTranscription.objects.filter(transcription_group_id=group_id)
                if all_audios.filter(status='processed').exists():
                    group.status = 'processed'
                elif all_audios.filter(status='failed').exists():
                    group.status = 'failed'
                else:
                    group.status = 'cancelled'
            
            group.save()
        
        return True

    except Exception as e:
        print(f"Error al cancelar las tareas del grupo: {str(e)}")
        return False

@shared_task
def validate_conversation_task(conversation_data, model="phi4", group_id=None):
    """
    Tarea asíncrona para validar una conversación utilizando el validador y
    guardar los resultados en el modelo TranscriptionGroup si se proporciona un group_id.
    
    Args:
        conversation_data (list[tuple[str, str]]): Lista de tuplas donde cada tupla contiene:
            - str: El rol del hablante (ej: 'pilot', 'atco')
            - str: La frase dicha por esa persona
        model (str, opcional): El modelo a utilizar para la validación. Por defecto "phi4"
        group_id (str, opcional): ID del grupo de transcripción para guardar los resultados
    
    Returns:
        dict: Resultado de la validación que incluye:
            - Lista de errores encontrados
            - Puntuaciones por diferentes categorías
            - Detalles de la validación de cada frase
            - Puntuación global del análisis
    """
    try:
        # Si se proporcionó un group_id, marcamos el grupo como en proceso
        if group_id:
            with transaction.atomic():
                try:
                    group = TranscriptionGroup.objects.select_for_update().get(id=group_id)
                    group.validation_status = 'in_process'
                    group.save()
                except TranscriptionGroup.DoesNotExist:
                    print(f"No se encontró el grupo de transcripción con ID: {group_id}")
                except Exception as db_error:
                    print(f"Error al actualizar el estado de validación: {str(db_error)}")
        
        # Inicializamos el validador con el modelo especificado
        validator = Validator(model=model)
        
        # Invocamos la validación
        # El método invoke ahora devuelve un resultado serializado
        result = validator.invoke(conversation_data)
        
        # Aseguramos que existe una puntuación global en el resultado
        if 'score' in result and 'puntuacion_total' in result['score']:
            # Extraemos la puntuación global para guardarla directamente en el grupo
            puntuacion_global = None
            if isinstance(result['score']['puntuacion_total'], dict) and 'score' in result['score']['puntuacion_total']:
                puntuacion_global = result['score']['puntuacion_total']['score']
            elif isinstance(result['score']['puntuacion_total'], str):
                # Intentar extraer el valor numérico si es una cadena con formato 'X.X/5'
                try:
                    puntuacion_str = result['score']['puntuacion_total'].split('/')[0]
                    puntuacion_global = float(puntuacion_str)
                except (ValueError, IndexError):
                    puntuacion_global = None
        
        # Si se proporcionó un group_id, guardamos los resultados en la base de datos
        if group_id:
            with transaction.atomic():
                try:
                    group = TranscriptionGroup.objects.select_for_update().get(id=group_id)
                    
                    # Guardamos los resultados de la validación
                    group.validation_date = timezone.now()
                    group.validation_status = 'success'
                    group.validation_result = result
                    
                    # Guardamos la puntuación global si se pudo extraer
                    if 'puntuacion_global' in locals() and puntuacion_global is not None:
                        group.validation_score = puntuacion_global
                    
                    # Guardar el grupo actualizado
                    group.save()
                except TranscriptionGroup.DoesNotExist:
                    print(f"No se encontró el grupo de transcripción con ID: {group_id}")
                except Exception as db_error:
                    print(f"Error al guardar los resultados de validación: {str(db_error)}")
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as error:
        # Si hay un error en la validación y tenemos un group_id, guardamos el error
        if group_id:
            try:
                group = TranscriptionGroup.objects.get(id=group_id)
                group.validation_date = timezone.now()
                group.validation_status = 'error'
                group.validation_result = {'error': str(error)}
                group.save()
            except:
                pass
                
        return {
            'status': 'error',
            'error': str(error)
        }

@shared_task
def retry_audio_process_task(audio_id):
    try:
        from api.diarizer import AudioDiarization
        from pathlib import Path
        from django.conf import settings

        # 1. Marcar como en proceso y limpiar segmentos antiguos
        with transaction.atomic():
            audio = AudioTranscription.objects.select_for_update().get(id=audio_id)
            audio.status = 'in_process'
            # Limpiar segmentos anteriores
            audio.segments.all().delete()
            audio.save()
            audio.transcription_group.update_status()

        # 2. Reinvocar diarización (operación costosa, fuera de lock)
        # audio.file.path es absoluto (/app/media/...)
        diarizer = AudioDiarization()
        diarized_segments = diarizer.invoke(audio.file.path)

        # 3. Crear nuevos segmentos y lanzar transcripción
        with transaction.atomic():
            audio = AudioTranscription.objects.select_for_update().get(id=audio_id)
            
            for idx, seg in enumerate(diarized_segments, start=1):
                abs_path = Path(seg['path'])
                
                # Intentar calcular ruta relativa a MEDIA_ROOT para guardar en BD
                try:
                    # relative_to lanza ValueError si no es subpath
                    relative_path = abs_path.relative_to(settings.MEDIA_ROOT)
                except ValueError:
                    # Fallback robusto: si está en /app/media pero relative_to falla por symlinks o formato
                    path_str = str(abs_path)
                    media_root_str = str(settings.MEDIA_ROOT)
                    if path_str.startswith(media_root_str):
                        relative_path = path_str[len(media_root_str):].lstrip(os.sep)
                    else:
                        # Si es un path totalmente distinto, guardamos el nombre base y rezamos
                        # O idealmente movemos el archivo a media.
                        # Diarizer debería guardar en media.
                        relative_path = abs_path.name

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
            
            # Reset status a pending para que process_audio_task lo tome
            audio.status = 'pending'
            audio.save()
            
            # Lanzar tarea de transcripción
            task = process_audio_task.delay(audio.id)
            audio.task_id = task.id
            audio.save()

    except Exception as e:
        logger.error(f"Error en retry_audio_process_task para audio {audio_id}: {e}")
        try:
            with transaction.atomic():
                audio = AudioTranscription.objects.get(id=audio_id)
                audio.status = 'failed'
                audio.save()
                audio.transcription_group.update_status()
        except:
            pass
        raise e
