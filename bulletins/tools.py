from . import forms
from . import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import re

#Des fonctionnalités supplémentaires aux fonctions définies dans les modèles

def extraireInfosCsv(request,checkCles):
    '''
    À partir d'un fichier CSV téléversé via un formulaire contenu dans une requête de type POST
    création d'une liste de dictionnaires pour préparer le peuplement de la DB.
    Le procédé est générique à toutes les
    :param request: une requête POST contenant nécessairement un type "file"
    checkCles : liste des clés qui vont vérifier le fichier
    :return:
    donnees :liste de dictionnaire d'éléments à traiter pour instancier la dB
    log : tableau contenant des erreurs générées et transmise au template
    '''
    donnees = []
    log=[]
    try:
        form = forms.ImportCsvFileForm(request.POST, request.FILES)
        if form.is_valid():
            fichier_csv = request.FILES["file"]
            if not fichier_csv.name.endswith('.csv'):
                log.append("Le fichier téléversé n'est pas un fichier .csv")
                return donnees,log
            elif fichier_csv.multiple_chunks():
                log.append("le fichier est trop volumineux (max : 2.5 Mo)")
                return donnees,log
            donnees_fichier = fichier_csv.read().decode("utf-8-sig")
            lignes = list(donnees_fichier.split('\n'))
            cles = lignes[0].strip().split(';')
            #vérification de la présence des bon champs dans le fichier d'importation
            for cle in checkCles :
                if cle not in cles :
                    log.append(f"Erreur : le fichier ne comporte par le champs '{cle}' pourtant requis")
                    return donnees,log
            del lignes[0]
            for ligne in lignes:
                data = ligne.strip().split(';')
                donnees.append(dict(zip(cles, data)))
    except:
        log.append('Erreur : impossible de téléverser le fichier')
    return donnees,log

def validate_date(date_string):
    '''
    Vérifie qu'une date est bien au format yyyy-mm-dd
    :param date_string: date
    :return: boolean
    '''
    pattern = "^\d{4}-\d{2}-\d{2}$"
    if re.match(pattern, date_string):
        return True
    else:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def validationAppreciationImportation(donnees):
    '''
            Vérifie que le dictionnaire donnees contient des données conformes à l'importation des appréciations
            :param donnees: dictionnaire
            :return: dictionnaire des donnees, fichier log avec rapport
            '''
    disciplines=models.Discipline.objects.all()
    id_disciplines = list(disciplines.values_list("id", flat=True))
    logError = []
    ligneProblemes = []
    numLigne = 1
    for enregistrement in donnees:
        numLigne += 1
        # Vérifier l'id de la discipline
        id_discipline=int(enregistrement['id_discipline'])
        if id_discipline not in id_disciplines:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, la discipline associée à cette appréciation n'existe pas.")
            ligneProblemes.append(numLigne)
        else :
            discipline=get_object_or_404(models.Discipline,id=int(enregistrement['id_discipline']))
            id_eleves = list(discipline.enseigneeA.values_list("id", flat=True))
            if int(enregistrement['id_eleve']) not in id_eleves :
                logError.append(
                    f"Erreur ligne {numLigne} : erreur d'importation, l'élève associée à cette appréciation n'existe pas ou ne participe pas à cet enseignement.")
                ligneProblemes.append(numLigne)
        #Vérifier le commentaire
        if len(enregistrement['commentaire'])>1000:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le commentaire de l'appréciation n'est pas conforme.")
            ligneProblemes.append(numLigne)
        # Vérifier l'attitude
        if not enregistrement['attitude'].isprintable() or len(enregistrement['attitude'])>2:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, l'attitude de l'appréciation n'est pas conforme.")
            ligneProblemes.append(numLigne)
        # Vérifier l'engagement
        if not enregistrement['engagement'].isprintable() or len(enregistrement['engagement'])>2:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, l'engagement de l'appréciation n'est pas conforme.")
            ligneProblemes.append(numLigne)
            # Vérifier le résultat
        if not enregistrement['resultat'].isprintable() or len(enregistrement['resultat'])>2 :
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le résultat de l'appréciation n'est pas conforme.")
            ligneProblemes.append(numLigne)
        # Vérifier la note
        if enregistrement['note'] != '' and not is_number(enregistrement['note']) or len(enregistrement['note'])>5:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation car la note spécifiée n'est pas conforme.")
            ligneProblemes.append(numLigne)

    return logError, ligneProblemes

def validationProjetImportation(donnees):
    '''
    Vérifie que le dictionnaire donnees contient des données conformes à l'importation de projets
    :param donnees: dictionnaire
    :return: dictionnaire des donnees, fichier log avec rapport
    '''
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes = models.Classe.objects.filter(annee=annee_en_cours)
    id_eleves=list(models.Eleve.objects.filter(classe__in=classes).values_list("id",flat=True))
    User = get_user_model()
    enseignants = list(User.objects.values_list("username", flat=True))
    listeTrimestre = ['T1', "T2", 'T3']
    listeTypeProjet=['TA','AUTRE','PERS']
    logError = []
    ligneProblemes = []
    numLigne = 1
    for enregistrement in donnees:
        numLigne += 1
        #Vérifier trimestre
        if enregistrement['trimestre'] not in listeTrimestre :
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le trimestre n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier id_tuteur
        if enregistrement['tuteur'] not in enseignants :
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le tuteur spécifié n'existe pas dans la base.")
            ligneProblemes.append(numLigne)
        #Vérifier id_eleve
        if int(enregistrement['id_eleve']) not in id_eleves :
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, l'élève spécifié n'existe pas dans la base.")
            ligneProblemes.append(numLigne)
        #Vérifier type_projet
        if enregistrement['type_projet'] not in listeTypeProjet:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le type de projet n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier titre
        if enregistrement['titre'] != '' and (not enregistrement['titre'].isprintable() or len(enregistrement['titre'])>60):
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le titre n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier descriptif
        if enregistrement['descriptif'] != '' and (not enregistrement['descriptif'].isprintable() or len(enregistrement['descriptif'])>800):
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le descriptif n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier l'appreciation
        if enregistrement['appreciation'] != '' and len(enregistrement['appreciation'])>1000:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, l'appréciation n'est pas conforme.")
            ligneProblemes.append(numLigne)
    return logError, ligneProblemes


def validationStageImportation(donnees):
    '''
            Vérifie que le dictionnaire donnees contient des données conformes à l'importation de stages
            :param donnees: dictionnaire
            :return: dictionnaire des donnees, fichier log avec rapport
            '''
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes = models.Classe.objects.filter(annee=annee_en_cours)
    id_eleves = list(models.Eleve.objects.filter(classe__in=classes).values_list("id", flat=True))
    User = get_user_model()
    enseignants = list(User.objects.values_list("username", flat=True))
    listeTrimestre = ['T1', "T2", 'T3']
    listeTypeStage=['AGR','ENT','SOC','AUTRE']
    logError = []
    ligneProblemes = []
    numLigne = 1
    for enregistrement in donnees:
        numLigne += 1
        #Vérifier type_stage
        if enregistrement['type_stage'] != '' and enregistrement['type_stage'] not in listeTypeStage:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le type de stage n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier lieu_stage
        if enregistrement['lieu_stage'] != '' and (len(enregistrement['lieu_stage'])>200 or not enregistrement['lieu_stage'].isprintable()):
            logError.append(
                f"Erreur ligne {numLigne} : le lieu du stage n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier maître_stage
        if enregistrement['maitre_stage'] != '' and (len(enregistrement['maitre_stage'])>60 or not enregistrement['maitre_stage'].isprintable()):
            logError.append(
                f"Erreur ligne {numLigne} : le maître de stage n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier descriptif
        if enregistrement['descriptif'] != '' and (len(enregistrement['descriptif'])>800 or not enregistrement['descriptif'].isprintable()):
            logError.append(
                f"Erreur ligne {numLigne} : le descriptif du stage n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier appréciation
        if enregistrement['appreciation'] != '' and (len(enregistrement['appreciation'])>1000 or not enregistrement['appreciation'].isprintable()):
            logError.append(
                f"Erreur ligne {numLigne} : l'appreciation du stage n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier nb_jours
        if enregistrement['nb_jours'] != '' and not enregistrement['nb_jours'].isnumeric():
                logError.append(
                    f"Erreur ligne {numLigne} : erreur d'importation car le nombre de jours spécifié n'est pas conforme.")
                ligneProblemes.append(numLigne)
        #Vérifier la date début
        if enregistrement['date_debut'] != '' and not validate_date(enregistrement['date_debut']):
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car une date proposée n'est pas au bon format ('yyyy-mm-dd').")
            ligneProblemes.append(numLigne)
        #Vérifier la date de fin
        if enregistrement['date_fin'] != '' and not validate_date(enregistrement['date_fin']):
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car une date proposée n'est pas au bon format ('yyyy-mm-dd').")
            ligneProblemes.append(numLigne)
        #Vérifier id_eleve
        if int(enregistrement['id_eleve']) not in id_eleves:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, l'élève spécifié n'existe pas dans la base.")
            ligneProblemes.append(numLigne)
        #Vérifier trimestre
        if enregistrement['trimestre'] not in listeTrimestre :
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le trimestre n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier tuteur
        if enregistrement['tuteur'] not in enseignants:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation, le tuteur spécifié n'existe pas dans la base.")
            ligneProblemes.append(numLigne)
    return logError, ligneProblemes

def validationDisciplineImportation(donnees):
    '''
        Vérifie que le dictionnaire donnees contient des données conformes à l'importation de disciplines
        :param donnees: dictionnaire
        :return: dictionnaire des donnees, fichier log avec rapport
        '''
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes = list(models.Classe.objects.filter(annee=annee_en_cours).values_list("nom", flat=True))
    User=get_user_model()
    enseignants=list(User.objects.values_list("username", flat=True))
    listeType=['PR',"AT",'HH','PRHH','HHAT','ST','PRHHAT','SPE']
    listeTrimestre = ['T1', "T2", 'T3']
    logError = []
    ligneProblemes = []
    numLigne = 1
    for enregistrement in donnees :
        numLigne += 1
        #Vérifier l'intitule
        if enregistrement['intitule']=='' or not enregistrement['intitule'].isprintable() :
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation, l'intitulé '{enregistrement['intitule']}' n'est pas conforme.")
            ligneProblemes.append(numLigne)
        # Vérifier l'intitule court
        if (enregistrement['intitule_court'] != '' and (len(enregistrement['intitule_court'])>30) or not enregistrement['intitule_court'].isprintable()):
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation, l'intitulé court '{enregistrement['intitule_court']}' n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier le titre
        if enregistrement['titre'] != '' and not enregistrement['titre'].isprintable() :
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation, le titre '{enregistrement['titre']}' n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier le descriptif
        if enregistrement['descriptif'] != '' and len(enregistrement['descriptif'])>600 :
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation, le descriptif de la discipline n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier la date début
        if enregistrement['date_debut'] != '' and not validate_date(enregistrement['date_debut']):
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car une date proposée n'est pas au bon format ('yyyy-mm-dd').")
            ligneProblemes.append(numLigne)
        #Vérifier la date de fin
        if enregistrement['date_fin'] != '' and not validate_date(enregistrement['date_fin']):
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car une date proposée n'est pas au bon format ('yyyy-mm-dd').")
            ligneProblemes.append(numLigne)
        #Vérifier le type d'enseignement
        if enregistrement['type_enseignement'] != '' and enregistrement['type_enseignement'] not in listeType:
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car le type d'enseignement n'est pas conforme.")
            ligneProblemes.append(numLigne)
        #Vérifier le volumeHoraire
        if enregistrement['volume_horaire'] != '' and not enregistrement['volume_horaire'].isnumeric():
                logError.append(
                    f"Erreur ligne {numLigne} : erreur d'importation car le volume horaire spécifié n'est pas conforme.")
                ligneProblemes.append(numLigne)
        #Vérifier la classe, d'abord en séparant les éventuelles valeurs multiples
        if enregistrement['classe'] != '' and not all(classe in classes for classe in enregistrement['classe'].split(',')) :
            logError.append(
            f"Erreur ligne {numLigne} : erreur d'importation car la ou les classes spécifiées sont non conformes.")
            ligneProblemes.append(numLigne)
        # Vérifier les enseignants, d'abord en séparant les éventuelles valeurs multiples
        if not all(prof in enseignants for prof in enregistrement['enseignant'].split(',')) :
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation car le ou les enseignants spécifiées sont non conformes.")
            ligneProblemes.append(numLigne)
        # Vérifier trimestre
        if enregistrement['trimestre'] not in listeTrimestre:
            logError.append(
                f"Erreur ligne {numLigne} : erreur d'importation car le trimestre spécifié n'est pas conforme.")
            ligneProblemes.append(numLigne)

    return logError, ligneProblemes


def validationEleveImportation(donnees):
    '''
    Vérifie que le dictionnaire donnees contient des données conformes à l'importation d'élèves
    :param donnees: dictionnaire
    :return: dictionnaire des donnees, fichier log avec rapport
    '''
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours)
    eleves=models.Eleve.objects.all()
    listeStatut=['EL','HP','EXC']
    listeGenre=['M','F']
    logError=[]
    ligneProblemes=[]
    #Résultat de l'analyse
    classeACreer=[]
    eleveACreer=[]
    numLigne=1
    for enregistrement in donnees :
        numLigne+=1
        #Vérifier si la première clé pas foirée...
        if enregistrement['nom']=='':
            logError.append(f"Erreur ligne {numLigne} : erreur d'importation, peut être provoqué par une ligne vide.")
            ligneProblemes.append(numLigne)
            return logError,ligneProblemes,classeACreer,eleveACreer
        #Vérifier si caractères alphanumériques sont ok
        if not enregistrement['nom'].replace(" ", "").isalpha() or not enregistrement['prenom'].replace(" ", "").isalpha():
            #tester si le carctère esapce dans le nom ou le prenom coince
            logError.append(f"Erreur ligne {numLigne} : l'importation de l'élève {enregistrement['nom']} {enregistrement['prenom']} est impossible car le nom ou le prénom ne contiennent pas seulement des caractères alphabétiques.")
            ligneProblemes.append(numLigne)
        if len(enregistrement['nom'])>30 :
            logError.append(
                f"Erreur ligne {numLigne} : l'importation de l'élève est impossible car le nom contient plus de 30 caractères.")
            ligneProblemes.append(numLigne)
        if len(enregistrement['prenom'])>30 :
            logError.append(
                f"Erreur ligne {numLigne} : l'importation de l'élève est impossible car le prenom contient plus de 30 caractères.")
            ligneProblemes.append(numLigne)
        #Vérifier si le genre est bien M ou F
        if enregistrement['genre'] not in listeGenre :
            logError.append(f"Erreur ligne {numLigne} : l'importation de l'élève {enregistrement['nom']} {enregistrement['prenom']} est impossible car le genre proposé n'est pas valide ('M' ou 'F').")
            ligneProblemes.append(numLigne)
        #Vérification du format de la date yyyy-mm-dd
        if enregistrement['date_naissance'] != '' and not validate_date(enregistrement['date_naissance']):
            logError.append(f"Erreur ligne {numLigne} : l'importation de l'élève {enregistrement['nom']} {enregistrement['prenom']} est impossible car le date proposée n'est pas au bon format ('yyyy-mm-dd').")
            ligneProblemes.append(numLigne)
        #Vérifier si le statut fait bien parti de la liste proposée
        if enregistrement['statut'] != '' and enregistrement['statut'] not in listeStatut :
            logError.append(f"Erreur ligne {numLigne} : l'importation de l'élève {enregistrement['nom']} {enregistrement['prenom']} est impossible car le statut proposé n'est pas valide ('EL','HP' ou 'EXC').")
            ligneProblemes.append(numLigne)
        #Vérifier si la classe est ok ou pas (caractère num, longueur max = 2)
        if enregistrement['classe'] != '' and enregistrement['classe'].isnumeric():
            # Vérifier si la classe existe ou pas, sinon proposer de créer la classe
            if classes.filter(nom=enregistrement['classe']).first() == None:
                if enregistrement['classe'] not in classeACreer:
                    classeACreer.append(enregistrement['classe'])
        else :
            logError.append(f"importation de l'élève {enregistrement['nom']} {enregistrement['prenom']} (ligne {numLigne}) est impossible car le nom de la classe proposé n'est pas valide (chiffres uniquement).")
            ligneProblemes.append(numLigne)

        #Vérifier si l'élève existe ou pas, sinon proposer de créer l'élève
        if eleves.filter(nom=enregistrement['nom']).filter(prenom=enregistrement['prenom']).first() == None:
            if (enregistrement['nom'],enregistrement['prenom']) not in eleveACreer :
                eleveACreer.append((enregistrement['nom'],enregistrement['prenom']))
    return logError,ligneProblemes,classeACreer,eleveACreer

def importationDiscipline(donnees):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    log = []
    User = get_user_model()
    for enregistrement in donnees:
        #On importe les champs obligatoires : intitule, classe, trimestres, enseignants,typeEnseignement,
        trimestre=models.Trimestre.objects.get(intitule=f"{enregistrement['trimestre'][1]}e Trimestre",annee=annee_en_cours)
        discipline=models.Discipline(intitule=enregistrement['intitule'],trimestre=trimestre)
        if enregistrement['type_enseignement'] != '':
            discipline.typeEnseignement=enregistrement['type_enseignement']
        if enregistrement['date_debut'] != '':
            discipline.dateDebut=enregistrement['date_debut']
        if enregistrement['titre'] != '':
            discipline.titre=enregistrement['titre']
        if enregistrement['date_fin'] != '':
            discipline.dateFin = enregistrement['date_fin']
        if enregistrement['volume_horaire'] != '':
            discipline.volumeHoraire = enregistrement['volume_horaire']
        if enregistrement['descriptif'] != '':
            discipline.descriptif = enregistrement['descriptif']
        if enregistrement['intitule_court'] != '':
            discipline.intitule_court=enregistrement['intitule_court']
        discipline.save()
        for prof in enregistrement['enseignant'].split(','):
            enseignant=User.objects.get(username=prof)
            discipline.enseigneePar.add(enseignant)
        for classe in enregistrement['classe'].split(','):
            classeAAjouter=models.Classe.objects.get(nom=classe,annee=annee_en_cours)
            discipline.enseigneeDans.add(classeAAjouter)
        #on remplit la discipline avec les élèves associés aux classes
        eleves = models.Eleve.objects.filter(classe__in=discipline.enseigneeDans.all())
        for eleve in eleves:
            discipline.enseigneeA.add(eleve)
        log.append(f"La discipline {discipline.intitule} {discipline.show_classes()} {discipline.trimestre} {discipline.show_enseignants()} a bien été créée.")
        #On importe les champs optionnels : dateDebut,dateFin, volumeHoraire
    return log

def importationProjet(donnees):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    log = []
    User = get_user_model()
    for enregistrement in donnees:
        trimestre=models.Trimestre.objects.get(intitule=f"{enregistrement['trimestre'][1]}e Trimestre",annee=annee_en_cours)
        eleve = get_object_or_404(models.Eleve, id=int(enregistrement['id_eleve']))
        tuteur = get_object_or_404(User, username=enregistrement['tuteur'])
        projet = models.Projet(eleve=eleve, tuteur=tuteur, trimestre=trimestre)
        if enregistrement['descriptif'] != '':
            projet.descriptif = enregistrement['descriptif']
        if enregistrement['appreciation'] != '':
            projet.appreciation = enregistrement['appreciation']
        if enregistrement['type_projet'] != '':
            projet.typeProjet = enregistrement['type_projet']
        projet.save()
        log.append(
            f"Le projet {projet.typeProjet} {projet.eleve} {projet.trimestre} suivi par {projet.tuteur} a bien été enregistré. ")
    return log

def importationStage(donnees):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    log=[]
    User = get_user_model()
    for enregistrement in donnees :
        eleve = get_object_or_404(models.Eleve, id=int(enregistrement['id_eleve']))
        tuteur = get_object_or_404(User,username=enregistrement['tuteur'])
        trimestre=models.Trimestre.objects.get(intitule=f"{enregistrement['trimestre'][1]}e Trimestre",annee=annee_en_cours)
        stage=models.Stage(eleve=eleve,tuteur=tuteur,trimestre=trimestre)
        if enregistrement['descriptif'] != '':
            stage.descriptif=enregistrement['descriptif']
        if enregistrement['appreciation'] != '':
            stage.appreciation=enregistrement['appreciation']
        if enregistrement['type_stage'] != '':
            stage.typeStage=enregistrement['type_stage']
        if enregistrement['lieu_stage'] != '':
            stage.lieuStage=enregistrement['lieu_stage']
        if enregistrement['maitre_stage'] != '':
            stage.maitreStage=enregistrement['maitre_stage']
        if enregistrement['nb_jours'] != '':
            stage.nbJours=enregistrement['nb_jours']
        if enregistrement['date_debut'] != '':
            stage.dateDebut=enregistrement['date_debut']
        if enregistrement['date_fin'] != '':
            stage.dateFin=enregistrement['date_fin']
        stage.save()
        log.append(f"Le stage {stage.typeStage} {stage.eleve} {stage.trimestre} suivi par {stage.tuteur} a bien été enregistré. ")
    return log




def importationAppreciation(donnees):
    log = []
    for enregistrement in donnees:
        discipline=get_object_or_404(models.Discipline,id=int(enregistrement['id_discipline']))
        eleve=get_object_or_404(models.Eleve,id=int(enregistrement['id_eleve']))
        appreciation_existante = models.Appreciation.objects.filter(discipline=discipline, eleve=eleve).first()

        if appreciation_existante != None:
            log.append(f"L'importation de l'appréciation pour l'élève {eleve.nom} {eleve.prenom} est impossible car celui-ci a déjà une appréciation pour cette discipline.")
        else :
            appreciation=models.Appreciation(discipline=discipline,eleve=eleve,commentaire=enregistrement['commentaire'],attitude=enregistrement['attitude'],engagement=enregistrement['engagement'],resultat=enregistrement['resultat'])
            if enregistrement['note']!='':
                appreciation.note=float(enregistrement['note'])
            appreciation.save()
            log.append(f"L'appréciation pour l'élève {appreciation.eleve.nom} {appreciation.eleve.prenom} et la discipline {appreciation.discipline.intitule} {appreciation.discipline.trimestre} {appreciation.discipline.show_classes()} a bien été créée.")
    return log

def importationEleve(donnees):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    log=[]
    for enregistrement in donnees:
        # traitement de la clé étrangère
        classe, already_exist = models.Classe.objects.get_or_create(nom=enregistrement['classe'], annee=annee_en_cours)
        if already_exist :
            log.append(f"La classe {classe.nom} a bien été créée.")

        try:
            eleve, already_exist = models.Eleve.objects.get_or_create(nom=enregistrement['nom'], prenom=enregistrement['prenom'])
            if not already_exist:
                if classe in eleve.classe.all():
                    log.append(
                        f"l'élève {eleve.nom} {eleve.prenom} est déjà affecté à la classe {classe.nom} pour l'année scolaire {annee_en_cours}.")
                else :
                    eleve.classe.add(classe)
                    classe.save()
                    log.append(f"l'élève {eleve.nom} {eleve.prenom} a été affecté à la classe {classe.nom} pour l'année scolaire {annee_en_cours}.")

            else:
                if enregistrement['date_naissance'] != '' :
                    eleve.dateNaissance = enregistrement['date_naissance']
                if enregistrement['statut'] != '':
                    eleve.statut = enregistrement['statut']
                eleve.genre = enregistrement['genre']
                eleve.save()
                eleve.classe.add(classe)
                classe.save()
                log.append(f"L'élève {eleve.nom} {eleve.prenom} a bien été créé, ajouté à la classe {classe.nom} pour l'année scolaire {annee_en_cours}.")
        except:
            log.append(f"Erreur d'importation")
    return log

    






