from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import crud.ingrediente_crud as ing_crud

def get_menu(db: Session, mid: int):
    return db.query(models.Menu).filter(models.Menu.id == mid).first()
def get_menu_by_name(db: Session, nombre: str):
    return db.query(models.Menu).filter(models.Menu.nombre == nombre).first()
def get_menus(db: Session):
    return db.query(models.Menu).all()

def get_menu_details(db: Session, mid: int):
    m = get_menu(db, mid)
    if not m: return None
    detalles = [{"ingrediente_id": a.ingrediente_id, "nombre": a.ingrediente.nombre, 
                 "cantidad": a.cantidad_requerida, "unidad": a.ingrediente.unidad} for a in m.ingredientes_asociados]
    return {"menu": m, "detalles": detalles}

def create_menu(db: Session, nombre: str, precio: float, desc: str, ing_data: list):
    if not nombre or precio <= 0 or not ing_data: raise ValueError("Datos inválidos.")
    if get_menu_by_name(db, nombre): raise IntegrityError("Menú ya existe.", None, None)
    
    menu = models.Menu(nombre=nombre, precio=precio, descripcion=desc)
    try:
        db.add(menu)
        for item in ing_data:
            assoc = models.MenuIngredienteAssociation(cantidad_requerida=item['cantidad'])
            assoc.ingrediente = ing_crud.get_ingrediente(db, item['id'])
            menu.ingredientes_asociados.append(assoc)
        db.commit(); db.refresh(menu); return menu
    except Exception as e: db.rollback(); raise e

def update_menu(db: Session, mid: int, nombre: str, precio: float, desc: str, ing_data: list):
    menu = get_menu(db, mid)
    if not menu: raise ValueError("Menú no encontrado.")
    
    menu.nombre = nombre; menu.precio = precio; menu.descripcion = desc
    try:
        for a in menu.ingredientes_asociados: db.delete(a)
        for item in ing_data:
            assoc = models.MenuIngredienteAssociation(cantidad_requerida=item['cantidad'])
            assoc.ingrediente = ing_crud.get_ingrediente(db, item['id'])
            menu.ingredientes_asociados.append(assoc)
        db.commit(); db.refresh(menu); return menu
    except Exception as e: db.rollback(); raise e

def delete_menu(db: Session, mid: int):
    menu = get_menu(db, mid)
    if not menu: raise ValueError("Menú no encontrado.")
    try:
        for a in menu.ingredientes_asociados: db.delete(a)
        db.delete(menu); db.commit(); return True
    except Exception as e: db.rollback(); raise e

# --- FUNCION PARA CARGA AUTOMATICA (BONUS UX) ---
def cargar_menus_base_automaticos(db: Session):
    recetas = [
        {"nombre": "Completo Italiano", "precio": 2500, "desc": "Pan, vienesa, tomate, palta", 
         "ing": [{"n": "Pan de completo", "c": 1}, {"n": "Vienesa", "c": 1}, {"n": "Tomate", "c": 0.1}, {"n": "Palta", "c": 0.1}]},
        {"nombre": "Churrasco Italiano", "precio": 4800, "desc": "Carne, tomate, palta", 
         "ing": [{"n": "Pan de hamburguesa", "c": 1}, {"n": "Churrasco de carne", "c": 1}, {"n": "Tomate", "c": 0.1}, {"n": "Palta", "c": 0.1}]},
        {"nombre": "Barros Luco", "precio": 5200, "desc": "Carne y queso caliente", 
         "ing": [{"n": "Pan de hamburguesa", "c": 1}, {"n": "Churrasco de carne", "c": 1}, {"n": "Lamina de queso", "c": 2}]},
        {"nombre": "Empanada de Pino", "precio": 2000, "desc": "Empanada de horno", 
         "ing": [{"n": "Masa de empanada", "c": 1}, {"n": "Carne de vacuno", "c": 0.1}, {"n": "Cebolla", "c": 0.05}, {"n": "Huevos", "c": 0.25}]}
    ]
    creados, errores = 0, 0
    for r in recetas:
        if get_menu_by_name(db, r["nombre"]): continue
        idata = []
        valido = True
        for i in r["ing"]:
            db_i = ing_crud.get_ingrediente_by_name(db, i["n"])
            if db_i: idata.append({"id": db_i.id, "cantidad": i["c"]})
            else: valido = False; break
        if valido:
            try: create_menu(db, r["nombre"], r["precio"], r["desc"], idata); creados += 1
            except: errores += 1
        else: errores += 1
    return f"Proceso terminado. Creados: {creados}. Faltantes: {errores}"