import os
import torch
import soundfile as sf
from librosa import load
from scipy import signal
from pydub import AudioSegment
from dotenv import load_dotenv
from pyannote.audio import Pipeline
from diarizers import SegmentationModel

load_dotenv()

HF_TOKEN = os.getenv('HF_TOKEN')


if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

class AudioDiarization:
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN).to(device)
        model = SegmentationModel().from_pretrained("miguelozaalon/speaker-segmentation-atc", use_auth_token=HF_TOKEN)
        model = model.to_pyannote_model()
        self.pipeline._segmentation.model = model.to(device)


    def invoke(self, audio_path: str):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"El archivo de audio {audio_path} no existe")

        # 1. Convertir cualquier formato a WAV estándar (16kHz, mono) usando pydub (ffmpeg)
        temp_wav_path = f"temp_clean_{os.path.basename(audio_path)}.wav"
        if not temp_wav_path.lower().endswith(".wav"):
             temp_wav_path += ".wav"

        audio_segment = AudioSegment.from_file(audio_path)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
        audio_segment.export(temp_wav_path, format="wav")

        # 2. Cargar con librosa desde el WAV temporal confiable
        array, sr = load(temp_wav_path, sr=None)

        # 3. Limpiar audio (filtro pasa-bajos)
        audio_data = self.clean_audio(array, sr)

        # 4. Guardar audio filtrado para diarización
        # Sobrescribimos el temporal o usamos otro nombre. Pyannote necesita un archivo en disco.
        processed_audio_path = f"processed_{os.path.basename(audio_path)}.wav"
        sf.write(processed_audio_path, audio_data, sr)

        # Limpiar primer temporal
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

        # 5. Ejecutar pipeline sobre audio procesado
        result = self.pipeline(processed_audio_path)
        
        # Limpiar segundo temporal
        if os.path.exists(processed_audio_path):
            os.remove(processed_audio_path)

        # Get the folder path for segments
        base_dir = os.path.dirname(audio_path)
        basename = os.path.splitext(os.path.basename(audio_path))[0]
        folder_path = os.path.join(base_dir, f"{basename}_segments")
        
        # Create a list to store segment paths
        segment_paths = []
        
        # Save segments and collect paths
        for idx, (turn, _, speaker) in enumerate(result.itertracks(yield_label=True), 1):
            segment_path = os.path.join(folder_path, f"{speaker}_{idx}.wav")
            segment_paths.append({'path': segment_path, 'start_time': turn.start, 'end_time': turn.end})
            
        if folder_path == "":
            folder_path = "."
        # Save the segments
        self.save_segments(folder_path, audio_path, result)

        return segment_paths

    def save_segments(self, folder_path: str, audio_path: str, diarization_result):
        """
        Guarda los segmentos de audio por hablante en la carpeta especificada.
        """
        audio = AudioSegment.from_file(audio_path)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for idx, (turn, _, speaker) in enumerate(diarization_result.itertracks(yield_label=True), 1):
            start_time = turn.start
            end_time = turn.end

            start_ms = start_time * 1000
            end_ms = end_time * 1000

            # Recortar el audio
            speaker_audio = audio[start_ms:end_ms]

            # Crear el nombre del archivo de salida usando el índice global
            output_filename = os.path.join(folder_path, f"{speaker}_{idx}.wav")

            # Guardar el fragmento de audio
            speaker_audio.export(output_filename, format="wav")

    def clean_audio(self, audio, sampling_rate):
        """
        Clean the noise from the audio
        """
        Wn = 1600 / (sampling_rate / 2) # Por debajo de este humbral pasa la señal (Frecuencia de Nyquist)
        sos = signal.butter(N=4, Wn=Wn, btype='low', analog=False, output='sos')
        return signal.sosfilt(sos, audio)
