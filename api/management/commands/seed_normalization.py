from django.core.management.base import BaseCommand
from api.models import Airline, TranscriptionCorrection
# Importamos desde el legacy para extraer los datos
from api.transcriber.normalize_legacy import airlines_oaci_codes, airlines_iata_codes, airlines_icao_codes, text_similarities, nato_similarities, terminology_mapping, nato_alphabet_mapping

class Command(BaseCommand):
    help = 'Seeds the database with normalization data from legacy dictionaries'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando migración de datos de normalización...")

        # 1. Migrar Aerolíneas
        airlines_data = {} # name -> {icao, iata, callsign}

        # Procesar OACI (Nombre -> ICAO)
        for name, code in airlines_oaci_codes.items():
            name = name.lower()
            if name not in airlines_data: airlines_data[name] = {}
            airlines_data[name]['icao_code'] = code

        # Procesar IATA (CODE -> Name)
        for code, name in airlines_iata_codes.items():
            name = name.lower()
            if name not in airlines_data: airlines_data[name] = {}
            airlines_data[name]['iata_code'] = code

        # Procesar ICAO (CODE -> Name)
        for code, name in airlines_icao_codes.items():
            name = name.lower()
            if name not in airlines_data: airlines_data[name] = {}
            airlines_data[name]['icao_code'] = code

        count_airlines = 0
        for name, data in airlines_data.items():
            obj, created = Airline.objects.update_or_create(
                name=name,
                defaults={
                    'icao_code': data.get('icao_code'),
                    'iata_code': data.get('iata_code')
                }
            )
            if created: count_airlines += 1

        self.stdout.write(f"Aerolíneas creadas/actualizadas: {count_airlines}")

        # 2. Migrar Correcciones
        count_corrections = 0
        
        # General
        for incorrect, correct in text_similarities.items():
            _, created = TranscriptionCorrection.objects.get_or_create(
                incorrect_text=incorrect.lower(),
                defaults={'correct_text': correct.lower(), 'category': 'general'}
            )
            if created: count_corrections += 1

        # NATO
        for incorrect, correct in nato_similarities.items():
            _, created = TranscriptionCorrection.objects.get_or_create(
                incorrect_text=incorrect.lower(),
                defaults={'correct_text': correct.lower(), 'category': 'general'}
            )
            if created: count_corrections += 1
            
        # Terminology
        for term, expansion in terminology_mapping.items():
             _, created = TranscriptionCorrection.objects.get_or_create(
                incorrect_text=term.lower(),
                defaults={'correct_text': expansion.lower(), 'category': 'terminology'}
            )
             if created: count_corrections += 1
        
        # NATO Alphabet & Numbers
        for term, expansion in nato_alphabet_mapping.items():
             _, created = TranscriptionCorrection.objects.get_or_create(
                incorrect_text=term.lower(),
                defaults={'correct_text': expansion, 'category': 'nato_alphabet'}
            )
             if created: count_corrections += 1

        self.stdout.write(f"Correcciones creadas: {count_corrections}")
