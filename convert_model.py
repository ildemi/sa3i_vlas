import os
import ctranslate2

# Nombre del modelo en HuggingFace
model_name = "jlvdoorn/whisper-large-v3-atco2-asr"
# Directorio donde guardaremos el modelo convertido compatible con Faster-Whisper
output_dir = "/app/.cache/faster_whisper_converted"

print(f"--- Starting Manual Conversion ---")
print(f"Model: {model_name}")
print(f"Output Directory: {output_dir}")

try:
    # Asegurar que el directorio existe
    os.makedirs(output_dir, exist_ok=True)

    print("Initializing TransformersConverter...")
    # Usamos el convertidor oficial de CTranslate2
    converter = ctranslate2.converters.TransformersConverter(
        model_name,
        copy_files=["tokenizer.json", "preprocessor_config.json", "vocab.json"]
    )

    print("Converting... (this may take a minute)")
    # Ejecutamos la conversión. 'float16' ofrece mayor precisión que int8, ideal para GPUs modernas.
    converter.convert(
        output_dir=output_dir,
        quantization="float16", 
        force=True
    )
    
    print("\n✅ Conversion SUCCESSFUL!")
    print(f"Verifying files in {output_dir}:")
    files = os.listdir(output_dir)
    for f in files:
        print(f" - {f}")
    
    if "model.bin" in files:
        print("\nCRITICAL: 'model.bin' exists. Faster-Whisper should work now.")
    else:
        print("\nWARNING: 'model.bin' missing despite success message.")

except Exception as e:
    print(f"\n❌ Conversion FAILED: {e}")
