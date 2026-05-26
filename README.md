cd ~/Estudios/Python/Proyectos/AutoVulnerabilities

cat > README.md << 'EOF'
#  AutoVulnerabilities - Sistema de Verificación y Auditoría de Dominios

Sistema automatizado para verificación de propiedad de dominios y análisis de vulnerabilidades.

##  Características

- ✅ **Registro de usuarios** con validación de emails corporativos
- ✅ **Generación de código único** de 43 caracteres por dominio
- ✅ **Verificación DNS TXT** para comprobar propiedad del dominio
- ✅ **Simulación de pago** con webhook integrado
- ✅ **Escaneo de vulnerabilidades** con OWASP ZAP
- ✅ **Base de datos SQLite** para almacenamiento persistente
- ✅ **Exportación automática a CSV** con crontab
- ✅ **Proxy inverso con Nginx** (dev.klbrs.es)

##  Tecnologías

| Tecnología | Uso |
|------------|-----|
| **FastAPI** | Framework web |
| **SQLite** | Base de datos embebida |
| **Docker** | Contenedor para OWASP ZAP |
| **Nginx** | Proxy inverso |
| **Crontab** | Automatización de backups |
| **SMTP** | Envío de emails |

##  Requisitos previos

- Python 3.11+
- Docker (para escaneos ZAP)
- Nginx (para proxy inverso)
- `dig` (para consultas DNS)

##  Instalación

```bash
# Clonar repositorio
git clone https://github.com/Luisit0/AutoVulnerabilities.git
cd AutoVulnerabilities

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env

# Inicializar base de datos
python -c "from app.models import init_db; init_db()"

# Ejecutar servidor
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
