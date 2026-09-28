let snapshot;
let activeTab = 'browse';
let rewardFilter = 'all';
let language = localStorage.getItem('language') === 'ar' ? 'ar' : 'en';
let arabicCatalog = {};
const arabicUI = {
  'Challenges':'التحديات','Language':'اللغة','Refresh':'تحديث','Browse':'تصفح','My list':'قائمتي','Plan':'الخطة','Settings':'الإعدادات',
  'Search challenges or tasks':'ابحث عن التحديات أو المهام','Soonest expiry':'الأقرب انتهاءً','Highest player rating':'أعلى تقييم لاعب','Most coins':'أكثر عملات','Best pack quality':'أفضل حزمة',
  'All categories':'كل الفئات','Active':'نشط','All availability':'كل الحالات','Upcoming':'قادم','Expired':'منتهٍ',
  'Match plan':'خطة المباريات','Counts are per condition. One match may count toward several.':'الأعداد لكل شرط. قد تُحتسب مباراة واحدة لأكثر من شرط.',
  'English source':'النص الإنجليزي الأصلي',
  'Needs attention':'يحتاج إلى مراجعة','Completed & unavailable':'المكتمل وغير المتاح','Modes & cycles':'الأنماط والفترات','Current cycle starts':'بداية الفترات الحالية',
  'Enter a verified UTC start for each daily or weekly challenge before saving progress.':'أدخل وقت بدء مؤكداً بالتوقيت العالمي UTC لكل تحدٍ يومي أو أسبوعي قبل حفظ التقدم.',
  'Save settings':'حفظ الإعدادات','Unknown':'غير معروف','Review':'مراجعة','Coins':'عملات','Prize':'جائزة','Rating unknown':'التقييم غير معروف',
  'Your data':'بياناتك','Progress is saved only in this browser. Export a backup before clearing browser data or changing phones.':'يُحفظ تقدمك في هذا المتصفح فقط. نزّل نسخة احتياطية قبل مسح بيانات المتصفح أو تغيير الهاتف.',
  'Download backup':'تنزيل نسخة احتياطية','Import backup':'استيراد نسخة احتياطية','Backup imported.':'استُوردت النسخة الاحتياطية.',
  'Sections':'الأقسام','Search challenges':'ابحث عن التحديات','Sort challenges':'رتّب التحديات','Category':'الفئة','Availability':'الحالة','Reward type':'نوع المكافأة',
  'FC 27 in-game expiry in UTC':'تاريخ الانتهاء داخل FC 27 بالتوقيت العالمي UTC',
  'mode unspecified':'النمط غير محدد','cumulative vs single match unclear':'غير واضح إن كان العدد تراكميًا أو في مباراة واحدة',
  'qualification dependency inferred':'علاقة التأهل مستنتجة وتحتاج مراجعة','source group changed':'تغيرت المجموعة في المصدر',
  'source task changed':'تغيرت المهمة في المصدر','source deadline conflict':'تعارض في تاريخ الانتهاء',
  'conflicting user deadlines':'تعارض في تواريخ الانتهاء المدخلة','stored task unlisted':'أزيلت المهمة من المصدر',
  'Quality unknown':'جودة الحزمة غير معروفة','player':'لاعب','players':'لاعبون','Reward leaders':'أبرز المكافآت','MOST COINS':'أكثر عملات',
  'BEST RATED PACK':'أفضل حزمة تقييماً','Largest single listed prizes. Player ratings are unknown in this export.':'أكبر المكافآت الفردية المعروضة. تقييمات اللاعبين غير متوفرة في هذا التصدير.',
  'All':'الكل','Players':'اللاعبون','Packs':'الحزم','COMPLETION PRIZE':'مكافأة إكمال المجموعة','listed player':'لاعب ضمن المكافآت','pack':'حزمة',
  'Remove from list':'إزالة من القائمة','+ Add to list':'+ أضف إلى القائمة','Open FUT.GG source':'افتح المصدر في FUT.GG',
  'Record in-game expiry':'سجّل تاريخ الانتهاء من اللعبة','Only enter an expiry observed in FC 27.':'أدخل تاريخ انتهاء رأيته داخل FC 27 فقط.',
  'Stored progress for removed tasks':'تقدم محفوظ لمهام أزيلت','Manual check':'تحقق يدوي','Rewards: ':'المكافآت: ',
  'Completed':'مكتمل','Save progress':'حفظ التقدم','Available':'متاح','Exclude from plan':'استبعد من الخطة',
  'No objectives match these filters.':'لا توجد تحديات تطابق هذه الفلاتر.','Add a challenge from Browse.':'أضف تحدياً من صفحة التصفح.',
  'Conditions':'الشروط','Unscheduled':'غير مجدول','No finite match blocks can be planned with the current selections, modes, and verified cycles.':'لا يمكن تخطيط مباريات محددة بالاختيارات والأنماط والفترات المؤكدة الحالية.',
  'No unscheduled tasks.':'لا توجد مهام غير مجدولة.','No completed tasks or unavailable groups.':'لا توجد مهام مكتملة أو مجموعات غير متاحة.',
  'Updated ':'آخر تحديث: ','Saved locally.':'حُفظ محلياً.','Minimum ':'الحد الأدنى: ','Expires: ':'ينتهي: ','Cycle: ':'الفترة: ',
  'Effective expiry: ':'الانتهاء المعتمد: ','In-game observation: ':'تاريخ رُصد داخل اللعبة: ',' · recorded ':' · سُجّل ',
  'When progress was first saved: ':'عند حفظ التقدم أول مرة: ','Enter an explicit cycle start in Modes & cycles before saving progress.':'أدخل بداية فترة محددة في الأنماط والفترات قبل حفظ التقدم.',
  'No source fields or tasks changed.':'لم تتغير حقول المصدر أو المهام.','Source changes since previous refresh':'تغييرات المصدر منذ آخر تحديث',
  'Raw export and interpreted export are from different refreshes. Run the interpretation command before relying on this plan.':'التصدير الخام والتصدير المحلل من تحديثين مختلفين. أعد تشغيل التحليل قبل الاعتماد على الخطة.',
  'Cannot load app':'تعذر تحميل التطبيق','Save failed':'تعذر الحفظ','Unknown group ':'مجموعة غير معروفة ','Unavailable: ':'غير متاح: ',
  'Stored evidence remains private.':'تبقى البيانات المحفوظة خاصة.','qualifying match':'مباراة مؤهلة','qualifying matches':'مباريات مؤهلة',
  'day left':'يوم متبقٍ','days left':'أيام متبقية','challenges':'تحديات','Tasks':'المهام','details':'التفاصيل',
  'active':'نشط','upcoming':'قادم','expired':'منتهٍ','unlisted':'أزيل من القائمة','missing':'مفقود','needs review':'يحتاج مراجعة',
  'daily':'يومي','weekly':'أسبوعي','match':'مباراة','matches':'مباريات','goals':'أهداف','assists':'تمريرات حاسمة',
  'checklist':'قائمة تحقق','dependency':'متطلب سابق','manual':'يدوي','seasonal':'موسمي','campaigns':'حملات','foundations':'تأسيس',
  'live events':'فعاليات مباشرة','milestones':'إنجازات','mastery':'إتقان','fc pro':'إف سي برو',
  'squad battles':'معارك الفرق','rivals':'المنافسون','champions':'الأبطال','rush':'راش','draft':'درافت','co op':'تعاوني',
  'pve live events':'فعاليات ضد الذكاء الاصطناعي','pvp live events':'فعاليات ضد لاعبين','fc pro open ladder':'سلم إف سي برو المفتوح',
  'Semi-Pro':'شبه محترف','Professional':'محترف','World Class':'فئة عالمية','Legendary':'أسطوري','Ultimate':'ألتميت',
};
const openDetails = new Set();
const $ = (id) => document.getElementById(id);
const ui = value => language === 'ar' ? (arabicUI[value] || value) : value;
const tr = value => language === 'ar' ? (arabicCatalog[value] || value) : value;
const number = value => Number(value).toLocaleString(language === 'ar' ? 'ar-SA' : undefined);
const countUnit = (count, unit) => {
  if (language !== 'ar' || unit !== 'matches') return `${number(count)} ${label(unit)}`;
  return `${number(count)} ${count === 2 ? 'مباراتين' : count >= 3 && count <= 10 ? 'مباريات' : 'مباراة'}`;
};
function setLanguage(value) {
  language = value;
  localStorage.setItem('language', value);
  document.documentElement.lang = value;
  document.documentElement.dir = value === 'ar' ? 'rtl' : 'ltr';
  document.title = ui('Challenges') + ' · FUT.GG';
  $('language').value = value;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = ui(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = ui(el.dataset.i18nPlaceholder); });
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => { el.setAttribute('aria-label', ui(el.dataset.i18nAriaLabel)); });
  if (snapshot) render();
}
const node = (tag, className, value) => {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (value !== undefined && value !== null) n.textContent = String(value);
  return n;
};
const add = (parent, ...children) => { children.forEach(c => parent.append(c)); return parent; };
const fmt = (value) => value ? new Date(value).toLocaleString(language === 'ar' ? 'ar-SA' : undefined, {timeZoneName:'short'}) : ui('Unknown');
const label = (value) => ui(String(value || '').replaceAll('_', ' ').replaceAll('-', ' '));
const groupMap = () => new Map(snapshot.groups.map(g => [g.id, g]));
const selectedMap = () => new Map(snapshot.view.selected_groups.map(g => [g.group_id, g]));
const message = (value) => { $('message').textContent = value || ''; };
function prizeFor(group) {
  // Derive from labels so an already-running local server works too.
  const parse = value => {
    const coins = value.match(/^([\d,]+) Coins$/i);
    if (coins) return {kind:'coins', label:`${Number(coins[1].replaceAll(',','')).toLocaleString()} Coins`, coins:Number(coins[1].replaceAll(',',''))};
    if (/pack/i.test(value)) {
      const rating = value.match(/(?<!\d)(\d{2})\+/);
      const packLabel = value.replace(/^\d+\s+x\s+/i, '');
      const count = packLabel.match(/^(\d+)\s*x\s*/i);
      return {kind:'pack', label:value, quality:{minimum_rating:rating ? Number(rating[1]) : null,
        player_count:count && /player/i.test(value) ? Number(count[1]) : /\bPlayer Pack\b/i.test(value) ? 1 : null}};
    }
    if (/(point|sp|token|badge|award|consumable|manager|trophy|boost|unlock|access|pick|tifo|theme|ball)/i.test(value))
      return {kind:'other', label:value};
    const rated = value.match(/^(.+?)\s*\((\d{2})\)$/);
    return {kind:'player', label:rated ? rated[1] : value, rating:rated ? Number(rated[2]) : null};
  };
  const completion = (group.completion_rewards || []).map(parse);
  const rewards = completion.concat((group.available_rewards || []).map(parse));
  const players=rewards.filter(r=>r.kind==='player'), coins=rewards.filter(r=>r.kind==='coins');
  const packs=rewards.filter(r=>r.kind==='pack');
  const main = ['player','coins','pack'].map(kind=>completion.find(r=>r.kind===kind)).find(Boolean)
    || completion[0] || {kind:'unknown',label:'Unknown'};
  const otherPlayers=[...new Set(players.map(r=>r.label).filter(value=>main.kind!=='player'||value!==main.label))];
  const ratings=players.map(r=>r.rating).filter(r=>r!=null);
  const rankedPacks=packs.filter(r=>r.quality.minimum_rating != null).sort((a,b)=>
    b.quality.minimum_rating-a.quality.minimum_rating || (b.quality.player_count||0)-(a.quality.player_count||0));
  return {main, other_players:otherPlayers, has_player:players.length>0, has_pack:packs.length>0,
    rating:ratings.length ? Math.max(...ratings) : null,
    coins:coins.length ? Math.max(...coins.map(r=>r.coins)) : null,
    pack_quality:rankedPacks[0]?.quality||null, best_pack_label:rankedPacks[0]?.label||null};
}
function prepareSnapshot(data) {
  data.groups.forEach(group => { group.prize = prizeFor(group); });
  return data;
}

async function load() {
  try {
    const catalogResponse = await fetch('./ar.json', {cache:'no-store'});
    if (catalogResponse.ok) arabicCatalog = await catalogResponse.json();
  } catch (_) { /* English source remains usable when the catalog is unavailable. */ }
  try {
    let data;
    if (window.objectiveApi) {
      message(language === 'ar' ? 'جارٍ تحميل بيانات التحديات…' : 'Loading objectives…');
      data = await window.objectiveApi.snapshot();
      message('');
    } else {
      const response = await fetch('/api/snapshot', {cache:'no-store'});
      data = await response.json();
      if (!response.ok) throw Error(data.error || 'Cannot load app');
    }
    snapshot = prepareSnapshot(data);
    render();
  } catch (error) { message(error.message); }
}
async function post(action, data) {
  try {
    let result;
    if (window.objectiveApi) {
      result = await window.objectiveApi.update(action, data);
    } else {
      const response = await fetch('/api/' + action, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
      result = await response.json();
      if (!response.ok) throw Error(result.error || 'Save failed');
    }
    snapshot = prepareSnapshot(result);
    message(ui('Saved locally.'));
    render();
  } catch (error) { message(error.message); }
}
function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === tab));
}
function flags(parent, values) { values.forEach(v => add(parent, node('span', 'flag', label(v)))); }
function availability(group) {
  const selected = selectedMap().get(group.id);
  if (selected) return selected.availability;
  if (group.expires_at && group.expires_at <= snapshot.view.as_of) return 'expired';
  if (group.starts_at && group.starts_at > snapshot.view.as_of) return 'upcoming';
  return 'active';
}
function deadlineLabel(group, selected) {
  if (selected?.review_flags?.some(flag => flag.includes('deadline'))) return ui('Review');
  const expiry = selected ? selected.effective_expires_at : group.expires_at;
  if (!expiry) return ui('Unknown');
  const days = Math.max(0, Math.ceil((new Date(expiry) - new Date(snapshot.view.as_of)) / 86400000));
  return days === 1 ? `${number(days)} ${ui('day left')}` : `${number(days)} ${ui('days left')}`;
}
function prizeLine(prize) {
  if (prize.kind === 'player') return [tr(prize.label), prize.rating == null ? ui('Rating unknown') : language === 'ar' ? `التقييم ${number(prize.rating)}` : `${prize.rating} rated`];
  if (prize.kind === 'pack') {
    const q = prize.quality;
    return [tr(prize.label), q.minimum_rating == null ? ui('Quality unknown') : `${number(q.minimum_rating)}+${playerCountText(q.player_count)}`];
  }
  return [tr(prize.label), prize.kind === 'coins' ? ui('Coins') : ui('Prize')];
}
function playerCountText(count) { return count ? ` · ${number(count)} ${ui(count === 1 ? 'player' : 'players')}` : ''; }
function sortGroups(groups) {
  const mode = $('sort').value;
  const score = g => {
    const prize = g.prize;
    if (mode === 'rating') return prize.rating;
    if (mode === 'coins') return prize.coins;
    if (mode === 'pack') return prize.pack_quality?.minimum_rating == null ? null :
      prize.pack_quality.minimum_rating * 10000 + (prize.pack_quality.player_count || 0);
    const selected = selectedMap().get(g.id);
    if (selected?.review_flags?.some(flag => flag.includes('deadline'))) return null;
    const expiry = selected ? selected.effective_expires_at : g.expires_at;
    return expiry ? new Date(expiry).getTime() : null;
  };
  return groups.sort((a,b) => {
    const left=score(a), right=score(b);
    if (left == null && right == null) {
      if (mode === 'rating' && a.prize.has_player !== b.prize.has_player) return a.prize.has_player ? -1 : 1;
      if (mode === 'pack' && a.prize.has_pack !== b.prize.has_pack) return a.prize.has_pack ? -1 : 1;
      return tr(a.title).localeCompare(tr(b.title), language);
    }
    if (left == null) return 1;
    if (right == null) return -1;
    return (mode === 'soonest' ? left-right : right-left) || tr(a.title).localeCompare(tr(b.title), language);
  });
}
function renderRewardControls(groups) {
  const leaders = $('reward-leaders'); leaders.replaceChildren();
  const coins = [...groups].filter(g=>g.prize.coins!=null).sort((a,b)=>b.prize.coins-a.prize.coins)[0];
  const packs = [...groups].filter(g=>g.prize.pack_quality).sort((a,b)=>
    b.prize.pack_quality.minimum_rating-a.prize.pack_quality.minimum_rating ||
    (b.prize.pack_quality.player_count||0)-(a.prize.pack_quality.player_count||0))[0];
  if (coins || packs) {
    add(leaders,node('h3','reward-heading',ui('Reward leaders')));
    const row=node('div','leader-grid');
    const leader=(title,value,group,kind) => {
      const button=node('button','leader');button.type='button';
      add(button,node('small','',ui(title)),node('strong','',value),node('span','',tr(group.title)));
      button.onclick=()=>{rewardFilter=kind;$('sort').value=kind;renderBrowse();$('browse-list').scrollIntoView({behavior:'smooth',block:'start'});};
      return button;
    };
    if (coins) add(row,leader('MOST COINS',`${number(coins.prize.coins)} ${ui('Coins')}`,coins,'coins'));
    if (packs) {
      const q=packs.prize.pack_quality;
      add(row,leader('BEST RATED PACK',`${number(q.minimum_rating)}+${playerCountText(q.player_count)}`,packs,'pack'));
    }
    add(leaders,row,node('p','leader-note',ui('Largest single listed prizes. Player ratings are unknown in this export.')));
  }
  const filters=$('reward-filters');filters.replaceChildren();
  for(const [key,title] of [['all','All'],['player','Players'],['coins','Coins'],['pack','Packs']]) {
    const count=key==='all'?groups.length:groups.filter(g=>key==='player'?g.prize.has_player:key==='coins'?g.prize.coins!=null:g.prize.has_pack).length;
    const button=node('button',rewardFilter===key?'active':'',`${ui(title)} ${number(count)}`);
    button.type='button';button.setAttribute('aria-pressed',rewardFilter===key?'true':'false');
    button.onclick=()=>{rewardFilter=key; if(key==='coins'||key==='pack')$('sort').value=key;renderBrowse();};
    add(filters,button);
  }
}
function groupCard(group, selected) {
  const card = node('article','card');
  const heading = node('div','card-heading');
  const status = availability(group);
  add(heading, node('span','category',label(group.category)), node('span','deadline '+(selected?.review_flags?.some(flag=>flag.includes('deadline'))?'review':''),deadlineLabel(group,selected)));
  if (status !== 'active') add(heading,node('span','badge off',label(status)));
  add(card,heading,node('h3','',tr(group.title)));
  const prize = node('div','prize');
  const [prizeName,quality] = prizeLine(group.prize.main);
  add(prize,node('span','prize-icon',group.prize.main.kind==='player'?'★':group.prize.main.kind==='coins'?'●':group.prize.main.kind==='pack'?'▣':'·'));
  const prizeText=node('div','prize-text');add(prizeText,node('small','prize-caption',ui('COMPLETION PRIZE')),node('strong','',prizeName),node('small','',quality));add(prize,prizeText);add(card,prize);
  const metrics=node('div','reward-metrics');
  group.prize.other_players.forEach(name=>add(metrics,node('span','reward-metric',`★ ${tr(name)} · ${ui('listed player')}`)));
  if (group.prize.coins != null && group.prize.main.kind !== 'coins')
    add(metrics,node('span','reward-metric',`● ${number(group.prize.coins)} ${ui('Coins')}`));
  if (group.prize.pack_quality && group.prize.main.label !== group.prize.best_pack_label) {
    const q=group.prize.pack_quality;
    add(metrics,node('span','reward-metric',`▣ ${number(q.minimum_rating)}+ ${ui('pack')}${playerCountText(q.player_count)}`));
  }
  if (metrics.children.length) add(card,metrics);
  const actions=node('div','card-actions');
  const button = node('button', selected ? 'selected-button' : 'primary', ui(selected ? 'Remove from list' : '+ Add to list'));
  button.onclick = () => post('select', {group_id:group.id, selected:!selected});
  add(actions,button);add(card,actions);
  const detail = node('details');
  detail.open = openDetails.has(group.id);
  detail.addEventListener('toggle', () => { if (detail.open) openDetails.add(group.id); else openDetails.delete(group.id); });
  add(detail,node('summary','',`${ui('Tasks')} (${number(group.tasks.length)}) · ${ui('details')}`));
  if (selected) {
    const status = node('p','fine',ui('Effective expiry: ') + fmt(selected.effective_expires_at));
    add(detail,status);
    if (selected.review_flags.length) flags(detail,selected.review_flags);
    selected.deadline_corrections.forEach(e => add(detail,node('p','fine',ui('In-game observation: ') + fmt(e.expires_at) + ui(' · recorded ') + fmt(e.recorded_at))));
  }
  const link = node('a','fine',ui('Open FUT.GG source')); link.href = group.url; link.target = '_blank'; link.rel='noopener noreferrer'; add(detail,link);
  const deadline = node('form','deadline-form');
  const expiry = node('input'); expiry.type='text'; expiry.placeholder='YYYY-MM-DDTHH:MM:SSZ'; expiry.required=true; expiry.setAttribute('aria-label','FC 27 in-game expiry in UTC');
  const save = node('button','',ui('Record in-game expiry')); save.type='submit';
  deadline.onsubmit = event => { event.preventDefault(); post('deadline',{group_id:group.id, expires_at:expiry.value.trim(), source:'fc27_in_game'}); };
  add(deadline,expiry,save); add(detail,node('p','fine',ui('Only enter an expiry observed in FC 27.')),deadline);
  const selectedTasks = new Map((selected?.tasks || []).map(t => [t.id,t]));
  group.tasks.forEach(task => add(detail,taskCard(task, selectedTasks.get(task.id), group)));
  if (selected?.unmatched_progress?.length) {
    add(detail,node('h3','',ui('Stored progress for removed tasks')));
    selected.unmatched_progress.forEach(p => add(detail,node('p','',p.task_id + ': ' + tr(p.source_text) + ' · ' + number(p.count))));
  }
  add(card,detail);
  return card;
}
function taskCard(task, stateTask, group) {
  const div = node('div','task');
  add(div,node('strong','',tr(task.title)),node('p','',tr(task.source_text)));
  if (language === 'ar' && tr(task.source_text) !== task.source_text) {
    const original = node('p','fine original-source',`${ui('English source')}: ${task.source_text}`);
    original.lang = 'en'; original.dir = 'ltr'; add(div,original);
  }
  const bits = node('div','meta');
  add(bits,node('span','',label(task.kind)),node('span','',task.target ? countUnit(task.target.count, task.target.unit) : ui('Manual check')));
  if (task.rewards.length) add(bits,node('span','',ui('Rewards: ') + task.rewards.map(tr).join(language === 'ar' ? '، ' : ', ')));
  add(div,bits);
  flags(div,[...task.review_reasons,...(stateTask?.review_flags || [])]);
  if (stateTask?.progress && stateTask.progress.source_text !== task.source_text)
    add(div,node('p','fine',ui('When progress was first saved: ') + tr(stateTask.progress.source_text)));
  if (!stateTask) return div;
  const form = node('form','task-controls');
  const count = node('input'); count.type='number'; count.min='0'; count.step='1'; count.value=stateTask.progress?.count ?? 0; count.required=true; count.setAttribute('aria-label',(language === 'ar' ? 'العدد اليدوي لـ ' : 'Manual count for ') + tr(task.title));
  const checkLabel = node('label'); const completed=node('input'); completed.type='checkbox'; completed.checked=stateTask.progress?.completed || false;
  add(checkLabel,completed,document.createTextNode(' ' + ui('Completed')));
  const save = node('button','',ui('Save progress')); save.type='submit';
  form.onsubmit = e => { e.preventDefault(); post('progress',{task_id:task.id,count:Number(count.value),completed:completed.checked}); };
  add(form,count,checkLabel,save); add(div,form);
  if (group.repeat.cadence) add(div,node('p','fine',stateTask.progress_key ? ui('Cycle: ') + fmt(snapshot.settings.cycles[group.id]) : ui('Enter an explicit cycle start in Modes & cycles before saving progress.')));
  return div;
}
function renderBrowse() {
  const changeBox=$('source-changes');changeBox.replaceChildren();
  if(snapshot.source_changes) {
    const details=node('details','card');
    add(details,node('summary','',`${ui('Source changes since previous refresh')} (${number(snapshot.source_changes.length)})`));
    if (!snapshot.source_changes.length) add(details,node('p','fine',ui('No source fields or tasks changed.')));
    snapshot.source_changes.forEach(c=>add(details,node('p','fine',`Group ${c.group_id}: ${c.change}${c.fields?.length ? ' · fields: '+c.fields.join(', ') : ''}${c.task_ids?.length ? ' · task IDs: '+c.task_ids.join(', ') : ''}`)));
    add(changeBox,details);
  }
  const categories = [...new Set(snapshot.groups.map(g => g.category))].sort();
  const chooser=$('category'), current=chooser.value; chooser.replaceChildren(node('option','',ui('All categories'))); chooser.firstChild.value='';
  categories.forEach(c => { const o=node('option','',label(c));o.value=c;add(chooser,o); });chooser.value=current;
  const query=$('search').value.toLocaleLowerCase(language), status=$('availability').value;
  const matching=snapshot.groups.filter(g => (!chooser.value || g.category===chooser.value) && (status==='all'||availability(g)===status) &&
    [g.title,g.description,...g.completion_rewards,...g.available_rewards,...g.tasks.flatMap(t=>[t.title,t.source_text]),
      arabicCatalog[g.title],arabicCatalog[g.description],...g.completion_rewards.map(v=>arabicCatalog[v]),
      ...g.available_rewards.map(v=>arabicCatalog[v]),...g.tasks.flatMap(t=>[arabicCatalog[t.title],arabicCatalog[t.source_text]])]
      .join(' ').toLocaleLowerCase(language).includes(query));
  renderRewardControls(matching);
  const groups=sortGroups(matching.filter(g=>rewardFilter==='all'||(rewardFilter==='player'&&g.prize.has_player)||
    (rewardFilter==='coins'&&g.prize.coins!=null)||(rewardFilter==='pack'&&g.prize.has_pack)));
  $('result-count').textContent=`${number(groups.length)} ${ui('challenges')}`;
  const list=$('browse-list');list.replaceChildren();
  if (!groups.length) add(list,node('div','empty',ui('No objectives match these filters.')));
  groups.forEach(g=>add(list,groupCard(g,selectedMap().get(g.id))));
}
function renderSelected() {
  const list=$('selected-list');list.replaceChildren(); const groups=groupMap();
  if (!snapshot.view.selected_groups.length) add(list,node('div','empty',ui('Add a challenge from Browse.')));
  snapshot.view.selected_groups.forEach(s => {
    const g=groups.get(s.group_id);
    if (g) add(list,groupCard(g,s));
    else { const card=node('article','card'); add(card,node('h3','',s.title ? tr(s.title) : ui('Unknown group ')+s.group_id),node('p','',`${ui('Unavailable: ')}${label(s.availability)}. ${ui('Stored evidence remains private.')}`));flags(card,s.review_flags);const b=node('button','danger',ui('Remove from list'));b.onclick=()=>post('select',{group_id:s.group_id,selected:false});add(card,b);add(list,card); }
  });
}
function renderPlan() {
  const p=snapshot.plan;
  $('plan-summary').replaceChildren();
  [['Conditions',p.match_blocks.length],['Unscheduled',p.unscheduled_tasks.length],['Completed',p.completed_tasks.length]].forEach(([name,count])=>{
    const box=node('div','stat');add(box,node('strong','',number(count)),node('span','',ui(name)));add($('plan-summary'),box);
  });
  const blocks=$('plan-blocks');blocks.replaceChildren();
  if (!p.match_blocks.length) add(blocks,node('div','empty',ui('No finite match blocks can be planned with the current selections, modes, and verified cycles.')));
  const routes=new Map();
  p.match_blocks.forEach(block=>{
    const key=JSON.stringify([block.group_id,block.cycle_start_utc,block.mode_option,block.effective_expires_at]);
    if(!routes.has(key)) routes.set(key,[]);
    routes.get(key).push(block);
  });
  routes.forEach(routeBlocks=>{
    const first=routeBlocks[0], card=node('article','card plan-route');
    add(card,node('h3','',tr(first.group_title)));
    const route=[first.mode_option.event ? tr(first.mode_option.event) : label(first.mode_option.mode),first.mode_option.minimum_difficulty && `${ui('Minimum ')}${ui(first.mode_option.minimum_difficulty)}`].filter(Boolean).join(' · ');
    if(route!==first.group_title) add(card,node('p','',route));
    add(card,node('p','fine',ui('Expires: ')+fmt(first.effective_expires_at)+(first.cycle_start_utc ? ' · '+ui('Cycle: ')+fmt(first.cycle_start_utc) : '')));
    routeBlocks.forEach(block=>{
      const condition=node('div','plan-condition');
      add(condition,node('strong','',language === 'ar' ? `${countUnit(block.qualifying_matches,'matches')} مؤهلة` : `${number(block.qualifying_matches)} ${ui(block.qualifying_matches===1?'qualifying match':'qualifying matches')}`));
      block.tasks.forEach(task=>add(condition,node('p','',tr(task.source_text))));
      add(card,condition);
    });
    add(blocks,card);
  });
  const unscheduled=$('plan-unscheduled');unscheduled.replaceChildren();
  if(!p.unscheduled_tasks.length) add(unscheduled,node('div','empty',ui('No unscheduled tasks.')));
  p.unscheduled_tasks.forEach(t=>{const card=node('article','card');add(card,node('strong','',t.task_id),node('p','',tr(t.source_text)));const reasons=node('div','reason-list');flags(reasons,t.reasons);add(card,reasons);add(unscheduled,card);});
  const other=$('plan-other');other.replaceChildren();
  p.completed_tasks.forEach(t=>{const card=node('article','card');add(card,node('span','badge',ui('Completed')),node('p','',t.task_id+' · '+t.progress_key));add(other,card);});
  p.unavailable_groups.forEach(g=>{const card=node('article','card');add(card,node('h3','',g.title ? tr(g.title) : g.group_id),node('p','',label(g.availability)));flags(card,g.review_flags);add(other,card);});
  if(!other.children.length) add(other,node('div','empty',ui('No completed tasks or unavailable groups.')));
}
function renderSettings() {
  const modes=$('modes');modes.replaceChildren();
  snapshot.mode_catalog.forEach(mode=>{
    const row=node('div','mode-row');add(row,node('strong','',label(mode)));
    for(const [key,title] of [['available_modes','Available'],['excluded_modes','Exclude from plan']]){
      const l=node('label'),box=node('input');box.type='checkbox';box.dataset.mode=mode;box.dataset.key=key;box.checked=snapshot.settings[key].includes(mode);add(l,box,document.createTextNode(ui(title)));add(row,l);
    }
    add(modes,row);
  });
  const cycles=$('cycles');cycles.replaceChildren();
  snapshot.groups.filter(g=>g.repeat.cadence).forEach(g=>{
    const row=node('label','cycle-row');add(row,node('strong','',tr(g.title)),node('small','',`${label(g.repeat.cadence)} · ID ${g.id}`));
    const input=node('input');input.type='text';input.placeholder='YYYY-MM-DDTHH:MM:SSZ';input.value=snapshot.settings.cycles[g.id]||'';input.dataset.groupId=g.id;add(row,input);add(cycles,row);
  });
  const backup=$('backup-controls');backup.replaceChildren();
  if (window.objectiveApi) {
    add(backup,node('h3','',ui('Your data')),node('p','fine',ui('Progress is saved only in this browser. Export a backup before clearing browser data or changing phones.')));
    const row=node('div','backup-actions');
    const download=node('button','',ui('Download backup'));
    download.type='button';download.onclick=()=>{
      const data=window.objectiveApi.exportPrivate() || JSON.stringify({state:JSON.stringify({schema_version:1,selections:{},deadline_corrections:{},progress:{}}),settings:JSON.stringify({schema_version:1,available_modes:[],excluded_modes:[],cycles:{}})});
      const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='futgg-progress-backup.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
    const upload=node('input');upload.type='file';upload.accept='application/json,.json';upload.setAttribute('aria-label',ui('Import backup'));
    upload.onchange=async()=>{
      try { if(!upload.files?.length)return;await window.objectiveApi.importPrivate(await upload.files[0].text());await load();message(ui('Backup imported.')); }
      catch(error){message(error.message);}finally{upload.value='';}
    };
    const uploadLabel=node('label','backup-upload',ui('Import backup'));
    add(uploadLabel,upload);add(row,download,uploadLabel);add(backup,row);
  }
}
function render() {
  $('source-date').textContent=ui('Updated ')+fmt(snapshot.view.source_fetched_at);
  $('selected-count').textContent=String(snapshot.view.selected_groups.length);
  if(snapshot.source_mismatch) message(ui('Raw export and interpreted export are from different refreshes. Run the interpretation command before relying on this plan.'));
  renderBrowse();renderSelected();renderPlan();renderSettings();switchTab(activeTab);
}
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
['search','sort','category','availability'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>snapshot&&renderBrowse()));
$('reload').onclick=()=>{message('');load();};
$('language').onchange=e=>setLanguage(e.target.value);
$('settings-form').onsubmit=e=>{
  e.preventDefault();
  const data={available_modes:[],excluded_modes:[],cycles:{}};
  document.querySelectorAll('#modes input').forEach(input=>{if(input.checked)data[input.dataset.key].push(input.dataset.mode);});
  document.querySelectorAll('#cycles input').forEach(input=>{if(input.value.trim())data.cycles[input.dataset.groupId]=input.value.trim();});
  post('settings',data);
};
setLanguage(language);
load();
