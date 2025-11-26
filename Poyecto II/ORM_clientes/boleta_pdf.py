from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        # --- ENCABEZADO DE LA EMPRESA ---
        self.set_font('Arial', 'B', 20)
        self.cell(0, 10, 'RESTAURANTE SABORES DEL SUR', 0, 1, 'C')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'R.U.T.: 76.123.456-7', 0, 1, 'C')
        self.cell(0, 5, 'Giro: Venta de Comidas y Bebidas', 0, 1, 'C')
        self.cell(0, 5, 'Casa Matriz: Av. Alemania 0123, Temuco', 0, 1, 'C')
        self.cell(0, 5, 'Fono: +56 45 234 5678', 0, 1, 'C')
        self.ln(5)
        
        # Línea separadora
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 5, 'TIMBRE ELECTRÓNICO SII', 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 5, 'Res. 80 de 2014 Verifique documento: www.sii.cl', 0, 1, 'C')
        self.cell(0, 5, f'Página {self.page_no()}', 0, 0, 'R')

def generar_boleta_pdf(pedido, cliente, items):
    pdf = PDF()
    pdf.add_page()
    
    # --- DATOS DEL DOCUMENTO Y CLIENTE ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(130, 10, f'BOLETA ELECTRÓNICA Nº {pedido.id}', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 10, f"Fecha: {datetime.date.today().strftime('%d-%m-%Y')}", 0, 1, 'R')
    
    pdf.ln(5)
    
    # Cuadro con datos del cliente
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 8, "Señor(a):", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 8, f"{cliente.nombre}", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 8, "Email:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 8, f"{cliente.email}", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 8, "Detalle:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 8, f"{pedido.descripcion}", 0, 1)
    
    pdf.ln(10)
    
    # --- TABLA DE PRODUCTOS ---
    # Encabezados
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    
    pdf.cell(15, 10, "Cant.", 1, 0, 'C', 1)
    pdf.cell(115, 10, "Descripción", 1, 0, 'L', 1)
    pdf.cell(30, 10, "P. Unit", 1, 0, 'R', 1)
    pdf.cell(30, 10, "Total", 1, 1, 'R', 1)
    
    # Filas
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    total_bruto = 0
    
    for item in items:
        m = item['menu']
        c = item['cantidad']
        sub = m.precio * c
        total_bruto += sub
        
        pdf.cell(15, 8, str(c), 1, 0, 'C')
        pdf.cell(115, 8, f" {m.nombre}", 1, 0, 'L')
        pdf.cell(30, 8, f"${m.precio:,.0f}".replace(",", "."), 1, 0, 'R')
        pdf.cell(30, 8, f"${sub:,.0f}".replace(",", "."), 1, 1, 'R')

    pdf.ln(5)
    
    # --- CÁLCULOS FINALES (NETO, IVA, TOTAL) ---
    # Cálculo inverso del IVA (Total / 1.19)
    neto = total_bruto / 1.19
    iva = total_bruto - neto
    
    # Posicionar a la derecha
    x_pos = 130 
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(x_pos) # Mover cursor a la derecha
    pdf.cell(30, 6, "Monto Neto:", 0, 0, 'R')
    pdf.cell(30, 6, f"${neto:,.0f}".replace(",", "."), 1, 1, 'R')
    
    pdf.cell(x_pos)
    pdf.cell(30, 6, "I.V.A. (19%):", 0, 0, 'R')
    pdf.cell(30, 6, f"${iva:,.0f}".replace(",", "."), 1, 1, 'R')
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(x_pos)
    pdf.cell(30, 10, "TOTAL:", 0, 0, 'R')
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(30, 10, f"${total_bruto:,.0f}".replace(",", "."), 1, 1, 'R', 1)
    
    # --- MENSAJE FINAL ---
    pdf.ln(15)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "¡Gracias por su preferencia!", 0, 1, 'C')

    filename = f"boleta_{pedido.id}.pdf"
    pdf.output(filename)
    return filename