// Configuration API
const API_URL = 'http://localhost:8000';

// État de l'application
let questionnaire = null;
let currentQuestionIndex = 0;
let responses = {
    likert: {},
    ouvertes: {}
};
let allQuestions = [];

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadQuestionnaire();
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
        addBotMessage('Désolé, une erreur est survenue. Veuillez rafraîchir la page.');
    }
});

// Charger le questionnaire depuis l'API
async function loadQuestionnaire() {
    try {
        const response = await fetch(`${API_URL}/questionnaire`);
        questionnaire = await response.json();
        
        // Préparer toutes les questions dans l'ordre
        allQuestions = [
            ...questionnaire.likert.map(q => ({ ...q, type: 'likert' })),
            ...questionnaire.ouvertes.map(q => ({ ...q, type: 'ouverte' }))
        ];
    } catch (error) {
        console.error('Erreur chargement questionnaire:', error);
        throw error;
    }
}

// Démarrer le questionnaire
function startQuestionnaire() {
    currentQuestionIndex = 0;
    responses = { likert: {}, ouvertes: {} };
    showNextQuestion();
}

// Afficher la prochaine question
function showNextQuestion() {
    if (currentQuestionIndex >= allQuestions.length) {
        submitResponses();
        return;
    }

    const question = allQuestions[currentQuestionIndex];
    const inputArea = document.getElementById('inputArea');
    
    // Afficher la progression
    const progressHtml = createProgressIndicator();
    
    if (question.type === 'likert') {
        inputArea.innerHTML = `
            ${progressHtml}
            <label class="question-label">${question.question}</label>
            <span class="question-subtitle">${question.echelle}</span>
            <div class="likert-scale">
                ${[1, 2, 3, 4, 5].map(value => `
                    <div class="likert-option">
                        <input type="radio" id="option-${value}" name="likert-response" value="${value}">
                        <label for="option-${value}">${value}</label>
                    </div>
                `).join('')}
            </div>
            <button class="btn-primary" onclick="submitLikertAnswer()">Suivant</button>
        `;
    } else {
        const placeholder = question.placeholder || 'Votre réponse...';
        inputArea.innerHTML = `
            ${progressHtml}
            <label class="question-label">${question.question}</label>
            <span class="question-subtitle">${placeholder}</span>
            <input type="text" class="text-input" id="openResponse" placeholder="${placeholder}">
            <button class="btn-primary" onclick="submitOpenAnswer()">Suivant</button>
        `;
        
        // Focus sur l'input
        setTimeout(() => document.getElementById('openResponse').focus(), 100);
        
        // Enter pour valider
        document.getElementById('openResponse').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submitOpenAnswer();
        });
    }
    
    inputArea.style.display = 'block';
}

// Créer l'indicateur de progression
function createProgressIndicator() {
    const totalQuestions = allQuestions.length;
    const dots = Array.from({ length: totalQuestions }, (_, i) => {
        const isActive = i === currentQuestionIndex;
        const isCompleted = i < currentQuestionIndex;
        return `<div class="progress-dot ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}"></div>`;
    }).join('');
    
    return `
        <div class="progress-indicator">${dots}</div>
        <div style="text-align: center; color: var(--text-secondary); margin-bottom: 20px;">
            Question ${currentQuestionIndex + 1} sur ${totalQuestions}
        </div>
    `;
}

// Soumettre une réponse Likert
function submitLikertAnswer() {
    const selected = document.querySelector('input[name="likert-response"]:checked');
    
    if (!selected) {
        alert('Veuillez sélectionner une réponse');
        return;
    }

    const question = allQuestions[currentQuestionIndex];
    const value = parseInt(selected.value);
    
    // Sauvegarder la réponse
    responses.likert[question.id] = value;
    
    // Afficher dans le chat
    addUserMessage(`${question.question}\n**Réponse:** ${value}/5`);
    
    currentQuestionIndex++;
    showNextQuestion();
}

// Soumettre une réponse ouverte
function submitOpenAnswer() {
    const input = document.getElementById('openResponse');
    const value = input.value.trim();
    
    if (!value) {
        alert('Veuillez entrer une réponse');
        return;
    }

    const question = allQuestions[currentQuestionIndex];
    
    // Parser la réponse (liste si séparée par des virgules)
    let parsedValue = value;
    if (question.type === 'liste' || question.id.includes('genres') || question.id.includes('artistes')) {
        parsedValue = value.split(',').map(item => item.trim()).filter(item => item);
    }
    
    // Sauvegarder la réponse
    responses.ouvertes[question.id] = parsedValue;
    
    // Afficher dans le chat
    addUserMessage(`${question.question}\n**Réponse:** ${value}`);
    
    currentQuestionIndex++;
    showNextQuestion();
}

// Soumettre toutes les réponses et obtenir les recommandations
async function submitResponses() {
    const inputArea = document.getElementById('inputArea');
    inputArea.style.display = 'none';
    
    const loading = document.getElementById('loading');
    loading.style.display = 'block';
    
    addBotMessage('Merci pour vos réponses ! Je suis en train d\'analyser vos préférences musicales... 🎵');

    try {
        const response = await fetch(`${API_URL}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(responses)
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la génération des recommandations');
        }

        const result = await response.json();
        loading.style.display = 'none';
        
        displayRecommendations(result);
    } catch (error) {
        loading.style.display = 'none';
        console.error('Erreur:', error);
        addBotMessage('Désolé, une erreur est survenue lors de la génération de vos recommandations. Veuillez réessayer.');
    }
}

// Afficher les recommandations
function displayRecommendations(result) {
    // Message d'introduction
    let introMessage = `🎉 Voici vos recommandations personnalisées !\n\n`;
    
    if (result.genres_preferes && result.genres_preferes.length > 0) {
        introMessage += `**Vos genres préférés:** ${result.genres_preferes.join(', ')}\n`;
    }
    
    introMessage += `**Niveau d'ouverture musicale:** ${result.niveau_ouverture}/5\n`;
    introMessage += `\n📊 J'ai analysé **${result.statistiques.nombre_elements_evalues}** éléments musicaux pour vous.`;
    
    addBotMessage(introMessage);

    // Afficher le rapport GenAI si disponible
    if (result.rapport_genai && result.rapport_genai.synthese) {
        setTimeout(() => {
            addBotMessage(`**💡 Analyse de vos goûts:**\n\n${result.rapport_genai.synthese}`);
        }, 500);
    }

    // Afficher les recommandations
    setTimeout(() => {
        displayRecommendationCards(result.recommandations);
    }, 1000);

    // Afficher le plan de progression si disponible
    if (result.rapport_genai && result.rapport_genai.plan_progression) {
        setTimeout(() => {
            addBotMessage(`**📈 Plan de découverte musicale:**\n\n${result.rapport_genai.plan_progression}`);
        }, 1500);
    }

    // Bouton pour recommencer
    setTimeout(() => {
        const restartHtml = `
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn-primary" onclick="location.reload()">✨ Nouvelle recommandation</button>
            </div>
        `;
        addBotMessage(restartHtml);
    }, 2000);
}

// Afficher les cartes de recommandation
function displayRecommendationCards(recommendations) {
    let cardsHtml = '<div style="margin-top: 20px;">';
    
    recommendations.forEach((rec, index) => {
        const scorePercent = Math.round(rec.score_global * 100);
        const genreBoost = rec.details_scores.genre_boost > 0 ? ' 🌟' : '';
        
        cardsHtml += `
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <span class="recommendation-rank">#${rec.rang}</span>
                    <span class="recommendation-score">${scorePercent}%${genreBoost}</span>
                </div>
                
                ${rec.type === 'chanson' ? `
                    <div class="recommendation-title">🎵 ${rec.nom}</div>
                    <div class="recommendation-artist">par ${rec.artiste}</div>
                    ${rec.genre ? `<span class="recommendation-genre">${rec.genre}</span>` : ''}
                    
                    ${rec.spotify_search_url ? `
                        <a href="${rec.spotify_search_url}" target="_blank" class="spotify-link">
                            <span>🎧</span>
                            <span>Écouter sur Spotify</span>
                        </a>
                    ` : ''}
                ` : `
                    <div class="recommendation-title">${getTypeIcon(rec.type)} ${rec.nom}</div>
                    ${rec.description ? `<p style="color: var(--text-secondary); margin-top: 10px;">${rec.description}</p>` : ''}
                `}
                
                <div style="margin-top: 15px; font-size: 12px; color: var(--text-secondary);">
                    <strong>Détails des scores:</strong>
                    Sémantique: ${Math.round(rec.details_scores.similarite_semantique * 100)}% | 
                    Mood: ${Math.round(rec.details_scores.mood_match * 100)}% | 
                    Préférences: ${Math.round(rec.details_scores.preferences_likert * 100)}%
                </div>
            </div>
        `;
    });
    
    cardsHtml += '</div>';
    
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">${cardsHtml}</div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Ajouter un message bot
function addBotMessage(text) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">${formatMessage(text)}</div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Ajouter un message utilisateur
function addUserMessage(text) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">${formatMessage(text)}</div>
    `;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Formater le message (markdown simple)
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// Obtenir l'icône selon le type
function getTypeIcon(type) {
    const icons = {
        'chanson': '🎵',
        'genre': '🎸',
        'mood': '😊',
        'ambiance': '🌟',
        'playlist': '📀'
    };
    return icons[type] || '🎵';
}

// Scroller vers le bas
function scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}
