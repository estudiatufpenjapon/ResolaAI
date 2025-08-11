from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import logs


# funcion para crear las tablas de la base de datos
def create_tables():
    """
    crea todas las tablas de la base de datos
    esta funcion se encarga de crear fisicamente en la base de datos
    las tablas que estan definidas en los modelos de SQLAlchemy
    usa el metadata de Base para obtener todas las definiciones de tablas
    y las crea en la base si no existen ya
    se enlaza con el engine para ejecutar los comandos en la base especifica
    en caso de error, imprime un mensaje con el error
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("database tables created successfully")
    except Exception as e:
        print(f"error creating tables: {e}")


# creacion de la aplicacion FastAPI principal
app = FastAPI(
    title=settings.project_name,
    description="Audit Log API for tracking user actions and system events",
    version="1.0.0",
    docs_url="/docs",  # ruta donde estara disponible la documentacion swagger
    redoc_url="/redoc"  # ruta donde estara disponible la documentacion ReDoc
)

# configuracion del middleware CORS para controlar accesos desde navegadores frontend
# CORS es un mecanismo de seguridad que controla que sitios pueden hacer peticiones a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite solicitudes desde cualquier origen (en produccion se recomienda limitar a sitios conocidos)
    allow_credentials=True,  # permite enviar cookies y credenciales
    allow_methods=["*"],  # permite todos los metodos HTTP (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],  # permite todos los encabezados HTTP
)


# evento que se ejecuta al iniciar la aplicacion FastAPI
@app.on_event("startup")
async def startup_event():
    """
    evento de inicio de aplicacion
    se ejecuta automaticamente cuando la aplicacion comienza a correr
    en este evento se llama a create_tables para asegurarse que las tablas
    en la base de datos existan antes de aceptar peticiones
    luego imprime un mensaje indicando que la aplicacion inicio correctamente
    """
    create_tables()
    print(f"{settings.project_name} started successfully")


# incluir las rutas definidas en el modulo logs dentro de la API
# se usan los prefijos y etiquetas definidos en la configuracion
app.include_router(
    logs.router,
    prefix=settings.api_v1_str,  # ruta base para version 1 de la API
    tags=["audit-logs"]          # etiqueta para agrupar estos endpoints en la documentacion
)


# endpoint raiz para chequeo basico de estado de la API
@app.get("/")
async def root():
    """
    endpoint raiz para chequeo de estado (health check)
    devuelve un mensaje basico con informacion general de la API
    puede usarse para monitoreo basico o pruebas rapidas
    """
    return {
        "message": "Mario Audit Log API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


# endpoint para verificar la salud completa de la API y la conexion a la base de datos
@app.get("/health")
async def health_check():
    """
    endpoint para chequeo de salud mas completo
    intenta ejecutar una consulta basica "SELECT 1" en la base de datos
    si la consulta es exitosa, confirma que la base de datos esta conectada y funcionando
    en caso de error lanza una excepcion HTTP 503 indicando que la base no esta disponible
    devuelve un objeto JSON con estado de salud y marca temporal
    """
    try:
        # abrir conexion a la base de datos usando el engine
        with engine.connect() as connection:
            # ejecutar una consulta simple para probar conexion
            connection.execute(text("SELECT 1"))

        # si la consulta fue exitosa, devolver estado saludable
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-08-11T00:00:00Z"  # puede ajustarse a hora actual dinamicamente
        }
    except Exception as e:
        # si ocurre error, lanzar una excepcion HTTP con codigo 503 (servicio no disponible)
        raise HTTPException(
            status_code=503,
            detail=f"database connection failed: {str(e)}"
        )


# manejador personalizado para errores 404 (recurso no encontrado)
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    handler para capturar errores 404
    devuelve un JSON con informacion estandarizada para errores de recurso no encontrado
    puede personalizarse para logging o formatos especificos
    """
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }


# manejador personalizado para errores 500 (error interno del servidor)
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """
    handler para capturar errores 500
    devuelve un JSON con mensaje generico de error interno
    util para evitar exponer detalles internos y mantener formato consistente
    """
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }


# bloque principal para ejecutar la aplicacion si este archivo es ejecutado directamente
if __name__ == "__main__":
    import uvicorn

    # imprimir informacion basica al iniciar
    print("Starting Mario Audit Log API...")
    print(f"Database: {settings.database_url}")
    print(f"Documentation: http://localhost:8000/docs")

    # arrancar el servidor uvicorn para correr la app FastAPI
    uvicorn.run(
        "main:app",     # nombre del modulo y objeto app a ejecutar
        host="0.0.0.0", # escuchar en todas las interfaces de red disponibles
        port=8000,      # puerto en el que se expondrá la API
        reload=True,    # activar recarga automatica al cambiar codigo (solo desarrollo)
        log_level="info" # nivel de log para salida de consola
    )
