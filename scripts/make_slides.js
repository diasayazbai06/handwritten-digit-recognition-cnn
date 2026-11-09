// Қорғауға арналған презентация (нұсқаулық: 8–12 слайд, ұсынылған құрылым бойынша)
// Іске қосу: node scripts/make_slides.js   (pptxgenjs қажет: npm install pptxgenjs)
const path = require("path");
const fs = require("fs");
const pptxgen = require(process.env.PPTXGENJS || "pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "outputs");
const FIG = path.join(OUT, "figures");
const M = JSON.parse(fs.readFileSync(path.join(OUT, "metrics.json"), "utf8"));
const DS = JSON.parse(fs.readFileSync(path.join(OUT, "dataset_report.json"), "utf8"));
const EXPS = M.experiments;
const kz = (x, n = 2) => x.toFixed(n).replace(".", ",");
const pct = (x) => kz(x * 100);
const exp = (id) => EXPS.find((e) => e.id === id);

const THEME = {
  name: "DigitNet",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "12142B", lt1: "FFFFFF", dk2: "3A3F66", lt2: "F3F4FA",
    accent1: "6D5EFC", accent2: "20C4F4", accent3: "16A34A", accent4: "F59E0B",
    accent5: "C9CBE0", accent6: "E11D48", hlink: "6D5EFC", folHlink: "3A3F66",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 × 7.5 дюйм
pres.author = "Аязбай Диас";
pres.title = "Қолжазба цифрларды CNN арқылы тану";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333, H = 7.5;

// ---------------- Макеттер (layouts) ----------------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 2.0,
        fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.25, w: 11.7, h: 1.0,
        fontSize: 18, color: C.accent5, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85,
        fontSize: 32, bold: true, color: C.text1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "Аязбай Д. · Терең оқыту (TO 4304) · ЕҰУ, 2026",
        options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.text2 },
});
pres.defineSlideMaster({
  title: "DARK_CONTENT",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85,
        fontSize: 32, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5 },
});

const img = (n) => path.join(FIG, n);
function card(slide, x, y, w, h, fill, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name,
    shadow: { type: "outer", color: "1C1F50", opacity: 0.12, blur: 8, offset: 2, angle: 90 },
  });
}
function badge(slide, x, y, label, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.55, h: 0.55, fill: { color: C.accent1 },
    line: { color: C.accent1 }, objectName: name + "-circle" });
  slide.addText(label, { x, y, w: 0.55, h: 0.55, align: "center", valign: "middle", fontSize: 16,
    bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: name + "-num" });
}

// ---------------- 1. Тақырып, автор, жетекші ----------------
pres.addSection({ title: "Кіріспе" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Кіріспе" });
s.addText("Конволюциялық нейрондық желілер негізінде қолжазба цифрларды тану жүйесін әзірлеу",
  { placeholder: "title" });
s.addText("Терең оқыту (TO 4304) пәні бойынша курстық жұмыс", { placeholder: "body" });
s.addText([
  { text: "Орындаған: ", options: { bold: true } }, { text: "Аязбай Диас, ЖИТ-31, 3-курс", options: { breakLine: true } },
  { text: "Ғылыми жетекші: ", options: { bold: true } }, { text: "Максутова К.М.", options: { breakLine: true } },
  { text: "Л.Н. Гумилев атындағы ЕҰУ · Жасанды интеллект технологиялары кафедрасы · Астана, 2026" },
], { x: 0.8, y: 5.6, w: 11.7, h: 1.2, fontSize: 14, color: C.background1, margin: 0, isTextBox: true,
  paraSpaceAfter: 4, objectName: "author-block" });
s.addText("7", { x: 11.2, y: 0.6, w: 1.4, h: 1.4, fontSize: 80, bold: true, color: C.accent1, align: "center",
  valign: "middle", margin: 0, isTextBox: true, fontFace: "Cambria", objectName: "logo-digit" });
s.addNotes("Сәлеметсіздер ме. Менің курстық жұмысымның тақырыбы – конволюциялық нейрондық желілер " +
  "негізінде қолжазба цифрларды тану жүйесін әзірлеу. Жетекшім – Максутова К.М.");

// ---------------- 2. Өзектілік, мәселе, мақсат, міндеттер ----------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Кіріспе" });
s.addText("Өзектілік, мәселе және мақсат", { placeholder: "title" });
const left = [
  ["Өзектілігі", "Чектер, бланктер, тест парақтары әлі қолмен толтырылады – оларды автоматты оқу OCR жүйелерінің негізгі бөлігі."],
  ["Мәселе", "Сызықтық әдістер жазу стиліне төзімсіз, ал үлкен модельдер мен ансамбльдер көп ресурс талап етеді."],
  ["Мақсаты", "CPU-да оқытылатын ықшам CNN әзірлеп, оны базалық әдіспен бірдей шартта салыстыру және веб-прототип ұсыну."],
];
left.forEach(([h, t], i) => {
  const y = 1.5 + i * 1.75;
  card(s, 0.6, y, 6.0, 1.5, C.background2, "card-" + i);
  s.addText(h, { x: 0.85, y: y + 0.15, w: 5.5, h: 0.4, fontSize: 18, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "card-h-" + i });
  s.addText(t, { x: 0.85, y: y + 0.55, w: 5.5, h: 0.85, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "card-t-" + i });
});
s.addText("Міндеттер", { x: 7.1, y: 1.5, w: 5.6, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "tasks-h" });
const tasks = ["Әдебиеттерге шолу, тәсілді негіздеу", "MNIST: сапасы, лицензиясы, бөлу",
  "Baseline + MLP + CNN іске асыру", "5 экспериментті бірдей шартта салыстыру",
  "Метрикалар және қателерді талдау", "Веб-қосымша және REST API"];
tasks.forEach((t, i) => {
  const y = 2.1 + i * 0.78;
  badge(s, 7.1, y, String(i + 1), "task-" + i);
  s.addText(t, { x: 7.85, y, w: 4.9, h: 0.55, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "task-t-" + i });
});
s.addNotes("Қолжазба цифрларды тану – құжаттарды цифрландырудың маңызды бөлігі. Мақсатым – кәдімгі " +
  "ноутбукта оқытылатын, бірақ жоғары дәлдікті модельді жасап, оны базалық әдістермен әділ салыстыру.");

// ---------------- 3. Деректер ----------------
pres.addSection({ title: "Деректер және әдіс" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Деректер және әдіс" });
s.addText("Деректер: MNIST жиыны және оны дайындау", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Train", labels: [..."0123456789"], values: DS.train_counts },
  { name: "Validation", labels: [..."0123456789"], values: DS.val_counts },
  { name: "Test", labels: [..."0123456789"], values: DS.test_counts },
], { x: 0.5, y: 1.4, w: 7.4, h: 5.3, barDir: "col", barGrouping: "clustered",
  chartColors: ["6D5EFC", "20C4F4", "F59E0B"], showLegend: true, legendPos: "b",
  legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: "3A3F66",
  showTitle: true, title: "Сыныптар таралуы (суреттер саны)", titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: "12142B",
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelColor: "3A3F66", valAxisLabelColor: "3A3F66",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  showCatAxisTitle: true, catAxisTitle: "Цифр", catAxisTitleFontSize: 11, catAxisTitleColor: "3A3F66",
  valGridLine: { color: "E3E5F0", size: 0.75 }, catGridLine: { style: "none" }, objectName: "class-chart" });
const facts = [
  ["70 000", "сурет, 28×28, сұр түсті"],
  [`${DS.n_train / 1000}k / ${DS.n_val / 1000}k / ${DS.n_test / 1000}k`, "train / validation / test"],
  ["CC BY-SA 3.0", "ашық лицензия"],
  [String(DS.missing_values) + " · " + String(DS.train_test_overlap), "жетіспейтін мән · train/test қиылысуы"],
];
facts.forEach(([b, t], i) => {
  const y = 1.45 + i * 1.32;
  card(s, 8.3, y, 4.4, 1.12, C.background2, "fact-" + i);
  s.addText(b, { x: 8.5, y: y + 0.08, w: 4.0, h: 0.55, fontSize: 24, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "fact-b-" + i });
  s.addText(t, { x: 8.5, y: y + 0.62, w: 4.0, h: 0.4, fontSize: 13, color: C.text2, margin: 0, isTextBox: true, objectName: "fact-t-" + i });
});
s.addNotes("MNIST – 70 мың қолжазба цифр, ашық CC BY-SA 3.0 лицензиясымен. Сыныптар теңгерімді, " +
  "жетіспейтін мәндер жоқ. Оқыту жиынынан seed 42 бойынша 54 мың train және 6 мың validation бөлдім, " +
  "тест жиыны тек соңғы бағалауға қолданылды. Нормализация, ал train үшін бұру мен жылжыту аугментациясы.");

// ---------------- 4. Базалық әдіс және архитектура ----------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Деректер және әдіс" });
s.addText("Базалық әдіс және таңдалған архитектура", { placeholder: "title" });
s.addImage({ path: img("architecture.png"), x: 0.6, y: 1.35, w: 12.1, h: 12.1 * 0.218, objectName: "arch-img" });
const models = [
  ["Baseline", "Логистикалық регрессия", "Пиксельдер бойынша сызықтық жіктеуіш (scikit-learn)"],
  ["Салыстыру", "MLP 784–256–128–10", "Толық байланысқан желі, кеңістікті ескермейді"],
  ["Негізгі модель", "DigitCNN · 468 010 параметр", "2 конволюциялық блок, BatchNorm, Dropout, Adam"],
];
models.forEach(([tag, h, t], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 4.35, 3.85, 2.3, i === 2 ? C.accent1 : C.background2, "model-" + i);
  const fg = i === 2 ? C.background1 : C.text1;
  s.addText(tag.toUpperCase(), { x: x + 0.25, y: 4.5, w: 3.4, h: 0.35, fontSize: 12, bold: true, color: i === 2 ? C.background1 : C.accent1, margin: 0, isTextBox: true, objectName: "model-tag-" + i });
  s.addText(h, { x: x + 0.25, y: 4.9, w: 3.4, h: 0.75, fontSize: 18, bold: true, color: fg, margin: 0, valign: "top", isTextBox: true, objectName: "model-h-" + i });
  s.addText(t, { x: x + 0.25, y: 5.65, w: 3.4, h: 0.85, fontSize: 14, color: fg, margin: 0, valign: "top", isTextBox: true, objectName: "model-t-" + i });
});
s.addNotes("Базалық әдіс ретінде логистикалық регрессияны алдым. Негізгі модель – DigitCNN: екі " +
  "конволюциялық блок, пакеттік нормализация, Dropout, барлығы 468 мың параметр. Модель нөлден оқытылды.");

// ---------------- 5. Эксперимент сызбасы ----------------
pres.addSection({ title: "Эксперимент және нәтижелер" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Эксперимент және нәтижелер" });
s.addText("Эксперимент сызбасы және гиперпараметрлер", { placeholder: "title" });
const hdr = { bold: true, color: "FFFFFF", fill: { color: "12142B" }, fontSize: 13, valign: "middle" };
const rows = [[
  { text: "ID", options: hdr }, { text: "Модель", options: hdr }, { text: "Өзгертілетін фактор", options: hdr },
  { text: "Гиперпараметрлер", options: hdr }]];
EXPS.forEach((e) => rows.push([e.id, e.model, e.note, e.hyperparams].map((t) => ({ text: String(t),
  options: { fontSize: 13, color: "12142B", fill: { color: e.id === M.best_experiment ? "ECEBFF" : "FFFFFF" } } }))));
s.addTable(rows, { x: 0.6, y: 1.45, w: 8.3, colW: [0.7, 2.6, 2.3, 2.7], border: { type: "solid", pt: 0.75, color: "E3E5F0" },
  rowH: 0.5, margin: 0.06, objectName: "exp-table" });
const cond = [["Seed", "42"], ["Бөлу", "54k / 6k / 10k"], ["Дәуірлер", "8"], ["Пакет", "128"],
  ["Оңтайландырғыш", "Adam + StepLR"], ["Таңдау", "тек validation"], ["Құрылғы", "CPU (GPU-сыз)"]];
card(s, 9.3, 1.45, 3.4, 5.2, C.background2, "cond-card");
s.addText("Бірдей шарттар", { x: 9.5, y: 1.6, w: 3.0, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "cond-h" });
cond.forEach(([k, v], i) => {
  s.addText(k, { x: 9.5, y: 2.2 + i * 0.6, w: 3.0, h: 0.27, fontSize: 12, color: C.text2, margin: 0, isTextBox: true, objectName: "cond-k-" + i });
  s.addText(v, { x: 9.5, y: 2.45 + i * 0.6, w: 3.0, h: 0.3, fontSize: 15, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "cond-v-" + i });
});
s.addNotes("Бес эксперимент бірдей шартта өтті: бірдей бөлу, seed 42, сегіз дәуір. Әр конфигурация " +
  "JSON файлда сақталған, нәтижелері тіркеу кестесіне автоматты жазылады. Модель тек validation бойынша таңдалды.");

// ---------------- 6. Негізгі сандық нәтижелер ----------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Эксперимент және нәтижелер" });
s.addText("Негізгі сандық нәтижелер", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Validation", labels: EXPS.map((e) => e.id), values: EXPS.map((e) => +(e.val_acc * 100).toFixed(2)) },
  { name: "Test", labels: EXPS.map((e) => e.id), values: EXPS.map((e) => +(e.test_acc * 100).toFixed(2)) },
], { x: 0.5, y: 1.35, w: 7.6, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: ["6D5EFC", "20C4F4"],
  valAxisMinVal: 90, valAxisMaxVal: 100, valAxisMajorUnit: 2, showValue: true, dataLabelPosition: "outEnd",
  dataLabelFontSize: 9, dataLabelFontFace: "+mn-lt", dataLabelColor: "3A3F66", dataLabelFormatCode: "0.00",
  showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: "3A3F66",
  showTitle: true, title: "Accuracy, % (validation / test)", titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: "12142B",
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelColor: "3A3F66", valAxisLabelColor: "3A3F66",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  valGridLine: { color: "E3E5F0", size: 0.75 }, catGridLine: { style: "none" }, objectName: "exp-chart" });
const stats = [
  [pct(M.test_acc) + "%", `тест дәлдігі (${M.best_experiment})`],
  [kz(M.roc_auc_macro, 5), "ROC-AUC (macro, one-vs-rest)"],
  [String(M.test_errors), "қате / 10 000 сурет"],
  ["+" + kz((M.test_acc - exp("E01").test_acc) * 100) + " п.т.", "baseline-нан артық"],
];
stats.forEach(([b, t], i) => {
  const y = 1.45 + i * 1.32;
  card(s, 8.5, y, 4.2, 1.12, i === 0 ? C.accent1 : C.background2, "stat-" + i);
  s.addText(b, { x: 8.7, y: y + 0.05, w: 3.8, h: 0.62, fontSize: 30, bold: true, color: i === 0 ? C.background1 : C.accent1, margin: 0, isTextBox: true, objectName: "stat-b-" + i });
  s.addText(t, { x: 8.7, y: y + 0.66, w: 3.8, h: 0.38, fontSize: 13, color: i === 0 ? C.background1 : C.text2, margin: 0, isTextBox: true, objectName: "stat-t-" + i });
});
s.addNotes(`Baseline ${pct(exp("E01").test_acc)}%, MLP ${pct(exp("E02").test_acc)}%, ал CNN 99%-дан асады. ` +
  `Validation бойынша үздік – ${M.best_experiment}, оның тест дәлдігі ${pct(M.test_acc)}%, macro-F1 ${pct(M.macro_avg["f1-score"])}%.`);

// ---------------- 7. Графиктер, қате мысалдар ----------------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Эксперимент және нәтижелер" });
s.addText("Оқыту қисықтары және қателерді талдау", { placeholder: "title" });
s.addImage({ path: img("training_curves.png"), x: 0.6, y: 1.35, w: 7.2, h: 7.2 * 0.364, objectName: "curves" });
s.addImage({ path: img("misclassified.png"), x: 0.6, y: 4.1, w: 5.9, h: 5.9 * 0.49, objectName: "errors" });
s.addImage({ path: img("confusion_matrix.png"), x: 8.1, y: 1.35, w: 4.6, h: 4.6 * 0.857, objectName: "cm" });
card(s, 8.1, 5.45, 4.6, 1.25, C.background2, "err-card");
s.addText("Қателер негізінен пішіні ұқсас цифрлар арасында (4↔9, 3↔5, 7↔1); көбі адам үшін де екіұшты.",
  { x: 8.3, y: 5.5, w: 4.2, h: 1.15, fontSize: 14, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "err-text" });
s.addNotes("Оқыту қисықтарында қайта оқыту жоқ: validation train-нен төмен емес. Қателер матрицасы " +
  "қателердің ұқсас цифрлар арасында болатынын көрсетеді, мысалдардың көбі адам үшін де қиын.");

// ---------------- 8. Демонстрация ----------------
pres.addSection({ title: "Прототип және қорытынды" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Прототип және қорытынды" });
s.addText("Демонстрация: DigitNet веб-қосымшасы", { placeholder: "title" });
s.addImage({ path: img("site_hero.png"), x: 0.6, y: 1.35, w: 6.0, h: 6.0 * 0.625, objectName: "site-hero" });
s.addImage({ path: img("site_demo.png"), x: 6.9, y: 1.35, w: 5.8, h: 5.8 * 0.487, objectName: "site-demo" });
const feats = ["Цифрды тышқанмен салу – нәтиже нақты уақытта", "Сурет жүктеу, MNIST мысалдары",
  "Flask REST API: /api/predict, /api/sample", "Телефонға бейімделген интерфейс"];
feats.forEach((t, i) => {
  const y = 4.35 + i * 0.6;
  badge(s, 6.9, y, String(i + 1), "feat-" + i);
  s.addText(t, { x: 7.6, y, w: 5.1, h: 0.55, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "feat-t-" + i });
});
s.addText("Іске қосу: python app.py → http://localhost:5000", { x: 0.6, y: 5.25, w: 6.0, h: 0.4, fontSize: 13,
  color: C.text2, margin: 0, isTextBox: true, objectName: "run-cmd" });
s.addNotes("Енді қысқаша демонстрация: сайтта цифрды тышқанмен саламын, модель оны бірден таниды және " +
  "10 класс бойынша ықтималдықтарды көрсетеді. Демонстрация интернетсіз жұмыс істейді; резерв ретінде скриншоттар бар.");

// ---------------- 9. Қорытынды, шектеулер, даму бағыттары ----------------
s = pres.addSlide({ masterName: "DARK_CONTENT", sectionTitle: "Прототип және қорытынды" });
s.addText("Қорытынды, шектеулер және даму бағыттары", { placeholder: "title" });
const cols = [
  ["Қорытынды", [`Табыс критерийі орындалды: тест дәлдігі ${pct(M.test_acc)}% ≥ 99%`,
    `Baseline-нан +${kz((M.test_acc - exp("E01").test_acc) * 100)} п.т.`, "CNN MLP-ден жоғары: кеңістікті ескеру маңызды",
    "Жұмыс істейтін веб-прототип және API"]],
  ["Шектеулер", ["Тек бір цифрды таниды", "Таза, ортаға қойылған кескіндер", "Бір seed, гиперпараметр іздеу шектеулі",
    "MNIST жазу дәстүрі бір аймақтан"]],
  ["Даму бағыттары", ["Көп цифрлы сандарды сегменттеу", "Нақты фотосуреттермен оқыту", "Ансамбль және бірнеше seed",
    "Қазақ әріптерін тану, ONNX/мобильді"]],
];
cols.forEach(([h, items], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 1.5, 3.85, 3.75, "232650", "concl-" + i);
  s.addText(h, { x: x + 0.3, y: 1.7, w: 3.3, h: 0.5, fontSize: 20, bold: true, color: i === 0 ? C.accent2 : C.background1, margin: 0, isTextBox: true, objectName: "concl-h-" + i });
  s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })),
    { x: x + 0.3, y: 2.35, w: 3.3, h: 2.8, fontSize: 15, color: C.background1, margin: 0, valign: "top",
      paraSpaceAfter: 10, isTextBox: true, objectName: "concl-t-" + i });
});
const kpis = [[pct(M.test_acc) + "%", "тест дәлдігі"], ["+" + kz((M.test_acc - exp("E01").test_acc) * 100) + " п.т.", "baseline-нан артық"],
  [kz(M.train_time_sec / 60, 1) + " мин", "CPU-да оқыту уақыты"]];
kpis.forEach(([v, t], i) => {
  const x = 0.6 + i * 4.1;
  s.addText(v, { x, y: 5.55, w: 3.85, h: 0.75, fontSize: 36, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "kpi-v-" + i });
  s.addText(t, { x, y: 6.3, w: 3.85, h: 0.4, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true, objectName: "kpi-t-" + i });
});
s.addNotes("Қорытындылай келе: мақсатқа жеттім, табыс критерийі орындалды. Шектеулерді және даму " +
  "бағыттарын атап өттім. Назарларыңызға рахмет, сұрақтарға жауап беруге дайынмын.");

// ---------------- 10. Рахмет ----------------
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Прототип және қорытынды" });
s.addText("Назарларыңызға рахмет!", { placeholder: "title" });
s.addText("Сұрақтарға жауап беруге дайынмын", { placeholder: "body" });
s.addNotes("Рахмет.");

(async () => {
  const file = path.join(ROOT, "Презентация_Аязбай_Диас.pptx");
  await pres.writeFile({ fileName: file });
  if (process.env.APPLY_THEME) {
    const { applyTheme } = require(process.env.APPLY_THEME);
    await applyTheme(file, THEME);
  }
  console.log("Сақталды:", file);
})();
