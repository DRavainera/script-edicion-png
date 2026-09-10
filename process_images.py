import os
import zipfile
import argparse
import base64
import json
from PIL import Image, ImageFilter, ImageDraw
from openai import OpenAI

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_ai_design_parameters(image_path, prompt, client, model="gpt-4o-mini"):
    """
    Usa un agente de IA (GPT-4o / GPT-4o-mini) para analizar la imagen y el prompt,
    retornando parámetros numéricos y de estilo para que Pillow aplique la edición exacta.
    """
    base64_image = encode_image(image_path)
    
    system_prompt = (
        "Eres un agente experto en diseño UI/UX (Material Design, Fluent Design, etc.). "
        "Analiza la imagen provista y el pedido del usuario. "
        "Debes retornar UNICAMENTE un objeto JSON válido con los parámetros de edición que Pillow debe aplicar: "
        "{\n"
        "  \"corner_radius\": <int (ej: 8 a 24)>, \n"
        "  \"shadow_blur\": <int (ej: 5 a 20)>, \n"
        "  \"shadow_offset_y\": <int (ej: 2 to 10)>, \n"
        "  \"shadow_opacity\": <int (ej: 30 a 100)>, \n"
        "  \"padding\": <int (ej: 10 a 40)>\n"
        "}"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Pedido de diseño: {prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
    except Exception as e:
        print(f"Error obteniendo parámetros del agente IA: {e}")
        # Valores por defecto en caso de fallo
        return {
            "corner_radius": 12,
            "shadow_blur": 10,
            "shadow_offset_y": 5,
            "shadow_opacity": 60,
            "padding": 20
        }

def apply_ai_design_to_image(image_path, params):
    """Aplica los parámetros calculados por la IA utilizando Pillow."""
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        
        radius = params.get("corner_radius", 12)
        shadow_blur = params.get("shadow_blur", 10)
        offset_y = params.get("shadow_offset_y", 5)
        opacity = params.get("shadow_opacity", 60)
        padding = params.get("padding", 20)
        
        # Esquinas redondeadas
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
        
        rounded = img.copy()
        rounded.putalpha(mask)
        
        # Sombra
        new_size = (img.width + padding * 2, img.height + padding * 2)
        canvas = Image.new("RGBA", new_size, (0, 0, 0, 0))
        
        shadow = Image.new("RGBA", img.size, (0, 0, 0, opacity))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        
        canvas.paste(shadow, (padding, padding + offset_y), shadow)
        canvas.paste(rounded, (padding, padding), rounded)
        
        return canvas

def process_zip(zip_path, prompt, model="gpt-4o-mini", api_key=None):
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
    
    # Bucle iterativo de una en una con agente IA
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith('.png'):
                file_path = os.path.join(root, file)
                out_path = os.path.join(processed_dir, file)
                
                print(f"Procesando imagen con agente IA ({model}): {file} | Prompt: '{prompt}'")
                
                # 1. Consultar al agente de IA los parámetros de diseño
                params = get_ai_design_parameters(file_path, prompt, client, model)
                print(f"  -> Parámetros recibidos de la IA: {params}")
                
                # 2. Aplicar la edición guiada por la IA
                processed_img = apply_ai_design_to_image(file_path, params)
                processed_img.save(out_path, "PNG")
                    
    zip_name = f"ai_agent_processed.zip"
    output_zip_path = os.path.join(base_dir, zip_name)
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for root, _, files in os.walk(processed_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                zip_out.write(abs_path, arcname=file)
                
    import shutil
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(processed_dir, ignore_errors=True)
    
    print(f"¡Proceso completado con agente IA! Archivo generado: {output_zip_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesa PNGs en un ZIP iterativamente usando un agente de IA (GPT-4o/4o-mini) y un prompt.")
    parser.add_argument("--zip", required=True, help="Ruta al archivo ZIP con los PNGs.")
    parser.add_argument("--prompt", required=True, help="Prompt descriptivo de la edición a realizar (ej. 'Estilo Material Design limpio').")
    parser.add_argument("--model", default="gpt-4o-mini", help="Modelo de OpenAI a utilizar (por defecto: gpt-4o-mini).")
    parser.add_argument("--apikey", required=False, help="API Key de OpenAI (opcional si se define en la variable de entorno OPENAI_API_KEY).")
    
    args = parser.parse_args()
    process_zip(args.zip, args.prompt, args.model, args.apikey)
