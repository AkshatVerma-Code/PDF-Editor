from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import uuid
import subprocess

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def parse_page_ranges(page_str):
    # Helper to parse '2,4,5' or '2-4' or '1-3,5' into a set of page numbers (0-indexed)
    pages = set()
    if not page_str:
        return pages
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.update(range(int(start)-1, int(end)))
        elif part.isdigit():
            pages.add(int(part)-1)
    return pages

@app.route('/operation', methods=['GET', 'POST'])
def operation():
    if request.method == 'POST':
        operation = request.form.get('operation')
        files = request.files.getlist('pdfFile')
        last_result = session.get('last_result')
        # If chaining, use last_result as input
        if request.args.get('continue') and last_result:
            files = [open(os.path.join(RESULT_FOLDER, last_result), 'rb')]
        if not files or not operation:
            return render_template('operation.html', error='Please select an operation and upload PDF(s).')
        if operation == 'merge':
            merger = PdfMerger()
            for file in files:
                merger.append(file)
            result_filename = f"result_{uuid.uuid4().hex}.pdf"
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            merger.write(result_path)
            merger.close()
            session['last_result'] = result_filename
            return redirect(url_for('result'))
        elif operation == 'watermark':
            watermark_text = request.form.get('watermarkText', 'Bhai ka Pdf')
            watermark_pdf = BytesIO()
            c = canvas.Canvas(watermark_pdf, pagesize=letter)
            c.setFont('Helvetica-Bold', 40)
            c.setFillColorRGB(1, 0, 0, alpha=0.3)
            c.saveState()
            c.translate(300, 400)
            c.rotate(45)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
            c.save()
            watermark_pdf.seek(0)
            watermark_reader = PdfReader(watermark_pdf)
            input_pdf = PdfReader(files[0])
            writer = PdfWriter()
            for page in input_pdf.pages:
                page.merge_page(watermark_reader.pages[0])
                writer.add_page(page)
            result_filename = f"result_{uuid.uuid4().hex}.pdf"
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            with open(result_path, 'wb') as f:
                writer.write(f)
            session['last_result'] = result_filename
            return redirect(url_for('result'))
        elif operation == 'compress':
            input_filename = f"input_{uuid.uuid4().hex}.pdf"
            input_path = os.path.join(RESULT_FOLDER, input_filename)
            with open(input_path, 'wb') as f:
                f.write(files[0].read())
            result_filename = f"result_{uuid.uuid4().hex}.pdf"
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            try:
                subprocess.run([
                    'gs',
                    '-sDEVICE=pdfwrite',
                    '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS=/ebook',
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    f'-sOutputFile={result_path}',
                    input_path
                ], check=True)
            except Exception as e:
                return render_template('operation.html', error=f'Compression failed: {e}')
            session['last_result'] = result_filename
            return redirect(url_for('result'))
        elif operation == 'delete':
            delete_pages = request.form.get('deletePages', '')
            pages_to_delete = parse_page_ranges(delete_pages)
            input_pdf = PdfReader(files[0])
            writer = PdfWriter()
            for i, page in enumerate(input_pdf.pages):
                if i not in pages_to_delete:
                    writer.add_page(page)
            result_filename = f"result_{uuid.uuid4().hex}.pdf"
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            with open(result_path, 'wb') as f:
                writer.write(f)
            session['last_result'] = result_filename
            return redirect(url_for('result'))
        elif operation == 'split':
            split_ranges = request.form.get('splitRanges', '')
            input_pdf = PdfReader(files[0])
            ranges = []
            for part in split_ranges.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-')
                    ranges.append((int(start)-1, int(end)))
                elif part.isdigit():
                    idx = int(part)-1
                    ranges.append((idx, idx+1))
            split_files = []
            for idx, (start, end) in enumerate(ranges):
                writer = PdfWriter()
                for i in range(start, min(end, len(input_pdf.pages))):
                    writer.add_page(input_pdf.pages[i])
                split_filename = f"split_{idx+1}_{uuid.uuid4().hex}.pdf"
                split_path = os.path.join(RESULT_FOLDER, split_filename)
                with open(split_path, 'wb') as f:
                    writer.write(f)
                split_files.append(split_filename)
            # For simplicity, return the first split file and store it for chaining
            if split_files:
                session['last_result'] = split_files[0]
                session['split_files'] = split_files
                return redirect(url_for('result'))
            else:
                return render_template('operation.html', error='No valid split ranges provided.')
    continue_edit = request.args.get('continue')
    last_result = session.get('last_result') if continue_edit else None
    return render_template('operation.html', last_result=last_result)

@app.route('/result')
def result():
    last_result = session.get('last_result')
    if not last_result:
        return redirect(url_for('operation'))
    download_url = url_for('download_result', filename=last_result)
    preview_url = url_for('preview_result', filename=last_result)
    return render_template('result.html', download_url=download_url, preview_url=preview_url)

@app.route('/download/<filename>')
def download_result(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)

@app.route('/preview/<filename>')
def preview_result(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True) 