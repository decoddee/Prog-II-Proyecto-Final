from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
import datetime

class MenuIngredienteAssociation(Base):
    __tablename__ = 'menu_ingrediente_association'
    menu_id = Column(Integer, ForeignKey('menus.id'), primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey('ingredientes.id'), primary_key=True)
    cantidad_requerida = Column(Float, nullable=False)
    
    ingrediente = relationship("Ingrediente")
    menu = relationship("Menu", back_populates="ingredientes_asociados")

class PedidoMenuAssociation(Base):
    __tablename__ = 'pedido_menu_association'
    pedido_id = Column(Integer, ForeignKey('pedidos.id'), primary_key=True)
    menu_id = Column(Integer, ForeignKey('menus.id'), primary_key=True)
    cantidad = Column(Integer, default=1)
    
    menu = relationship("Menu", back_populates="pedidos_asociados")
    pedido = relationship("Pedido", back_populates="menus_asociados")

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    pedidos = relationship("Pedido", back_populates="cliente")

class Ingrediente(Base):
    __tablename__ = "ingredientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    stock = Column(Float, nullable=False, default=0.0)
    unidad = Column(String)

class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String)
    precio = Column(Float, nullable=False)

    ingredientes_asociados = relationship("MenuIngredienteAssociation", back_populates="menu")
    pedidos_asociados = relationship("PedidoMenuAssociation", back_populates="menu")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, default=datetime.date.today, nullable=False)
    total = Column(Float, nullable=False)
    descripcion = Column(String, default="Pedido")
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cliente = relationship("Cliente", back_populates="pedidos")
    menus_asociados = relationship("PedidoMenuAssociation", back_populates="pedido")