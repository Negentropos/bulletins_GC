from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Frame
from . import pdf

def validate_file_size(value):
    """Valide que le fichier ne dépasse pas 100 ko"""
    max_size = 100 * 1024  # 100 ko en octets
    if value.size > max_size:
        raise ValidationError(
            _('Le fichier ne peut pas dépasser 100 ko. Taille actuelle : %(size)s ko'),
            params={'size': round(value.size / 1024, 2)},
        )

class Annee(models.Model):
    intitule = models.CharField(max_length=9)
    is_active=models.BooleanField(default=False,verbose_name='en cours')

    def __str__(self):
        return f'{self.intitule[2:5]}{self.intitule[7:]}'

    def export(self):
        return f'{self.intitule[2:4]}-{self.intitule[7:]}'

class Classe(models.Model):

    class Cycle(models.TextChoices):
        PRIMAIRE = 'PRI', _("Primaire")
        COLLEGE = 'COL',_("Collège")
        LYCEE = 'LYC', _("Lycée")

    nom = models.CharField(max_length=20)
    effectifs=models.PositiveIntegerField(blank=True,null=True,default=0)
    annee=models.ForeignKey(Annee,on_delete=models.CASCADE,blank=True,null=True)
    tuteur=models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True)
    cycle = models.fields.CharField(choices=Cycle.choices, max_length=10, default=Cycle.COLLEGE)

    def calculEffectifs(self):
        eleves=Eleve.objects.filter(classe = self)
        if self.effectifs != None :
            self.effectifs = len(eleves.all())
        else :
            self.effectifs = 0

    def save(self, *args, **kwargs):
        self.calculEffectifs()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nom}'

    def show_nom(self):
        return f'{self.nom}e classe'

    def show_tuteur(self):
        return ', '.join([a.first_name[0]+'.' + ' ' + a.last_name for a in self.tuteur.all()])

    show_tuteur.short_description = "Tuteur(s)"

class Eleve(models.Model):

    class Genre(models.TextChoices):
        MASCULIN = 'M', _("Masculin")
        FEMININ = 'F', _("Féminin")

    class Statut(models.TextChoices):
        ELEVE = 'EL', _("Élève")
        HOTE_PAYANT = 'HP',_("Hôte payant(e)")
        ECHANGE = 'EXC', _("Échange ling.")

    nom = models.CharField(max_length=30, verbose_name='Nom')
    prenom = models.CharField(max_length=30, verbose_name='Prénom')
    dateNaissance = models.DateField(null=True,blank=True)
    genre = models.fields.CharField(choices=Genre.choices, max_length=5)
    statut = models.fields.CharField(choices=Statut.choices,max_length=10,default=Statut.ELEVE)
    classe = models.ManyToManyField(Classe,blank=True)
    emails_bulletin = models.TextField(blank=True, null=True, verbose_name='Adresses email pour l\'expédition du bulletin', 
                                       help_text='Séparez plusieurs adresses par des virgules (ex: email1@exemple.com, email2@exemple.com)')


    def __str__(self):
        return f'{self.nom} {self.prenom}'

    def show_classe(self):
        annee_en_cours=Annee.objects.filter(is_active=True)[0]
        if not self.classe.filter(annee=annee_en_cours) :
            return "ancien élève"
        else :
            return self.classe.filter(annee=annee_en_cours)[0]
    
    def get_emails_bulletin_list(self):
        """
        Retourne la liste des adresses email pour l'expédition du bulletin.
        """
        if self.emails_bulletin:
            # Séparer par virgules et nettoyer les espaces
            emails = [email.strip() for email in self.emails_bulletin.split(',') if email.strip()]
            return emails
        return []

class Journal(models.Model):
    message=models.CharField(max_length=50)
    date=models.DateTimeField(auto_now=True)
    utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,
                                  on_delete=models.SET_NULL,
                                  related_name='logs',
                                  )

class Trimestre(models.Model):

    class Trimestre(models.TextChoices):
        TRIMESTRE_1 = 'T1', _("Trimestre 1")
        TRIMESTRE_2 = 'T2',_("Trimestre 2")
        TRIMESTRE_3 = 'T3', _("Trimestre 3")

    intitule = models.CharField(max_length=30, choices=Trimestre.choices, verbose_name='Intitulé')
    edition = models.BooleanField(default=False,verbose_name="Ouvert à l'édition")
    dateDebut = models.DateField(null=True,blank=True,verbose_name='Date de début')
    dateFin = models.DateField(null=True,blank=True,verbose_name='Date de fin')
    annee=models.ForeignKey(Annee,on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.intitule[0]}e Trim. {self.annee}'

    def show_racc(self):
        return f'{self.intitule[0]}e Trim.'

    def show_num(self):
        return f'{self.intitule[0]}'

    def show_Tnum(self):
        return f'T{self.intitule[0]}'

class Absence(models.Model):
    nbRetard=models.PositiveIntegerField(default=0)
    nbAbsenceExc = models.PositiveIntegerField(default=0,verbose_name="Demi-journées d'absences excusées")
    nbAbsenceNonExc = models.PositiveIntegerField(default=0,verbose_name="Demi-journées d'absences non-excusées")
    trimestre = models.ForeignKey(Trimestre,on_delete=models.CASCADE)
    eleve = models.ForeignKey(Eleve,on_delete=models.CASCADE)
    nbAbsenceTot = models.PositiveIntegerField(default=0,verbose_name="Demi-journées d'absences")

    def __str__(self):
        return f'{self.eleve}'

    def calculAbsencesTot(self):
        self.nbAbsenceTot = self.nbAbsenceExc + self.nbAbsenceNonExc

    def save(self,*args,**kwargs):
        self.calculAbsencesTot()
        super().save(*args,**kwargs)

class Projet(models.Model):

    class TypeProjet(models.TextChoices):
        TRAVAIL_ANNEE = 'TA', _("Travail d'année")
        PROJET_PILOTE = 'PP', _("Projet pilote")
        AUTRE = 'AUTRE', _("Projet divers")
        PERSO = 'PERS', _("Projet personnel")
        COLL = 'COLL', _("Projet collectif")

    typeProjet=models.CharField(max_length=60, choices=TypeProjet.choices)
    titre = models.CharField(max_length=60, null=True, blank=True)
    titre_correction = models.CharField(max_length=60, null=True, blank=True)
    descriptif = models.CharField(max_length=800, blank=True, null=True)
    descriptif_correction = models.CharField(max_length=800, blank=True, null=True)
    appreciation = models.CharField(max_length=800, blank=True, null=True)
    appreciation_correction = models.CharField(max_length=800, blank=True, null=True)
    remarque_correction = models.CharField(max_length=800, blank=True, null=True)
    relectureActive = models.BooleanField(default=False, verbose_name='ouvert à relecture')
    presentBulletin = models.BooleanField(default=True, verbose_name='intégrer au bulletin')
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    relecteur = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  null=True,
                                  blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name='relecteurProjet',
                                  )
    tuteur = models.ForeignKey(settings.AUTH_USER_MODEL,
                               null=True,
                               blank=True,
                               on_delete=models.SET_NULL,
                               related_name='tuteurProjet',
                               )
    eleve = models.ForeignKey(Eleve,
                              on_delete=models.CASCADE,
                              related_name='eleveProjet'
                              )
    correctionsAValider = models.BooleanField(default=False, verbose_name='corrections à valider')

    def checkCorrections(self):
        if (self.descriptif_correction != None and self.descriptif_correction != '')  or (self.appreciation_correction != None and self.appreciation_correction != '') or (self.titre_correction != None and self.titre_correction != '') or (self.remarque_correction != None and self.remarque_correction != '') :
            self.correctionsAValider = True
        else :
            self.correctionsAValider = False




    def save(self,*args,**kwargs):
        if self.id :
            self.checkCorrections()
        super().save(*args,**kwargs)


class Stage(models.Model):

    class TypeStage(models.TextChoices):
        AGRICOLE = 'AGR', _("Stage agricole")
        ENTREPRISE = 'ENT', _("Stage en entreprise")
        SOCIAL = 'SOC', _("Stage en milieu social")
        LINGUISTIQUE = 'LING', _("Échange linguistique")
        AUTRE = 'AUTRE', _("Stage divers")

    typeStage = models.CharField(max_length=60, choices=TypeStage.choices)
    lieuStage=models.CharField(max_length=200, blank=True, null=True)
    dureeStage = models.CharField(max_length=20, blank=True, null=True)
    maitreStage=models.CharField(max_length=60,blank=True, null=True)
    eleve=models.ForeignKey(Eleve,
                                on_delete=models.CASCADE
                                )
    descriptif = models.CharField(max_length=800, blank=True, null=True)
    descriptif_correction = models.CharField(max_length=800, blank=True, null=True)
    appreciation = models.CharField(max_length=1000, blank=True, null=True)
    appreciation_correction = models.CharField(max_length=1000, blank=True, null=True)
    dateDebut = models.DateField(null=True, blank=True, verbose_name='A débuté le : ')
    dateFin = models.DateField(null=True, blank=True, verbose_name="S'est terminé le : ")
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    relectureActive=models.BooleanField(default=False,verbose_name='ouvert à relecture')
    remarque_correction = models.CharField(max_length=800, blank=True, null=True)
    presentBulletin = models.BooleanField(default=True, verbose_name='intégrer au bulletin')
    relecteur = models.ForeignKey(settings.AUTH_USER_MODEL,
                                null=True,
                                blank=True,
                                on_delete=models.SET_NULL,
                                related_name = 'reluPar',
                                )
    tuteur = models.ForeignKey(settings.AUTH_USER_MODEL,
                                null=True,
                                blank=True,
                                on_delete=models.SET_NULL,
                                related_name='tuteurStage',
                                )
    correctionsAValider = models.BooleanField(default=False, verbose_name='corrections à valider')

    def checkCorrections(self):
        if (self.descriptif_correction != None and self.descriptif_correction != '')  or (self.appreciation_correction != None and self.appreciation_correction != '') or (self.remarque_correction != None and self.remarque_correction != '') :
            self.correctionsAValider = True
        else :
            self.correctionsAValider = False

    def save(self,*args,**kwargs):
        if self.id :
            self.checkCorrections()
        super().save(*args,**kwargs)

class Bareme(models.Model):
    intitule=models.CharField(max_length=50)
    defaut=models.BooleanField(default=False, verbose_name='')
    titre=models.CharField(max_length=50,default='',blank=True)
    intro=models.CharField(max_length=1000,default='',blank=True)
    attitude=models.CharField(max_length=300,default='',blank=True)
    attitudeA = models.CharField(max_length=400,default='',blank=True)
    attitudeB = models.CharField(max_length=400,default='',blank=True)
    attitudeC = models.CharField(max_length=400,default='',blank=True)
    attitudeD = models.CharField(max_length=400,default='',blank=True)
    engagement = models.CharField(max_length=300,default='',blank=True)
    engagementA = models.CharField(max_length=400,default='',blank=True)
    engagementB = models.CharField(max_length=400,default='',blank=True)
    engagementC = models.CharField(max_length=400,default='',blank=True)
    engagementD = models.CharField(max_length=400,default='',blank=True)
    resultat = models.CharField(max_length=300,default='',blank=True)
    resultatA = models.CharField(max_length=400,default='',blank=True)
    resultatB = models.CharField(max_length=400,default='',blank=True)
    resultatC = models.CharField(max_length=400,default='',blank=True)
    resultatD = models.CharField(max_length=400,default='',blank=True)
    piedPage = models.CharField(max_length=150,default='',blank=True)

    def __str__(self):
        return self.intitule

    def save(self,*args,checkDefaut=False,**kwargs):
        #vérifier si défaut :
        if checkDefaut and self.defaut :
            baremes=Bareme.objects.exclude(id=self.id)
            for bareme in baremes :
                if bareme.defaut==True:
                    bareme.defaut=False
                    bareme.save()
                    break
            super().save(*args, **kwargs)
        else :
            super().save(*args,**kwargs)



class Discipline(models.Model):
    class TypeEnseignement(models.TextChoices):
        PERIODE = 'PR', _("Enseignement de période")
        ATELIER = 'AT',_("Enseignement d'atelier")
        HEUREHEBDO = 'HH', _("Enseignement en heures hebdomadaires")
        PERIODE_HH =  'PRHH', _("Enseignement en heures hebdomadaires et en période")
        HEUREHEBDO_AT= 'HHAT', _("Enseignement en heures hebdomadaires et en atelier")
        SEMAINE_THEMA = 'ST', _("Semaine thématique")
        PERIODE_HH_AT='PRHHAT', _("Enseignement en période, en heures hebdomadaires et en atelier")
        SPECIALITE='SPE', _("Enseignement de spécialité (première générale)")

    intitule=models.CharField(max_length=60)
    intitule_court=models.CharField(max_length=30,blank=True,null=True)
    titre=models.CharField(max_length=200,blank=True,null=True)
    titre_correction=models.CharField(max_length=200,blank=True,null=True)
    remarque_correction=models.CharField(max_length=800, blank=True, null=True)
    typeEnseignement=models.CharField(max_length=60,blank=True,null=True,choices=TypeEnseignement.choices)
    volumeHoraire=models.PositiveIntegerField(blank=True,null=True)
    descriptif=models.CharField(max_length=600,blank=True,null=True)
    descriptif_correction = models.CharField(max_length=600, blank=True, null=True)
    dateDebut=models.DateField(null=True,blank=True,verbose_name='A débuté le : ')
    dateFin=models.DateField(null=True,blank=True,verbose_name="S'est terminée le : ")
    trimestre=models.ForeignKey(Trimestre,null=True,on_delete=models.SET_NULL)
    voirProf = models.BooleanField(default=True,verbose_name='Afficher les professeurs')
    reluPar=models.ForeignKey(settings.AUTH_USER_MODEL,
                              null=True,
                              blank=True,
                              verbose_name="est relu par : ",
                              related_name='relecteurs',
                              on_delete=models.SET_NULL
                            )
    enseigneePar=models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True,verbose_name="enseignée par :")
    enseigneeA=models.ManyToManyField(Eleve,blank=True,verbose_name='enseignée à :')
    enseigneeDans=models.ManyToManyField(Classe,blank=True,verbose_name='enseignée en :')
    relectureActive=models.BooleanField(default=False,verbose_name='ouverte à relecture')
    moyenne=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    notePlusHaute = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notePlusBasse = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    effectifs = models.PositiveIntegerField(blank=True,null=True)
    nbAppreciationsVides=models.PositiveIntegerField(blank=True,null=True)
    presentBulletin = models.BooleanField(default=True,verbose_name='intégrer au bulletin')
    activerMoyenne = models.BooleanField(default=True,verbose_name='afficher la moyenne')
    correctionsAValider = models.BooleanField(default=False, verbose_name='corrections à valider')

    def __str__(self):
        return f'{self.intitule}'

    def appreciationsVides(self):
        nb=0
        appreciations=Appreciation.objects.filter(discipline=self)
        for appreciation in appreciations :
            if appreciation.commentaire != None :
                if len(appreciation.commentaire) ==0 :
                    nb+=1
        self.nbAppreciationsVides=nb

    def show_enseignants(self):
        return ', '.join([a.first_name[0] + '.' + ' ' + a.last_name for a in self.enseigneePar.all()])

    def show_enseignant_export(self):
        return ','.join(a.username for a in self.enseigneePar.all())

    def show_classes_export(self):
        return ','.join(a.nom for a in self.enseigneeDans.all())

    show_enseignants.short_description = "Enseignant(s)"

    def show_classes(self):
        return ', '.join([f'{a.nom}e' for a in self.enseigneeDans.all()])

    show_classes.short_description = "Classe(s)"

    def list_classes(self):
        return [classe for classe in self.enseigneeDans.all()]

    def calculEffectifs(self):
        self.effectifs=len(self.enseigneeA.all())

    def checkCorrections(self):
        if (self.titre_correction != None and self.titre_correction != '')  or (self.descriptif_correction != None and self.descriptif_correction != '') or (self.remarque_correction != None and self.remarque_correction != '') :
            self.correctionsAValider = True
        elif CompetencesConnaissances.objects.filter(discipline=self).exclude(intitule_correction__isnull=True).exclude(intitule_correction__exact='') :
            self.correctionsAValider = True
        elif Appreciation.objects.filter(discipline=self).exclude(commentaire_correction__isnull=True,remarque_correction__isnull=True).exclude(commentaire_correction__exact='',remarque_correction__exact='') :
            self.correctionsAValider = True
        else :
            self.correctionsAValider = False

    def calculMoyenneEtAutres(self):
        appreciations = Appreciation.objects.filter(discipline=self)
        liste_notes = []
        for appreciation in appreciations :
            if appreciation.note is not None :
                liste_notes.append(appreciation.note)
        if liste_notes != []:
            self.notePlusHaute = max(liste_notes)
            self.notePlusBasse = min(liste_notes)
            self.moyenne = sum(liste_notes)/len(liste_notes)
        else :
            self.notePlusHaute = None
            self.notePlusBasse = None
            self.moyenne = None

    def save(self,*args,**kwargs):
        if self.id :
            self.appreciationsVides()
            self.checkCorrections()
            self.calculEffectifs()
            self.calculMoyenneEtAutres()
        super().save(*args,**kwargs)

    class Meta:
        permissions = [
            ('admin_discipline', 'Peut administrer les disciplines')
        ]


class CompetencesConnaissances(models.Model):
    intitule=models.CharField(max_length=200,null=True)
    intitule_correction=models.CharField(max_length=200,null=True,blank=True)
    discipline=models.ForeignKey(Discipline,on_delete=models.CASCADE)

    def __str__(self):
        return self.intitule

class Appreciation(models.Model):
    commentaire=models.TextField(max_length=1000,null=True,blank=True)
    commentaire_correction=models.TextField(max_length=1000,null=True,blank=True)
    remarque_correction=models.TextField(max_length=600,null=True,blank=True)
    note=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    attitude=models.CharField(max_length=2,null=True,blank=True)
    engagement=models.CharField(max_length=2, null=True, blank=True)
    resultat=models.CharField(max_length=2, null=True, blank=True)
    discipline=models.ForeignKey(Discipline,on_delete=models.CASCADE)
    eleve=models.ForeignKey(Eleve,on_delete=models.CASCADE)
    competencesConnaissances=models.ManyToManyField(CompetencesConnaissances,
                                                    verbose_name='appartient à ',
                                                    through='CompetencesAppreciations'
                                                    )

    def discipline_export(self):
        return f"{self.discipline.intitule} {self.discipline.show_classes()} {self.discipline.show_enseignants()} {self.discipline.trimestre}"

    def competences_export(self):
        return ','.join(a.id for a in self.competencesConnaissances.all())

class CompetencesAppreciations(models.Model):

    class TypeEvaluation(models.TextChoices):
        NONEVAL = '-', _("Non évalué")
        NONACQUIS = 'Maîtrise insuffisante', _("Maîtrise insuffisante")
        PARTIELLEMENTACQUIS = 'Maîtrise partielle', _("Maîtrise partielle")
        ACQUIS = 'Très bonne maîtrise', _("Très bonne maîtrise")
        GLOBALACQUIS = 'Maîtrise satisfaisante', _("Maîtrise satisfaisante")



    competence=models.ForeignKey(CompetencesConnaissances,on_delete=models.CASCADE)
    appreciation=models.ForeignKey(Appreciation,on_delete=models.CASCADE)
    evaluation=models.CharField(max_length=23,choices=TypeEvaluation.choices,default="Non évalué")

    class Meta:
        unique_together= ('competence','appreciation')

class AvisCollege(models.Model):
    eleve=models.ForeignKey(Eleve,on_delete=models.CASCADE)
    trimestre=models.ForeignKey(Trimestre,on_delete=models.CASCADE)
    avis=models.TextField(max_length=1000,null=True,blank=True)

    class Meta :
        unique_together=('eleve','trimestre')

class MiseEnPageBulletin(models.Model):
    class ChoixPolice(models.TextChoices):
        HELVETICA = 'Helvetica', _("Helvetica")
        COURIER = 'Courier', _("Courier")

    intitule = models.CharField(max_length=50, blank=True, null=True)
    taillePolice=models.DecimalField(default=8.0,max_digits=3,decimal_places=1)
    police=models.CharField(max_length=30,default='Helvetica',choices=ChoixPolice.choices)
    couleurAppreciation=models.CharField(max_length=10,default='#ebebeb')
    couleurStageProjet = models.CharField(max_length=10, default='#ebebeb')
    couleurAvis = models.CharField(max_length=10, default='#ebebeb')
    couleurNotice=models.CharField(max_length=10,default='#ebebeb')
    hauteurPage1=models.DecimalField(default=24.0,max_digits=3,decimal_places=1)
    largeurPage1=models.DecimalField(default=20.0,max_digits=3,decimal_places=1)
    hauteurPage2=models.DecimalField(default=27.7,max_digits=3,decimal_places=1)
    largeurIntitule=models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],default=20)
    largeurDescriptif=models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],default=25)
    largeurEvaluation=models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],default=55)
    signature_directeur_college=models.ImageField(upload_to='signatures/', blank=True, null=True, verbose_name='Signature directeur collège', validators=[validate_file_size])
    signature_directeur_lycee=models.ImageField(upload_to='signatures/', blank=True, null=True, verbose_name='Signature directeur lycée', validators=[validate_file_size])

    def __str__(self):
        return self.intitule


class ListBulletinScolaire(models.Model):
    trimestres=models.ManyToManyField(Trimestre)
    eleves=models.ManyToManyField(Eleve,blank=True)
    signatureBulletin=models.BooleanField(default=False)
    bulletinAbsencesRetards=models.BooleanField(default=False)
    bulletinUtilisationCompetence=models.BooleanField(default=False)
    bulletinVersionProvisoire = models.BooleanField(default=True)
    bulletinNotice=models.BooleanField(default=False)
    bulletinAvisCollege=models.BooleanField(default=False)
    miseEnPage=models.ForeignKey(MiseEnPageBulletin,on_delete=models.SET_NULL,null=True,blank=True)

    #TODO : ordonner matières par volume horaire ? puis par date de commencement (réservé aux périodes - donc les périodes d'abord ?)

    def returnAbsences(self):
        return Absence.objects.filter(eleve__in=self.eleves.all()).filter(trimestre__in=self.trimestres.all())
    #va retourner les absences et les retards pour le trimestre condisdéré

    def returnAppreciations(self):
        disciplines = Discipline.objects.filter(trimestre__in=self.trimestres.all()).filter(presentBulletin=True)
        return Appreciation.objects.filter(eleve__in=self.eleves.all()).filter(discipline__in=disciplines),disciplines


    def returnStage(self):
        return Stage.objects.filter(trimestre__in=self.trimestres.all()).filter(eleve__in=self.eleves.all())

    def returnProjet(self):
        return Projet.objects.filter(trimestre__in=self.trimestres.all()).filter(eleve__in=self.eleves.all())

    def returnAvisCollege(self):
        return AvisCollege.objects.filter(trimestre__in=self.trimestres.all()).filter(eleve__in=self.eleves.all())

    def produceBulletin(self):
        appreciations_eleves,disciplines_eleves=self.returnAppreciations()
        absencesEleves = self.returnAbsences()
        avisCollege_eleves=self.returnAvisCollege()
        stages_eleves=self.returnStage()
        projets_eleves=self.returnProjet()

        # Create a file-like buffer to receive PDF data.
        buffer = io.BytesIO()
        # Create the PDF object, using the buffer as its "file."
        fichierBulletins = canvas.Canvas(buffer,pagesize=A4)
        dictParamBulletins={
            #Valeurs par défaut de police de caractère, taille de police
                        'font':'Helvetica',
                        'fontBold' : 'Helvetica-Bold',
                        'fontSize' : 8,
                        'largeur_tot_tab_appreciations':20*cm,
                        'hauteurPage1':24*cm,
                        'hauteurPage2':27.7*cm,
                        "piedPageBulletin" : "École Mathias Grünewald - 4 rue Herzog 68124 Logelbach - www.ecole-mathias-grunewald.org",
                        'couleurAppreciation':'#ebebeb',
                        'couleurStageProjet': '#ebebeb',
                        'couleurAvis': '#ebebeb',
                        'couleurNotice': '#ebebeb',
                        'largeurIntitule': 20,
                        'largeurDescriptif':25,
                        'largeurEvaluation':55,
                        }


        if self.miseEnPage != None :
            dictParamBulletins['font']=self.miseEnPage.police
            dictParamBulletins['fontSize']=float(self.miseEnPage.taillePolice)
            dictParamBulletins['fontBold'] =self.miseEnPage.police + '-Bold'
            dictParamBulletins['largeur_tot_tab_appreciations']=float(self.miseEnPage.largeurPage1)*cm
            dictParamBulletins['hauteurPage1'] = float(self.miseEnPage.hauteurPage1)*cm
            dictParamBulletins['hauteurPage2'] = float(self.miseEnPage.hauteurPage2)*cm
            dictParamBulletins['couleurAppreciation']=self.miseEnPage.couleurAppreciation
            dictParamBulletins['couleurStageProjet']=self.miseEnPage.couleurStageProjet
            dictParamBulletins['couleurAvis']=self.miseEnPage.couleurAvis
            dictParamBulletins['couleurNotice']=self.miseEnPage.couleurNotice
            dictParamBulletins['largeurIntitule']=self.miseEnPage.largeurIntitule
            dictParamBulletins['largeurDescriptif'] = self.miseEnPage.largeurDescriptif
            dictParamBulletins['largeurEvaluation'] = self.miseEnPage.largeurEvaluation
            # Ajout des signatures si elles existent
            try:
                if self.miseEnPage.signature_directeur_college and self.miseEnPage.signature_directeur_college.name:
                    dictParamBulletins['signature_college'] = self.miseEnPage.signature_directeur_college.path
                else:
                    dictParamBulletins['signature_college'] = None
            except (ValueError, AttributeError):
                dictParamBulletins['signature_college'] = None
            try:
                if self.miseEnPage.signature_directeur_lycee and self.miseEnPage.signature_directeur_lycee.name:
                    dictParamBulletins['signature_lycee'] = self.miseEnPage.signature_directeur_lycee.path
                else:
                    dictParamBulletins['signature_lycee'] = None
            except (ValueError, AttributeError):
                dictParamBulletins['signature_lycee'] = None
        else:
            dictParamBulletins['signature_college'] = None
            dictParamBulletins['signature_lycee'] = None

        for eleve in self.eleves.all() :
            for trimestre in self.trimestres.all():
                disciplines=disciplines_eleves.filter(trimestre=trimestre)
                appreciations=appreciations_eleves.filter(eleve=eleve).filter(discipline__in=disciplines)
                stages=stages_eleves.filter(trimestre=trimestre).filter(eleve=eleve)
                projets=projets_eleves.filter(trimestre=trimestre).filter(eleve=eleve)
                avisCollege=avisCollege_eleves.filter(trimestre=trimestre).filter(eleve=eleve).first()
                if not absencesEleves.filter(trimestre=trimestre).filter(eleve=eleve).exists() :
                    absenceEleve=Absence(eleve=eleve,trimestre=trimestre)
                else :
                    absenceEleve=absencesEleves.filter(trimestre=trimestre).get(eleve=eleve)
                #génération de l'en tête du bulletin
                pdf.enTete(eleve,trimestre,fichierBulletins,dictParamBulletins)
                if self.bulletinVersionProvisoire :
                    pdf.versionProvisoire(fichierBulletins)

                frameAppreciations = Frame(x1=0.5 * cm, y1=1 * cm, width=dictParamBulletins['largeur_tot_tab_appreciations'], height=dictParamBulletins['hauteurPage1'], showBoundary=0,
                                           leftPadding=0,
                                           topPadding=0, rightPadding=0, bottomPadding=0)
                story_page1=[]
                story_page2 = []
                pdf.ligneEnTeteAppreciation(story_page1,dictParamBulletins)
                numAppreciation=0
                for appreciation in appreciations:
                    competences = CompetencesAppreciations.objects.filter(appreciation=appreciation)
                    if appreciation.commentaire is not None and len(appreciation.commentaire) > 0 :
                        pdf.creerBulletinAppreciations(appreciation,competences,fichierBulletins,dictParamBulletins,story_page1,self.bulletinUtilisationCompetence,numAppreciation)
                    numAppreciation+=1

                if stages.exists() or projets.exists():
                    pdf.espace(story_page1,0.5)
                    pdf.stagesProjets(stages,projets,dictParamBulletins,story_page1)
                if avisCollege != None and self.bulletinAvisCollege :
                    pdf.espace(story_page1,0.5)
                    pdf.avisCollege(avisCollege,dictParamBulletins, story_page1)

                pdf.espace(story_page1)
                pdf.absenceEtVisa(story_page1,absenceEleve,dictParamBulletins,self.signatureBulletin,self.bulletinAbsencesRetards)

                notice = Bareme.objects.filter(defaut=True).first()
                if self.bulletinNotice :
                    pdf.noticeBulletin(story_page1,dictParamBulletins,notice)

                page1_full = False



                fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'] * 0.8)
                if notice != None :
                    fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm, notice.piedPage)
                else :
                    fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])

                compteur=0
                for p in story_page1:
                    if page1_full == False :
                        compteur+=1
                        if frameAppreciations.add(p,fichierBulletins) == 0 :
                            page1_full = True
                            fichierBulletins.setFont(dictParamBulletins['font'],
                                                     size=dictParamBulletins['fontSize'] * 0.8)
                            if notice != None:
                                fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm, notice.piedPage)
                            else:
                                fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])
                            story_page2.append(p)
                    else :
                        story_page2.append(p)


                #Frame saturée mais il reste des éléments dans la liste...
                if story_page2 != []:
                    fichierBulletins.drawString(20 * cm, 0.5 * cm, "1/2")
                    fichierBulletins.showPage()
                    frameAppreciations_page2 = Frame(x1=0.5 * cm, y1=1 * cm, width=dictParamBulletins['largeur_tot_tab_appreciations'], height=dictParamBulletins['hauteurPage2'], showBoundary=0,
                                               leftPadding=0,
                                               topPadding=0, rightPadding=0, bottomPadding=0)
                    if self.bulletinVersionProvisoire:
                        pdf.versionProvisoire(fichierBulletins)
                    if compteur <= (numAppreciation+1) :
                        enTete=[]
                        pdf.ligneEnTeteAppreciation(enTete, dictParamBulletins)
                        frameAppreciations_page2.add(enTete[0],fichierBulletins)
                    frameAppreciations_page2.addFromList(story_page2,fichierBulletins)
                    fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'])
                    fichierBulletins.drawString(20 * cm, 0.5 * cm, "2/2")
                    fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'] * 0.8)
                    fichierBulletins.drawString(6.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])
                fichierBulletins.showPage()


        fichierBulletins.save()

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="bulletinsEMG.pdf")
    #Va créer le bulletin PDF
    
    def produceBulletinContent(self):
        """
        Génère le PDF du bulletin et retourne le contenu binaire (pour l'envoi par email).
        """
        appreciations_eleves,disciplines_eleves=self.returnAppreciations()
        absencesEleves = self.returnAbsences()
        avisCollege_eleves=self.returnAvisCollege()
        stages_eleves=self.returnStage()
        projets_eleves=self.returnProjet()

        # Create a file-like buffer to receive PDF data.
        buffer = io.BytesIO()
        # Create the PDF object, using the buffer as its "file."
        fichierBulletins = canvas.Canvas(buffer,pagesize=A4)
        dictParamBulletins={
            #Valeurs par défaut de police de caractère, taille de police
                        'font':'Helvetica',
                        'fontBold' : 'Helvetica-Bold',
                        'fontSize' : 8,
                        'largeur_tot_tab_appreciations':20*cm,
                        'hauteurPage1':24*cm,
                        'hauteurPage2':27.7*cm,
                        "piedPageBulletin" : "École Mathias Grünewald - 4 rue Herzog 68124 Logelbach - www.ecole-mathias-grunewald.org",
                        'couleurAppreciation':'#ebebeb',
                        'couleurStageProjet': '#ebebeb',
                        'couleurAvis': '#ebebeb',
                        'couleurNotice': '#ebebeb',
                        'largeurIntitule': 20,
                        'largeurDescriptif':25,
                        'largeurEvaluation':55,
                        }


        if self.miseEnPage != None :
            dictParamBulletins['font']=self.miseEnPage.police
            dictParamBulletins['fontSize']=float(self.miseEnPage.taillePolice)
            dictParamBulletins['fontBold'] =self.miseEnPage.police + '-Bold'
            dictParamBulletins['largeur_tot_tab_appreciations']=float(self.miseEnPage.largeurPage1)*cm
            dictParamBulletins['hauteurPage1'] = float(self.miseEnPage.hauteurPage1)*cm
            dictParamBulletins['hauteurPage2'] = float(self.miseEnPage.hauteurPage2)*cm
            dictParamBulletins['couleurAppreciation']=self.miseEnPage.couleurAppreciation
            dictParamBulletins['couleurStageProjet']=self.miseEnPage.couleurStageProjet
            dictParamBulletins['couleurAvis']=self.miseEnPage.couleurAvis
            dictParamBulletins['couleurNotice']=self.miseEnPage.couleurNotice
            dictParamBulletins['largeurIntitule']=self.miseEnPage.largeurIntitule
            dictParamBulletins['largeurDescriptif'] = self.miseEnPage.largeurDescriptif
            dictParamBulletins['largeurEvaluation'] = self.miseEnPage.largeurEvaluation
            # Ajout des signatures si elles existent
            try:
                if self.miseEnPage.signature_directeur_college and self.miseEnPage.signature_directeur_college.name:
                    dictParamBulletins['signature_college'] = self.miseEnPage.signature_directeur_college.path
                else:
                    dictParamBulletins['signature_college'] = None
            except (ValueError, AttributeError):
                dictParamBulletins['signature_college'] = None
            try:
                if self.miseEnPage.signature_directeur_lycee and self.miseEnPage.signature_directeur_lycee.name:
                    dictParamBulletins['signature_lycee'] = self.miseEnPage.signature_directeur_lycee.path
                else:
                    dictParamBulletins['signature_lycee'] = None
            except (ValueError, AttributeError):
                dictParamBulletins['signature_lycee'] = None
        else:
            dictParamBulletins['signature_college'] = None
            dictParamBulletins['signature_lycee'] = None

        for eleve in self.eleves.all() :
            for trimestre in self.trimestres.all():
                disciplines=disciplines_eleves.filter(trimestre=trimestre)
                appreciations=appreciations_eleves.filter(eleve=eleve).filter(discipline__in=disciplines)
                stages=stages_eleves.filter(trimestre=trimestre).filter(eleve=eleve)
                projets=projets_eleves.filter(trimestre=trimestre).filter(eleve=eleve)
                avisCollege=avisCollege_eleves.filter(trimestre=trimestre).filter(eleve=eleve).first()
                if not absencesEleves.filter(trimestre=trimestre).filter(eleve=eleve).exists() :
                    absenceEleve=Absence(eleve=eleve,trimestre=trimestre)
                else :
                    absenceEleve=absencesEleves.filter(trimestre=trimestre).get(eleve=eleve)
                #génération de l'en tête du bulletin
                pdf.enTete(eleve,trimestre,fichierBulletins,dictParamBulletins)
                if self.bulletinVersionProvisoire :
                    pdf.versionProvisoire(fichierBulletins)

                frameAppreciations = Frame(x1=0.5 * cm, y1=1 * cm, width=dictParamBulletins['largeur_tot_tab_appreciations'], height=dictParamBulletins['hauteurPage1'], showBoundary=0,
                                           leftPadding=0,
                                           topPadding=0, rightPadding=0, bottomPadding=0)
                story_page1=[]
                story_page2 = []
                pdf.ligneEnTeteAppreciation(story_page1,dictParamBulletins)
                numAppreciation=0
                for appreciation in appreciations:
                    competences = CompetencesAppreciations.objects.filter(appreciation=appreciation)
                    if appreciation.commentaire is not None and len(appreciation.commentaire) > 0 :
                        pdf.creerBulletinAppreciations(appreciation,competences,fichierBulletins,dictParamBulletins,story_page1,self.bulletinUtilisationCompetence,numAppreciation)
                    numAppreciation+=1

                if stages.exists() or projets.exists():
                    pdf.espace(story_page1,0.5)
                    pdf.stagesProjets(stages,projets,dictParamBulletins,story_page1)
                if avisCollege != None and self.bulletinAvisCollege :
                    pdf.espace(story_page1,0.5)
                    pdf.avisCollege(avisCollege,dictParamBulletins, story_page1)

                pdf.espace(story_page1)
                pdf.absenceEtVisa(story_page1,absenceEleve,dictParamBulletins,self.signatureBulletin,self.bulletinAbsencesRetards)

                notice = Bareme.objects.filter(defaut=True).first()
                if self.bulletinNotice :
                    pdf.noticeBulletin(story_page1,dictParamBulletins,notice)

                page1_full = False



                fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'] * 0.8)
                if notice != None :
                    fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm, notice.piedPage)
                else :
                    fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])

                compteur=0
                for p in story_page1:
                    if page1_full == False :
                        compteur+=1
                        if frameAppreciations.add(p,fichierBulletins) == 0 :
                            page1_full = True
                            fichierBulletins.setFont(dictParamBulletins['font'],
                                                     size=dictParamBulletins['fontSize'] * 0.8)
                            if notice != None:
                                fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm, notice.piedPage)
                            else:
                                fichierBulletins.drawCentredString(10.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])
                            story_page2.append(p)
                    else :
                        story_page2.append(p)


                #Frame saturée mais il reste des éléments dans la liste...
                if story_page2 != []:
                    fichierBulletins.drawString(20 * cm, 0.5 * cm, "1/2")
                    fichierBulletins.showPage()
                    frameAppreciations_page2 = Frame(x1=0.5 * cm, y1=1 * cm, width=dictParamBulletins['largeur_tot_tab_appreciations'], height=dictParamBulletins['hauteurPage2'], showBoundary=0,
                                               leftPadding=0,
                                               topPadding=0, rightPadding=0, bottomPadding=0)
                    if self.bulletinVersionProvisoire:
                        pdf.versionProvisoire(fichierBulletins)
                    if compteur <= (numAppreciation+1) :
                        enTete=[]
                        pdf.ligneEnTeteAppreciation(enTete, dictParamBulletins)
                        frameAppreciations_page2.add(enTete[0],fichierBulletins)
                    frameAppreciations_page2.addFromList(story_page2,fichierBulletins)
                    fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'])
                    fichierBulletins.drawString(20 * cm, 0.5 * cm, "2/2")
                    fichierBulletins.setFont(dictParamBulletins['font'], size=dictParamBulletins['fontSize'] * 0.8)
                    fichierBulletins.drawString(6.5 * cm, 0.5 * cm,dictParamBulletins['piedPageBulletin'])
                fichierBulletins.showPage()


        fichierBulletins.save()

        buffer.seek(0)
        return buffer.getvalue()

class SMTPSettings(models.Model):
    """
    Modèle singleton pour stocker les paramètres SMTP.
    Une seule instance doit exister dans la base de données.
    """
    host = models.CharField(max_length=255, blank=True, null=True, verbose_name='Serveur SMTP', help_text='Ex: smtp.gmail.com')
    port = models.PositiveIntegerField(default=587, blank=True, null=True, verbose_name='Port', help_text='Port SMTP (587 pour TLS, 465 pour SSL)')
    use_tls = models.BooleanField(default=True, verbose_name='Utiliser TLS', help_text='Cocher pour TLS, décocher pour SSL')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nom d\'utilisateur', help_text='Email ou nom d\'utilisateur SMTP')
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name='Mot de passe', help_text='Mot de passe SMTP')
    from_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='Email expéditeur', help_text='Adresse email utilisée comme expéditeur par défaut')
    is_active = models.BooleanField(default=False, verbose_name='Activer l\'envoi d\'emails', help_text='Cocher pour activer l\'envoi d\'emails via SMTP')
    email_subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Objet des emails de bulletins',
        help_text='Objet personnalisé pour les emails de bulletins. Vous pouvez utiliser {prenom}, {nom} et {trimestres} comme variables.',
        default='Bulletin scolaire - {prenom} {nom} - {trimestres}'
    )
    email_message = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Message d\'accompagnement des bulletins',
        help_text='Message personnalisé qui accompagne l\'envoi des bulletins. Vous pouvez utiliser {prenom}, {nom} et {trimestres} comme variables.',
        default='Bonjour,\n\nVous trouverez ci-joint le bulletin scolaire de {prenom} {nom} pour {trimestres}.\n\nCordialement,\nL\'équipe de l\'École Mathias Grünewald'
    )
    
    class Meta:
        verbose_name = 'Paramètres SMTP'
        verbose_name_plural = 'Paramètres SMTP'
    
    def __str__(self):
        return f'SMTP: {self.host}:{self.port}'
    
    def save(self, *args, **kwargs):
        """
        S'assure qu'il n'y a qu'une seule instance de SMTPSettings.
        """
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """
        Récupère l'instance unique des paramètres SMTP.
        Crée une instance par défaut si elle n'existe pas.
        """
        default_subject = 'Bulletin scolaire - {prenom} {nom} - {trimestres}'
        default_message = 'Bonjour,\n\nVous trouverez ci-joint le bulletin scolaire de {prenom} {nom} pour {trimestres}.\n\nCordialement,\nL\'équipe de l\'École Mathias Grünewald'
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'email_subject': default_subject,
                'email_message': default_message
            }
        )
        # Si l'instance existe mais n'a pas de sujet/message, utiliser les valeurs par défaut
        if not obj.email_subject:
            obj.email_subject = default_subject
        if not obj.email_message:
            obj.email_message = default_message
        if not obj.email_subject or not obj.email_message:
            obj.save()
        return obj
