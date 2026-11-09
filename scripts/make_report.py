"""Курстық жұмыстың түсіндірме жазбасын (.docx) генерациялау.

Құрылымы мен рәсімделуі «Терең оқыту (TO 4304) пәні бойынша курстық жұмыс.
Әдістемелік нұсқаулық» талаптарына сәйкес:
  – А4; өрістер: сол 3 см, оң 1 см, жоғары/төмен 2 см; Times New Roman 14;
    жоларалық интервал 1,0; абзац шегінісі 1,25 см; ені бойынша туралау;
  – бет нөмірі төменгі ортада; титулдық бет пен тапсырма нөмірленеді, бірақ нөмір басылмайды;
  – «Кесте N – Атауы» кестенің үстінде, «Сурет N – Атауы» суреттің астында;
  – белгілеулер мен қысқартулар мазмұннан кейін, тек ≥3 рет қолданылғандары;
  – барлық сандық нәтижелер outputs/ бумасындағы нақты эксперимент файлдарынан алынады.

Іске қосу:  python scripts/make_report.py
"""
import csv
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
FIG = OUTPUTS / "figures"
OUT = ROOT / "Курстық_жұмыс_Аязбай_Диас.docx"

# ---------------- Жеке деректер ----------------
STUDENT = "Аязбай Диас Нурболулы"
STUDENT_SHORT = "Аязбай Д.Н."
GROUP = "ЖИТ-31"
COURSE = "3"
PROGRAM = "6В06112 – Жасанды интеллект технологиялары"
SUBJECT = "Терең оқыту"
SUBJECT_CODE = "TO 4304"
SUPERVISOR = "Максутова К.М."
YEAR = "2026"
ACCESSED = "01.11.2026"
TOPIC = ("Конволюциялық нейрондық желілер негізінде қолжазба "
         "цифрларды тану жүйесін әзірлеу")

# ---------------- Нәтижелер (тек нақты файлдардан) ----------------
M = json.loads((OUTPUTS / "metrics.json").read_text(encoding="utf-8"))
DS = json.loads((OUTPUTS / "dataset_report.json").read_text(encoding="utf-8"))
with open(OUTPUTS / "experiments.csv", encoding="utf-8") as f:
    EXPS = {r["id"]: r for r in csv.DictReader(f)}
RES = {i: json.loads((OUTPUTS / "experiments" / i / "result.json").read_text(encoding="utf-8"))
       for i in EXPS}
ENV = M["environment"]
BEST = M["best_experiment"]
CFG = M["config"]
ACC = M["test_acc"] * 100
ERR = M["test_errors"]
VAL = M["best_val_acc"] * 100
PARAMS = M["params"]
EPOCHS = M["epochs"]
TTIME = M["train_time_sec"]
MACRO = M["macro_avg"]
AUC = M["roc_auc_macro"]


def kz(x, nd=2):
    """Ондық бөлшекті үтірмен жазу: 99.31 -> 99,31"""
    return f"{x:.{nd}f}".replace(".", ",")


def sp(n):
    return f"{int(n):,}".replace(",", " ")


def va(i):
    return float(EXPS[i]["val_acc"]) * 100


def ta(i):
    return float(EXPS[i]["test_acc"]) * 100


def tsec(i):
    return float(EXPS[i]["time_sec"])


def mins(sec):
    return kz(sec / 60, 1)


# ---------------- Дереккөздер (мәтінде алғаш аталу ретімен нөмірленеді) ----------------
REFS = {
    "lecun98": "LeCun Y., Bottou L., Bengio Y., Haffner P. Gradient-based learning applied to "
               "document recognition // Proceedings of the IEEE. 1998. Vol. 86, No. 11. "
               "P. 2278–2324. DOI: 10.1109/5.726791.",
    "mnist": f"LeCun Y., Cortes C., Burges C. J. C. The MNIST Database of Handwritten Digits. "
             f"Courant Institute (NYU), Google Labs, Microsoft Research, 1998. "
             f"URL: http://yann.lecun.com/exdb/mnist/ (қаралған күні: {ACCESSED}).",
    "baldominos": "Baldominos A., Saez Y., Isasi P. A Survey of Handwritten Character Recognition "
                  "with MNIST and EMNIST // Applied Sciences. 2019. Vol. 9, No. 15. Art. 3169. "
                  "DOI: 10.3390/app9153169.",
    "goodfellow": "Goodfellow I., Bengio Y., Courville A. Deep Learning. Cambridge: MIT Press, 2016. 800 p.",
    "d2l": f"Zhang A., Lipton Z. C., Li M., Smola A. J. Dive into Deep Learning. Cambridge: "
           f"Cambridge University Press, 2023. URL: https://d2l.ai (қаралған күні: {ACCESSED}).",
    "ronkin": "Ронкин М.В., Долганов А.Ю. Компьютерлік көру жүйелеріндегі терең оқыту: оқу құралы. 2025.",
    "rumelhart": "Rumelhart D. E., Hinton G. E., Williams R. J. Learning representations by "
                 "back-propagating errors // Nature. 1986. Vol. 323. P. 533–536. DOI: 10.1038/323533a0.",
    "kingma": "Kingma D. P., Ba J. Adam: A Method for Stochastic Optimization // 3rd International "
              "Conference on Learning Representations (ICLR). 2015. URL: https://arxiv.org/abs/1412.6980.",
    "ioffe": "Ioffe S., Szegedy C. Batch Normalization: Accelerating Deep Network Training by Reducing "
             "Internal Covariate Shift // Proceedings of the 32nd International Conference on Machine "
             "Learning. PMLR, 2015. Vol. 37. P. 448–456.",
    "srivastava": "Srivastava N., Hinton G., Krizhevsky A., Sutskever I., Salakhutdinov R. Dropout: "
                  "A Simple Way to Prevent Neural Networks from Overfitting // Journal of Machine "
                  "Learning Research. 2014. Vol. 15. P. 1929–1958.",
    "verma": "Verma G., Doriya R. (eds.). Deep Learning: Theory, Architectures and Applications in "
             "Speech, Image and Language Processing. Bentham Science Publishers, 2023.",
    "krizhevsky": "Krizhevsky A., Sutskever I., Hinton G. E. ImageNet Classification with Deep "
                  "Convolutional Neural Networks // Advances in Neural Information Processing Systems. "
                  "2012. Vol. 25. P. 1097–1105.",
    "simonyan": "Simonyan K., Zisserman A. Very Deep Convolutional Networks for Large-Scale Image "
                "Recognition // International Conference on Learning Representations (ICLR). 2015. "
                "URL: https://arxiv.org/abs/1409.1556.",
    "szegedy": "Szegedy C., Liu W., Jia Y. et al. Going Deeper with Convolutions // Proceedings of the "
               "IEEE Conference on Computer Vision and Pattern Recognition (CVPR). 2015. P. 1–9. "
               "DOI: 10.1109/CVPR.2015.7298594.",
    "he2016": "He K., Zhang X., Ren S., Sun J. Deep Residual Learning for Image Recognition // "
              "Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR). "
              "2016. P. 770–778. DOI: 10.1109/CVPR.2016.90.",
    "tan2021": "Tan M., Le Q. V. EfficientNetV2: Smaller Models and Faster Training // Proceedings of "
               "the 38th International Conference on Machine Learning. PMLR, 2021. Vol. 139. "
               "P. 10096–10106.",
    "vit": "Dosovitskiy A., Beyer L., Kolesnikov A. et al. An Image is Worth 16x16 Words: Transformers "
           "for Image Recognition at Scale // International Conference on Learning Representations "
           "(ICLR). 2021. URL: https://arxiv.org/abs/2010.11929.",
    "convnext": "Liu Z., Mao H., Wu C.-Y., Feichtenhofer C., Darrell T., Xie S. A ConvNet for the 2020s // "
                "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR). "
                "2022. P. 11976–11986. DOI: 10.1109/CVPR52688.2022.01167.",
    "ciresan": "Ciresan D., Meier U., Schmidhuber J. Multi-column Deep Neural Networks for Image "
               "Classification // Proceedings of the IEEE Conference on Computer Vision and Pattern "
               "Recognition (CVPR). 2012. P. 3642–3649. DOI: 10.1109/CVPR.2012.6248110.",
    "an2020": "An S., Lee M., Park S., Yang H., So J. An Ensemble of Simple Convolutional Neural Network "
              "Models for MNIST Digit Recognition // arXiv preprint arXiv:2008.10400. 2020. "
              "URL: https://arxiv.org/abs/2008.10400.",
    "byerly": "Byerly A., Kalganova T., Dear I. No Routing Needed Between Capsules // Neurocomputing. "
              "2021. Vol. 463. P. 545–553. DOI: 10.1016/j.neucom.2021.08.064.",
    "emnist": "Cohen G., Afshar S., Tapson J., van Schaik A. EMNIST: Extending MNIST to Handwritten "
              "Letters // International Joint Conference on Neural Networks (IJCNN). 2017. "
              "P. 2921–2926. DOI: 10.1109/IJCNN.2017.7966217.",
    "chollet": "Chollet F. Deep Learning with Python. 2nd ed. Shelter Island: Manning, 2021. 504 p.",
    "geron": "Géron A. Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow. 2nd ed. "
             "Sebastopol: O’Reilly Media, 2019. 856 p.",
    "paszke": "Paszke A., Gross S., Massa F. et al. PyTorch: An Imperative Style, High-Performance Deep "
              "Learning Library // Advances in Neural Information Processing Systems. 2019. Vol. 32. "
              "P. 8024–8035.",
    "pytorch_docs": f"PyTorch Documentation [Электрондық ресурс]. URL: https://pytorch.org/docs/stable/ "
                    f"(қаралған күні: {ACCESSED}).",
    "pedregosa": "Pedregosa F., Varoquaux G., Gramfort A. et al. Scikit-learn: Machine Learning in "
                 "Python // Journal of Machine Learning Research. 2011. Vol. 12. P. 2825–2830.",
    "flask": f"Flask Documentation [Электрондық ресурс]. Pallets Projects. "
             f"URL: https://flask.palletsprojects.com/ (қаралған күні: {ACCESSED}).",
    "mdn": f"Canvas API – MDN Web Docs [Электрондық ресурс]. Mozilla. "
           f"URL: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API (қаралған күні: {ACCESSED}).",
}
_ref_order = []


def cite(*keys):
    nums = []
    for k in keys:
        if k not in REFS:
            raise KeyError(k)
        if k not in _ref_order:
            _ref_order.append(k)
        nums.append(_ref_order.index(k) + 1)
    return "[" + ", ".join(str(n) for n in sorted(nums)) + "]"


# Белгілеулер мен қысқартулар: тек мәтінде ≥3 рет кездесетіндері автоматты енгізіледі
ABBR = [
    ("ЖИ", "жасанды интеллект"),
    ("ЖНЖ", "жасанды нейрондық желі"),
    ("CNN", "Convolutional Neural Network – конволюциялық нейрондық желі"),
    ("MLP", "Multilayer Perceptron – көп қабатты перцептрон"),
    ("MNIST", "Modified National Institute of Standards and Technology – қолжазба цифрлар деректер жиыны"),
    ("EMNIST", "Extended MNIST – әріптер мен цифрлардың кеңейтілген жиыны"),
    ("OCR", "Optical Character Recognition – таңбаларды оптикалық тану"),
    ("ReLU", "Rectified Linear Unit – түзетілген сызықтық активация функциясы"),
    ("SGD", "Stochastic Gradient Descent – стохастикалық градиенттік түсу"),
    ("ViT", "Vision Transformer – кескіндерге арналған трансформер"),
    ("ROC-AUC", "Receiver Operating Characteristic – Area Under Curve, ROC-қисығы астындағы аудан"),
    ("API", "Application Programming Interface – қолданбалы бағдарламалау интерфейсі"),
    ("REST", "Representational State Transfer – веб-сервистер архитектуралық стилі"),
    ("JSON", "JavaScript Object Notation – деректер алмасу форматы"),
    ("HTML", "HyperText Markup Language – гипермәтінді белгілеу тілі"),
    ("CSS", "Cascading Style Sheets – каскадтық стильдер кестесі"),
    ("CPU", "Central Processing Unit – орталық процессор"),
    ("GPU", "Graphics Processing Unit – графикалық процессор"),
    ("TP, FP, FN", "True Positive, False Positive, False Negative – дұрыс оң, жалған оң, жалған теріс жауаптар"),
]

doc = Document()

# ---------------- Бет параметрлері ----------------
sec1 = doc.sections[0]
sec1.page_height, sec1.page_width = Cm(29.7), Cm(21.0)
sec1.left_margin, sec1.right_margin = Cm(3.0), Cm(1.0)
sec1.top_margin, sec1.bottom_margin = Cm(2.0), Cm(2.0)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(14)
normal.font.color.rgb = RGBColor(0, 0, 0)
_rpr = normal.element.get_or_add_rPr()
_rpr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
_rpr.rFonts.set(qn("w:cs"), "Times New Roman")
normal.paragraph_format.line_spacing = 1.0
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)


def style_font(st, bold=None):
    st.font.name = "Times New Roman"
    st.font.size = Pt(14)
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.font.italic = False
    if bold is not None:
        st.font.bold = bold
    rf = st.element.get_or_add_rPr().get_or_add_rFonts()
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), "Times New Roman")


for lvl in (1, 2):
    st = doc.styles[f"Heading {lvl}"]
    style_font(st, bold=True)
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(14)
    st.paragraph_format.line_spacing = 1.0
    st.paragraph_format.keep_with_next = True
    for el in st.element.rPr.findall(qn("w:color")):
        el.set(qn("w:val"), "000000")
        for a in ("w:themeColor", "w:themeShade"):
            if el.get(qn(a)) is not None:
                del el.attrib[qn(a)]

for name in ("TOC 1", "TOC 2"):
    try:
        st = doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style_font(st, bold=False)
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.line_spacing = 1.0
    st.paragraph_format.left_indent = Cm(0 if name == "TOC 1" else 0.5)


# ---------------- Көмекші функциялар ----------------
def para(text="", bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True,
         italic=False, size=None, after=0, before=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Cm(1.25) if indent else Cm(0)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    if text:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        if size:
            r.font.size = Pt(size)
    return p


def ptext(text, indent=True):
    """Абзац; **...** – жуан мәтін."""
    p = para(indent=indent)
    for i, part in enumerate(text.split("**")):
        if part:
            p.add_run(part).bold = (i % 2 == 1)
    return p


def bullets(items, numbered=False):
    for i, it in enumerate(items, 1):
        ptext(f"{f'{i})' if numbered else '–'} {it}")


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def h1(text, center=False, new_page=True):
    if new_page:
        page_break()
    p = doc.add_heading(text, level=1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(0) if center else Cm(1.25)
    return p


def h2(text):
    p = doc.add_heading(text, level=2)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_before = Pt(14)
    return p


_formula_no = [0]


def formula(text):
    _formula_no[0] += 1
    p = para(indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=4, before=4)
    ts = p.paragraph_format.tab_stops
    ts.add_tab_stop(Cm(8.5), WD_TAB_ALIGNMENT.CENTER)
    ts.add_tab_stop(Cm(17.0), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t")
    p.add_run(text).italic = True
    p.add_run(f"\t({_formula_no[0]})")
    return _formula_no[0]


fig_no, tab_no = [0], [0]


def nf():
    return fig_no[0] + 1


def nt():
    return tab_no[0] + 1


def figure(name, caption, width=15.5):
    fig_no[0] += 1
    path = FIG / name
    if path.exists():
        p = para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=6)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Cm(width))
    else:
        para(f"[Сурет табылмады: {name}]", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(f"Сурет {fig_no[0]} – {caption}", align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=10)


def set_borders(table, val="single"):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    table._tbl.tblPr.append(borders)


def _is_num(sv):
    return sv.replace(" ", "").replace(",", "").replace("≈", "").replace("×", "") \
        .replace("–", "").replace(".", "").replace("%", "").isdigit() or sv in ("", "–", "—")


def table(caption, header, rows, widths, font=12):
    tab_no[0] += 1
    cp = para(f"Кесте {tab_no[0]} – {caption}", indent=False, before=6, after=2)
    cp.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_borders(t)

    def fill(cell, text, bold=False, center=False):
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.first_line_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(str(text))
        r.bold = bold
        r.font.size = Pt(font)

    for i, h in enumerate(header):
        fill(t.rows[0].cells[i], h, bold=True, center=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            fill(cells[i], v, center=_is_num(str(v)))
    for ri, row in enumerate(t.rows):
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
            if ri < len(t.rows) - 1 and len(t.rows) <= 16:
                for p in row.cells[i].paragraphs:
                    p.paragraph_format.keep_with_next = True
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    # Ұзын кестеде тақырып жолын әр бетте қайталау
    th = OxmlElement("w:tblHeader")
    t.rows[0]._tr.get_or_add_trPr().append(th)
    para(after=6)
    return t


def code_block(code, size=10):
    for line in code.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        r = p.add_run(line if line else " ")
        r.font.name = "Courier New"
        rf = r._r.get_or_add_rPr().rFonts
        rf.set(qn("w:hAnsi"), "Courier New")
        rf.set(qn("w:cs"), "Courier New")
        rf.set(qn("w:eastAsia"), "Courier New")
        r.font.size = Pt(size)


def add_field(run, instr, placeholder="1"):
    for kind, txt in (("begin", None), ("instr", instr), ("separate", None), ("text", placeholder), ("end", None)):
        if kind in ("begin", "separate", "end"):
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        elif kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = f" {txt} "
        else:
            el = OxmlElement("w:t")
            el.text = txt
        run._r.append(el)


def center(text, bold=False, after=0, size=None):
    return para(text, bold=bold, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=after, size=size)


def blank(n):
    for _ in range(n):
        para()


def block_line(label, text, left=8.0):
    p = para(align=WD_ALIGN_PARAGRAPH.LEFT, indent=False)
    p.paragraph_format.left_indent = Cm(left)
    if label:
        p.add_run(label).bold = True
    p.add_run(text)
    return p


# =====================================================================
# ТИТУЛДЫҚ БЕТ (нұсқаулықтың А қосымшасы)
# =====================================================================
blank(1)
center("«Л.Н. Гумилев атындағы Еуразия ұлттық университеті» КеАҚ", bold=True)
blank(1)
center("Жасанды интеллект технологиялары кафедрасы", bold=True)
blank(7)
center(f"{SUBJECT} пәні бойынша курстық жұмыс", bold=True, after=12)
center(f"Тақырыбы: «{TOPIC}»")
blank(8)
block_line("Орындаған: ", STUDENT)
block_line("", f"{PROGRAM} БББ {COURSE}-курс студенті, тобы {GROUP}")
para()
block_line("Ғылыми жетекші: ", SUPERVISOR)
block_line("", "_______________________________")
p = block_line("", "(лауазымы, ғылыми дәрежесі)")
p.runs[0].font.size = Pt(10)
blank(9)
center("Астана", bold=True)
center(YEAR, bold=True)

# =====================================================================
# ТАПСЫРМА (нұсқаулықтың Ә қосымшасы) – бет нөмірі басылмайды
# =====================================================================
page_break()
center("«Л.Н. Гумилев атындағы Еуразия ұлттық университеті» КеАҚ", bold=True)
center("Кафедра: Жасанды интеллект технологиялары")
center(f"Пән: {SUBJECT} ({SUBJECT_CODE})", after=10)
for line in ("БЕКІТЕМІН", "Кафедра меңгерушісі", "__________________________", f"«____» ____________ {YEAR} ж."):
    para(line, align=WD_ALIGN_PARAGRAPH.RIGHT, indent=False)
para()
center("БІЛІМ АЛУШЫНЫҢ КУРСТЫҚ ЖҰМЫСЫНА ТАПСЫРМА", bold=True, after=8)


def task_line(label, text):
    p = para(indent=False, after=3)
    p.add_run(label).bold = True
    p.add_run(" " + text)


task_line("Білім алушы:", STUDENT)
task_line("Тобы:", GROUP)
task_line("Курстық жұмыс тақырыбы:", TOPIC)
task_line("Жұмыстың мақсаты:", "конволюциялық нейрондық желі негізінде қолжазба цифрларды тану "
          "моделін әзірлеу, оны базалық әдіспен және балама конфигурациялармен салыстыру, "
          "нәтижелерді бағалау және веб-прототип түрінде ұсыну.")
task_line("Бастапқы деректер/деректер жиынтығы:", "MNIST (LeCun Y., Cortes C., Burges C.), 70 000 "
          "сұр түсті 28×28 сурет, 10 класс; ашық лицензия CC BY-SA 3.0.")
task_line("Қарастырылатын негізгі мәселелер:", "")
for t_ in ("1. Деректерді зерттеу, алдын ала өңдеу және train/validation/test бөлу.",
           "2. Базалық әдіс пен терең оқыту модельдерін бірдей шартта салыстыратын эксперименттер.",
           "3. Нәтижелерді бағалау, қателерді талдау және бағдарламалық прототип (веб-қосымша) әзірлеу."):
    para(t_, indent=False, after=2)
task_line("Бағалау метрикалары:", "Accuracy, Precision, Recall, F1-score, ROC-AUC, қателер матрицасы.")
task_line("Бағдарламалық құралдар:", "Python, PyTorch, scikit-learn, Flask, HTML/CSS/JavaScript.")
task_line("Есептің көлемі:", "25–30 бет (қосымшаларды есептемегенде).")
task_line("Жетекшіге аралық нәтижелерді ұсыну мерзімі:", "")
for t_ in (f"а) жоспар, әдебиеттер және деректер: «____» ____________ {YEAR} ж.",
           f"ә) модель және алғашқы эксперименттер: «____» ____________ {YEAR} ж.",
           f"б) алдын ала есеп: «____» ____________ {YEAR} ж."):
    para(t_, indent=False, after=2)
task_line("Курстық жұмысты тапсыру мерзімі:", f"«____» ____________ {YEAR} ж.")
para(f"Курстық жұмыс жетекшісі: _____________________ /{SUPERVISOR}/", indent=False, after=3)
para(f"Тапсырманы қабылдаған білім алушы: __________ /{STUDENT_SHORT}/", indent=False)

# =====================================================================
# 2-бөлім: бет нөмірлері басылады (нөмірлеу жалғасады: мазмұн – 3-бет)
# =====================================================================
sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
sec2.footer.is_linked_to_previous = False
fp = sec2.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_field(fp.add_run(), "PAGE")
sec1.footer.is_linked_to_previous = False  # 1-бөлімнің төменгі колонтитулы бос

# ---------------- МАЗМҰНЫ ----------------
center("МАЗМҰНЫ", bold=True, after=14)
_p = doc.add_paragraph()
_r = _p.add_run()
for kind, txt in (("begin", None), ("instr", ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None),
                  ("text", "Мазмұнды жаңарту: тышқанның оң жағы → «Обновить поле»."), ("end", None)):
    if kind in ("begin", "separate", "end"):
        el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
    elif kind == "instr":
        el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = txt
    else:
        el = OxmlElement("w:t"); el.text = txt
    _r._r.append(el)

# ---------------- БЕЛГІЛЕУЛЕР МЕН ҚЫСҚАРТУЛАР ----------------
h1("БЕЛГІЛЕУЛЕР МЕН ҚЫСҚАРТУЛАР", center=True)
para("Осы курстық жұмыста төмендегі белгілеулер мен қысқартулар қолданылған:", indent=False, after=6)
ABBR_ANCHOR = para()

# =====================================================================
# КІРІСПЕ
# =====================================================================
BODY_START = len(doc.paragraphs)
h1("КІРІСПЕ", center=True)
ptext("**Тақырыптың өзектілігі.** Қазіргі уақытта жасанды интеллект (ЖИ) технологиялары "
      "құжат айналымын цифрландырудың негізгі құралына айналды. Банктік чектер, пошта "
      "индекстері, сауалнамалар, емтихан парақтары және мемлекеттік бланктер сияқты "
      "құжаттардың едәуір бөлігі әлі де қолмен толтырылады. Мұндай деректерді қолмен енгізу "
      "көп уақыт алады және адам факторына байланысты қателерге әкеледі. Сондықтан "
      "қолжазба таңбаларды, соның ішінде цифрларды автоматты тану – таңбаларды оптикалық "
      f"тану (Optical Character Recognition, OCR) жүйелерінің маңызды бөлігі {cite('lecun98', 'baldominos')}.")
ptext("Соңғы онжылдықта терең оқыту әдістері, әсіресе конволюциялық нейрондық желілер "
      "(Convolutional Neural Networks, CNN), компьютерлік көру міндеттерінде классикалық "
      f"машиналық оқыту әдістерінен айтарлықтай жоғары нәтиже көрсетті {cite('goodfellow', 'krizhevsky', 'ronkin')}. "
      "Қолжазба цифрларды тану міндеті бір жағынан ашық эталондық деректері бар, "
      "нәтижесі объективті өлшенетін міндет, екінші жағынан нақты жүйелерде қолданылатын "
      "барлық кезеңдерді – деректерді дайындау, модельді жобалау, оқыту, бағалау және "
      "енгізуді – толық қамтиды. Бұл оны терең оқыту әдістерін салыстырмалы зерттеуге "
      "ыңғайлы етеді.")
ptext("**Зерттеу мәселесі.** Қарапайым әдістер (мысалы, пиксельдер бойынша сызықтық "
      "жіктеуіш) жазу стилінің әртүрлілігіне, цифрдың көлбеулігі мен жылжуына төзімсіз, "
      "ал өте терең модельдер мен ансамбльдер көп есептеу ресурсын талап етеді. Сондықтан "
      "кәдімгі дербес компьютерде (графикалық процессорсыз) оқытылатын, жоғары дәлдікті және "
      "пайдаланушы суреттерімен жұмыс істей алатын ықшам модельді таңдау және оның "
      "тиімділігін базалық әдістермен салыстыру қажет.")
ptext("**Зерттеу сұрағы:** ықшам конволюциялық желі мен деректерді аугментациялау "
      "қолжазба цифрларды тану дәлдігін базалық сызықтық модельмен және толық "
      "байланысқан желімен салыстырғанда қаншалықты арттырады?")
ptext("**Жұмыстың мақсаты** – конволюциялық нейрондық желі негізінде қолжазба цифрларды "
      "жоғары дәлдікпен тануға қабілетті модельді әзірлеу, оны базалық әдіспен және балама "
      "конфигурациялармен бірдей шартта салыстыру және нәтижені веб-қосымша түрінде ұсыну.")
ptext("Мақсатқа жету үшін келесі **міндеттер** қойылды:")
TASKS = [
    "тақырып бойынша ғылыми әдебиеттерге және қолданыстағы шешімдерге шолу жасап, "
    "таңдалған тәсілді негіздеу;",
    "MNIST (Modified National Institute of Standards and Technology) деректер жиынын таңдау, "
    "оның шығу көзін, лицензиясын, сапасын және сыныптар "
    "таралуын талдау, алдын ала өңдеу және бөлу;",
    "базалық әдісті (логистикалық регрессия) және кемінде бір терең оқыту архитектурасын "
    "іске асыру;",
    "модельдерді бірдей шартта оқыту, гиперпараметрлерді validation бөлігі бойынша таңдау, "
    "эксперименттерді қайталанатындай тіркеу;",
    "нәтижелерді Accuracy, Precision, Recall, F1 және ROC-қисығы астындағы аудан "
    "метрикаларымен бағалау, "
    "қателерді талдау;",
    "бағдарламалық прототип – веб-қосымша және қолданбалы бағдарламалау интерфейсін әзірлеу;",
    "жұмыстың шектеулерін, этикалық тәуекелдерін және даму бағыттарын көрсету.",
]
bullets(TASKS, numbered=True)
ptext("**Зерттеу объектісі** – қолжазба цифрлардың сандық кескіндері.")
ptext("**Зерттеу пәні** – конволюциялық нейрондық желілер негізінде кескіндерді жіктеу "
      "әдістері және олардың конфигурациясының (аугментация, оқыту жылдамдығы) тану "
      "сапасына әсері.")
ptext("**Зерттеу әдістері:** әдебиеттерді салыстырмалы талдау, деректерді зерттеушілік "
      "талдау, терең оқыту (кері тарату, Adam оңтайландырғышы, аугментация), бірдей "
      "шарттағы салыстырмалы эксперимент, жіктеу сапасын статистикалық бағалау.")
ptext("**Табыс критерийі:** қорытынды модельдің тест жиынындағы дәлдігі (Accuracy) "
      "кемінде 99% болуы және базалық әдістен кемінде 5 пайыздық тармаққа жоғары болуы; "
      "модель кәдімгі процессорда 30 минуттан аз уақытта оқытылуы тиіс.")
ptext(f"**Практикалық маңызы.** Әзірленген жүйе тест жиынында {kz(ACC)}% дәлдікке жетті. "
      "Оны бланктерді, чектерді және тест парақтарын автоматты өңдеу жүйелерінің құрамдас "
      "бөлігі ретінде, сондай-ақ терең оқыту пәнін оқытуда интерактивті көрнекі құрал "
      "ретінде пайдалануға болады.")
ptext("**Автордың жеке үлесі:** деректерді талдау және бөлу, пайдаланушы суретін MNIST "
      "форматына келтіру алгоритмі, модельдер мен эксперименттер жүйесін іске асыру, "
      "нәтижелерді талдау және веб-қосымшаны әзірлеу.")
ptext("**Жұмыстың құрылымы.** Курстық жұмыс белгілеулер мен қысқартулардан, кіріспеден, "
      "үш тараудан, қорытындыдан, пайдаланылған дерек көздерінің тізімінен, генеративті "
      "ЖИ құралдарын пайдалану туралы мәліметтен және үш қосымшадан тұрады. Бірінші тарауда "
      "теориялық негіздер мен әдебиеттерге шолу, екінші тарауда деректер мен зерттеу "
      "әдістемесі, үшінші тарауда бағдарламалық іске асыру, эксперименттер және нәтижелер "
      "берілген.")

# =====================================================================
# 1 ТЕОРИЯЛЫҚ НЕГІЗДЕР ЖӘНЕ ӘДЕБИЕТТЕРГЕ ШОЛУ
# =====================================================================
h1("1 ТЕОРИЯЛЫҚ НЕГІЗДЕР ЖӘНЕ ӘДЕБИЕТТЕРГЕ ШОЛУ")
h2("1.1 Зерттеу міндетінің теориялық негіздері")
ptext("Қолжазба цифрларды тану – кескінді жіктеу міндеті: 28×28 өлшемді кескін x "
      "берілгенде, оның {0, 1, …, 9} кластарының қайсысына жататынын анықтау қажет. "
      "Басылған мәтінмен салыстырғанда қолжазбаны тану әлдеқайда күрделі, өйткені жазу "
      "стилі әртүрлі (мысалы, «7» цифры көлденең сызықпен немесе онсыз жазылады), "
      "таңбалардың көлбеулігі, өлшемі мен қалыңдығы әркелкі, ал 4 пен 9, 3 пен 5, 7 мен 1 "
      f"сияқты цифрлар пішіні жағынан ұқсас {cite('baldominos')}.")
ptext("Жасанды нейрондық желі (ЖНЖ) – биологиялық нейрондардың жұмыс принципіне "
      "негізделген математикалық модель. Оның негізгі элементі – жасанды нейрон. Ол кіріс "
      "сигналдарын x₁, …, xₙ салмақтарға w₁, …, wₙ көбейтіп, ығысу b мәнін қосады және "
      "нәтижені активация функциясы f арқылы өткізеді:")
formula("y = f(w₁x₁ + w₂x₂ + … + wₙxₙ + b) = f(wᵀx + b)")
ptext("Активация функциясы желіге сызықтық емес қасиет береді. Қазіргі терең желілерде "
      "түзетілген сызықтық функция (Rectified Linear Unit, ReLU) кеңінен қолданылады: "
      "ReLU(z) = max(0, z). Ол есептеуге оңай және градиенттің жоғалу мәселесін азайтады "
      f"{cite('krizhevsky')}. Көп класты жіктеудің шығыс қабатында Softmax функциясы "
      "қолданылып, шығыстар ықтималдықтарға айналады:")
formula("softmax(zᵢ) = e^zᵢ / Σⱼ e^zⱼ ,   i = 1, …, K")
ptext("мұндағы zᵢ – i-ші класқа сәйкес шығыс мәні (логит), K – кластар саны (K = 10). "
      "Желіні оқыту – шығын функциясын минимумға жеткізетін салмақтарды табу. Көп класты "
      "жіктеуде кросс-энтропия қолданылады:")
formula("L = – Σᵢ yᵢ · log(ŷᵢ)")
ptext("мұндағы yᵢ – нақты классты білдіретін бір-ыстық (one-hot) вектордың компоненті, "
      "ŷᵢ – модельдің i-ші класқа берген ықтималдығы. Салмақтар градиенттік түсу әдісімен "
      "жаңартылады:")
formula("w ← w – η · ∂L/∂w")
ptext("мұндағы η – оқыту жылдамдығы (learning rate), ∂L/∂w – шығын функциясының салмақ "
      f"бойынша градиенті. Градиенттер кері тарату алгоритмімен есептеледі {cite('rumelhart')}. "
      "Практикада салмақтар деректердің шағын бөліктері (mini-batch) бойынша жаңартылады – "
      "бұл стохастикалық градиенттік түсу (Stochastic Gradient Descent, SGD) деп аталады. "
      "Осы жұмыста SGD-нің бейімделгіш нұсқасы – Adam оңтайландырғышы қолданылды "
      f"{cite('kingma')}: ол әр параметр үшін градиенттің бірінші және екінші моменттерінің "
      "жылжымалы орташасын есептеп, қадам ұзындығын автоматты түрде реттейді.")
ptext("**Конволюциялық қабат.** Толық байланысқан желіні кескінге тікелей қолдану тиімсіз: "
      "ол пикселдердің кеңістіктік орналасуын ескермейді, ал параметрлер саны тез өседі. "
      "CNN бұл мәселені жергілікті байланыстар мен салмақтарды ортақ пайдалану арқылы "
      f"шешеді {cite('lecun98', 'goodfellow')}. Шағын сүзгі (ядро) K кескін I бойымен жылжып, "
      "белгілер картасын S есептейді:")
formula("S(i, j) = Σₘ Σₙ I(i + m, j + n) · K(m, n) + b")
ptext("мұндағы (i, j) – белгілер картасындағы позиция, (m, n) – ядро ішіндегі индекстер. "
      "Шығыс өлшемі мына формуламен анықталады:")
formula("O = (W – F + 2P) / S + 1")
ptext("мұндағы W – кіріс өлшемі, F – ядро өлшемі, P – толтыру (padding), S – қадам "
      "(stride). Мысалы, W = 28, F = 3, P = 1, S = 1 болғанда O = 28.")
ptext("**Субдискретизация (pooling)** белгілер картасын кішірейтіп, модельді шағын "
      "жылжуларға тұрақты етеді: 2×2 максималды пулинг өлшемді екі есе азайтады. "
      f"**Пакеттік нормализация** (Batch Normalization) {cite('ioffe')} қабат шығыстарын "
      "әр mini-batch ішінде нормалап, оқытуды тұрақтандырады. **Dropout** "
      f"{cite('srivastava')} оқыту кезінде нейрондардың кездейсоқ бөлігін өшіріп, қайта "
      "оқытуды (overfitting) азайтады. Сонымен, типтік CNN архитектурасы: [Конволюция → "
      "ReLU → Пулинг] × N → Flatten → Толық байланысқан қабаттар → Softmax.")
ptext("**Бағалау метрикалары.** Жіктеу міндеті үшін нұсқаулыққа сәйкес Accuracy, "
      "Precision, Recall және F1-score метрикалары, сондай-ақ ROC-қисығы астындағы аудан "
      "(Receiver Operating Characteristic – Area Under Curve, ROC-AUC) қолданылады. TP, FP, "
      "FN – k класы үшін дұрыс оң, жалған оң және жалған теріс жауаптар саны болсын. Онда:")
formula("Precision = TP / (TP + FP),   Recall = TP / (TP + FN)")
formula("F1 = 2 · Precision · Recall / (Precision + Recall)")
ptext("Көп класты жағдайда бұл метрикалар әр класс үшін есептеліп, арифметикалық "
      "ортасы (macro-average) алынады. Accuracy – дұрыс жіктелген суреттердің жалпы санға "
      "қатынасы. Қосымша талдау үшін қателер матрицасы (confusion matrix) және қате "
      "жіктелген мысалдар қолданылады.")

h2("1.2 Қолданыстағы модельдер мен архитектураларға шолу")
ptext("Кескіндерді жіктеуге арналған архитектуралардың дамуы ашық деректер жиындарымен "
      f"тығыз байланысты {cite('d2l', 'verma')}. 1998 жылы ұсынылған LeNet-5 "
      f"{cite('lecun98')} – алғашқы табысты CNN; ол АҚШ банктерінде чектерді оқуда іс жүзінде "
      f"қолданылды. AlexNet {cite('krizhevsky')} ReLU, Dropout және графикалық процессорда "
      "(Graphics Processing Unit, GPU) оқытуды қолданып, ImageNet жарысында жеңіске жетті. "
      f"VGG {cite('simonyan')} тек 3×3 ядролардан тұратын біркелкі терең құрылымды ұсынса, "
      f"GoogLeNet {cite('szegedy')} әртүрлі өлшемді сүзгілерді параллель қолданатын Inception "
      f"модулін енгізді. ResNet {cite('he2016')} қалдық (skip) байланыстар арқылы жүздеген "
      "қабаттан тұратын желілерді оқытуға мүмкіндік берді.")
ptext("Соңғы жылдары екі бағыт дамыды. Біріншісі – тиімді CNN: EfficientNetV2 "
      f"{cite('tan2021')} желінің тереңдігі, ені және кіріс өлшемін бірге масштабтап, оқыту "
      f"жылдамдығын арттырды, ал ConvNeXt {cite('convnext')} трансформерлердің дизайн "
      "шешімдерін классикалық CNN-ге көшіріп, олармен бәсекелес нәтиже көрсетті. Екіншісі – "
      f"кескіндерге арналған трансформерлер (Vision Transformer, ViT) {cite('vit')}: ViT "
      "кескінді патчтарға бөліп, self-attention механизмімен өңдейді, бірақ жоғары нәтиже "
      "үшін өте үлкен жиында алдын ала оқытуды қажет етеді. Негізгі архитектуралардың "
      f"сипаттамасы {nt()}-кестеде келтірілген.")
table("Кескіндерді жіктеуге арналған негізгі архитектуралар",
      ["Архитектура", "Жылы", "Қабат саны", "Негізгі идеясы", "MNIST үшін қолайлылығы"],
      [["LeNet-5", "1998", "7", "Конволюция + субдискретизация", "Жоғары: осы міндетке жасалған"],
       ["AlexNet", "2012", "8", "ReLU, Dropout, GPU", "Артық күрделі"],
       ["VGG-16", "2014", "16", "Тек 3×3 ядролар", "Идеясы пайдалы, модель үлкен"],
       ["GoogLeNet", "2014", "22", "Inception модулі", "Артық күрделі"],
       ["ResNet-50", "2015", "50", "Қалдық байланыстар", "Артық күрделі"],
       ["EfficientNetV2", "2021", "әртүрлі", "Масштабтау, жылдам оқыту", "Ресурс көп"],
       ["ViT", "2021", "12–32 блок", "Self-attention, патчтар", "Үлкен алдын ала оқыту қажет"],
       ["ConvNeXt", "2022", "әртүрлі", "Заманауи CNN дизайны", "Артық күрделі"]],
      widths=[2.9, 1.5, 2.0, 5.2, 5.4], font=11)
ptext("Шолу көрсеткендей, 28×28 өлшемді сұр түсті кескіндер үшін жүздеген қабатты "
      "немесе үлкен алдын ала оқытуды қажет ететін модельдер артық: олардың есептеу құны "
      "жоғары, ал MNIST жиынында дәлдік бойынша артықшылығы шамалы. Сондықтан LeNet-5 "
      "идеясына негізделген, бірақ VGG стиліндегі 3×3 ядролармен, пакеттік нормализациямен "
      "және Dropout-пен жетілдірілген ықшам CNN тиімді таңдау болып табылады.")

h2("1.3 Ұқсас зерттеулердің салыстырмалы талдауы және таңдалған тәсілді негіздеу")
ptext("MNIST жиыны 1998 жылдан бері кескінді жіктеу әдістерін салыстыратын эталон "
      f"ретінде қолданылады {cite('mnist', 'baldominos')}. Ұқсас зерттеулердің әдістері, "
      "деректері, метрикалары, нәтижелері мен шектеулері "
      f"{nt()}-кестеде салыстырылған.")
table("Ұқсас зерттеулердің салыстырмалы талдауы",
      ["Жұмыс", "Әдіс", "Деректер", "Метрика / нәтиже", "Шектеулері"],
      [[f"LeCun және т.б., 1998 {cite('lecun98')}", "LeNet-5 (CNN)", "MNIST",
        "Accuracy 99,05%", "Сол кездегі оңтайландыру әдістері, аугментациясыз нұсқа"],
       [f"Ciresan және т.б., 2012 {cite('ciresan')}", "35 CNN ансамблі", "MNIST",
        "Accuracy 99,77%", "35 желіні оқыту қажет, есептеу құны жоғары"],
       [f"Cohen және т.б., 2017 {cite('emnist')}", "Жаңа EMNIST (Extended MNIST) жиыны, базалық жіктеуіштер",
        "EMNIST", "Accuracy (әр бөлік бойынша)", "Әріптер қосылғандықтан міндет күрделірек"],
       [f"Baldominos және т.б., 2019 {cite('baldominos')}", "MNIST/EMNIST әдістеріне шолу",
        "MNIST, EMNIST", "Қате пайызы", "Жаңа модель ұсынылмайды"],
       [f"An және т.б., 2020 {cite('an2020')}", "Қарапайым CNN-дер ансамблі", "MNIST",
        "Accuracy 99,91%", "Бірнеше модельді оқыту және біріктіру"],
       [f"Byerly және т.б., 2021 {cite('byerly')}", "Маршрутизациясыз капсулалық желі",
        "MNIST және т.б.", "Accuracy (үздік нәтижелер қатарында)", "Архитектурасы күрделірек"],
       [f"Dosovitskiy және т.б., 2021 {cite('vit')}", "Vision Transformer", "ImageNet, JFT-300M",
        "Top-1 accuracy", "Шағын жиындарда алдын ала оқытусыз әлсіз"],
       ["Осы жұмыс", "Ықшам CNN + аугментация", "MNIST",
        f"Accuracy {kz(ACC)}%, F1 {kz(MACRO['f1-score']*100)}%", "Бір модель, орталық процессорда оқыту"]],
      widths=[3.6, 3.3, 2.4, 3.4, 4.3], font=10)
ptext("Талдаудан келесі қорытындылар шығады. Біріншіден, MNIST бойынша ең жоғары "
      "нәтижелерге (99,7–99,9%) ансамбльдер арқылы жетеді, бірақ олар бірнеше ондаған "
      "модельді оқытуды талап етеді. Екіншіден, жеке ықшам CNN 99,3–99,5% деңгейіне "
      "жетуге қабілетті, бұл практикалық қолдану үшін жеткілікті. Үшіншіден, "
      "трансформерлер шағын сұр түсті кескіндер үшін тиімсіз. Сондықтан осы жұмыста "
      "**таңдалған тәсіл** – бір ықшам CNN (DigitCNN) және деректерді аугментациялау; ал "
      "оның тиімділігі базалық логистикалық регрессиямен, көп қабатты перцептронмен "
      "(Multilayer Perceptron, MLP) және аугментациясыз нұсқасымен бірдей шартта "
      "салыстырылады. Бұл тәсіл есептеу ресурсына қойылатын талап пен дәлдік арасындағы "
      "тепе-теңдікті қамтамасыз етеді.")

# =====================================================================
# 2 ДЕРЕКТЕР МЕН ЗЕРТТЕУ ӘДІСТЕМЕСІ
# =====================================================================
h1("2 ДЕРЕКТЕР МЕН ЗЕРТТЕУ ӘДІСТЕМЕСІ")
h2("2.1 Деректер жиынтығы: шығу көзі, лицензиясы және құрамы")
ptext("Жұмыста MNIST (Modified National Institute of Standards and Technology) деректер "
      f"жиыны қолданылды {cite('mnist')}. Жиынды Я. Лекун, К. Кортес және К. Бёрджес "
      "АҚШ Ұлттық стандарттар және технологиялар институтының (NIST) қолжазба "
      "деректерінен құрастырған. Цифрлар 20×20 аймаққа сыйдырылып, масса орталығы "
      "бойынша 28×28 кенептің ортасына орналастырылған. Жиын Creative Commons "
      "Attribution-Share Alike 3.0 (CC BY-SA 3.0) лицензиясымен ашық таратылады, "
      "сондықтан оны оқу және зерттеу мақсатында заңды түрде пайдалануға болады. "
      "Деректер torchvision.datasets.MNIST класы арқылы автоматты жүктеледі, сондықтан "
      "электрондық тапсыру жиынтығына деректердің өзі емес, оларды жүктеу тәсілі "
      "енгізілді. Жиынның сипаттамасы "
      f"{nt()}-кестеде берілген.")
table("MNIST деректер жиынының сипаттамасы",
      ["Сипаттама", "Мәні"],
      [["Атауы, нұсқасы", "MNIST, түпнұсқа нұсқа (1998)"],
       ["Авторлары / ұйымы", "LeCun Y., Cortes C., Burges C. J. C."],
       ["Лицензиясы", "CC BY-SA 3.0"],
       ["Көлемі", f"{sp(DS['n_train'] + DS['n_val'])} оқыту + {sp(DS['n_test'])} тест суреті"],
       ["Кескін өлшемі", f"{DS['image_shape'][0]}×{DS['image_shape'][1]} пиксель, 1 арна (сұр түсті)"],
       ["Пиксель мәндері", "0–255 (0 – фон, 255 – цифр)"],
       ["Кластар саны", "10 (0–9 цифрлары)"],
       ["Жүктеу тәсілі", "torchvision.datasets.MNIST"]],
      widths=[5.5, 11.5])
ptext(f"Деректер жиынынан мысалдар {nf()}-суретте көрсетілген.")
figure("dataset_samples.png", f"MNIST тест жиынынан мысалдар (дереккөз: MNIST {cite('mnist')})", width=16)

h2("2.2 Деректердің сапасы мен сыныптар таралуын талдау")
tc = DS["train_counts"]
ptext("Модельді оқытпас бұрын деректерге зерттеушілік талдау жүргізілді (src/data.py "
      "модуліндегі dataset_report функциясы). Талдау нәтижелері "
      f"{nt()}-кестеде, ал сыныптардың таралуы {nf()}-суретте көрсетілген.")
table("Деректер сапасын тексеру нәтижелері",
      ["Тексеру", "Нәтиже"],
      [["Жетіспейтін мәндер", str(DS["missing_values"])],
       ["Оқыту жиынындағы бірдей (қайталанатын) суреттер", str(DS["duplicates_in_train"])],
       ["Оқыту мен тест жиыны арасындағы бірдей суреттер", str(DS["train_test_overlap"])],
       ["Train бөлігіндегі пиксельдердің орташа мәні", kz(DS["pixel_mean_train"], 4)],
       ["Train бөлігіндегі пиксельдердің стандартты ауытқуы", kz(DS["pixel_std_train"], 4)],
       ["Ең аз класс (train)", f"{tc.index(min(tc))} цифры – {sp(min(tc))} сурет"],
       ["Ең көп класс (train)", f"{tc.index(max(tc))} цифры – {sp(max(tc))} сурет"]],
      widths=[11.0, 6.0])
figure("class_distribution.png", "Сыныптардың train, validation және test бөліктері бойынша таралуы", width=15.5)
ratio = max(tc) / min(tc)
ptext(f"Талдау көрсеткендей, деректерде жетіспейтін мәндер жоқ, ал ең көп және ең аз "
      f"кластың қатынасы {kz(ratio)} құрайды. Демек, сыныптар салыстырмалы түрде "
      "теңгерімді, сондықтан кластарға салмақ беру немесе қосымша теңгерімдеу қажет емес, "
      "ал Accuracy метрикасы модель сапасын дұрыс сипаттайды. Сонымен бірге әр класс "
      "бойынша Precision, Recall және F1 бөлек есептелді. Деректердің шуы негізінен "
      "жазудың өзіндегі екіұштылықпен байланысты (3.4-бөлімді қараңыз).")

h2("2.3 Train/validation/test бөлу қағидасы және алдын ала өңдеу")
ptext("Нұсқаулық талабына сәйкес бөліктер алдын ала белгіленді. Ресми 60 000 оқыту "
      "суретінен seed = 42 бойынша кездейсоқ ауыстыру арқылы 54 000 сурет train, 6 000 "
      "сурет validation бөлігіне бөлінді. Ресми 10 000 тест суреті тек қорытынды "
      "бағалауда қолданылды: гиперпараметрлерді және үздік модельді таңдау тек validation "
      "бойынша жүргізілді. Тест жиынындағы суреттерді басқа адамдар жазғандықтан және "
      "оқыту мен тест арасында бірдей суреттер жоқ екені тексерілгендіктен, деректердің "
      f"ағып кетуі болмайды ({nt()}-кесте).")
table("Деректердің бөлінуі",
      ["Бөлік", "Суреттер саны", "Мақсаты"],
      [["Train", sp(DS["n_train"]), "Модель салмақтарын оқыту"],
       ["Validation", sp(DS["n_val"]), "Гиперпараметрлерді және үздік дәуірді/модельді таңдау"],
       ["Test", sp(DS["n_test"]), "Тек қорытынды тәуелсіз бағалау"]],
      widths=[3.5, 3.5, 10.0])
ptext("Алдын ала өңдеу қадамдары және олардың негіздемесі:")
bullets([
    "пиксель мәндерін [0; 1] аралығына келтіру – оңтайландыру тұрақтылығы үшін;",
    "нормализация x′ = (x – 0,1307) / 0,3081, мұндағы 0,1307 және 0,3081 – MNIST "
    "оқыту жиынының орташа мәні мен стандартты ауытқуы (тек оқыту деректері бойынша "
    "есептелген, сондықтан ақпарат ағып кетпейді);",
    "аугментация (тек train бөлігі үшін): ±10° бұру, 10%-ға дейін жылжыту, 90–110% "
    "масштабтау. Негіздемесі – нақты қолжазба әртүрлі көлбеулікпен және орында "
    "жазылады; аугментация модельді осы өзгерістерге төзімді етеді. Оның әсері E03 және "
    "E04 эксперименттерінде тексерілді.",
])
ptext("Веб-қосымшада пайдаланушы жүктеген немесе салған сурет MNIST суреттерінен "
      "ерекшеленуі мүмкін (ақ фон, басқа өлшем, цифр шетте орналасқан). Сондықтан "
      "оны MNIST форматына келтіретін алгоритм жасалды (src/predict.py): сұр түске "
      "айналдыру; фон ашық болса инверсиялау; әлсіз шуды тазалау; цифрды қоршайтын "
      "шекараны қию; пропорцияны сақтап 20×20 аймаққа сыйдыру; 28×28 кенепте масса "
      f"орталығы бойынша ортаға қою. Тану жүйесінің жалпы тізбегі {nf()}-суретте көрсетілген.")
figure("pipeline.png", "Тану жүйесінің жалпы тізбегі", width=16.5)

h2("2.4 Базалық шешім")
ptext("Нұсқаулыққа сәйкес алдымен қарапайым модель арқылы бастапқы нәтиже алынды. "
      "Базалық шешім ретінде пиксельдер бойынша көп класты логистикалық регрессия "
      f"(scikit-learn кітапханасы {cite('pedregosa')}, L2-регуляризация C = 0,1, lbfgs "
      "алгоритмі, 500 итерация) таңдалды. Бұл модель әр пиксельді тәуелсіз белгі ретінде "
      "қарастырып, сызықтық бөлу бетін құрады; ол кеңістіктік құрылымды ескермейді. "
      f"Базалық модельдің validation дәлдігі – {kz(va('E01'))}%, тест дәлдігі – "
      f"{kz(ta('E01'))}%. Бұл кейінгі терең модельдерді салыстыруға арналған төменгі шекара.")
ptext("Екінші салыстыру моделі – толық байланысқан көп қабатты перцептрон (MLP): "
      "784 → 256 → 128 → 10, ReLU активациясы және Dropout(0,2). Ол сызықтық емес "
      "белгілерді үйрене алады, бірақ пикселдердің көршілестігін ескермейді.")

h2("2.5 Негізгі модельдің архитектурасы")
ptext("Негізгі модель – DigitCNN. Ол екі конволюциялық блоктан және классификатордан "
      "тұрады. Әр конволюциялық блокта екі 3×3 конволюциялық қабат, пакеттік "
      "нормализация, ReLU активациясы, 2×2 максималды пулинг және Dropout(0,25) бар. "
      "Классификатор 128 нейронды жасырын қабаттан, Dropout(0,5)-тен және 10 нейронды "
      f"шығыс қабатынан тұрады. Архитектура сызбасы {nf()}-суретте, ал қабаттардың толық "
      f"сипаттамасы {nt()}-кестеде берілген.")
figure("architecture.png", "DigitCNN моделінің архитектурасы", width=16.5)
table("DigitCNN моделінің қабаттары",
      ["Қабат", "Шығыс өлшемі", "Параметрлер саны"],
      [["Кіріс", "1×28×28", "–"],
       ["Conv2d 3×3, 32 сүзгі", "32×28×28", "320"],
       ["BatchNorm2d + ReLU", "32×28×28", "64"],
       ["Conv2d 3×3, 32 сүзгі + ReLU", "32×28×28", "9 248"],
       ["MaxPool 2×2 + Dropout 0,25", "32×14×14", "0"],
       ["Conv2d 3×3, 64 сүзгі", "64×14×14", "18 496"],
       ["BatchNorm2d + ReLU", "64×14×14", "128"],
       ["Conv2d 3×3, 64 сүзгі + ReLU", "64×14×14", "36 928"],
       ["MaxPool 2×2 + Dropout 0,25", "64×7×7", "0"],
       ["Flatten", "3136", "0"],
       ["Linear + ReLU + Dropout 0,5", "128", "401 536"],
       ["Linear (шығыс) + Softmax", "10", "1 290"],
       ["Барлығы", "", sp(PARAMS)]],
      widths=[8.5, 4.0, 4.5])
ptext(f"Модельдің оқытылатын параметрлерінің саны – {sp(PARAMS)}. Параметрлердің "
      "басым бөлігі (≈86%) бірінші толық байланысқан қабатқа тиесілі. Барлық "
      "конволюцияларда padding = 1, сондықтан (6) формула бойынша өлшем тек пулинг "
      "қабаттарында кішірейеді: 28 → 14 → 7. Модель нөлден оқытылды: дайын модель немесе "
      "алдын ала оқытылған салмақтар (transfer learning) қолданылмады.")

h2("2.6 Шығын функциясы, оптимизатор және гиперпараметрлер")
ptext("Шығын функциясы ретінде (3) формуладағы кросс-энтропия, оңтайландырғыш ретінде "
      "Adam таңдалды. Оқыту жылдамдығы әр 3 дәуір сайын 2 есе азайтылды (StepLR). "
      "Регуляризация үшін Dropout, пакеттік нормализация және аугментация қолданылды. "
      "Әр дәуірдің соңында модель validation бөлігінде бағаланып, validation дәлдігі ең "
      "жоғары болған дәуірдің салмақтары сақталды (early model selection). "
      f"Гиперпараметрлер {nt()}-кестеде келтірілген.")
table("Терең модельдердің гиперпараметрлері",
      ["Параметр", "Мәні", "Таңдау негіздемесі"],
      [["Шығын функциясы", "CrossEntropyLoss", "Көп класты жіктеудің стандарты"],
       ["Оңтайландырғыш", "Adam", "Бейімделгіш қадам, тез жинақталу"],
       ["Оқыту жылдамдығы", "0,001 / 0,0003", "Екі мән validation бойынша салыстырылды"],
       ["Оқыту жылдамдығын азайту", "StepLR: 3 дәуір, γ = 0,5", "Соңғы дәуірлерде нақтылау"],
       ["Пакет өлшемі", "128", "CPU жады мен жылдамдық арасындағы тепе-теңдік"],
       ["Дәуірлер саны", str(EPOCHS), "Validation қисығы тұрақталады"],
       ["Dropout", "0,25 / 0,5", "Қайта оқытудың алдын алу"],
       ["Аугментация", "RandomAffine", "Жазудың көлбеулігі мен жылжуына төзімділік"],
       ["Seed", str(CFG["seed"]), "Қайталанатын нәтиже"]],
      widths=[4.6, 4.4, 8.0], font=11)

h2("2.7 Эксперименттер жоспары және есептеу ортасы")
ptext("Нұсқаулық талабына сәйкес бірнеше конфигурация бірдей шартта салыстырылды: "
      "барлығында бірдей деректер бөлінісі, seed = 42, пакет өлшемі 128, дәуірлер саны 8 "
      "және бірдей есептеу ортасы қолданылды. Әр эксперименттің конфигурациясы configs/ "
      f"бумасында JSON (JavaScript Object Notation) форматындағы файл ретінде сақталды (Б қосымшасы). Эксперименттер жоспары {nt()}-кестеде берілген.")
table("Эксперименттер жоспары",
      ["ID", "Модель", "Өзгертілетін фактор", "Тексерілетін сұрақ"],
      [["E01", "Логистикалық регрессия", "Базалық шешім", "Төменгі шекара қандай?"],
       ["E02", "MLP", "Толық байланысқан желі", "Сызықтық емес модельдің пайдасы"],
       ["E03", "DigitCNN", "Аугментациясыз", "Конволюцияның MLP-ден артықшылығы"],
       ["E04", "DigitCNN", "Аугментация, lr = 0,001", "Аугментацияның әсері"],
       ["E05", "DigitCNN", "Аугментация, lr = 0,0003", "Оқыту жылдамдығының әсері"]],
      widths=[1.4, 3.8, 5.0, 6.8], font=11)
ptext(f"Есептеу ортасы {nt()}-кестеде көрсетілген. Барлық эксперименттер графикалық "
      "процессорсыз, кәдімгі ноутбуктың орталық процессорында (Central Processing Unit, "
      "CPU) орындалды.")
table("Бағдарламалық орта және есептеу құрылғысы",
      ["Компонент", "Нұсқасы / сипаттамасы"],
      [["Операциялық жүйе", ENV["os"]],
       ["Процессор", f"{ENV['cpu']} ({ENV['threads']} ағын)"],
       ["Есептеу құрылғысы", ENV["device"].upper()],
       ["Python", ENV["python"]],
       ["PyTorch / torchvision", f"{ENV['torch']} / {ENV['torchvision']}"],
       ["NumPy", ENV["numpy"]],
       ["scikit-learn", ENV["scikit-learn"]],
       ["Кездейсоқтық параметрі (seed)", str(CFG["seed"])]],
      widths=[6.0, 11.0])

# =====================================================================
# 3 БАҒДАРЛАМАЛЫҚ ІСКЕ АСЫРУ, ЭКСПЕРИМЕНТ ЖӘНЕ НӘТИЖЕЛЕР
# =====================================================================
h1("3 БАҒДАРЛАМАЛЫҚ ІСКЕ АСЫРУ, ЭКСПЕРИМЕНТ ЖӘНЕ НӘТИЖЕЛЕР")
h2("3.1 Бағдарламаның құрылымы және негізгі модульдері")
ptext(f"Бағдарлама Python тілінде PyTorch кітапханасы {cite('paszke', 'pytorch_docs')} "
      "негізінде жазылды; кодты құрылымдауда және оқыту циклін ұйымдастыруда "
      f"практикалық ұсыныстар {cite('geron', 'chollet')} ескерілді. Жоба құрылымы нұсқаулықта ұсынылған репозиторий құрылымына "
      f"сәйкес ұйымдастырылды ({nt()}-кесте).")
table("Жобаның құрылымы және модульдері",
      ["Файл / бума", "Мақсаты"],
      [["src/data.py", "MNIST жүктеу, train/validation/test бөлу, деректерді талдау"],
       ["src/model.py", "MLP және DigitCNN модельдері"],
       ["src/train.py", "Конфигурация бойынша бір экспериментті оқыту және тіркеу"],
       ["src/evaluate.py", "Үздік модельді validation бойынша таңдау, тест метрикалары, графиктер"],
       ["src/predict.py", "Пайдаланушы суретін өңдеу және болжау"],
       ["configs/", "Эксперименттер конфигурациялары (E01–E05, JSON)"],
       ["outputs/", "experiments.csv, metrics.json, графиктер, логтар"],
       ["models/", "Оқытылған модельдердің салмақтары (.pt)"],
       ["tests/", "Модуль тесттері (unittest)"],
       ["app.py, web/", "Flask сервері, сайттың беті, стильдері және скрипті"],
       ["README.md, requirements.txt", "Іске қосу нұсқаулығы және тәуелділіктер"]],
      widths=[5.2, 11.8], font=11)
ptext("DigitCNN моделі nn.Module класынан мұраланған класс ретінде іске асырылды. Модель "
      "кодының талдау үшін маңызды бөлігі төменде берілген (толық код А қосымшасында):")
code_block('''
class DigitCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25))
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Linear(64 * 7 * 7, 128), nn.ReLU(),
            nn.Dropout(0.5), nn.Linear(128, num_classes))
''')
para(after=6)
ptext("Оқыту циклінде үздік модель тек validation дәлдігі бойынша сақталады – бұл тест "
      "жиынының таңдауға қатыспауын қамтамасыз етеді:")
code_block('''
for epoch in range(1, cfg["epochs"] + 1):
    tl, ta = run_epoch(model, train_loader, criterion, device, optimizer)
    vl, va = run_epoch(model, val_loader, criterion, device)   # validation
    scheduler.step()
    if va > best_val:                       # таңдау тек validation бойынша
        best_val, best_epoch = va, epoch
        torch.save(model.state_dict(), weights)
''')
para(after=6)
ptext("Әр эксперимент «python -m src.train --config configs/<ID>.json» командасымен "
      "іске қосылады; нәтижесі outputs/experiments.csv тіркеу кестесіне жазылады. "
      "Барлық эксперимент аяқталғаннан кейін «python -m src.evaluate --select-best» "
      "командасы validation бойынша үздік модельді таңдап, тест жиынында қорытынды "
      "бағалау жүргізеді. Кодтың дұрыстығы 8 модуль тестімен тексерілді "
      "(«python -m unittest discover tests»).")

h2("3.2 Оқыту барысы")
hist = M["history"]
ptext(f"Validation бойынша үздік нәтиже {BEST} экспериментінде алынды. Оның оқыту "
      f"барысындағы көрсеткіштері {nt()}-кестеде және {nf()}-суретте көрсетілген.")
table(f"{BEST} экспериментінің оқыту барысы",
      ["Дәуір", "Train loss", "Train accuracy, %", "Val. loss", "Val. accuracy, %", "Уақыт, с"],
      [[i + 1, kz(hist["train_loss"][i], 4), kz(hist["train_acc"][i] * 100),
        kz(hist["val_loss"][i], 4), kz(hist["val_acc"][i] * 100), kz(hist["epoch_time"][i], 0)]
       for i in range(len(hist["train_loss"]))],
      widths=[1.7, 2.8, 3.2, 2.8, 3.3, 2.2], font=11)
figure("training_curves.png", f"{BEST} экспериментіндегі шығын функциясы мен дәлдіктің өзгеруі", width=16)
gap = (hist["val_acc"][-1] - hist["train_acc"][-1]) * 100
ptext(f"Шығын функциясы алғашқы дәуірлерде күрт төмендеп, кейін тұрақталады. Validation "
      f"дәлдігі бірінші дәуірде-ақ {kz(hist['val_acc'][0]*100)}%-ға жетіп, ең жоғары мәні "
      f"{kz(VAL)}% болды ({M['best_epoch']}-дәуір). Соңғы дәуірдегі validation мен train "
      f"дәлдіктерінің айырмасы {kz(gap)} пайыздық тармақ. "
      + ("Validation көрсеткішінің train-нен жоғары болуы аугментация мен Dropout тек "
         "оқыту кезінде жұмыс істейтінімен түсіндіріледі; бұл модельдің қайта оқытылмағанын "
         "көрсетеді. " if gap > 0 else
         "Айырма аз, демек қайта оқыту байқалмайды. ")
      + f"Оқытудың жалпы уақыты {mins(TTIME)} минутты құрады.")

h2("3.3 Эксперименттер нәтижелері және модельдерді салыстыру")
ptext("Барлық эксперименттердің нәтижелері нұсқаулықтың Г қосымшасындағы үлгіге сәйкес "
      f"тіркеу кестесінде берілген ({nt()}-кесте). Метрика ретінде validation және test "
      "дәлдігі көрсетілген; модельді таңдау тек validation бойынша жүргізілді.")
rows = []
for i, r in EXPS.items():
    rows.append([i, r["model"], "MNIST v1", r["hyperparams"], r["seed"],
                 f"{kz(va(i))} / {kz(ta(i))}", f"{kz(tsec(i), 0)} с", r["note"]])
table("Эксперименттерді тіркеу кестесі (Accuracy, %: validation / test)",
      ["ID", "Модель", "Деректер нұсқасы", "Негізгі гиперпараметрлер", "Seed", "Метрика",
       "Уақыт", "Ескерту"],
      rows, widths=[1.1, 3.0, 1.8, 3.0, 1.1, 2.5, 1.6, 2.9], font=9)
ptext(f"Эксперименттердің validation дәлдігінің дәуірлер бойынша өзгерісі {nf()}-суретте, "
      f"ал қорытынды салыстыру {nf() + 1}-суретте көрсетілген.")
figure("experiments_val_curves.png", "Эксперименттердің validation дәлдігі (дәуірлер бойынша)", width=14.5)
figure("experiments_bar.png", "Эксперименттердің validation және test дәлдігін салыстыру", width=14.5)


def diff_text(a, b):
    d = va(b) - va(a)
    word = "арттырды" if d > 0 else "төмендетті" if d < 0 else "өзгертпеді"
    return d, word


d23 = va("E03") - va("E02")
d34, w34 = diff_text("E03", "E04")
d45 = va("E05") - va("E04")
ptext("Нәтижелерді талдау:")
bullets([
    f"базалық логистикалық регрессия (E01) validation жиынында {kz(va('E01'))}% дәлдік "
    "көрсетті – сызықтық модель жазу стилінің әртүрлілігін толық сипаттай алмайды;",
    f"MLP (E02) сызықтық емес белгілерді үйрену арқылы дәлдікті {kz(va('E02'))}%-ға дейін "
    f"арттырды (+{kz(va('E02') - va('E01'))} п.т.);",
    f"DigitCNN (E03) MLP-ден {('жоғары' if d23 > 0 else 'төмен')} нәтиже берді: "
    f"{kz(va('E03'))}% ({'+' if d23 >= 0 else ''}{kz(d23)} п.т.). Бұл конволюцияның "
    "кеңістіктік құрылымды ескеруінің артықшылығын растайды;",
    f"аугментация (E04) validation дәлдігін {kz(abs(d34))} п.т.-ға {w34} "
    f"({kz(va('E03'))}% → {kz(va('E04'))}%); оқыту уақыты {mins(tsec('E03'))} және "
    f"{mins(tsec('E04'))} минут болды (айырма есептеу құрылғысының жүктемесіне байланысты);",
    f"оқыту жылдамдығын 0,0003-ке азайту (E05) validation дәлдігін "
    f"{kz(va('E05'))}%-ға {'арттырды' if d45 > 0 else 'төмендетті' if d45 < 0 else 'өзгертпеді'} "
    f"(E04-пен салыстырғанда {'+' if d45 >= 0 else ''}{kz(d45)} п.т.).",
])
ptext(f"Validation дәлдігі бойынша үздік конфигурация – **{BEST}** "
      f"({EXPS[BEST]['model']}, {EXPS[BEST]['hyperparams']}). Тек осы модель қорытынды "
      f"модель ретінде таңдалып, тест жиынында бағаланды. Оның тест дәлдігі {kz(ACC)}% – "
      f"базалық шешімнен {kz(ACC - ta('E01'))} пайыздық тармаққа жоғары. Басқа "
      "эксперименттердің тест мәндері кестеде тек салыстыру үшін келтірілген және таңдауға "
      "әсер еткен жоқ.")
cnn_ids = ["E03", "E04", "E05"]
spread = max(va(i) for i in cnn_ids) - min(va(i) for i in cnn_ids)
best_test_id = max(cnn_ids, key=ta)
note = (f"Айта кету керек, CNN конфигурацияларының (E03–E05) validation дәлдігі арасындағы "
        f"айырма {kz(spread)} п.т.-дан аспайды, яғни 6 000 суреттің {round(spread / 100 * 6000)}-іне "
        "ғана тең. ")
if best_test_id != BEST:
    note += (f"Тест жиынында ең жоғары нәтижені {best_test_id} көрсетті ({kz(ta(best_test_id))}%), "
             f"бірақ ол validation бойынша {BEST}-тен төмен болғандықтан, нұсқаулық талабына сәйкес "
             "қорытынды модель ретінде таңдалмады: тест нәтижесіне қарап модель таңдау деректердің "
             "ағып кетуіне тең болар еді. ")
note += ("Бір seed-пен алынған мұндай шағын айырмалар статистикалық тұрғыдан маңызды деп айтуға "
         "негіз бермейді. Демек, MNIST-те аугментация мен оқыту жылдамдығының әсері шамалы, ал "
         "негізгі сапа өсімі конволюциялық архитектураның өзінен (E02 → E03) алынды. "
         "Аугментацияның пайдасы пайдаланушы салған, MNIST-тен өзгеше суреттерде көбірек байқалуы "
         "мүмкін, бірақ бұл жеке тексеруді қажет етеді.")
ptext(note)

h2("3.4 Қорытынды модельді бағалау және қателерді талдау")
ptext(f"Қорытынды модель ({BEST}) тест жиынында (10 000 сурет) **{kz(ACC)}%** дәлдік "
      f"көрсетті, яғни {ERR} сурет қате жіктелді. Макро-орташа Precision – "
      f"{kz(MACRO['precision']*100)}%, Recall – {kz(MACRO['recall']*100)}%, F1 – "
      f"{kz(MACRO['f1-score']*100)}%, ROC-AUC (one-vs-rest, macro) – {kz(AUC, 5)}. "
      f"Әр цифр бойынша метрикалар {nt()}-кестеде берілген.")
pc_rows = []
for d in range(10):
    r = M["per_class"][str(d)]
    pc_rows.append([d, kz(r["precision"] * 100), kz(r["recall"] * 100),
                    kz(r["f1-score"] * 100), sp(r["support"])])
pc_rows.append(["Макро-орташа", kz(MACRO["precision"] * 100), kz(MACRO["recall"] * 100),
                kz(MACRO["f1-score"] * 100), "10 000"])
table("Тест жиынындағы әр цифр бойынша жіктеу метрикалары",
      ["Цифр", "Precision, %", "Recall, %", "F1, %", "Суреттер саны"],
      pc_rows, widths=[3.4, 3.4, 3.4, 3.4, 3.4], font=11)
worst = min(range(10), key=lambda d: M["per_class"][str(d)]["f1-score"])
best_d = max(range(10), key=lambda d: M["per_class"][str(d)]["f1-score"])
cm = M["confusion_matrix"]
pairs = sorted(((cm[i][j], i, j) for i in range(10) for j in range(10) if i != j), reverse=True)[:3]
pair_txt = "; ".join(f"{i} цифры {j} ретінде – {n} рет" for n, i, j in pairs)
ptext(f"Ең жақсы танылатын цифр – {best_d} (F1 = {kz(M['per_class'][str(best_d)]['f1-score']*100)}%), "
      f"ең қиыны – {worst} (F1 = {kz(M['per_class'][str(worst)]['f1-score']*100)}%). Қателердің "
      f"кластар арасында таралуын қателер матрицасы ({nf()}-сурет) көрсетеді: диагональ – "
      "дұрыс жауаптар, ал диагональдан тыс элементтер – қателер.")
figure("confusion_matrix.png", f"Қорытынды модельдің ({BEST}) тест жиынындағы қателер матрицасы", width=12.5)
ptext(f"Ең жиі кездесетін қателер: {pair_txt}. Бұл цифрлардың жазылу пішіні шынымен "
      f"ұқсас. Модель қателескен мысалдар {nf()}-суретте көрсетілген.")
figure("misclassified.png", "Модель қате жіктеген тест суреттерінің мысалдары", width=15.5)
ptext("Қате жіктелген суреттерді талдау олардың көпшілігі адам үшін де екіұшты екенін "
      "көрсетеді: цифрлар өте көлбеу, үзік немесе әдеттен тыс стильде жазылған. Кей "
      "жағдайда модель қате жауапқа жоғары сенімділік береді – бұл нақты жүйеде сенімділігі "
      "төмен нәтижелерді адамның тексеруіне жіберу қажеттігін көрсетеді.")

h2("3.5 Бағдарламалық прототип: веб-қосымша және API")
ptext("Модельді соңғы пайдаланушыға қолжетімді ету үшін «DigitNet» веб-қосымшасы "
      "әзірленді. Серверлік бөлік Flask микрофреймворкінде "
      f"{cite('flask')}, клиенттік бөлік гипермәтінді белгілеу тілі (HyperText Markup "
      "Language, HTML), каскадтық стильдер кестесі (Cascading Style Sheets, CSS) және "
      f"JavaScript тілінде жазылды; цифр салатын тақта HTML Canvas API {cite('mdn')} арқылы "
      "іске асырылды. Сервер іске қосылғанда модельді жадқа бір рет жүктейді және "
      "қолданбалы бағдарламалау интерфейсін (Application Programming Interface, API) "
      "REST стилінде (Representational State Transfer) ұсынады. Жауаптар JavaScript Object "
      f"Notation (JSON) форматында қайтарылады ({nt()}-кесте).")
table("Веб-қосымшаның API нүктелері",
      ["Нүкте", "Әдіс", "Сипаттамасы"],
      [["/", "GET", "Басты бет (HTML шаблоны)"],
       ["/api/predict", "POST", "Суретті қабылдап, цифрды, сенімділікті және 10 ықтималдықты JSON түрінде қайтарады"],
       ["/api/sample", "GET", "MNIST тест жиынынан кездейсоқ сурет және оның болжамы"],
       ["/api/metrics", "GET", "Қорытынды модельдің метрикалары (JSON)"],
       ["/results/<файл>", "GET", "Оқыту графиктері (PNG)"]],
      widths=[3.6, 1.8, 11.6], font=11)
ptext("Сайт келесі бөлімдерден тұрады: негізгі көрсеткіштері бар басты экран; "
      "интерактивті демо (тышқанмен немесе саусақпен салу, сурет жүктеу, MNIST "
      "мысалдары); нәтиже панелі (танылған цифр, сенімділік, 10 класс бойынша "
      "ықтималдықтар, модельге берілетін 28×28 сурет); жұмыс принципі; модель "
      "архитектурасы; эксперименттер мен метрикалар; жоба туралы мәлімет. Салу тақтасында "
      "нәтиже нақты уақытта жаңарады: JavaScript коды әр 180 мс сайын кенептің суретін "
      "серверге жібереді. Сайттың басты экраны "
      f"{nf()}-суретте, ал тышқанмен салынған цифрды тану мысалы {nf() + 1}-суретте көрсетілген.")
figure("site_hero.png", "DigitNet веб-қосымшасының басты экраны", width=16)
figure("site_demo.png", "Тышқанмен салынған «3» цифрын тану нәтижесі", width=15.5)
ptext("Сайт бейімделгіш (responsive) етіп жасалған: смартфон экранында бөлімдер бір "
      "бағанға орналасады. Қорғау кезіндегі демонстрация интернетке тәуелді емес: "
      "сервер жергілікті компьютерде іске қосылады, ал техникалық ақауға арналған "
      "резервтік нұсқа ретінде сайттың скриншоттары дайындалды. Іске қосу нұсқаулығы "
      "Ә қосымшасында берілген.")

h2("3.6 Шектеулер және этикалық тәуекелдер")
ptext("Жұмыстың **шектеулері**:")
bullets([
    "модель тек бір цифрды таниды; бірнеше цифрдан тұратын санды тану үшін алдымен "
    "сегменттеу қажет;",
    "MNIST суреттері таза әрі ортаға қойылған; нақты фотосуреттердегі көлеңке, "
    "жарықтың біркелкі болмауы немесе фондағы сызықтар сапаны төмендетуі мүмкін;",
    "MNIST негізінен АҚШ тұрғындарының жазуынан құралған, сондықтан басқа жазу "
    "дәстүрлеріне (мысалы, «1» және «7» цифрларының еуропалық жазылуына) модельдің "
    "жалпылау қабілеті шектеулі болуы мүмкін;",
    "эксперименттер бір seed-пен орындалды; әр конфигурацияны бірнеше рет қайталау "
    "нәтижелердің статистикалық сенімділігін арттырар еді;",
    "есептеу ресурсының шектеулілігіне байланысты гиперпараметрлерді іздеу тек оқыту "
    "жылдамдығының екі мәнімен шектелді.",
])
ptext("**Этикалық тәуекелдер.** MNIST жиынында дербес деректер жоқ (тек цифрлар "
      "кескіндері) және ол ашық лицензиямен таратылады. Дегенмен нақты жүйеде (банк, "
      "сайлау, емтихан) тану қатесі адамға тікелей әсер етуі мүмкін, сондықтан сенімділігі "
      "төмен нәтижелерді адам тексеруі, ал модельдің шешімдері тіркеліп отыруы қажет. "
      "Веб-қосымша пайдаланушы суреттерін дискіге сақтамайды – олар тек жадта өңделеді.")

# =====================================================================
# ҚОРЫТЫНДЫ
# =====================================================================
h1("ҚОРЫТЫНДЫ", center=True)
ptext("Курстық жұмыста конволюциялық нейрондық желі негізінде қолжазба цифрларды тану "
      "жүйесі әзірленді. Қойылған міндеттер бойынша келесі нәтижелер алынды:")
crit_ok = ACC >= 99 and (ACC - ta("E01")) >= 5 and TTIME < 1800
bullets([
    "әдебиеттерге шолу жасалып, LeNet-тен ConvNeXt пен ViT-ке дейінгі архитектуралар "
    "салыстырылды; MNIST үшін ықшам CNN мен аугментацияның тиімділігі негізделді;",
    f"MNIST жиынының лицензиясы, сапасы және сыныптар таралуы талданды (жетіспейтін мәндер "
    f"жоқ, сыныптар теңгерімді), деректер {sp(DS['n_train'])}/{sp(DS['n_val'])}/{sp(DS['n_test'])} "
    "бөліктерге ағып кетусіз бөлінді;",
    f"базалық логистикалық регрессия ({kz(ta('E01'))}% тест дәлдігі), MLP және DigitCNN "
    f"({sp(PARAMS)} параметр) іске асырылды;",
    "бес эксперимент бірдей шартта (seed = 42) жүргізіліп, тіркеу кестесіне жазылды; "
    f"validation бойынша үздік конфигурация – {BEST};",
    f"қорытынды модель тест жиынында Accuracy {kz(ACC)}%, macro-F1 "
    f"{kz(MACRO['f1-score']*100)}%, ROC-AUC {kz(AUC, 5)} көрсетті; қателер негізінен "
    "пішіні ұқсас цифрлар арасында болатыны анықталды;",
    "цифрды салып, нақты уақытта тануға мүмкіндік беретін Flask негізіндегі веб-қосымша "
    "және REST API әзірленді;",
    "жұмыстың шектеулері мен этикалық тәуекелдері сипатталды.",
], numbered=True)
ptext("**Мақсатқа жету дәрежесі.** Кіріспеде қойылған табыс критерийі (тест дәлдігі "
      "≥ 99%, базалық әдістен кемінде 5 п.т. жоғары, CPU-да 30 минуттан аз оқыту) "
      + ("толық орындалды: " if crit_ok else "ішінара орындалды: ")
      + f"дәлдік {kz(ACC)}%, базалық әдістен айырма {kz(ACC - ta('E01'))} п.т., "
      f"оқыту уақыты {mins(TTIME)} минут. Зерттеу сұрағына жауап: ықшам CNN толық "
      "байланысқан желіден және сызықтық модельден айтарлықтай жоғары нәтиже береді, "
      "ал MNIST-те аугментация мен оқыту жылдамдығының әсері шамалы (validation бойынша "
      "0,1 п.т. шамасында) екені анықталды.")
ptext("**Практикалық құндылығы.** Әзірленген модель мен веб-қосымшаны бланктерді, "
      "сауалнамаларды және тест парақтарын автоматты өңдеу жүйелерінің құрамдас бөлігі "
      "ретінде, сондай-ақ терең оқыту пәнін оқытуда интерактивті құрал ретінде қолдануға "
      "болады.")
ptext("**Шектеулер мен даму бағыттары.** Модель бір цифрды таниды және таза кескіндерге "
      "бейімделген. Әрі қарай: көп цифрлы сандарды сегменттеу және тану; нақты "
      "фотосуреттерден жиналған деректермен қосымша оқыту; бірнеше seed бойынша "
      "эксперименттерді қайталау; модельдер ансамблін қолдану; қазақ әліпбиінің қолжазба "
      "әріптерін тануға бейімдеу; модельді ONNX форматына түрлендіріп, мобильді "
      "құрылғыларға орналастыру жоспарлануда.")

# Абревиатураларды санау үшін негізгі мәтінді сақтау (дереккөздер мен қосымшаларсыз)
_body_parts = [p.text for p in doc.paragraphs[BODY_START:]]
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            _body_parts.append(c.text)
BODY_TEXT = "\n".join(_body_parts)

# =====================================================================
# ПАЙДАЛАНЫЛҒАН ДЕРЕК КӨЗДЕРІНІҢ ТІЗІМІ
# =====================================================================
h1("ПАЙДАЛАНЫЛҒАН ДЕРЕК КӨЗДЕРІНІҢ ТІЗІМІ", center=True)
uncited = [k for k in REFS if k not in _ref_order]
if uncited:
    print("ЕСКЕРТУ: мәтінде сілтеме жоқ дереккөздер:", uncited)
for i, k in enumerate(_ref_order, 1):
    para(f"{i}. {REFS[k]}", indent=True)

# =====================================================================
# ГЕНЕРАТИВТІ ЖИ ҚҰРАЛДАРЫН ПАЙДАЛАНУ ТУРАЛЫ МӘЛІМЕТ
# =====================================================================
h1("ГЕНЕРАТИВТІ ЖАСАНДЫ ИНТЕЛЛЕКТ ҚҰРАЛДАРЫН ПАЙДАЛАНУ ТУРАЛЫ МӘЛІМЕТ", center=True)
ptext("Әдістемелік нұсқаулықтың академиялық адалдық талабына сәйкес жұмыста "
      "пайдаланылған генеративті ЖИ құралдары туралы мәлімет беріледі.")
ptext("**Құрал атауы:** Claude (Anthropic компаниясы), Claude Code ортасы.")
ptext("**Қолданылған мақсаты:** бағдарлама кодының құрылымын (src/, configs/, tests/) және "
      "веб-интерфейстің бастапқы нұсқасын дайындау, эксперименттерді автоматтандыру "
      "сценарийлерін жазу, түсіндірме жазба мәтінінің жобасын құрастыру және рәсімдеуге "
      "көмектесу.")
ptext("**Нәтижелердің шынайылығы:** барлық эксперименттер автордың компьютерінде нақты "
      "іске қосылды; жұмыста келтірілген барлық метрикалар, кестелер мен графиктер "
      "outputs/ бумасындағы эксперимент файлдарынан автоматты түрде алынған, ойдан "
      "құрастырылған мәндер жоқ.")
ptext("**Студент тексерген және өзгерткен бөліктер:** "
      "_______________________________________________________________"
      "_______________________________________________________________ "
      "(студент өзі толтырады).")

# =====================================================================
# ҚОСЫМШАЛАР
# =====================================================================
h1("ҚОСЫМША А", center=True)
center("Бағдарламаның толық коды", bold=True, after=8)
for k, fname in enumerate(("src/data.py", "src/model.py", "src/train.py", "src/evaluate.py",
                           "src/predict.py", "app.py", "web/static/app.js"), 1):
    para(f"А.{k} {fname} файлы", bold=True, indent=False, after=4, before=6)
    code_block((ROOT / fname).read_text(encoding="utf-8"), size=9)

h1("ҚОСЫМША Ә", center=True)
center("Іске қосу нұсқаулығы (README.md)", bold=True, after=8)
code_block((ROOT / "README.md").read_text(encoding="utf-8"), size=9)

h1("ҚОСЫМША Б", center=True)
center("Эксперименттер конфигурациялары және тәуелділіктер", bold=True, after=8)
for k, cfgp in enumerate(sorted((ROOT / "configs").glob("*.json")), 1):
    para(f"Б.{k} configs/{cfgp.name}", bold=True, indent=False, after=4, before=6)
    code_block(cfgp.read_text(encoding="utf-8"), size=9)
para(f"Б.{k + 1} requirements.txt", bold=True, indent=False, after=4, before=6)
code_block((ROOT / "requirements.txt").read_text(encoding="utf-8"), size=9)

# =====================================================================
# Белгілеулер кестесін толтыру: тек ≥3 рет қолданылғандары
# =====================================================================
def count_abbr(abbr):
    if abbr == "TP, FP, FN":
        return min(len(re.findall(r"(?<![A-Za-z])" + a + r"(?![A-Za-z])", BODY_TEXT)) for a in ("TP", "FP", "FN"))
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(abbr) + r"(?![A-Za-z0-9])", BODY_TEXT))


used = [(a, d, count_abbr(a)) for a, d in ABBR]
kept = [(a, d) for a, d, n in used if n >= 3]
print("Қысқартулар:", ", ".join(f"{a}={n}" for a, d, n in used))
abbr_tbl = doc.add_table(rows=0, cols=2)
for a, d in kept:
    cells = abbr_tbl.add_row().cells
    for c, txt in zip(cells, (a, d)):
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.first_line_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(txt)
for row in abbr_tbl.rows:
    row.cells[0].width = Cm(3.8)
    row.cells[1].width = Cm(13.2)
ABBR_ANCHOR._p.addnext(abbr_tbl._tbl)

doc.save(OUT)
print("Сақталды:", OUT)
print("Дереккөздер саны:", len(_ref_order))
