from io import BytesIO
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.pdfgen import canvas
from django.conf import settings
from decimal import Decimal

class InvoicePDFGenerator:
    """
    Classe pour générer un PDF à partir d'une facture avec pagination automatique.
    """
    def __init__(self, invoice):
        """
        Initialisation avec une facture.
        
        Args:
            invoice: Instance du modèle Invoice
        """
        self.invoice = invoice
        self.buffer = BytesIO()
        self.width, self.height = A4
        
        # Définition des styles
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.title_style.alignment = 1  # Centré
        
        self.subtitle_style = self.styles['Heading2']
        self.normal_style = self.styles['Normal']
        
        # Style pour l'entête
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=14,
            alignment=2,  # Droite
        )
        
        # Style pour les informations client
        self.client_style = ParagraphStyle(
            'ClientStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=13,
        )
        
        # Style pour les sections
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Heading3'],
            fontSize=12,
            leading=14,
            spaceAfter=6,
            spaceBefore=12,
        )
        
        # Style pour les totaux
        self.total_style = ParagraphStyle(
            'TotalStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=14,
            fontName='Helvetica-Bold',
        )
        
        # Nombre maximal d'éléments par page (ajuster selon besoin)
        self.items_per_page = 15
    
    def _format_currency(self, amount):
        """
        Formate un montant en devise (Euro).
        """
        if amount is None:
            return "0,00 €"
        
        if isinstance(amount, Decimal):
            amount = float(amount)
        
        return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")
    
    def _format_percentage(self, percentage):
        """
        Formate un pourcentage.
        """
        if percentage is None:
            return "0,00 %"
        
        if isinstance(percentage, Decimal):
            percentage = float(percentage)
        
        return f"{percentage:.2f} %".replace(".", ",")
    
    def _build_header(self, canvas, doc):
        """
        Dessine l'en-tête sur chaque page.
        """
        canvas.saveState()
        
        # Logo de l'entreprise (si disponible)
        # logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
        # if os.path.exists(logo_path):
        #     canvas.drawImage(logo_path, 1*cm, self.height - 3*cm, width=5*cm, height=2*cm)
        
        # Nom de l'entreprise et informations
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawString(1*cm, self.height - 2*cm, "ENTREPRISE BTP")
        
        canvas.setFont('Helvetica', 10)
        canvas.drawString(1*cm, self.height - 2.5*cm, "123 rue de la Construction")
        canvas.drawString(1*cm, self.height - 3*cm, "75000 PARIS")
        canvas.drawString(1*cm, self.height - 3.5*cm, "Tél: 01 23 45 67 89")
        canvas.drawString(1*cm, self.height - 4*cm, "Email: contact@entreprise-btp.fr")
        
        # Numéro de facture et date
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(self.width - 7*cm, self.height - 2*cm, f"FACTURE N° {self.invoice.number}")
        
        canvas.setFont('Helvetica', 10)
        canvas.drawString(self.width - 7*cm, self.height - 2.5*cm, f"Date: {self.invoice.issue_date.strftime('%d/%m/%Y')}")
        if self.invoice.due_date:
            canvas.drawString(self.width - 7*cm, self.height - 3*cm, f"Échéance: {self.invoice.due_date.strftime('%d/%m/%Y')}")
        
        # Numéro de page
        canvas.setFont('Helvetica', 9)
        page_num = f"Page {doc.page} / {doc.pageCount}"
        canvas.drawString(self.width - 2*cm, 1*cm, page_num)
        
        canvas.restoreState()
    
    def _build_footer(self, canvas, doc):
        """
        Dessine le pied de page sur chaque page.
        """
        canvas.saveState()
        
        # Mentions légales
        canvas.setFont('Helvetica', 8)
        canvas.drawString(1*cm, 1.5*cm, "SIRET: 123 456 789 00010 - TVA: FR12 345 678 90")
        canvas.drawString(1*cm, 1.2*cm, "Conditions de paiement: " + (self.invoice.terms_and_conditions or "Voir conditions générales"))
        
        canvas.restoreState()
    
    def _add_invoice_info(self, elements):
        """
        Ajoute les informations générales de la facture.
        """
        elements.append(Spacer(1, 4*cm))  # Espace pour l'en-tête
        
        # Client et projet
        client_info = [
            [Paragraph("<b>CLIENT</b>", self.section_style)],
            [Paragraph(f"<b>{self.invoice.client_name}</b>", self.normal_style)],
        ]
        
        if self.invoice.client_address:
            for line in self.invoice.client_address.split("\n"):
                client_info.append([Paragraph(line, self.normal_style)])
        
        client_table = Table(client_info, colWidths=[8*cm])
        client_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        # Projet si disponible
        if self.invoice.project_name:
            project_info = [
                [Paragraph("<b>PROJET</b>", self.section_style)],
                [Paragraph(f"<b>{self.invoice.project_name}</b>", self.normal_style)],
            ]
            
            if self.invoice.project_address:
                for line in self.invoice.project_address.split("\n"):
                    project_info.append([Paragraph(line, self.normal_style)])
            
            if self.invoice.project_reference:
                project_info.append([Paragraph(f"Référence: {self.invoice.project_reference}", self.normal_style)])
            
            project_table = Table(project_info, colWidths=[8*cm])
            project_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            
            # Mettre client et projet côte à côte
            info_table = Table([[client_table, project_table]], colWidths=[8*cm, 8*cm])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(info_table)
        else:
            elements.append(client_table)
        
        elements.append(Spacer(1, 1*cm))
    
    def _add_items_table(self, elements):
        """
        Ajoute le tableau des éléments de facture avec pagination.
        """
        # Entête du tableau
        table_header = [
            [
                Paragraph("<b>Désignation</b>", self.normal_style),
                Paragraph("<b>Quantité</b>", self.normal_style),
                Paragraph("<b>Prix unitaire</b>", self.normal_style),
                Paragraph("<b>TVA</b>", self.normal_style),
                Paragraph("<b>Total HT</b>", self.normal_style),
            ]
        ]
        
        # Largeurs des colonnes
        col_widths = [9*cm, 2*cm, 3*cm, 2*cm, 3*cm]
        
        # Récupérer tous les éléments (hors chapitres/sections pour simplifier)
        items = self.invoice.items.exclude(type__in=["chapter", "section"]).order_by('position')
        
        # Diviser les éléments en pages si nécessaire
        total_items = items.count()
        
        # Si peu d'éléments, tout sur une page
        if total_items <= self.items_per_page:
            data = table_header.copy()
            
            for item in items:
                data.append([
                    Paragraph(f"{item.designation}<br/>{item.description or ''}", self.normal_style),
                    Paragraph(f"{item.quantity} {item.unit or ''}", self.normal_style),
                    Paragraph(self._format_currency(item.unit_price), self.normal_style),
                    Paragraph(f"{item.vat_rate}%", self.normal_style),
                    Paragraph(self._format_currency(item.total_ht), self.normal_style),
                ])
            
            # Créer le tableau
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ]))
            
            elements.append(table)
        else:
            # Diviser en plusieurs pages
            for i in range(0, total_items, self.items_per_page):
                page_items = items[i:i+self.items_per_page]
                
                data = table_header.copy()
                
                for item in page_items:
                    data.append([
                        Paragraph(f"{item.designation}<br/>{item.description or ''}", self.normal_style),
                        Paragraph(f"{item.quantity} {item.unit or ''}", self.normal_style),
                        Paragraph(self._format_currency(item.unit_price), self.normal_style),
                        Paragraph(f"{item.vat_rate}%", self.normal_style),
                        Paragraph(self._format_currency(item.total_ht), self.normal_style),
                    ])
                
                # Créer le tableau
                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ]))
                
                elements.append(table)
                
                # Ajouter un saut de page si ce n'est pas la dernière page
                if i + self.items_per_page < total_items:
                    elements.append(PageBreak())
    
    def _add_totals(self, elements):
        """
        Ajoute les totaux de la facture.
        """
        elements.append(Spacer(1, 0.5*cm))
        
        # Tableau des totaux
        data = [
            ["Total HT:", self._format_currency(self.invoice.total_ht)],
            ["Total TVA:", self._format_currency(self.invoice.total_vat)],
            ["Total TTC:", self._format_currency(self.invoice.total_ttc)],
        ]
        
        # Ajouter les informations de paiement si applicable
        if self.invoice.paid_amount > 0:
            data.append(["Déjà payé:", self._format_currency(self.invoice.paid_amount)])
            data.append(["Reste à payer:", self._format_currency(self.invoice.remaining_amount)])
        
        # Créer le tableau des totaux
        totals_table = Table(data, colWidths=[4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (1, -1), 12),
            ('LINEBELOW', (0, -2), (1, -2), 0.5, colors.black),
        ]))
        
        # Aligner à droite
        totals_wrapper = Table([[totals_table]], colWidths=[self.width - 2*cm])
        totals_wrapper.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
        ]))
        
        elements.append(totals_wrapper)
    
    def _add_notes(self, elements):
        """
        Ajoute les notes et conditions de la facture.
        """
        elements.append(Spacer(1, 1*cm))
        
        # Notes si disponibles
        if self.invoice.notes:
            elements.append(Paragraph("<b>Notes:</b>", self.section_style))
            elements.append(Paragraph(self.invoice.notes, self.normal_style))
            elements.append(Spacer(1, 0.5*cm))
        
        # Conditions de paiement
        if self.invoice.terms_and_conditions:
            elements.append(Paragraph("<b>Conditions de paiement:</b>", self.section_style))
            elements.append(Paragraph(self.invoice.terms_and_conditions, self.normal_style))
    
    def _add_payments_info(self, elements):
        """
        Ajoute les informations sur les paiements déjà effectués.
        """
        payments = self.invoice.payments.all()
        
        if payments:
            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph("<b>Paiements enregistrés:</b>", self.section_style))
            
            # Entête du tableau
            data = [
                [
                    Paragraph("<b>Date</b>", self.normal_style),
                    Paragraph("<b>Méthode</b>", self.normal_style),
                    Paragraph("<b>Référence</b>", self.normal_style),
                    Paragraph("<b>Montant</b>", self.normal_style),
                ]
            ]
            
            # Ajouter chaque paiement
            for payment in payments:
                data.append([
                    payment.date.strftime("%d/%m/%Y"),
                    payment.get_method_display(),
                    payment.reference or "",
                    self._format_currency(payment.amount)
                ])
            
            # Créer le tableau
            table = Table(data, colWidths=[3*cm, 4*cm, 6*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ]))
            
            elements.append(table)
    
    def generate_pdf(self):
        """
        Génère le PDF de la facture.
        """
        # Créer le document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        # Liste des éléments à ajouter au document
        elements = []
        
        # Ajouter les différentes sections
        self._add_invoice_info(elements)
        self._add_items_table(elements)
        
        # Les totaux et notes vont sur la dernière page
        self._add_totals(elements)
        self._add_payments_info(elements)
        self._add_notes(elements)
        
        # Construire le document
        doc.build(
            elements,
            onFirstPage=self._build_header,
            onLaterPages=self._build_header,
            canvasmaker=NumberedCanvas
        )
        
        # Récupérer le contenu du PDF
        pdf_value = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_value


class NumberedCanvas(canvas.Canvas):
    """
    Canvas personnalisé pour numéroter les pages.
    """
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.page = 0
        self.pageCount = 0

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        self.page += 1

    def save(self):
        """
        Ajoute le numéro de page à chaque page du document.
        """
        self.pageCount = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self) 