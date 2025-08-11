from dotenv import load_dotenv
import os

# cargar las variables de entorno desde el archivo .env
# esto permite usar configuraciones sensibles o que cambian sin ponerlas en el codigo
load_dotenv()


class Settings:
    def __init__(self):
        # obtener la url de la base de datos desde las variables de entorno
        # si no existe, sera None
        self.database_url = os.getenv("DATABASE_URL")

        # obtener la clave secreta para encriptacion o tokens desde variables de entorno
        self.secret_key = os.getenv("SECRET_KEY")

        # obtener el algoritmo para tokens o encriptacion, si no esta definido usa 'HS256' por defecto
        self.algorithm = os.getenv("ALGORITHM", "HS256")

        # obtener el tiempo de expiracion del token en minutos, si no esta definido usa 30 minutos por defecto
        # se convierte a entero porque os.getenv devuelve string
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # ruta base para la version 1 de la api, definida directamente en el codigo
        self.api_v1_str = "/api/v1"

        # nombre del proyecto o aplicacion, tambien definido directamente en el codigo
        self.project_name = "Mario Audit Log API"


# crear una instancia unica de Settings para usarla en toda la aplicacion
settings = Settings()
