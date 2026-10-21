"""Собирает отчёт report/report.html и печатает его в report/Конанчук_Лаба2_Метод_ломаных.pdf (через Edge)."""

import os
import subprocess
import tempfile

from examples import EXAMPLES
from piyavsky import estimate_L, parse, piyavsky

FIO = "Конанчук Иван Алексеевич"
STREAM = "1.1"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PDF = "report/Конанчук_Лаба2_Метод_ломаных.pdf"

TEX = {
    "practice": r"W(x) = \tfrac12 (x-2)^2 + \sin(\pi x)",
    "rastrigin": r"W(x) = x^2 - 10\cos(2\pi x) + 10",
    "ackley": r"W(x) = -20\,e^{-0.2|x|} - e^{\cos(2\pi x)} + e + 20",
    "task": r"W(x) = x + \sin(3.14159\,x)",
}


def run_all():
    out = {}
    for name, title, expr, a, b, eps, L in EXAMPLES:
        f = parse(expr)
        slope = None
        if L is None:
            L, slope = estimate_L(f, a, b)
        res = piyavsky(f, a, b, eps, L)
        out[name] = dict(title=title, expr=expr, a=a, b=b, eps=eps, L=L, slope=slope, res=res)
    return out


def fnum(v, d=4):
    v = round(v, d) + 0.0
    return f"{v:.{d}f}"


def example_block(name, e, intro, newpage=True):
    r = e["res"]
    k, x, p, w, d = r["last"]
    if e["slope"] is None:
        lline = f"$L = {e['L']:g}$ (взял как на практике)."
    else:
        lline = (f"Наибольшая крутизна по оценке $\\max|W'| \\approx {e['slope']:.2f}$, "
                 f"беру $L = {e['L']:.2f}$ (запас 20%).")
    return f"""
<h3{' class="pb"' if newpage else ''}>{e['title']}</h3>
<p>{intro}</p>
<p>${TEX[name]}$, отрезок $[{e['a']}, {e['b']}]$, $\\varepsilon = {e['eps']}$. {lline}</p>
<figure><img src="../img/{name}.png"></figure>
<table class="res">
<tr><td>найденный минимум</td><td>$x^* \\approx {fnum(r['x'])}$, $W(x^*) \\approx {fnum(r['W'])}$</td></tr>
<tr><td>итераций</td><td>{r['iters']} (вычислений $W$: {r['evals']}, вместе с концами отрезка)</td></tr>
<tr><td>время</td><td>{r['time'] * 1000:.2f} мс</td></tr>
<tr><td>остановка</td><td>последняя проба $x = {fnum(x)}$: $\\delta = W - p = {fnum(d)} < {e['eps']}$</td></tr>
</table>
"""


def build():
    E = run_all()
    pr = E["practice"]["res"]
    lecture = ["2", "7/6 ≈ 1.167", "17/6 ≈ 2.833", "0.763", "1.571", "2.346", "3.321", "1.430"]
    rows = "".join(
        f"<tr><td>{k}</td><td>{lecture[k - 1]}</td><td>{fnum(x, 3)}</td><td>{fnum(p, 3)}</td>"
        f"<td>{fnum(w, 3)}</td><td>{fnum(d, 3)}</td></tr>"
        for k, x, p, w, d in pr["history"])

    summary = "".join(
        f"<tr><td>{e['title']}</td><td>[{e['a']}, {e['b']}]</td><td>{e['eps']}</td><td>{e['L']:.2f}</td>"
        f"<td>{fnum(e['res']['x'])}</td><td>{fnum(e['res']['W'])}</td><td>{e['res']['iters']}</td>"
        f"<td>{e['res']['time'] * 1000:.2f}</td></tr>"
        for e in E.values())

    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Лабораторная работа 2. Метод ломаных</title>
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
  figure {{ margin: 6pt 0; page-break-inside: avoid; text-align: center; }}
  figure img {{ width: 100%; }}
  figcaption {{ font-size: 11pt; }}
  table.res, table.t {{ border-collapse: collapse; margin: 6pt 0; page-break-inside: avoid; }}
  table.res td, table.t td, table.t th {{ border: 1px solid #555; padding: 3pt 8pt; }}
  table.t td, table.t th {{ text-align: center; }}
  code {{ font-size: 11pt; }}
  .pb {{ page-break-before: always; }}
</style></head><body>

<h1>Лабораторная работа №2</h1>
<div class="sub">«Метод ломаных (метод Пиявского)»<br>Методы оптимизации</div>

<table class="meta">
<tr><td>ФИО:</td><td>{FIO}</td></tr>
<tr><td>Поток:</td><td>{STREAM}</td></tr>
<tr><td>Код:</td><td>https://github.com/chikirao/met_opt (папка L2)</td></tr>
</table>

<h2>Постановка задачи</h2>
<p>Нужно найти глобальный минимум функции одной переменной $W(x)$ на отрезке $[a, b]$.
Функция может иметь несколько локальных минимумов, и локальный спуск из одной точки сходится к ближайшему из них, который не обязательно глобальный.
Программа принимает строку с формулой, концы отрезка и точность $\\varepsilon$, а выдаёт рисунок
(функция, итоговая ломаная, найденная точка), приближённые $x^*$ и $W(x^*)$, число итераций и время счёта.</p>

<h2>Метод</h2>
<p>Функция липшицева, если есть число $L$, что $|W(u) - W(v)| \\le L|u - v|$: график нигде не круче прямой с наклоном $L$.
Тогда для каждой точки $u$, в которой посчитано значение функции, график на всём отрезке лежит не ниже «галочки» $g(x) = W(u) - L|x - u|$.
Верхняя огибающая всех галочек (ломаная) лежит под графиком и служит нижней оценкой функции, а её нижние углы показывают,
где функция может принимать наименьшие значения.</p>
<p>Алгоритм я реализовал в том же виде, что и на практике:</p>
<ol>
<li>Считаю $W$ в концах отрезка $a$ и $b$. Точки, в которых посчитано $W$, дальше называю верхними.</li>
<li>Между каждыми соседними верхними точками $u_л, u_п$ нахожу угол ломаной, то есть пересечение двух галочек:
$$x = \\frac{{W_л - W_п}}{{2L}} + \\frac{{u_л + u_п}}{{2}}, \\qquad p = W_л - L(x - u_л).$$</li>
<li>Выбираю угол с самым маленьким $p$ (при ничьей левый) и считаю в нём $W(x)$. Новая точка становится верхней.</li>
<li>Считаю зазор $\\delta = W(x) - p$. Если $\\delta < \\varepsilon$, останавливаюсь.</li>
<li>Ответ: из всех посчитанных точек та, где $W$ меньше всего.</li>
</ol>
<p>Критерий остановки обоснован так: $p$ это наименьшее значение ломаной, а ломаная лежит под графиком, значит глобальный минимум не меньше $p$.
Лучшее найденное значение не больше $W(x)$, поэтому оно отличается от глобального минимума меньше чем на $\\varepsilon$.</p>
<p>Минимум не ищется перебором по мелкой сетке: каждая следующая точка вычисляется как пересечение галочек.</p>

<h3>Как я выбираю $L$</h3>
<p>$L$ должна быть не меньше наибольшего значения $|W'|$ на отрезке, иначе ломаная может пройти выше графика и метод пропустит минимум.
Если $L$ задана, программа использует её. Если нет, я оцениваю её так: на отрезке беру соседние точки, считаю $|\\Delta W| / |\\Delta x|$,
нахожу максимум и добавляю запас 20%. Эта оценка нужна только для $L$, минимум по ней не ищется.
$L$ выбирается один раз до начала расчёта и не меняется. Завышенная $L$ не нарушает корректность ответа, но увеличивает число итераций.</p>

<h2>Проверка на примере с практики</h2>
<p>Сначала я проверил программу на примере, который разбирали на практике: $W(x) = \\tfrac12(x-2)^2 + \\sin(\\pi x)$, $[0, 4]$, $L = 6$, $\\varepsilon = 1$.
Все пробы совпали с ручным расчётом с практики.</p>
<table class="t">
<tr><th>шаг</th><th>проба на практике</th><th>$x$</th><th>$p$</th><th>$W(x)$</th><th>$\\delta$</th></tr>
{rows}
</table>
<p>На шаге 8 зазор $0.917 < 1$, остановка. Лучшая посчитанная точка $x^* \\approx {fnum(pr['x'], 3)}$, $W \\approx {fnum(pr['W'], 3)}$
(глобальный минимум около $1.546$ и $-0.887$, разница меньше $\\varepsilon$).</p>
<figure><img src="../img/steps.png"><figcaption>Первые четыре шага: оранжевая ломаная, её самый низкий угол и новая проба.</figcaption></figure>
<figure><img src="../img/practice.png"></figure>

<h2 class="pb">Демонстрация на тестовых функциях</h2>
{example_block("rastrigin", E["rastrigin"], "Одномерная функция Растригина. На отрезке четыре локальных минимума (около −1, 0, 1 и 2), глобальный в нуле. Отрезок я выбрал несимметричным, чтобы первая проба не попала в ноль сразу.", newpage=False)}
{example_block("ackley", E["ackley"], "Одномерная функция Экли. На отрезке много локальных минимумов, глобальный в нуле. В нуле у функции излом из-за $|x|$, производной там нет, но функция липшицева.")}
{example_block("task", E["task"], "Функция из примера в задании. На отрезке два локальных минимума: около $-0.6$ (глобальный) и около $1.4$.")}

<h2 class="pb">Итоги</h2>
<table class="t">
<tr><th>функция</th><th>отрезок</th><th>$\\varepsilon$</th><th>$L$</th><th>$x^*$</th><th>$W(x^*)$</th><th>итераций</th><th>время, мс</th></tr>
{summary}
</table>
<p>Во всех примерах найден глобальный минимум. По рисункам видно, что пробы сгущаются около локальных минимумов, а на участках, где функция заведомо выше уже найденного значения, их почти нет.</p>

<h2>Программа</h2>
<p>Код на Python в файле <code>piyavsky.py</code>. Запуск:</p>
<p><code>python piyavsky.py "x + sin(3.14159*x)" -1 3 0.01</code> (можно добавить <code>--L 6</code> и <code>--show</code>).</p>
<ul>
<li><code>parse</code> превращает строку в функцию; разрешены только $x$ и математические функции (sin, cos, exp, abs, pi и т.д.).</li>
<li><code>estimate_L</code> оценивает $L$, если она не задана.</li>
<li><code>corner</code> считает угол ломаной по формуле выше.</li>
<li><code>piyavsky</code> основной цикл: выбор угла, проба, зазор, остановка.</li>
<li><code>plot</code> рисует функцию, ломаную, пробы, ответ и график зазора по итерациям.</li>
</ul>
<p>Все примеры из отчёта запускаются командой <code>python examples.py</code>.</p>

<h2>Выводы по работе</h2>
<p>Я реализовал метод ломаных на Python: программа принимает формулу функции строкой, концы отрезка и точность $\\varepsilon$,
на каждом шаге считает углы ломаной как пересечения галочек, вычисляет функцию в самом низком угле и останавливается,
когда зазор между значением функции и углом ломаной меньше $\\varepsilon$. На примере с практики ($L = 6$, $\\varepsilon = 1$)
все 8 проб совпали с ручным расчётом, ответ $x^* \\approx {fnum(pr['x'], 3)}$, $W \\approx {fnum(pr['W'], 3)}$.
На функции Растригина метод нашёл глобальный минимум $x^* \\approx {fnum(E['rastrigin']['res']['x'], 4)}$ за {E['rastrigin']['res']['iters']} итерации,
на функции Экли $x^* \\approx {fnum(E['ackley']['res']['x'], 4)}$ за {E['ackley']['res']['iters']} итераций,
на функции из задания $x^* \\approx {fnum(E['task']['res']['x'], 3)}$, $W \\approx {fnum(E['task']['res']['W'], 3)}$ за {E['task']['res']['iters']} итерации,
каждый расчёт занял несколько миллисекунд. Больше всего итераций потребовала функция Растригина: у неё самая большая
константа Липшица ($L \\approx {E['rastrigin']['L']:.1f}$), а соседние локальные минимумы около $\\pm 1$ лишь примерно на 1 выше глобального,
поэтому ломаная долго не может их отбросить. Главное ограничение метода в том, что константу $L$ нужно знать заранее:
при заниженной $L$ ломаная проходит выше графика и минимум можно пропустить, а при сильно завышенной растёт число итераций.</p>

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
    path = os.path.abspath("report/report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build())
    pdf = os.path.abspath(PDF)
    if os.path.exists(pdf):
        os.remove(pdf)
    profile = os.path.join(tempfile.gettempdir(), "edge-report-profile")
    subprocess.run([
        EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--user-data-dir={profile}", "--virtual-time-budget=15000",
        "--allow-file-access-from-files", f"--print-to-pdf={pdf}", path,
    ], check=True, capture_output=True)
    if not os.path.exists(pdf):
        raise SystemExit("Edge не создал PDF")
    print(pdf)


if __name__ == "__main__":
    main()
