import os
import zipfile
import argparse
from PIL import Image, ImageOps, ImageFilter, ImageDraw

def add_corner_radius(image, radius):
    """Aplica esquinas redondeadas a una imagen RGBA."""
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
    
    result = image.copy()
    result.putalpha(mask)
    return result

def apply_material_style(image):
    """Estilo Material Design: Esquinas ligeramente redondeadas y sombra sólida/definida."""
    radius = max(4, int(min(image.size) * 0.03))
    rounded = add_corner_radius(image, radius)
    
    padding = 20
    new_size = (image.width + padding * 2, image.height + padding * 2)
    canvas = Image.new("RGBA", new_size, (0, 0, 0, 0))
    
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    
    canvas.paste(shadow, (padding, padding + 8), shadow)
    canvas.paste(rounded, (padding, padding), rounded)
    
    return canvas

def apply_fluent_style(image):
    """Estilo Fluent Design (Microsoft): Esquinas más redondeadas y sombra difusa (acrílica)."""
    radius = max(8, int(min(image.size) * 0.06))
    rounded = add_corner_radius(image, radius)
    
    padding = 30
    new_size = (image.width + padding * 2, image.height + padding * 2)
    canvas = Image.new("RGBA", new_size, (0, 0, 0, 0))
    
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
    
    canvas.paste(shadow, (padding, padding + 4), shadow)
    canvas.paste(rounded, (padding, padding), rounded)
    
    return canvas

def process_zip(zip_path, style):
    base_dir = os.path.dirname(os.path.abspath(zip_path))
    extract_dir = os.path.join(base_dir, "temp_extracted")
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    processed_dir = os.path.join(base_dir, "temp_processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    style_lower = style.lower()
    
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith('.png'):
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        img = img.convert("RGBA")
                        if "material" in style_lower:
                            processed_img = apply_material_style(img)
                        elif "fluent" in style_lower:
                            processed_img = apply_fluent_style(img)
                        else:
                            processed_img = apply_material_style(img)
                            
                        out_path = os.path.join(processed_dir, file)
                        processed_img.save(out_path, "PNG")
                except Exception as e:
                    print(f"Error procesando {file}: {e}")
                    
    zip_name = f"processed_{style_lower}_{os.path.basename(zip_path)}"
    output_zip_path = os.path.join(base_dir, zip_name)
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for root, _, files in os.walk(processed_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                zip_out.write(abs_path, arcname=file)
                
    import shutil
    shutil.rmtree(extract_dir)
    shutil.rmtree(processed_dir)
    
    print(f"¡Proceso completado! Archivo generado: {output_zip_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesa PNGs en un ZIP aplicando estilos de diseño (Material o Fluent).")
    parser.add_argument("--zip", required=True, help="Ruta al archivo ZIP con los PNGs.")
    parser.add_argument("--style", required=True, choices=["material", "fluent"], help="Estilo de diseño a aplicar: 'material' o 'fluent'.")
    
    args = parser.parse_args()
    process_zip(args.zip, args.style)
