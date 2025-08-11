import sys
import os

# agregar el directorio actual al path de python
# asi python puede encontrar modulos que esten en esta carpeta sin problemas
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# intentar importar la aplicacion principal y correr el servidor uvicorn
try:
    from app.main import app
    import uvicorn

    print("Starting Mario Audit Log API...")
    print("Database: SQLite")
    print("Documentation: http://localhost:8000/docs")

    # iniciar uvicorn para servir la app FastAPI en todas las interfaces, puerto 8000
    # sin recarga automatica (reload=False), nivel de log info
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

# en caso de error al importar, mostrar mensaje y detalles
except ImportError as e:
    print(f"Import error: {e}")
    print("Current directory:", current_dir)
    print("Contents:", os.listdir(current_dir))
