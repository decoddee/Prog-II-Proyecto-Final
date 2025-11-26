from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import csv

def get_ingrediente(db: Session, ingrediente_id: int):
    return db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()
def get_ingrediente_by_name(db: Session, nombre: str):
    return db.query(models.Ingrediente).filter(models.Ingrediente.nombre == nombre).first()
def get_ingredientes(db: Session):
    return db.query(models.Ingrediente).all()

def create_ingrediente(db: Session, nombre: str, stock: float, unidad: str):
    if not nombre: raise ValueError("El nombre no puede estar vacío.")
    if stock <= 0: raise ValueError("El stock debe ser positivo.")
    if get_ingrediente_by_name(db, nombre):
        raise IntegrityError(f"Ingrediente '{nombre}' ya existe.", params=None, orig=None)
    
    db_ingrediente = models.Ingrediente(nombre=nombre, stock=stock, unidad=unidad)
    try:
        db.add(db_ingrediente); db.commit(); db.refresh(db_ingrediente)
        return db_ingrediente
    except Exception as e: db.rollback(); raise e

def update_ingrediente(db: Session, ingrediente_id: int, nombre: str, stock: float, unidad: str):
    db_ing = get_ingrediente(db, ingrediente_id)
    if not db_ing: raise ValueError("Ingrediente no encontrado.")
    if stock <= 0: raise ValueError("El stock debe ser positivo.")
    
    db_ing.nombre = nombre; db_ing.stock = stock; db_ing.unidad = unidad
    try:
        db.commit(); db.refresh(db_ing); return db_ing
    except Exception as e: db.rollback(); raise e

def delete_ingrediente(db: Session, ingrediente_id: int):
    db_ing = get_ingrediente(db, ingrediente_id)
    if not db_ing: raise ValueError("Ingrediente no encontrado.")
    try:
        db.delete(db_ing); db.commit(); return True
    except Exception as e: db.rollback(); raise e

def cargar_ingredientes_csv(db: Session, csv_file_path: str):
    try:
        # 'utf-8-sig' maneja el BOM de Excel
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file); filas = list(reader)
            
            # USO DE MAP Y LAMBDA (Requisito Pauta)
            def procesar_fila(fila):
                try: 
                    # Adaptado a tu CSV que usa 'cantidad' en vez de 'stock'
                    return {"nombre": fila['nombre'], "stock": float(fila['cantidad']), "unidad": fila['unidad']}
                except (KeyError, ValueError): return None
            
            procesados = list(map(procesar_fila, filas))
            # USO DE FILTER Y LAMBDA (Requisito Pauta)
            validos = list(filter(lambda x: x is not None and x['stock'] > 0, procesados))
            
            res = {"c": 0, "a": 0, "e": 0}
            for item in validos:
                try:
                    db_ing = get_ingrediente_by_name(db, item['nombre'])
                    if db_ing:
                        db_ing.stock = item['stock']; db_ing.unidad = item['unidad']; res["a"] += 1
                    else:
                        db.add(models.Ingrediente(**item)); res["c"] += 1
                    db.commit()
                except Exception: db.rollback(); res["e"] += 1
            return f"Carga CSV: {res['c']} Creados, {res['a']} Actualizados, {res['e']} Errores."
    except Exception as e: return f"Error: {e}"