# app/models/database.py
import os
<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
=======
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
>>>>>>> bab022f4c848bc228d794e576292b4310b4d0d91
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env local
load_dotenv()

# Obtiene la URI de la base de datos
<<<<<<< HEAD
#DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = "postgresql://postgres:Abu02775401@db.obewsquzazreknuxtzxj.supabase.co:5432/postgres?sslmode=require"
=======
DATABASE_URL = os.getenv("DATABASE_URL")
>>>>>>> bab022f4c848bc228d794e576292b4310b4d0d91

if not DATABASE_URL:
    raise ValueError("❌ Error Crítico: La variable DATABASE_URL no está definida en el archivo .env")

# Configuración del motor de SQLAlchemy optimizado para Supabase (Puerto 6543)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica la validez de las conexiones antes de usarlas
    pool_recycle=1800    # Recicla las conexiones caídas cada 30 minutos
)

# Generador de sesiones locales independientes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán todos los modelos ORM
Base = declarative_base()

# ==============================================================================
<<<<<<< HEAD
# MODELOS DE DATOS COMPARTIDOS (Debe reflejar las tablas del Bot de WhatsApp)
=======
# MODELOS DE DATOS COMPARITDOS (Debe reflejar las tablas del Bot de WhatsApp)
>>>>>>> bab022f4c848bc228d794e576292b4310b4d0d91
# ==============================================================================

class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, index=True, nullable=False)
    monto = Column(Float, nullable=False)
    divisa = Column(String(3), default="ARS")         # Ejemplo: 'ARS' o 'USD'
    tipo = Column(String(10), nullable=False)          # 'ingreso' o 'egreso'
    categoria = Column(String(50), index=True)         # Ejemplo: 'Supermercado', 'Servicios'
    fecha = Column(DateTime, nullable=False)

class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, index=True, nullable=False)
    limite = Column(Float, nullable=False)
    activo = Column(Boolean, default=True)

class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    objetivo = Column(Float, nullable=False)
    saldo_actual = Column(Float, default=0.0)
<<<<<<< HEAD
    aceptado = Column(Boolean, default=False)
    fecha_aceptacion = Column(DateTime, default=datetime.utcnow)

# Dependencia para obtener la sesión de la base de datos en las rutas de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
=======
    usuario_id = Column(Uuid, nullable=False)
    version_id = Column(Uuid, ForeignKey("versiones_consentimiento.id"))
    aceptado = Column(Boolean, default=False)
    fecha_aceptacion = Column(DateTime(timezone=True), default=datetime.utcnow)
>>>>>>> bab022f4c848bc228d794e576292b4310b4d0d91
