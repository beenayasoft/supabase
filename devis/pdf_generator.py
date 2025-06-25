from io import BytesIO
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import KeepTogether
from django.conf import settings
from decimal import Decimal

class DevisPDFGenerator:
    """
    Classe pour générer un PDF à partir d'un devis.
    """
    def __init__(self, devis, show_costs=False):
        """
        Initialisation avec un devis et les paramètres de visualisation.
        
        Args:
            devis: Instance du modèle Devis
            show_costs: Booléen indiquant si les coûts doivent être inclus dans le PDF
        """
        self.devis = devis
        self.show_costs = show_costs
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
    
    def _build_header(self, doc, canvas, document):
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
        
        # Numéro de page
        canvas.setFont('Helvetica', 9)
        # Estimation du nombre total de pages (on divise par 40 lignes par page en moyenne)
        total_pages = max(1, (len(document) // 40) + 1)
        page_num = f"Page {doc}/{total_pages}"
        canvas.drawString(self.width - 2*cm, 1*cm, page_num)
        
        canvas.restoreState()
    
    def _build_footer(self, canvas, document):
        """
        Dessine le pied de page sur chaque page.
        """
        canvas.saveState()
        
        # Mentions légales
        canvas.setFont('Helvetica', 8)
        canvas.drawString(1*cm, 1.5*cm, "SIRET: 123 456 789 00010 - TVA: FR12 345 678 90")
        canvas.drawString(1*cm, 1.2*cm, "Conditions de paiement: " + (self.devis.conditions_paiement or "Voir conditions générales"))
        
        canvas.restoreState()
    
    def _add_devis_info(self, elements):
        """
        Ajoute les informations générales du devis.
        """
        elements.append(Spacer(1, 1*cm))
        
        # Titre du document
        elements.append(Paragraph(f"DEVIS N° {self.devis.numero}", self.title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Date et validité
        date_info = [
            ["Date d'émission:", self.devis.date_creation.strftime("%d/%m/%Y")],
            ["Date de validité:", self.devis.date_validite.strftime("%d/%m/%Y") if self.devis.date_validite else "Non spécifiée"]
        ]
        date_table = Table(date_info, colWidths=[4*cm, 4*cm])
        date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(date_table)
        
        elements.append(Spacer(1, 1*cm))
    
    def _add_client_info(self, elements):
        """
        Ajoute les informations du client.
        """
        elements.append(Paragraph("CLIENT", self.section_style))
        
        client = self.devis.client
        
        # Récupération du contact principal pour devis s'il existe
        contact_principal = None
        contacts = client.contacts.filter(contact_principal_devis=True)
        if contacts.exists():
            contact_principal = contacts.first()
        
        # Ajout des adresses du client
        adresses = client.adresses.all()
        if adresses.exists():
            adresse = adresses.first()  # On prend la première adresse (ou adresse de facturation si disponible)
            adresse_facturation = client.adresses.filter(facturation=True).first()
            if adresse_facturation:
                adresse = adresse_facturation
            
            client_info = [
                ["Nom:", client.nom],
                ["Adresse:", adresse.libelle or adresse.rue],
                ["Ville:", f"{adresse.code_postal} {adresse.ville}"],
            ]
            
            # Ajout des informations de contact si disponibles
            if contact_principal:
                if contact_principal.telephone:
                    client_info.append(["Téléphone:", contact_principal.telephone])
                if contact_principal.email:
                    client_info.append(["Email:", contact_principal.email])
                if contact_principal.fonction:
                    client_info.append(["Contact:", f"{contact_principal.prenom} {contact_principal.nom} ({contact_principal.fonction})"])
                elif contact_principal.nom:
                    client_info.append(["Contact:", f"{contact_principal.prenom} {contact_principal.nom}"])
        else:
            # Si pas d'adresse, on affiche juste les infos de base
            client_info = [
                ["Nom:", client.nom],
            ]
            
            # Ajout des informations de contact si disponibles
            if contact_principal:
                if contact_principal.telephone:
                    client_info.append(["Téléphone:", contact_principal.telephone])
                if contact_principal.email:
                    client_info.append(["Email:", contact_principal.email])
                if contact_principal.fonction:
                    client_info.append(["Contact:", f"{contact_principal.prenom} {contact_principal.nom} ({contact_principal.fonction})"])
                elif contact_principal.nom:
                    client_info.append(["Contact:", f"{contact_principal.prenom} {contact_principal.nom}"])
        
        # Ajout du SIRET si c'est une entreprise
        if client.type == 'entreprise' and client.siret:
            client_info.append(["SIRET:", client.siret])
        if client.tva:
            client_info.append(["TVA:", client.tva])
        
        client_table = Table(client_info, colWidths=[3*cm, 10*cm])
        client_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(client_table)
        
        elements.append(Spacer(1, 1*cm))
    
    def _add_objet(self, elements):
        """
        Ajoute l'objet du devis.
        """
        elements.append(Paragraph("OBJET DU DEVIS", self.section_style))
        elements.append(Paragraph(self.devis.objet, self.normal_style))
        
        # Ajout du commentaire s'il existe
        if self.devis.commentaire:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("Commentaires:", ParagraphStyle(
                'CommentTitle',
                parent=self.styles['Normal'],
                fontName='Helvetica-Bold'
            )))
            elements.append(Paragraph(self.devis.commentaire, self.normal_style))
        
        elements.append(Spacer(1, 1*cm))
    
    def _add_lots_et_lignes(self, elements):
        """
        Ajoute les lots et leurs lignes.
        """
        elements.append(Paragraph("PRESTATIONS", self.section_style))
        
        # Parcourir chaque lot
        for lot in self.devis.lots.all().order_by('ordre'):
            # Titre du lot
            elements.append(Paragraph(lot.nom, ParagraphStyle(
                'LotTitle',
                parent=self.styles['Heading4'],
                fontSize=11,
                leading=13,
                spaceBefore=6,
            )))
            
            # Description du lot s'il y en a une
            if lot.description:
                elements.append(Paragraph(lot.description, self.normal_style))
            
            # Entêtes du tableau des lignes
            if self.show_costs:
                headers = ["Description", "Qté", "Unité", "P.U. HT", "Déboursé", "Marge", "Total HT"]
                col_widths = [8*cm, 1.2*cm, 1.5*cm, 2*cm, 2*cm, 1.8*cm, 2.5*cm]
            else:
                headers = ["Description", "Qté", "Unité", "P.U. HT", "Total HT"]
                col_widths = [10*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3.5*cm]
            
            # Données du tableau
            data = [headers]
            
            # Ajouter chaque ligne
            for ligne in lot.lignes.all().order_by('ordre'):
                if self.show_costs:
                    row = [
                        ligne.description,
                        f"{ligne.quantite:,.2f}".replace(",", " ").replace(".", ","),
                        ligne.unite,
                        self._format_currency(ligne.prix_unitaire),
                        self._format_currency(ligne.debourse),
                        self._format_percentage(ligne.marge),
                        self._format_currency(ligne.total_ht)
                    ]
                else:
                    row = [
                        ligne.description,
                        f"{ligne.quantite:,.2f}".replace(",", " ").replace(".", ","),
                        ligne.unite,
                        self._format_currency(ligne.prix_unitaire),
                        self._format_currency(ligne.total_ht)
                    ]
                data.append(row)
            
            # Ajouter le sous-total du lot
            if self.show_costs:
                subtotal_row = [
                    "Sous-total",
                    "",
                    "",
                    "",
                    self._format_currency(lot.total_debourse),
                    self._format_percentage(lot.marge),
                    self._format_currency(lot.total_ht)
                ]
            else:
                subtotal_row = [
                    "Sous-total",
                    "",
                    "",
                    "",
                    self._format_currency(lot.total_ht)
                ]
            data.append(subtotal_row)
            
            # Créer et styliser le tableau
            table = Table(data, colWidths=col_widths)
            
            # Style de base
            style = [
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Entête en gras
                ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Sous-total en gras
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Fond gris pour l'entête
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Grille complète
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Colonne description alignée à gauche
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Autres colonnes alignées à droite
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alignement vertical au milieu
            ]
            
            table.setStyle(TableStyle(style))
            
            # Encapsuler le tableau pour qu'il ne soit pas coupé entre deux pages
            lot_content = KeepTogether([
                Spacer(1, 3*mm),
                table,
                Spacer(1, 5*mm)
            ])
            elements.append(lot_content)
        
        elements.append(Spacer(1, 0.5*cm))
    
    def _add_total_global(self, elements):
        """
        Ajoute le tableau des totaux globaux.
        """
        elements.append(Paragraph("RÉCAPITULATIF", self.section_style))
        
        # Créer les lignes du tableau des totaux
        if self.show_costs:
            total_data = [
                ["Total déboursé HT", self._format_currency(self.devis.total_debourse)],
                ["Marge moyenne", self._format_percentage(self.devis.marge_totale)],
                ["TOTAL HT", self._format_currency(self.devis.total_ht)],
                ["TVA (20%)", self._format_currency(self.devis.total_ht * Decimal('0.20'))],
                ["TOTAL TTC", self._format_currency(self.devis.total_ht * Decimal('1.20'))]
            ]
        else:
            total_data = [
                ["TOTAL HT", self._format_currency(self.devis.total_ht)],
                ["TVA (20%)", self._format_currency(self.devis.total_ht * Decimal('0.20'))],
                ["TOTAL TTC", self._format_currency(self.devis.total_ht * Decimal('1.20'))]
            ]
        
        # Créer le tableau
        total_table = Table(total_data, colWidths=[10*cm, 5*cm])
        
        # Styliser le tableau
        style = [
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (1, -1), 12),  # Grand total en gros caractères
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),  # Ligne au-dessus du total TTC
            ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey),  # Fond gris pour le total TTC
        ]
        total_table.setStyle(TableStyle(style))
        
        elements.append(total_table)
        
        elements.append(Spacer(1, 1*cm))
    
    def _add_conditions(self, elements):
        """
        Ajoute les conditions de paiement et mentions légales.
        """
        elements.append(Paragraph("CONDITIONS DE PAIEMENT", self.section_style))
        
        conditions = self.devis.conditions_paiement if self.devis.conditions_paiement else "Paiement à 30 jours à compter de la date de facturation."
        elements.append(Paragraph(conditions, self.normal_style))
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("Ce devis est valable jusqu'au " + 
            (self.devis.date_validite.strftime("%d/%m/%Y") if self.devis.date_validite else "..."), 
            self.normal_style))
        
        elements.append(Spacer(1, 1*cm))
        
        # Signatures
        signature_data = [
            ["Fait à ............, le ............", "BON POUR ACCORD"],
            ["Cachet et signature:", "Nom, date et signature:"],
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""],
        ]
        signature_table = Table(signature_data, colWidths=[9*cm, 9*cm])
        signature_table.setStyle(TableStyle([
            ('FONT', (0, 0), (1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(signature_table)
    
    def generate_pdf(self):
        """
        Génère le PDF et retourne le buffer.
        """
        # Création du document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=5*cm,  # Marge haute pour l'en-tête
            bottomMargin=2*cm  # Marge basse pour le pied de page
        )
        
        # Liste des éléments du document
        elements = []
        
        # Ajout des sections
        self._add_devis_info(elements)
        self._add_client_info(elements)
        self._add_objet(elements)
        self._add_lots_et_lignes(elements)
        self._add_total_global(elements)
        self._add_conditions(elements)
        
        # Création du document avec en-têtes et pieds de page
        # Nous combinons l'en-tête et le pied de page dans les mêmes fonctions
        def add_page_elements(canvas, doc_obj, page_num):
            self._build_header(page_num, canvas, elements)
            self._build_footer(canvas, doc_obj)
        
        doc.build(
            elements,
            onFirstPage=lambda canvas, doc_obj: add_page_elements(canvas, doc_obj, 1),
            onLaterPages=lambda canvas, doc_obj: add_page_elements(canvas, doc_obj, doc_obj.page)
        )
        
        # Retourner le buffer
        self.buffer.seek(0)
        return self.buffer 