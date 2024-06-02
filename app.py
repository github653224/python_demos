from flask import Flask, render_template, request, jsonify, send_file, url_for, after_this_request
from PIL import Image, ImageEnhance
import numpy as np
import easyocr
import io
import os
import fitz  # PyMuPDF
import zipfile
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)  # 支持中文简体和英文


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/text-recognition')
def text_recognition():
    return render_template('text_recognition.html')


@app.route('/pdf-image-extraction')
def pdf_image_extraction():
    return render_template('pdf_image_extraction.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename.lower())
        if filename.endswith('.pdf'):
            return extract_images_from_pdf(file, filename)
        else:
            return recognize_text(file, filename)
    return jsonify({'error': 'File type not supported'})


def recognize_text(file, filename):
    if not file:
        return jsonify({'error': 'No file provided'})
    if not filename.endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({'error': 'Invalid file format'})
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # image = Image.open(io.BytesIO(file.read()))

    # 图像预处理：转换为灰度图像，增强对比度
    # gray_image = image.convert('L')
    # enhancer = ImageEnhance.Contrast(gray_image)
    # enhanced_image = enhancer.enhance(2.0)

    # 将图像转换为 numpy 数组
    # image_np = np.array(enhanced_image)

    # 使用 EasyOCR 识别文本
    # result = reader.readtext(image_np)
    # text = [item[1] for item in result]

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)
    result = reader.readtext(image_path, detail=0)

    # Save the recognized text to a file
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'result.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in result:
            f.write(line + '\n')

    @after_this_request
    def remove_file(response):
        try:
            os.remove(image_path)
        except Exception as e:
            app.logger.error(f'Error removing file: {e}')
        return response

    return jsonify({'text': result, 'download_url': url_for('download_file', filename='result.txt')})


def extract_images_from_pdf(file, filename):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)

    pdf_file = fitz.open(pdf_path)
    images = []
    for page in pdf_file:
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(pdf_file, xref)
            if pix.n > 4:  # this is GRAY or RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_filename = f'image{page.number + 1}_{img_index}.png'
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
            pix.save(img_path)
            images.append(url_for('uploaded_file', filename=img_filename))
            pix = None

    pdf_file.close()
    os.remove(pdf_path)  # 清理临时文件

    return jsonify({'images': images, 'download_url': url_for('download_images_zip')})


def zip_images():
    zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for img in os.listdir(app.config['UPLOAD_FOLDER']):
            if img.endswith('.png'):
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
                zipf.write(img_path, os.path.basename(img_path))
                os.remove(img_path)  # 清理临时图片文件
    return zip_file_path


@app.route('/download/images.zip')
def download_images_zip():
    zip_file_path = zip_images()
    return send_file(zip_file_path, as_attachment=True)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


@app.route('/download/<filename>')
def download_file(filename):
    # return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    @after_this_request
    def remove_text_file(response):
        try:
            os.remove(file_path)
        except Exception as e:
            app.logger.error(f'Error removing text file: {e}')
        return response

    # Read the content of the file
    with open(file_path, 'rb') as f:
        data = f.read()

    # Create a temporary file to store the content
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(data)
    temp_file.close()

    return send_file(temp_file.name, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(debug=True)
