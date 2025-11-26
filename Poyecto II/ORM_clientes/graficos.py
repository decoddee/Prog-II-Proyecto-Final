import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import datetime

def ventas_diarias(db: Session):
    res = db.query(models.Pedido.fecha, func.sum(models.Pedido.total)).group_by(models.Pedido.fecha).all()
    if not res: raise ValueError("Sin datos")
    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot([r[0] for r in res], [r[1] for r in res], marker='o')
    ax.set_title("Ventas Diarias"); fig.tight_layout()
    return fig

def menus_populares(db: Session):
    res = db.query(models.Menu.nombre, func.sum(models.PedidoMenuAssociation.cantidad)).join(models.PedidoMenuAssociation).group_by(models.Menu.nombre).all()
    if not res: raise ValueError("Sin datos")
    fig, ax = plt.subplots(figsize=(6,4))
    ax.barh([r[0] for r in res], [r[1] for r in res], color='#0078d7')
    ax.set_title("Menús Vendidos"); fig.tight_layout()
    return fig

def uso_ingredientes(db: Session):
    # Lógica compleja simplificada para el gráfico
    sub = db.query(models.PedidoMenuAssociation.menu_id, func.sum(models.PedidoMenuAssociation.cantidad).label('t')).group_by(models.PedidoMenuAssociation.menu_id).subquery()
    res = db.query(models.Ingrediente.nombre, func.sum(models.MenuIngredienteAssociation.cantidad_requerida * sub.c.t)).join(models.MenuIngredienteAssociation).join(sub, models.MenuIngredienteAssociation.menu_id == sub.c.menu_id).group_by(models.Ingrediente.nombre).limit(10).all()
    if not res: raise ValueError("Sin datos")
    fig, ax = plt.subplots(figsize=(6,4))
    ax.barh([r[0] for r in res], [r[1] for r in res], color='green')
    ax.set_title("Ingredientes Usados"); fig.tight_layout()
    return fig

def draw_figure(canvas_frame, figure):
    for widget in canvas_frame.winfo_children(): widget.destroy()
    c = FigureCanvasTkAgg(figure, master=canvas_frame)
    c.draw(); c.get_tk_widget().pack(fill="both", expand=True)
    return c