# pdf_generator.py
# Handles the generation of PDF documents for challans and monthly bills.

import io
from fpdf import FPDF
from num2words import num2words
from datetime import datetime
from PIL import Image # Import the Pillow library

class PDF(FPDF):
    def __init__(self, company_details, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_details = company_details
        self.doc_title = "INVOICE"
        self.is_monthly_bill = False

    def set_doc_title(self, title, is_monthly_bill=False):
        self.doc_title = title
        self.is_monthly_bill = is_monthly_bill

    def _draw_text_header(self):
        """A fallback function to draw a text-based header if the image fails."""
        self.set_y(10)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 6, self.company_details['name'], 0, 1, "C")
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, self.company_details['brand_name'], 0, 1, "C")
        self.set_font("Helvetica", "", 9)
        address_text = f"{self.company_details['address']} | Phone - {self.company_details['phone']}"
        self.cell(0, 5, address_text, 0, 1, "C")
        self.cell(0, 5, f"PAN No. - {self.company_details['pan']} | LLP PIN - {self.company_details['llp_pin']}", 0, 1, "C")
        self.set_y(45)

    def _draw_text_footer(self):
        """A fallback function to draw a text-based footer if the image fails."""
        self.set_y(-30)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, "For OnLine YourDesk Stationer & Services LLP", 0, 1, "R")
        self.ln(8)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "-# Thank You, Order Again and Be Happy #-", 0, 1, "C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, f"Reg. Address - {self.company_details['reg_address']}", 0, 1, "C")

    def header(self):
        if self.is_monthly_bill:
            try:
                with Image.open('Bill Header.png') as img:
                    rgb_img = img.convert('RGB')
                    with io.BytesIO() as temp_img_buffer:
                        rgb_img.save(temp_img_buffer, format='PNG')
                        temp_img_buffer.seek(0)
                        
                        page_width = self.w - self.l_margin - self.r_margin
                        self.image(temp_img_buffer, x=self.l_margin, y=8, w=page_width, type='PNG')
                
                self.set_y(45)
            except Exception as e:
                print(f"!!! PDF HEADER WARNING: Could not load 'Bill Header.png'. Falling back to text. Reason: {e}")
                self._draw_text_header()
            
            self.set_font("Helvetica", "B", 14)
            self.cell(0, 8, self.doc_title, 0, 1, "C")
            self.ln(2)
        else:
            # Challan Header
            self.set_y(15)
            try:
                self.set_font("Elephant", "", 16)
            except RuntimeError:
                self.set_font("Helvetica", "B", 16)
            
            self.set_text_color(2, 122, 235)
            self.cell(0, 7, "OnLine Your Desk Stationer", 0, 1, "C")
            self.cell(0, 7, "Services LLP", 0, 1, "C")
            self.set_font("Helvetica", "B", 10)
            self.ln(2)
            self.set_text_color(0, 0, 0)
            address_text = (f"Shop No 01, Shejarcha Katta, Vitthal Rukumai Mandir Road,\n"
                           f"Ghatla Village, Chembur, Mumbai - 400071.\n"
                           f"Mob - {self.company_details['phone']}")
            self.multi_cell(0, 5, address_text, 0, "C")
            self.ln(5)

    def footer(self):
        if self.is_monthly_bill:
            try:
                with Image.open('Bill Footer.png') as img:
                    rgb_img = img.convert('RGB')
                    with io.BytesIO() as temp_img_buffer:
                        rgb_img.save(temp_img_buffer, format='PNG')
                        temp_img_buffer.seek(0)
                        
                        page_width = self.w - self.l_margin - self.r_margin
                        footer_height = 20
                        self.image(temp_img_buffer, x=self.l_margin, y=self.h - footer_height - 15, w=page_width, type='PNG')
            except Exception as e:
                print(f"!!! PDF FOOTER WARNING: Could not load 'Bill Footer.png'. Falling back to text. Reason: {e}")
                self._draw_text_footer()
        
        elif not self.is_monthly_bill:
            self.set_y(-30)
            self.set_x(20)
            self.set_font("Helvetica", "B", 11)
            self.cell(0, 8, "Thanks", 0, 1, 'L')
            self.set_x(20)
            self.cell(0, 8, "OnLine Services LLP", 0, 1, 'L')

def create_monthly_bill_pdf(company_details, bill_data, items_data):
    pdf = PDF(company_details, 'P', 'mm', 'A4')
    pdf.set_doc_title("INVOICE", is_monthly_bill=True)
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    
    drawable_width = pdf.w - pdf.l_margin - pdf.r_margin

    # --- HEADER & CLIENT INFO ---
    pdf.set_x(30)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(drawable_width / 2, 7, f"Bill No - {bill_data['bill_no_formatted']}", 0, 0, "L")
    pdf.set_x(95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(drawable_width / 2, 7, f"Date - {bill_data['billing_date']}", 0, 1, "R")
    
    pdf.set_x(30)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(15, 8, "M/S. -", 0, 0, "L")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(pdf.get_string_width(bill_data['client_name']) + 2, 8, bill_data['client_name'], "B", 1, "L")
    pdf.ln(4)

    # --- TABLE DEFINITION (CENTERED) ---
    col_widths = {'sr': 10, 'part': 75, 'date': 20, 'rate': 15, 'qty': 18, 'amt': 28}
    table_width = sum(col_widths.values())
    start_x = pdf.l_margin + (drawable_width - table_width) / 2
    
    header_height = 9
    pdf.set_x(start_x)
    
    pdf.set_fill_color(138, 138, 138)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)

    header_start_y = pdf.get_y()
    
    pdf.multi_cell(col_widths['sr'], header_height/2, "Sr.\nNo.", 1, "C", fill=True)
    pdf.set_y(header_start_y)
    pdf.set_x(start_x + col_widths['sr'])
    pdf.cell(col_widths['part'], header_height, "Particular", 1, 0, "C", fill=True)
    pdf.multi_cell(col_widths['date'], header_height/2, "Date\nDelivery", 1, "C", fill=True)
    pdf.set_y(header_start_y)
    pdf.set_x(start_x + col_widths['sr'] + col_widths['part'] + col_widths['date'])
    pdf.cell(col_widths['rate'], header_height, "Rate", 1, 0, "C", fill=True)
    pdf.cell(col_widths['qty'], header_height, "QTY.", 1, 0, "C", fill=True)
    pdf.cell(col_widths['amt'], header_height, "Amount", 1, 1, "C", fill=True)
    pdf.line(start_x, header_start_y + header_height, start_x + table_width, header_start_y + header_height)

    # --- FIXED SIZE TABLE ---
    table_start_y = pdf.get_y()
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(232, 232, 232)
    
    num_item_rows = 20
    row_height = 7
    for i in range(num_item_rows):
        pdf.set_x(start_x)
        pdf.cell(col_widths['sr'], row_height, '', 'LR', 0, fill=True)
        pdf.cell(col_widths['part'], row_height, '', 'LR', 0, fill=True)
        pdf.cell(col_widths['date'], row_height, '', 'LR', 0, fill=True)
        pdf.cell(col_widths['rate'], row_height, '', 'LR', 0, fill=True)
        pdf.cell(col_widths['qty'], row_height, '', 'LR', 0, fill=True)
        pdf.cell(col_widths['amt'], row_height, '', 'LR', 1, fill=True)

    current_y = table_start_y
    grand_total = 0
    for i, item in enumerate(items_data, 1):
        if i > num_item_rows: break
        grand_total += item['item_total']
        pdf.set_y(current_y)
        pdf.set_x(start_x)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_widths['sr'], row_height, str(i), 0, 0, "C")
        pdf.cell(col_widths['part'], row_height, item['name'], 0, 0, "L")
        
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_widths['date'], row_height, item['challan_date'].strftime('%d-%b'), 0, 0, "C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_widths['rate'], row_height, f"{item['price_per_unit']:.0f}", 0, 0, "R")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_widths['qty'], row_height, str(item['quantity']), 0, 0, "C")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_widths['amt'], row_height, f"{item['item_total']:.0f}", 0, 1, "R")
        
        current_y += row_height
    
    pdf.set_font("Helvetica", "", 10)

    # --- FIXED POSITION ACCOUNT DETAILS ---
    pdf.set_y(200) # Set a fixed Y position
    pdf.set_x(start_x + col_widths['sr'])
    
    pdf.set_font("Helvetica", "B", 10)
    bank = company_details['bank_details']
    pdf.multi_cell(col_widths['part'], 4,
        f"Account Details-\n"
        f"Ac No - {bank['ac_no']}\n"
        f"IFSC No - {bank['ifsc']}\n"
        f"Branch - {bank['branch']}\n"
        f"Bank Name - {bank['bank_name']}",
        0, "L"
    )

    # --- SUMMARY ROWS ---
    table_end_y = table_start_y + (num_item_rows * row_height)
    pdf.set_y(table_end_y)
    
    pdf.set_x(start_x)
    subtotal_label_width = table_width - col_widths['amt']
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(subtotal_label_width, 6, "Sub-Total", 1, 0, "R")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_widths['amt'], 6, f"{int(grand_total)}", 1, 1, "R")

    pdf.set_x(start_x)
    amount_in_words = "Amount - " + num2words(int(grand_total), lang='en_IN').title() + " Only"
    total_amount_str = f"{int(grand_total):,}"
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(table_width - col_widths['amt'], 6, amount_in_words, 1, 0, "R")
    pdf.cell(col_widths['amt'], 6, total_amount_str, 1, 1, "R")

    pdf_bytes = pdf.output()
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

def create_challan_pdf(company_details, challan_data, items_data):
    pdf = PDF(company_details, 'P', 'mm', 'A5')
    
    try:
        pdf.add_font('Elephant', '', 'elephant.ttf', uni=True)
    except Exception:
        print("WARNING: elephant.ttf not found or failed to load. Falling back to default font.")

    pdf.set_auto_page_break(auto=False)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    pdf.rect(5.0, 5.0, 138.0, 200.0)

    pdf.set_font("Helvetica", "B", 10)
    month_prefix = challan_data['challan_date'].strftime('%B')[:2].upper()
    challan_text = f"Bill Challan {month_prefix}{challan_data['challan_id']:03d}"
    date_text = f"Date - {challan_data['challan_date'].strftime('%d-%b-%Y')}"
    
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    half_width = page_width / 2
    pdf.cell(half_width, 8, challan_text, 0, 0, "C")
    pdf.cell(half_width, 8, date_text, 0, 1, "C")
    
    pdf.line(pdf.get_x() + 16, pdf.get_y(), pdf.get_x() + 48, pdf.get_y())
    pdf.line(pdf.get_x() + 80, pdf.get_y(), pdf.get_x() + 112, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(15, 8, "M/s.-", 0, 0, "L")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, challan_data['company_name'], 0, 1, "L")
    pdf.line(pdf.get_x() + 15, pdf.get_y(), pdf.get_x() + page_width, pdf.get_y())
    pdf.ln(5)

    col_widths = {'sr': 10, 'part': 68, 'qty': 15, 'rate': 15, 'amt': 20}

    pdf.set_font("Helvetica", "B", 10)
    header_start_y = pdf.get_y()
    pdf.multi_cell(col_widths['sr'], 4, "Sr.\nNo.", 1, "C")
    pdf.set_y(header_start_y)
    pdf.set_x(10 + col_widths['sr'])
    pdf.cell(col_widths['part'], 8, "Particular", 1, 0, "C")
    pdf.cell(col_widths['qty'], 8, "Qty.", 1, 0, "C")
    pdf.cell(col_widths['rate'], 8, "Rate", 1, 0, "C")
    pdf.cell(col_widths['amt'], 8, "Amount", 1, 1, "C")
    
    table_start_y = pdf.get_y()
    pdf.set_font("Helvetica", "", 10)
    
    num_item_rows = 12
    for i in range(num_item_rows):
        pdf.cell(col_widths['sr'], 7, '', 'LR', 0)
        pdf.cell(col_widths['part'], 7, '', 'LR', 0)
        pdf.cell(col_widths['qty'], 7, '', 'LR', 0)
        pdf.cell(col_widths['rate'], 7, '', 'LR', 0)
        pdf.cell(col_widths['amt'], 7, '', 'LR', 1)

    current_y = table_start_y
    for i, item in enumerate(items_data, 1):
        if i > num_item_rows: break
        pdf.set_y(current_y)
        pdf.set_x(10)
        pdf.cell(col_widths['sr'], 7, str(i), 0, 0, "C")
        pdf.cell(col_widths['part'], 7, item['name'], 0, 0, "L")
        pdf.cell(col_widths['qty'], 7, str(item['quantity']), 0, 0, "C")
        pdf.cell(col_widths['rate'], 7, f"{item['price_per_unit']:.0f}", 0, 0, "R")
        pdf.cell(col_widths['amt'], 7, f"{item['item_total']:.0f}", 0, 1, "R")
        current_y += 7

    # Set a fixed Y position for account details
    pdf.set_y(153)
    pdf.set_x(10 + col_widths['sr'])
    
    pdf.set_font("Helvetica", "B", 8)
    bank = company_details['bank_details']
    pdf.multi_cell(col_widths['part'], 3,
        f"Account Details-\n"
        f"Ac No - {bank['ac_no']}\n"
        f"IFSC No - {bank['ifsc']}\n"
        f"Branch - {bank['branch']}\n"
        f"Bank Name - {bank['bank_name']}",
        0, "L"
    )

    total_amount = challan_data['total_amount']
    amount_in_words = "Rs. - " + num2words(int(total_amount), lang='en_IN').title() + " Only"
    total_amount_str = f"{total_amount:,.0f}/-"
    
    final_row_y = table_start_y + (num_item_rows * 7) 
    pdf.set_y(final_row_y)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_widths['sr'] + col_widths['part'], 8, amount_in_words, 'LTB', 0, "L")
    pdf.cell(col_widths['qty'] + col_widths['rate'], 8, "", 'TRB', 0, "C")
    pdf.cell(col_widths['amt'], 8, total_amount_str, 1, 1, "R")

    pdf_bytes = pdf.output()
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer