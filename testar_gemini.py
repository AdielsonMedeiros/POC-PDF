"""
Teste do modelo gemini-2.0-flash
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

print('Testando gemini-2.0-flash...')

model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content('Responda apenas: OK')
print(f'SUCESSO! Resposta: {response.text}')
