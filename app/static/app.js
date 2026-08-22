const state = { interviewId: null, role: '', questions: [], current: 0 };
const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}
function show(id) { $(id).classList.remove('hidden'); }
function hide(id) { $(id).classList.add('hidden'); }
function showOnly(id) { ['welcome', 'interview', 'report', 'history'].forEach((view) => view === id ? show(view) : hide(view)); }

async function loadRoles() {
  const { roles } = await api('/api/roles');
  $('roleSelect').innerHTML = roles.map((role) => `<option>${role}</option>`).join('');
}
async function startInterview() {
  try {
    const data = await api('/api/interviews', { method: 'POST', body: JSON.stringify({ role: $('roleSelect').value }) });
    Object.assign(state, { interviewId: data.interview_id, role: data.role, questions: data.questions, current: 0 });
    showOnly('interview'); renderQuestion();
  } catch (error) { alert(error.message); }
}
function renderQuestion() {
  const question = state.questions[state.current];
  $('question').textContent = question.question;
  $('roleName').textContent = state.role;
  $('progressText').textContent = `${state.current + 1} / ${state.questions.length}`;
  $('progressBar').style.width = `${(state.current / state.questions.length) * 100}%`;
  $('answer').value = ''; $('wordCount').textContent = '0 words'; hide('feedback'); hide('nextButton'); show('submitButton');
  $('answer').focus();
}
async function submitAnswer() {
  const answer = $('answer').value.trim();
  if (answer.split(/\s+/).filter(Boolean).length < 5) return alert('Please write a slightly longer answer (at least 5 words).');
  const button = $('submitButton'); button.disabled = true; button.textContent = 'Analysing...';
  try {
    const result = await api('/api/answers', { method: 'POST', body: JSON.stringify({ interview_id: state.interviewId, question_index: state.current, answer }) });
    $('feedback').innerHTML = `<strong>Score: ${result.score}/100</strong><br>${result.feedback}<br><small>Method: ${result.method} · Similarity: ${result.similarity}%</small>`;
    show('feedback'); hide('submitButton'); show('nextButton');
  } catch (error) { alert(error.message); }
  finally { button.disabled = false; button.innerHTML = 'Analyse answer <span>→</span>'; }
}
async function nextQuestion() {
  state.current += 1;
  if (state.current < state.questions.length) renderQuestion(); else await finishInterview();
}
async function finishInterview() {
  try {
    const data = await api(`/api/interviews/${state.interviewId}/finish`, { method: 'POST' });
    showOnly('report'); $('overallScore').textContent = data.interview.overall_score; $('performanceLevel').textContent = data.level;
    $('reportSummary').textContent = `You completed a ${data.interview.role} practice session. Your next session will use another random set of questions.`;
    $('answerReview').innerHTML = data.answers.map((answer, i) => `<article class="review"><span class="badge">QUESTION ${String(i + 1).padStart(2, '0')} · ${answer.score}/100</span><h3>${answer.question}</h3><p>${answer.feedback}</p></article>`).join('');
  } catch (error) { alert(error.message); }
}
async function openHistory() {
  try {
    const data = await api('/api/history'); showOnly('history');
    $('historyList').innerHTML = data.history.length ? data.history.map((item) => `<div class="history-item"><span><strong>${item.role}</strong><br><small>${new Date(item.started_at).toLocaleString()}</small></span><span class="history-score">${item.overall_score}/100</span></div>`).join('') : '<p class="lead">No completed sessions yet. Your first result will appear here.</p>';
  } catch (error) { alert(error.message); }
}

$('startButton').onclick = startInterview; $('submitButton').onclick = submitAnswer; $('nextButton').onclick = nextQuestion;
$('restartButton').onclick = () => showOnly('welcome'); $('historyButton').onclick = openHistory; $('closeHistory').onclick = () => showOnly('welcome');
$('answer').addEventListener('input', () => { const words = $('answer').value.trim().split(/\s+/).filter(Boolean).length; $('wordCount').textContent = `${words} ${words === 1 ? 'word' : 'words'}`; });
loadRoles().catch((error) => alert(error.message));
