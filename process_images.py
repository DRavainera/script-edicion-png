import os
import zipfile
import argparse
import base64
import requests
from PIL import Image
from openai import OpenAI

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_with_ai(image_path, prompt, client):
    """
    Procesa una imagen individual usando un modelo de IA de OpenAI (GPT-4o o DALL-E) 
    guiado por el prompt indicado.
    """
    try:
        # Opcion A: Usar chat completion con vision (GPT-4o) si se solicita análisis/modificación descriptiva,
        # Opcion B: Usar DALL-E / Images Edit si se prefiere edición directa.
        # Aquí implementamos la llamada estándar a la API de OpenAI con soporte de imágenes y prompt.
        
        print(f"Procesando imagen con IA: {os.path.basename(image_path)} | Prompt: '{prompt}'")
        
        # Ejemplo usando OpenAI ChatCompletions con imagen (multimodal) o API de edición
        # Nota: Ajustar según el modelo y API específica (ej. DALL-E images.edit o GPT-4o output).
        
        with open(image_path, "rb") as img_file:
            response = client.images.edit(
                image=img_file,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        
        return img_data
    except Exception as e:
        print(f"Error en IA para {image_path}: {e}")
        return None

def process_zip(zip_path, prompt, api_key=None):
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    client = OpenAI()
    
    base_dir = os.path.dirname(os.path.abspath(zip_path))
    extract_dir = os.path.join(base_dir, "temp_extracted")
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    processed_dir = os.path.join(base_dir, "temp_processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # Bucle iterativo de una en una
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith('.png'):
                file_path = os.path.join(root, file)
                out_path = os.path.join(processed_dir, file)
                
                # Llamada al agente/modelo de IA iterativo
                img_data = process_image_with_ai(file_path, prompt, client)
                
                if img_data:
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                else:
                    print(f"Advertencia: No se pudo procesar {file}, se omite o mantiene original.")
                    
    zip_name = f"ai_processed_zip.zip"
    output_zip_path = os.path.join(base_dir, zip_name)
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for root, _, files in os.walk(processed_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                zip_out.write(abs_path, arcname=file)
                
    import shutil
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(processed_dir, ignore_errors=True)
    
    print(f"¡Proceso con IA completado! Archivo generado: {output_zip_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesa PNGs en un ZIP iterativamente usando un agente de IA y un prompt.")
    parser.add_argument("--zip", required=True, help="Ruta al archivo ZIP con los PNGs.")
    parser.add_argument("--prompt", required=True, help="Prompt descriptivo de la edición a realizar en cada imagen.")
    parser.add_argument("--apikey", required=False, help="API Key de OpenAI (opcional si se define en la variable de entorno OPENAI_API_KEY).")
    
    args = parser.parse_args()
    process_zip(args.zip, args.prompt, args.apikey)
