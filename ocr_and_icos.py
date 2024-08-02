import os
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfWriter
from PIL import Image
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#$env:PATH = "C:\Program Files\poppler\Library\bin;" + $env:PATH

COS_ENDPOINT = "https://s3.us-south.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID = "JJjTT0SsOpkUdNX8kR2Whw5ghIlr8hlmhxl1RzZ6Sl0i"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/a704679d44274f75b74b60a5a7c9ddd1:1c03c254-f0cd-4bb6-9aa1-1298c1116b55::"
BUCKET_NAME = "kr-bucket2"

cos = ibm_boto3.resource("s3",
                         ibm_api_key_id=COS_API_KEY_ID,
                         ibm_service_instance_id=COS_INSTANCE_CRN,
                         config=Config(signature_version="oauth"),
                         endpoint_url=COS_ENDPOINT)

def ocr_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    text = ""
    for page in pages:
        img = page.convert('L')
        text += pytesseract.image_to_string(img, lang="spa")
    return text

def save_text_as_pdf(text, output_path, title):
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle(title)
    width, height = letter
    y_position = height - 40  
    
    for line in text.split('\n'):
        if y_position < 40:  
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 40
        
        c.setFont("Helvetica", 12)
        c.drawString(40, y_position, line)
        y_position -= 14  
    
    c.save()

def upload_to_ibm_cos(file_path, bucket_name, item_name):
    try:
        cos.Bucket(bucket_name).upload_file(file_path, item_name)
        print(f"'{item_name}' uploaded to bucket '{bucket_name}'.")
    except ClientError as e:
        print(f"Unable to upload file: {e}")

def list_buckets():
    try:
        for bucket in cos.buckets.all():
            print(bucket.name)
    except ClientError as e:
        print(f"Unable to list buckets: {e}")
        exit()

input_directory = r"C:\Users\FALABELLA\Desktop\IBM Cloud\Contratos"
output_directory = r"C:\Users\FALABELLA\Desktop\IBM Cloud\Contratos_ocr2"

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for root, dirs, files in os.walk(input_directory):
    for file in files:
        if file.endswith('.pdf'):
            input_path = os.path.join(root, file)
            company_name = os.path.basename(root)
            output_path = os.path.join(output_directory, f"{company_name}_{file}")
            print(f"Processing file: {input_path}")
            extracted_text = ocr_from_pdf(input_path)
            title = os.path.splitext(file)[0]  
            save_text_as_pdf(extracted_text, output_path, title)

            item_name = f"{company_name}_{file}"
            upload_to_ibm_cos(output_path, BUCKET_NAME, item_name)

print("Processing complete.")
