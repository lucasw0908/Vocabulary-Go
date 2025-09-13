const words = [];

const wordsField = document.getElementById('wordsField');
const tableBody = document.getElementById('wordsTableBody');
const englishInput = document.getElementById('englishInput');
const chineseInput = document.getElementById('chineseInput');
const addWordBtn = document.getElementById('addWordBtn');
const clearWordsBtn = document.getElementById('clearWordsBtn');
const csvInput = document.getElementById('csvInput');
const jsonInput = document.getElementById('jsonInput');

function syncHiddenField() {
    wordsField.value = JSON.stringify(words);
}

function renderTable() {
    tableBody.innerHTML = '';
    words.forEach((w, idx) => {
        const tr = document.createElement('tr');

        const tdEn = document.createElement('td');
        const tdZh = document.createElement('td');
        const tdAct = document.createElement('td');

        const enInput = document.createElement('input');
        enInput.type = 'text';
        enInput.className = 'form-control form-control-sm dark-input';
        enInput.value = w.English || '';
        enInput.oninput = () => { words[idx].English = enInput.value; syncHiddenField(); };

        const zhInput = document.createElement('input');
        zhInput.type = 'text';
        zhInput.className = 'form-control form-control-sm dark-input';
        zhInput.value = w.Chinese || '';
        zhInput.oninput = () => { words[idx].Chinese = zhInput.value; syncHiddenField(); };

        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'btn btn-outline-danger btn-sm';
        delBtn.textContent = '刪除';
        delBtn.onclick = () => { words.splice(idx, 1); renderTable(); syncHiddenField(); };

        tdEn.appendChild(enInput);
        tdZh.appendChild(zhInput);
        tdAct.appendChild(delBtn);

        tr.appendChild(tdEn);
        tr.appendChild(tdZh);
        tr.appendChild(tdAct);

        tableBody.appendChild(tr);
    });
}

addWordBtn.addEventListener('click', function (e) {
    e.preventDefault();
    const en = (englishInput.value || '').trim();
    const zh = (chineseInput.value || '').trim();
    if (!en || !zh) return;
    words.push({ English: en, Chinese: zh });
    englishInput.value = '';
    chineseInput.value = '';
    renderTable();
    syncHiddenField();
});

clearWordsBtn.addEventListener('click', function (e) {
    e.preventDefault();
    words.splice(0, words.length);
    renderTable();
    syncHiddenField();
});

function parseCsv(text) {
    const lines = text.split(/\r?\n/).filter(Boolean);
    if (lines.length === 0) return [];
    const header = lines[0].split(',').map(h => h.trim().toLowerCase());
    const enIdx = header.indexOf('english');
    const zhIdx = header.indexOf('chinese');
    const start = (enIdx === -1 || zhIdx === -1) ? 0 : 1;
    const result = [];
    for (let i = start; i < lines.length; i++) {
        const cols = lines[i].split(',');
        const en = (enIdx !== -1 && zhIdx !== -1) ? cols[enIdx] : cols[0];
        const zh = (enIdx !== -1 && zhIdx !== -1) ? cols[zhIdx] : cols[1];
        if (en && zh) result.push({ English: en.trim(), Chinese: zh.trim() });
    }
    return result;
}

csvInput.addEventListener('change', async function () {
    const file = csvInput.files && csvInput.files[0];
    if (!file) return;
    const text = await file.text();
    const rows = parseCsv(text);
    if (rows.length) {
        words.splice(0, words.length, ...rows);
        renderTable();
        syncHiddenField();
    }
    csvInput.value = '';
});

jsonInput.addEventListener('change', async function () {
    const file = jsonInput.files && jsonInput.files[0];
    if (!file) return;
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        if (Array.isArray(data)) {
            const normalized = data
                .map(x => ({ English: (x.English || x.english || '').toString().trim(), Chinese: (x.Chinese || x.chinese || '').toString().trim() }))
                .filter(x => x.English && x.Chinese);
            words.splice(0, words.length, ...normalized);
            renderTable();
            syncHiddenField();
        }
    } catch (e) {
        console.error(e);
    }
    jsonInput.value = '';
});

// Initialize
syncHiddenField();
renderTable();