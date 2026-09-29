let snapshot;
let activeTab = 'browse';
let rewardFilter = 'all';
let language = typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'ar' ? 'ar' : 'en';
let arabicCatalog = {};
const arabicUI = {
  'Challenges':'التحديات','Language':'اللغة','Refresh':'تحديث','Browse':'تصفح','My list':'قائمتي','Plan':'الخطة','Settings':'الإعدادات',
  'Search challenges or tasks':'ابحث عن التحديات أو المهام','Soonest expiry':'الأقرب انتهاءً','Highest player rating':'أعلى تقييم لاعب','Most coins':'أكثر عملات','Best pack quality':'أفضل حزمة',
  'All categories':'كل الفئات','Active':'نشط','All availability':'كل الحالات','Upcoming':'قادم','Expired':'منتهٍ',
  'Match plan':'خطة المباريات','Counts are per condition. One match may count toward several.':'الأعداد لكل شرط. قد تُحتسب مباراة واحدة لأكثر من شرط.',
  'Shared match runs':'مباريات مشتركة','Condition details':'تفاصيل الشروط','Shared qualifying matches':'مباريات مؤهلة مشتركة',
  'Conditional minimum for separate-match tasks. Goals, assists, wins, and squad rules must hold; cumulative targets can progress here but may need more matches.':'الحد الأدنى المشروط لمهام المباريات المنفصلة. يجب تحقيق شروط الأهداف والتمريرات والفوز والتشكيلة؛ ويمكن التقدم في الأهداف التراكمية هنا لكنها قد تحتاج إلى مباريات إضافية.',
  'Shared across ':'مشتركة بين ',' challenges':' تحديات','Suggested starting squad: ':'التشكيلة الأساسية المقترحة: ',
  'One starter can satisfy more than one listed trait when eligible.':'يمكن للاعب أساسي واحد استيفاء أكثر من سمة مذكورة إذا كان مؤهلاً لها.',
  'Check that you own an eligible card for any overlapping traits.':'تحقق من امتلاكك بطاقة مؤهلة للسمات المتداخلة.',
  'Compatible routes for this run: ':'المسارات المتوافقة لهذه المباريات: ',
  'For Squad Battles wins at this difficulty, play the weakest available team for a better chance of winning.':'لفوز سكواد باتلز بهذه الصعوبة، العب ضد أضعف فريق متاح لفرصة أفضل للفوز.',
  'Required scorers and assisters must start; they can be substituted after contributing.':'يجب أن يبدأ اللاعبون المطلوب منهم التسجيل أو الصناعة؛ ويمكن استبدالهم بعد مساهمتهم.',
  'Cumulative targets that can progress during this run':'الأهداف التراكمية التي يمكن التقدم فيها خلال هذه المباريات',
  'Required scorer: ':'اللاعب الذي يسجل: ','Required assister: ':'اللاعب الذي يصنع الأهداف: ',' (must start)':' (يجب أن يبدأ المباراة)',
  'No shared match runs can be planned.':'لا يمكن تخطيط مباريات مشتركة.','Search limited; this is the best plan found, not a proven minimum.':'البحث محدود؛ هذه أفضل خطة عُثر عليها، وقد لا تكون الحد الأدنى.',
  'English source':'النص الإنجليزي الأصلي',
  'Needs attention':'يحتاج إلى مراجعة','Completed & unavailable':'المكتمل وغير المتاح','Modes & cycles':'الأنماط والفترات','Current cycle starts':'بداية الفترات الحالية',
  'Enter a verified UTC start for each daily or weekly challenge before saving progress.':'أدخل وقت بدء مؤكداً بالتوقيت العالمي UTC لكل تحدٍ يومي أو أسبوعي قبل حفظ التقدم.',
  'Save settings':'حفظ الإعدادات','Unknown':'غير معروف','Review':'مراجعة','Coins':'عملات','Prize':'جائزة','Rating unknown':'التقييم غير معروف',
  'Your data':'بياناتك','Progress is saved only in this browser. Export a backup before clearing browser data or changing phones.':'يُحفظ تقدمك في هذا المتصفح فقط. نزّل نسخة احتياطية قبل مسح بيانات المتصفح أو تغيير الهاتف.',
  'Download backup':'تنزيل نسخة احتياطية','Import backup':'استيراد نسخة احتياطية','Backup imported.':'استُوردت النسخة الاحتياطية.',
  'Sections':'الأقسام','Search challenges':'ابحث عن التحديات','Sort challenges':'رتّب التحديات','Category':'الفئة','Availability':'الحالة','Reward type':'نوع المكافأة',
  'FC 27 in-game expiry in UTC':'تاريخ الانتهاء داخل FC 27 بالتوقيت العالمي UTC',
  'mode unspecified':'النمط غير محدد','cumulative vs single match unclear':'غير واضح إن كان العدد تراكميًا أو في مباراة واحدة',
  'qualification dependency inferred':'علاقة التأهل مستنتجة وتحتاج مراجعة','prerequisite incomplete':'المتطلب السابق غير مكتمل','source group changed':'تغيرت المجموعة في المصدر',
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
  'All selected tasks are completed. Browse for another challenge or check upcoming cycles.':'اكتملت كل المهام المختارة. تصفح تحدياً آخر أو راجع الفترات القادمة.','All selected tasks completed':'اكتملت كل المهام المختارة','You have finished every task currently on your list. Browse for another challenge or review upcoming cycles.':'أنهيت كل المهام الموجودة في قائمتك. تصفح تحدياً آخر أو راجع الفترات القادمة.','Browse challenges':'تصفح التحديات','No selected tasks remain.':'لا توجد مهام مختارة متبقية.',
  'No match runs are needed for the remaining manual targets. Record them from the plan.':'لا تحتاج الأهداف اليدوية المتبقية إلى مباريات محددة. سجّلها من الخطة.','Open plan':'افتح الخطة','No match runs are needed for the remaining manual tasks.':'لا تحتاج المهام اليدوية المتبقية إلى مباريات محددة.','Add a verified cycle start to include these repeat tasks in your plan.':'أضف بداية فترة مؤكدة لإدراج هذه المهام المتكررة في خطتك.','Some selected tasks need review before they can be planned.':'بعض المهام المختارة تحتاج إلى مراجعة قبل تخطيطها.','Your remaining work is cumulative. Record progress as you play.':'عملك المتبقي تراكمي. سجّل التقدم أثناء اللعب.','No match runs are needed for your remaining tasks.':'لا تحتاج مهامك المتبقية إلى مباريات محددة.',
  'Listing ends':'ينتهي العرض','cycle':'دورة','Counts are evidence you entered; confirm completion after checking the objective in game.':'الأعداد التي أدخلتها دليل على التقدم؛ أكّد الإكمال بعد التحقق من الهدف داخل اللعبة.','Confirm completion':'أكّد الإكمال','Save progress':'حفظ التقدم','Review this task':'راجع هذه المهمة',
  'Choose a local time to convert it to UTC.':'اختر الوقت المحلي لتحويله إلى UTC.','UTC value':'القيمة بالتوقيت العالمي UTC','Local time':'الوقت المحلي','Local time picker':'اختيار الوقت المحلي','Verified start in UTC':'بداية مؤكدة بالتوقيت العالمي UTC','verified cycle start in UTC':'بداية الفترة المؤكدة بالتوقيت العالمي UTC','Enter a valid date and time with Z or +00:00, or use the local time picker.':'أدخل تاريخاً ووقتاً صالحين مع Z أو ‎+00:00، أو استخدم اختيار الوقت المحلي.','Use the start shown or confirmed in FC 27; do not estimate it from the listing expiry.':'استخدم وقت البداية الظاهر أو المؤكد في FC 27؛ لا تقدّره من موعد انتهاء العرض.',
  'Record a match':'سجّل مباراة','Enter the match stats once, then mark every task this match advanced.':'أدخل إحصاءات المباراة مرة واحدة، ثم حدّد كل مهمة تقدمت فيها.','Cancel':'إلغاء','Save match progress':'احفظ تقدم المباراة','Goals scored':'الأهداف المسجلة','Assists made':'التمريرات الحاسمة','Match stats':'إحصاءات المباراة','Which tasks did this match advance?':'ما المهام التي تقدمت فيها هذه المباراة؟','Cumulative progress':'التقدم التراكمي','Updated from match stats':'يُحدّث من إحصاءات المباراة','Choose at least one task or enter goals or assists that advance a cumulative target.':'اختر مهمة واحدة على الأقل أو أدخل أهدافاً أو تمريرات حاسمة تحقق هدفاً تراكمياً.',
  'Previous cycle progress':'تقدم الفترة السابقة','Recorded':'تم تسجيل التقدم','recorded':'مسجل',
  'Conditions':'الشروط','Unscheduled':'غير مجدول','No finite match blocks can be planned with the current selections, modes, and verified cycles.':'لا يمكن تخطيط مباريات محددة بالاختيارات والأنماط والفترات المؤكدة الحالية.',
  'No unscheduled tasks.':'لا توجد مهام غير مجدولة.','No completed tasks or unavailable groups.':'لا توجد مهام مكتملة أو مجموعات غير متاحة.',
  'Play this next':'العب هذا أولاً','Then play':'ثم العب','Qualifying matches planned':'مباريات مؤهلة مخططة',
  'These are qualifying results, not predicted attempts. One match can count for several tasks. Cumulative targets may need more matches.':'هذه نتائج مؤهلة وليست توقعاً لعدد المحاولات. قد تُحتسب المباراة لأكثر من مهمة، وقد تحتاج الأهداف التراكمية إلى مباريات إضافية.',
  'Choose a compatible route':'اختر مساراً متوافقاً','Starting XI':'التشكيلة الأساسية','Starting squad':'الفريق الأساسي','Required players':'اللاعبون المطلوبون',
  'During this run':'خلال هذه المباريات','Also work toward':'تابع أيضاً','Cumulative targets':'الأهداف التراكمية',
  'Task wording & conditions':'نص المهمة وشروطها','Source wording':'نص المصدر','Parsed conditions':'الشروط المستخلصة',
  'Run context':'تفاصيل هذه المباريات','Review other tasks':'راجع المهام الأخرى','Tasks to review':'مهام تحتاج مراجعة',
  'Completed & unavailable':'المكتمل وغير المتاح','Set available modes':'حدد الأنماط المتاحة',
  'Add challenges to make a plan.':'أضف تحديات لإنشاء خطة.','No playable runs yet. Review modes, cycles, and tasks below.':'لا توجد مباريات قابلة للتخطيط بعد. راجع الأنماط والفترات والمهام أدناه.',
  'Use the start shown or confirmed in FC 27; do not estimate it from the listing expiry.':'استخدم وقت البداية الظاهر أو المؤكد في FC 27؛ لا تقدّره من موعد انتهاء العرض.',
  'Play':'العب','Win':'افز','Score':'سجّل','Assist':'اصنع','per match':'في كل مباراة','total':'إجمالاً',
  'goal':'هدف','assist':'تمريرة حاسمة','Starting player traits may overlap when you own an eligible card.':'يمكن أن يجمع لاعب أساسي بين عدة سمات إذا كنت تملك بطاقة مؤهلة.',
  'A required scorer or assister must start; you may substitute them after they contribute.':'يجب أن يبدأ المسجل أو صانع الأهداف المطلوب؛ ويمكن استبداله بعد مساهمته.',
  'Record progress':'سجّل التقدم',
  'Focus first':'ابدأ بهذا التحدي','Due ':'ينتهي ','Start with this lineup':'ابدأ بهذه التشكيلة',
  'Start these players':'ابدأ بهؤلاء اللاعبين','These traits apply to their listed task counts, not every match.':'تنطبق هذه السمات على عدد مباريات مهامها، وليس بالضرورة على كل مباراة.',
  'Other challenge targets':'أهداف التحديات الأخرى','Manual tasks':'مهام يدوية',
  'Cycle start required':'يلزم تحديد بداية الفترة','Set verified cycle start':'حدّد بداية فترة مؤكدة',
  'Not in plan until cycle start':'خارج الخطة حتى تحديد بداية الفترة',
  'Waiting for a verified cycle start':'ينتظر تحديد بداية فترة مؤكدة','Waiting tasks':'مهام تنتظر الفترة',
  'Only use a cycle start you know from FC 27.':'استخدم فقط بداية فترة تعرفها من FC 27.',
  'starter':'لاعب أساسي','starters':'لاعبون أساسيون','scorer':'مسجّل','assister':'صانع أهداف',
  'in starting XI':'في التشكيلة الأساسية','in starting squad':'في الفريق الأساسي',
  'Cycle start needed':'يلزم تحديد بداية الفترة','No permitted mode':'لا يوجد نمط مسموح','Needs source review':'تحتاج مراجعة المصدر',
  'Condition':'الشرط','Value':'القيمة','Remaining':'المتبقي',
  'type':'النوع','value':'القيمة','minimum per match':'الحد الأدنى لكل مباراة','minimum':'الحد الأدنى',
  'trait':'السمة','slot':'الموضع','must start':'يجب أن يبدأ','starting 11':'التشكيلة الأساسية',
  'group cycle start required':'يلزم تحديد بداية فترة التحدي','progress cycle unknown':'فترة التقدم غير معروفة',
  'no permitted mode':'لا يوجد نمط مسموح','match count not bounded':'عدد المباريات غير محدد',
  'not match task':'ليست مهمة مباريات','completion needs confirmation':'يلزم تأكيد الإكمال',
  'cycle starts in future':'الفترة تبدأ لاحقاً','effective deadline passed':'انتهى الموعد المعتمد',
  'source task missing':'المهمة غير موجودة في المصدر','task needs review':'المهمة تحتاج مراجعة',
  'availability expired':'انتهى التحدي','availability upcoming':'التحدي قادم','availability unlisted':'أزيل التحدي من القائمة',
  'group source group changed':'تغيرت مجموعة المصدر','group source deadline conflict':'تعارض موعد المصدر',
  'Updated ':'آخر تحديث: ','Saved locally.':'حُفظ محلياً.','Minimum ':'الحد الأدنى: ','Expires: ':'ينتهي: ','Cycle: ':'الفترة: ',
  'Effective expiry: ':'الانتهاء المعتمد: ','In-game observation: ':'تاريخ رُصد داخل اللعبة: ',' · recorded ':' · سُجّل ',
  'When progress was first saved: ':'عند حفظ التقدم أول مرة: ','Enter an explicit cycle start in Modes & cycles before saving progress.':'أدخل بداية فترة محددة في الأنماط والفترات قبل حفظ التقدم.',
  'No source fields or tasks changed.':'لم تتغير حقول المصدر أو المهام.','Source changes since previous refresh':'تغييرات المصدر منذ آخر تحديث',
  'Raw export and interpreted export are from different refreshes. Run the interpretation command before relying on this plan.':'التصدير الخام والتصدير المحلل من تحديثين مختلفين. أعد تشغيل التحليل قبل الاعتماد على الخطة.',
  'Cannot load app':'تعذر تحميل التطبيق','Save failed':'تعذر الحفظ','Unknown group ':'مجموعة غير معروفة ','Unavailable: ':'غير متاح: ',
  'Stored evidence remains private.':'تبقى البيانات المحفوظة خاصة.','qualifying match':'مباراة مؤهلة','qualifying matches':'مباريات مؤهلة',
  'day left':'يوم متبقٍ','days left':'أيام متبقية','challenges':'تحديات','Tasks':'المهام','details':'التفاصيل',
  'Next step':'الخطوة التالية','Choose challenges':'اختر التحديات','Set up modes':'حدد الأنماط','Follow your plan':'اتبع خطتك','Track progress':'سجّل تقدمك',
  'Add a challenge to start a personal plan.':'أضف تحدياً لبدء خطة شخصية.','Choose the modes you can play to build your match plan.':'حدد الأنماط التي يمكنك لعبها لإنشاء خطة المباريات.',
  'Your selected tasks need another playable mode.':'تحتاج مهامك المختارة إلى نمط لعب آخر متاح.',
  'Set a verified cycle start for repeat challenges before tracking them.':'حدد بداية فترة مؤكدة للتحديات المتكررة قبل تتبعها.',
  'Your next match run is ready.':'مبارياتك التالية جاهزة.','Review tasks that need attention in your list.':'راجع المهام التي تحتاج اهتماماً في قائمتك.',
  'Open Browse':'افتح التصفح','Open settings':'افتح الإعدادات','Open plan':'افتح الخطة','Open my list':'افتح قائمتي',
  'Select a challenge to see its tasks and plan.':'اختر تحدياً لعرض مهامه وخطته.','Browse challenges':'تصفح التحديات',
  'tasks completed':'مهام مكتملة','of':'من','selected challenges':'تحديات مختارة','Record this task':'سجّل هذه المهمة',
  'selected challenge':'تحدٍ مختار',
  'Manual count':'العدد اليدوي','Set a cycle start before recording progress for this challenge.':'حدد بداية الفترة قبل تسجيل التقدم لهذا التحدي.',
  'Choose modes you can play. Exclude a mode to keep it out of the plan.':'اختر الأنماط التي يمكنك لعبها. استبعد أي نمط لا تريده في الخطة.',
  'Selected tasks list these modes: ':'الأنماط المذكورة في المهام المختارة: ',
  'Unsaved changes':'تغييرات غير محفوظة','Clear filters':'امسح الفلاتر','No challenges found. Try clearing the filters.':'لم يُعثر على تحديات. جرّب مسح الفلاتر.',
  'Selected repeat challenges':'التحديات المتكررة المختارة','Other repeat challenges':'تحديات متكررة أخرى','No selected repeat challenges.':'لا توجد تحديات متكررة مختارة.',
  'active':'نشط','upcoming':'قادم','expired':'منتهٍ','unlisted':'أزيل من القائمة','missing':'مفقود','needs review':'يحتاج مراجعة',
  'daily':'يومي','weekly':'أسبوعي','match':'مباراة','matches':'مباريات','goals':'أهداف','assists':'تمريرات حاسمة',
  'checklist':'قائمة تحقق','dependency':'متطلب سابق','manual':'يدوي','seasonal':'موسمي','campaigns':'حملات','foundations':'تأسيس',
  'live events':'فعاليات مباشرة','milestones':'إنجازات','mastery':'إتقان','fc pro':'إف سي برو',
  'squad battles':'سكواد باتلز','rivals':'رايفلز','champions':'تشامبيونز','rush':'راش','draft':'درافت','co op':'تعاوني',
  'pve live events':'فعاليات ضد الذكاء الاصطناعي','pvp live events':'فعاليات ضد لاعبين','fc pro open ladder':'سلم إف سي برو المفتوح',
  'Spanish player':'لاعب إسباني','Serie A player':'لاعب من الدوري الإيطالي','Premier League':'الدوري الإنجليزي الممتاز',
  'French players':'لاعبون فرنسيون','Japanese':'ياباني','English':'إنجليزي','players from Eredivisie':'لاعبون من الدوري الهولندي',
  'Destined for Glory player':'لاعب من «مقدّر للمجد»','First Owned players':'لاعبون من الملكية الأولى',
  'Preferred Position: LM':'المركز المفضل: وسط أيسر','players from USA':'لاعبون من الولايات المتحدة',
  'player from any Premier League team':'لاعب من الدوري الإنجليزي الممتاز',
  "player from any Women's Super League team":'لاعبة من الدوري الإنجليزي الممتاز للسيدات',
  'outside the box':'من خارج منطقة الجزاء',
  'Semi-Pro':'شبه محترف','Professional':'محترف','World Class':'فئة عالمية','Legendary':'أسطوري','Ultimate':'ألتميت',
};
const openDetails = new Set();
let pendingTaskFocus = null;
const savedPlanRoutes = (() => {
  try { const value=JSON.parse(typeof localStorage !== 'undefined' ? localStorage.getItem('planRoutes') || '{}' : '{}');return value && typeof value==='object' && !Array.isArray(value) ? value : {}; }
  catch (_) { return {}; }
})();
const $ = (id) => document.getElementById(id);
const ui = value => language === 'ar' ? (arabicUI[value] || value) : value;
const tr = value => language === 'ar' ? (arabicCatalog[value] || arabicUI[value] || value) : value;
const number = value => Number(value).toLocaleString(language === 'ar' ? 'ar-SA' : undefined);
const countUnit = (count, unit) => {
  const singular = {matches:'match',goals:'goal',assists:'assist',wins:'win',matches_played:'match'};
  if (language !== 'ar') return `${number(count)} ${count === 1 ? singular[unit] || label(unit) : label(unit)}`;
  if (unit === 'matches') return count === 1 ? 'مباراة واحدة' : count === 2 ? 'مباراتين' : `${number(count)} ${count >= 3 && count <= 10 ? 'مباريات' : 'مباراة'}`;
  if (unit === 'goals') return count === 1 ? 'هدفاً واحداً' : count === 2 ? 'هدفين' : `${number(count)} أهداف`;
  return `${number(count)} ${label(unit)}`;
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
  if ($('settings-form').classList.contains('dirty')) $('settings-dirty').textContent=ui('Unsaved changes');
  if ($('message').textContent === 'Saved locally.' || $('message').textContent === 'حُفظ محلياً.') message(ui('Saved locally.'));
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
    if (pendingTaskFocus) {
      const target=pendingTaskFocus;pendingTaskFocus=null;
      requestAnimationFrame(()=>focusTask(target.groupId,target.taskId));
    }
  } catch (error) { pendingTaskFocus=null;message(error.message); }
}
function switchTab(tab) {
  if (tab !== activeTab && ($('message').textContent === 'Saved locally.' || $('message').textContent === 'حُفظ محلياً.')) message('');
  activeTab = tab;
  document.querySelectorAll('.tabs button').forEach(b => {
    const active=b.dataset.tab === tab;
    b.classList.toggle('active', active);
    b.setAttribute('aria-current', active ? 'page' : 'false');
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === tab));
}
function focusTask(groupId, taskId) {
  const card=[...$('selected-list').querySelectorAll('[data-group-id]')].find(el=>el.dataset.groupId===groupId);
  const task=[...(card?.querySelectorAll('[data-task-id]')||[])].find(el=>el.dataset.taskId===taskId);
  const target=task?.querySelector('input:not([type=checkbox]), button') || task || card;
  target?.scrollIntoView({block:'center',behavior:'smooth'});
  target?.focus({preventScroll:true});
}
function goToTask(groupId, taskId) {
  openDetails.add(groupId);
  renderSelected();switchTab('selected');
  requestAnimationFrame(()=>focusTask(groupId,taskId));
}
function cycleSettings(groupId) {
  switchTab('settings');
  const input=[...document.querySelectorAll('#cycles input')].find(el=>el.dataset.groupId===groupId);
  input?.scrollIntoView({block:'center',behavior:'smooth'});input?.focus({preventScroll:true});
}
function renderNextStep() {
  const target=$('next-step');target.replaceChildren();
  const selected=snapshot.view.selected_groups;
  const hasModes=snapshot.settings.available_modes.some(mode=>!snapshot.settings.excluded_modes.includes(mode));
  const hasRun=Boolean(snapshot.plan.combined_plan?.runs?.length);
  const allComplete=selected.length>0 && selected.every(group=>group.tasks.length>0 && group.tasks.every(task=>task.progress?.completed));
  const needsMode=snapshot.plan.unscheduled_tasks.some(task=>task.reasons.includes('no_permitted_mode'));
  const missingCycle=selected.find(group=>snapshot.groups.find(source=>source.id===group.group_id)?.repeat?.cycle_key_required && !snapshot.settings.cycles[group.group_id]);
  let copy, action, tab;
  if (!selected.length) [copy,action,tab]=['Add a challenge to start a personal plan.','Open Browse','browse'];
  else if (allComplete) [copy,action,tab]=['All selected tasks are completed. Browse for another challenge or check upcoming cycles.','Browse challenges','browse'];
  else if (!hasModes && needsMode) [copy,action,tab]=['Choose the modes you can play to build your match plan.','Open settings','settings'];
  else if (!hasRun && needsMode) [copy,action,tab]=['Your selected tasks need another playable mode.','Open settings','settings'];
  else if (!hasRun && missingCycle) [copy,action,tab]=['Set a verified cycle start for repeat challenges before tracking them.','Open settings','settings'];
  else if (hasRun) [copy,action,tab]=['Your next match run is ready.','Open plan','plan'];
  else if (snapshot.plan.unscheduled_tasks.some(task=>task.reasons.length===1&&task.reasons[0]==='not_match_task')) [copy,action,tab]=['No match runs are needed for the remaining manual targets. Record them from the plan.','Open plan','plan'];
  else [copy,action,tab]=['Review tasks that need attention in your list.','Open my list','selected'];
  const steps=node('div','journey-steps');
  [['Choose challenges','browse'],['Set up modes','settings'],['Follow your plan','plan'],['Track progress','selected']].forEach(([title,id],index)=>{
    const step=node('span','journey-step',`${number(index+1)}. ${ui(title)}`);
    if(id===tab) step.classList.add('current');
    add(steps,step);
  });
  const body=node('div','next-step-body');
  const copyBox=node('div');add(copyBox,node('strong','',ui('Next step')),node('p','',ui(copy)));
  const button=node('button','primary',ui(action));button.type='button';
  button.onclick=()=>tab==='settings'&&missingCycle&&hasModes&&!hasRun&&!needsMode?cycleSettings(missingCycle.group_id):switchTab(tab);
  add(body,copyBox,button);add(target,steps,body);
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
  const remaining=days === 1 ? `${number(days)} ${ui('day left')}` : `${number(days)} ${ui('days left')}`;
  return group.repeat?.cadence ? `${ui('Listing ends')}: ${remaining}` : remaining;
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
  card.dataset.groupId=group.id;
  const heading = node('div','card-heading');
  const status = availability(group);
  add(heading, node('span','category',label(group.category)), node('span','deadline '+(selected?.review_flags?.some(flag=>flag.includes('deadline'))?'review':''),deadlineLabel(group,selected)));
  if(group.repeat?.cadence) add(heading,node('span','badge cycle-cue',`${label(group.repeat.cadence)} ${ui('cycle')}`));
  if (status !== 'active') add(heading,node('span','badge off',label(status)));
  add(card,heading,node('h3','',tr(group.title)));
  if (selected) {
    const completed=selected.tasks.filter(task=>task.progress?.completed).length;
    const progress=node('div','group-progress');
    add(progress,node('span','',`${number(completed)} ${ui('of')} ${number(selected.tasks.length)} ${ui('tasks completed')}`));
    const meter=node('progress');meter.max=Math.max(1,selected.tasks.length);meter.value=completed;
    meter.setAttribute('aria-label',`${tr(group.title)}: ${number(completed)} ${ui('of')} ${number(selected.tasks.length)} ${ui('tasks completed')}`);
    add(progress,meter);add(card,progress);
  }
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
  const expiry = node('input'); expiry.type='text'; expiry.placeholder='YYYY-MM-DDTHH:MM:SSZ'; expiry.required=true; expiry.setAttribute('aria-label',ui('FC 27 in-game expiry in UTC'));
  const save = node('button','',ui('Record in-game expiry')); save.type='submit';
  deadline.onsubmit = event => { event.preventDefault(); post('deadline',{group_id:group.id, expires_at:expiry.value.trim(), source:'fc27_in_game'}); };
  add(deadline,expiry,save); add(detail,node('p','fine',ui('Only enter an expiry observed in FC 27.')),deadline);
  const selectedTasks = new Map((selected?.tasks || []).map(t => [t.id,t]));
  group.tasks.forEach(task => add(detail,taskCard(task, selectedTasks.get(task.id), group)));
  if (selected?.unmatched_progress?.length) {
    add(detail,node('h3','',ui('Stored progress for removed tasks')));
    selected.unmatched_progress.forEach(p => add(detail,node('p','',p.task_id + ': ' + tr(p.source_text) + ' · ' + number(p.count))));
  }
  if(selected?.progress_history?.length){
    const history=node('details','cycle-history');add(history,node('summary','',`${ui('Previous cycle progress')} · ${number(selected.progress_history.length)}`));
    const cycles=new Map();selected.progress_history.forEach(entry=>{if(!cycles.has(entry.cycle_start_utc))cycles.set(entry.cycle_start_utc,[]);cycles.get(entry.cycle_start_utc).push(entry);});
    cycles.forEach((entries,start)=>{
      const section=node('div','cycle-history-period');add(section,node('h4','',`${label(group.repeat.cadence)} · ${fmt(start)}`));
      entries.forEach(entry=>{
        const sourceTask=group.tasks.find(task=>task.id===entry.task_id);
        const quantity=sourceTask?.target?countUnit(entry.count,sourceTask.target.unit):`${number(entry.count)} ${ui('recorded')}`;
        add(section,node('p','fine',`${tr(entry.source_text)} · ${quantity} · ${ui(entry.completed?'Completed':'Recorded')}`));
      });add(history,section);
    });add(detail,history);
  }
  add(card,detail);
  return card;
}
function taskCard(task, stateTask, group) {
  const div = node('div','task');
  div.dataset.taskId=task.id;div.tabIndex=-1;
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
  if (group.repeat.cadence && !stateTask.progress_key) {
    add(div,node('p','fine',ui('Set a cycle start before recording progress for this challenge.')));
    const setup=node('button','',ui('Set verified cycle start'));setup.type='button';setup.onclick=()=>cycleSettings(group.id);
    add(div,setup);return div;
  }
  const form = node('form','task-controls');
  const count = node('input'); count.type='number'; count.min='0'; count.step='1'; count.value=stateTask.progress?.count ?? 0; count.required=true; count.setAttribute('aria-label',(language === 'ar' ? 'العدد اليدوي لـ ' : 'Manual count for ') + tr(task.title));
  const countLabel=node('label','count-label',ui('Manual count'));add(countLabel,count);
  const checkLabel = node('label'); const completed=node('input'); completed.type='checkbox'; completed.checked=stateTask.progress?.completed || false;
  const reached=Boolean(task.target && stateTask.progress && stateTask.progress.count>=task.target.count && !stateTask.progress.completed);
  const completionHint=node('p','fine completion-hint',ui('Counts are evidence you entered; confirm completion after checking the objective in game.'));
  completionHint.hidden=!reached || Boolean(stateTask.progress?.completed);
  add(checkLabel,completed,document.createTextNode(' ' + ui('Completed')));
  const save = node('button',reached?'primary':'',ui(reached?'Confirm completion':'Save progress')); save.type='submit';
  count.addEventListener('input',()=>{const targetReached=Boolean(task.target && Number(count.value)>=task.target.count);completionHint.hidden=!targetReached||completed.checked;save.textContent=ui(targetReached&&!completed.checked?'Confirm completion':'Save progress');save.classList.toggle('primary',targetReached&&!completed.checked);});
  completed.addEventListener('change',()=>{completionHint.hidden=!reached||completed.checked;save.textContent=ui(reached&&!completed.checked?'Confirm completion':'Save progress');save.classList.toggle('primary',reached&&!completed.checked);});
  form.onsubmit = e => { e.preventDefault(); pendingTaskFocus={groupId:group.id,taskId:task.id};post('progress',{task_id:task.id,count:Number(count.value),completed:completed.checked}); };
  add(form,countLabel,checkLabel,save); add(div,completionHint,form);
  if (group.repeat.cadence) add(div,node('p','fine',stateTask.progress_key ? ui('Cycle: ') + fmt(snapshot.settings.cycles[group.id]) : ui('Enter an explicit cycle start in Modes & cycles before saving progress.')));
  return div;
}
function renderBrowse() {
  const changeBox=$('source-changes');changeBox.replaceChildren();
  if(snapshot.source_changes?.length) {
    const details=node('details','card');
    add(details,node('summary','',`${ui('Source changes since previous refresh')} (${number(snapshot.source_changes.length)})`));
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
  if (!groups.length) {
    const empty=node('div','empty');add(empty,node('p','',ui('No challenges found. Try clearing the filters.')));
    const clear=node('button','',ui('Clear filters'));clear.type='button';clear.onclick=()=>{
      $('search').value='';$('sort').value='soonest';$('category').value='';$('availability').value='active';rewardFilter='all';renderBrowse();
    };add(empty,clear);add(list,empty);
  }
  groups.forEach(g=>add(list,groupCard(g,selectedMap().get(g.id))));
}
function renderSelected() {
  const list=$('selected-list'),summary=$('selected-summary');list.replaceChildren();summary.replaceChildren();const groups=groupMap();
  if (!snapshot.view.selected_groups.length) {
    const empty=node('div','empty');add(empty,node('p','',ui('Select a challenge to see its tasks and plan.')));
    const browse=node('button','primary',ui('Browse challenges'));browse.type='button';browse.onclick=()=>switchTab('browse');add(empty,browse);add(list,empty);
  } else {
    const selected=snapshot.view.selected_groups;
    const total=selected.reduce((sum,group)=>sum+group.tasks.length,0);
    const done=selected.reduce((sum,group)=>sum+group.tasks.filter(task=>task.progress?.completed).length,0);
    const bar=node('div','selected-overview');
    const copy=node('div');add(copy,node('strong','',`${number(selected.length)} ${ui(selected.length===1?'selected challenge':'selected challenges')}`),node('span','',`${number(done)} ${ui('of')} ${number(total)} ${ui('tasks completed')}`));
    const plan=node('button','',ui('Open plan'));plan.type='button';plan.onclick=()=>switchTab('plan');add(bar,copy,plan);add(summary,bar);
  }
  const ordered=[...snapshot.view.selected_groups].sort((a,b)=>{
    const deadline=group=>group.effective_expires_at ? Date.parse(group.effective_expires_at) : Infinity;
    return deadline(a)-deadline(b) || tr(a.title||'').localeCompare(tr(b.title||''),language);
  });
  ordered.forEach(s => {
    const g=groups.get(s.group_id);
    if (g) add(list,groupCard(g,s));
    else { const card=node('article','card'); add(card,node('h3','',s.title ? tr(s.title) : ui('Unknown group ')+s.group_id),node('p','',`${ui('Unavailable: ')}${label(s.availability)}. ${ui('Stored evidence remains private.')}`));flags(card,s.review_flags);const b=node('button','danger',ui('Remove from list'));b.onclick=()=>post('select',{group_id:s.group_id,selected:false});add(card,b);add(list,card); }
  });
}
function planRouteText(option) {
  const englishModes={squad_battles:'Squad Battles',rivals:'Rivals',champions:'Champions',rush:'Rush',
    live_events:'Live Events',pve_live_events:'PVE Live Events',pvp_live_events:'PVP Live Events',
    draft:'Draft',co_op:'Co-op',fc_pro_open_ladder:'FC Pro Open Ladder'};
  const mode=language==='ar' ? label(option.mode) : (englishModes[option.mode] || label(option.mode));
  return [mode,option.event ? tr(option.event) : null,
    option.minimum_difficulty && `${ui('Minimum ')}${ui(option.minimum_difficulty)}`].filter(Boolean).join(' · ');
}
function planTraitShort(trait) {
  const english={'Serie A player':'Serie A','players from Eredivisie':'Eredivisie','players from USA':'USA',
    'Preferred Position: LM':'LM','player from any Premier League team':'Premier League',
    "player from any Women's Super League team":'Women’s Super League'};
  const arabic={'Serie A player':'الدوري الإيطالي','players from Eredivisie':'الدوري الهولندي',
    'players from USA':'الولايات المتحدة','Preferred Position: LM':'وسط أيسر',
    'player from any Premier League team':'الدوري الإنجليزي الممتاز',
    "player from any Women's Super League team":'الدوري الإنجليزي للسيدات'};
  return (language==='ar'?arabic:english)[trait] || tr(trait);
}
function planStarterText(requirement) {
  const amount=requirement.minimum;
  const trait=planTraitShort(requirement.trait);
  if(language!=='ar') return `${amount==='all'?ui('All'):number(amount)} ${trait} ${ui(requirement.slot==='starting_squad'?'in starting squad':amount===1?'starter':'starters')}`;
  const place=requirement.slot==='starting_squad' ? 'في الفريق الأساسي' : 'أساسي';
  if(amount==='all') return `كل اللاعبين ${place} من ${trait}`;
  if(amount===1) return `لاعب ${place} من ${trait}`;
  if(amount===2) return `لاعبان ${requirement.slot==='starting_squad'?'في الفريق الأساسي':'أساسيان'} من ${trait}`;
  return `${number(amount)} لاعبين ${requirement.slot==='starting_squad'?'في الفريق الأساسي':'أساسيين'} من ${trait}`;
}
function planRoleText(role, forTask=false) {
  if(language!=='ar') return `${planTraitShort(role.trait)} ${ui(role.role==='assisting_player'?'assister':'scorer')}`;
  const player=role.trait==='Japanese' ? 'لاعب ياباني' : role.trait==='Preferred Position: LM' ?
    'لاعب مركزه المفضل وسط أيسر' : tr(role.trait);
  return forTask ? `باستخدام ${player}` : `${player} ${role.role==='assisting_player'?'للصناعة':'للتسجيل'}`;
}
function planCoreRequirements(run) {
  const squad=new Map(), roles=new Map();
  run.match_tasks.forEach(task=>task.conditions.forEach(condition=>{
    if(condition.type==='squad') {
      const key=JSON.stringify([condition.slot,condition.trait]);
      const previous=squad.get(key);
      if(!previous || condition.minimum==='all' || (previous.minimum!=='all' && condition.minimum>previous.minimum))
        squad.set(key,{slot:condition.slot,trait:condition.trait,minimum:condition.minimum});
    }
    if(condition.type==='scoring_player' || condition.type==='assisting_player') {
      const key=JSON.stringify([condition.type,condition.trait,condition.must_start]);
      roles.set(key,{role:condition.type,trait:condition.trait,must_start:condition.must_start});
    }
  }));
  return {squad:[...squad.values()],roles:[...roles.values()]};
}
function planGroupOrder(run,groups) {
  return [...new Set(run.match_tasks.map(task=>task.group_id))].sort((a,b)=>{
    const expiry=id=>groups.get(id)?.effective_expires_at ? Date.parse(groups.get(id).effective_expires_at) : Infinity;
    return expiry(a)-expiry(b) || String(a).localeCompare(String(b));
  });
}
function planIssues(plan,runs) {
  const attached=new Set(runs.flatMap(run=>run.cumulative_targets.map(task=>task.task_id)));
  const cycle=new Map(),cumulative=[],manual=[],blocked=[];
  plan.unscheduled_tasks.forEach(task=>{
    if(attached.has(task.task_id)) return;
    if(task.reasons.includes('group_cycle_start_required')) {
      if(!cycle.has(task.group_id)) cycle.set(task.group_id,[]);
      cycle.get(task.group_id).push(task);
    } else if(task.reasons.length===1 && task.reasons[0]==='match_count_not_bounded') cumulative.push(task);
    else if(task.reasons.length===1 && task.reasons[0]==='not_match_task') manual.push(task);
    else blocked.push(task);
  });
  return {cycle,cumulative,manual,blocked};
}
function planTaskText(task, cumulative=false) {
  const conditions=task.conditions || [];
  const result=conditions.find(c=>c.type==='result' && c.value==='win');
  const goals=conditions.find(c=>c.type==='goals');
  const assists=conditions.find(c=>c.type==='assists');
  const style=conditions.find(c=>c.type==='goal_style');
  const location=conditions.find(c=>c.type==='goal_location');
  const scorer=conditions.find(c=>c.type==='scoring_player');
  const squads=conditions.filter(c=>c.type==='squad');
  const qualifier=scorer ? planRoleText({role:'scoring_player',trait:scorer.trait},true) : squads.length ?
    squads.map(planStarterText).join(' + ') : null;
  let action;
  if (result) action=ui('Win');
  else if (goals || style || location || (cumulative && task.target?.unit==='goals')) {
    const amount=cumulative ? task.remaining : goals?.minimum_per_match;
    if (language==='ar') action=[ui('Score'),amount!=null ? countUnit(amount,'goals') : ui('goal'),
      style ? `ب${tr(style.value)}` : null,location ? ui('outside the box') : null,
      !cumulative && amount!=null ? ui('per match') : cumulative ? ui('total') : null].filter(Boolean).join(' ');
    else action=[ui('Score'),amount!=null ? number(amount) : null,style ? tr(style.value) : null,
      location ? label(location.value) : null,ui(amount===1?'goal':'goals'),!cumulative && amount!=null ? ui('per match') : cumulative ? ui('total') : null].filter(Boolean).join(' ');
  }
  else if (assists || (cumulative && task.target?.unit==='assists')) {
    const amount=cumulative ? task.remaining : assists?.minimum_per_match;
    if (language==='ar') action=[ui('Assist'),amount!=null ? number(amount) : null,
      amount===1 ? ui('assist') : ui('assists'),!cumulative && amount!=null ? ui('per match') : cumulative ? ui('total') : null].filter(Boolean).join(' ');
    else action=[ui('Assist'),amount!=null ? number(amount) : null,ui(amount===1?'goal':'goals'),
      !cumulative && amount!=null ? ui('per match') : cumulative ? ui('total') : null].filter(Boolean).join(' ');
  }
  else action=cumulative ? tr(task.source_text) : ui('Play');
  return qualifier ? `${action} · ${qualifier}` : action;
}
function planTaskDetail(task, cumulative=false, related=[]) {
  const detail=node('details','plan-task');
  const summary=node('summary');
  add(summary,node('span','plan-task-action',planTaskText(task,cumulative)));
  if (!cumulative) add(summary,node('span','plan-task-count',countUnit(task.remaining_qualifying_matches,'matches')));
  add(detail,summary);
  [task,...related].forEach(item=>{
    const source=node('div','plan-source-item');
    add(source,node('p','fine',ui('Source wording')+': '+tr(item.source_text)));
    if (language==='ar' && tr(item.source_text)!==item.source_text) {
      const original=node('p','fine original-source',`${ui('English source')}: ${item.source_text}`);
      original.lang='en';original.dir='ltr';add(source,original);
    }
    const button=node('button','plan-task-link',ui('Record this task'));button.type='button';
    button.onclick=()=>goToTask(item.group_id,item.task_id);add(source,button);add(detail,source);
  });
  const conditions=task.conditions || [];
  if (conditions.length) {
    const list=node('ul','plan-conditions');
    conditions.forEach(c=>add(list,node('li','',Object.entries(c).map(([key,value])=>`${label(key)}: ${typeof value==='boolean' ? (value ? '✓' : '—') : typeof value==='number' ? number(value) : tr(label(value))}`).join(' · '))));
    add(detail,node('p','fine',ui('Parsed conditions')),list);
  }
  return detail;
}
function planDisclosure(title, count, className) {
  const detail=node('details',className);
  add(detail,node('summary','',count == null ? ui(title) : `${ui(title)} · ${number(count)}`));
  return detail;
}
function openMatchCheckin(run) {
  const dialog=$('checkin-dialog'),content=$('checkin-content'),form=$('checkin-form');
  content.replaceChildren();$('checkin-error').textContent='';
  const groups=selectedMap();
  const stats=node('div','checkin-stats');
  [['goals','Goals scored'],['assists','Assists made']].forEach(([key,title])=>{
    const label=node('label','count-label',ui(title)),input=node('input');input.type='number';input.min='0';input.step='1';input.value='0';input.dataset.stat=key;add(label,input);add(stats,label);
  });
  add(content,node('h3','',ui('Match stats')),stats);
  const taskList=node('div','checkin-task-list');
  add(taskList,node('h3','',ui('Which tasks did this match advance?')));
  run.match_tasks.forEach(task=>{
    const label=node('label','checkin-task'),check=node('input');check.type='checkbox';check.dataset.taskId=task.task_id;
    add(label,check,node('span','',`${tr(groups.get(task.group_id)?.title||task.group_id)} · ${planTaskText(task)} — ${tr(task.source_text)}`));add(taskList,label);
  });
  add(content,taskList);
  const cumulative=run.cumulative_targets.filter(task=>['goals','assists'].includes(task.target?.unit));
  if(cumulative.length){
    const section=node('div','checkin-cumulative');add(section,node('h3','',ui('Cumulative progress')));
    cumulative.forEach(task=>add(section,node('p','fine',`${tr(groups.get(task.group_id)?.title||task.group_id)} · ${tr(task.source_text)} (${ui('Updated from match stats')})`)));
    add(content,section);
  }
  form.onsubmit=event=>{
    event.preventDefault();
    const entries=[...content.querySelectorAll('input[data-task-id]:checked')].map(input=>{
      const taskId=input.dataset.taskId,groupId=taskId.split(':',1)[0],stateTask=groups.get(groupId)?.tasks.find(item=>item.id===taskId);
      return {task_id:taskId,count:(stateTask?.progress?.count||0)+1,completed:Boolean(stateTask?.progress?.completed)};
    });
    const statsValues=Object.fromEntries([...content.querySelectorAll('input[data-stat]')].map(input=>[input.dataset.stat,Number(input.value)]));
    cumulative.forEach(task=>{
      const increment=statsValues[task.target.unit]||0;
      if(increment<=0)return;
      const stateTask=groups.get(task.group_id)?.tasks.find(item=>item.id===task.task_id);
      entries.push({task_id:task.task_id,count:(stateTask?.progress?.count||0)+increment,completed:Boolean(stateTask?.progress?.completed)});
    });
    const unique=[...new Map(entries.map(entry=>[entry.task_id,entry])).values()];
    if(!unique.length){$('checkin-error').textContent=ui('Choose at least one task or enter goals or assists that advance a cumulative target.');return;}
    dialog.close();post('progress_batch',{entries:unique});
  };
  dialog.showModal();
}
function planTaskList(tasks) {
  const list=node('div','plan-checklist');
  const taskGroups=new Map();
  tasks.forEach(task=>{
    const signature=JSON.stringify([planTaskText(task),task.conditions]);
    if(!taskGroups.has(signature)) taskGroups.set(signature,[]);
    taskGroups.get(signature).push(task);
  });
  taskGroups.forEach(group=>{
    group.sort((a,b)=>b.remaining_qualifying_matches-a.remaining_qualifying_matches);
    add(list,planTaskDetail(group[0],false,group.slice(1)));
  });
  return list;
}
function renderPlan() {
  const p=snapshot.plan;
  const combined=p.combined_plan||{runs:[],qualifying_match_count:0,optimization:'exact_for_separate_matches'};
  const runs=$('plan-runs'), extra=$('plan-extra'), summary=$('plan-summary');
  runs.replaceChildren();extra.replaceChildren();summary.replaceChildren();
  if (!snapshot.view.selected_groups.length) {
    const empty=node('div','empty');add(empty,node('p','',ui('Add challenges to make a plan.')));
    const browse=node('button','primary',ui('Browse challenges'));browse.type='button';browse.onclick=()=>switchTab('browse');add(empty,browse);add(summary,empty);
    return;
  }
  const total=node('div','plan-total');
  add(total,node('strong','',number(combined.qualifying_match_count)),node('div','',ui('Qualifying matches planned')));
  add(summary,total,node('p','fine plan-caveat',ui('These are qualifying results, not predicted attempts. One match can count for several tasks. Cumulative targets may need more matches.')));
  if (combined.optimization==='search_limited') add(summary,node('p','fine',ui('Search limited; this is the best plan found, not a proven minimum.')));
  const groups=selectedMap();
  const ordered=[...combined.runs].sort((a,b)=>{
    const expiry=run=>Math.min(...run.group_ids.map(id=>{
      const value=groups.get(id)?.effective_expires_at;
      return value ? Date.parse(value) : Infinity;
    }));
    return expiry(a)-expiry(b) || a.qualifying_matches-b.qualifying_matches || planRouteText(a.mode_option).localeCompare(planRouteText(b.mode_option));
  });
  const issues=planIssues(p,ordered);
  const selected=snapshot.view.selected_groups;
  const allComplete=selected.length>0 && selected.every(group=>group.tasks.length>0 && group.tasks.every(task=>task.progress?.completed));
  if(allComplete) {
    const done=node('div','complete-state');
    add(done,node('strong','',ui('All selected tasks completed')),node('p','',ui('You have finished every task currently on your list. Browse for another challenge or review upcoming cycles.')));
    const browse=node('button','primary',ui('Browse challenges'));browse.type='button';browse.onclick=()=>switchTab('browse');add(done,browse);
    add(summary,done);add(runs,node('p','empty',ui('No selected tasks remain.')));
    return;
  }
  issues.cycle.forEach((tasks,id)=>{
    const openCycleSettings=()=>cycleSettings(id);
    if(ordered.length) {
      const teaser=node('button','plan-cycle-teaser',`${tr(groups.get(id)?.title||id)} · ${ui('Not in plan until cycle start')}`);
      teaser.type='button';teaser.onclick=openCycleSettings;add(summary,teaser);
    }
    const alert=node('div','plan-cycle-alert');
    add(alert,node('strong','',`${tr(groups.get(id)?.title||id)} · ${ui('Cycle start required')}`),
      node('p','fine',`${number(tasks.length)} ${ui('Waiting for a verified cycle start')}. ${ui('Only use a cycle start you know from FC 27.')}`));
    const settings=node('button','',ui('Set verified cycle start'));settings.type='button';settings.onclick=openCycleSettings;
    add(alert,settings);
    const waiting=planDisclosure('Waiting tasks',tasks.length,'plan-subdetails');
    tasks.forEach(task=>add(waiting,node('p','fine',tr(task.source_text))));
    add(alert,waiting);add(ordered.length?extra:summary,alert);
  });
  if (!ordered.length) {
    const emptyCopy=issues.manual.length ? 'No match runs are needed for the remaining manual tasks.' :
      issues.cycle.size ? 'Add a verified cycle start to include these repeat tasks in your plan.' :
      issues.blocked.length ? 'Some selected tasks need review before they can be planned.' :
      issues.cumulative.length ? 'Your remaining work is cumulative. Record progress as you play.' :
      'No match runs are needed for your remaining tasks.';
    add(runs,node('p','empty',ui(emptyCopy)));
    const blockedModes=issues.blocked.filter(task=>task.reasons.includes('no_permitted_mode'));
    if(blockedModes.length) {
      const taskIds=new Set(blockedModes.map(task=>task.task_id));
      const named=[...new Set(snapshot.groups.flatMap(group=>group.tasks.filter(task=>taskIds.has(task.id)).flatMap(task=>task.mode_options.map(option=>option.mode))))];
      if(named.length) add(runs,node('p','fine',ui('Selected tasks list these modes: ')+named.map(label).join(' · ')));
      const settings=node('button','ghost',ui('Set available modes'));settings.type='button';settings.onclick=()=>switchTab('settings');add(runs,settings);
    }
  }
  ordered.forEach((run,index)=>{
    const card=node('article',index===0?'plan-run plan-next':'plan-run');
    const taskGroupIds=planGroupOrder(run,groups);
    const core=planCoreRequirements(run);
    const key=run.match_tasks.map(t=>t.task_id).sort().join('|');
    const options=run.route_options?.length ? run.route_options : [run.mode_option];
    const selected=options.find(option=>JSON.stringify(option)===savedPlanRoutes[key]) || run.mode_option;
    const kicker=node('span','plan-kicker',ui(index===0?'Play this next':'Then play'));
    const heading=node('div','plan-run-heading');
    add(heading,node('strong','plan-run-number',number(run.qualifying_matches)),node('div','plan-run-title',label(run.qualifying_matches===1?'match':'matches')));
    const routeLine=node('div','plan-mode',planRouteText(selected));
    add(card,kicker,heading,routeLine);
    if(taskGroupIds.length>1) {
      const focusId=taskGroupIds[0], focus=groups.get(focusId),group=groupMap().get(focusId);
      const priority=node('div','plan-priority');
      add(priority,node('span','plan-setup-label',ui('Focus first')),
        node('strong','',tr(focus?.title||focusId)));
      if(group) add(priority,node('span','fine',deadlineLabel(group,focus)));
      add(card,priority);
    }
    if(options.length>1) {
      const routeLabel=node('label','plan-route-choice',ui('Choose a compatible route'));
      const chooser=node('select');chooser.setAttribute('aria-label',ui('Choose a compatible route'));
      options.forEach((option,i)=>{const item=node('option','',planRouteText(option));item.value=String(i);add(chooser,item);});
      chooser.value=String(Math.max(0,options.findIndex(option=>JSON.stringify(option)===JSON.stringify(selected))));
      chooser.onchange=()=>{savedPlanRoutes[key]=JSON.stringify(options[Number(chooser.value)]);localStorage.setItem('planRoutes',JSON.stringify(savedPlanRoutes));renderPlan();};
      add(routeLabel,chooser);add(card,routeLabel);
    }
    const setup=node('div','plan-setup');
    if(core.squad.length || core.roles.length) add(setup,node('span','plan-setup-label',ui('Start with this lineup')));
    if(core.squad.length) {
      const slots=new Map();
      core.squad.forEach(req=>{
        if(!slots.has(req.slot)) slots.set(req.slot,[]);
        slots.get(req.slot).push(req);
      });
      slots.forEach((requirements,slot)=>{
        const row=node('div');add(row,node('span','plan-setup-label',ui(slot==='starting_squad'?'Starting squad':'Starting XI')),
          node('strong','',requirements.map(req=>language==='ar'?planStarterText(req):`${req.minimum==='all'?ui('All'):number(req.minimum)} ${planTraitShort(req.trait)}`).join(' · ')));add(setup,row);
      });
    }
    if(core.roles.length) {
      const row=node('div');add(row,node('span','plan-setup-label',ui('Start these players')),
        node('strong','',core.roles.map(role=>planRoleText(role)).join(' · ')));add(setup,row);
    }
    if(setup.children.length) add(card,setup);
    const focusTasks=run.match_tasks.filter(task=>task.group_id===taskGroupIds[0]);
    const targets=node('section','plan-targets');
    add(targets,node('h4','',ui('During this run')),planTaskList(focusTasks));
    add(card,targets);
    if(taskGroupIds.length>1) {
      const others=planDisclosure('Other challenge targets',taskGroupIds.length-1,'plan-subdetails');
      taskGroupIds.slice(1).forEach(id=>{
        add(others,node('h4','plan-other-title',tr(groups.get(id)?.title||id)),
          planTaskList(run.match_tasks.filter(task=>task.group_id===id)));
      });
      add(card,others);
    }
    if(run.cumulative_targets.length) {
      const cumulative=planDisclosure('Also work toward',run.cumulative_targets.length,'plan-subdetails');
      run.cumulative_targets.forEach(task=>add(cumulative,planTaskDetail(task,true)));
      add(card,cumulative);
    }
    const context=planDisclosure('Run context',null,'plan-subdetails');
    run.group_ids.forEach(id=>{
      const group=groups.get(id);
      if(group) add(context,node('p','fine',`${tr(group.title)}${group.effective_expires_at ? ' · '+ui('Expires: ')+fmt(group.effective_expires_at) : ''}${snapshot.groups.find(g=>g.id===id)?.repeat?.cadence ? ' · '+ui('Cycle: ')+fmt(snapshot.settings.cycles[id]) : ''}`));
    });
    if(core.squad.length>1) add(context,node('p','fine',ui('Starting player traits may overlap when you own an eligible card.')));
    if(core.squad.length || core.roles.length) add(context,node('p','fine',ui('These traits apply to their listed task counts, not every match.')));
    if(core.roles.some(role=>role.must_start)) add(context,node('p','fine',ui('A required scorer or assister must start; you may substitute them after they contribute.')));
    if(selected.mode==='squad_battles' && selected.minimum_difficulty && run.match_tasks.some(task=>task.conditions.some(c=>c.type==='result'&&c.value==='win')))
      add(context,node('p','fine',ui('For Squad Battles wins at this difficulty, play the weakest available team for a better chance of winning.')));
    add(card,context);
    const checkin=node('button','plan-checkin',ui('Record a match'));checkin.type='button';checkin.onclick=()=>openMatchCheckin(run);add(card,checkin);
    const progress=node('button','plan-progress',ui('Record progress'));progress.type='button';
    progress.onclick=()=>{
      goToTask(taskGroupIds[0],focusTasks[0]?.task_id);
    };
    add(card,progress);add(runs,card);
  });
  if(issues.cumulative.length) {
    const section=planDisclosure('Cumulative targets',issues.cumulative.length,'plan-extra-section');
    issues.cumulative.forEach(t=>{
      const row=node('div','plan-extra-row');add(row,node('strong','',tr(t.source_text)));
      if(t.target) add(row,node('p','fine',`${ui('Remaining')}: ${countUnit(Math.max(0,t.target.count-(groups.get(t.group_id)?.tasks.find(x=>x.id===t.task_id)?.progress?.count||0)),t.target.unit)}`));
      const record=node('button','plan-task-link',ui('Record this task'));record.type='button';record.onclick=()=>goToTask(t.group_id,t.task_id);add(row,record);
      add(section,row);
    });add(extra,section);
  }
  if(issues.manual.length) {
    const section=planDisclosure('Manual tasks',issues.manual.length,'plan-extra-section');
    issues.manual.forEach(t=>{
      const row=node('div','plan-extra-row');add(row,node('span','',tr(t.source_text)));
      const record=node('button','plan-task-link',ui('Record this task'));record.type='button';record.onclick=()=>goToTask(t.group_id,t.task_id);add(row,record);add(section,row);
    });
    add(extra,section);
  }
  if(issues.blocked.length) {
    const section=planDisclosure('Tasks to review',issues.blocked.length,'plan-extra-section');
    issues.blocked.forEach(t=>{
      const row=node('div','plan-extra-row');add(row,node('strong','',tr(t.source_text)));
      const reasons=node('div','reason-list');flags(reasons,t.reasons);add(row,reasons);add(section,row);
      const selectedGroup=groups.get(t.group_id);
      const stateTask=selectedGroup?.tasks.find(task=>task.id===t.task_id);
      const sourceTask=groupMap().get(t.group_id)?.tasks.find(task=>task.id===t.task_id);
      const reached=Boolean(t.reasons.includes('completion_needs_confirmation') || stateTask?.progress && sourceTask?.target && stateTask.progress.count>=sourceTask.target.count && !stateTask.progress.completed);
      const action=node('button','plan-task-link',ui(reached?'Confirm completion':'Review this task'));action.type='button';action.onclick=()=>goToTask(t.group_id,t.task_id);add(row,action);
    });add(extra,section);
  }
  if(p.completed_tasks.length || p.unavailable_groups.length) {
    const section=planDisclosure('Completed & unavailable',p.completed_tasks.length+p.unavailable_groups.length,'plan-extra-section');
    p.completed_tasks.forEach(t=>{const row=node('div','plan-extra-row');add(row,node('span','badge',ui('Completed')),node('span','',`${tr(groups.get(t.group_id)?.title||t.group_id)} · ${t.task_id}`));add(section,row);});
    p.unavailable_groups.forEach(g=>{const row=node('div','plan-extra-row');add(row,node('strong','',tr(g.title||g.group_id)),node('p','fine',label(g.availability)));flags(row,g.review_flags);add(section,row);});
    add(extra,section);
  }
}
function renderSettings() {
  $('settings-form').classList.remove('dirty');
  $('settings-dirty').textContent='';
  const modes=$('modes');modes.replaceChildren();
  snapshot.mode_catalog.forEach(mode=>{
    const row=node('div','mode-row');add(row,node('strong','',label(mode)));
    for(const [key,title] of [['available_modes','Available'],['excluded_modes','Exclude from plan']]){
      const l=node('label'),box=node('input');box.type='checkbox';box.dataset.mode=mode;box.dataset.key=key;box.checked=snapshot.settings[key].includes(mode);
      box.setAttribute('aria-label',`${label(mode)}: ${ui(title)}`);add(l,box,document.createTextNode(ui(title)));add(row,l);
    }
    add(modes,row);
  });
  const cycles=$('cycles');cycles.replaceChildren();
  const selectedIds=new Set(snapshot.view.selected_groups.map(group=>group.group_id));
  const repeat=snapshot.groups.filter(g=>g.repeat.cadence);
  const selectedRepeat=repeat.filter(g=>selectedIds.has(g.id));
  const otherRepeat=repeat.filter(g=>!selectedIds.has(g.id));
  const selectedSection=node('div','cycle-section');add(selectedSection,node('h4','',ui('Selected repeat challenges')));
  if (!selectedRepeat.length) add(selectedSection,node('p','fine',ui('No selected repeat challenges.')));
  const otherSection=planDisclosure('Other repeat challenges',otherRepeat.length,'cycle-other');
  const cycleRow=g=>{
    const row=node('label','cycle-row');add(row,node('strong','',tr(g.title)),node('small','',`${label(g.repeat.cadence)} · ID ${g.id}`));
    const input=node('input');input.type='text';input.placeholder='YYYY-MM-DDTHH:MM:SSZ';input.value=snapshot.settings.cycles[g.id]||'';input.dataset.groupId=g.id;input.setAttribute('aria-label',`${tr(g.title)} ${ui('verified cycle start in UTC')}`);
    const local=node('input');local.type='datetime-local';local.className='cycle-local';local.setAttribute('aria-label',`${tr(g.title)} ${ui('Local time picker')}`);
    const preview=node('small','cycle-preview',input.value ? `${ui('Local time')}: ${fmt(input.value)}` : ui('Choose a local time to convert it to UTC.'));
    local.addEventListener('input',()=>{if(!local.value)return;input.value=new Date(local.value).toISOString().replace('.000Z','Z');preview.textContent=`${ui('UTC value')}: ${input.value}`;input.dispatchEvent(new Event('input',{bubbles:true}));});
    if(input.value){const date=new Date(input.value);if(Number.isFinite(date.getTime()))local.value=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;}
    const error=node('small','cycle-error');error.id=`cycle-error-${g.id}`;error.setAttribute('role','alert');input.setAttribute('aria-describedby',error.id);
    input.addEventListener('input',()=>{error.textContent='';input.removeAttribute('aria-invalid');});
    add(row,node('small','',ui('Verified start in UTC')),input,node('small','',ui('Local time picker')),local,preview,error);
    return row;
  };
  selectedRepeat.forEach(g=>add(selectedSection,cycleRow(g)));
  otherRepeat.forEach(g=>add(otherSection,cycleRow(g)));
  add(cycles,selectedSection,otherSection);
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
  renderBrowse();renderSelected();renderPlan();renderSettings();renderNextStep();switchTab(activeTab);
}
if (typeof module !== 'undefined') module.exports={planCoreRequirements,planGroupOrder,planIssues,planTaskText};
if (typeof document !== 'undefined') {
  document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
  ['search','sort','category','availability'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>snapshot&&renderBrowse()));
  $('reload').onclick=()=>{message('');load();};
  $('checkin-cancel').onclick=()=>$('checkin-dialog').close();
  $('language').onchange=e=>setLanguage(e.target.value);
  $('settings-form').onsubmit=e=>{
    e.preventDefault();
    const data={available_modes:[],excluded_modes:[],cycles:{}};
    document.querySelectorAll('#modes input').forEach(input=>{if(input.checked)data[input.dataset.key].push(input.dataset.mode);});
    const cycleInputs=[...document.querySelectorAll('#cycles input[data-group-id]')];
    for(const input of cycleInputs){
      const value=input.value.trim(),error=$(`cycle-error-${input.dataset.groupId}`);error.textContent='';input.removeAttribute('aria-invalid');
      if(!value)continue;
      if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|\+00:00)$/.test(value)||!Number.isFinite(Date.parse(value))){
        error.textContent=ui('Enter a valid date and time with Z or +00:00, or use the local time picker.');input.setAttribute('aria-invalid','true');input.scrollIntoView({block:'center',behavior:'smooth'});input.focus({preventScroll:true});return;
      }
      data.cycles[input.dataset.groupId]=value;
    }
    post('settings',data);
  };
  $('settings-form').addEventListener('change',e=>{
    if(e.target.matches('#modes input') && e.target.checked) {
      const opposite=e.target.dataset.key==='available_modes'?'excluded_modes':'available_modes';
      const other=[...document.querySelectorAll('#modes input')].find(input=>input.dataset.mode===e.target.dataset.mode&&input.dataset.key===opposite);
      if(other) other.checked=false;
    }
    $('settings-form').classList.add('dirty');
    $('settings-dirty').textContent=ui('Unsaved changes');
  });
  $('settings-form').addEventListener('input',()=>{$('settings-form').classList.add('dirty');$('settings-dirty').textContent=ui('Unsaved changes');});
  setLanguage(language);
  load();
}
