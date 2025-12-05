import json
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import modelformset_factory
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode
from . import models
from . import forms
from . import tools
import csv

@login_required
def home(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    classes_tutorat = models.Classe.objects.filter(tuteur=request.user)
    eleves = models.Eleve.objects.filter(classe__in=classes_tutorat)
    avisCollege = models.AvisCollege.objects.filter(eleve__in=eleves).filter(trimestre__in=trimestres)
    disciplines = models.Discipline.objects.filter(enseigneePar=request.user).filter(trimestre__in=trimestres)
    my_corrections_disciplines = disciplines.filter(correctionsAValider=True)
    stages = models.Stage.objects.filter(tuteur=request.user).filter(trimestre__in=trimestres)
    my_corrections_stages = stages.filter(correctionsAValider=True)
    projets = models.Projet.objects.filter(tuteur=request.user).filter(trimestre__in=trimestres)
    my_corrections_projets = projets.filter(correctionsAValider=True)
    corrections_disciplines=models.Discipline.objects.filter(reluPar=request.user).filter(trimestre__in=trimestres).filter(relectureActive=True)
    corrections_stages=models.Stage.objects.filter(relecteur=request.user).filter(trimestre__in=trimestres).filter(relectureActive=True)
    corrections_projets=models.Projet.objects.filter(relecteur=request.user).filter(trimestre__in=trimestres).filter(relectureActive=True)
    corrections=0
    if corrections_disciplines.exists():
        corrections+=len(corrections_disciplines)
    if corrections_stages.exists():
        corrections+=len(corrections_stages)
    if corrections_projets.exists():
        corrections+=len(corrections_projets)
    my_corrections=0
    if my_corrections_projets.exists() :
        my_corrections+=len(my_corrections_projets)
    if my_corrections_stages.exists() :
        my_corrections+=len(my_corrections_stages)
    if my_corrections_disciplines.exists() :
        my_corrections+=len(my_corrections_disciplines)
    return render(request,'bulletins/home.html',context={'annee_en_cours':annee_en_cours,'trimestres':trimestres,'disciplines':disciplines,'stages':stages,'projets':projets,'my_corrections':my_corrections,'corrections':corrections,'avis':avisCollege})

#Vues relatives à la gestion des classes

@login_required
@permission_required('bulletins.view_classe')
def classes_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')
    return render(request,'bulletins/classe/classes_list.html',context={'classes':classes,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_classe')
def classes_list_admin(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes=models.Classe.objects.all().order_by('-annee')
    if request.method=='POST':
        form = forms.ClasseForm(request.POST)
        if form.is_valid():
            classe=form.save()
            classe.annee=annee_en_cours
            classe.save()
        return redirect('classes_list_admin')
    else :
        form = forms.ClasseForm()
        return render(request,'bulletins/classe/classes_list_admin.html',context={'classes':classes,'form':form,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_classe')
def classe_change(request,id):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classe = models.Classe.objects.get(id=id)
    eleves=models.Eleve.objects.filter(classe=classe)
    if request.method == 'POST':
        if 'edit_classe' in request.POST :
            formClasse = forms.ClasseForm(request.POST, instance=classe)
            if formClasse.is_valid():
                formClasse.save()
                log = models.Journal(utilisateur=request.user,
                                     message=f'''Modification de la {classe.nom}e classe''')
                log.save()
            return redirect('classes_list_admin')
        if 'classe_add_eleve' in request.POST :
            formClasseAddEleve = forms.ClasseAddEleveForm(request.POST)
            if formClasseAddEleve.is_valid():
                disciplineTest = formClasseAddEleve.save()
                for eleve in disciplineTest.enseigneeA.all():
                    eleve.classe.add(classe)
                    classe.save()
                disciplineTest.delete()
                log = models.Journal(utilisateur=request.user, message=f'''Modification des effectifs en {classe.nom}e classe''')
                log.save()
            return redirect('classe_change', id)

    else:
        formClasse = forms.ClasseForm(instance=classe)
        formClasseAddEleve = forms.ClasseAddEleveForm(idClasse=id)
        return render(request, 'bulletins/classe/classe_change.html', context={'formClasse': formClasse,'formClasseAddEleve':formClasseAddEleve,'classe': classe,'eleves':eleves,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.delete_classe')
def classe_eleve_remove(request,idClasse,idEleve):
    classe=get_object_or_404(models.Classe,id=idClasse)
    eleve=get_object_or_404(models.Eleve,id=idEleve)
    if classe in eleve.classe.all():
        eleve.classe.remove(classe)
        classe.save()
        log = models.Journal(utilisateur=request.user,
                             message=f'''Retrait de {eleve.prenom[0]} {eleve.nom} de la {classe.nom}e classe''')
        log.save()
    return redirect('classe_change',idClasse)

@login_required
@permission_required('bulletins.view_classe')
def classe_detail(request,id):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classe=models.Classe.objects.get(id=id)
    eleves=models.Eleve.objects.filter(classe=classe)
    return render(request,'bulletins/classe/classe_detail.html',context={'classe':classe,'eleves':eleves,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.delete_classe')
def classe_delete(request,id):
    classe = get_object_or_404(models.Classe,id=id)
    log = models.Journal(utilisateur=request.user, message=f'''Suppression de la classe : {classe.nom}''')
    log.save()
    classe.delete()
    return redirect('classes_list_admin')

#Vues relatives à la gestion des élèves

@login_required
@permission_required('bulletins.view_eleve')
def eleves_list(request):
    annees = models.Annee.objects.all()
    annee_en_cours = annees.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours)
    eleves=models.Eleve.objects.filter(classe__in=classes)
    return render(request,'bulletins/eleve/eleve_list.html',context={'eleves':eleves,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.view_eleve')
def anciens_eleves_list(request):
    annees = models.Annee.objects.all()
    annee_en_cours = annees.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours)
    anciens_eleves=models.Eleve.objects.exclude(classe__in=classes)
    return render(request,'bulletins/eleve/ancien_eleve_list.html',context={'anciens_eleves':anciens_eleves,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_eleve')
def eleves_list_admin(request):
    annees = models.Annee.objects.all()
    annee_en_cours = annees.filter(is_active=True)[0]
    eleves=models.Eleve.objects.all()
    if request.method=='POST':
        form = forms.EleveForm(request.POST)
        if form.is_valid():
            eleve=form.save()
            log = models.Journal(utilisateur=request.user,message=f'''Création de l'élève : {eleve.prenom} {eleve.nom}''')
            log.save()
        return redirect('eleves_list_admin')
    else :
        form = forms.EleveForm(annee_en_cours=annee_en_cours)
        return render(request,'bulletins/eleve/eleves_list_admin.html',context={'eleves':eleves,'annee_en_cours':annee_en_cours,'form':form})

@login_required
@permission_required('bulletins.view_eleve')
def eleve_detail(request,id):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    eleve=models.Eleve.objects.get(id=id)
    classes=eleve.classe.all().order_by('-annee')
    appreciations=models.Appreciation.objects.filter(eleve=eleve).order_by('-discipline__trimestre__annee','-discipline__trimestre','discipline__intitule')
    competencesAppreciations=models.CompetencesAppreciations.objects.filter(appreciation__in=appreciations)
    stages=models.Stage.objects.filter(eleve=eleve).order_by('-trimestre')
    projets=models.Projet.objects.filter(eleve=eleve).order_by('-trimestre')
    avisCollege=models.AvisCollege.objects.filter(eleve=eleve).exclude(avis__exact='').exclude(avis__isnull=True).order_by('-trimestre')
    absencesRetards=models.Absence.objects.filter(eleve=eleve)
    return render(request,'bulletins/eleve/eleve_detail.html',context={'eleve':eleve,'avisCollege':avisCollege,'classes':classes,'appreciations':appreciations,'absencesRetards':absencesRetards,'annee_en_cours':annee_en_cours,'stages':stages,'projets':projets,'competencesAppreciations':competencesAppreciations})

@login_required
@permission_required('bulletins.change_eleve')
def eleve_change(request,id):
    annees = models.Annee.objects.all()
    annee_en_cours = annees.filter(is_active=True)[0]
    eleve = models.Eleve.objects.get(id=id)
    if request.method=='POST':
        form=forms.EleveForm(request.POST,instance=eleve)
        if form.is_valid():
            eleve=form.save()
            log = models.Journal(utilisateur=request.user,
                                 message=f'''Modification de l'élève : {eleve.prenom} {eleve.nom}''')
            log.save()
            return redirect('eleves_list_admin')
    else :
        form = forms.EleveForm(annee_en_cours=annee_en_cours,instance=eleve)
        return render(request,'bulletins/eleve/eleve_change.html',context={'form':form,'eleve':eleve,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.delete_eleve')
def eleve_delete(request,id):
    eleve = models.Eleve.objects.get(id=id)
    log = models.Journal(utilisateur=request.user, message=f'''Suppression de l'élève : {eleve.prenom} {eleve.nom}''')
    log.save()
    eleve.delete()
    return redirect('eleves_list_admin')

#Gestion des années

@login_required
@permission_required('bulletins.change_annee')
def annee_list(request):
    annees=models.Annee.objects.all().order_by('intitule')
    annee_en_cours=annees.filter(is_active=True)[0]
    if request.method=='POST':
        if 'edit_annee' in request.POST :
            form = forms.AnneeForm(request.POST)
            if form.is_valid():
                annee=form.save()
                log = models.Journal(utilisateur=request.user, message=f'''Création de l'année : {annee.intitule}''')
                log.save()
                #Génération des trois trimestres pour l'année sélectionnée
                for i in range(1,4):
                    trimestre=models.Trimestre()
                    trimestre.intitule=f'{i}e Trimestre'
                    trimestre.annee=annee
                    trimestre.save()
        if 'modifAnneEnCours' in request.POST :
            annee_id = int(request.POST.getlist('annees')[0])
            for annee in annees:
                if annee.id == annee_id:
                    annee.is_active = True
                    log = models.Journal(utilisateur=request.user,
                                         message=f'''Activation de l'année : {annee.intitule}''')
                    log.save()
                    annee.save()
                else:
                    annee.is_active = False
                    annee.save()
        return redirect('annee_list')
    else :  
        form=forms.AnneeForm()
        return render(request,'bulletins/annee/annee_list.html',context={'annees':annees,'annee_en_cours':annee_en_cours,'form':form})


#Gestion des trimestres

@login_required
@permission_required('bulletins.change_trimestre')
def trimestres_change(request):
    annee_en_cours=models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    TrimestreFormSet = modelformset_factory(models.Trimestre, forms.TrimestreForm, edit_only=True, extra=0)
    if request.method == 'POST':
        formset = TrimestreFormSet(request.POST,queryset=trimestres)
        if formset.is_valid():
            for form in formset:
                form.save()
                log = models.Journal(utilisateur=request.user, message=f'''Modification des trimestres''')
                log.save()
        return redirect('trimestres_change')

    else:
        formset = TrimestreFormSet(queryset=trimestres)
        return render(request, 'bulletins/trimestre/trimestres_change.html',context={'formset': formset,'trimestres':trimestres,'annee_en_cours':annee_en_cours})

#Gestion des avis du collège

@login_required
@permission_required('bulletins.view_aviscollege')
def avis_college_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actif=trimestres.filter(edition=True)
    avisCollege = models.AvisCollege.objects.filter(trimestre__in=trimestres)
    return render(request,'bulletins/avisCollege/avis_college_list.html',context={'avisCollege':avisCollege,'annee_en_cours':annee_en_cours,'trimestres_actif':trimestres_actif})

@login_required
#TODO : créer permission spéciale pour avis Collège
def avis_college_admin_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours)
    avisCollege = models.AvisCollege.objects.filter(trimestre__in=trimestres)
    return render(request,'bulletins/avisCollege/avis_college_admin_list.html',context={'avisCollege':avisCollege,'annee_en_cours':annee_en_cours,'trimestres':trimestres})

@login_required
@permission_required('bulletins.change_aviscollege')
def avis_college_change(request,idAvis):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    avis=get_object_or_404(models.AvisCollege,id=idAvis)
    if request.method == 'POST':
        form = forms.AvisCollegeForm(request.POST,instance=avis)
        if form.is_valid():
            avis=form.save()
            if 'admin' in request.path :
                message=f'''Modification (admin) de l'avis : {avis.trimestre} {avis.eleve}'''
            else :
                f'''Modification de l'avis : {avis.trimestre} {avis.eleve}'''
            log = models.Journal(utilisateur=request.user, message=f'''Modification de l'avis : {avis.trimestre} {avis.eleve}''')
            log.save()

        if 'admin' in request.path:
            return redirect('avis_college_admin_liste')
        else :
            return redirect('avis_college_liste')

    else:
        form = forms.AvisCollegeForm(instance=avis)
        return render(request, 'bulletins/avisCollege/avis_college_change.html',
                      context={'annee_en_cours': annee_en_cours, 'form': form,'avis':avis})

@login_required
@permission_required('bulletins.delete_aviscollege')
def avis_college_delete(request,idAvis):
    avis=get_object_or_404(models.AvisCollege,id=idAvis)
    log = models.Journal(utilisateur=request.user, message=f'''Suppression de l'avis : {avis.trimestre} {avis.eleve}''')
    log.save()
    avis.delete()

    if 'admin' in request.path:
        return redirect('avis_college_admin_liste')
    else:
        return redirect('avis_college_liste')

@login_required
@permission_required('bulletins.add_aviscollege')
def avis_college_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method=='POST':
        form=forms.AvisCollegeAddForm(request.POST,user=request.user)
        if form.is_valid():
            avis=form.save()
            log = models.Journal(utilisateur=request.user,
                                 message=f'''Création de l'avis : {avis.trimestre} {avis.eleve}''')
            log.save()

        return redirect('avis_college_liste')
    else :
        form = forms.AvisCollegeAddForm(user=request.user)
        return render(request,'bulletins/avisCollege/avis_college_add.html',context={'annee_en_cours':annee_en_cours,'form':form})

#Gestion des absences par trimestre
@login_required
@permission_required('bulletins.view_absence')
def absences_retards_select_list(request):
    #pour l'édition des retards & absences
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    list_id_tuteur=[]
    classes=models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')
    if 'admin' not in request.path :
        for classe in classes :
            if request.user in classe.tuteur.all():
                list_id_tuteur.append(classe.id)
        classes=classes.filter(id__in=list_id_tuteur).order_by('nom')
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    return render(request,'bulletins/absence/absences_retards_list.html',context={'classes':classes,'trimestres':trimestres,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_absence')
def absences_retards_select_classe_change(request,idClasse,idTrimestre):
    classe = models.Classe.objects.get(id=idClasse)
    trimestre = models.Trimestre.objects.get(id=idTrimestre)
    eleves = models.Eleve.objects.filter(classe=classe)
    for eleve in eleves :
        absence, _=models.Absence.objects.get_or_create(eleve=eleve,trimestre=trimestre)
    absences = models.Absence.objects.filter(eleve__in=eleves, trimestre=trimestre)

    #Gestion formulaires :

    AbsenceFormSet = modelformset_factory(models.Absence, forms.AbsenceForm, edit_only=True, extra=0)
    if request.method == 'POST':
        formset = AbsenceFormSet(request.POST,queryset=absences)
        if formset.is_valid():
            for form in formset:
                form.save()
            log = models.Journal(utilisateur=request.user,
                                 message=f'''Modification absences retards : {trimestre} {classe.nom}''')
            log.save()
        if 'admin' in request.path:
            return redirect('absences_admin_retards')
        else :
            return redirect('absences_retards')
    else:
        formset = AbsenceFormSet(queryset=absences)
        return render(request, 'bulletins/absence/absences_retards_classes_change.html',
                      context={'formset': formset, 'trimestre':trimestre,'absences':absences,'classe':classe})

#Exportations et importations csv
@login_required
#TODO : def permission admin importexport ?
def export_csv(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    return render(request,'bulletins/csv/export_csv.html',context={'annee_en_cours':annee_en_cours})

def export_csv_journal(request):
    infos=models.Journal.objects.all()
    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_journal.csv"'

    writer = csv.writer(reponse, delimiter=';')
    writer.writerow(['id', 'date', 'user', 'message'])

    for info in infos:
        writer.writerow([info.id, info.date, info.message])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation du journal''')
    log.save()
    return reponse


@login_required
@permission_required('bulletins.view_eleve')
def export_csv_eleves(request):
    eleves=models.Eleve.objects.all()
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_eleves.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','nom','prenom','date_naissance','genre','statut','classe'])

    for eleve in eleves :
        if not eleve.classe.filter(annee=annee_en_cours):
            classe=None
        else :
            classe = eleve.classe.filter(annee=annee_en_cours)[0]
        writer.writerow([eleve.id,eleve.nom,eleve.prenom,eleve.dateNaissance,eleve.genre,eleve.statut,classe])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des élèves - actifs & inactifs''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_eleve')
def export_csv_eleves_actifs(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours)
    eleves=models.Eleve.objects.filter(classe__in=classes)

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = f'attachment ; filename= "EMG_exportation_eleves_{annee_en_cours.export()}.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','nom','prenom','date_naissance','genre','statut','classe'])

    for eleve in eleves :
        classe = eleve.classe.filter(annee=annee_en_cours)[0]
        writer.writerow([eleve.id,eleve.nom,eleve.prenom,eleve.dateNaissance,eleve.genre,eleve.statut,classe])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des élèves actifs''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_disciplines(request):
    #annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    disciplines=models.Discipline.objects.all()

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_enseignements.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','intitule','classe','trimestre','enseignant','titre','descriptif','type_enseignement','date_debut','date_fin','volume_horaire'])

    for discipline in disciplines :
        writer.writerow([discipline.id,discipline.intitule,discipline.show_classes_export(),discipline.trimestre,discipline.show_enseignant_export(),discipline.titre,discipline.descriptif,discipline.typeEnseignement,discipline.dateDebut,discipline.dateFin,discipline.volumeHoraire])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation de toutes les disciplines''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_disciplines_actives(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    disciplines=models.Discipline.objects.filter(trimestre__in=trimestres)

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_enseignements_{annee_en_cours.export()}.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','intitule','classe','trimestre','enseignant','titre','descriptif','type_enseignement','date_debut','date_fin','volume_horaire'])

    for discipline in disciplines :
        writer.writerow([discipline.id,discipline.intitule,discipline.show_classes_export(),discipline.trimestre,discipline.show_enseignant_export(),discipline.titre,discipline.descriptif,discipline.typeEnseignement,discipline.dateDebut,discipline.dateFin,discipline.volumeHoraire])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des disciplines(année en cours)''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_appreciations(request):
    appreciations=models.Appreciation.objects.all()

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_appreciations.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','enseignement','id_enseignement','nom_eleve','prenom_eleve','commentaire','note','attitude','engagement','resultat','id_competences'])

    for appreciation in appreciations :
        writer.writerow([appreciation.id,appreciation.discipline_export(),appreciation.discipline.id,appreciation.eleve.nom,appreciation.eleve.prenom,appreciation.commentaire,appreciation.note,appreciation.attitude,appreciation.engagement,appreciation.resultat,appreciation.competences_export()])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation de toutes les appréciations''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_appreciations_actives(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    disciplines=models.Discipline.objects.filter(trimestre__in=trimestres)
    appreciations=models.Appreciation.objects.filter(discipline__in=disciplines)

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_appreciations_{annee_en_cours.export()}.csv"'

    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','enseignement','id_enseignement','nom_eleve','prenom_eleve','commentaire','note','attitude','engagement','resultat','id_competences'])

    for appreciation in appreciations :
        writer.writerow([appreciation.id,appreciation.discipline_export(),appreciation.discipline.id,appreciation.eleve.nom,appreciation.eleve.prenom,appreciation.commentaire,appreciation.note,appreciation.attitude,appreciation.engagement,appreciation.resultat,appreciation.competences_export()])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des appréciations année en cours''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_stages(request):
    stages=models.Stage.objects.all()

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_stages_{annee_en_cours.export()}.csv"'
    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','typeStage','nom_eleve','prenom_eleve','lieuStage','dureeStage','maitreStage','tuteur','dateDebut','dateFin','descriptif','appreciation'])

    for stage in stages :
        writer.writerow([stage.id,stage.get_typeStage_display(),stage.eleve.nom,stage.eleve.prenom,stage.lieuStage,stage.dureeStage,stage.maitreStage,stage.tuteur.nom_court(),stage.dateDebut,stage.dateFin,stage.descriptif,stage.appreciation])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des stages''')
    log.save()
    return reponse

@login_required
@permission_required('bulletins.view_discipline')
def export_csv_stages_actives(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    stages=models.Stage.objects.filter(trimestre__in=trimestres)

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment ; filename= "EMG_exportation_stages_{annee_en_cours.export()}.csv"'
    writer = csv.writer(reponse,delimiter=';')
    writer.writerow(['id','typeStage','nom_eleve','prenom_eleve','lieuStage','dureeStage','maitreStage','tuteur','dateDebut','dateFin','descriptif','appreciation'])

    for stage in stages :
        writer.writerow([stage.id,stage.get_typeStage_display(),stage.eleve.nom,stage.eleve.prenom,stage.lieuStage,stage.dureeStage,stage.maitreStage,stage.tuteur.nom_court(),stage.dateDebut,stage.dateFin,stage.descriptif,stage.appreciation])

    log = models.Journal(utilisateur=request.user, message=f'''Exportation des stages année en cours''')
    log.save()
    return reponse

@login_required
def import_csv(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    formEleve=forms.ImportCsvEleveFileForm()
    formDiscipline = forms.ImportCsvDisciplineFileForm()
    formAppreciation = forms.ImportCsvAppreciationFileForm()
    formStage=forms.ImportCsvStageFileForm()
    formProjet=forms.ImportCsvProjetFileForm
    logEleve=[]
    logDiscipline=[]
    logAppreciation=[]
    logStage=[]
    logProjet=[]
    clesProjet=['id_eleve','trimestre','type_projet','titre','descriptif','appreciation','tuteur']
    clesStage=['id_eleve','trimestre','type_stage','lieu_stage','maitre_stage','descriptif','appreciation','nb_jours','date_debut','date_fin','tuteur']
    clesEleves = ['nom', 'prenom', 'genre', 'classe', 'date_naissance', 'statut']
    clesDiscipline = ['intitule','intitule_court','titre', 'descriptif','type_enseignement','volume_horaire','date_debut','date_fin','classe','trimestre','enseignant']
    clesAppreciations = ['id_discipline', 'id_eleve','commentaire', 'note', 'attitude','engagement','resultat']
    if request.method=='POST':
        if 'import_eleve' in request.POST:
            donnees,logEleve=tools.extraireInfosCsv(request,clesEleves)
            if logEleve == [] :
                data = json.dumps(donnees)
                base_url = reverse('import_csv_eleves')
                query_string = urlencode({'data': data})
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
        if 'import_stage' in request.POST:
            donnees,logStage=tools.extraireInfosCsv(request,clesStage)
            if logStage==[]:
                data = json.dumps(donnees)
                base_url = reverse('import_csv_stages')
                query_string = urlencode({'data': data})
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
        if 'import_projet' in request.POST:
            donnees,logProjet=tools.extraireInfosCsv(request,clesProjet)
            if logProjet==[]:
                data = json.dumps(donnees)
                base_url = reverse('import_csv_projets')
                query_string = urlencode({'data': data})
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
        if 'import_appreciation' in request.POST:
            donnees,logAppreciation=tools.extraireInfosCsv(request,clesAppreciations)
            if logAppreciation== [] :
                data = json.dumps(donnees)
                base_url = reverse('import_csv_appreciations')
                query_string = urlencode({'data': data})
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
        if 'import_discipline' in request.POST:
            donnees, logDiscipline = tools.extraireInfosCsv(request, clesDiscipline)
            if logDiscipline == []:
                data = json.dumps(donnees)
                base_url = reverse('import_csv_disciplines')
                query_string = urlencode({'data': data})
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
    return render(request, 'bulletins/csv/import_csv.html', context={'formEleve': formEleve,'formDiscipline': formDiscipline,'formStage':formStage,'formProjet':formProjet,'formAppreciation':formAppreciation, 'logEleve': logEleve,'logDiscipline': logDiscipline,'logAppreciation': logAppreciation,'logProjet': logProjet,'logStage': logStage,'annee_en_cours':annee_en_cours})

def import_stage_csv(request):
    logError = []
    ligneProblemes = []
    if 'data' in request.GET.keys():
        donnees = json.loads(request.GET.get('data'))
        logError, ligneProblemes = tools.validationStageImportation(donnees)
    if request.method == 'POST':
        if logError == []:
            log = tools.importationStage(donnees=donnees)
            info = models.Journal(utilisateur=request.user, message=f'''Importation de stages''')
            info.save()
            return render(request, 'bulletins/csv/import_report.html', context={'log': log})
    else:
        return render(request, 'bulletins/csv/import_csv_stage.html',
                      context={'logError': logError, 'ligneProblemes': ligneProblemes})

def import_projet_csv(request):
    logError = []
    ligneProblemes = []
    if 'data' in request.GET.keys():
        donnees = json.loads(request.GET.get('data'))
        logError, ligneProblemes = tools.validationProjetImportation(donnees)
    if request.method == 'POST':
        if logError == []:
            log = tools.importationProjet(donnees=donnees)
            info = models.Journal(utilisateur=request.user, message=f'''Importation de projets''')
            info.save()
            return render(request, 'bulletins/csv/import_report.html', context={'log': log})
    else:
        return render(request, 'bulletins/csv/import_csv_projet.html',
                      context={'logError': logError, 'ligneProblemes': ligneProblemes})

def import_appreciation_csv(request):
    logError = []
    ligneProblemes = []
    if 'data' in request.GET.keys():
        donnees = json.loads(request.GET.get('data'))
        logError, ligneProblemes = tools.validationAppreciationImportation(donnees)
    if request.method == 'POST':
        if logError == []:
            log = tools.importationAppreciation(donnees=donnees)
            info = models.Journal(utilisateur=request.user, message=f'''Importation d'appréciations''')
            info.save()
            return render(request, 'bulletins/csv/import_report.html', context={'log': log})
    else:
        return render(request, 'bulletins/csv/import_csv_appreciation.html',
                      context={'logError': logError, 'ligneProblemes': ligneProblemes})

def import_discipline_csv(request):
    logError=[]
    ligneProblemes=[]
    if 'data' in request.GET.keys():
        donnees = json.loads(request.GET.get('data'))
        logError, ligneProblemes = tools.validationDisciplineImportation(donnees)
    if request.method=='POST':
        if logError == []:
            log=tools.importationDiscipline(donnees=donnees)
            info = models.Journal(utilisateur=request.user, message=f'''Importation de disciplines''')
            info.save()
            return render(request,'bulletins/csv/import_report.html',context={'log':log})
    else :
        return render(request,'bulletins/csv/import_csv_discipline.html',context={'logError':logError,'ligneProblemes':ligneProblemes})

def import_eleve_csv(request):
    logError=[]
    ligneProblemes=[]
    classesACreer=[]
    elevesACreer=[]
    if 'data' in request.GET.keys():
        donnees = json.loads(request.GET.get('data'))
        logError, ligneProblemes, classesACreer, elevesACreer = tools.validationEleveImportation(donnees)
    if request.method=='POST':
        if logError == []:
            log=tools.importationEleve(donnees=donnees)
            info = models.Journal(utilisateur=request.user, message=f'''Importation d'élèves''')
            info.save()
            return render(request,'bulletins/csv/import_report.html',context={'log':log})
    else :
        return render(request,'bulletins/csv/import_csv_eleve.html',context={'logError':logError,'ligneProblemes':ligneProblemes,'classesACreer':classesACreer,'elevesACreer':elevesACreer})

#Vues disciplines

@login_required
@permission_required('bulletins.view_discipline')
def disciplines_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actif=trimestres.filter(edition=True)
    disciplines=models.Discipline.objects.filter(trimestre__in=trimestres).order_by('-trimestre')
    return render(request,'bulletins/discipline/discipline_list.html',context={'disciplines':disciplines,'annee_en_cours':annee_en_cours,'trimestres_actif':trimestres_actif})

@login_required
@permission_required('bulletins.view_discipline')
def my_disciplines_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actif=trimestres.filter(edition=True)
    disciplines=models.Discipline.objects.filter(trimestre__in=trimestres_actif).order_by('-trimestre').filter(enseigneePar=request.user)
    return render(request,'bulletins/discipline/my_discipline_list.html',context={'disciplines':disciplines,'annee_en_cours':annee_en_cours,'trimestres_actif':trimestres_actif})

@login_required
@permission_required('bulletins.admin_discipline')
def disciplines_list_admin(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours)
    disciplines = models.Discipline.objects.filter(trimestre__in=trimestres).order_by('-id')
    return render(request,'bulletins/discipline/discipline_list_admin.html',context={'annee_en_cours':annee_en_cours,'disciplines':disciplines})

@login_required
@permission_required('bulletins.view_discipline')
def disciplineEleve_detail(request,idDiscipline):
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    eleves=discipline.enseigneeA.all()
    return render(request,'bulletins/discipline/discipline_eleve_detail.html',context={'discipline':discipline,'eleves':eleves})

@login_required
@permission_required('bulletins.add_discipline')
def discipline_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method=='POST':
        form=forms.MyDisciplineForm(request.POST)
        if form.is_valid():
            discipline = form.save()
            discipline.enseigneePar.add(request.user)
            eleves = models.Eleve.objects.filter(classe__in=discipline.enseigneeDans.all())
            for eleve in eleves :
                discipline.enseigneeA.add(eleve)
            discipline.calculEffectifs()
            discipline.save()
            info = models.Journal(utilisateur=request.user, message=f'''Création enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
            info.save()
            return redirect('my_disciplines_liste')
        else :
            return render(request, 'bulletins/discipline/discipline_add.html', context={'form':form})
    form = forms.MyDisciplineForm(user=request.user.username)
    return render(request,'bulletins/discipline/discipline_add.html',context={'form':form,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_discipline')
def discipline_change(request,idDiscipline):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    discipline=models.Discipline.objects.get(id=idDiscipline)
    competences = models.CompetencesConnaissances.objects.filter(discipline=discipline)
    if request.method == 'POST':
        if 'edit_competence' in request.POST:
            form = forms.CompetencesConnaissancesForm(request.POST)
            if form.is_valid():
                competence_connaissance = form.save(commit=False)
                competence_connaissance.discipline = discipline
                competence_connaissance.save()
            return redirect('discipline_change', idDiscipline)

        if 'edit_discipline' in request.POST :
            if 'admin' in request.path:
                form = forms.MyDisciplineChangeForm(request.POST, instance=discipline)
                if form.is_valid():
                    discipline = form.save()
                    info = models.Journal(utilisateur=request.user,
                                          message=f'''Modification (admin) enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
                    info.save()
                return redirect('discipline_change', idDiscipline)
            else :
                form = forms.MyDisciplineChangeForm(request.POST, instance=discipline, user=request.user.username)
                if form.is_valid():
                    discipline = form.save()
                    discipline.enseigneePar.add(request.user)
                    info = models.Journal(utilisateur=request.user,
                                          message=f'''Modification enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
                    info.save()
                return redirect('discipline_change', idDiscipline)
    else :
        formComp = forms.CompetencesConnaissancesForm()
        if 'admin' in request.path:
            form = forms.MyDisciplineChangeForm(instance=discipline)
        else :
            form = forms.MyDisciplineChangeForm(user=request.user.username, instance=discipline)
        return render(request, 'bulletins/discipline/discipline_change.html', context={'form': form,'formComp': formComp,'discipline':discipline,'annee_en_cours':annee_en_cours,'competences':competences})


@login_required
@permission_required('bulletins.delete_discipline')
def discipline_delete(request,idDiscipline):
    discipline = models.Discipline.objects.get(id=idDiscipline)
    if 'admin' in request.path:
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression (admin) enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
        info.save()
        discipline.delete()
        return redirect('disciplines_liste_admin')
    else:
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
        info.save()
        discipline.delete()
        return redirect('disciplines_liste')

@login_required
@permission_required('bulletins.view_discipline')
def discipline_detail(request,idDiscipline):
    discipline = get_object_or_404(models.Discipline, id=idDiscipline)
    appreciations=models.Appreciation.objects.filter(discipline=discipline)
    competences = models.CompetencesConnaissances.objects.filter(discipline=discipline)
    competencesAppreciations=models.CompetencesAppreciations.objects.filter(appreciation__in=appreciations)
    return render(request, 'bulletins/discipline/discipline_detail.html',context={'discipline': discipline, 'competences': competences,'appreciations':appreciations,'competencesAppreciations':competencesAppreciations})

@login_required
@permission_required('bulletins.view_discipline')
def disciplineEleve_change(request,idDiscipline):
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    if request.method == 'POST':
        form=forms.MyDisciplineChangeEleveForm(request.POST, instance=discipline)
        if form.is_valid():
            discipline=form.save()
            discipline.save()
            eleves=discipline.enseigneeA.all()
            appreciations = models.Appreciation.objects.filter(discipline=discipline).exclude(eleve__in=eleves)
            appreciations.delete()
            if 'admin' in request.path:
                info = models.Journal(utilisateur=request.user,
                                      message=f'''Modification (admin) effectifs enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
                info.save()
            else :
                info = models.Journal(utilisateur=request.user,
                                      message=f'''Modification effectifs enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
                info.save()
        if 'admin' in request.path:
            return redirect('disciplines_liste_admin')
        else:
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Modification effectifs enseignement {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
            info.save()
            return redirect('my_disciplines_liste')
    else :
        classes=discipline.enseigneeDans.all()
        form = forms.MyDisciplineChangeEleveForm(instance=discipline, classes=classes)
        return render (request,'bulletins/discipline/discipline_eleve_change.html',context={'discipline':discipline,'form':form,})


@login_required
@permission_required('bulletins.change_discipline')
def discipline_evaluate(request,idDiscipline):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    notice=models.Bareme.objects.filter(defaut=True).first()
    #On récupère la liste de tous les élèves inscrits dans cette enseignement
    eleves=discipline.enseigneeA.all()
    #On leur créé une appréciation vierge si elle n'existe pas déjà
    for eleve in eleves :
        appreciation, _= models.Appreciation.objects.get_or_create(eleve=eleve,discipline=discipline)
    #On récupère toutes les appréciations qui existent vis-à-vis de cette discipline
    appreciations=models.Appreciation.objects.filter(discipline=discipline)
    #si dans ces appréciations, certaines sont affectées à des élèves qui ne font plus partie des élèves inscrits, on les supprime...
    for appreciation in appreciations :
        if appreciation.eleve not in eleves :
            appreciation.delete()
    #On reconstitue la bonne liste des appréciations pour la suite;
    appreciations=models.Appreciation.objects.filter(eleve__in=eleves,discipline=discipline)

    #On génére également les éléments de compétences associés
    competencesAppreciations=models.CompetencesConnaissances.objects.filter(discipline=discipline)
    for appreciation in appreciations :
        for elementCompetence in competencesAppreciations :
            if elementCompetence not in appreciation.competencesConnaissances.all():
                appreciation.competencesConnaissances.add(elementCompetence)

    #On supprime ceux qui ne sont plus d'actualité
    for appreciation in appreciations :
        for elementCompetence in appreciation.competencesConnaissances.all() :
            if elementCompetence not in competencesAppreciations :
                appreciation.competencesConnaissances.delete(elementCompetence)

    #On construit les formulaires hybrides pour les injecter dans le template
    #Pour chaque élève : son appréciation, les éléments de compétences associés
    liste_formulaires=[]

    for eleve in eleves :
        forms_eleve=[]
        forms_eleve.append(eleve)

        appreciation=models.Appreciation.objects.get(eleve=eleve,discipline=discipline)
        competences=models.CompetencesAppreciations.objects.filter(appreciation=appreciation)

        form_appreciation = forms.AppreciationForm(instance=appreciation)
        forms_eleve.append(form_appreciation)
        #Créer un formset pour les lots de compétences
        CompetencesFormset = modelformset_factory(models.CompetencesAppreciations,
                                                  forms.CompetencesAppreciationForm,
                                                  edit_only=True, extra=0)
        formset = CompetencesFormset(queryset=competences)
        forms_eleve.append(formset)

        liste_formulaires.append(forms_eleve)

    if request.method == 'POST':
        #Pour chaque élève on rassemble les données contenues dans la requête
        for eleve,i in zip(eleves,range(len(eleves))) :
            list_appreciation=['attitude','engagement','resultat','commentaire','note']
            data={}
            for valeur in list_appreciation:
                data[valeur]=request.POST.getlist(valeur)[i]
            data['eleve']=eleve
            appreciation_old = models.Appreciation.objects.get(discipline=discipline,eleve=eleve)
            appreciation_form = forms.AppreciationForm(data,instance=appreciation_old)
            if appreciation_form.is_valid():
                appreciation=appreciation_form.save()

            #Même procédé pour gérer cette fois l'évaluation des competences associées à la discipline
            competenceConnaissances = models.CompetencesConnaissances.objects.filter(discipline=discipline)
            for competenceConnaissance,j in zip(competenceConnaissances,range(len(competenceConnaissances.all()))):
                #for j in range(int(request.POST.getlist('form-TOTAL_FORMS')[i])):
                #idCompetenceConnaissance = int(request.POST.getlist(f'form-{j}-competence')[i])
                new_data={}
                #competenceConnaissance = get_object_or_404(models.CompetencesConnaissances,id=idCompetenceConnaissance)
                new_data['competence']= competenceConnaissance
                new_data['evaluation']=request.POST.getlist(f'form-{j}-evaluation')[i]
                new_data['appreciation']=appreciation
                competence_old = models.CompetencesAppreciations.objects.get(appreciation=appreciation,competence=competenceConnaissance)
                competence_form = forms.CompetencesAppreciationForm(new_data,instance=competence_old)
                if competence_form.is_valid():
                    competence_form.save()
        discipline.save()
        info = models.Journal(utilisateur=request.user,
                              message=f'''Modification évaluations {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
        info.save()
        if 'admin' in request.path:
            return redirect('discipline_admin_evaluate',idDiscipline)
        else :
            return redirect('discipline_evaluate', idDiscipline)
    else:
        return render(request, 'bulletins/discipline/discipline_evaluate.html',
                      context={'eleves':eleves,
                               'discipline':discipline,
                               'liste_formulaires':liste_formulaires,
                               'bareme':notice,
                               'annee_en_cours':annee_en_cours})

#Gestion des projets
@login_required
@permission_required('bulletins.view_projet')
def projets_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actifs=trimestres.filter(edition=True)
    projets=models.Projet.objects.filter(trimestre__in=trimestres).order_by('-trimestre','eleve')
    return render(request,'bulletins/projets/projets_list.html',context={'annee_en_cours':annee_en_cours,'projets':projets,'trimestres_actif':trimestres_actifs})

@login_required
@permission_required('bulletins.view_projet')
def my_projets_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actifs=trimestres.filter(edition=True)
    projets=models.Projet.objects.filter(trimestre__in=trimestres_actifs).order_by('-trimestre','eleve').filter(tuteur=request.user)
    return render(request,'bulletins/projets/my_projets_list.html',context={'annee_en_cours':annee_en_cours,'projets':projets,'trimestres_actif':trimestres_actifs})

@login_required
#TODO : créer permission admin_projet (comme discipline)
def projets_admin_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours)
    projets = models.Projet.objects.filter(trimestre__in=trimestres).order_by('eleve', 'trimestre')
    return render(request, 'bulletins/projets/projets_admin_list.html',context={'annee_en_cours': annee_en_cours, 'projets': projets})


@login_required
@permission_required('bulletins.add_projet')
def projets_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method == 'POST':
        form=forms.ProjectAddForm(request.POST)
        if form.is_valid():
            projet=form.save()
            projet.tuteur=request.user
            projet.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Ajout projet : {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
            info.save()
        return redirect('my_projets_liste')
    else :
        form=forms.ProjectAddForm(user=request.user.username)
        return render(request,'bulletins/projets/projets_add.html',context={'annee_en_cours':annee_en_cours,'form':form})

@login_required
@permission_required('bulletins.change_projet')
def projets_change(request,idProjet):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    projet=get_object_or_404(models.Projet,id=idProjet)
    if request.method == 'POST':
        form=forms.ProjetChangeForm(request.POST,instance=projet)
        if form.is_valid():
            projet=form.save()
            if 'admin' in request.path:
                message=f'''Modification (admin) projet : {projet.typeProjet} {projet.eleve} {projet.trimestre}'''
            else :
                message=f'''Modification projet : {projet.typeProjet} {projet.eleve} {projet.trimestre}'''
            info = models.Journal(utilisateur=request.user,message=message)
            info.save()
        if 'admin' in request.path :
            return redirect('projets_admin_liste')
        else :
            return redirect('my_projets_liste')
    else :
        if 'admin' in request.path :
            form=forms.ProjetChangeForm(instance=projet)
        else :
            form=forms.ProjetChangeForm(instance=projet,user=request.user.username)
        return render(request,'bulletins/projets/projets_change.html',context={'annee_en_cours':annee_en_cours,'form':form,'projet':projet})


@login_required
@permission_required('bulletins.delete_projet')
def projets_delete(request,idProjet):
    projet=get_object_or_404(models.Projet,id=idProjet)
    if 'admin' in request.path:
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression (admin) projet : {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
        info.save()
        projet.delete()
        return redirect('projets_admin_liste')
    else :
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression projet : {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
        info.save()
        projet.delete()
        return redirect('projets_liste')

#Gestion des stages

@login_required
@permission_required('bulletins.view_stage')
def stages_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actifs=trimestres.filter(edition=True)
    stages=models.Stage.objects.filter(trimestre__in=trimestres).order_by('-trimestre','eleve')
    return render(request,'bulletins/stages/stages_list.html',context={'annee_en_cours':annee_en_cours,'stages':stages,'trimestres_actif':trimestres_actifs})

@login_required
@permission_required('bulletins.view_stage')
def my_stages_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours)
    trimestres_actifs=trimestres.filter(edition=True)
    stages=models.Stage.objects.filter(trimestre__in=trimestres_actifs).order_by('-trimestre','eleve').filter(tuteur=request.user)
    return render(request,'bulletins/stages/my_stages_list.html',context={'annee_en_cours':annee_en_cours,'stages':stages,'trimestres_actif':trimestres_actifs})

@login_required
#TODO : créer permission admin_stage (comme discipline)
def stages_admin_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours)
    stages = models.Stage.objects.filter(trimestre__in=trimestres).order_by('eleve', 'trimestre')
    return render(request, 'bulletins/stages/stages_admin_list.html',context={'annee_en_cours': annee_en_cours, 'stages': stages})


@login_required
@permission_required('bulletins.add_stage')
def stages_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method == 'POST':
        form=forms.StageAddForm(request.POST)
        if form.is_valid():
            stage=form.save()
            stage.tuteur=request.user
            stage.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Ajout stage : {stage.typeStage} {stage.eleve} {stage.trimestre}''')
            info.save()
        return redirect('my_stages_liste')
    else :
        form=forms.StageAddForm(user=request.user.username)
        return render(request,'bulletins/stages/stages_add.html',context={'annee_en_cours':annee_en_cours,'form':form})

@login_required
@permission_required('bulletins.change_stage')
def stages_change(request,idStage):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    stage=get_object_or_404(models.Stage,id=idStage)
    if request.method == 'POST':
        form=forms.StageChangeForm(request.POST,instance=stage)
        if form.is_valid():
            stage=form.save()
            if 'admin' in request.path:
                message=f'''Modification (admin) stage : {stage.typeStage} {stage.eleve} {stage.trimestre}'''
            else :
                message=f'''Modification stage : {stage.typeStage} {stage.eleve} {stage.trimestre}'''
            info = models.Journal(utilisateur=request.user,message=message)
            info.save()
        if 'admin' in request.path :
            return redirect('stages_admin_liste')
        else :
            return redirect('my_stages_liste')
    else :
        if 'admin' in request.path :
            form=forms.StageChangeForm(instance=stage)
        else :
            form=forms.StageChangeForm(instance=stage,user=request.user.username)
        return render(request,'bulletins/stages/stages_change.html',context={'annee_en_cours':annee_en_cours,'form':form,'stage':stage})


@login_required
@permission_required('bulletins.delete_stage')
def stages_delete(request,idStage):
    stage=get_object_or_404(models.Stage,id=idStage)
    if 'admin' in request.path:
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression (admin) stage : {stage.typeStage} {stage.eleve} {stage.trimestre}''')
        info.save()
        stage.delete()
        return redirect('stages_admin_liste')
    else :
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression stage : {stage.typeStage} {stage.eleve} {stage.trimestre}''')
        info.save()
        stage.delete()
        return redirect('stages_liste')

#Gestion des corrections
@login_required
@permission_required('bulletins.view_discipline')
def corrections_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres=models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    disciplines=models.Discipline.objects.filter(reluPar=request.user).filter(relectureActive=True).filter(trimestre__in=trimestres)
    stages=models.Stage.objects.filter(relecteur=request.user).filter(relectureActive=True).filter(trimestre__in=trimestres)
    projets=models.Projet.objects.filter(relecteur=request.user).filter(relectureActive=True).filter(trimestre__in=trimestres)
    return render(request,'bulletins/corrections/corrections_list.html',context={'disciplines':disciplines,'annee_en_cours':annee_en_cours,'stages':stages,'projets':projets})

@login_required
@permission_required('bulletins.change_stage')
def correction_stage_detail(request,idStage):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    stage = get_object_or_404(models.Stage, id=idStage)
    if request.method == 'POST':
        form = forms.StageCorrectionForm(request.POST, instance=stage)
        if form.is_valid():
            stage=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Correction stage {stage.typeStage} {stage.eleve} {stage.trimestre}''')
            info.save()
        return redirect('corrections_liste')

    else :
        form = forms.StageCorrectionForm(instance=stage)
        return render(request,'bulletins/corrections/correction_stage_detail.html',context={'stage':stage,'form':form,'annee_en_cours':annee_en_cours})


@login_required
@permission_required('bulletins.change_projet')
def correction_projet_detail(request,idProjet):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    projet = get_object_or_404(models.Projet, id=idProjet)
    if request.method == 'POST':
        form = forms.ProjetCorrectionForm(request.POST, instance=projet)
        if form.is_valid():
            projet=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Correction projet {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
            info.save()
        return redirect('corrections_liste')

    else :
        form = forms.ProjetCorrectionForm(instance=projet)
        return render(request,'bulletins/corrections/correction_projet_detail.html',context={'projet':projet,'form':form,'annee_en_cours':annee_en_cours})


@login_required
@permission_required('bulletins.change_discipline')
def correction_discipline_detail(request,idDiscipline):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    competencesConnaissances = models.CompetencesConnaissances.objects.filter(discipline=discipline)
    appreciations=models.Appreciation.objects.filter(discipline=discipline).exclude(commentaire='')
    competencesAppreciations=models.CompetencesAppreciations.objects.filter(appreciation__in=appreciations)
    CompetenceCorrectionsFormSet = modelformset_factory(models.CompetencesConnaissances, forms.CompetencesConnaissancesCorrectionForm, edit_only=True, extra=0)
    AppreciationsCorrectionsFormset=modelformset_factory(models.Appreciation,forms.AppreciationCorrectionForm,edit_only=True, extra=0)
    if request.method == 'POST':
        form=forms.DisciplineCorrectionForm(request.POST,instance=discipline)
        formset_competence = CompetenceCorrectionsFormSet(request.POST,prefix="competences",queryset=competencesConnaissances)
        formset_appreciations = AppreciationsCorrectionsFormset(request.POST,prefix="appreciations",queryset=appreciations)
        if formset_competence.is_valid():
            for form_competence in formset_competence :
                form_competence.save()
        if formset_appreciations.is_valid():
            for form_appreciation in formset_appreciations :
                form_appreciation.save()
        if form.is_valid():
            discipline=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Correction {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
            info.save()
        return redirect('correction_discipline_detail',idDiscipline)
    else :
        form = forms.DisciplineCorrectionForm(instance=discipline)
        formset_competence = CompetenceCorrectionsFormSet(prefix="competences",queryset=competencesConnaissances)
        formset_appreciations = AppreciationsCorrectionsFormset(prefix="appreciations",queryset=appreciations)
        return render(request,'bulletins/corrections/correction_detail.html',context={'discipline':discipline,'form':form,'formset_competence':formset_competence,'formset_appreciations':formset_appreciations,'competencesConnaissances':competencesConnaissances,'competencesAppreciations':competencesAppreciations,'appreciations':appreciations,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.admin_discipline')
def admin_corrections_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    disciplines = models.Discipline.objects.filter(Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    stages=models.Stage.objects.filter(Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    projets=models.Projet.objects.filter(Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    return render(request,'bulletins/corrections/corrections_admin_list.html',context={'disciplines':disciplines,'stages':stages,'projets':projets,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.view_discipline')
def my_corrections_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    disciplines = models.Discipline.objects.filter(Q(enseigneePar=request.user) & Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    stages = models.Stage.objects.filter(Q(tuteur=request.user) & Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    projets = models.Projet.objects.filter(Q(tuteur=request.user) & Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    return render(request,'bulletins/corrections/my_corrections_list.html',context={'disciplines':disciplines,'stages':stages,'projets':projets,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_stage')
def my_correction_stage_detail(request,idStage):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    stage=get_object_or_404(models.Stage,id=idStage)
    if request.method=='POST':
        form = forms.StageCorrectionForm(request.POST, instance=stage)
        if form.is_valid():
            stage = form.save()
            if stage.descriptif_correction != '' and stage.descriptif_correction != None:
                stage.descriptif = stage.descriptif_correction
                stage.descriptif_correction = None
            if stage.appreciation_correction != '' and stage.appreciation_correction != None:
                stage.appreciation = stage.appreciation_correction
                stage.appreciation_correction = None
            if stage.remarque_correction != '' and stage.remarque_correction != None:
                stage.remarque_correction = None
            stage.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Validation corrections stage {stage.typeStage} {stage.eleve} {stage.trimestre}''')
            info.save()
        if 'admin' in request.path:
            return redirect('corrections_admin_liste')
        else:
            return redirect('my_corrections_liste')
    else :
        form = forms.StageCorrectionForm(instance=stage)
        return render(request,'bulletins/corrections/my_correction_stage_detail.html',context={'stage':stage,'form':form,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_projet')
def my_correction_projet_detail(request,idProjet):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    projet=get_object_or_404(models.Projet,id=idProjet)
    if request.method=='POST':
        form = forms.ProjetCorrectionForm(request.POST,instance=projet)
        if form.is_valid():
            projet = form.save()
            if projet.descriptif_correction != '' and projet.descriptif_correction != None :
                projet.descriptif = projet.descriptif_correction
                projet.descriptif_correction = None
            if projet.titre_correction != '' and projet.titre_correction != None :
                projet.titre = projet.titre_correction
                projet.titre_correction = None
            if projet.appreciation_correction != '' and projet.appreciation_correction != None :
                projet.appreciation = projet.appreciation_correction
                projet.appreciation_correction = None
            if projet.remarque_correction != '' and projet.remarque_correction != None :
                projet.remarque_correction=None
            projet.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Validation corrections projet {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
            info.save()
        if 'admin' in request.path :
            return redirect('corrections_admin_liste')
        else :
            return redirect('my_corrections_liste')
    else :
        form = forms.ProjetCorrectionForm(instance=projet)
        return render(request,'bulletins/corrections/my_correction_projet_detail.html',context={'projet':projet,'form':form,'annee_en_cours':annee_en_cours})

@login_required
@permission_required('bulletins.change_discipline')
def my_correction_discipline_detail(request,idDiscipline):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    appreciations=models.Appreciation.objects.filter(discipline=discipline).exclude(commentaire_correction__isnull=True,remarque_correction__isnull=True).exclude(commentaire_correction__exact='',remarque_correction__exact='')
    competencesAppreciations=models.CompetencesAppreciations.objects.filter(appreciation__in=appreciations)
    competencesConnaissances = models.CompetencesConnaissances.objects.filter(discipline=discipline)
    CompetenceCorrectionsFormSet = modelformset_factory(models.CompetencesConnaissances, forms.CompetencesConnaissancesCorrectionForm, edit_only=True,extra=0)
    AppreciationsCorrectionsFormset = modelformset_factory(models.Appreciation, forms.AppreciationCorrectionForm,edit_only=True, extra=0)
    if request.method=="POST":
        form = forms.DisciplineCorrectionForm(request.POST, instance=discipline)
        formset_competence = CompetenceCorrectionsFormSet(request.POST, prefix="competences",
                                                          queryset=competencesConnaissances)
        formset_appreciations = AppreciationsCorrectionsFormset(request.POST, prefix="appreciations",
                                                                queryset=appreciations)
        if formset_competence.is_valid():
            for form_competence in formset_competence:
                competence=form_competence.save()
                if competence.intitule_correction != '' and competence.intitule_correction != None:
                    competence.intitule=competence.intitule_correction
                    competence.intitule_correction=None
                    competence.save()
        if formset_appreciations.is_valid():
            for form_appreciation in formset_appreciations:
                appreciation=form_appreciation.save()
                if appreciation.commentaire_correction != '' and appreciation.commentaire_correction != None:
                    appreciation.commentaire=appreciation.commentaire_correction
                    appreciation.commentaire_correction=None
                    appreciation.save()
                if appreciation.remarque_correction != '' and appreciation.remarque_correction != None :
                    appreciation.remarque_correction=None
        if form.is_valid():
            discipline=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Validation corrections {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
            info.save()
            if discipline.remarque_correction != '' and discipline.remarque_correction != None:
                discipline.remarque_correction=None
            if discipline.titre_correction != '' and discipline.titre_correction != None:
                discipline.titre=discipline.titre_correction
                discipline.titre_correction=None
                discipline.save()
            if discipline.descriptif_correction != '' and discipline.descriptif_correction != None :
                discipline.descriptif = discipline.descriptif_correction
                discipline.descriptif_correction=None
                discipline.save()
        if 'admin' in request.path :
            return redirect('corrections_admin_liste')
        else :
            return redirect('my_corrections_liste')

    else :
        form = forms.DisciplineCorrectionForm(instance=discipline)
        formset_competence = CompetenceCorrectionsFormSet(prefix="competences", queryset=competencesConnaissances)
        formset_appreciations = AppreciationsCorrectionsFormset(prefix="appreciations", queryset=appreciations)
        return render(request,'bulletins/corrections/my_correction_detail.html',context={'discipline':discipline,'form':form,'formset_competence':formset_competence,'formset_appreciations':formset_appreciations,'annee_en_cours':annee_en_cours,'competencesConnaissances':competencesConnaissances,'competencesAppreciations':competencesAppreciations,'appreciations':appreciations})

@login_required
@permission_required('bulletins.view_discipline')
def corrections_list_admin(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    trimestres = models.Trimestre.objects.filter(annee=annee_en_cours).filter(edition=True)
    disciplines = models.Discipline.objects.filter(Q(trimestre__in=trimestres) & Q(correctionsAValider=True))
    return render(request, 'bulletins/corrections/corrections_admin_list.html',context={'disciplines': disciplines, 'annee_en_cours': annee_en_cours})

@login_required
@permission_required('bulletins.change_stage')
def my_correction_stage_delete(request,idStage):
    stage=get_object_or_404(models.Stage,id=idStage)
    stage.descriptif_correction=None
    stage.appreciation_correction=None
    stage.remarque_correction=None
    stage.save()
    info = models.Journal(utilisateur=request.user,
                          message=f'''Invalidation corrections stage {stage.typeStage} {stage.eleve} {stage.trimestre}''')
    info.save()
    if 'admin' in request.path :
        return redirect('corrections_admin_liste')
    else :
        return redirect('my_corrections_liste')

@login_required
@permission_required('bulletins.change_projet')
def my_correction_projet_delete(request,idProjet):
    projet=get_object_or_404(models.Projet,id=idProjet)
    projet.titre_correction = None
    projet.descriptif_correction=None
    projet.appreciation_correction=None
    projet.remarque_correction = None
    projet.save()
    info = models.Journal(utilisateur=request.user,
                          message=f'''Invalidation corrections projet {projet.typeProjet} {projet.eleve} {projet.trimestre}''')
    info.save()
    if 'admin' in request.path :
        return redirect('corrections_admin_liste')
    else :
        return redirect('my_corrections_liste')


@login_required
@permission_required('bulletins.change_discipline')
def my_correction_discipline_delete(request,idDiscipline):
    discipline = get_object_or_404(models.Discipline, id=idDiscipline)
    appreciations = models.Appreciation.objects.filter(discipline=discipline).exclude(commentaire_correction__isnull=True,remarque_correction__isnull=True).exclude(commentaire_correction__exact='',remarque_correction__exact='')
    competencesConnaissances = models.CompetencesConnaissances.objects.filter(discipline=discipline).exclude(intitule_correction__isnull=True).exclude(intitule_correction__exact='')
    for appreciation in appreciations :
        appreciation.commentaire_correction=None
        appreciation.remarque_correction = None
        appreciation.save()
    for competence in competencesConnaissances :
        competence.intitule_correction=None
        competence.save()
    discipline.titre_correction = None
    discipline.remarque_correction = None
    discipline.descriptif_correction = None
    discipline.save()
    info = models.Journal(utilisateur=request.user,
                          message=f'''Invalidation corrections {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
    info.save()
    if 'admin' in request.path :
        return redirect('corrections_admin_liste')
    else :
        return redirect('my_corrections_liste')

@login_required
#TODO : définir les bonnes permissions...
def journal_list(request):
    lignes=models.Journal.objects.all().order_by('-date')
    return render(request, 'bulletins/journal/journal_list.html',context={"lignes": lignes})

def journal_delete(request):
    lignes = models.Journal.objects.all()
    for ligne in lignes :
        ligne.delete()
    info = models.Journal(utilisateur=request.user,
                          message=f'''RAZ Journal''')
    info.save()
    return redirect('journal_list')


@login_required
@permission_required('bulletins.add_competencesconnaissances')
def competence_connaissance_list(request,idDiscipline):
    discipline=get_object_or_404(models.Discipline,id = idDiscipline)
    competences = models.CompetencesConnaissances.objects.filter(discipline=discipline)
    if request.method == 'POST':
        form=forms.CompetencesConnaissancesForm(request.POST)
        if form.is_valid():
            competence_connaissance=form.save(commit=False)
            competence_connaissance.discipline = discipline
            competence_connaissance.save()
        if 'admin' in request.path:
            return redirect('competence_connaissance_admin_list', idDiscipline)
        else :
            return redirect('competence_connaissance_list',idDiscipline)
    else :
        form = forms.CompetencesConnaissancesForm()
        return render(request,'bulletins/competenceConnaissance/competenceConnaissance_list.html',context={"discipline":discipline,"competences":competences,'form':form})


@login_required
@permission_required('bulletins.change_competencesconnaissances')
def competence_connaissance_change(request,idDiscipline):
    discipline=get_object_or_404(models.Discipline,id=idDiscipline)
    competences_connaissances=models.CompetencesConnaissances.objects.filter(discipline=discipline)
    CompetenceConnaissanceFormSet=modelformset_factory(models.CompetencesConnaissances,forms.CompetencesConnaissancesForm,edit_only=True,extra=0)
    if request.method == 'POST':
        formset = CompetenceConnaissanceFormSet(request.POST, queryset=competences_connaissances)
        if formset.is_valid():
            for form in formset:
                competence_connaissance=form.save()
                info = models.Journal(utilisateur=request.user,
                                      message=f'''Modification compétences {discipline.intitule} {discipline.show_classes()} {discipline.trimestre}''')
                info.save()
        if 'admin' in request.path:
            return redirect('discipline_admin_change', idDiscipline)
        else:
            return redirect('discipline_change', idDiscipline)
    else :
        formset = CompetenceConnaissanceFormSet(queryset=competences_connaissances)
        return render(request,'bulletins/competenceConnaissance/competenceConnaissance_change.html',context={'formset': formset, 'discipline': discipline})

@login_required
@permission_required('bulletins.delete_competencesconnaissances')
def competence_connaissance_delete(request,idDiscipline,idCompetence):
    competence_connaissance=get_object_or_404(models.CompetencesConnaissances,id=idCompetence)
    if 'admin' in request.path:
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression (admin) compétence {competence_connaissance.discipline.intitule} {competence_connaissance.discipline.show_classes()} {competence_connaissance.discipline.trimestre}''')
        info.save()
        competence_connaissance.delete()
        return redirect('discipline_admin_change',idDiscipline)
    else :
        info = models.Journal(utilisateur=request.user,
                              message=f'''Suppression compétence {competence_connaissance.discipline.intitule} {competence_connaissance.discipline.show_classes()} {competence_connaissance.discipline.trimestre}''')
        info.save()
        competence_connaissance.delete()
        return redirect('discipline_change', idDiscipline)


#Production des bulletins

@login_required
def bulletins_select(request):
    models.ListBulletinScolaire.objects.all().delete()
    #On récupère les classes sélectionnées et on constitue un champ trimestre manuel
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    classes=models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')
    list_classes=[]
    log=[]
    formMiseEnForme=forms.BulletinMisEnForme()
    for classe in classes:
        form = forms.BulletinSelectEleves(classe = classe)
        list_classes.append([classe,form])
    if request.method=='POST':
        #Constitution d'une liste d'élèves
        liste_IdElevesStr = request.POST.getlist('eleves')
        list_IdEleves = []
        for classe in classes:
            if f"{classe.nom}entier" in request.POST:
                eleves=models.Eleve.objects.filter(classe=classe)
                for eleve in eleves :
                    list_IdEleves.append(eleve.id)
        for IdEleve in liste_IdElevesStr:
            list_IdEleves.append(int(IdEleve))
        if list_IdEleves != []:
            eleves = models.Eleve.objects.filter(id__in=list_IdEleves)
            liste_Trimestres = request.POST.getlist('trimestres')
            trimestres = models.Trimestre.objects.filter(intitule__in=liste_Trimestres).filter(annee=annee_en_cours)
            data = {'eleves': eleves, 'trimestres': trimestres}
            if 'signatureBulletin' in request.POST :
                data['signatureBulletin']=True
            if 'bulletinUtilisationCompetence' in request.POST :
                data['bulletinUtilisationCompetence']=True
            if 'bulletinAbsencesRetards' in request.POST :
                data['bulletinAbsencesRetards'] = True
            if 'bulletinNotice' in request.POST :
                data['bulletinNotice'] = True
            if 'admin' not in request.path:
                data['bulletinVersionProvisoire'] = True
            if 'bulletinVersionProvisoire' in request.POST :
                data['bulletinVersionProvisoire'] = True
            if 'bulletinAvisCollege' in request.POST :
                data['bulletinAvisCollege'] = True
            if 'miseEnPage' in request.POST :
                idMiseEnpage = request.POST.getlist('miseEnPage')
                if idMiseEnpage[0] != '':
                    miseEnPage=get_object_or_404(models.MiseEnPageBulletin,id=int(idMiseEnpage[0]))
                    data['miseEnPage']=miseEnPage
            bulletins_form = forms.BulletinsEdition(data)
            if bulletins_form.is_valid():
                bulletinsEdition = bulletins_form.save()
                info = models.Journal(utilisateur=request.user,
                                      message=f'''Édition bulletin''')
                info.save()
                return bulletinsEdition.produceBulletin()
            else :
                log.append("Sélectionnez au moins un trimestre.")
        else :
            log.append("Veuillez sélectionner au moins un élève !")
    return render(request,'bulletins/bulletin/bulletin_select.html',context={'list_classes':list_classes,'log':log,'annee_en_cours':annee_en_cours,'formMiseEnForme':formMiseEnForme})


def bareme_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    baremes=models.Bareme.objects.all()
    return render(request,'bulletins/bareme/bareme_list.html',context={'annee_en_cours':annee_en_cours,'baremes':baremes})

def bareme_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method=='POST':
        form=forms.BaremeForm(request.POST)
        if form.is_valid:
            bareme = form.save(commit=False)
            bareme.save(checkDefaut=True)
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Création notice {bareme.intitule}''')
            info.save()
        return redirect('bareme_list')
    else :
        form = forms.BaremeForm()
        return render(request, 'bulletins/bareme/bareme_add.html',context={'annee_en_cours': annee_en_cours, 'form': form})

def bareme_change(request,idBareme):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    bareme=get_object_or_404(models.Bareme,id=idBareme)
    if request.method == 'POST':
        form = forms.BaremeForm(request.POST,instance=bareme)
        if form.is_valid:
            bareme=form.save(commit=False)
            bareme.save(checkDefaut=True)
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Modification notice {bareme.intitule}''')
            info.save()
        return redirect('bareme_list')
    else:
        form = forms.BaremeForm(instance=bareme)
        return render(request, 'bulletins/bareme/bareme_change.html',
                      context={'annee_en_cours': annee_en_cours, 'form': form})

def bareme_delete(request,idBareme):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    bareme = get_object_or_404(models.Bareme, id=idBareme)
    info = models.Journal(utilisateur=request.user,
                          message=f'''Suppression notice {bareme.intitule}''')
    info.save()
    bareme.delete()
    return redirect('bareme_list')

#Vue relatives à la mise en page des bulletins
def mise_en_page_list(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    mise_en_pages=models.MiseEnPageBulletin.objects.all()
    return render(request,'bulletins/miseEnPage/mise_en_page_list.html',context={'annee_en_cours':annee_en_cours,'mise_en_pages':mise_en_pages})

def mise_en_page_add(request):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    if request.method=='POST':
        form=forms.MiseEnPageBulletinForm(request.POST)
        if form.is_valid:
            mise_en_page=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Création mise en page {mise_en_page.intitule}''')
            info.save()
        return redirect('mise_en_page_list')
    else :
        form = forms.MiseEnPageBulletinForm()
        return render(request,'bulletins/miseEnPage/mise_en_page_add.html',context={'annee_en_cours': annee_en_cours, 'form': form})

def mise_en_page_change(request,idMiseEnPage):
    annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
    mise_en_page=get_object_or_404(models.MiseEnPageBulletin,id=idMiseEnPage)
    if request.method == 'POST':
        form = forms.MiseEnPageBulletinForm(request.POST,instance=mise_en_page)
        if form.is_valid:
            mise_en_page=form.save()
            info = models.Journal(utilisateur=request.user,
                                  message=f'''Modification mise en page {mise_en_page.intitule}''')
            info.save()
        return redirect('mise_en_page_list')
    else:
        form = forms.MiseEnPageBulletinForm(instance=mise_en_page)
        return render(request,'bulletins/miseEnPage/mise_en_page_change.html',context={'annee_en_cours': annee_en_cours, 'form': form})

def mise_en_page_delete(request,idMiseEnPage):
    mise_en_page = get_object_or_404(models.MiseEnPageBulletin, id=idMiseEnPage)
    info = models.Journal(utilisateur=request.user,
                          message=f'''Suppression mise en page {mise_en_page.intitule}''')
    info.save()
    mise_en_page.delete()
    return redirect('mise_en_page_list')