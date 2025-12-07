export interface AudioSegment {
  id: string;
  audio: string;
  text: string;
  modified_text: string;
  speaker_type: string;
  order: number;
  segment_file: string;
  segment_file_url: string;
}

export interface AudioFile {
  id: string;
  file: string;
  file_name: string;
  file_url: string;
  status: string;
  order: number;
  transcription_date: string;
  upload_date: string;
  showButtons: boolean;
  transcription_group: string;
  speech_segments: AudioSegment[];
}

export interface TranscriptionGroup {
  group_id: string
  status: string
  audios: AudioFile[]
  group_name: string
  validation_status?: string
}
