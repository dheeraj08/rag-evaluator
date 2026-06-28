from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from evaluator import evaluate, load_scores
import json

app = FastAPI(title="RAG Evaluator")

class EvalRequest(BaseModel):
    question: str
    answer: str
    context: str

@app.post("/evaluate")
def run_evaluation(request: EvalRequest):
    try:
        result = evaluate(
            question=request.question,
            answer=request.answer,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scores")
def get_scores():
    return load_scores()

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    scores = load_scores()
    scores_json = json.dumps(scores)

    avg_faithfulness = 0
    avg_relevance = 0
    avg_precision = 0
    total = len(scores)
    passed = 0
    failed = 0

    if total > 0:
        avg_faithfulness = round(sum(s["scores"]["faithfulness"] for s in scores) / total, 2)
        avg_relevance = round(sum(s["scores"]["relevance"] for s in scores) / total, 2)
        avg_precision = round(sum(s["scores"]["context_precision"] for s in scores) / total, 2)
        passed = sum(1 for s in scores if s["verdict"] == "PASS")
        failed = total - passed

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAG Evaluator — Mission Control</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; min-height: 100vh; }
    .container { max-width: 1100px; margin: 0 auto; padding: 2rem; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #222; padding-bottom: 1.5rem; }
    .header h1 { font-size: 1.4rem; font-weight: 500; color: #fff; }
    .header p { font-size: 13px; color: #666; margin-top: 4px; }
    .live-dot { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #666; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #1D9E75; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 2rem; }
    .metric-card { background: #1a1a1a; border: 1px solid #222; border-radius: 12px; padding: 1.25rem; }
    .metric-card .label { font-size: 12px; color: #666; margin-bottom: 6px; }
    .metric-card .value { font-size: 28px; font-weight: 500; }
    .metric-card .sub { font-size: 11px; color: #444; margin-top: 4px; }
    .section-title { font-size: 13px; color: #666; margin-bottom: 12px; }
    .chart-wrap { background: #1a1a1a; border: 1px solid #222; border-radius: 12px; padding: 1.25rem; margin-bottom: 2rem; }
    .queries { display: flex; flex-direction: column; gap: 10px; margin-bottom: 2rem; }
    .query-card { background: #1a1a1a; border: 1px solid #222; border-radius: 12px; padding: 1rem 1.25rem; cursor: pointer; transition: border-color 0.2s; }
    .query-card:hover { border-color: #333; }
    .query-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
    .query-question { font-size: 14px; color: #ccc; flex: 1; padding-right: 12px; line-height: 1.5; }
    .badge { font-size: 11px; padding: 3px 10px; border-radius: 6px; white-space: nowrap; font-weight: 500; }
    .badge-pass { background: rgba(29,158,117,0.15); color: #1D9E75; }
    .badge-fail { background: rgba(226,75,74,0.15); color: #E24B4A; }
    .query-scores { display: flex; gap: 16px; flex-wrap: wrap; }
    .query-scores span { font-size: 12px; color: #555; }
    .query-scores span b { color: #999; font-weight: 500; }
    .reasoning { display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid #222; }
    .reasoning p { font-size: 12px; color: #555; line-height: 1.6; margin-bottom: 6px; }
    .reasoning p b { color: #777; }
    .query-card.open .reasoning { display: block; }
    .evaluator { background: #1a1a1a; border: 1px solid #222; border-radius: 12px; padding: 1.25rem; margin-bottom: 2rem; }
    .form-group { margin-bottom: 12px; }
    .form-group label { font-size: 12px; color: #555; display: block; margin-bottom: 6px; }
    .form-group input, .form-group textarea { width: 100%; background: #111; border: 1px solid #222; border-radius: 8px; padding: 10px 12px; color: #ccc; font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.2s; resize: vertical; }
    .form-group input:focus, .form-group textarea:focus { border-color: #333; }
    .disclaimer { font-size: 11px; color: #444; margin-bottom: 12px; }
    .btn { background: #1D9E75; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; cursor: pointer; font-family: inherit; transition: opacity 0.2s; }
    .btn:hover { opacity: 0.85; }
    .btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .eval-result { margin-top: 1rem; padding: 1rem; background: #111; border-radius: 8px; border: 1px solid #222; display: none; }
    .score-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
    .score-row span { font-size: 13px; color: #666; }
    .score-row span b { font-weight: 500; }
    .empty { text-align: center; padding: 3rem; color: #444; font-size: 14px; }
    .built-by { font-size: 12px; color: #333; text-align: center; padding: 2rem 0 1rem; }
    .built-by a { color: #1D9E75; text-decoration: none; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>RAG Evaluator</h1>
      <p>Mission control — LLM output observability by <a href="https://github.com/dheeraj08" style="color:#1D9E75;text-decoration:none;">Dheeraj M</a></p>
    </div>
    <div class="live-dot"><span class="dot"></span>Live</div>
  </div>

  <div class="metrics">
    <div class="metric-card">
      <div class="label">Avg faithfulness</div>
      <div class="value" id="mFaith" style="color:""" + ("#1D9E75" if avg_faithfulness >= 0.7 else "#EF9F27" if avg_faithfulness >= 0.5 else "#E24B4A") + """">""" + str(avg_faithfulness) + """</div>
      <div class="sub" id="mFaithSub">across """ + str(total) + """ queries</div>
    </div>
    <div class="metric-card">
      <div class="label">Avg relevance</div>
      <div class="value" id="mRelev" style="color:""" + ("#1D9E75" if avg_relevance >= 0.7 else "#EF9F27" if avg_relevance >= 0.5 else "#E24B4A") + """">""" + str(avg_relevance) + """</div>
      <div class="sub" id="mRelevSub">across """ + str(total) + """ queries</div>
    </div>
    <div class="metric-card">
      <div class="label">Context precision</div>
      <div class="value" id="mPrec" style="color:""" + ("#1D9E75" if avg_precision >= 0.7 else "#EF9F27" if avg_precision >= 0.5 else "#E24B4A") + """">""" + str(avg_precision) + """</div>
      <div class="sub" id="mPrecSub">across """ + str(total) + """ queries</div>
    </div>
    <div class="metric-card">
      <div class="label">Pass rate</div>
      <div class="value" id="mPass" style="color:#fff">""" + str(passed) + "/" + str(total) + """</div>
      <div class="sub" id="mFailed">""" + str(failed) + """ flagged</div>
    </div>
  </div>

  <div class="chart-wrap">
    <p class="section-title">Score trend — last 20 queries</p>
    <div style="position:relative;height:200px;">
      <canvas id="trendChart"></canvas>
    </div>
    <div style="display:flex;gap:16px;margin-top:12px;font-size:12px;color:#555;">
      <span style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:2px;background:#1D9E75;display:inline-block;"></span>Faithfulness</span>
      <span style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:2px;background:#378ADD;display:inline-block;"></span>Relevance</span>
      <span style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:2px;background:#EF9F27;display:inline-block;"></span>Context precision</span>
    </div>
  </div>

  <p class="section-title">Live evaluator — test any LLM output</p>
  <div class="evaluator">
    <p class="disclaimer">Public demo. Do not submit confidential or sensitive information.</p>
    <div class="form-group"><label>Question</label><input type="text" id="eq" placeholder="What is RAG?" /></div>
    <div class="form-group"><label>Generated answer</label><textarea id="ea" rows="3" placeholder="The model's answer..."></textarea></div>
    <div class="form-group"><label>Retrieved context</label><textarea id="ec" rows="3" placeholder="The chunks retrieved from your vector store..."></textarea></div>
    <button class="btn" id="evalBtn" onclick="runEval()">Run evaluation</button>
    <div class="eval-result" id="evalResult">
      <div class="score-row" id="scoreRow"></div>
      <div id="verdictRow" style="font-size:13px;margin-top:6px;"></div>
    </div>
  </div>

  <p class="section-title">Recent evaluations</p>
  <div class="queries" id="queriesList"></div>

  <div class="built-by">Built by <a href="https://github.com/dheeraj08">Dheeraj M</a> — AI Engineer</div>
</div>

<script>
const initialScores = """ + scores_json + """;

function getColor(val) {
  return val >= 0.7 ? '#1D9E75' : val >= 0.5 ? '#EF9F27' : '#E24B4A';
}

function renderCards(scores) {
  const list = document.getElementById('queriesList');
  list.innerHTML = '';
  const recent = scores.slice(-20).reverse();
  if (recent.length === 0) {
    list.innerHTML = '<div class="empty">No evaluations yet — run your first query above</div>';
    return;
  }
  recent.forEach((s) => {
    const card = document.createElement('div');
    card.className = 'query-card';
    card.onclick = () => card.classList.toggle('open');
    card.innerHTML = `
      <div class="query-header">
        <div class="query-question">${s.question}</div>
        <span class="badge badge-${s.verdict.toLowerCase()}">${s.verdict}</span>
      </div>
      <div class="query-scores">
        <span>Faithfulness <b style="color:${getColor(s.scores.faithfulness)}">${s.scores.faithfulness}</b></span>
        <span>Relevance <b style="color:${getColor(s.scores.relevance)}">${s.scores.relevance}</b></span>
        <span>Context <b style="color:${getColor(s.scores.context_precision)}">${s.scores.context_precision}</b></span>
        <span>ROUGE <b style="color:#999">${s.scores.rouge_l}</b></span>
      </div>
      <div class="reasoning">
        <p><b>Faithfulness:</b> ${s.reasoning.faithfulness}</p>
        <p><b>Relevance:</b> ${s.reasoning.relevance}</p>
        <p><b>Context precision:</b> ${s.reasoning.context_precision}</p>
      </div>
    `;
    list.appendChild(card);
  });
}

function updateMetricCards(all) {
  if (all.length === 0) return;
  const avgF = all.reduce((s, x) => s + x.scores.faithfulness, 0) / all.length;
  const avgR = all.reduce((s, x) => s + x.scores.relevance, 0) / all.length;
  const avgP = all.reduce((s, x) => s + x.scores.context_precision, 0) / all.length;
  const passed = all.filter(s => s.verdict === 'PASS').length;
  const failed = all.length - passed;
  const mFaith = document.getElementById('mFaith');
  mFaith.textContent = avgF.toFixed(2);
  mFaith.style.color = getColor(avgF);
  document.getElementById('mFaithSub').textContent = 'across ' + all.length + ' queries';
  const mRelev = document.getElementById('mRelev');
  mRelev.textContent = avgR.toFixed(2);
  mRelev.style.color = getColor(avgR);
  document.getElementById('mRelevSub').textContent = 'across ' + all.length + ' queries';
  const mPrec = document.getElementById('mPrec');
  mPrec.textContent = avgP.toFixed(2);
  mPrec.style.color = getColor(avgP);
  document.getElementById('mPrecSub').textContent = 'across ' + all.length + ' queries';
  document.getElementById('mPass').textContent = passed + '/' + all.length;
  document.getElementById('mFailed').textContent = failed + ' flagged';
}

const labels = initialScores.slice(-20).map((_, i) => 'Q' + (i + 1));
const faith = initialScores.slice(-20).map(s => s.scores.faithfulness);
const relev = initialScores.slice(-20).map(s => s.scores.relevance);
const prec = initialScores.slice(-20).map(s => s.scores.context_precision);

const chart = new Chart(document.getElementById('trendChart'), {
  type: 'line',
  data: {
    labels,
    datasets: [
      { label: 'Faithfulness', data: faith, borderColor: '#1D9E75', backgroundColor: 'rgba(29,158,117,0.06)', borderWidth: 1.5, pointRadius: 2, tension: 0.3, fill: true },
      { label: 'Relevance', data: relev, borderColor: '#378ADD', backgroundColor: 'rgba(55,138,221,0.04)', borderWidth: 1.5, pointRadius: 2, tension: 0.3, fill: true },
      { label: 'Context precision', data: prec, borderColor: '#EF9F27', backgroundColor: 'rgba(239,159,39,0.04)', borderWidth: 1.5, pointRadius: 2, tension: 0.3, fill: true }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { min: 0, max: 1, ticks: { stepSize: 0.25, font: { size: 11 }, color: '#444' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      x: { ticks: { font: { size: 11 }, color: '#444', autoSkip: true, maxTicksLimit: 10 }, grid: { display: false } }
    }
  }
});

renderCards(initialScores);
updateMetricCards(initialScores);

async function refreshAll() {
  const res = await fetch('/scores');
  const all = await res.json();
  renderCards(all);
  updateMetricCards(all);
  if (all.length > 0) {
    const recent20 = all.slice(-20);
    chart.data.labels = recent20.map((_, i) => 'Q' + (i + 1));
    chart.data.datasets[0].data = recent20.map(s => s.scores.faithfulness);
    chart.data.datasets[1].data = recent20.map(s => s.scores.relevance);
    chart.data.datasets[2].data = recent20.map(s => s.scores.context_precision);
    chart.update();
  }
}

async function runEval() {
  const question = document.getElementById('eq').value.trim();
  const answer = document.getElementById('ea').value.trim();
  const context = document.getElementById('ec').value.trim();
  if (!question || !answer || !context) { alert('Please fill in all three fields'); return; }
  const btn = document.getElementById('evalBtn');
  btn.disabled = true;
  btn.textContent = 'Evaluating...';
  try {
    const res = await fetch('/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, answer, context })
    });
    const data = await res.json();
    document.getElementById('scoreRow').innerHTML = `
      <span>Faithfulness <b style="color:${getColor(data.scores.faithfulness)}">${data.scores.faithfulness}</b></span>
      <span>Relevance <b style="color:${getColor(data.scores.relevance)}">${data.scores.relevance}</b></span>
      <span>Context <b style="color:${getColor(data.scores.context_precision)}">${data.scores.context_precision}</b></span>
      <span>ROUGE <b style="color:#999">${data.scores.rouge_l}</b></span>
    `;
    document.getElementById('verdictRow').innerHTML = `Verdict: <b style="color:${data.verdict === 'PASS' ? '#1D9E75' : '#E24B4A'}">${data.verdict}</b>`;
    document.getElementById('evalResult').style.display = 'block';
    await refreshAll();
  } catch(e) {
    alert('Evaluation failed: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run evaluation';
  }
}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)