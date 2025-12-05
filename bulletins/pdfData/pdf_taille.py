#Calcul des différentes tailles de polices utilisées dans la génération des bulletins

def intitule(nom_discipline,taillePolice):
    if len(nom_discipline)>40 :
        return taillePolice*0.9
    elif len(nom_discipline)>30 :
        return taillePolice
    elif len(nom_discipline)>20 :
        return taillePolice*1.1
    else :
        return taillePolice*1.2

def evaluation(len_commentaire,len_competences,taillePolice):
    somme=len_commentaire + len_competences
    #Seuil max de réduction : 0.5 au delà de 500 caractères
    seuil_max=500
    seuil_min=200
    size_min=0.7
    if somme > seuil_max :
        return taillePolice*size_min
    if somme > seuil_min :
        somme-=seuil_min
        return taillePolice*(1-((1-size_min)*somme)/(seuil_max-seuil_min))
    else :
        return taillePolice

def description(len_titre,len_descriptif,taillePolice):
    somme = len_titre + len_descriptif
    # Seuil max de réduction : 0.7 au delà de 400 caractères,réduction à partir de seuil_min
    seuil_max = 400
    seuil_min = 140
    size_min = 0.7
    if somme > seuil_max:
        return taillePolice * size_min
    if somme > seuil_min:
        somme -= seuil_min
        return taillePolice * (1 - ((1 - size_min) * somme) / (seuil_max - seuil_min))
    else:
        return taillePolice

def dates(taillePolice):
    return taillePolice * 0.8

def avisCollege(avis,taillePolice):
    return taillePolice

def prof(nom_prof,taillePolice):
    if len(nom_prof)>40:
        return taillePolice *0.6
    elif len(nom_prof)>20:
        return taillePolice*0.8
    else :
        return taillePolice


def projet(projetEleve,taille):
    if projetEleve.descriptif != None :
        tailleDescriptif = len(projetEleve.descriptif)
    else :
        tailleDescriptif = 0
    if projetEleve.appreciation != None :
        tailleAppreciation = len(projetEleve.appreciation)
    else :
        tailleAppreciation = 0
    if (tailleDescriptif + tailleAppreciation)>400 :
        return taille*0.8
    elif (tailleDescriptif + tailleAppreciation)>300 :
        return taille*0.9
    else :
        return taille

def stage(stageEleve,taille):
    if stageEleve.descriptif != None :
        tailleDescriptif = len(stageEleve.descriptif)
    else :
        tailleDescriptif = 0
    if stageEleve.appreciation != None :
        tailleAppreciation = len(stageEleve.appreciation)
    else :
        tailleAppreciation = 0
    if (tailleDescriptif + tailleAppreciation) > 400:
        return taille * 0.8
    elif (tailleDescriptif + tailleAppreciation) > 300:
        return taille * 0.9
    else:
        return taille

def noticeBulletin(taille):
    return taille