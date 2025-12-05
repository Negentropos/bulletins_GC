#Liste les différents styles utilisés dans la génération des bulletins
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import TableStyle
from reportlab.lib import colors
from . import pdf_taille

#Couleur de la charte graphique

COULEUR_EN_TETE_TABLEAU_APPRECIATION = colors.skyblue
COULEUR_EN_TETE_TABLEAU_STAGEETPROJET = colors.azure
COULEUR_EN_TETE_TABLEAU_AVIS = colors.crimson
COULEUR_GRILLE_APPRECIATION = colors.lightsteelblue


def caseDiscipline(taillePolice,font):
    return ParagraphStyle('case_discipline',leading=taillePolice * 1.2,alignment=0,fontName=font)

def caseDescriptif(taillePolice,font):
    return ParagraphStyle('case_descriptif',leading=taillePolice * 1.2,alignment=0,fontName=font)

def caseCommentaire(taillePolice,font):
    return ParagraphStyle('case_descriptif',leading=taillePolice * 1.2,alignment=0,fontName=font)

def ligneEnTete(taille,font,couleurAppreciation):
    return TableStyle([
        #('BOX',(0,0),(-1,-1),1,colors.black),
        ('LINEBELOW',(0,0),(-1,0),0.75,colors.HexColor(val=couleurAppreciation)),
        ('LINEBEFORE', (1, 0), (-1, 0), 0.75, colors.HexColor(val=couleurAppreciation)),
        ('FONTNAME', (0, 0), (-1, -1), font + '-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), taille*1.2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        #('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ])

def tableauAppreciationTotaleAvecEvaluation(num,couleurAppreciation) :
    style = TableStyle([
        #Suppression du padding dans le tableau d'évaluation
        ('LEFTPADDING', (2, 0), (-1, -1), 0),
        ('RIGHTPADDING', (2, 0), (-1, -1), 0),
        ('TOPPADDING', (1, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (1, 0), (-1, -1), 1),
        # Suppression du padding dans le tableau d'évaluation
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
    if num % 2 ==0:
        style.add('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(val=couleurAppreciation))
        style.add('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white)
    else :
        style.add('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor(val=couleurAppreciation))
    return style

#Style de la 3e colonne d'une appreciation
def tableauEvaluation(num,couleur):
    style= TableStyle([
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('TOPPADDING',(0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 2), (0, -1), 0),
        ('LEFTPADDING', (0, 2), (0, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ])
    if num % 2 == 0:
        style.add('INNERGRID', (0, 0), (-1, -1), 0.25, colors.white)
    else :
        style.add('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor(val=couleur))

    return style


#Définit le style de la ligne Attitude, Résultat etc.
def tableauLigneEvaluation(taille,font):
    return TableStyle([
        #('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE',(0,0),(-1,-1),taille),
        ('FONTNAME', (0, 0), (5, 0),font),
        ('FONTNAME', (1, 0), (1, 0), font + '-Bold'),
        ('FONTNAME', (3, 0), (3, 0), font + '-Bold'),
        ('FONTNAME', (5, 0), (5, 0), font + '-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',(0, 0), (-1, -1), 1),
        ('RIGHTPADDING',(0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        #Centrer les notes
        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
    ])

ligneTableauCompetence= TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (0, 0), 6),
    ('LEFTPADDING', (1, 0), (1, 0), 0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    #('BOX', (0, 0), (-1, -1), 0.25, colors.black),
    #('INNERGRID', (0, 0), (-1, -1), 0.15, colors.black),
    ])


def competenceEvaluation(taille,font):
    return ParagraphStyle('competenceEvaluation',leading=taille * 1.2,alignment=2,fontName=font,rightIndent=5)

def competenceIntitule(taille,font):
    return ParagraphStyle('competenceIntitule',leading=taille * 1.2,alignment=0,fontName=font)

def tableauAvisCollege(taille,font,couleur):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(val=couleur)),
        ('FONTSIZE',(0,0),(0,0),taille*1.2),
        ('FONTNAME', (0, 0), (0, 0), font + "-Bold"),
        #('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(val=couleur)),
        ('INNERGRID', (0, 0), (-1,-1), 0.25, colors.HexColor(val=couleur)),
        #('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ])

def avisCollege(taille,font):
    return ParagraphStyle('avisCollege',leading=taille * 1.5,alignment=0,fontName=font)

def retardsAbsences(taillePolice,font):
    return ParagraphStyle('retards_absences',
                                   fontName=font,
                                   fontSize=taillePolice,
                                   leading=taillePolice*1.5,
                                   alignment=0,
                                   )

def tableauStagesProjets(taille,font,couleur):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(val=couleur)),
        ('FONTSIZE',(0,0),(0,0),taille*1.2),
        ('FONTNAME', (0, 0), (0, 0), font + "-Bold"),
        #('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(val=couleur)),
        ('INNERGRID', (0, 0), (-1,-1), 0.25, colors.HexColor(val=couleur)),
        #('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ])

def tableauAbsenceEtVisa(taille,font):
    return TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),taille*1.2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',(0,1),(-1,1),'CENTER')

    ])

def stage(taillePolice,font):
    return ParagraphStyle('stage',
                                   fontName=font,
                                   fontSize=taillePolice,
                                   leading=taillePolice*1.5,
                                   alignment=0,
                                   )

def projet(taillePolice,font):
    return ParagraphStyle('stage',
                                   fontName=font,
                                   fontSize=taillePolice,
                                   leading=taillePolice*1.5,
                                   alignment=0,
                                   )

def tableauNoticeBulletin(taillePolice,font,couleur):
    return TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('ALIGN',(0,0),(1,0),'CENTER'),
        #('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(val=couleur)),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor(val=couleur)),
        #('ROUNDEDCORNERS',[5,5,5,5]),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(val=couleur)),
    ])

def noticeBulletin(taillePolice,font):
    return ParagraphStyle('notice_bulletin',
                                   fontName=font,
                                   fontSize=taillePolice,
                                   leading=taillePolice*1.3,
                                   alignment=0,
                                   )

def noticeTitreBulletin(taillePolice,font):
    return ParagraphStyle('notice_titre_bulletin',
                                   fontName=font + '-Bold',
                                   fontSize=taillePolice*1.4,
                                   leading=taillePolice*1.8,
                                   alignment=1,
                                   )