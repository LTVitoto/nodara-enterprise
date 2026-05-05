Markdown
# Manual de Despliegue - Nodara Enterprise

Bienvenido a Nodara Enterprise, el orquestador multi-agente definitivo. Sigue estos pasos para desplegar el entorno completo en tu máquina local.

## 📌 Requisitos Previos
1. **Git:** Instalado en tu sistema para clonar el repositorio.
2. **Docker Desktop:** Instalado y en ejecución (asegúrate de que el motor de Docker esté activo).
3. **Docker Compose:** Incluido por defecto en instalaciones modernas de Docker.

## 🚀 Instalación y Ejecución

**1. Clonar el Repositorio**
Abre tu terminal y ejecuta:
```bash
git clone https://github.com/LTVitoto/nodara-enterprise.git
cd nodara-enterprise
2. Configurar Variables de Entorno
Copia el archivo de ejemplo .env.example a .env 

Bash
cp .env.example .env
Asegúrate de incluir tu GITHUB_PERSONAL_ACCESS_TOKEN para habilitar el GitOps automático.

3. Levantar los Contenedores
Ejecuta el siguiente comando para construir las imágenes y levantar los servicios en segundo plano:

Bash
docker compose up -d --build
Nota: La primera vez tomará un par de minutos mientras descarga las imágenes de PostgreSQL, Node y Python.

🌐 Accesos al Sistema
Una vez que los contenedores estén en estado Running, puedes acceder a los servicios a través de las siguientes URLs:

Aplicación Frontend (Nodara UI): http://localhost:3000

API Backend (Documentación Swagger): http://localhost:8000/docs

Gestor de Base de Datos (pgAdmin): http://localhost:5050

🗄️ Conexión a la Base de Datos en pgAdmin
Para inspeccionar las tablas directamente en la interfaz web de pgAdmin, utiliza las siguientes credenciales (revisa tu docker-compose.yml para confirmar si usaste valores personalizados):

Email (Login pgAdmin): admin@admin.com

Password (Login pgAdmin): admin

Para registrar el servidor PostgreSQL dentro de pgAdmin:

Haz clic en "Add New Server".

Name: Nodara DB

Ve a la pestaña Connection:

Host name/address: db (este es el nombre del servicio en Docker)

Port: 5432

Maintenance database: nodara_db (o el valor de tu POSTGRES_DB)

Username: postgres (o el valor de tu POSTGRES_USER)

Password: root (o el valor de tu POSTGRES_PASSWORD)




Arquitectura y Diseño por:
www.victorfigueroa.cl