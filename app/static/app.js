const state = { interviewId: null, role: '', questions: [], current: 0, results: [] };
const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, { headers: {'Content-Type':'application/json'}, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}
function show(id) { $(id).classList.remove('hidden'); }
function hide(id) { $(id).classList.add('hidden'); }

async function loadRoles() {
  const data = await api('/api/roles');
  $('roleSelect').innerHTML = data.roles.map(role => `<option>${role}</option>`).join('');
}
async function startInterview() {
  try {
    const data = await api('/api/interviews', {method:'POST', body:JSON.stringify({role:$('roleSelect').value})});
    Object.assign(state, {interviewId:data.interview_id, role:data.role, questions:data.questions, current:0, results:[]});
    hide('welcome'); hide('report'); hide('history'); show('interview'); renderQuestion();
  } catch (error) { alert(error.message); }
}
function renderQuestion() {
  const q = state.questions[state.current];
  $('question').textContent = q.question; $('roleName').textContent = state.role;
  $('progressText').textContent = `Question ${state.current + 1} of ${state.questions.length}`;
  $('progressBar').style.width = `${(state.current / state.questions.length) * 100}%`;
  $('answer').value = ''; $('wordCount').textContent = '0 words'; hide('feedback'); hide('nextButton'); show('submitButton');
}
async function submitAnswer() {
  const answer = $('answer').value.trim();
  if (!answer) return alert('Please write an answer first.');
  $('submitButton').disabled = true; $('submitButton').textContent = 'Evaluating...';
  try {
    const result = await api('/api/answers', {method:'POST', body:JSON.stringify({interview_id:state.interviewId, question_index:state.current, answer})});
    state.results.push({...result, question:state.questions[state.current].question});
    $('feedback').innerHTML = `<strong>Score: ${result.score}/100</strong><br>${result.feedback}<br><small>Evaluation: ${result.method}</small>`;
    show('feedback'); hide('submitButton'); show('nextButton');
  } catch (error) { alert(error.message); }
  finally { $('submitButton').disabled = false; $('submitButton').textContent = 'Get feedback'; }
}
async function nextQuestion() {
  state.current++;
  if (state.current < state.questions.length) renderQuestion(); else await finishInterview();
}
async function finishInterview() {
  try {
    const data = await api(`/api/interviews/${state.interviewId}/finish`, {method:'POST'});
    hide('interview'); show('report'); $('overallScore').textContent = data.interview.overall_score; $('performanceLevel').textContent = data.level;
    $('reportSummary').textContent = `You completed a ${data.interview.role} practice interview. Review your feedback below and try again to improve.`;
    $('answerReview').innerHTML = data.answers.map((a,i) => `<article class="review"><span class="badge">Question ${i+1} · ${a.score}/100</span><h3>${a.question}</h3><p>${a.feedback}</p></article>`).join('');
  } catch(error) { alert(error.message); }
}
async function openHistory() {
  try { const data = await api('/api/history'); hide('welcome'); hide('interview'); hide('report'); show('history'); $('historyList').innerHTML = data.history.length ? data.history.map(x => `<div class="history-item"><span><strong>${x.role}</strong><br><small>${new Date(x.started_at).toLocaleString()}</small></span><strong>${x.overall_score}/100</strong></div>`).join('') : '<p>No completed interviews yet.</p>'; } catch(e) { alert(e.message); }
}
$('startButton').onclick = startInterview; $('submitButton').onclick = submitAnswer; $('nextButton').onclick = nextQuestion; $('restartButton').onclick = () => { hide('report'); show('welcome'); }; $('historyButton').onclick = openHistory; $('closeHistory').onclick = () => { hide('history'); show('welcome'); };
$('answer').addEventListener('input', () => $('wordCount').textContent = `${$('answer').value.trim().split(/\s+/).filter(Boolean).length} words`);
loadRoles().catch(e => alert(e.message));
