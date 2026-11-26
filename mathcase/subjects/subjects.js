(() => {
  const tableUrl = new URL('aixiv-subjects.tsv', document.currentScript.src);
  const allowedLevels = new Set(['Checked case', 'Supporting artifact', 'Proposed']);
  const status = document.getElementById('subject-status');
  const groups = document.getElementById('subject-groups');
  const empty = document.getElementById('subject-empty');
  const form = document.getElementById('subject-filters');
  const search = document.getElementById('subject-search');
  const fieldFilter = document.getElementById('field-filter');
  const availabilityFilter = document.getElementById('availability-filter');
  const coverageFilter = document.getElementById('coverage-filter');
  const allCount = document.getElementById('count-all');
  const openCount = document.getElementById('count-open');
  const comingCount = document.getElementById('count-coming');
  let rows = [];

  const parseTSV = (text) => {
    const lines = text.replace(/^\uFEFF/, '').trimEnd().split(/\r?\n/);
    const header = lines.shift().split('\t');
    const expected = ['code', 'name', 'field', 'submissions', 'coverage', 'topic', 'check', 'evidence'];
    if (header.join('|') !== expected.join('|')) throw new Error('The subject table has an unexpected column layout.');
    const parsed = lines.map((line) => {
      const values = line.split('\t');
      if (values.length !== expected.length) throw new Error('A row in the subject table is incomplete.');
      return Object.fromEntries(expected.map((key, index) => [key, values[index].trim()]));
    });
    if (parsed.length !== 155 || new Set(parsed.map((row) => row.code)).size !== 155) throw new Error('The subject table did not pass its 155-row integrity check.');
    if (parsed.filter((row) => row.submissions === 'open').length !== 40 || parsed.filter((row) => row.submissions === 'coming soon').length !== 115) throw new Error('The dated category totals did not match the published snapshot.');
    if (parsed.some((row) => !allowedLevels.has(row.coverage))) throw new Error('A row has an unrecognized evidence label.');
    return parsed;
  };

  const text = (tag, value, className) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = value;
    return element;
  };

  function makeCard(row) {
    const article = document.createElement('article');
    article.className = 'subject-card';
    const line = document.createElement('div');
    line.className = 'subject-code-line';
    line.append(text('span', row.code, 'subject-code'));
    const level = text('span', row.coverage, 'subject-tag');
    level.dataset.level = row.coverage === 'Checked case' ? 'checked' : row.coverage === 'Supporting artifact' ? 'supporting' : 'proposed';
    line.append(level);
    const availability = text('span', row.submissions === 'open' ? 'Open in snapshot' : 'Coming soon in snapshot', 'subject-tag');
    availability.dataset.status = row.submissions === 'open' ? 'open' : 'coming';
    line.append(availability);
    article.append(line, text('h3', row.name));
    const topic = document.createElement('p'); topic.className = 'subject-description';
    topic.append(text('strong', 'Topic: '), document.createTextNode(row.topic)); article.append(topic);
    const check = document.createElement('p'); check.className = 'subject-description';
    check.append(text('strong', 'Possible check: '), document.createTextNode(row.check)); article.append(check);
    const evidence = document.createElement('p'); evidence.className = 'subject-evidence';
    if (row.evidence && row.evidence !== '—' && /^https:\/\//i.test(row.evidence)) {
      evidence.append(document.createTextNode('Evidence: '));
      const link = document.createElement('a'); link.href = row.evidence; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Open linked artifact ↗'; evidence.append(link);
    } else if (row.coverage === 'Proposed') {
      evidence.textContent = 'No artifact linked in this row.';
    } else {
      evidence.textContent = 'Evidence link unavailable in this row.';
    }
    article.append(evidence);
    return article;
  }

  function render() {
    const query = search.value.trim().toLocaleLowerCase();
    const selectedField = fieldFilter.value;
    const selectedAvailability = availabilityFilter.value;
    const selectedCoverage = coverageFilter.value;
    const filtered = rows.filter((row) => {
      const searchable = `${row.code} ${row.name} ${row.field} ${row.topic} ${row.check} ${row.coverage}`.toLocaleLowerCase();
      return (!query || searchable.includes(query)) && (!selectedField || row.field === selectedField) && (!selectedAvailability || row.submissions === selectedAvailability) && (!selectedCoverage || row.coverage === selectedCoverage);
    });
    groups.replaceChildren();
    const order = [...new Set(rows.map((row) => row.field))].sort((a, b) => a.localeCompare(b));
    for (const field of order) {
      const matches = filtered.filter((row) => row.field === field);
      if (!matches.length) continue;
      const details = document.createElement('details'); details.className = 'subject-field'; details.open = Boolean(query || selectedField || selectedAvailability || selectedCoverage) || field === 'Mathematics';
      const summary = document.createElement('summary'); summary.append(document.createTextNode(field));
      summary.append(text('span', `${matches.length} ${matches.length === 1 ? 'category' : 'categories'}`, 'subject-field-count'));
      const cards = document.createElement('div'); cards.className = 'subject-cards';
      matches.forEach((row) => cards.append(makeCard(row)));
      details.append(summary, cards); groups.append(details);
    }
    empty.hidden = filtered.length !== 0;
    groups.setAttribute('aria-busy', 'false');
    const checked = filtered.filter((row) => row.coverage === 'Checked case').length;
    const supporting = filtered.filter((row) => row.coverage === 'Supporting artifact').length;
    const proposed = filtered.filter((row) => row.coverage === 'Proposed').length;
    status.textContent = `Showing ${filtered.length} of ${rows.length} categories: ${checked} categories with checked work, ${supporting} with supporting material, and ${proposed} proposed.`;
  }

  function fail(error) {
    groups.setAttribute('aria-busy', 'false');
    status.textContent = `The subject table could not be loaded: ${error.message}`;
    groups.replaceChildren();
    empty.hidden = false;
    empty.textContent = 'The downloadable source table and guide remain available below.';
  }

  fetch(tableUrl, { credentials: 'same-origin' }).then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.text();
  }).then((body) => {
    rows = parseTSV(body);
    allCount.textContent = String(rows.length);
    openCount.textContent = String(rows.filter((row) => row.submissions === 'open').length);
    comingCount.textContent = String(rows.filter((row) => row.submissions === 'coming soon').length);
    const values = [...new Set(rows.map((row) => row.field))].sort((a, b) => a.localeCompare(b));
    for (const value of values) fieldFilter.append(new Option(value, value));
    form.addEventListener('input', render);
    form.addEventListener('change', render);
    form.addEventListener('reset', () => requestAnimationFrame(render));
    render();
  }).catch(fail);
})();
