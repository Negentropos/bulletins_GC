from django import forms
from django.contrib.auth import get_user_model
from . import models

class ClasseForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        Model = get_user_model()
        self.fields['tuteur'].queryset=Model.objects.exclude(is_active=False).exclude(role='INFO').order_by('last_name')

    edit_classe = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    class Meta:
        model = models.Classe
        exclude=('effectifs','annee')
        widgets={
            'nom': forms.TextInput(attrs={'placeholder': 'Nom'}),
            'tuteur': forms.CheckboxSelectMultiple(),
            'cycle': forms.Select(attrs={'placeholder': 'Cycle'}),
            #'annee': forms.Select(attrs={'placeholder': 'Année'}),
        }


class ClasseAddEleveForm(forms.ModelForm):
    classe_add_eleve = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    def __init__(self,*args,idClasse=None,**kwargs):
        super().__init__(*args,**kwargs)
        if idClasse :
            classe=models.Classe.objects.get(id=idClasse)
            self.fields['enseigneeA'].queryset=models.Eleve.objects.exclude(classe=classe)
            self.fields['enseigneeA'].label="Sélectionnez les élèves à ajouter"

    class Meta:
        model = models.Discipline
        fields=['enseigneeA']
        widgets={
            'enseigneeA': forms.CheckboxSelectMultiple(),
        }

class AvisCollegeAddForm(forms.ModelForm):
    def __init__(self, *args, user=None,**kwargs):
        super().__init__(*args, **kwargs)
        annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
        self.fields['trimestre'].queryset = models.Trimestre.objects.exclude(edition=False).filter(annee=annee_en_cours)
        if user:
            classes=models.Classe.objects.filter(tuteur=user).filter(annee=annee_en_cours)
        else : classes = models.Classe.objects.filter(annee=annee_en_cours)
        self.fields['eleve'].queryset = models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model = models.AvisCollege
        fields=['avis','eleve','trimestre']
        widgets={
            'trimestre':forms.Select(attrs={'placeholder': 'Trimestre'}),
            'eleve': forms.Select(attrs={'placeholder': 'Élève'}),
            'avis': forms.Textarea(attrs={'placeholder': 'Avis du collège', 'style': 'height: 200px'}),
        }

class AvisCollegeForm(forms.ModelForm):
    class Meta :
        model = models.AvisCollege
        exclude=['eleve','trimestre']
        widgets={
            'avis':forms.Textarea(attrs={'placeholder': 'Avis du collège','style':'height: 150px'}),
        }

class EleveForm(forms.ModelForm):

    def __init__(self,*args,annee_en_cours=None,**kwargs):
        super().__init__(*args,**kwargs)
        if annee_en_cours :
            self.fields['classe'].queryset=models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')

    def clean_emails_bulletin(self):
        """
        Valide que les adresses email sont correctement formatées.
        """
        emails = self.cleaned_data.get('emails_bulletin', '')
        if emails:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            email_list = [email.strip() for email in emails.split(',') if email.strip()]
            invalid_emails = []
            for email in email_list:
                if not re.match(email_pattern, email):
                    invalid_emails.append(email)
            if invalid_emails:
                raise forms.ValidationError(
                    f'Adresses email invalides : {", ".join(invalid_emails)}'
                )
        return emails

    class Meta:
        model = models.Eleve
        exclude=['actif',]
        widgets={
            'nom': forms.TextInput(attrs={'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'placeholder': 'Prenom'}),
            'dateNaissance': forms.DateInput(attrs={'placeholder': 'Date de naissance'}),
            'genre': forms.Select(attrs={'placeholder': 'Genre'}),
            'statut': forms.Select(attrs={'placeholder': 'Statut'}),
            'classe':forms.CheckboxSelectMultiple(),
            'emails_bulletin': forms.Textarea(attrs={'placeholder': 'email1@exemple.com, email2@exemple.com', 'rows': 3}),
        }


class AnneeForm(forms.ModelForm):
    edit_annee = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    class Meta:
        model = models.Annee
        fields=['intitule']
        widgets= {
            'intitule' : forms.TextInput(attrs={'placeholder': 'Intitulé'}),
        }

class TrimestreForm(forms.ModelForm):
    class Meta :
        model = models.Trimestre
        fields ='__all__'
        exclude=('annee','intitule',)
        widgets = {
            'dateDebut': forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFin': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
        }

class AbsenceForm(forms.ModelForm):
    class Meta :
        model = models.Absence
        exclude = ('eleve','trimestre','nbAbsenceTot')
        widgets={
            'nbAbsenceExc':forms.NumberInput(attrs={'max':"9999"}),
            'nbAbsenceNonExc':forms.NumberInput(attrs={'max':"9999"}),
            'nbRetard':forms.NumberInput(attrs={'max':"9999"}),
        }

class ImportCsvFileForm(forms.Form):
    file = forms.FileField()

class ImportCsvEleveFileForm(forms.Form):
    import_eleve = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    file = forms.FileField()

class ImportCsvAppreciationFileForm(forms.Form):
    import_appreciation = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    file = forms.FileField()

class ImportCsvDisciplineFileForm(forms.Form):
    import_discipline = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    file = forms.FileField()

class ImportCsvStageFileForm(forms.Form):
    import_stage = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    file = forms.FileField()

class ImportCsvProjetFileForm(forms.Form):
    import_projet = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    file = forms.FileField()

class DisciplineForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        Model = get_user_model()
        annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
        self.fields['enseigneePar'].queryset=Model.objects.exclude(is_active=False).exclude(role='INFO').order_by('last_name')
        self.fields['reluPar'].queryset = Model.objects.exclude(is_active=False).exclude(role='INFO').order_by('last_name')
        self.fields['enseigneeDans'].queryset = models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')
        self.fields['trimestre'].queryset = models.Trimestre.objects.filter(annee=annee_en_cours)

    class Meta:
        model = models.Discipline
        exclude=('enseigneeA','titre_correction','descriptif_correction','moyenne',)
        widgets= {
            'intitule': forms.TextInput(attrs={'placeholder': 'Intitulé'}),
            'intitule_court': forms.TextInput(attrs={'placeholder': 'Intitulé court'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif','style':'height: 150px'}),
            'dateDebut':forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFin': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
            'volumeHoraire': forms.NumberInput(attrs={'placeholder': 'Volume Horaire'}),
            'enseigneeDans': forms.CheckboxSelectMultiple(),

        }

class StageCorrectionForm(forms.ModelForm):
    class Meta:
        model = models.Stage
        fields =['descriptif_correction','appreciation_correction','remarque_correction']
        widgets={
            'descriptif_correction': forms.Textarea(attrs={'placeholder': 'descriptif','style':'height: 100px'}),
            'appreciation_correction': forms.Textarea(attrs={'placeholder': 'descriptif', 'style': 'height: 100px'}),
            'remarque_correction': forms.Textarea(attrs={'placeholder': 'remarque', 'style': 'height: 100px'}),
        }

class ProjetCorrectionForm(forms.ModelForm):
    class Meta:
        model = models.Projet
        fields =['titre_correction','descriptif_correction','appreciation_correction','remarque_correction']
        widgets={
            'titre_correction': forms.TextInput(attrs={'placeholder': 'titre'}),
            'descriptif_correction': forms.Textarea(attrs={'placeholder': 'descriptif','style':'height: 100px'}),
            'appreciation_correction': forms.Textarea(attrs={'placeholder': 'descriptif', 'style': 'height: 100px'}),
            'remarque_correction': forms.Textarea(attrs={'placeholder': 'remarque', 'style': 'height: 100px'}),
        }

class DisciplineCorrectionForm(forms.ModelForm):
    class Meta:
        model = models.Discipline
        fields =['titre_correction','descriptif_correction','remarque_correction']
        widgets={
            'titre_correction': forms.TextInput(attrs={'placeholder': 'titre'}),
            'descriptif_correction': forms.Textarea(attrs={'placeholder': 'descriptif','style':'height: 140px'}),
            'remarque_correction': forms.Textarea(attrs={'placeholder': 'remarque', 'style': 'height: 100px'}),
        }

class MyDisciplineChangeForm(forms.ModelForm):
    edit_discipline = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    #Une discipline déjà créée ne peut pas changer de classe ou de trimestre

    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        Model = get_user_model()
        if user :
            self.fields['enseigneePar'].queryset=Model.objects.exclude(username=user).exclude(is_active=False).exclude(role='INFO').order_by('last_name')
            self.fields['enseigneePar'].label="Ajouter des enseignants supplémentaires"
            self.fields['reluPar'].queryset = Model.objects.exclude(username=user).exclude(is_active=False).exclude(role='INFO').order_by('last_name')
        else :
            self.fields['enseigneePar'].queryset=Model.objects.exclude(is_active=False).exclude(role='INFO').order_by('last_name')
            self.fields['reluPar'].queryset = Model.objects.exclude(is_active=False).exclude(role='INFO').order_by('last_name')




    class Meta:
        model = models.Discipline
        exclude=('enseigneeA','titre_correction','descriptif_correction','enseigneeDans','trimestre')
        widgets= {
            'intitule': forms.TextInput(attrs={'placeholder': 'Intitulé'}),
            'intitule_court': forms.TextInput(attrs={'placeholder': 'Intitulé court'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif','style':'height: 100px'}),
            'dateDebut':forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFin': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
            'volumeHoraire': forms.NumberInput(attrs={'placeholder': 'Volume Horaire'}),
            'moyenne':forms.NumberInput(attrs={'readonly': True})
        }


class BaremeForm(forms.ModelForm):
    class Meta:
        model = models.Bareme
        fields='__all__'
        widgets= {
            'intitule': forms.TextInput(attrs={'placeholder': 'Intitulé'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'intro': forms.Textarea(attrs={'placeholder': 'Introduction', 'style': 'height: 120px'}),
            'attitude': forms.Textarea(attrs={'placeholder': 'Attitude', 'style': 'height: 75px'}),
            'engagement': forms.Textarea(attrs={'placeholder': 'Engagement', 'style': 'height: 75px'}),
            'resultat': forms.Textarea(attrs={'placeholder': 'Résultat', 'style': 'height: 75px'}),
            'attitudeA': forms.Textarea(attrs={'placeholder': 'Attitude A', 'style': 'height: 60px'}),
            'attitudeB': forms.Textarea(attrs={'placeholder': 'Attitude B', 'style': 'height: 60px'}),
            'attitudeC': forms.Textarea(attrs={'placeholder': 'Attitude C', 'style': 'height: 60px'}),
            'attitudeD': forms.Textarea(attrs={'placeholder': 'Attitude D', 'style': 'height: 60px'}),
            'engagementA': forms.Textarea(attrs={'placeholder': 'Engagement A', 'style': 'height: 60px'}),
            'engagementB': forms.Textarea(attrs={'placeholder': 'Engagement B', 'style': 'height: 60px'}),
            'engagementC': forms.Textarea(attrs={'placeholder': 'Engagement C', 'style': 'height: 60px'}),
            'engagementD': forms.Textarea(attrs={'placeholder': 'Engagement D', 'style': 'height: 60px'}),
            'resultatA': forms.Textarea(attrs={'placeholder': 'Résultat A', 'style': 'height: 60px'}),
            'resultatB': forms.Textarea(attrs={'placeholder': 'Résultat B', 'style': 'height: 60px'}),
            'resultatC': forms.Textarea(attrs={'placeholder': 'Résultat C', 'style': 'height: 60px'}),
            'resultatD': forms.Textarea(attrs={'placeholder': 'Résultat D', 'style': 'height: 60px'}),
            'piedPage': forms.Textarea(attrs={'placeholder': 'Pied de page', 'style': 'height: 60px'}),
        }
class MyDisciplineForm(forms.ModelForm):
    #Surcharge de la fonction init pour permettre d'exclure de certains champs du formulaire la valeur user

    def __init__(self,*args,user=None,trimestre=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user :
            Model = get_user_model()
            annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
            self.fields['enseigneePar'].queryset=Model.objects.exclude(username=user).exclude(is_active=False).exclude(role='INFO').order_by('last_name')
            self.fields['enseigneePar'].label="Ajouter des enseignants supplémentaires"
            self.fields['reluPar'].queryset = Model.objects.exclude(username=user).exclude(is_active=False).exclude(role='INFO').order_by('last_name')
            self.fields['enseigneeDans'].queryset = models.Classe.objects.filter(annee=annee_en_cours).order_by('nom')
            self.fields['trimestre'].queryset = models.Trimestre.objects.exclude(edition=False).filter(annee=annee_en_cours)
        if trimestre :
            self.fields['trimestre']=trimestre

    class Meta:
        model = models.Discipline
        exclude=('enseigneeA','titre_correction','descriptif_correction','moyenne')
        widgets= {
            'intitule': forms.TextInput(attrs={'placeholder': 'Intitulé'}),
            'intitule_court': forms.TextInput(attrs={'placeholder': 'Intitulé court'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif','style':'height: 150px'}),
            'dateDebut':forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFin': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
            'volumeHoraire': forms.NumberInput(attrs={'placeholder': 'Volume Horaire'}),
            'enseigneeDans': forms.CheckboxSelectMultiple(),
            'trimestre':forms.Select(attrs={'placeholder': 'Trimestre'}),
        }

class MyDisciplineChangeEleveForm(forms.ModelForm):
    def __init__(self,*args,classes=None,**kwargs):
        super().__init__(*args,**kwargs)
        #création d'un queryset qui limite le choix des élèves aux classes associées à l'enseignement
        if classes :
            self.fields['enseigneeA'].queryset = models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model = models.Discipline
        fields=['enseigneeA']
        widgets={
            'enseigneeA': forms.CheckboxSelectMultiple(),
        }

class MyDisciplineAddEleveForm(forms.ModelForm):
    def __init__(self,*args,classes=None,**kwargs):
        super().__init__(*args,**kwargs)
        if classes :
            self.fields['enseigneeA'].queryset = models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model = models.Discipline
        fields=['enseigneeA']
        widgets={
            'enseigneeA': forms.CheckboxSelectMultiple(),
        }


class ProjectAddForm(forms.ModelForm):
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user :
            Model = get_user_model()
            annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
            self.fields['relecteur'].queryset = Model.objects.exclude(username=user).exclude(role='INFO').exclude(is_active=False).order_by('last_name')
            self.fields['trimestre'].queryset = models.Trimestre.objects.exclude(edition=False).filter(annee=annee_en_cours)
            classes=models.Classe.objects.filter(annee=annee_en_cours)
            self.fields['eleve'].queryset=models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model=models.Projet
        exclude=('descriptif_correction','titre_correction','appreciation_correction','tuteur',)
        widgets = {
            'typeProjet': forms.Select(attrs={'placeholder': 'Type de projet'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif', 'style': 'height: 100px'}),
            'appreciation': forms.Textarea(attrs={'placeholder': 'Appreciation', 'style': 'height: 100px'}),
            'eleve': forms.Select(attrs={'placeholder': 'Élève'}),
            'trimestre': forms.Select(attrs={'placeholder': 'Trimestre'}),
            'relecteur': forms.Select(attrs={'placeholder': 'Relecteur'}),
        }



class ProjetChangeForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        Model = get_user_model()
        if user:
            self.fields['relecteur'].queryset = Model.objects.exclude(username=user).exclude(role='INFO').exclude(is_active=False).order_by('last_name')
        else :
            annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
            self.fields['relecteur'].queryset = Model.objects.exclude(role='INFO').exclude(is_active=False).order_by('last_name')
            self.fields['tuteur'].queryset = Model.objects.exclude(role='INFO').exclude(is_active=False).order_by('last_name')
            self.fields['trimestre'].queryset = models.Trimestre.objects.filter(annee=annee_en_cours)
            classes = models.Classe.objects.filter(annee=annee_en_cours)
            self.fields['eleve'].queryset = models.Eleve.objects.filter(classe__in=classes)


    class Meta:
        model=models.Projet
        exclude=('descriptif_correction','titre_correction','appreciation_correction')
        widgets = {
            'typeProjet': forms.Select(attrs={'placeholder': 'Type de projet'}),
            'titre': forms.TextInput(attrs={'placeholder': 'Titre'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif', 'style': 'height: 100px'}),
            'appreciation': forms.Textarea(attrs={'placeholder': 'Appreciation', 'style': 'height: 100px'}),
            'relecteur': forms.Select(attrs={'placeholder': 'Relecteur'}),
            'trimestre': forms.Select(attrs={'placeholder': 'Trimestre'}),
            'tuteur': forms.Select(attrs={'placeholder': 'Tuteur'}),
            'eleve': forms.Select(attrs={'placeholder': 'Élève'}),
        }

class StageAddForm(forms.ModelForm):

    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user :
            Model = get_user_model()
            annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
            self.fields['relecteur'].queryset = Model.objects.exclude(username=user).exclude(role='INFO').exclude(is_active=False).order_by('last_name')
            self.fields['trimestre'].queryset = models.Trimestre.objects.exclude(edition=False).filter(annee=annee_en_cours)
            classes = models.Classe.objects.filter(annee=annee_en_cours)
            self.fields['eleve'].queryset = models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model=models.Stage
        exclude=('descriptif_correction','appreciation_correction','tuteur','remarque_correction')
        widgets = {
            'typeStage': forms.Select(attrs={'placeholder': 'Type de stage'}),
            'lieuStage': forms.TextInput(attrs={'placeholder': 'Lieu de stage'}),
            'maitreStage': forms.TextInput(attrs={'placeholder': 'Maître de stage'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif', 'style': 'height: 100px'}),
            'appreciation': forms.Textarea(attrs={'placeholder': 'Appreciation', 'style': 'height: 100px'}),
            'dateDebutStage': forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFinStage': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
            'nbJours': forms.NumberInput(attrs={'placeholder': 'Nombre de jours'}),
            'trimestre': forms.Select(attrs={'placeholder': 'Trimestre'}),
            'eleve': forms.Select(attrs={'placeholder': 'Élève'}),
            'dureeStage': forms.TextInput(attrs={'placeholder': 'Lieu de stage'}),
            'relecteur': forms.Select(attrs={'placeholder': 'Relecteur'})
        }

class StageChangeForm(forms.ModelForm):

    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        Model = get_user_model()
        if user :
            self.fields['relecteur'].queryset = Model.objects.exclude(username=user).exclude(role='INFO').exclude(is_active=False).order_by('last_name')
        else :
            annee_en_cours = models.Annee.objects.filter(is_active=True)[0]
            self.fields['relecteur'].queryset = Model.objects.exclude(role='INFO').exclude(is_active=False).order_by(
                'last_name')
            self.fields['tuteur'].queryset = Model.objects.exclude(role='INFO').exclude(is_active=False).order_by(
                'last_name')
            self.fields['trimestre'].queryset = models.Trimestre.objects.filter(annee=annee_en_cours)
            classes = models.Classe.objects.filter(annee=annee_en_cours)
            self.fields['eleve'].queryset = models.Eleve.objects.filter(classe__in=classes)

    class Meta:
        model=models.Stage
        exclude=('descriptif_correction','appreciation_correction')
        widgets = {
            'typeStage': forms.Select(attrs={'placeholder': 'Type de stage'}),
            'lieuStage': forms.TextInput(attrs={'placeholder': 'Lieu de stage'}),
            'maitreStage': forms.TextInput(attrs={'placeholder': 'Maître de stage'}),
            'descriptif': forms.Textarea(attrs={'placeholder': 'Descriptif', 'style': 'height: 100px'}),
            'appreciation': forms.Textarea(attrs={'placeholder': 'Appreciation', 'style': 'height: 100px'}),
            'dateDebut': forms.DateInput(attrs={'placeholder': 'Date de début'}),
            'dateFin': forms.DateInput(attrs={'placeholder': 'Date de fin'}),
            'nbJours': forms.NumberInput(attrs={'placeholder': 'Nombre de jours'}),
            'relecteur': forms.Select(attrs={'placeholder': 'Relecteur'}),
            'eleve': forms.Select(attrs={'placeholder': 'Élève'}),
            'trimestre': forms.Select(attrs={'placeholder': 'Trimestre'}),
            'dureeStage': forms.TextInput(attrs={'placeholder': 'Lieu de stage'}),
            'tuteur': forms.Select(attrs={'placeholder': 'Tuteur'})
        }

class CompetencesConnaissancesForm(forms.ModelForm):
    edit_competence = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    class Meta:
        model = models.CompetencesConnaissances
        exclude=('discipline','intitule_correction')
        widgets={
            'intitule':forms.TextInput(attrs={'placeholder': 'Intitulé'}),
        }

class CompetencesConnaissancesCorrectionForm(forms.ModelForm):
    class Meta:
        model = models.CompetencesConnaissances
        fields = ('intitule_correction',)
        widgets = {
            'intitule_correction': forms.TextInput(attrs={'placeholder': "Correction de l'intitulé"}),
        }

class AppreciationForm(forms.ModelForm):

    class Meta:
        model = models.Appreciation
        exclude=('discipline','competencesConnaissances',)
        widgets={
            'attitude': forms.TextInput(attrs={'placeholder': 'attitude'}),
            'engagement': forms.TextInput(attrs={'placeholder': 'Engagement'}),
            'resultat': forms.TextInput(attrs={'placeholder': 'Résultat'}),
            'note': forms.NumberInput(attrs={'placeholder': 'Note'}),
            'commentaire': forms.Textarea(attrs={'placeholder': 'Commentaire'})
        }

class MiseEnPageBulletinForm(forms.ModelForm):

    class Meta:
        model = models.MiseEnPageBulletin
        fields='__all__'
        widgets={
            'intitule': forms.TextInput(attrs={'placeholder': 'Intitulé'}),
            'taillePolice': forms.NumberInput(attrs={'placeholder': 'Taille de la police'}),
            'police': forms.Select(attrs={'placeholder': 'Police de caractère'}),
            'couleurAppreciation':forms.NumberInput(attrs={'placeholder':'Couleur des appréciations','type':'color'}),
            'couleurStageProjet': forms.NumberInput(
                attrs={'placeholder': 'Couleur des stages et projets', 'type': 'color'}),
            'couleurAvis': forms.NumberInput(
                attrs={'placeholder': 'Couleur des avis du collège', 'type': 'color'}),
            'couleurNotice': forms.NumberInput(
                attrs={'placeholder': 'Couleur de la notice', 'type': 'color'}),
            'hauteurPage1': forms.NumberInput(attrs={'placeholder': 'Hauteur page 1 (cm)'}),
            'hauteurPage2': forms.NumberInput(attrs={'placeholder': 'Hauteur page 2 (cm)'}),
            'largeurPage1': forms.NumberInput(attrs={'placeholder': 'Largeur page 1 (cm)'}),
            'largeurIntitule': forms.NumberInput(attrs={'placeholder': 'Largeur colonne titre (%)'}),
            'largeurDescriptif': forms.NumberInput(attrs={'placeholder': 'Largeur colonne descriptif (%)'}),
            'largeurEvaluation': forms.NumberInput(attrs={'placeholder': 'Largeur colonne évaluation (%)'}),
            'signature_directeur_college': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
            'signature_directeur_lycee': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
        }
        help_texts = {
            'signature_directeur_college': 'Taille maximale : 100 ko',
            'signature_directeur_lycee': 'Taille maximale : 100 ko',
        }

class AppreciationCorrectionForm(forms.ModelForm):
    class Meta :
        model = models.Appreciation
        fields = ('commentaire_correction','remarque_correction')
        widgets={
            'commentaire_correction': forms.Textarea(attrs={'placeholder': 'Correction du commentaire', 'style': 'height: 120px'}),
            'remarque_correction': forms.Textarea(attrs={'placeholder': 'Remarque', 'style': 'height: 100px'})
        }

class CompetencesAppreciationForm(forms.ModelForm):
    class Meta:
        model = models.CompetencesAppreciations
        exclude=('appreciation',)
        widgets={
            'competence': forms.Select(attrs={'placeholder': 'Trimestre','readonly':True,'disabled':True}),
        }


class BulletinSelectEleves(forms.ModelForm):

    def __init__(self,*args,classe=None,**kwargs):
        super().__init__(*args,**kwargs)
        if classe :
            self.fields['eleves'].queryset=models.Eleve.objects.filter(classe=classe)
        
    class Meta :
        model = models.ListBulletinScolaire
        fields=('eleves',)
        widgets={
            'eleves':forms.SelectMultiple(attrs={'size':10, 'style':"width:100%;font-size:0.8rem;"}),
        }

class BulletinMisEnForme(forms.ModelForm):
    class Meta:
        model=models.ListBulletinScolaire
        fields=('miseEnPage',)
        widgets={
            'miseEnPage': forms.Select(attrs={'placeholder': 'Mise en page'}),
        }

class BulletinsEdition(forms.ModelForm):
    class Meta :
        model = models.ListBulletinScolaire
        fields = '__all__'

class SMTPSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si on modifie une instance existante, rendre le champ password optionnel
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Laissez vide pour conserver le mot de passe actuel'
    
    def clean_password(self):
        """
        Si le champ password est vide et qu'on modifie une instance existante,
        conserver le mot de passe actuel.
        """
        password = self.cleaned_data.get('password')
        if not password and self.instance and self.instance.pk:
            # Récupérer le mot de passe actuel depuis la base de données
            current_instance = models.SMTPSettings.objects.get(pk=self.instance.pk)
            return current_instance.password
        return password
    
    class Meta:
        model = models.SMTPSettings
        fields = '__all__'
        widgets = {
            'host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'smtp.gmail.com'}),
            'port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '587'}),
            'use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'votre.email@exemple.com'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe (laisser vide pour conserver)'}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'expediteur@exemple.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Objet personnalisé...'}),
            'email_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Message personnalisé...'}),
        }
        help_texts = {
            'host': 'Adresse du serveur SMTP (ex: smtp.gmail.com, smtp.office365.com)',
            'port': 'Port SMTP (587 pour TLS, 465 pour SSL)',
            'use_tls': 'Cocher pour utiliser TLS, décocher pour SSL',
            'username': 'Nom d\'utilisateur ou adresse email pour l\'authentification SMTP',
            'password': 'Mot de passe pour l\'authentification SMTP (laisser vide pour conserver le mot de passe actuel)',
            'from_email': 'Adresse email utilisée comme expéditeur par défaut',
            'is_active': 'Activer cette option pour permettre l\'envoi d\'emails via SMTP',
            'email_subject': 'Objet personnalisé pour les emails de bulletins. Variables disponibles : {prenom}, {nom}, {trimestres}',
            'email_message': 'Message personnalisé qui accompagne l\'envoi des bulletins. Variables disponibles : {prenom}, {nom}, {trimestres}',
        }