"""
URL configuration for EMG_Bulletins_GC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
import bulletins.views
import authentication.views


urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', LoginView.as_view(template_name='authentication/login.html', redirect_authenticated_user=True),name='login'),
    path('',authentication.views.login_page,name='login'),
    path('logout/', authentication.views.logout_user, name='logout'),
    #path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('home/', bulletins.views.home, name='home'),

    #gestion des classes

    path('classes/',bulletins.views.classes_list,name='classes_list'),
    path('classesAdmin/',bulletins.views.classes_list_admin,name='classes_list_admin'),
    path('classes/<int:id>',bulletins.views.classe_detail,name='classe_detail'),
    path('classe/<int:idClasse>/<int:idEleve>/remove',bulletins.views.classe_eleve_remove,name='classe_eleve_remove'),
    path('classes/<int:id>/change',bulletins.views.classe_change,name='classe_change'),
    path('classes/<int:id>/delete',bulletins.views.classe_delete,name='classe_delete'),

    #Gestion du journal d'administration
    path('journal/',bulletins.views.journal_list,name='journal_list'),
    path('journal/delete', bulletins.views.journal_delete, name='journal_delete'),

    #gestion des élèves

    path('eleves/admin',bulletins.views.eleves_list_admin,name='eleves_list_admin'),
    path('eleves/',bulletins.views.eleves_list,name='eleves_list'),
    path('anciens_eleves/',bulletins.views.anciens_eleves_list,name='anciens_eleves_list'),
    path('eleves/<int:id>',bulletins.views.eleve_detail,name='eleve_detail'),
    path('eleves/<int:id>/change',bulletins.views.eleve_change,name='eleve_change'),
    path('eleves/<int:id>/delete',bulletins.views.eleve_delete,name='eleve_delete'),

    #configuration des trimestre _ pas d'opérations d'ajout possible

    path('trimestres/change',bulletins.views.trimestres_change,name='trimestres_change'),

    #configuration des absences

    path('absences_retards',bulletins.views.absences_retards_select_list,name='absences_retards'),
    path('absences_retards/<int:idClasse>/<int:idTrimestre>/change',bulletins.views.absences_retards_select_classe_change,name='absences_retards_classe_change'),

    #supervision des absences & retards
    path('absences_retards/admin/', bulletins.views.absences_retards_select_list, name='absences_admin_retards'),
    path('absences_retards/admin/<int:idClasse>/<int:idTrimestre>/change',bulletins.views.absences_retards_select_classe_change, name='absences_admin_retards_classe_change'),

    #Configuration des exportations et importations en CSV

    path('export_csv',bulletins.views.export_csv,name='export_csv'),
    path('export_csv/eleves',bulletins.views.export_csv_eleves,name='export_eleves_csv'),
    path('export_csv/journal', bulletins.views.export_csv_journal, name='export_journal_csv'),
    path('export_csv/eleves_actifs', bulletins.views.export_csv_eleves_actifs, name='export_eleves_actifs_csv'),
    path('export_csv/disciplines', bulletins.views.export_csv_disciplines, name='export_disciplines_csv'),
    path('export_csv/disciplines_actives', bulletins.views.export_csv_disciplines_actives, name='export_disciplines_actives_csv'),
    path('export_csv/stages_actives',bulletins.views.export_csv_stages_actives,name='export_stages_actives_csv'),
    path('export_csv/stages',bulletins.views.export_csv_stages,name='export_stages_csv'),
    path('export_csv/appreciations', bulletins.views.export_csv_appreciations, name='export_appreciations_csv'),
    path('export_csv/appreciations_actives', bulletins.views.export_csv_appreciations_actives, name='export_appreciations_actives_csv'),
    path('import_csv',bulletins.views.import_csv,name='import_csv'),
    path('import_csv/eleves/',bulletins.views.import_eleve_csv,name='import_csv_eleves'),
    path('import_csv/stages/', bulletins.views.import_stage_csv, name='import_csv_stages'),
    path('import_csv/projets/', bulletins.views.import_projet_csv, name='import_csv_projets'),
    path('import_csv/disciplines/', bulletins.views.import_discipline_csv, name='import_csv_disciplines'),
    path('import_csv/appreciations/', bulletins.views.import_appreciation_csv, name='import_csv_appreciations'),

    #Enseignements (Consultation)

    path('disciplines',bulletins.views.disciplines_list,name='disciplines_liste'),
    path('my_disciplines',bulletins.views.my_disciplines_list,name='my_disciplines_liste'),
    path('disciplines/add', bulletins.views.discipline_add, name='discipline_add'),
    path('disciplines/<int:idDiscipline>/delete', bulletins.views.discipline_delete, name='discipline_delete'),
    path('disciplines/<int:idDiscipline>/evaluate', bulletins.views.discipline_evaluate, name='discipline_evaluate'),
    path('disciplines/<int:idDiscipline>/change', bulletins.views.discipline_change, name='discipline_change'),
    path('disciplines/<int:idDiscipline>/eleve/change', bulletins.views.disciplineEleve_change,name='discipline_eleve_change'),
    path('disciplines/<int:idDiscipline>/eleve/detail', bulletins.views.disciplineEleve_detail,name='discipline_eleve_detail'),
    path('disciplines/<int:idDiscipline>/detail', bulletins.views.discipline_detail, name='discipline_detail'),

    #Enseignements (Supervision)
    path('disciplines/admin', bulletins.views.disciplines_list_admin, name='disciplines_liste_admin'),
    path('disciplines/admin/<int:idDiscipline>/eleve/detail', bulletins.views.disciplineEleve_detail,name='discipline_admin_eleve_detail'),
    path('disciplines/admin/<int:idDiscipline>/eleve/change', bulletins.views.disciplineEleve_change,name='discipline_admin_eleve_change'),
    path('discipline/admin/<int:idDiscipline>/evaluate', bulletins.views.discipline_evaluate,name='discipline_admin_evaluate'),
    path('disciplines/admin/<int:idDiscipline>/change', bulletins.views.discipline_change, name='discipline_admin_change'),
    path('disciplines/admin/<int:idDiscipline>/delete', bulletins.views.discipline_delete, name='discipline_admin_delete'),

    #Les corrections - des disciplines, les stages et les projets
    path('corrections/',bulletins.views.corrections_list,name='corrections_liste'),
    path('my_corrections/', bulletins.views.my_corrections_list, name='my_corrections_liste'),
    path('corrections/<int:idDiscipline>/',bulletins.views.correction_discipline_detail,name='correction_discipline_detail'),
    path('corrections/stages/<int:idStage>/', bulletins.views.correction_stage_detail,name='correction_stage_detail'),
    path('corrections/projets/<int:idProjet>/', bulletins.views.correction_projet_detail,name='correction_projet_detail'),
    path('my_corrections/<int:idDiscipline>/',bulletins.views.my_correction_discipline_detail,name='my_correction_discipline_detail'),
    path('my_corrections/stages/<int:idStage>/', bulletins.views.my_correction_stage_detail,name='my_correction_stage_detail'),
    path('my_corrections/projets/<int:idProjet>/', bulletins.views.my_correction_projet_detail,name='my_correction_projet_detail'),

    path('my_corrections/<int:idDiscipline>/delete',bulletins.views.my_correction_discipline_delete,name='my_correction_delete'),
    path('my_corrections/stages/<int:idStage>/delete', bulletins.views.my_correction_stage_delete,name='my_correction_stage_delete'),
    path('my_corrections/projets/<int:idProjet>/delete', bulletins.views.my_correction_projet_delete,name='my_correction_projet_delete'),

    #Corrections (Supervision)
    path('my_corrections/admin/', bulletins.views.admin_corrections_list, name='corrections_admin_liste'),
    path('my_corrections/admin/<int:idDiscipline>/', bulletins.views.my_correction_discipline_detail,name='my_correction_discipline_admin_detail'),
    path('my_corrections/admin/<int:idDiscipline>/delete', bulletins.views.my_correction_discipline_delete,name='my_correction_admin_delete'),
    path('my_corrections/admin/stages/<int:idStage>/', bulletins.views.my_correction_stage_detail,name='my_correction_stage_admin_detail'),
    path('my_corrections/admin/projets/<int:idProjet>/', bulletins.views.my_correction_projet_detail,name='my_correction_projet_admin_detail'),
    path('my_corrections/admin/stages/<int:idStage>/delete', bulletins.views.my_correction_stage_delete,name='my_correction_admin_stage_delete'),
    path('my_corrections/admin/projets/<int:idProjet>/delete', bulletins.views.my_correction_projet_delete,name='my_correction_admin_projet_delete'),

    #AvisCollège

    path('avisCollege/add', bulletins.views.avis_college_add,name='avis_college_add'),
    path('avisCollege/<int:idAvis>/delete',bulletins.views.avis_college_delete,name='avis_college_delete'),
    path('avisCollege/<int:idAvis>/change',bulletins.views.avis_college_change,name='avis_college_change'),
    path('avisCollege/',bulletins.views.avis_college_list,name='avis_college_liste'),

    #AvisCollege (supervision)
    path('avisCollege/admin/', bulletins.views.avis_college_admin_list, name='avis_college_admin_liste'),
    path('avisCollege/admin/<int:idAvis>/change', bulletins.views.avis_college_change, name='avis_college_admin_change'),
    path('avisCollege/admin/<int:idAvis>/delete', bulletins.views.avis_college_delete, name='avis_college_admin_delete'),

    #Gestion projets
    path('projets/',bulletins.views.projets_list,name='projets_liste'),
    path('my_projets/', bulletins.views.my_projets_list, name='my_projets_liste'),
    path('projets/add',bulletins.views.projets_add,name='projets_add'),
    path('projets/<int:idProjet>/change',bulletins.views.projets_change,name='projets_change'),
    path('projets/<int:idProjet>/delete', bulletins.views.projets_delete, name='projets_delete'),

    #Gestion projets (admin)
    path('projets/admin/',bulletins.views.projets_admin_list,name='projets_admin_liste'),
    path('projets/admin/<int:idProjet>/change',bulletins.views.projets_change,name='projets_admin_change'),
    path('projets/admin/<int:idProjet>/delete', bulletins.views.projets_delete, name='projets_admin_delete'),


    #Gestion stages
    path('stages/', bulletins.views.stages_list, name='stages_liste'),
    path('my_stages/', bulletins.views.my_stages_list, name='my_stages_liste'),
    path('stages/add', bulletins.views.stages_add, name='stages_add'),
    path('stages/<int:idStage>/change', bulletins.views.stages_change, name='stages_change'),
    path('stages/<int:idStage>/delete', bulletins.views.stages_delete, name='stages_delete'),

    #Gestion stages (admin)
    path('stages/admin/', bulletins.views.stages_admin_list, name='stages_admin_liste'),
    path('stages/admin/<int:idStage>/change', bulletins.views.stages_change, name='stages_admin_change'),
    path('stages/admin/<int:idStage>/delete', bulletins.views.stages_delete, name='stages_admin_delete'),


    #competenceConnaissance
    path('disciplines/<int:idDiscipline>/competenceConnaissance_list',bulletins.views.competence_connaissance_list,name='competence_connaissance_list'),
    path('disciplines/<int:idDiscipline>/competenceConnaissance_change',bulletins.views.competence_connaissance_change,name='competence_connaissance_change'),
    path('disciplines/<int:idDiscipline>/competenceConnaissance/<int:idCompetence>/delete',bulletins.views.competence_connaissance_delete,name='competence_connaissance_delete'),

    #competenceConnaissance (Supervision)
    path('discipline/admin/<int:idDiscipline>/competenceConnaissance_list', bulletins.views.competence_connaissance_list,name='competence_connaissance_admin_list'),
    path('discipline/admin/<int:idDiscipline>/competenceConnaissance_change', bulletins.views.competence_connaissance_change,name='competence_connaissance_admin_change'),
    path('discipline/admin/<int:idDiscipline>/competenceConnaissance/<int:idCompetence>/delete',bulletins.views.competence_connaissance_delete, name='competence_connaissance_admin_delete'),

    # Édition des bulletins
    path('bulletin/select/',bulletins.views.bulletins_select,name='bulletins_select'),
    path('bulletin/admin/select/', bulletins.views.bulletins_select, name='bulletins_admin_select'),

    #Édition du barême de la notice
    path('bareme/',bulletins.views.bareme_list,name='bareme_list'),
    path('bareme/admin',bulletins.views.bareme_list,name='bareme_admin_list'),
    path('bareme/add/',bulletins.views.bareme_add,name='bareme_add'),
    path('bareme/<int:idBareme>/change',bulletins.views.bareme_change,name='bareme_change'),
    path('bareme/<int:idBareme>/delete',bulletins.views.bareme_delete,name='bareme_delete'),

    #Paramètres de mise en page du bulletin
    path('mise_en_page/',bulletins.views.mise_en_page_list,name='mise_en_page_list'),
    path('mise_en_page/add/',bulletins.views.mise_en_page_add,name='mise_en_page_add'),
    path('mise_en_page/<int:idMiseEnPage>/change',bulletins.views.mise_en_page_change,name='mise_en_page_change'),
    path('mise_en_page/<int:idMiseEnPage>/delete',bulletins.views.mise_en_page_delete,name='mise_en_page_delete'),
    
    #Gestion années
    path('annee/',bulletins.views.annee_list,name='annee_list'),

    #Gestion des enseignants
    path('enseignants/',authentication.views.enseignants_list,name='enseignants_list'),
    path('profil/',authentication.views.myProfil,name="my_profil"),
]
