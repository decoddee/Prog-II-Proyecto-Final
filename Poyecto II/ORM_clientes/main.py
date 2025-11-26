from database import engine, Base
import models 

print("Inicializando la base de datos y creando tablas...")
Base.metadata.create_all(bind=engine)
print("Base de datos 'restaurante.db' creada con éxito.")