from sqlalchemy.orm import Session
import models
import datetime
from functools import reduce
import crud.ingrediente_crud as ing_crud
import crud.menu_crud as menu_crud
import crud.cliente_crud as cli_crud

def get_pedidos(db: Session):
    return db.query(models.Pedido).order_by(models.Pedido.fecha.desc()).all()
def get_pedidos_by_cliente(db: Session, cid: int):
    return db.query(models.Pedido).filter(models.Pedido.cliente_id == cid).order_by(models.Pedido.fecha.desc()).all()
def get_pedido(db: Session, pid: int):
    return db.query(models.Pedido).filter(models.Pedido.id == pid).first()

def get_pedido_details(db: Session, pid: int):
    p = get_pedido(db, pid)
    if not p: return None
    detalles = [{"menu_id": a.menu_id, "nombre": a.menu.nombre, "cantidad": a.cantidad,
                 "precio_unitario": a.menu.precio, "subtotal": a.menu.precio * a.cantidad} for a in p.menus_asociados]
    return {"pedido": p, "cliente": p.cliente, "detalles": detalles}

def delete_pedido(db: Session, pid: int):
    p = get_pedido(db, pid)
    if not p: raise ValueError("Pedido no encontrado.")
    try:
        for a in p.menus_asociados: db.delete(a)
        db.delete(p); db.commit(); return True
    except Exception as e: db.rollback(); raise e

def create_pedido(db: Session, cid: int, items: list):
    if not items: raise ValueError("Carrito vacío.")
    cli = cli_crud.get_cliente(db, cid)
    if not cli: raise ValueError("Cliente inválido.")
    
    try:
        # USO DE MAP Y REDUCE (Requisito Pauta)
        subtotales = list(map(lambda x: x['menu'].precio * x['cantidad'], items))
        total = reduce(lambda a, b: a + b, subtotales, 0.0)

        # Validar y descontar stock (Requisito Crítico)
        for item in items:
            menu = item['menu']; cant = item['cantidad']
            detalles = menu_crud.get_menu_details(db, menu.id)
            for ing in detalles['detalles']:
                db_ing = ing_crud.get_ingrediente(db, ing['ingrediente_id'])
                req = ing['cantidad'] * cant
                if db_ing.stock < req:
                    raise ValueError(f"Stock insuficiente: {db_ing.nombre}")
                db_ing.stock -= req
        
        pedido = models.Pedido(total=total, cliente_id=cid, fecha=datetime.date.today(), descripcion=f"Pedido {cli.nombre}")
        db.add(pedido)
        
        for item in items:
            assoc = models.PedidoMenuAssociation(cantidad=item['cantidad'])
            assoc.menu = item['menu']
            pedido.menus_asociados.append(assoc)
            
        db.commit(); db.refresh(pedido); return pedido
    except Exception as e: db.rollback(); raise e