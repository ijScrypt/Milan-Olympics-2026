
/* --- State ------------------------------------------------------------------- */
let queries = {};
let charts = {};
let activeTab = 'kpi';

/* ─── Utilities ─────────────────────────────────────────────────────────────── */
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

async function apiFetch(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

function animateNumber(el, target, duration = 800) {
    const start = parseInt(el.textContent) || 0;
    const range = target - start;
    const startTime = performance.now();

    function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        el.textContent = Math.round(start + range * eased).toLocaleString('fr-FR');
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

/* --- Toast System ------------------------------------------------------------ */
function showToast(message, type = 'info') {
    const container = $('#toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
        <span></span>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/* --- Connection Status ------------------------------------------------------- */
async function checkConnection() {
    const statusEl = $('#connection-status');
    try {
        await apiFetch('/kpis');
        statusEl.innerHTML = `<span class="status-dot status-dot--connected"></span><span class="status-text">Connecté</span>`;
        return true;
    } catch {
        statusEl.innerHTML = `<span class="status-dot status-dot--error"></span><span class="status-text">Déconnecté</span>`;
        return false;
    }
}

/* --- KPI Loading ------------------------------------------------------------- */
async function loadKPIs() {
    try {
        const data = await apiFetch('/kpis');
        animateNumber($('#kpi-tweets-val'), data.total_tweets);
        animateNumber($('#kpi-users-val'), data.total_users);
        animateNumber($('#kpi-hashtags-val'), data.distinct_hashtags);
        animateNumber($('#kpi-milano-val'), data.tweets_milano2026);
    } catch (err) {
        console.error('KPI load failed:', err);
        showToast('Impossible de charger les KPIs', 'error');
    }
}

/* --- Chart Config (shared) --------------------------------------------------- */
Chart.defaults.color = '#a1a1aa';
Chart.defaults.borderColor = 'rgba(63, 63, 70, 0.35)';
Chart.defaults.font.family = "'Inter', sans-serif";

const CHART_COLORS = [
    '#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e',
    '#8b5cf6', '#ec4899', '#14b8a6', '#eab308', '#ef4444'
];

const CHART_COLORS_ALPHA = CHART_COLORS.map(c => c + '33');

/* --- Charts ------------------------------------------------------------------ */
async function loadCharts() {
    await Promise.all([
        loadHashtagsChart(),
        loadLikesChart(),
        loadRolesChart(),
        loadTimelineChart()
    ]);
}

async function loadHashtagsChart() {
    try {
        const data = await apiFetch('/top-hashtags');
        const ctx = $('#chart-hashtags').getContext('2d');
        if (charts.hashtags) charts.hashtags.destroy();
        charts.hashtags = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => '#' + d.hashtag),
                datasets: [{
                    label: 'Tweets',
                    data: data.map(d => d.count),
                    backgroundColor: CHART_COLORS.map(c => c + '99'),
                    borderColor: CHART_COLORS,
                    borderWidth: 1.5,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(24,24,27,0.95)',
                        borderColor: 'rgba(99,102,241,0.3)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        titleFont: { weight: '600' },
                    }
                },
                scales: {
                    x: { grid: { color: 'rgba(63,63,70,0.2)' } },
                    y: { grid: { display: false } }
                }
            }
        });
    } catch (err) { console.error('Hashtag chart error:', err); }
}

async function loadLikesChart() {
    try {
        const data = await apiFetch('/top-tweets');
        const ctx = $('#chart-likes').getContext('2d');
        if (charts.likes) charts.likes.destroy();
        charts.likes = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.text ? d.text.substring(0, 25) + '...' : 'Tweet'),
                datasets: [{
                    label: 'Likes',
                    data: data.map(d => d.favorite_count),
                    backgroundColor: 'rgba(244, 63, 94, 0.65)',
                    borderColor: '#f43f5e',
                    borderWidth: 1.5,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(24,24,27,0.95)',
                        borderColor: 'rgba(244,63,94,0.3)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            title: (items) => {
                                const idx = items[0].dataIndex;
                                return data[idx].text || 'Tweet';
                            }
                        }
                    }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } },
                    y: { grid: { color: 'rgba(63,63,70,0.2)' } }
                }
            }
        });
    } catch (err) { console.error('Likes chart error:', err); }
}

async function loadRolesChart() {
    try {
        const data = await apiFetch('/user-roles');
        const labels = Object.keys(data);
        const values = Object.values(data);
        const ctx = $('#chart-roles').getContext('2d');
        if (charts.roles) charts.roles.destroy();
        charts.roles = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: values,
                    backgroundColor: CHART_COLORS.slice(0, labels.length).map(c => c + 'cc'),
                    borderColor: CHART_COLORS.slice(0, labels.length),
                    borderWidth: 2,
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 16, usePointStyle: true, pointStyleWidth: 12, font: { size: 12 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(24,24,27,0.95)',
                        borderColor: 'rgba(99,102,241,0.3)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                    }
                }
            }
        });
    } catch (err) { console.error('Roles chart error:', err); }
}

async function loadTimelineChart() {
    try {
        const data = await apiFetch('/tweet-timeline');
        const ctx = $('#chart-timeline').getContext('2d');
        if (charts.timeline) charts.timeline.destroy();
        charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Tweets',
                    data: data.map(d => d.count),
                    fill: true,
                    backgroundColor: 'rgba(99, 102, 241, 0.08)',
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#09090b',
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(24,24,27,0.95)',
                        borderColor: 'rgba(99,102,241,0.3)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45, font: { size: 10 }, maxTicksLimit: 15 }
                    },
                    y: { grid: { color: 'rgba(63,63,70,0.2)' }, beginAtZero: true }
                }
            }
        });
    } catch (err) { console.error('Timeline chart error:', err); }
}

/* --- Query System ------------------------------------------------------------ */
async function loadPopularHashtags() {
    const paramInput = $('#query-param');
    try {
        const hashtags = await apiFetch('/top-hashtags');
        paramInput.innerHTML = '<option value=""> Choisir un hashtag </option>';
        hashtags.forEach(h => {
            const opt = document.createElement('option');
            opt.value = h.hashtag;
            opt.textContent = '#' + h.hashtag + ` (${h.count})`;
            paramInput.appendChild(opt);
        });
        // Default select if milano2026 is present
        if (hashtags.some(h => h.hashtag === 'milano2026')) {
            paramInput.value = 'milano2026';
        }
    } catch (err) {
        console.error('Hashtag load error:', err);
        paramInput.innerHTML = '<option value="milano2026"> milano2026 (par défaut) </option>';
    }
}

async function loadQueries() {
    try {
        queries = await apiFetch('/queries');
        updateQueryOptions();
    } catch (err) {
        console.error('Query load error:', err);
    }
}

function updateQueryOptions() {
    const select = $('#query-select');
    const currentVal = select.value;
    select.innerHTML = '<option value=""> Choisir une requête </option>';

    // Sort keys logically by number or label if you like, but keys are already in roughly OK order
    for (const [id, q] of Object.entries(queries)) {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = q.label;
        select.appendChild(opt);
    }
    select.value = currentVal;
    onQuerySelect({ target: select });
}

function onQuerySelect(e) {
    const id = e.target.value;
    const btn = $('#btn-execute');
    const desc = $('#query-description');
    const paramWrap = $('#query-param-wrapper');
    
    if (id && queries[id]) {
        btn.disabled = false;
        desc.textContent = queries[id].description;
        
        // Show parameter input for hashtag-specific queries
        if (id === 'q4_count_tweets_hashtag' || id === 'q5_distinct_users_milano2026') {
             paramWrap.style.display = 'block';
             loadPopularHashtags();
        } else {
             paramWrap.style.display = 'none';
        }
    } else {
        btn.disabled = true;
        desc.textContent = '';
        paramWrap.style.display = 'none';
    }
}

async function executeQuery() {
    const select = $('#query-select');
    const queryId = select.value;
    if (!queryId) return;

    const btn = $('#btn-execute');
    const resultEl = $('#query-result');
    btn.classList.add('btn--loading');

    const payload = { query_id: queryId };
    
    // Add optional parameter if provided
    const paramInput = $('#query-param');
    if (paramInput && (queryId === 'q4_count_tweets_hashtag' || queryId === 'q5_distinct_users_milano2026') && paramInput.value.trim()) {
        payload.param = paramInput.value.trim();
    }

    try {
        $('#query-result-placeholder').style.display = 'none';
        $('#query-result-split').style.display = 'flex';

        const spinHtml = '<div class="panel-empty-state"><div style="width:24px;height:24px;border:3px solid var(--accent-indigo);border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite"></div><p>Chargement...</p></div>';
        $('#result-mongo-content').innerHTML = spinHtml;
        $('#result-neo4j-content').innerHTML = spinHtml;

        const res = await apiFetch('/execute', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        renderQueryResultBoth(res);

        showToast(`Requête exécutée avec succès`, 'success');
    } catch (err) {
        $('#query-result-placeholder').style.display = 'flex';
        $('#query-result-split').style.display = 'none';
        $('#query-result-placeholder').innerHTML = `<div class="query-result__placeholder" style="color:var(--accent-rose);">
            <p>Erreur : ${err.message}</p>
        </div>`;
        showToast('Erreur lors de l\'exécution', 'error');
    } finally {
        btn.classList.remove('btn--loading');
    }
}

function renderQueryResultBoth(res) {
    const result = res.result || res;
    const query = res.query || {};
    const queryId = $('#query-select').value;
    
    // Fallback if the backend returned no_data wrapper (from previous code)
    const actualResult = result.no_data ? {} : result;
    const dataList = actualResult.data || [];
    const theCount = actualResult.count;

    const mongoContainer = $('#result-mongo-content');
    const neo4jContainer = $('#result-neo4j-content');

    // MONGODB PANEL (Text / Table)
    if (theCount !== undefined && !actualResult.data) {
        mongoContainer.innerHTML = `
            <div class="query-result__count" style="height: 100%; justify-content: center;">
                <div>
                    <div class="result-big-number">${theCount.toLocaleString('fr-FR')}</div>
                    <div class="result-big-label">${query.label || ''}</div>
                </div>
            </div>
        `;
    } else if (dataList.length > 0 && typeof dataList[0] === 'string') {
        mongoContainer.innerHTML = `
            <div class="result-table-wrapper" style="height:100%; overflow:auto;">
                <table class="result-table">
                    <thead><tr><th>Résultats</th></tr></thead>
                    <tbody>${dataList.map(item => `<tr><td>${escapeHtml(item)}</td></tr>`).join('')}</tbody>
                </table>
            </div>
        `;
    } else if (dataList.length > 0) {
        const keys = Object.keys(dataList[0]).filter(k => k !== '_id' && k !== 'tweets');
        let countHtml = '';
        if (theCount !== undefined) {
            countHtml = `<div style="padding: var(--space-md) var(--space-xl) 0; color: var(--text-secondary); font-size: 0.82rem;">Total : <strong style="color:var(--text-primary)">${theCount}</strong> résultats</div>`;
        }

        mongoContainer.innerHTML = `
            ${countHtml}
            <div class="result-table-wrapper" style="overflow:auto; height: 100%;">
                <table class="result-table">
                    <thead><tr>${keys.map(k => `<th>${k}</th>`).join('')}</tr></thead>
                    <tbody>
                        ${dataList.map(row => `<tr>${keys.map(k => `<td title="${escapeHtml(String(row[k] ?? ''))}">${escapeHtml(formatCell(row[k]))}</td>`).join('')}</tr>`).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else {
        mongoContainer.innerHTML = `<pre class="result-json" style="padding: var(--space-md);">${JSON.stringify(actualResult, null, 2)}</pre>`;
    }


    // NEO4J PANEL (Interactive Graph)
    neo4jContainer.innerHTML = '<div class="graph-box" style="width:100%; height:100%; min-height:400px; background:var(--bg-base);"></div>';
    const graphContainer = neo4jContainer.querySelector('.graph-box');
    
    let nodesData = [], edgesData = [];
    
    // Graph construction for ALL queries
    if (['q1_count_users', 'q2_count_tweets', 'q3_count_distinct_hashtags', 'q4_count_tweets_hashtag'].includes(queryId)) {
        nodesData.push({ id: 1, label: String(theCount || 0), value: theCount || 10, title: query.label, color: '#6366f1', font: {size: 24, bold: true} });
    } else if (queryId === 'q5_distinct_users_milano2026') {
        const hLabel = $('#query-param') && $('#query-param').value ? '#' + $('#query-param').value : '#milano2026';
        nodesData.push({ id: 'Root', label: hLabel, color: '#f59e0b', font: {size: 18} });
        dataList.forEach((u, i) => {
            nodesData.push({ id: u.user_id || i, label: escapeHtml(u.username || 'User ' + i), color: '#06b6d4' });
            edgesData.push({ from: u.user_id || i, to: 'Root', label: 'TWEETED' });
        });
    } else if (queryId === 'q6_reply_tweets') {
        dataList.forEach((t) => {
            nodesData.push({ id: t.tweet_id, label: escapeHtml(t.text || '').substring(0, 20) + '...', color: '#10b981' });
            if (t.in_reply_to_tweet_id) {
                nodesData.push({ id: t.in_reply_to_tweet_id, label: 'Parent Tweet', color: '#6366f1' });
                edgesData.push({ from: t.tweet_id, to: t.in_reply_to_tweet_id, label: 'REPLY_TO' });
            }
        });
    } else if (queryId === 'q12_top_10_tweets_likes') {
        dataList.forEach(t => {
            nodesData.push({ id: t.tweet_id, label: escapeHtml(t.text || '').substring(0,25) + '...', value: t.favorite_count || 10, title: t.favorite_count + ' likes', color: '#f43f5e' });
        });
    } else if (queryId === 'q13_top_10_hashtags') {
        dataList.forEach((h, i) => {
            const hName = h._id || h.hashtag || 'Tag'+i;
            nodesData.push({ id: hName, label: '#' + hName, value: h.count || 10, title: h.count + ' occurrences', color: '#8b5cf6' });
        });
    } else if (['q7_neo4j_milano_ops_followers', 'q8_neo4j_milano_ops_following', 'q9_neo4j_mutual_follows'].includes(queryId)) {
        nodesData.push({id: 'MilanoOps', label: 'MilanoOps', group: 'Target', color: '#f59e0b', font: {size: 16}});
        dataList.forEach(user => {
            nodesData.push({id: user, label: user, color: '#06b6d4'});
            if (queryId === 'q7_neo4j_milano_ops_followers') edgesData.push({from: user, to: 'MilanoOps', label: 'FOLLOWS'});
            if (queryId === 'q8_neo4j_milano_ops_following') edgesData.push({from: 'MilanoOps', to: user, label: 'FOLLOWS'});
            if (queryId === 'q9_neo4j_mutual_follows') edgesData.push({from: user, to: 'MilanoOps', label: 'MUTUAL', arrows: 'to, from'});
        });
    } else if (['q10_neo4j_hubs'].includes(queryId)) {
        dataList.forEach(user => {
            nodesData.push({id: user.user_id, label: escapeHtml(user.username), value: user.follower_count, title: user.follower_count + ' followers', color: '#f43f5e'});
        });
    } else if (['q11_neo4j_active_followers'].includes(queryId)) {
        dataList.forEach(user => {
            nodesData.push({id: user.user_id, label: escapeHtml(user.username), value: user.following_count, title: user.following_count + ' following', color: '#06b6d4'});
        });
    } else if (['q14_neo4j_conversation_roots'].includes(queryId)) {
        dataList.forEach(t => nodesData.push({id: t.tweet_id, label: escapeHtml(t.text || '').substring(0,25)+'...', color: '#10b981'}));
    } else if (['q15_neo4j_longest_discussion'].includes(queryId)) {
        let prevId = null;
        dataList.forEach((t) => {
            nodesData.push({id: t.tweet_id, label: escapeHtml(t.text || '').substring(0,25)+'...', color: '#10b981'});
            if (prevId) edgesData.push({from: prevId, to: t.tweet_id, label: 'REPLY_TO'});
            prevId = t.tweet_id;
        });
    } else if (['q16_neo4j_thread_extents'].includes(queryId)) {
        dataList.forEach(ext => {
            const firstId = ext.first_tweet_id + '_s';
            const lastId = ext.last_tweet_id + '_e';
            nodesData.push({id: firstId, label: 'Root: ' + escapeHtml(ext.first_tweet_text || '').substring(0,20), color: '#f59e0b'});
            if (ext.last_tweet_id && ext.last_tweet_id !== ext.first_tweet_id) {
                nodesData.push({id: lastId, label: 'Leaf: ' + escapeHtml(ext.last_tweet_text || '').substring(0,20), color: '#10b981'});
                edgesData.push({from: lastId, to: firstId, label: 'ENDS_AT'});
            }
        });
    }

    const safeNodesData = [];
    const existingNodeIds = new Set();
    for (const n of nodesData) {
        if (!existingNodeIds.has(n.id)) {
            existingNodeIds.add(n.id);
            safeNodesData.push(n);
        } else if (n.label && n.label !== 'Parent Tweet') {
            const existing = safeNodesData.find(x => x.id === n.id);
            if (existing && existing.label === 'Parent Tweet') existing.label = n.label;
        }
    }

    const safeEdgesData = [];
    const existingEdgeKeys = new Set();
    for (const e of edgesData) {
        const key = `${e.from}-${e.to}-${e.label}`;
        if (!existingEdgeKeys.has(key)) {
            existingEdgeKeys.add(key);
            safeEdgesData.push(e);
        }
    }

    new vis.Network(graphContainer, {nodes: safeNodesData, edges: safeEdgesData}, {
        nodes: { shape: 'dot', size: 15, font: { color: getComputedStyle(document.body).getPropertyValue('--text-primary'), size: 12 } },
        edges: { color: { color: '#6366f1', highlight: '#06b6d4' }, font: { color: '#a1a1aa', size: 10, align: 'middle' }, arrows: 'to' },
        physics: { forceAtlas2Based: { springLength: 100 }, solver: 'forceAtlas2Based', stabilization: { iterations: 150 } }
    });
}

function formatCell(val) {
    if (val === null || val === undefined) return '—';
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'string' && val.length > 60) return val.substring(0, 57) + '...';
    return String(val);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* --- Tabs Switching -------------------------------------------------------- */
function setupTabs() {
    // Initial State
    $('#kpi-section').style.display = '';
    $('.charts-section').style.display = '';
    $('#query-section').style.display = 'none';
    const ds = $('#data-section');
    if(ds) ds.style.display = 'none';

    $$('.db-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            activeTab = tab.dataset.tab;
            $$('.db-tab').forEach(t => t.classList.remove('db-tab--active'));
            tab.classList.add('db-tab--active');

            const isKpi = activeTab === 'kpi';
            const isQueries = activeTab === 'queries';
            const isData = activeTab === 'data';

            $('#kpi-section').style.display = isKpi ? '' : 'none';
            $('.charts-section').style.display = isKpi ? '' : 'none';
            $('#query-section').style.display = isQueries ? '' : 'none';
            if(ds) ds.style.display = isData ? '' : 'none';
        });
    });
}

/* --- Re-seed ----------------------------------------------------------------- */
async function reseed() {
    const btn = $('#btn-seed');
    btn.classList.add('btn--loading');
    try {
        await apiFetch('/seed', { method: 'POST' });
        showToast('Base de données re-seedée avec succès !', 'success');
        // Reload everything
        await Promise.all([loadKPIs(), loadCharts()]);
    } catch (err) {
        showToast('Erreur lors du re-seed', 'error');
    } finally {
        btn.classList.remove('btn--loading');
    }
}

/* --- Init -------------------------------------------------------------------- */
async function init() {
    setupTabs();

    // Event listeners
    $('#query-select').addEventListener('change', onQuerySelect);
    $('#btn-execute').addEventListener('click', executeQuery);
    $('#btn-seed').addEventListener('click', reseed);

    // Check connection & load data
    const connected = await checkConnection();
    if (connected) {
        showToast('Connecté à MongoDB avec succès', 'success');
        await Promise.all([loadKPIs(), loadCharts(), loadQueries()]);
    } else {
        showToast('Impossible de se connecter au serveur. Lancez api.py d\'abord.', 'error');
    }
}

/* --- Data CRUD --------------------------------------------------------------- */
function showForm(type, action) {
    const panel = document.getElementById(`data-${type}s-panel`);
    if (!panel) return;
    
    // Hide all forms AND the empty state
    panel.querySelectorAll('.data-form-container').forEach(el => el.style.display = 'none');
    const emptyState = document.getElementById(`${type}-crud-empty`);
    if (emptyState) emptyState.style.display = 'none';

    const formContainer = document.getElementById(`form-${type}-${action}`);
    if (formContainer) {
        formContainer.style.display = 'block';
    }
}

async function submitCrud(event, resourceType, method) {
    event.preventDefault();
    const form = event.target;
    const btn = form.querySelector('button[type="submit"]');
    btn.classList.add('btn--loading');
    btn.disabled = true;

    try {
        let endpoint = `/${resourceType}`;
        let payload = {};
        const inputs = form.querySelectorAll('input, select, textarea');
        let idField = null;

        inputs.forEach(input => {
            if (input.id.includes('-id') && !input.id.includes('userid')) {
                idField = parseInt(input.value);
            } else if (input.id.includes('userid')) {
                if (input.value !== '') payload.user_id = parseInt(input.value);
            } else if (input.id.includes('username')) {
                if (input.value) payload.username = input.value;
            } else if (input.id.includes('role')) {
                if (input.value) payload.role = input.value;
            } else if (input.id.includes('country')) {
                if (input.value) payload.country = input.value;
            } else if (input.id.includes('text')) {
                if (input.value) payload.text = input.value;
            } else if (input.id.includes('hashtags')) {
                if (input.value) payload.hashtags = input.value.split(',').map(s => s.trim().toLowerCase()).filter(s => s);
            } else if (input.id.includes('fav')) {
                if (input.value !== '') payload.favorite_count = parseInt(input.value);
            } else if (input.id.includes('reply')) {
                if (input.value !== '') payload.in_reply_to_tweet_id = parseInt(input.value);
            }
        });

        if (method !== 'POST' && idField !== null) {
            endpoint += `/${idField}`;
        }

        if (method === 'DELETE') {
            payload = undefined;
        }

        const res = await apiFetch(endpoint, {
            method: method,
            body: payload ? JSON.stringify(payload) : null
        });

        if (res.success) {
            showToast(`${method} réussi pour ${resourceType}`, 'success');
            form.reset();
            form.parentElement.style.display = 'none';
            
            // Show empty state again
            const type = resourceType.endsWith('s') ? resourceType.slice(0, -1) : resourceType;
            const emptyState = document.getElementById(`${type}-crud-empty`);
            if (emptyState) emptyState.style.display = 'flex';
            
            await Promise.all([loadKPIs(), loadCharts()]);
        } else {
            showToast(`Erreur: ${res.error}`, 'error');
        }

    } catch (err) {
        console.error(err);
        showToast(`Erreur technique: ${err.message}`, 'error');
    } finally {
        btn.classList.remove('btn--loading');
        btn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', init);
