from flask import Flask, render_template, request, url_for, session, redirect, Response
import io
import random
import json
import requests
import secrets
import re
import pdfplumber

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Initialize the Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(16)

API_URL_LIST = [
  "https://api-inference.huggingface.co/models/Michael-Vptn/text-summarization-t5-base",  # Michael API
  "https://api-inference.huggingface.co/models/Nehu/Flan",  # Neha API
  "https://api-inference.huggingface.co/models/Michael-Vptn/text-summarization-t5-base",  # Michael API
  "https://api-inference.huggingface.co/models/Nehu/Flan",
]

headers = {"Authorization": "Bearer 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"}

global_input_text = ""
global_output_text = ""

#
#
#


# Function used for initially loading index.html
@app.route('/')
def index():
  return render_template('index.html')


@app.route('/model.html')
def modelpage():
  return render_template('model.html')


@app.route('/aboutme.html')
def about():
  return render_template('aboutme.html')


def divide(input_str, num):
  # Use regular expression to find sentence breaks
  sentence_breaks = [0] + [
    match.end() for match in re.finditer(r'[.!?]\s+', input_str)
  ]
  total_sentences = len(sentence_breaks)

  # Calculate the indices for dividing the sentences
  indices = [
    sentence_breaks[int(total_sentences * i / num)] for i in range(1, num)
  ]

  # Divide the input string into sentences
  strings = []
  start_index = 0
  for index in indices:
    strings.append(input_str[start_index:index])
    start_index = index

  strings.append(input_str[start_index:])  # Add the remaining part
  return strings


def combine(str_list, bullet_type='bullet'):
  if bullet_type == 'bullet':
    bullet = "• \n"
  elif bullet_type == 'number':
    bullet = "1. "
  else:
    bullet = "- "

  combined = "\n".join([f"{bullet}{item}" for item in str_list])
  return combined


def generate(input_text):
  try:
    if len(input_text) > 500:

      input_strings = divide(input_text, len(API_URL_LIST))
      output_segments = [
      ]  # List to store generated text segments from different APIs

      for i in range(len(API_URL_LIST)):
        segment = query({"inputs": input_strings[i]}, API_URL_LIST[i])

        output_segments.append(segment[0]["generated_text"])

        output_text = combine(
          output_segments)  # Combine generated text segments
    else:
      output_text = query(
        {"inputs": input_text},
        API_URL_LIST[0])  # if input is too short, only use one api

      output_text = output_text[0]["generated_text"]

    return output_text
  except Exception as e:
    print(f"generate text error: {e}")
    return "OH NO! An error has occoured within our generate text function. This may be due to the provided text or too many people using this API at this moment. Please try again later! -cozycornbreads"


def query(payload, API):  # query payload to APIs
  response = requests.post(API, headers=headers, json=payload)
  return response.json()


@app.route('/noteai.html', methods=['GET', 'POST'])
def noteai():
  global global_output_text
  try:
    global global_input_text  # Use the global_input_text variable
    input_text = global_input_text
    output_text = ""

    if request.method == 'POST':
      input_text = request.form['input_text']
      print(input_text)

      output_text = generate(input_text)
      global_output_text = output_text

      print(output_text)

  except Exception as e:
    input_text = ""
    output_text = "OH NO! An error has occoured within our main function. We don't really know what caused this but it will hopefully be fixed soon. Please try again later! -cozycornbreads"
    print(f"Main error: {e}")  # Print specific main error to console

  return render_template('noteai.html',
                         input_text=input_text[:],
                         output_text=output_text)


@app.route('/upload', methods=['POST'])
def upload_file():
  try:
    global global_input_text  # Use the global_input_text variable
    if 'pdf_file' in request.files:
      pdf_file = request.files['pdf_file']

      if pdf_file.filename != '':
        with pdfplumber.open(pdf_file) as pdf:
          pdf_text = "\n".join([page.extract_text() for page in pdf.pages])
        global_input_text = pdf_text  # Save the uploaded PDF text to the global variable

  except Exception as e:
    global_input_text = "OH NO! An error has occoured with our PDF upload system. Please try again later! -cozycornbreads"
    print(f"PDF Upload error: {e}")

  return redirect(
    '/noteai.html')  # Redirect back to the noteai page after upload


def generate_pdf(output_text, file_path):
  doc = SimpleDocTemplate(file_path, pagesize=letter)
  styles = getSampleStyleSheet()

  content = []
  content.append(Paragraph("Generated Summary:", styles['Title']))

  # Add the output_text to the PDF
  content.append(Spacer(1, 12))
  content.append(Paragraph(output_text, styles['Normal']))

  doc.build(content)


@app.route('/export_to_pdf')
def export_to_pdf():
  try:
    global global_input_text
    global output_text
    output_text = global_output_text  # Generate the output_text without passing any arguments

    # Create an in-memory PDF file
    pdf_buffer = io.BytesIO()
    generate_pdf(output_text, pdf_buffer)
    pdf_buffer.seek(0)

    # Create a Flask Response with the PDF file
    return Response(
      pdf_buffer.read(),
      content_type='application/pdf',
      headers={'Content-Disposition': 'inline; filename=summary.pdf'})
  except Exception as e:
    error_message = str(e)  # Convert the exception to a string
    print("Export to PDF error:", error_message)
    return f"An error occurred while exporting to PDF: {error_message}"


if __name__ == "__main__":
  # Start the Flask app
  app.run(host='0.0.0.0', port=81, debug=True)
