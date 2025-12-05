#Préparation des données pour incorporation dans les bulletins
from . import pdf_taille
from . import pdf_styles

def datesMiseEnForme(dateDebut,dateFin,taille,volumeHoraire=None):
    dateDebutFormate = str(dateDebut).split('-')
    dateFinFormate = str(dateFin).split('-')
    if volumeHoraire == None or volumeHoraire == '':
        return f'''<font size={pdf_taille.dates(taille)}>du {dateDebutFormate[2]}/{dateDebutFormate[1]}/{dateDebutFormate[0][-2:]} au {dateFinFormate[2]}/{dateFinFormate[1]}/{dateFinFormate[0][-2:]   }</font>'''
    else :
        return f'''<font size={pdf_taille.dates(taille)}>du {dateDebutFormate[2]}/{dateDebutFormate[1]}/{dateDebutFormate[0][-2:]} au {dateFinFormate[2]}/{dateFinFormate[1]}/{dateFinFormate[0][-2:]} - {volumeHoraire} h</font>'''



def discipline(intitule,prof,dateDebut,dateFin,volumeHoraire,taille,typeEnseignement,afficherProf,font):
    paragraphe=""
    if intitule != None :
        paragraphe+=f'''<b><font size={pdf_taille.intitule(intitule,taille)}>{intitule}</font></b> <br/>'''
    if typeEnseignement=="SPE":
        paragraphe+=f'''<b><font size={pdf_taille.intitule(intitule,taille)}>(spécialité)</font></b> <br/>'''
    if afficherProf and prof != None :
        paragraphe+=f'''<font size={pdf_taille.prof(prof,taille)}>{prof}</font><br/>'''
    if dateDebut != None and dateFin != None :
        paragraphe+=datesMiseEnForme(dateDebut,dateFin,taille,volumeHoraire)+"<br />"
    elif volumeHoraire != None :
        paragraphe+=f'''<font size={pdf_taille.dates(taille)}>{volumeHoraire} h</font>'''
    return paragraphe,pdf_styles.caseDiscipline(pdf_taille.intitule(intitule, taille),font)

def descriptif(descriptif, titre, taille,font):
    paragraphe=''
    if titre != None :
        paragraphe+=f'''<b><font size={taille}>{titre}</font></b><br/>'''
    if descriptif != None:
        paragraphe += f'''<font size={taille}>{descriptif}</font>'''
    return paragraphe,pdf_styles.caseDescriptif(taille,font)

def commentaire(commentaire,taille,font):
    paragraphe=''
    if commentaire != None :
        paragraphe+=f'''<font size={taille}>{commentaire}</font>'''
    return paragraphe,pdf_styles.caseCommentaire(taille,font)

def ligneEvaluation(dictEvaluation,largeurRubrique,largeurEvaluationRubrique):
    donneesLigneEvaluation=[]
    colonnesLigneEvaluation=[]
    if 'attitude' in dictEvaluation.keys():
        donneesLigneEvaluation.append("Attitude : ")
        colonnesLigneEvaluation.append(largeurRubrique)
        donneesLigneEvaluation.append(dictEvaluation['attitude'])
        colonnesLigneEvaluation.append(largeurEvaluationRubrique)
    if 'engagement' in dictEvaluation.keys():
        donneesLigneEvaluation.append("     Engagement :")
        colonnesLigneEvaluation.append(largeurRubrique)
        donneesLigneEvaluation.append(dictEvaluation['engagement'])
        colonnesLigneEvaluation.append(largeurEvaluationRubrique)
    if 'resultat' in dictEvaluation.keys():
        donneesLigneEvaluation.append("     Résultat :")
        colonnesLigneEvaluation.append(largeurRubrique)
        donneesLigneEvaluation.append(dictEvaluation['resultat'])
        colonnesLigneEvaluation.append(largeurEvaluationRubrique)
    elif 'note' in dictEvaluation.keys():
        donneesLigneEvaluation.append("     Note :")
        colonnesLigneEvaluation.append(largeurRubrique)
        donneesLigneEvaluation.append(dictEvaluation['note'])
        colonnesLigneEvaluation.append(largeurEvaluationRubrique)
        if 'moyenne' in dictEvaluation.keys():
            donneesLigneEvaluation.append("     (moy. clas. :")
            colonnesLigneEvaluation.append(largeurRubrique)
            donneesLigneEvaluation.append(str(dictEvaluation['moyenne'])+")")
            colonnesLigneEvaluation.append(largeurEvaluationRubrique)

    return donneesLigneEvaluation,colonnesLigneEvaluation

def competenceIntitule(intitule,taillePolice,font):
    paragraphe = ''
    if intitule != None:
        paragraphe += f'''<font size={taillePolice}>{intitule}</font>'''
    return paragraphe,pdf_styles.competenceIntitule(taillePolice,font)

def competenceEvaluation(evaluation,taillePolice,font):
    paragraphe = ''
    if evaluation != None:
        paragraphe += f'''<font size={taillePolice}>{evaluation}</font>'''
    return paragraphe, pdf_styles.competenceEvaluation(taillePolice,font)

def avisCollege(avis,taillePolice,font):
    paragraphe = f"""
                <font size={pdf_taille.avisCollege(avis,taillePolice)}>
                {avis.avis} <br/>
                Pour le collège des professeurs : {avis.eleve.show_classe().show_tuteur()}
                </font>
                """
    return paragraphe,pdf_styles.avisCollege(pdf_taille.avisCollege(avis,taillePolice),font)

def stage(stageEleve,fontSize,font):
    paragraphe=''
    if stageEleve.typeStage == 'AGR':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Stage agricole</font></b>'''
    elif stageEleve.typeStage == 'ENT':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Stage en entreprise</font></b>'''
    elif stageEleve.typeStage == 'LING':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Échange linguistique</font></b>'''
    elif stageEleve.typeStage == 'SOC':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Stage en milieu social</font></b>'''
    else :
        paragraphe += f'''<b><font size={fontSize * 1.1}>Stage</font></b>'''

    if stageEleve.lieuStage != None and stageEleve.lieuStage != '':
        paragraphe+=f'''<font size={fontSize}> - Lieu : {stageEleve.lieuStage}</font>'''
    if stageEleve.maitreStage != None and stageEleve.maitreStage != '':
            paragraphe+=f'''<font size={fontSize}> - Maître de stage : {stageEleve.maitreStage}</font>'''
    if stageEleve.dureeStage != None and stageEleve.dureeStage != '':
        paragraphe+=f'''<font size={fontSize}> - {stageEleve.dureeStage} </font>'''
    if stageEleve.dateDebut != None and stageEleve.dateDebut != '' and stageEleve.dateFin != None and stageEleve.dateFin != '':
        paragraphe+=" - " + datesMiseEnForme(stageEleve.dateDebut, stageEleve.dateFin, fontSize/0.8)

    if stageEleve.descriptif != None and stageEleve.descriptif !='':
        paragraphe+=f'''<br/><font size={pdf_taille.stage(stageEleve,fontSize)}>{stageEleve.descriptif}</font>'''

    if stageEleve.appreciation != None and stageEleve.appreciation !='':
        paragraphe+=f'''<br/><font size={pdf_taille.stage(stageEleve,fontSize)}>{stageEleve.appreciation}</font>'''

    if stageEleve.typeStage != 'LING':
        paragraphe += f''' {stageEleve.tuteur.nom_court()}'''
    return paragraphe,pdf_styles.stage(pdf_taille.stage(stageEleve,fontSize),font)


def projet(projetEleve,fontSize,font):
    paragraphe = ''
    if projetEleve.typeProjet == 'TA':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Travail d'année'''
    elif projetEleve.typeProjet == 'PERS':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Projet personnel'''
    elif projetEleve.typeProjet == 'COLL':
        paragraphe+=f'''<b><font size={fontSize*1.1}>Projet collectif'''
    else :
        paragraphe+= f'''<b><font size={fontSize * 1.1}>Projet'''
    if projetEleve.titre != None and projetEleve.titre != '':
        paragraphe += f''' - {projetEleve.titre}</font></b>'''
    else :
        paragraphe+=f'''</font></b>'''
    if projetEleve.descriptif != None and projetEleve.descriptif != '':
        paragraphe += f'''<br/><font size={pdf_taille.projet(projetEleve, fontSize)}><b>Objectif :</b> {projetEleve.descriptif}</font>'''
    if projetEleve.appreciation != None and projetEleve.appreciation != '':
        paragraphe += f'''<br/><font size={pdf_taille.projet(projetEleve, fontSize)}>'''
        if projetEleve.typeProjet == 'TA':
            paragraphe +=f'''<b>Bilan du {projetEleve.trimestre.intitule} :</b>'''
        paragraphe +=f''' {projetEleve.appreciation}</font>'''
    paragraphe += f''' {projetEleve.tuteur.nom_court()}'''
    return paragraphe, pdf_styles.projet(pdf_taille.projet(projetEleve,fontSize), font)
