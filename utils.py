import os

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def allowed_excel_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

def create_upload_folders():
    folders = ['uploads', 'uploads/templates', 'uploads/excel']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)