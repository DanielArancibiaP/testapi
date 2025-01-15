from flask import Flask, request, jsonify
from PIL import Image
import os

app = Flask(__name__)

# Ruta para subir y redimensionar una imagen
@app.route('/upload', methods=['POST'])
def resize_image():
    # Obtener el archivo de la solicitud
    image = request.files.get('file')

    # Verificar si se recibió el archivo
    if not image:
        return jsonify({'error': 'No file part'}), 400
    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Abrir la imagen usando Pillow
        img = Image.open(image)

        # Redimensionar la imagen
        img = img.resize((200, 200))  # Cambia las dimensiones según sea necesario

        # Guardar la imagen redimensionada
        output_path = os.path.join('uploads', image.filename)
        img.save(output_path)

        return jsonify({'message': f'Image saved at {output_path}'}), 200
    except Exception as e:
        # Capturar errores y devolver una respuesta
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Crear carpeta de uploads si no existe
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
