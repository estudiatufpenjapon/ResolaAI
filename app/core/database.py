from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# crear el engine de la base de datos
# el engine se encarga de manejar el pool de conexiones y comunicarse con la base de datos
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # verificar que las conexiones esten activas antes de usarlas
    pool_recycle=300,    # recrear conexiones cada 300 segundos (5 minutos) para evitar desconexiones
    echo=False           # poner True para que muestre las consultas SQL en consola (debug)
)

# crear la fabrica de sesiones
# las sesiones manejan transacciones individuales a la base de datos
SessionLocal = sessionmaker(
    autocommit=False,    # controlar manualmente cuando hacer commit en transacciones
    autoflush=False,     # controlar manualmente cuando enviar cambios a la base de datos
    bind=engine          # asociar la sesion con nuestro engine de base de datos
)

# clase base para todos los modelos de la base de datos
# todos los modelos de SQLAlchemy van a heredar de esta clase base
Base = declarative_base()

# funcion dependencia para FastAPI
# proporciona una sesion de base de datos a los endpoints de la API
def get_db():
    """
    dependencia para la sesion de base de datos en los endpoints de FastAPI
    cierra la sesion automaticamente despues de procesar la peticion
    """
    db = SessionLocal()  # crear una nueva sesion
    try:
        yield db  # entregar la sesion al endpoint
    finally:
        db.close()  # cerrar siempre la sesion para liberar recursos
