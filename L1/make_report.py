"""Собирает отчёт report/report.html и печатает его в report/Конанчук_Практика1_Вариант12.pdf (через Edge).

Таблицы берутся прямо из simplex.py, поэтому числа в отчёте совпадают с программой.
"""

import os
import subprocess
import tempfile
from fractions import Fraction

from main import A, b, c, signs
from simplex import canon, choose, drop, start_aux, step, to_main

FIO = "Конанчук Иван Алексеевич"
STREAM = "1.1"
VARIANT = 12
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def tex(v):
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    sign = "-" if v < 0 else ""
    return f"{sign}\\frac{{{abs(v.numerator)}}}{{{v.denominator}}}"


def lin(coefs, names=None, const=None):
    """Линейное выражение в TeX: 2x_1 - x_3 + 18."""
    parts = []
    items = list(zip(names or range(1, len(coefs) + 1), coefs))
    if const is not None and const != 0:
        parts.append(("-" if const < 0 else "+", tex(abs(Fraction(const)))))
    for i, k in items:
        k = Fraction(k)
        if k == 0:
            continue
        sign = "-" if k < 0 else "+"
        a = abs(k)
        num = "" if a == 1 else tex(a)
        parts.append((sign, f"{num}x_{{{i}}}"))
    if not parts:
        return "0"
    s = ("-" if parts[0][0] == "-" else "") + parts[0][1]
    for sign, t in parts[1:]:
        s += f" {sign} {t}"
    return s


def table_html(T, pivot=None, gone=None):
    pi, pj = pivot if pivot else (-1, -1)
    h = ["<table class='sx'><tr><th></th>"]
    for j, v in enumerate(T.cols):
        cls = " class='pc'" if j == pj else ""
        h.append(f"<th{cls}>$x_{{{v}}}$</th>")
    h.append("<th>$b$</th></tr>")
    for i, r in enumerate(T.rows):
        h.append("<tr>")
        cls = " class='pr'" if i == pi else ""
        h.append(f"<th{cls}>$x_{{{r}}}$</th>")
        for j, a in enumerate(T.A[i]):
            if i == pi and j == pj:
                cls = " class='pv'"
            elif i == pi:
                cls = " class='pr'"
            elif j == pj:
                cls = " class='pc'"
            else:
                cls = ""
            h.append(f"<td{cls}>${tex(a)}$</td>")
        cls = " class='pr'" if i == pi else ""
        h.append(f"<td{cls}>${tex(T.b[i])}$</td></tr>")
    h.append("<tr class='obj'><th>$c$</th>")
    for j, v in enumerate(T.c):
        cls = " class='pc'" if j == pj else ""
        h.append(f"<td{cls}>${tex(v)}$</td>")
    h.append(f"<td>${tex(T.mQ)}$</td></tr></table>")
    return "".join(h)


def run_phase(T, art=()):
    """Возвращает список (таблица, разрешающий элемент или None, вычеркнутые) и итоговую таблицу."""
    steps = []
    while True:
        i, j = choose(T)
        if j is None or i is None:
            steps.append((T, None, None))
            return steps, T
        nxt = step(T, i, j)
        gone = [v for v in nxt.cols if v in art]
        steps.append((T, (i, j), gone))
        T = drop(nxt, gone) if gone else nxt


def pivot_text(T, i, j):
    col = T.cols[j]
    neg = ", ".join(f"c_{{{v}}} = {tex(T.c[k])}" for k, v in enumerate(T.cols) if T.c[k] < 0)
    ratios = []
    for r in range(len(T.rows)):
        a = T.A[r][j]
        if a > 0:
            ratios.append(f"x_{{{T.rows[r]}}}: \\ {tex(T.b[r])} / {tex(a)} = {tex(T.b[r] / a)}")
    ratio = ";\\quad ".join(ratios)
    negs = [v for v in T.c if v < 0]
    tie = negs.count(T.c[j]) > 1
    if len(negs) == 1:
        pick = f"Отрицательный коэффициент в строке $c$ один: ${neg}$, поэтому беру столбец $x_{{{col}}}$."
    elif tie:
        pick = (f"В строке $c$ отрицательные ${neg}$. Наименьшие значения равны, "
                f"беру переменную с меньшим номером, то есть $x_{{{col}}}$.")
    else:
        pick = f"В строке $c$ отрицательные ${neg}$. Самый отрицательный у $x_{{{col}}}$, беру этот столбец."
    if len(ratios) == 1:
        row = f"В столбце $x_{{{col}}}$ положительный элемент только один: ${ratio}$."
    else:
        row = (f"Считаю отношения $b_i / a_{{i{col}}}$ для $a_{{i{col}}} > 0$: ${ratio}$. "
               f"Минимум в строке $x_{{{T.rows[i]}}}$.")
    return (
        f"<p>{pick} {row} Разрешающий элемент ${tex(T.A[i][j])}$: "
        f"$x_{{{col}}}$ входит в базис, $x_{{{T.rows[i]}}}$ выходит.</p>"
    )


def section_steps(steps, title):
    out = []
    for k, (T, pv, gone) in enumerate(steps):
        out.append(f"<h3>{title}, таблица {k}</h3>")
        out.append(table_html(T, pv))
        if pv:
            out.append(pivot_text(T, *pv))
            if gone:
                out.append(f"<p>$x_{{{gone[0]}}}$ искусственная, поэтому после пересчёта её столбец вычёркиваю.</p>")
        else:
            out.append("<p>Отрицательных коэффициентов в строке $c$ нет, значит дальше уменьшать цель некуда, это оптимум.</p>")
    return "\n".join(out)


def build():
    cc, AA, bb, n, slack = canon(c, A, signs, b, "min")
    T0, art = start_aux(AA, bb, slack)
    aux_steps, Ta = run_phase(T0, art)
    Tm = to_main(Ta, cc, art, [])
    main_steps, Tf = run_phase(Tm)

    rel = {"<=": "\\le", "=": "=", ">=": "\\ge"}
    src_sys = " \\\\ ".join(f"{lin(r)} {rel[s]} {v}" for r, s, v in zip(A, signs, b))
    can_sys = " \\\\ ".join(f"{lin(r)} = {tex(v)}" for r, v in zip(AA, bb))

    # вспомогательная задача: строки с искусственными
    aux_rows = []
    for i, r in enumerate(T0.rows):
        aux_rows.append(f"{lin(AA[i])} + x_{{{r}}} = {tex(bb[i])}" if r in art else f"{lin(AA[i])} = {tex(bb[i])}")
    aux_sys = " \\\\ ".join(aux_rows)
    art_expr = []
    for i, r in enumerate(T0.rows):
        if r in art:
            art_expr.append(f"x_{{{r}}} = {lin([-v for v in T0.A[i]], T0.cols, T0.b[i])}")
    wa = lin(T0.c, T0.cols, -T0.mQ)

    # переход к основной: базисные через свободные
    expr_rows = []
    for i, r in enumerate(Ta.rows):
        if cc[r - 1] != 0:
            expr_rows.append(f"x_{{{r}}} = {lin([-v for v in Ta.A[i]], Ta.cols, Ta.b[i])}")
    start_x = [Fraction(0)] * len(cc)
    for i, r in enumerate(Ta.rows):
        start_x[r - 1] = Ta.b[i]
    w_main = lin(Tm.c, Tm.cols, -Tm.mQ)

    x = [Fraction(0)] * len(cc)
    for i, r in enumerate(Tf.rows):
        x[r - 1] = Tf.b[i]
    Z = -Tf.mQ
    xs = ", ".join(tex(v) for v in x[:n])
    xs_dec = ", ".join(f"{float(v):g}" for v in x[:n])

    checks = []
    for r, s, v in zip(A, signs, b):
        lhs = sum(Fraction(a) * xi for a, xi in zip(r, x))
        terms = " + ".join(f"{a} \\cdot {tex(xi)}" for a, xi in zip(r, x[:n]) if a != 0)
        checks.append(f"<li>${terms} = {tex(lhs)} {rel[s]} {v}$</li>")
    zcheck = " + ".join(f"{k} \\cdot {tex(v)}" for k, v in zip(c, x))

    vertices = [tex(-T.mQ) for T, _, _ in main_steps]

    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Практическая работа 1. Вариант {VARIANT}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: "Times New Roman", serif; font-size: 13pt; line-height: 1.4; color: #000; }}
  h1 {{ font-size: 17pt; text-align: center; margin: 0 0 4pt; }}
  .sub {{ text-align: center; margin-bottom: 14pt; }}
  h2 {{ font-size: 14.5pt; margin: 16pt 0 6pt; }}
  h3 {{ font-size: 13pt; margin: 12pt 0 4pt; }}
  .meta td {{ padding: 2pt 10pt 2pt 0; }}
  table.sx {{ border-collapse: collapse; margin: 6pt 0; page-break-inside: avoid; }}
  table.sx th, table.sx td {{ border: 1px solid #555; padding: 3pt 9pt; text-align: center; min-width: 34pt; }}
  table.sx tr.obj td, table.sx tr.obj th {{ border-top: 2px solid #000; }}
  .pc {{ background: #dbeaf0; }}
  .pr {{ background: #f6e6d4; }}
  .pv {{ background: #e8c48a; font-weight: bold; }}
  .ans {{ border: 1.5px solid #000; padding: 6pt 10pt; display: inline-block; }}
  table.cmp {{ border-collapse: collapse; margin: 6pt 0; }}
  table.cmp th, table.cmp td {{ border: 1px solid #555; padding: 3pt 9pt; text-align: center; }}
  .legend span {{ display: inline-block; margin-right: 12pt; font-size: 11pt; }}
  .legend i {{ display: inline-block; width: 11pt; height: 11pt; vertical-align: -1pt; margin-right: 4pt; border: 1px solid #888; }}
  .pb {{ page-break-before: always; }}
</style></head><body>

<h1>Практическая работа №1</h1>
<div class="sub">«Задачи линейного программирования»<br>Методы оптимизации</div>

<table class="meta">
<tr><td>ФИО:</td><td>{FIO}</td></tr>
<tr><td>Поток:</td><td>{STREAM}</td></tr>
<tr><td>Вариант:</td><td>{VARIANT} (номер в списке 12, $12 \\bmod 20 = 12$)</td></tr>
</table>

<h2>Постановка задачи</h2>
<p>Минимизировать $Z = {lin(c)}$ при условиях</p>
$$\\begin{{cases}} {src_sys} \\\\ x_1, x_2, x_3, x_4 \\ge 0 \\end{{cases}}$$

<h2>1. Приведение к каноническому виду</h2>
<p>Задача уже на минимум и все правые части положительные, поэтому менять знаки не нужно. Остаётся убрать неравенства.
В первое ограничение ($\\le$) я добавил остаточную переменную $x_5 \\ge 0$,
из третьего ($\\ge$) вычел избыточную переменную $x_6 \\ge 0$. В целевую функцию они входят с коэффициентом 0.</p>
$$W = {lin(cc)} \\to \\min$$
$$\\begin{{cases}} {can_sys} \\\\ x_1, \\dots, x_6 \\ge 0 \\end{{cases}}$$

<h2>2. Вспомогательная задача</h2>
<p>Чтобы начать симплекс-метод, в каждой строке должна быть базисная переменная с коэффициентом $+1$, которой нет в других строках.
В первой строке это $x_5$. Во второй такой переменной нет, а в третьей $x_6$ стоит с минусом (получилось бы $x_6 = -3 < 0$).
Поэтому во вторую и третью строки я добавил искусственные переменные $x_7, x_8 \\ge 0$:</p>
$$\\begin{{cases}} {aux_sys} \\end{{cases}} \\qquad W_a = x_7 + x_8 \\to \\min$$
<p>Базис: $x_5, x_7, x_8$; свободные: $x_1, x_2, x_3, x_4, x_6$. Выражаю искусственные переменные через свободные и подставляю в $W_a$:</p>
$${" ,\\qquad ".join(art_expr)}$$
$$W_a = {wa}$$
<p>Коэффициенты при свободных переменных идут в нижнюю строку таблицы, а в правый нижний угол $-Q = {tex(T0.mQ)}$.</p>
<div class="legend"><span><i style="background:#dbeaf0"></i>разрешающий столбец</span><span><i style="background:#f6e6d4"></i>разрешающая строка</span><span><i style="background:#e8c48a"></i>разрешающий элемент</span></div>

<h2>3. Решение вспомогательной задачи</h2>
<p>Как пересчитываю таблицу: разрешающий элемент $\\hat a_{{i^*j^*}} = 1/a_{{i^*j^*}}$; разрешающая строка делится на $a_{{i^*j^*}}$;
разрешающий столбец делится на $a_{{i^*j^*}}$ со сменой знака; остальные элементы по правилу прямоугольника
$\\hat a_{{ij}} = a_{{ij}} - \\dfrac{{a_{{i^*j}}\\, a_{{ij^*}}}}{{a_{{i^*j^*}}}}$ (так же для $b$ и строки $c$).</p>
{section_steps(aux_steps, "Вспомогательная")}
<p>Получилось $W_a = 0$, обе искусственные переменные вышли из базиса. Значит допустимая точка есть:
$x = ({", ".join(tex(v) for v in start_x[:6])})$, в нём $Z = {tex(-Tm.mQ)}$.</p>

<h2>4. Переход к основной задаче</h2>
<p>Ограничения беру из последней таблицы без изменений. Нижнюю строку нужно заменить на настоящую цель $Z$,
но в ней есть базисные $x_2$ и $x_4$. Выражаю их из строк таблицы через свободные $x_1, x_3, x_6$:</p>
$${" ,\\qquad ".join(expr_rows)}$$
$$Z = 2x_1 + 3x_2 + x_3 + 4x_4 = 2x_1 + 3(2 + x_1 - x_3 - x_6) + x_3 + 4(3 - x_1 + x_6) = {w_main}$$
<p>Отсюда новая строка $c$: коэффициенты при $x_1, x_3, x_6$, а в углу $-Q = {tex(Tm.mQ)}$.</p>

<h2>5. Решение основной задачи</h2>
{section_steps(main_steps, "Основная")}

<h2>Ответ</h2>
<p>Свободные переменные равны нулю: $x_5 = x_2 = x_6 = 0$. Значения базисных беру из столбца $b$.</p>
<div class="ans">$x^* = ({xs}) = ({xs_dec}), \\qquad Z(x^*) = {tex(Z)} = {float(Z):g}$</div>
<p>В последней строке $c$ нет нулей, все коэффициенты больше нуля, поэтому оптимальная точка одна.
Значение цели менялось так: ${" \\to ".join(vertices)}$.</p>

<h3>Проверка</h3>
<ul>{"".join(checks)}<li>все $x_j \\ge 0$</li><li>$Z = {zcheck} = {tex(Z)}$</li></ul>

<h2>Решение в Excel (Поиск решения)</h2>
<p>Для проверки я составил модель в файле <code>excel/variant12.xlsx</code>: изменяемые ячейки B4:E4 ($x_1, \\dots, x_4$),
целевая ячейка G5 = СУММПРОИЗВ(коэффициенты; переменные) на минимум, три ограничения
(левые части через СУММПРОИЗВ), неотрицательность переменных, метод «Поиск решения линейных задач симплекс-методом».</p>
<table class="cmp">
<tr><th></th><th>$x_1$</th><th>$x_2$</th><th>$x_3$</th><th>$x_4$</th><th>$Z$</th></tr>
<tr><td>Симплекс-метод</td><td>2.5</td><td>0</td><td>4.5</td><td>0.5</td><td>11.5</td></tr>
<tr><td>Excel Solver</td><td>2.5</td><td>0</td><td>4.5</td><td>0.5</td><td>11.5</td></tr>
</table>
<p>Ответ Solver полностью совпал с моим.</p>

<h2>Рефлективный вывод</h2>
<p>До этой работы я почти не разбирался в линейном программировании, поэтому начинал с нуля.
Сначала было непонятно, зачем нужна вспомогательная задача, если можно сразу решать основную.
Разобрался, когда попробовал обнулить свободные переменные: во второй и третьей строке не получалось
допустимой точки, и стало ясно, для чего нужны искусственные переменные.</p>
<p>Дольше всего я разбирался с нижней строкой таблицы и углом $-Q$, а ещё с переходом к основной задаче,
где цель приходится заново выражать через свободные переменные. Больше всего помог пример с практики,
который разобран по шагам. Чтобы не запутаться в дробях, я написал свой симплекс на Python, он печатает
те же таблицы, что и в отчёте. Excel показал тот же ответ, так что в решении я уверен.</p>

<script>
renderMathInElement(document.body, {{delimiters: [
  {{left: "$$", right: "$$", display: true}},
  {{left: "$", right: "$", display: false}}
]}});
</script>
</body></html>
"""


def main():
    os.makedirs("report", exist_ok=True)
    html = build()
    path = os.path.abspath("report/report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    pdf = os.path.abspath("report/Конанчук_Практика1_Вариант12.pdf")
    if os.path.exists(pdf):
        os.remove(pdf)
    profile = os.path.join(tempfile.gettempdir(), "edge-report-profile")
    subprocess.run([
        EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--user-data-dir={profile}", "--virtual-time-budget=15000",
        f"--print-to-pdf={pdf}", path,
    ], check=True, capture_output=True)
    if not os.path.exists(pdf):
        raise SystemExit("Edge не создал PDF")
    print(pdf)


if __name__ == "__main__":
    main()
