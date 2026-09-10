# Script de Edición de PNGs con Agente de IA

Este script en Python procesa archivos ZIP con imágenes PNG de forma iterativa, enviando cada imagen individualmente a un modelo de IA (como OpenAI DALL-E / Images API) junto con un prompt personalizado que indica el diseño o modificación a realizar.

## Requisitos

- Python 3.8+
- Dependencias indicadas en `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Uso

1. Configura tu clave de API de OpenAI como variable de entorno:
   ```bash
   export OPENAI_API_KEY="tu-api-key"
   ```
2. Ejecuta el script indicando el archivo ZIP y el prompt con la edición deseada:
   ```bash
   python process_images.py --zip /ruta/a/imagenes.zip --prompt "Aplica estilo Material Design con esquinas redondeadas y sombra definida"
   ```
