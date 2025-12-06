// Correcteur orthographique automatique
(function() {
    'use strict';
    
    // Configuration
    const CORRECTEUR_URL = '/api/correcteur/';
    const DEBOUNCE_DELAY = 1000; // Attendre 1 seconde après la dernière frappe
    
    // Fonction pour ajouter le bouton de correction
    function addCorrectorButton(textarea) {
        // Vérifier si le bouton existe déjà
        if (textarea.dataset.correcteurAdded === 'true') {
            return;
        }
        textarea.dataset.correcteurAdded = 'true';
        
        // Créer le wrapper pour le bouton
        const wrapper = document.createElement('div');
        wrapper.className = 'correcteur-wrapper d-flex justify-content-end mb-2';
        wrapper.style.marginTop = '10px';
        
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-secondary correcteur-btn';
        button.innerHTML = '<i class="bi bi-spellcheck"></i> Vérifier';
        
        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'correcteur-results w-100';
        resultsDiv.style.display = 'none';
        
        wrapper.appendChild(button);
        
        // Trouver le parent form-floating ou créer un conteneur
        let container = textarea.closest('.form-floating');
        if (!container) {
            container = textarea.parentElement;
        }
        
        // Insérer le wrapper avant le textarea (dans le form-floating) ou après
        if (container && container.classList.contains('form-floating')) {
            // Insérer après le label
            const label = container.querySelector('label');
            if (label && label.nextSibling) {
                container.insertBefore(wrapper, label.nextSibling);
            } else {
                container.appendChild(wrapper);
            }
            // Insérer resultsDiv après le form-floating
            container.parentNode.insertBefore(resultsDiv, container.nextSibling);
        } else {
            // Insérer avant le textarea
            textarea.parentNode.insertBefore(wrapper, textarea);
            textarea.parentNode.insertBefore(resultsDiv, textarea.nextSibling);
        }
        
        // Stocker la référence du bouton dans le textarea pour y accéder plus tard
        textarea.dataset.correcteurButton = 'true';
        textarea._correcteurButton = button;
        textarea._correcteurResults = resultsDiv;
        
        // Ajouter l'événement au bouton
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            checkText(textarea, resultsDiv, button);
        });
    }
    
    // Fonction pour normaliser les sauts de ligne
    function normalizeLineBreaks(text) {
        // Normaliser tous les types de sauts de ligne en \n
        return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    }
    
    // Fonction pour vérifier le texte
    function checkText(textarea, resultsDiv, button) {
        const text = textarea.value;
        if (!text.trim()) {
            showMessage(resultsDiv, 'Veuillez saisir du texte à vérifier.', 'warning');
            return;
        }
        
        // Normaliser le texte avant l'envoi
        const normalizedText = normalizeLineBreaks(text);
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Vérification...';
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<div class="alert alert-info">Vérification en cours...</div>';
        
        // Envoyer la requête
        const formData = new FormData();
        formData.append('text', normalizedText);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        fetch(CORRECTEUR_URL, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-spellcheck"></i> Vérifier';
            
            if (data.success && data.matches && data.matches.length > 0) {
                displayErrors(resultsDiv, data.matches, textarea, normalizedText);
            } else if (data.success) {
                showMessage(resultsDiv, '<i class="bi bi-check-circle"></i> Aucune erreur détectée !', 'success');
            } else {
                showMessage(resultsDiv, 'Erreur lors de la vérification : ' + (data.error || 'Erreur inconnue'), 'danger');
            }
        })
        .catch(error => {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-spellcheck"></i> Vérifier';
            showMessage(resultsDiv, 'Erreur de connexion au service de correction.', 'danger');
            console.error('Erreur correcteur:', error);
        });
    }
    
    // Fonction pour afficher les erreurs
    function displayErrors(resultsDiv, matches, textarea, normalizedText) {
        // Utiliser le texte normalisé pour les positions, mais stocker aussi le texte original
        const originalText = textarea.value;
        const textForPositions = normalizedText || normalizeLineBreaks(originalText);
        
        let html = '<div class="alert alert-warning"><strong>Erreurs détectées :</strong><ul class="mb-0 mt-2">';
        
        matches.forEach((match, index) => {
            const start = match.offset;
            const end = match.offset + match.length;
            // Utiliser le texte normalisé pour extraire l'erreur et le contexte
            const context = textForPositions.substring(Math.max(0, start - 20), Math.min(textForPositions.length, end + 20));
            const errorText = textForPositions.substring(start, end);
            // Échapper les sauts de ligne pour l'affichage
            const highlighted = context.replace(/\n/g, '\\n').replace(
                errorText.replace(/\n/g, '\\n'),
                '<strong class="text-danger">' + errorText.replace(/\n/g, '\\n') + '</strong>'
            );
            
            html += `<li class="mb-2" data-match-index="${index}">
                <code>${highlighted}</code><br>
                <small class="text-muted">${match.message}</small>`;
            
            if (match.replacements && match.replacements.length > 0) {
                html += '<br><small><strong>Suggestions :</strong> ';
                // Stocker l'index du match, le texte original et la position pour recalculer
                html += match.replacements.slice(0, 3).map(r => 
                    `<span class="badge bg-secondary suggestion" 
                           data-match-index="${index}" 
                           data-match-offset="${start}"
                           data-match-length="${match.length}"
                           data-error-text="${errorText.replace(/"/g, '&quot;').replace(/\n/g, '\\n')}"
                           data-replacement="${r.value.replace(/"/g, '&quot;')}">${r.value}</span>`
                ).join(' ');
                html += '</small>';
            }
            html += '</li>';
        });
        
        html += '</ul></div>';
        resultsDiv.innerHTML = html;
        
        // Stocker les matches pour pouvoir les utiliser lors du clic
        resultsDiv._matches = matches;
        resultsDiv._originalText = originalText;
        resultsDiv._normalizedText = textForPositions;
        
        // Ajouter les événements aux suggestions
        resultsDiv.querySelectorAll('.suggestion').forEach(suggestion => {
            suggestion.style.cursor = 'pointer';
            suggestion.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const matchIndex = parseInt(this.dataset.matchIndex);
                const matchOffset = parseInt(this.dataset.matchOffset);
                const matchLength = parseInt(this.dataset.matchLength);
                const replacement = this.dataset.replacement;
                
                const currentText = textarea.value;
                const match = resultsDiv._matches[matchIndex];
                const normalizedText = resultsDiv._normalizedText;
                
                // Normaliser le texte actuel pour la recherche
                const currentTextNormalized = normalizeLineBreaks(currentText);
                
                // Récupérer le texte d'erreur depuis le texte normalisé (celui utilisé par LanguageTool)
                const errorText = normalizedText.substring(matchOffset, matchOffset + matchLength);
                
                // Prendre un contexte unique avant et après pour identifier de manière unique l'erreur
                const contextBeforeLength = 15;
                const contextAfterLength = 15;
                const contextBefore = Math.max(0, matchOffset - contextBeforeLength);
                const contextAfter = Math.min(normalizedText.length, matchOffset + matchLength + contextAfterLength);
                const originalContextBefore = normalizedText.substring(contextBefore, matchOffset);
                const originalContextAfter = normalizedText.substring(matchOffset + matchLength, contextAfter);
                
                // Construire une chaîne de recherche unique : contexte avant + erreur + contexte après
                const uniqueSearchString = originalContextBefore + errorText + originalContextAfter;
                
                // Chercher cette chaîne unique dans le texte actuel normalisé
                const searchIndex = currentTextNormalized.indexOf(uniqueSearchString);
                
                if (searchIndex !== -1) {
                    // Trouvé ! Calculer la position de l'erreur dans cette chaîne
                    const errorStart = searchIndex + originalContextBefore.length;
                    const errorEnd = errorStart + matchLength;
                    
                    // Vérifier une dernière fois que le texte correspond dans le texte normalisé
                    const textAtPos = currentTextNormalized.substring(errorStart, errorEnd);
                    if (textAtPos === errorText) {
                        // Convertir la position du texte normalisé vers le texte original
                        // Fonction helper pour convertir une position normalisée en position originale
                        function normalizedToOriginalPos(normalizedPos, originalText) {
                            let originalPos = 0;
                            let normalizedCount = 0;
                            
                            for (let i = 0; i < originalText.length && normalizedCount < normalizedPos; i++) {
                                if (originalText[i] === '\r' && i + 1 < originalText.length && originalText[i + 1] === '\n') {
                                    // \r\n compte pour un seul caractère dans le texte normalisé
                                    normalizedCount++;
                                    i++; // Sauter le \n
                                    originalPos = i + 1;
                                } else if (originalText[i] === '\r' || originalText[i] === '\n') {
                                    normalizedCount++;
                                    originalPos = i + 1;
                                } else {
                                    normalizedCount++;
                                    originalPos = i + 1;
                                }
                            }
                            return originalPos;
                        }
                        
                        const realStart = normalizedToOriginalPos(errorStart, currentText);
                        const realEnd = normalizedToOriginalPos(errorEnd, currentText);
                        
                        // Appliquer la correction dans le texte original
                        textarea.value = currentText.substring(0, realStart) + replacement + currentText.substring(realEnd);
                        textarea.focus();
                        const button = textarea._correcteurButton;
                        if (button) {
                            setTimeout(() => {
                                checkText(textarea, resultsDiv, button);
                            }, 100);
                        }
                        return;
                    }
                }
                
                // Si on ne trouve pas avec le contexte unique, essayer directement la position originale normalisée
                if (matchOffset < currentTextNormalized.length) {
                    const textAtOriginalPos = currentTextNormalized.substring(matchOffset, matchOffset + matchLength);
                    if (textAtOriginalPos === errorText) {
                        // Fonction helper pour convertir une position normalisée en position originale
                        function normalizedToOriginalPos(normalizedPos, originalText) {
                            let originalPos = 0;
                            let normalizedCount = 0;
                            
                            for (let i = 0; i < originalText.length && normalizedCount < normalizedPos; i++) {
                                if (originalText[i] === '\r' && i + 1 < originalText.length && originalText[i + 1] === '\n') {
                                    normalizedCount++;
                                    i++;
                                    originalPos = i + 1;
                                } else if (originalText[i] === '\r' || originalText[i] === '\n') {
                                    normalizedCount++;
                                    originalPos = i + 1;
                                } else {
                                    normalizedCount++;
                                    originalPos = i + 1;
                                }
                            }
                            return originalPos;
                        }
                        
                        const realStart = normalizedToOriginalPos(matchOffset, currentText);
                        const realEnd = normalizedToOriginalPos(matchOffset + matchLength, currentText);
                        
                        textarea.value = currentText.substring(0, realStart) + replacement + currentText.substring(realEnd);
                        textarea.focus();
                        const button = textarea._correcteurButton;
                        if (button) {
                            setTimeout(() => {
                                checkText(textarea, resultsDiv, button);
                            }, 100);
                        }
                        return;
                    }
                }
                
                // Si vraiment introuvable, relancer la vérification complète
                const button = textarea._correcteurButton;
                if (button) {
                    checkText(textarea, resultsDiv, button);
                }
            });
        });
    }
    
    // Fonction pour afficher un message
    function showMessage(resultsDiv, message, type) {
        resultsDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }
    
    // Fonction pour obtenir le cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Initialiser le correcteur sur tous les textareas concernés
    function initCorrecteur() {
        console.log('Initialisation du correcteur...');
        
        // Trouver tous les textareas
        const allTextareas = document.querySelectorAll('textarea');
        console.log('Textareas trouvés:', allTextareas.length);
        
        // Éviter les doublons
        const processedTextareas = new Set();
        
        // Liste des champs autorisés (exactement comme demandé)
        const allowedFields = [
            'commentaire',      // Commentaire associé à une évaluation (appréciation)
            'descriptif',       // Descriptif d'un enseignement (discipline)
            'appreciation',     // Commentaire associé à un projet ou stage
            'avis'              // Avis trimestriel
        ];
        
        allTextareas.forEach(textarea => {
            // Vérifier que c'est bien un textarea et qu'il n'a pas déjà été traité
            if (textarea.tagName === 'TEXTAREA' && !processedTextareas.has(textarea)) {
                // Vérifier que le textarea est visible
                const style = window.getComputedStyle(textarea);
                const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
                const hasSize = textarea.offsetHeight > 30 || textarea.offsetWidth > 30;
                
                // Filtrer uniquement les champs autorisés
                const id = (textarea.id || '').toLowerCase();
                const name = (textarea.name || '').toLowerCase();
                
                // Vérifier si le champ correspond exactement à un des champs autorisés
                // (sans les suffixes _correction, etc.)
                let isRelevant = false;
                for (const field of allowedFields) {
                    // Correspondance exacte ou avec suffixe (mais pas _correction)
                    if (id === field || name === field || 
                        (id.includes(field) && !id.includes('correction') && !id.includes('remarque')) ||
                        (name.includes(field) && !name.includes('correction') && !name.includes('remarque'))) {
                        isRelevant = true;
                        break;
                    }
                }
                
                if (isVisible && hasSize && isRelevant) {
                    processedTextareas.add(textarea);
                    console.log('Ajout du bouton correcteur pour:', textarea.id || textarea.name);
                    addCorrectorButton(textarea);
                }
            }
        });
        
        console.log('Correcteur initialisé. Boutons ajoutés:', processedTextareas.size);
    }
    
    // Initialiser au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCorrecteur);
    } else {
        initCorrecteur();
    }
    
    // Observer les nouveaux éléments ajoutés dynamiquement (pour les formsets)
    const observer = new MutationObserver(function(mutations) {
        let shouldInit = false;
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && (node.tagName === 'TEXTAREA' || node.querySelector('textarea'))) {
                    shouldInit = true;
                }
            });
        });
        if (shouldInit) {
            // Délai pour laisser le DOM se stabiliser
            setTimeout(initCorrecteur, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();

