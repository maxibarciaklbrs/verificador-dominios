# 🔐 Sistema de Verificación de Dominios

Sistema completo para verificar propiedad de dominios mediante:
- 📁 Archivo TXT en el servidor web (URL)
- 🌐 Registro TXT en DNS

## 🚀 Características

- Formulario de registro con validación de emails gratuitos
- Generación de códigos de verificación seguros (32-43 caracteres)
- Verificación mediante URL (archivo .txt) o DNS TXT
- API independiente para consultas
- Envío automático de emails con instrucciones

## 📋 Requisitos

- Python 3.8+
- FastAPI
- Uvicorn
- dnspython
- requests

## 🔧 Instalación

```bash
# Clonar repositorio
git clone https://github.com/klbrs/verificador-dominios.git
cd verificador-dominios

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
