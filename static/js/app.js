// State
let currentSessionId = null;
let currentAssessmentState = null;
let currentPlan = null;

// DOM Elements
const sections = ['section-hero', 'section-upload', 'section-skills', 'section-assess', 'section-results', 'section-plan'];
const navSteps = document.querySelectorAll('.nav-step');

// Show Section
function showSection(sectionId) {
    sections.forEach(id => {
        document.getElementById(id).classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    // Update Nav
    const stepIndex = sections.indexOf(sectionId) - 1; // hero is -1
    navSteps.forEach((step, idx) => {
        if (idx === stepIndex) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else if (idx < stepIndex) {
            step.classList.remove('active');
            step.classList.add('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });

    if (sectionId === 'section-assess' && currentAssessmentState) {
        scrollToBottom();
    }
}

function resetAssessment() {
    // Clear the form inputs
    document.getElementById('jdInput').value = '';
    document.getElementById('resumeTextInput').value = '';
    if (typeof removeFile === 'function') {
        removeFile(); // Clears PDF dropzone
    }

    // Reset application state
    currentSessionId = null;
    currentAssessmentState = null;
    currentPlan = null;

    // Go straight to the upload page
    showSection('section-upload');
}

// ═══ Upload Logic ═══
function toggleResumeMode(mode) {
    const isPdf = mode === 'pdf';
    document.getElementById('btnUploadPdf').classList.toggle('active', isPdf);
    document.getElementById('btnPasteText').classList.toggle('active', !isPdf);
    document.getElementById('resumePdfMode').style.display = isPdf ? 'block' : 'none';
    document.getElementById('resumeTextMode').style.display = !isPdf ? 'block' : 'none';
}

// Drag & Drop
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('resumeFile');
const dropzoneContent = document.querySelector('.dropzone-content');
const dropzoneSelected = document.getElementById('dropzoneSelected');
const fileNameDisplay = document.getElementById('fileName');

dropzone.addEventListener('click', () => {
    if (dropzoneSelected.style.display === 'none') {
        fileInput.click();
    }
});

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelection(e.target.files[0]);
    }
});

let selectedFile = null;

function handleFileSelection(file) {
    if (file.type !== 'application/pdf') {
        showError("Please upload a PDF file.");
        return;
    }
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    dropzoneContent.style.display = 'none';
    dropzoneSelected.style.display = 'flex';
}

function removeFile() {
    selectedFile = null;
    fileInput.value = '';
    dropzoneContent.style.display = 'block';
    dropzoneSelected.style.display = 'none';
}

function showError(msg) {
    const errDiv = document.getElementById('uploadError');
    errDiv.textContent = msg;
    errDiv.style.display = 'block';
    setTimeout(() => errDiv.style.display = 'none', 5000);
}

// API Call: Upload & Analyse
async function analyseDocuments() {
    const jdText = document.getElementById('jdInput').value.trim();
    if (!jdText) {
        showError("Please provide a Job Description.");
        return;
    }

    const isPdfMode = document.getElementById('btnUploadPdf').classList.contains('active');
    const resumeText = document.getElementById('resumeTextInput').value.trim();

    if (isPdfMode && !selectedFile) {
        showError("Please upload a resume PDF.");
        return;
    }
    if (!isPdfMode && !resumeText) {
        showError("Please paste your resume text.");
        return;
    }

    const btn = document.getElementById('btnAnalyse');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    loader.style.display = 'inline-flex';
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('jd_text', jdText);
        if (isPdfMode) {
            formData.append('resume_file', selectedFile);
        } else {
            formData.append('resume_text', resumeText);
        }

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Upload failed');
        }

        const result = await response.json();
        currentSessionId = result.session_id;
        
        populateSkillsOverview(result.extraction_result);
        showSection('section-skills');
    } catch (err) {
        showError(err.message);
    } finally {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
        btn.disabled = false;
    }
}

// ═══ Skills Overview ═══
function populateSkillsOverview(data) {
    const reqList = document.getElementById('requiredSkillsList');
    const canList = document.getElementById('candidateSkillsList');
    const gapList = document.getElementById('gapList');
    
    reqList.innerHTML = '';
    canList.innerHTML = '';
    gapList.innerHTML = '';

    const candidateSkillNames = data.candidate_skills.map(s => s.name.toLowerCase());

    data.required_skills.forEach(skill => {
        const hasSkill = candidateSkillNames.includes(skill.name.toLowerCase());
        const el = document.createElement('div');
        el.className = `skill-tag ${skill.importance} ${hasSkill ? 'match' : 'missing'}`;
        el.innerHTML = `${hasSkill ? '✅' : '❌'} ${skill.name}`;
        reqList.appendChild(el);
    });

    data.candidate_skills.forEach(skill => {
        const isRequired = data.required_skills.find(rs => rs.name.toLowerCase() === skill.name.toLowerCase());
        const el = document.createElement('div');
        el.className = `skill-tag ${isRequired ? 'match' : ''}`;
        el.innerHTML = `${skill.name} <span style="opacity:0.5; font-size:0.8em">(${skill.claimed_experience})</span>`;
        canList.appendChild(el);
    });

    data.initial_gaps.forEach(gap => {
        const el = document.createElement('div');
        el.className = `skill-tag ${gap.status}`;
        el.innerHTML = `⚠️ ${gap.skill} <span style="opacity:0.6; font-size:0.8em">(${gap.status})</span>`;
        gapList.appendChild(el);
    });
}

// ═══ Chat Assessment ═══
async function startAssessment() {
    const btn = document.getElementById('btnStartAssessment');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    loader.style.display = 'inline-flex';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/assess/start?session_id=${currentSessionId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to start assessment');
        
        currentAssessmentState = await response.json();
        
        document.getElementById('chatMessages').innerHTML = '';
        updateAssessmentProgress();
        showSection('section-assess');
        
        appendMessage('system', "Assessment started. Please answer the questions to the best of your ability. Keep answers concise but demonstrate practical understanding.");
        appendMessage('ai', currentAssessmentState.question.question);
        
    } catch (err) {
        alert(err.message);
    } finally {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
        btn.disabled = false;
    }
}

function updateAssessmentProgress() {
    if (!currentAssessmentState) return;
    
    const curSkill = currentAssessmentState.current_skill_number || 1;
    const totalSkills = currentAssessmentState.total_skills || 1;
    const skillName = currentAssessmentState.question?.skill_name || '...';
    
    document.getElementById('currentSkillNum').textContent = curSkill;
    document.getElementById('totalSkills').textContent = totalSkills;
    document.getElementById('currentSkillName').textContent = skillName;
    
    const pct = ((curSkill - 1) / totalSkills) * 100;
    document.getElementById('assessProgressBar').style.width = `${pct}%`;
}

function appendMessage(role, text) {
    const container = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message msg-${role}`;
    
    // Escape HTML tags to prevent them from being rendered as invisible DOM elements
    let safeText = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Simple markdown formatting (bold, newlines)
    let formattedText = safeText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    msgDiv.innerHTML = `<p>${formattedText}</p>`;
    container.appendChild(msgDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'chat-message msg-ai typing-container';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function hideTypingIndicator() {
    const ind = document.getElementById('typingIndicator');
    if (ind) ind.remove();
}

function scrollToBottom() {
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function handleChatKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitAnswer();
    }
}

async function submitAnswer() {
    const input = document.getElementById('chatInput');
    const answer = input.value.trim();
    if (!answer) return;

    input.value = '';
    input.disabled = true;
    document.getElementById('btnSend').disabled = true;

    appendMessage('user', answer);
    showTypingIndicator();

    try {
        const response = await fetch('/api/assess/answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: currentSessionId,
                answer: answer
            })
        });

        hideTypingIndicator();

        if (!response.ok) {
            let errorDetail = 'Error submitting answer. The server might have restarted.';
            try {
                const errData = await response.json();
                errorDetail = errData.detail || errorDetail;
            } catch (e) {}
            throw new Error(errorDetail);
        }
        
        const result = await response.json();
        
        // Show feedback
        appendMessage('system', `Score: ${result.evaluation.score}/5 (${result.evaluation.level})\n${result.evaluation.feedback}`);

        if (result.is_assessment_complete) {
            appendMessage('system', "Assessment complete! Generating your results...");
            document.getElementById('assessProgressBar').style.width = '100%';
            setTimeout(() => fetchResults(), 1500);
        } else {
            currentAssessmentState.current_skill_number = result.current_skill_number;
            currentAssessmentState.question = result.next_question;
            updateAssessmentProgress();
            
            if (result.is_skill_complete && result.skill_result) {
                appendMessage('system', `Moving to next skill: **${result.next_question.skill_name}**`);
            }
            
            appendMessage('ai', result.next_question.question);
        }
    } catch (err) {
        hideTypingIndicator();
        appendMessage('system', `Error: ${err.message}. Your answer was restored in the text box so you can try again!`);
        input.value = answer; // Restore the answer
    } finally {
        input.disabled = false;
        document.getElementById('btnSend').disabled = false;
        input.focus();
    }
}

// ═══ Results Dashboard ═══
async function fetchResults() {
    try {
        const response = await fetch(`/api/assess/${currentSessionId}`);
        const data = await response.json();
        
        populateResults(data.skill_scores);
        showSection('section-results');
    } catch (err) {
        alert("Error fetching results: " + err.message);
    }
}

function populateResults(scores) {
    const grid = document.getElementById('resultsGrid');
    grid.innerHTML = '';

    let totalScore = 0;

    scores.forEach(score => {
        totalScore += (score.final_score / 5);
        
        const card = document.createElement('div');
        card.className = 'skill-result-card';
        card.innerHTML = `
            <div class="skill-result-header">
                <h3>${score.skill_name}</h3>
                <span class="skill-result-score score-${Math.round(score.final_score)}">${score.final_score}/5</span>
            </div>
            <div class="skill-result-level">${score.level}</div>
        `;
        grid.appendChild(card);
    });

    const avgScore = scores.length ? (totalScore / scores.length) * 100 : 0;
    
    document.getElementById('overallScoreValue').textContent = `${Math.round(avgScore)}%`;
    
    // Update SVG Ring
    const ring = document.getElementById('scoreRingFill');
    const offset = 339.292 - (339.292 * (avgScore / 100));
    ring.style.strokeDashoffset = offset;
    
    let label = 'Needs Work';
    if (avgScore >= 80) label = 'Highly Ready';
    else if (avgScore >= 60) label = 'Ready with minor gaps';
    else if (avgScore >= 40) label = 'Needs Preparation';
    
    document.getElementById('overallScoreLabel').textContent = label;
}

// ═══ Learning Plan ═══
async function generatePlan() {
    const btn = document.getElementById('btnGeneratePlan');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    loader.style.display = 'inline-flex';
    btn.disabled = true;

    try {
        const response = await fetch('/api/plan/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId})
        });

        if (!response.ok) throw new Error('Error generating plan');
        
        const result = await response.json();
        currentPlan = result.plan;
        
        populatePlan(currentPlan);
        showSection('section-plan');
        
    } catch (err) {
        alert(err.message);
    } finally {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
        btn.disabled = false;
    }
}

function populatePlan(plan) {
    document.getElementById('planSummary').textContent = plan.summary;
    
    const strengthsUl = document.getElementById('planStrengths');
    strengthsUl.innerHTML = plan.strengths.map(s => `<li>${s}</li>`).join('');
    
    const gapsUl = document.getElementById('planGaps');
    gapsUl.innerHTML = plan.critical_gaps.map(g => `<li>${g}</li>`).join('');
    
    const timeline = document.getElementById('learningTimeline');
    timeline.innerHTML = '';
    
    plan.learning_items.forEach((item, idx) => {
        const card = document.createElement('div');
        card.className = `learning-item priority-${item.priority}`;
        
        const resourcesHtml = item.resources.map(res => `
            <a href="${res.url}" target="_blank" class="resource-link">
                <span>${res.title}</span>
                <span class="resource-type">${res.type} (${res.estimated_hours}h)</span>
            </a>
        `).join('');

        card.innerHTML = `
            <div class="learning-card">
                <div class="learning-header">
                    <div>
                        <div class="learning-skill">${item.skill_name}</div>
                        <div class="learning-progression">${item.current_level} → ${item.target_level}</div>
                    </div>
                    <div class="learning-meta">Est. ${item.estimated_weeks} weeks</div>
                </div>
                <p style="margin-bottom: 10px; color: var(--text-muted); font-size: 0.95em;">${item.why_important}</p>
                ${item.prerequisites_you_have.length ? `<p style="font-size: 0.85em; color: var(--accent-primary);">Based on your knowledge of: ${item.prerequisites_you_have.join(', ')}</p>` : ''}
                
                <div class="learning-resources">
                    <h4 style="margin-bottom: 8px;">Recommended Resources</h4>
                    <div class="resource-list">
                        ${resourcesHtml}
                    </div>
                </div>
            </div>
        `;
        timeline.appendChild(card);
    });
}

function exportPlan() {
    if (!currentPlan || !currentSessionId) return;
    
    // Open the PDF export endpoint which triggers a download in the browser
    window.open(`/api/plan/export-pdf/${currentSessionId}`, '_blank');
}
