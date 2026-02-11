"""
PDF Report Service za generisanje Izveštaja o rezultatima kvizova
"""
import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import logging

logger = logging.getLogger(__name__)


class PDFReportService:
    """Servis za kreiranje PDF Izveštaja o rezultatima kvizova"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Kreira custom stilove za PDF"""
        # Naslov Izveštaja
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Podnaslov
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Sekcija naslova
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Info tekst
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#424242'),
            spaceAfter=6
        ))
        
        # Footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#757575'),
            alignment=TA_CENTER
        ))
    
    def _add_header_footer(self, canvas_obj, doc):
        """Dodaje header i footer na stranicu"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#1a237e'))
        canvas_obj.drawString(2*cm, self.page_height - 1.5*cm, "QuizPlatform")
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#757575'))
        footer_text = f"Stranica {doc.page} | Generisano: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        canvas_obj.drawRightString(
            self.page_width - 2*cm,
            1.5*cm,
            footer_text
        )
        
        # Linija ispod headera
        canvas_obj.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(2*cm, self.page_height - 2*cm, self.page_width - 2*cm, self.page_height - 2*cm)
        
        canvas_obj.restoreState()
    
    def generate_quiz_report(self, quiz_data, results_data):
        """
        Generise PDF Izveštaj za kviz
        
        Args:
            quiz_data: Dict sa podacima o kvizu (title, author, questions, etc.)
            results_data: Dict sa rezultatima (ukupno, prosek, lista rezultata)
            
        Returns:
            BytesIO objekat sa PDF sadržajem
        """
        logger.info(f"Generisanje PDF Izveštaja za kviz: {quiz_data.get('title', 'N/A')}")
        
        # Kreiraj BytesIO buffer
        buffer = io.BytesIO()
        
        # Kreiraj PDF dokument
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2.5*cm
        )
        
        # Lista elemenata dokumenta
        story = []
        
        # ===== NASLOVNICA =====
        story.append(Spacer(1, 2*cm))
        
        # Glavni naslov
        title = Paragraph(
            "IZVEŠTAJ O REZULTATIMA KVIZA",
            self.styles['ReportTitle']
        )
        story.append(title)
        
        # Naziv kviza
        quiz_title = Paragraph(
            f"<b>{quiz_data.get('title', 'Nepoznat kviz')}</b>",
            self.styles['ReportSubtitle']
        )
        story.append(quiz_title)
        
        story.append(Spacer(1, 1*cm))
        
        # Info tabela
        info_data = [
            ['Autor kviza:', quiz_data.get('author_name', 'N/A')],
            ['Broj pitanja:', str(quiz_data.get('question_count', 0))],
            ['Trajanje:', f"{quiz_data.get('duration_seconds', 0)} sekundi"],
            ['Datum kreiranja:', quiz_data.get('created_at', 'N/A')[:10] if quiz_data.get('created_at') else 'N/A'],
            ['Datum Izveštaja:', datetime.now().strftime('%d.%m.%Y %H:%M')]
        ]
        
        info_table = Table(info_data, colWidths=[5*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        
        story.append(PageBreak())
        
        # ===== STATISTIKA REZULTATA =====
        story.append(Paragraph("STATISTIKA REZULTATA", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.5*cm))
        
        # Statistika podaci
        total_attempts = results_data.get('total_attempts', 0)
        avg_score = results_data.get('average_score', 0)
        avg_percentage = results_data.get('average_percentage', 0)
        max_score = results_data.get('max_score', 0)
        min_score = results_data.get('min_score', 0)
        max_possible = results_data.get('max_possible_score', 0)
        
        stats_data = [
            ['Ukupno pokušaja:', str(total_attempts)],
            ['Prosječan rezultat:', f"{avg_score:.1f} / {max_possible} ({avg_percentage:.1f}%)"],
            ['Najbolji rezultat:', f"{max_score} / {max_possible}"],
            ['Najlošiji rezultat:', f"{min_score} / {max_possible}"],
        ]
        
        stats_table = Table(stats_data, colWidths=[7*cm, 8*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#212121')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdbdbd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(stats_table)
        
        story.append(Spacer(1, 1*cm))
        
        # ===== LISTA REZULTATA =====
        if total_attempts > 0:
            story.append(Paragraph("DETALJNA LISTA REZULTATA", self.styles['SectionTitle']))
            story.append(Spacer(1, 0.3*cm))
            
            # Header tabele
            results_data_list = [
                ['#', 'Korisnik', 'Rezultat', 'Procenat', 'Vrijeme', 'Datum']
            ]
            
            # Dodaj rezultate
            results = results_data.get('results', [])
            for idx, result in enumerate(results[:50], 1):  # Limit na 50 rezultata
                user_name = result.get('user_name', 'N/A')
                score = result.get('score', 0)
                percentage = result.get('percentage', 0)
                time_taken = result.get('time_taken', 0)
                submitted_at = result.get('submitted_at', '')
                
                # Formatiranje datuma
                if submitted_at:
                    try:
                        dt = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                        date_str = dt.strftime('%d.%m.%Y')
                        time_str = dt.strftime('%H:%M')
                    except:
                        date_str = submitted_at[:10]
                        time_str = ''
                else:
                    date_str = 'N/A'
                    time_str = ''
                
                results_data_list.append([
                    str(idx),
                    user_name[:30],  # Limit imena na 30 karaktera
                    f"{score}/{max_possible}",
                    f"{percentage:.1f}%",
                    f"{time_taken}s",
                    f"{date_str}\n{time_str}"
                ])
            
            # Kreiranje tabele
            results_table = Table(
                results_data_list,
                colWidths=[1*cm, 5*cm, 2.5*cm, 2.5*cm, 2*cm, 3*cm]
            )
            
            # Stilizovanje tabele
            table_style = [
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Body
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Korisnik
                ('ALIGN', (2, 1), (-1, -1), 'CENTER'), # Ostalo
                
                # Gridlines
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
            
            # Alternativne boje redova
            for i in range(1, len(results_data_list)):
                if i % 2 == 0:
                    table_style.append(
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5'))
                    )
                else:
                    table_style.append(
                        ('BACKGROUND', (0, i), (-1, i), colors.white)
                    )
            
            results_table.setStyle(TableStyle(table_style))
            story.append(results_table)
            
            # Napomena ako ima više od 50 rezultata
            if len(results) > 50:
                story.append(Spacer(1, 0.5*cm))
                note = Paragraph(
                    f"<i>Napomena: Prikazano je prvih 50 od ukupno {len(results)} rezultata.</i>",
                    self.styles['InfoText']
                )
                story.append(note)
        else:
            story.append(Paragraph(
                "Još uvijek nema rezultata za ovaj kviz.",
                self.styles['InfoText']
            ))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        # Vrati BytesIO buffer
        buffer.seek(0)
        logger.info("PDF Izveštaj uspešno generisan")
        return buffer
    
    def save_report_to_file(self, buffer, filename):
        """Čuva PDF iz buffer-a u fajl"""
        try:
            filepath = os.path.join('reports', filename)
            os.makedirs('reports', exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            
            logger.info(f"PDF Izveštaj sačuvan: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Greška pri čuvanju PDF-a: {e}")
            return None


# Globalna instanca servisa
pdf_service = PDFReportService()
