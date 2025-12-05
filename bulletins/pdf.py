#Fonctionnalités utilisées pour la génération des pdf
#Création d'une classe qui hérite de Canva avec des méthodes supplémentaires
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Frame, Paragraph,Image,Table,Spacer
from reportlab.platypus.flowables import TopPadder
from .pdfData import pdf_styles,pdf_donnees,pdf_taille
from django.conf import settings



def versionProvisoire(canvas):
    for ord in range (2,24,7):
        canvas.drawImage(settings.BASE_DIR.joinpath('static/images/version_provisoire.png'), width=4.9 * cm,height=5.08 * cm, x=3 * cm, y=ord * cm, mask='auto')

        canvas.drawImage(settings.BASE_DIR.joinpath('static/images/version_provisoire.png'), width=4.9 * cm, height=5.08 * cm,x=15 * cm, y=ord * cm, mask='auto')

def enTete(eleve, trimestre,canvas,dictParamBulletins):
    frameInfosEcole = Frame(x1=1 * cm, y1=24.87 * cm, width=5 * cm, height=4.43 * cm, showBoundary=0,
                                 leftPadding=0,
                                 topPadding=4, rightPadding=0, bottomPadding=0)
    frameInfosEleve = Frame(x1=6 * cm, y1=25.40 * cm, width=14 * cm, height=4.43 * cm, showBoundary=0,
                                 leftPadding=10, topPadding=0, rightPadding=0, bottomPadding=0)
    #infosEcole = [Image(dictParamBulletins['logoFile'], width=5 * cm, height=3.43 * cm)]
    infosEcole = [Image(settings.BASE_DIR.joinpath('static/images/logobull.jpg'), width=5 * cm, height=3.43 * cm)]
    styleInfosEleve = ParagraphStyle('infos_Eleve',
                                     #font=dictParamBulletins['font'],
                                     leading=24,
                                     alignment=0,
                                     )

    dateNaissance=str(eleve.dateNaissance).split('-')
    if eleve.genre == 'F':
        dateNaissanceBulletin = f"née le {dateNaissance[2]}/{dateNaissance[1]}/{dateNaissance[0]}"
    else:
        dateNaissanceBulletin = f"né le {dateNaissance[2]}/{dateNaissance[1]}/{dateNaissance[0]}"
    infosEleve = [TopPadder(Paragraph(f'''
                <font size=10>Bulletin scolaire - {trimestre.intitule} {trimestre.annee.intitule}</font> <br />
                <font size = 17>{eleve.prenom} {eleve.nom} </font><br />
                <font size = 11>{dateNaissanceBulletin} </font><br />
                <font size = 13>{eleve.show_classe()}e Classe</font>
                ''',
                                      styleInfosEleve))]

    frameInfosEcole.addFromList(infosEcole, canvas)
    frameInfosEleve.addFromList(infosEleve, canvas)

def ligneEnTeteAppreciation(story,dictParamBulletins):
    # Largeur des colonnes d'un tableau appreciation
    largeur_discipline = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurIntitule'] / 100
    largeur_descriptif = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurDescriptif'] / 100
    largeur_evaluation = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurEvaluation'] / 100
    TAILLE_POLICE = dictParamBulletins['fontSize']
    font=dictParamBulletins['font']
    couleurAppreciation=dictParamBulletins['couleurAppreciation']
    contenuEnTete = [["Enseignement", "Programme", "Évaluation"]]
    ligneEnTete = Table(contenuEnTete, colWidths=[largeur_discipline,
                                                                         largeur_descriptif, largeur_evaluation],
                                      style=pdf_styles.ligneEnTete(TAILLE_POLICE,font,couleurAppreciation))
    story.append(ligneEnTete)

def creerBulletinAppreciations(appreciation,competences,canvas,dictParamBulletins,story,bulletinUtilisationCompetence,num):

    # définit une variable qui active ou non la ligne évaluation
    if (appreciation.note == '' or appreciation.note==None) and (appreciation.attitude == '' or appreciation.attitude==None) and (appreciation.engagement == '' or appreciation.engagement == None) and (appreciation.resultat == '' or appreciation.resultat == None) :
        evaluation_active = False
    else:
        evaluation_active = True

    # Structure d'une ligne d'appréciation :
    # Une ligne divisée en 3 cases : Discipline (paragraphe), Descriptif (paragraphe), Evaluation(Tableau)
    # Le tableau Evaluation se divise ensuite en plusieurs lignes : Commentaire, Valeurs, Compétences
    # La case Valeurs - doit se diviser en plusieurs colonnes, la case commentaire en 2 colonnes

    # Largeur des colonnes d'un tableau appreciation
    largeur_discipline = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurIntitule'] / 100
    largeur_descriptif = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurDescriptif'] / 100
    largeur_evaluation = dictParamBulletins['largeur_tot_tab_appreciations'] * dictParamBulletins['largeurEvaluation'] / 100
    largeur_rubrique = largeur_evaluation*1/4*3/4
    largeur_evaluation_rubrique = largeur_evaluation*1/4*1/4
    largeur_competence = largeur_evaluation*11/15
    largeur_evaluation_competence=largeur_evaluation*4/15

    TAILLE_POLICE = dictParamBulletins['fontSize']
    font=dictParamBulletins['font']

    couleurAppreciation=dictParamBulletins['couleurAppreciation']

    #Calcul de la taille de la police pour l'évaluation de l'appréciation
    #Tenir compte de la ligne résultat à ajouter au total...
    len_competences = 0
    if bulletinUtilisationCompetence:
        for competence in competences.all():
            len_competences+=len(competence.competence.intitule)
    if appreciation.commentaire:
        len_commentaire=len(appreciation.commentaire)
    else : len_commentaire=0
    if evaluation_active:
        len_commentaire+=40
    taillePoliceEvaluation = pdf_taille.evaluation(len_commentaire,len_competences,TAILLE_POLICE)

    # Calcul de la taille de la police pour la description de l'appréciation

    if appreciation.discipline.titre:
        len_titre=len(appreciation.discipline.titre)
    else : len_titre=0
    if appreciation.discipline.descriptif:
        len_descriptif = len(appreciation.discipline.descriptif)
    else : len_descriptif=0
    taillePoliceDescription = pdf_taille.description(len_titre,len_descriptif,TAILLE_POLICE)


    # première ligne d'une appréciation
    # Case titre d'une discipline

    contenu,style=pdf_donnees.discipline(appreciation.discipline.intitule,appreciation.discipline.show_enseignants(),appreciation.discipline.dateDebut,appreciation.discipline.dateFin,appreciation.discipline.volumeHoraire,TAILLE_POLICE,appreciation.discipline.typeEnseignement,appreciation.discipline.voirProf,font)
    caseDiscipline = Paragraph(contenu,style)

    contenu,style=pdf_donnees.descriptif(appreciation.discipline.descriptif,appreciation.discipline.titre,taillePoliceDescription,font)
    caseDescriptif = Paragraph(contenu,style)

    #Début des contenus de la 3e colonne Evaluation
    contenuTableauEvaluation=[]

    # première ligne du tableau évaluation :
    if evaluation_active:
        dict_evaluation = {}
        if appreciation.attitude != None and appreciation.attitude != '':
            dict_evaluation['attitude'] = appreciation.attitude
        if appreciation.engagement != None and appreciation.engagement != '':
            dict_evaluation['engagement'] = appreciation.engagement
        if appreciation.note is not None and appreciation.note >= 0:
            dict_evaluation['note'] = appreciation.note
            if appreciation.discipline.activerMoyenne and appreciation.discipline.moyenne is not None:
                dict_evaluation['moyenne'] = appreciation.discipline.moyenne
        elif appreciation.resultat != None and appreciation.resultat != '':
            dict_evaluation['resultat'] = appreciation.resultat

        donneesLigneEvaluation, colonnesLigneEvaluation = pdf_donnees.ligneEvaluation(dict_evaluation, largeur_rubrique,
                                                                                      largeur_evaluation_rubrique)
        tableauLigneEvaluation = Table([donneesLigneEvaluation],# colWidths=colonnesLigneEvaluation,
                                       style=pdf_styles.tableauLigneEvaluation(TAILLE_POLICE*0.9,font))
        contenuTableauEvaluation.append([tableauLigneEvaluation])

    #2e ligne du tableau évaluation : le commentaire
    contenu,style=pdf_donnees.commentaire(appreciation.commentaire,taillePoliceEvaluation,font)
    caseCommentaire = Paragraph(contenu,style)
    contenuTableauEvaluation.append([caseCommentaire])


    if bulletinUtilisationCompetence == True:
        for competence in competences.all():
            if competence.evaluation != '-':
                competenceIntitule,styleCompetenceIntitule=pdf_donnees.competenceIntitule(competence.competence.intitule,taillePoliceEvaluation,font)
                competenceEvaluation,styleCompetenceEvaluation=pdf_donnees.competenceEvaluation(competence.evaluation,taillePoliceEvaluation*0.8,font)
                ligneTableauCompetence=Table([[Paragraph(competenceIntitule,styleCompetenceIntitule),Paragraph(competenceEvaluation,styleCompetenceEvaluation)]],colWidths=[largeur_competence,largeur_evaluation_competence],style=pdf_styles.ligneTableauCompetence)
                contenuTableauEvaluation.append([ligneTableauCompetence])


    # Constitution finale de la 3e colonne Evaluation
    tableauEvaluation = Table(contenuTableauEvaluation,colWidths=[largeur_evaluation],style=pdf_styles.tableauEvaluation(num,couleurAppreciation))

    appreciationTotaleData = [[caseDiscipline,caseDescriptif,tableauEvaluation]]
    tableauAppreciationTotale = Table(appreciationTotaleData, colWidths=[largeur_discipline,
                                        largeur_descriptif,largeur_evaluation],
                                            style=pdf_styles.tableauAppreciationTotaleAvecEvaluation(num,couleurAppreciation),)
    story.append(tableauAppreciationTotale)

def espace(story,h=0.25):
    story.append(Spacer(20 * cm, h * cm))

def absencesRetards(absence,dictParamBulletins):
    retardsAbsences = ''
    if absence.nbRetard!=0:
        retardsAbsences = f"Nombre de retard en classe injustifié au cours du trimestre : {absence.nbRetard} <br />"
    if absence.nbAbsenceTot != 0:
        retardsAbsences += f"Nombre de demi-journées d'absence au cours du trimestre : {absence.nbAbsenceTot},"
        if absence.nbAbsenceNonExc == 0:
            retardsAbsences += " aucune non-excusée <br />"
        else :
            retardsAbsences += f" dont {absence.nbAbsenceNonExc} non-excusée(s) <br />"
    if retardsAbsences == '' :
        retardsAbsences=f"Aucune absence ou retard injustifié au cours du trimestre"
    return Paragraph(retardsAbsences,pdf_styles.retardsAbsences(dictParamBulletins['fontSize'],dictParamBulletins['font']))

def avisCollege(avisCollege,dictParamBulletins,story):
    # Largeur des colonnes d'un tableau appreciation
    largeur_avis = dictParamBulletins['largeur_tot_tab_appreciations']
    TAILLE_POLICE = dictParamBulletins['fontSize']
    font = dictParamBulletins['font']
    couleur=dictParamBulletins['couleurAvis']
    data=[]
    data.append(["Avis du collège des professeurs"])
    contenu, style = pdf_donnees.avisCollege(avisCollege, TAILLE_POLICE, font)
    data.append([Paragraph(contenu,style)])
    tableauAvisCollege = Table(data, colWidths=[largeur_avis],
                        style=pdf_styles.tableauAvisCollege(TAILLE_POLICE,font,couleur))
    story.append(tableauAvisCollege)

def stagesProjets(stagesEleve,projetsEleve,dictParamBulletins,story):
    largeur_avis = dictParamBulletins['largeur_tot_tab_appreciations']
    TAILLE_POLICE = dictParamBulletins['fontSize']
    couleur=dictParamBulletins['couleurStageProjet']
    font = dictParamBulletins['font']
    data = []
    data.append(["Stages & Projets"])
    for stage in stagesEleve :
        contenu,style=pdf_donnees.stage(stage,TAILLE_POLICE,font)
        data.append([Paragraph(contenu,style)])
    for projet in projetsEleve :
        contenu,style=pdf_donnees.projet(projet,TAILLE_POLICE,font)
        data.append([Paragraph(contenu,style)])
    tableauStagesProjets = Table(data, colWidths=[largeur_avis],
                               style=pdf_styles.tableauStagesProjets(TAILLE_POLICE, font,couleur))
    story.append(tableauStagesProjets)



def noticeBulletin(story,dictParamBulletins,notice):
    # Largeur des colonnes d'un tableau appreciation
    largeur_avis = dictParamBulletins['largeur_tot_tab_appreciations']
    largeur_rubrique = largeur_avis * 1/4
    largeur_symboles = largeur_avis * 3/4
    TAILLE_POLICE = dictParamBulletins['fontSize']*0.8
    font = dictParamBulletins['font']
    couleur=dictParamBulletins['couleurNotice']
    contenuNotice = {}
    if notice == None:
        #Notice par défaut
        contenuNotice['titre']='''Bulletin EMG <br />Barême d'évaluation'''
        contenuNotice['intro'] = '''Pour caractériser la scolarité d'un élève de grandes classes durant un trimestre, le collège des professeurs évalue trois domaines spécifiques pour chaque enseignement suivi : l'attitude, l'engagement et le résultat obtenu, à l'aide de lettres A, B, C et D, dont les repères correspondants sont précisés ci-dessous. Un descriptif plus complet et détaillé des enseignements suivis est disponible dans le projet pédagogique de l'école (en ligne à l'adresse : https://www.projetpeda.ecole-mathias-grunewald.org).'''
        contenuNotice['attitude']='''comportement en classe vis à vis des camarades et des enseignants, soin du matériel et des locaux, participation aux tâches collectives etc.'''
        contenuNotice['resultat'] = '''acquisition des compétences et savoirs relatifs à l'enseignement s'applique également à l'évaluation au cas par cas de l'acquisition des compétences.'''
        contenuNotice['engagement'] = '''participation aux activités proposées, réactivité, prise d'initiative, assiduité et sérieux dans la réalisation du travail demandé.'''
        contenuNotice['attitudeA'] = "Attitude positive et constructive."
        contenuNotice['attitudeB'] = "Attitude adaptée et satisfaisante dans l'ensemble."
        contenuNotice['attitudeC'] = "Remarques et rappels à l'ordre concernant l'attitude encore trop fréquents."
        contenuNotice['attitudeD'] = "Attitude inacceptable durant cet enseignement de manière répétée, en manquant de respect aux camarades et aux enseignants."
        contenuNotice['engagementA'] = "Engagement irréprochable, au-delà parfois même du travail demandé."
        contenuNotice['engagementB'] = "Le travail demandé est globalement réalisé avec régularité et sérieux, le contrat est rempli."
        contenuNotice['engagementC'] = "Le travail demandé n'est pas réalisé avec assez de soin et/ou de régularité, et cela freine votre progression."
        contenuNotice['engagementD'] = "Engagement dans la discipline largement insuffisant : impossible dans ces conditions d'espérer progresser vers les objectifs à atteindre."
        contenuNotice['resultatA'] = "Très bonne maîtrise des connaissances et compétences visées lors de cet enseignement."
        contenuNotice['resultatB'] = "Maîtrise satisfaisante des connaissances et compétences visées lors de cet enseignement."
        contenuNotice['resultatC'] = "Maîtrise fragile des connaissances et compétences visées lors de cet enseignement."
        contenuNotice['resultatD'] = "Maîtrise insuffisante des connaissances et compétences visées lors de cet enseignement."
    else :
        contenuNotice['titre'] =notice.titre
        contenuNotice['intro'] =notice.intro
        contenuNotice['attitude'] = notice.attitude
        contenuNotice['engagement'] = notice.engagement
        contenuNotice['resultat'] = notice.resultat
        contenuNotice['resultatA'] = notice.resultatA
        contenuNotice['resultatB'] = notice.resultatB
        contenuNotice['resultatC'] = notice.resultatC
        contenuNotice['resultatD'] = notice.resultatD
        contenuNotice['engagementA'] = notice.engagementA
        contenuNotice['engagementB'] = notice.engagementB
        contenuNotice['engagementC'] = notice.engagementC
        contenuNotice['engagementD'] = notice.engagementD
        contenuNotice['attitudeA'] = notice.attitudeA
        contenuNotice['attitudeB'] = notice.attitudeB
        contenuNotice['attitudeC'] = notice.attitudeC
        contenuNotice['attitudeD'] = notice.attitudeD


    data = []
    ligne=[]
    contenu=contenuNotice['titre']
    style=pdf_styles.noticeTitreBulletin(TAILLE_POLICE,font)
    ligne.append(Paragraph(contenu, style))
    contenu =contenuNotice['intro']
    style = pdf_styles.noticeBulletin(TAILLE_POLICE,font)
    ligne.append(Paragraph(contenu, style))
    data.append(ligne)
    #Attitude
    ligne = []
    contenu = '''<b>Attitude : </b>''' + contenuNotice['attitude']
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    #Lettres Attitudes
    contenu = f'''<b>A : </b> {contenuNotice['attitudeA']}<br/>
                <b>B : </b> {contenuNotice['attitudeB']}<br/>
                <b>C : </b> {contenuNotice['attitudeC']}<br/>
                <b>D : </b> {contenuNotice['attitudeD']}<br/>
    '''
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    data.append(ligne)
    #Engagement
    ligne = []
    contenu = '''<b>Engagement : </b>''' + contenuNotice['engagement']
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    # Lettres Engagement
    contenu = f'''<b>A : </b> {contenuNotice['engagementA']}<br/>
                    <b>B : </b> {contenuNotice['engagementB']}<br/>
                    <b>C : </b> {contenuNotice['engagementC']}<br/>
                    <b>D : </b> {contenuNotice['engagementD']}<br/>
        '''
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    data.append(ligne)
    # Résultat
    ligne = []
    contenu = '''<b>Résultat : </b>''' + contenuNotice['resultat']
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    # Lettres Résultat
    contenu = f'''<b>A : </b> {contenuNotice['resultatA']}<br/>
                        <b>B : </b> {contenuNotice['resultatB']}<br/>
                        <b>C : </b> {contenuNotice['resultatC']}<br/>
                        <b>D : </b> {contenuNotice['resultatD']}<br/>
            '''
    style = pdf_styles.noticeBulletin(TAILLE_POLICE, font)
    ligne.append(Paragraph(contenu, style))
    data.append(ligne)
    tableauNoticeBulletin = Table(data, colWidths=[largeur_rubrique,largeur_symboles],
                               style=pdf_styles.tableauNoticeBulletin(TAILLE_POLICE, font,couleur),)
    story.append(TopPadder(tableauNoticeBulletin))

def absenceEtVisa(story,absencesEleve,dictParamBulletins,signatureBulletin,bulletinAbsencesRetards):
    largeur_avis = dictParamBulletins['largeur_tot_tab_appreciations']
    largeur_absences = largeur_avis*12/18
    largeur_espace=largeur_avis*1/18
    largeur_visa=largeur_avis*5/18
    TAILLE_POLICE = dictParamBulletins['fontSize']*0.95
    font = dictParamBulletins['font']
    data = []
    ligne=[]
    if bulletinAbsencesRetards :
        ligne.append(absencesRetards(absencesEleve, dictParamBulletins))
    else :
        ligne.append("")
    ligne.append("")
    if signatureBulletin :
        ligne.append("Visa du Chef d'établissement")
        data.append(ligne)
        if absencesEleve.eleve.show_classe().cycle == 'COL' :
            chemin='static/images/visa_college.png'
        elif absencesEleve.eleve.show_classe().cycle == 'LYC' :
            chemin = 'static/images/visa_lycee.png'
        else :
            chemin = 'static/images/visa_primaire.png'
        data.append(["", "", Image(settings.BASE_DIR.joinpath(chemin), width=3 * cm, height=0.9 * cm)])

    else :
        ligne.append("")
        data.append(ligne)
    tableauAbsenceEtVisa = Table(data, colWidths=[largeur_absences,largeur_espace,largeur_visa],
                               style=pdf_styles.tableauAbsenceEtVisa(TAILLE_POLICE, font))
    story.append(tableauAbsenceEtVisa)

