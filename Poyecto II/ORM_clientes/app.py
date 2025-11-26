#FINAL
import customtkinter as ctk
from customtkinter import CTkEntry, CTkButton, CTkLabel, CTkFrame, CTkOptionMenu, CTkTextbox
import tkinter.messagebox as messagebox
from tkinter import ttk
import os

from database import SessionLocal
import crud.ingrediente_crud as ic
import crud.cliente_crud as cc
import crud.menu_crud as mc
import crud.pedido_crud as pc
import boleta_pdf
import graficos

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppRestaurante(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Restaurante - EV3")
        self.geometry("1100x700")
        self.db = SessionLocal()
        
        # Variables temporales
        self.cart = [] 
        self.temp_menu_ing = [] 
        
        # Layout principal
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.tabs = ctk.CTkTabview(self); self.tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Crear Pestañas
        self.t_compra = self.tabs.add("Panel de Caja")
        self.t_pedidos = self.tabs.add("Historial Pedidos")
        self.t_graficos = self.tabs.add("Estadísticas")
        self.t_clientes = self.tabs.add("Clientes")
        self.t_menus = self.tabs.add("Menús")
        self.t_ingred = self.tabs.add("Inventario")
        
        self.setup_styles()
        
        # Inicializar Módulos
        self.ui_compra(); self.ui_pedidos(); self.ui_graficos()
        self.ui_clientes(); self.ui_menus(); self.ui_ingredientes()
        
        self.actualizar_menus()

    def setup_styles(self):
        s = ttk.Style(); s.theme_use("default")
        s.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        s.map("Treeview", background=[('selected', '#1f6aa5')])

    # --- NUEVA FUNCIÓN: CLICK DERECHO PARA DESELECCIONAR ---
    def deseleccionar(self, event):
        # Quita la selección de cualquier fila en el árbol donde se hizo click
        try:
            tree = event.widget
            # selection_remove espera los items separados, por eso usamos * para desempaquetar la tupla
            if tree.selection():
                tree.selection_remove(*tree.selection())
        except Exception: pass

    # --- 1. MODULO COMPRA (CAJA) ---
    def ui_compra(self):
        t = self.t_compra; t.grid_columnconfigure(0, weight=1); t.grid_columnconfigure(1, weight=2)
        
        f1 = CTkFrame(t); f1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        CTkLabel(f1, text="Nueva Venta", font=("Arial", 20, "bold")).pack(pady=10)
        
        CTkLabel(f1, text="Cliente:").pack(); self.c_cli = CTkOptionMenu(f1); self.c_cli.pack(pady=5)
        CTkLabel(f1, text="Menú:").pack(); self.c_men = CTkOptionMenu(f1); self.c_men.pack(pady=5)
        CTkLabel(f1, text="Cantidad:").pack(); self.c_cant = CTkEntry(f1); self.c_cant.pack(pady=5)
        CTkButton(f1, text="Agregar al Carrito", command=self.añadir_carta, fg_color="green").pack(pady=20)
        
        # PANEL DERECHO
        f2 = CTkFrame(t); f2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.tree_cart = ttk.Treeview(f2, columns=("Prod", "Cant", "Sub"), show="headings")
        self.tree_cart.heading("Prod", text="Producto"); self.tree_cart.heading("Cant", text="Cant"); self.tree_cart.heading("Sub", text="Subtotal")
        self.tree_cart.pack(fill="both", expand=True, padx=5, pady=5)
        
        # BIND CLICK DERECHO
        self.tree_cart.bind("<Button-3>", self.deseleccionar)
        
        CTkButton(f2, text="Eliminar Item Seleccionado", command=self.borrar_producto, fg_color="#C0392B", height=30).pack(pady=5)
        
        # --- SECCIÓN TOTALES ---
        f_tot = CTkFrame(f2, fg_color="transparent")
        f_tot.pack(pady=10, fill="x")
        
        self.lbl_sub = CTkLabel(f_tot, text="Subtotal (Neto): $0", font=("Arial", 14))
        self.lbl_sub.pack(anchor="e", padx=20)
        
        self.lbl_iva = CTkLabel(f_tot, text="IVA (19%): $0", font=("Arial", 14))
        self.lbl_iva.pack(anchor="e", padx=20)
        
        self.lbl_tot = CTkLabel(f_tot, text="Total: $0", font=("Arial", 24, "bold"))
        self.lbl_tot.pack(anchor="e", padx=20)
        
        CTkButton(f2, text="FINALIZAR COMPRA", command=self.checkout, height=40, fg_color="#d35400").pack(fill="x", padx=20, pady=10)

    def añadir_carta(self):
        try:
            mid = int(self.c_men.get().split(":")[0])
            cant = int(self.c_cant.get())
            if cant <= 0: raise ValueError
            menu = mc.get_menu(self.db, mid)
            self.cart.append({"menu": menu, "cantidad": cant})
            self.recargar_carta()
        except: messagebox.showerror("Error", "Datos inválidos")

    def borrar_producto(self):
        try:
            selected = self.tree_cart.selection()
            if not selected: messagebox.showwarning("Atención", "Selecciona un producto."); return
            idx = self.tree_cart.index(selected[0])
            del self.cart[idx]
            self.recargar_carta()
        except Exception as e: messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def recargar_carta(self):
        for i in self.tree_cart.get_children(): self.tree_cart.delete(i)
        
        total_bruto = 0
        for x in self.cart:
            sub = x['menu'].precio * x['cantidad']
            total_bruto += sub
            self.tree_cart.insert("", "end", values=(x['menu'].nombre, x['cantidad'], f"${sub:.0f}"))
        
        neto = total_bruto / 1.19
        iva = total_bruto - neto
        
        self.lbl_sub.configure(text=f"Subtotal (Neto): ${neto:.0f}")
        self.lbl_iva.configure(text=f"IVA (19%): ${iva:.0f}")
        self.lbl_tot.configure(text=f"Total: ${total_bruto:.0f}")

    def checkout(self):
        try:
            if not self.cart: raise ValueError("Carrito vacío")
            cid = int(self.c_cli.get().split(":")[0])
            ped = pc.create_pedido(self.db, cid, self.cart)
            pdf = boleta_pdf.generar_boleta_pdf(ped, cc.get_cliente(self.db, cid), self.cart)
            os.startfile(pdf)
            messagebox.showinfo("Éxito", "Venta realizada")
            self.cart = []; self.recargar_carta(); self.actualizar_inventario(); self.refrescar_pedido()
        except Exception as e: messagebox.showerror("Error", str(e))

    # --- 2. MODULO PEDIDOS ---
    def ui_pedidos(self):
        self.tree_ped = ttk.Treeview(self.t_pedidos, columns=("ID", "Fecha", "Cliente", "Total"), show="headings")
        for c in ["ID", "Fecha", "Cliente", "Total"]: self.tree_ped.heading(c, text=c)
        self.tree_ped.pack(fill="both", expand=True, padx=10, pady=10)
        
        # BIND CLICK DERECHO
        self.tree_ped.bind("<Button-3>", self.deseleccionar)
        
        f_btns = CTkFrame(self.t_pedidos)
        f_btns.pack(pady=5)
        CTkButton(f_btns, text="Refrescar Lista", command=self.refrescar_pedido).pack(side="left", padx=5)
        CTkButton(f_btns, text="Eliminar Pedido", command=self.borrar_orden, fg_color="#C0392B").pack(side="left", padx=5)
        self.refrescar_pedido()

    def refrescar_pedido(self):
        for i in self.tree_ped.get_children(): self.tree_ped.delete(i)
        for p in pc.get_pedidos(self.db):
            self.tree_ped.insert("", "end", values=(p.id, p.fecha, p.cliente.nombre, f"${p.total:.0f}"))

    def borrar_orden(self):
        try:
            selected = self.tree_ped.selection()
            if not selected: messagebox.showwarning("Atención", "Selecciona un pedido."); return
            oid = int(self.tree_ped.item(selected[0])['values'][0])
            if messagebox.askyesno("Confirmar", f"¿Eliminar pedido ID {oid}?"):
                pc.delete_pedido(self.db, oid); self.refrescar_pedido()
                messagebox.showinfo("Éxito", "Pedido eliminado.")
        except Exception as e: messagebox.showerror("Error", str(e))

    # --- 3. MODULO GRAFICOS ---
    def ui_graficos(self):
        f = CTkFrame(self.t_graficos); f.pack(side="top", fill="x")
        self.g_opt = CTkOptionMenu(f, values=["Ventas Diarias", "Menús Populares", "Uso Ingredientes"])
        self.g_opt.pack(side="left", padx=10, pady=10)
        CTkButton(f, text="Generar", command=self.mostrar_grafico).pack(side="left")
        self.g_frame = CTkFrame(self.t_graficos); self.g_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def mostrar_grafico(self):
        try:
            o = self.g_opt.get()
            if o == "Ventas Diarias": fig = graficos.ventas_diarias(self.db)
            elif o == "Menús Populares": fig = graficos.menus_populares(self.db)
            else: fig = graficos.uso_ingredientes(self.db)
            graficos.draw_figure(self.g_frame, fig)
        except Exception as e: messagebox.showwarning("Info", str(e))

    # --- 4. MODULO CLIENTES ---
    def ui_clientes(self):
        f = CTkFrame(self.t_clientes); f.pack(side="left", fill="y", padx=10, pady=10)
        self.cl_nom = CTkEntry(f, placeholder_text="Nombre"); self.cl_nom.pack(pady=5)
        self.cl_eml = CTkEntry(f, placeholder_text="Email"); self.cl_eml.pack(pady=5)
        CTkButton(f, text="Guardar Nuevo", command=self.guardar_cliente).pack(pady=10)
        CTkButton(f, text="Eliminar Cliente", command=self.borrar_cliente, fg_color="#C0392B").pack(pady=10)

        self.tree_cli = ttk.Treeview(self.t_clientes, columns=("ID", "Nom", "Email"), show="headings")
        for c in ["ID", "Nom", "Email"]: self.tree_cli.heading(c, text=c)
        self.tree_cli.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # BIND CLICK DERECHO
        self.tree_cli.bind("<Button-3>", self.deseleccionar)
        
        self.actualizar_cliente()

    def guardar_cliente(self):
        try: cc.create_cliente(self.db, self.cl_nom.get(), self.cl_eml.get()); self.actualizar_cliente()
        except Exception as e: messagebox.showerror("Error", str(e))
    
    def borrar_cliente(self):
        try:
            selected = self.tree_cli.selection()
            if not selected: messagebox.showwarning("Atención", "Selecciona un cliente."); return
            cid = int(self.tree_cli.item(selected[0])['values'][0])
            if messagebox.askyesno("Confirmar", "¿Estás seguro?"):
                cc.borrar_clienteente(self.db, cid); self.actualizar_cliente(); messagebox.showinfo("Éxito", "Eliminado.")
        except ValueError as ve: messagebox.showerror("Error", str(ve))
        except Exception as e: messagebox.showerror("Error", f"Error: {e}")

    def actualizar_cliente(self):
        for i in self.tree_cli.get_children(): self.tree_cli.delete(i)
        for c in cc.get_clientes(self.db): self.tree_cli.insert("", "end", values=(c.id, c.nombre, c.email))
        self.actualizar_menus()

    # --- 5. MODULO MENUS ---
    def ui_menus(self):
        self.t_menus.grid_columnconfigure(0, weight=1)
        self.t_menus.grid_columnconfigure(1, weight=2)

        # IZQUIERDA: Crear
        f_left = CTkFrame(self.t_menus)
        f_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        CTkLabel(f_left, text="Crear Menú", font=("Arial", 18, "bold")).pack(pady=10)
        self.m_nom = CTkEntry(f_left, placeholder_text="Nombre Menú"); self.m_nom.pack(pady=5)
        self.m_desc = CTkEntry(f_left, placeholder_text="Descripción"); self.m_desc.pack(pady=5)
        self.m_precio = CTkEntry(f_left, placeholder_text="Precio ($)"); self.m_precio.pack(pady=5)
        
        CTkLabel(f_left, text="--- Ingredientes ---", font=("Arial", 12, "bold")).pack(pady=5)
        self.c_menu_ing = CTkOptionMenu(f_left, values=["-"]); self.c_menu_ing.pack(pady=2)
        self.m_cant_ing = CTkEntry(f_left, placeholder_text="Cantidad Requerida"); self.m_cant_ing.pack(pady=2)
        CTkButton(f_left, text="+ Agregar Ingrediente", command=self.agregar_ingrediente, fg_color="#2980B9").pack(pady=5)
        self.lbl_ing_list = CTkLabel(f_left, text="Ingredientes agregados: 0", text_color="gray")
        self.lbl_ing_list.pack(pady=2)
        CTkButton(f_left, text="GUARDAR MENÚ", command=self.guardar_nuevo_menu, fg_color="green").pack(pady=15)

        # DERECHA: Lista y Detalles
        f_right = CTkFrame(self.t_menus)
        f_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        CTkButton(f_right, text="⚡ CARGA AUTOMÁTICA", fg_color="#E67E22", command=self.auto_menu).pack(fill="x", pady=5)
        
        self.tree_men = ttk.Treeview(f_right, columns=("ID", "Nombre", "Precio"), show="headings", height=8)
        for c in ["ID", "Nombre", "Precio"]: self.tree_men.heading(c, text=c)
        self.tree_men.pack(fill="both", expand=True, padx=5, pady=5)
        
        # BIND CLICK DERECHO
        self.tree_men.bind("<Button-3>", self.deseleccionar)
        self.tree_men.bind("<<TreeviewSelect>>", self.mostrar_menu_clientes)
        
        CTkButton(f_right, text="Eliminar Menú Seleccionado", command=self.borrar_menu, fg_color="#C0392B").pack(fill="x", pady=5)
        
        CTkLabel(f_right, text="--- Información Detallada del Menú ---", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        self.txt_detalles = CTkTextbox(f_right, height=150, fg_color="#333333", text_color="white")
        self.txt_detalles.pack(fill="x", padx=5, pady=5)
        self.txt_detalles.insert("0.0", "Selecciona un menú de la lista para ver su descripción e ingredientes aquí.")
        self.txt_detalles.configure(state="disabled")
        
        self.actualizar_menu()

    def mostrar_menu_clientes(self, event):
        try:
            selected = self.tree_men.selection()
            if not selected: return
            mid = int(self.tree_men.item(selected[0])['values'][0])
            
            data = mc.get_menu_details(self.db, mid)
            if not data: return
            
            m = data['menu']
            texto = f"MENÚ: {m.nombre}\n"
            texto += f"PRECIO: ${m.precio:.0f}\n"
            texto += f"DESCRIPCIÓN: {m.descripcion}\n\n"
            texto += "INGREDIENTES REQUERIDOS:\n"
            for d in data['detalles']:
                texto += f"• {d['nombre']}: {d['cantidad']} {d['unidad'] or ''}\n"
            
            self.txt_detalles.configure(state="normal")
            self.txt_detalles.delete("0.0", "end")
            self.txt_detalles.insert("0.0", texto)
            self.txt_detalles.configure(state="disabled")
        except Exception as e: print(e)

    def agregar_ingrediente(self):
        try:
            sel = self.c_menu_ing.get()
            if sel == "-" or not sel: return
            iid = int(sel.split(":")[0])
            nom = sel.split(":")[1].strip()
            cant = float(self.m_cant_ing.get())
            if cant <= 0: raise ValueError
            
            self.temp_menu_ing.append({"id": iid, "nombre": nom, "cantidad": cant})
            self.lbl_ing_list.configure(text=f"Ingredientes agregados: {len(self.temp_menu_ing)}")
            messagebox.showinfo("Agregado", f"{nom} agregado.")
            self.m_cant_ing.delete(0, 'end')
        except: messagebox.showerror("Error", "Datos inválidos")

    def guardar_nuevo_menu(self):
        try:
            nom = self.m_nom.get()
            desc = self.m_desc.get()
            prec = float(self.m_precio.get())
            if not self.temp_menu_ing: raise ValueError("Faltan ingredientes")
            
            mc.create_menu(self.db, nom, prec, desc, self.temp_menu_ing)
            messagebox.showinfo("Éxito", "Menú creado")
            
            self.m_nom.delete(0, 'end'); self.m_desc.delete(0, 'end'); self.m_precio.delete(0, 'end')
            self.temp_menu_ing = []
            self.lbl_ing_list.configure(text="Ingredientes agregados: 0")
            self.actualizar_menu()
        except Exception as e: messagebox.showerror("Error", str(e))

    def borrar_menu(self):
        try:
            selected = self.tree_men.selection()
            if not selected: messagebox.showwarning("Atención", "Selecciona un menú."); return
            mid = int(self.tree_men.item(selected[0])['values'][0])
            
            if messagebox.askyesno("Eliminar", f"¿Borrar menú ID {mid}?"):
                mc.delete_menu(self.db, mid); self.actualizar_menu()
                self.txt_detalles.configure(state="normal"); self.txt_detalles.delete("0.0", "end"); self.txt_detalles.configure(state="disabled")
                messagebox.showinfo("Éxito", "Menú eliminado.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def auto_menu(self):
        if messagebox.askyesno("Confirmar", "¿Cargar menús base?"):
            msg = mc.cargar_menus_base_automaticos(self.db); messagebox.showinfo("Res", msg); self.actualizar_menu()
    def actualizar_menu(self):
        for i in self.tree_men.get_children(): self.tree_men.delete(i)
        for m in mc.get_menus(self.db): self.tree_men.insert("", "end", values=(m.id, m.nombre, f"${m.precio:.0f}"))
        self.actualizar_menus()

    # --- 6. MODULO INVENTARIO ---
    def ui_ingredientes(self):
        self.t_ingred.grid_columnconfigure(0, weight=1)
        self.t_ingred.grid_columnconfigure(1, weight=3)

        # PANEL IZQUIERDO: Formulario
        f_left = CTkFrame(self.t_ingred)
        f_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        CTkLabel(f_left, text="Nuevo Ingrediente", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.i_nom = CTkEntry(f_left, placeholder_text="Nombre Ingrediente")
        self.i_nom.pack(pady=5)
        
        self.i_stock = CTkEntry(f_left, placeholder_text="Stock a Agregar (Ej: 10)")
        self.i_stock.pack(pady=5)
        
        CTkLabel(f_left, text="Unidad:", font=("Arial", 12)).pack(pady=2)
        self.i_unidad = CTkOptionMenu(f_left, values=["un", "kg", "lt", "gr", "ml"])
        self.i_unidad.pack(pady=5)

        CTkButton(f_left, text="Guardar Ingrediente", command=self.guardar_ingrediente, fg_color="green").pack(pady=15)
        CTkButton(f_left, text="Eliminar Seleccionado", command=self.borrar_ingrediente, fg_color="#C0392B").pack(pady=5)

        # PANEL DERECHO: Lista y CSV
        f_right = CTkFrame(self.t_ingred)
        f_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        CTkButton(f_right, text="📂 Cargar desde CSV", command=self.cargar_csv, fg_color="#2980B9").pack(fill="x", pady=5)

        self.tree_inv = ttk.Treeview(f_right, columns=("ID", "Nom", "Stock", "Unidad"), show="headings")
        self.tree_inv.heading("ID", text="ID"); self.tree_inv.column("ID", width=30)
        self.tree_inv.heading("Nom", text="Nombre")
        self.tree_inv.heading("Stock", text="Stock")
        self.tree_inv.heading("Unidad", text="Unidad")
        self.tree_inv.pack(fill="both", expand=True, padx=5, pady=5)
        
        # BIND CLICK DERECHO
        self.tree_inv.bind("<Button-3>", self.deseleccionar)
        
        self.actualizar_inventario()

    def guardar_ingrediente(self):
        try:
            nom = self.i_nom.get().strip()
            if not nom: raise ValueError("El nombre no puede estar vacío.")
            stock = float(self.i_stock.get())
            if stock <= 0: raise ValueError("El stock debe ser mayor a 0.")
            uni = self.i_unidad.get()

            existing = ic.get_ingrediente_by_name(self.db, nom)
            
            if existing:
                if existing.unidad != uni:
                    raise ValueError(f"ERROR DE UNIDAD:\nEl ingrediente '{nom}' ya existe en '{existing.unidad}'.\nNo puedes agregarlo en '{uni}'.")
                
                existing.stock += stock
                self.db.commit()
                messagebox.showinfo("Actualizado", f"Ingrediente existente.\nSe sumaron {stock} {uni} a '{nom}'.\nNuevo Total: {existing.stock}")
            else:
                ic.create_ingrediente(self.db, nom, stock, uni)
                messagebox.showinfo("Creado", f"Nuevo ingrediente '{nom}' creado con éxito.")

            self.i_nom.delete(0, 'end'); self.i_stock.delete(0, 'end')
            self.actualizar_inventario()
            
        except ValueError as ve:
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def borrar_ingrediente(self):
        try:
            selected = self.tree_inv.selection()
            if not selected: messagebox.showwarning("Atención", "Selecciona un ingrediente."); return
            iid = int(self.tree_inv.item(selected[0])['values'][0])
            if messagebox.askyesno("Confirmar", "¿Eliminar ingrediente?"):
                ic.borrar_ingrediente(self.db, iid)
                self.actualizar_inventario()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_csv(self):
        msg = ic.cargar_ingredientes_csv(self.db, "ingredientes_menu.csv"); messagebox.showinfo("CSV", msg); self.actualizar_inventario()

    def actualizar_inventario(self):
        for i in self.tree_inv.get_children(): self.tree_inv.delete(i)
        for i in ic.get_ingredientes(self.db): self.tree_inv.insert("", "end", values=(i.id, i.nombre, i.stock, i.unidad))
        self.actualizar_menus()

    # --- UTILIDADES ---
    def actualizar_menus(self):
        cs = [f"{c.id}: {c.nombre}" for c in cc.get_clientes(self.db)]
        self.c_cli.configure(values=cs if cs else ["-"]); self.c_cli.set(cs[0] if cs else "-")
        
        ms = [f"{m.id}: {m.nombre}" for m in mc.get_menus(self.db)]
        self.c_men.configure(values=ms if ms else ["-"]); self.c_men.set(ms[0] if ms else "-")
        
        ings = [f"{i.id}: {i.nombre}" for i in ic.get_ingredientes(self.db)]
        if hasattr(self, 'c_menu_ing'):
            self.c_menu_ing.configure(values=ings if ings else ["-"])
            self.c_menu_ing.set(ings[0] if ings else "-")

if __name__ == "__main__":
    app = AppRestaurante()
    app.mainloop()