from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import re

def validate_email(email):
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError("Correo inválido.")

def get_cliente(db: Session, cid: int):
    return db.query(models.Cliente).filter(models.Cliente.id == cid).first()
def get_clientes(db: Session):
    return db.query(models.Cliente).all()

def create_cliente(db: Session, nombre: str, email: str):
    validate_email(email)
    if not nombre: raise ValueError("Nombre requerido.")
    if db.query(models.Cliente).filter(models.Cliente.email == email).first():
        raise IntegrityError("Correo ya existe.", None, None)
    
    cli = models.Cliente(nombre=nombre, email=email)
    try: db.add(cli); db.commit(); db.refresh(cli); return cli
    except Exception as e: db.rollback(); raise e

def update_cliente(db: Session, cid: int, nombre: str, email: str):
    cli = get_cliente(db, cid)
    if not cli: raise ValueError("Cliente no encontrado.")
    validate_email(email)
    
    check = db.query(models.Cliente).filter(models.Cliente.email == email).first()
    if check and check.id != cid: raise IntegrityError("Correo ya existe.", None, None)
    
    cli.nombre = nombre; cli.email = email
    try: db.commit(); db.refresh(cli); return cli
    except Exception as e: db.rollback(); raise e

def delete_cliente(db: Session, cid: int):
    cli = get_cliente(db, cid)
    if not cli: raise ValueError("Cliente no encontrado.")
    # VALIDACION CRITICA: No borrar si tiene pedidos
    if cli.pedidos: raise ValueError("No se puede eliminar: Tiene pedidos asociados.")
    try: db.delete(cli); db.commit(); return True
    except Exception as e: db.rollback(); raise e