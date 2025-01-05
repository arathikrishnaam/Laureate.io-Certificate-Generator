from flask import Flask, request, render_template, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS
from google_drive import GoogleDriveManager

app = Flask(__name__, static_url_path='/static')
CORS(app)

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def get_font(size):
    """
    Get a font object with the specified size.
    Attempts to load Arial font from various system locations, falls back to default if not found.
    """
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            font_paths = [
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # Linux
                "/Library/Fonts/Arial.ttf",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                os.path.join(BASE_DIR, 'fonts', 'arial.ttf')  # Local directory
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

# Initialize GoogleDriveManager
drive_manager = GoogleDriveManager(
    credentials_path='credentials.json', 
    token_path='token.pickle'
)

# Create necessary directories
for folder in [UPLOAD_FOLDER, STATIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/generate', methods=['POST'])
def generate_certificates():
    try:
        if 'template' not in request.files or 'excel' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400

        template = request.files['template']
        excel_file = request.files['excel']
        
        # Get text settings from form
        x_pos = int(request.form.get('x_pos', 400))
        y_pos = int(request.form.get('y_pos', 300))
        font_size = int(request.form.get('font_size', 36))
        text_color = request.form.get('text_color', '#000000')

        if template.filename == '' or excel_file.filename == '':
            return jsonify({'error': 'No selected files'}), 400

        # Create folder for this batch
        folder_name = f'Certificates_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(folder_path)
        
        # Create a corresponding folder in Google Drive
        drive_folder_id = drive_manager.create_folder(folder_name)
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        if 'name' not in df.columns:
            return jsonify({'error': 'Excel file must contain a "name" column'}), 400

        template_image = Image.open(template)
        font = get_font(font_size)
        generated_certificates = []
        
        # Process each name
        for index, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                if not name:  # Skip empty names
                    continue

                img = template_image.copy()
                draw = ImageDraw.Draw(img)

                # Calculate text size for centering
                bbox = draw.textbbox((0, 0), name, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x_pos - text_width // 2
                text_y = y_pos - text_height // 2

                # Draw the name at specified position
                draw.text(
                    (text_x, text_y),
                    name,
                    font=font,
                    fill=text_color
                )

                # Save certificate locally
                filename = f'certificate_{secure_filename(name)}.png'
                filepath = os.path.join(folder_path, filename)
                img.save(filepath, 'PNG')

                # Prepare file for Google Drive upload
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                # Upload to Google Drive
                drive_link = drive_manager.upload_file(
                    filename,
                    img_byte_arr,
                    'image/png',
                    drive_folder_id
                )

                # Store generated certificate details
                generated_certificates.append({
                    'name': name,
                    'local_link': f'/uploads/{folder_name}/{filename}',
                    'drive_link': drive_link
                })

            except Exception as e:
                print(f"Error processing certificate for {name}: {str(e)}")
                continue

        if not generated_certificates:
            return jsonify({'error': 'No certificates were generated'}), 400

        return jsonify({
            'success': True,
            'folder_name': folder_name,
            'certificates': generated_certificates
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)