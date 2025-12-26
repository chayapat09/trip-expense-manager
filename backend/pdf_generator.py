"""
PDF Generator for invoices and refund statements
Using ReportLab for PDF generation with Thai font support
"""
import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List, Dict, Any

from schemas import InvoiceData, RefundData, InvoiceExpenseItem



# Company branding
COMPANY_NAME = "Nine Travel Co., Ltd."


class PDFGenerator:
    def __init__(self):
        self._register_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _register_fonts(self):
        """Register Sarabun font (Thai support)"""
        font_path = os.path.join(os.path.dirname(__file__), "data", "fonts", "Sarabun-Regular.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Sarabun', font_path))
            self.font_name = 'Sarabun'
            self.bold_font_name = 'Sarabun' # Using regular for bold since we only have regular
        else:
            print(f"Warning: Font not found at {font_path}, using Helvetica")
            self.font_name = 'Helvetica'
            self.bold_font_name = 'Helvetica-Bold'


    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='TitleStyle',
            fontSize=18,
            leading=22,
            spaceAfter=12,
            textColor=colors.HexColor('#1a1a2e'),
            fontName=self.bold_font_name
        ))
        self.styles.add(ParagraphStyle(
            name='SubtitleStyle',
            fontSize=12,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor('#4a4a4a'),
            fontName=self.font_name
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#1a1a2e'),
            fontName=self.bold_font_name
        ))
        self.styles.add(ParagraphStyle(
            name='TotalStyle',
            fontSize=14,
            leading=16,
            spaceBefore=12,
            textColor=colors.HexColor('#16213e'),
            fontName=self.bold_font_name
        ))
    
    def _create_table_style(self) -> TableStyle:
        """Standard table styling"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ])
    
    def generate_invoice_pdf(self, data: InvoiceData, trip_name: str) -> bytes:
        """Generate invoice PDF and return bytes (on-the-fly)"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        # --- Company Header ---
        elements.append(Paragraph(f"<font size=10 color='#666666'>{COMPANY_NAME}</font>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"INVOICE", self.styles['TitleStyle']))
        elements.append(Paragraph(f"<b>Trip:</b> {trip_name}", self.styles['SubtitleStyle']))
        elements.append(Paragraph(f"<b>Invoice #:</b> {data.version}", self.styles['SubtitleStyle']))
        elements.append(Paragraph(f"<b>Date:</b> {data.generated_at}", self.styles['SubtitleStyle']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        elements.append(Spacer(1, 0.2*inch))
        
        # --- Bill To ---
        elements.append(Paragraph("BILL TO:", self.styles['SectionHeader']))
        elements.append(Paragraph(f"<font size=14><b>{data.participant_name}</b></font>", self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # --- New Expenses Section ---
        if data.new_expenses:
            elements.append(Paragraph("NEW EXPENSES", self.styles['SectionHeader']))
            elements.append(Paragraph("<i>(Expenses incurred since last invoice)</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table
            table_data = [['Item', 'Original', 'Rate', 'Share', 'THB']]
            for item in data.new_expenses:
                currency_symbol = '¥' if item.currency == 'JPY' else '฿'
                rate_str = f"{item.buffer_rate}" if item.currency == 'JPY' else '-'
                table_data.append([
                    item.name,
                    f"{currency_symbol}{item.original_amount:,.0f}",
                    rate_str,
                    item.share,
                    f"฿{item.your_share_thb:,.2f}"
                ])
            
            table = Table(table_data, colWidths=[3*inch, 1*inch, 0.7*inch, 0.7*inch, 1*inch])
            table.setStyle(self._create_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
            
            # --- Total Section ---
            elements.append(Paragraph(f"<b>TOTAL AMOUNT DUE: ฿{data.this_invoice_total:,.2f}</b>", self.styles['TotalStyle']))
        else:
            elements.append(Paragraph("No new expenses since last invoice.", self.styles['Normal']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # --- Footer ---
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Please pay the total amount due to the trip organizer.", self.styles['Normal']))
        elements.append(Paragraph("Thank you for your prompt payment!", self.styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_refund_pdf(self, data: RefundData) -> bytes:
        """Generate detailed refund statement PDF (on-the-fly)"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=1.5*cm, leftMargin=1.5*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        # --- Company Header ---
        elements.append(Paragraph(f"<font size=10 color='#666666'>{COMPANY_NAME}</font>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"REFUND STATEMENT", self.styles['TitleStyle']))
        elements.append(Paragraph(f"<b>Trip:</b> {data.trip_name}", self.styles['SubtitleStyle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Info section
        elements.append(Paragraph(f"<b>Participant:</b> {data.participant_name}", self.styles['SubtitleStyle']))
        elements.append(Paragraph(f"<b>Generated:</b> {data.generated_at}", self.styles['SubtitleStyle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Section 1: Amount Collected
        elements.append(Paragraph("SECTION 1: AMOUNT COLLECTED (Upfront)", self.styles['SectionHeader']))
        elements.append(Paragraph("<i>(Based on buffer rates for shared expenses)</i>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        if data.collected_items:
            table_data = [['Item', 'Original', 'Rate', 'Share', 'Collected (THB)']]
            for item in data.collected_items:
                currency_symbol = '¥' if item.currency == 'JPY' else '฿'
                rate_str = f"{item.buffer_rate}" if item.buffer_rate else '-'
                table_data.append([
                    item.expense_name,
                    f"{currency_symbol}{item.original_amount:,.0f}",
                    rate_str,
                    item.share,
                    f"฿{item.collected_thb:,.2f}"
                ])
            
            table = Table(table_data, colWidths=[2.5*inch, 1*inch, 0.6*inch, 0.6*inch, 1.2*inch])
            table.setStyle(self._create_table_style())
            elements.append(table)
        else:
            elements.append(Paragraph("No collected items.", self.styles['Normal']))
        
        elements.append(Paragraph(f"<b>SUBTOTAL COLLECTED: ฿{data.total_collected:,.2f}</b>", self.styles['TotalStyle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Section 2: Actual Cost
        elements.append(Paragraph("SECTION 2: ACTUAL COST (Realized)", self.styles['SectionHeader']))
        elements.append(Paragraph("<i>(Your share of what was actually paid)</i>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        if data.actual_items:
            table_data = [['Item', 'Paid', 'Actual THB', 'Share', 'Your Cost (THB)']]
            for item in data.actual_items:
                currency_symbol = '¥' if item.paid_currency == 'JPY' else '฿'
                table_data.append([
                    item.expense_name,
                    f"{currency_symbol}{item.paid_amount:,.0f}",
                    f"฿{item.actual_thb:,.2f}",
                    item.share,
                    f"฿{item.your_cost_thb:,.2f}"
                ])
            
            table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 0.6*inch, 1.2*inch])
            table.setStyle(self._create_table_style())
            elements.append(table)
        else:
            elements.append(Paragraph("No actual payments recorded yet.", self.styles['Normal']))
        
        elements.append(Paragraph(f"<b>SUBTOTAL ACTUAL: ฿{data.total_actual:,.2f}</b>", self.styles['TotalStyle']))
        elements.append(Spacer(1, 0.4*inch))
        
        # Summary section
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a1a2e')))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("SUMMARY CALCULATION", self.styles['SectionHeader']))
        
        summary_data = [
            [f"Total Collected (Upfront):", f"฿{data.total_collected:,.2f}"],
            [f"Less: Total Actual Cost:", f"- ฿{data.total_actual:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#000000')),
        ]))
        elements.append(summary_table)
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Final refund line
        if data.refund_amount >= 0:
            refund_text = f"💰 REFUND DUE TO {data.participant_name.upper()}: ฿{data.refund_amount:,.2f}"
            status_color = colors.HexColor('#22c55e') # Green
        else:
            refund_text = f"⚠️ {data.participant_name.upper()} OWES ADDITIONAL: ฿{abs(data.refund_amount):,.2f}"
            status_color = colors.HexColor('#ef4444') # Red
        
        p_style = ParagraphStyle('FinalTotal', parent=self.styles['TotalStyle'], textColor=status_color, fontSize=16)
        elements.append(Paragraph(refund_text, p_style))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_receipt_pdf(self, data, trip_name: str) -> bytes:
        """Generate receipt PDF confirming payment received (on-the-fly)"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        # --- Company Header ---
        elements.append(Paragraph(f"<font size=10 color='#666666'>{COMPANY_NAME}</font>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"PAYMENT RECEIPT #{data.receipt_number}", self.styles['TitleStyle']))
        elements.append(Paragraph(f"<b>Trip:</b> {trip_name}", self.styles['SubtitleStyle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Info section
        elements.append(Paragraph(f"<b>Received from:</b> {data.participant_name}", self.styles['SubtitleStyle']))
        elements.append(Paragraph(f"<b>Date:</b> {data.generated_at}", self.styles['SubtitleStyle']))
        if data.payment_method:
            elements.append(Paragraph(f"<b>Payment Method:</b> {data.payment_method}", self.styles['SubtitleStyle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment confirmation
        elements.append(Paragraph("PAYMENT RECEIVED FOR:", self.styles['SectionHeader']))
        
        if data.items:
            table_data = [['Item', 'Original', 'Rate', 'Share', 'Amount (THB)']]
            for item in data.items:
                currency_symbol = '¥' if item.currency == 'JPY' else '฿'
                rate_str = f"{item.buffer_rate}" if item.buffer_rate else '-'
                table_data.append([
                    item.expense_name,
                    f"{currency_symbol}{item.original_amount:,.0f}",
                    rate_str,
                    item.share,
                    f"฿{item.amount_paid:,.2f}"
                ])
            
            table = Table(table_data, colWidths=[3*inch, 1*inch, 0.7*inch, 0.7*inch, 1*inch])
            table.setStyle(self._create_table_style())
            elements.append(table)
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#22c55e')))
        elements.append(Spacer(1, 0.2*inch))
        
        # Total with green success color
        elements.append(Paragraph(f"<b>✓ TOTAL RECEIVED: ฿{data.total_paid:,.2f}</b>", self.styles['TotalStyle']))
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Thank you for your payment!", self.styles['SubtitleStyle']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Singleton instance
pdf_generator = PDFGenerator()
