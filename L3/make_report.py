"""Собирает отчёт в HTML и PDF через Microsoft Edge.

Программные результаты вычисляются заново. Формулы MathML работают без интернета.
"""

import contextlib
import html
import io
import subprocess
import tempfile
from pathlib import Path

import sympy as sp

from lagrange import solve
from main import BASE, constraints, f, main, x, y

FIO = "Конанчук Иван Алексеевич"
STREAM = "1.1"
VARIANT = 12
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PDF = BASE / "report/Конанчук_Лаба3_Вариант12.pdf"


def m(*expressions, block=False):
    """Цепочка равенств в MathML, без внешних скриптов и шрифтов."""
    parts = [sp.printing.mathml(e, printer="presentation") for e in expressions]
    body = "<mo>=</mo>".join(parts)
    for name, symbol in [("lam", "λ"), ("phi", "φ"), ("v", "V")]:
        body = body.replace(f"<mi>{name}</mi>", f"<mi>{symbol}</mi>")
    return (f'<math xmlns="http://www.w3.org/1998/Math/MathML" '
            f'display="{"block" if block else "inline"}">{body}</math>')


def build(output):
    res = solve(f, constraints, (x, y))
    lam = res["unknowns"][-1]
    candidate = res["candidates"][0]
    root = candidate["solution"]
    t, b = sp.symbols("t b", real=True)
    L = sp.Symbol("L")
    h = sp.Function("h")(x, y)
    fx = sp.Function("f")(x, y)
    phi = sp.Function("phi")(t)
    system = "".join(m(eq, sp.Integer(0), block=True) for eq in res["equations"])
    program_values = [root[x], root[y], root[lam], candidate["value"],
                      candidate["constraints"][0], tuple(candidate["stationarity"])]
    program_row = "".join(f"<td>{value}</td>" for value in program_values)
    # Ключевой фрагмент вычислений; полные исходники приложены к отчёту.
    code = '''x, y = sp.symbols("x y", real=True)
lam = sp.Symbol("lam", real=True)
f = x**2 + y**2
constraints = [2*x + y - 10]
L = f + lam*constraints[0]
equations = [sp.diff(L, v) for v in (x, y, lam)]
roots = sp.solve(equations, (x, y, lam), dict=True)
for root in roots:
    print(root)
    print("h =", sp.simplify(constraints[0].subs(root)))
    print("f =", sp.simplify(f.subs(root)))'''
    start = output.index("Действительных кандидатов:")
    end = output.index("Проверка на допустимой прямой:")
    excerpt = output[start:end].strip().replace("\n\n", "\n")

    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Лабораторная работа 3. Вариант 12</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: "Times New Roman", serif; font-size: 13pt;
         line-height: 1.3; color: #000; margin: 0; }}
  h1 {{ font-size: 17pt; text-align: center; margin: 0 0 4pt; }}
  .sub {{ text-align: center; margin-bottom: 14pt; }}
  h2 {{ font-size: 14.5pt; margin: 11pt 0 6pt; break-after: avoid; }}
  h3 {{ font-size: 13pt; margin: 10pt 0 4pt; break-after: avoid; }}
  p {{ margin: 5pt 0; }}
  .meta td {{ padding: 2pt 10pt 2pt 0; }}
  math {{ font-family: "Cambria Math", math; }}
  math[display="block"] {{ margin: 7pt 0; break-inside: avoid; }}
  .system math {{ margin: 2pt 0; }}
  .system {{ border-left: 1px solid #555; width: fit-content; padding: 2pt 14pt;
             margin: 6pt auto; break-inside: avoid; }}
  .pb {{ break-before: page; }}
  .ans {{ border: 1.5px solid #000; padding: 6pt 10pt; margin: 8pt 0; }}
  table.cmp {{ width: 100%; border-collapse: collapse; margin: 7pt 0; break-inside: avoid; }}
  .cmp td, .cmp th {{ border: 1px solid #555; padding: 3pt 8pt; text-align: center; }}
  .program {{ font-size: 12pt; line-height: 1.3; }}
  figure {{ margin: 8pt 0; text-align: center; break-inside: avoid; }}
  figure img {{ width: 100%; }}
  figcaption {{ font-size: 11pt; }}
  pre {{ font-family: Consolas, monospace; font-size: 9.5pt; line-height: 1.2;
         border: 1px solid #888; padding: 7pt; white-space: pre-wrap; overflow-wrap: anywhere;
         break-inside: avoid; margin: 6pt 0; }}
  code {{ font-family: Consolas, monospace; font-size: 10.5pt; }}
  .small {{ font-size: 11pt; }}
  a {{ color: #000; overflow-wrap: anywhere; }}
</style></head><body>

<h1>Лабораторная работа №3</h1>
<div class="sub">«Метод множителей Лагранжа»<br>Методы оптимизации</div>
<table class="meta">
<tr><td>ФИО:</td><td>{FIO}</td></tr>
<tr><td>Поток:</td><td>{STREAM}</td></tr>
<tr><td>Вариант:</td><td>{VARIANT} (номер в потоке 12, остаток от деления на 12 равен 0)</td></tr>
<tr><td>Код:</td><td>github.com/chikirao/met_opt, папка L3</td></tr>
</table>

<h2>Цель работы</h2>
<p>Найти минимум функции при заданном ограничении методом множителей Лагранжа.
Проверить найденную точку, доказать, что минимум достигается именно в ней,
и сравнить ручное решение с программной проверкой.</p>

<h2>1. Постановка задачи</h2>
<p>Для варианта 12 нужно найти минимум функции при ограничении-равенстве:</p>
{m(fx, f, block=True)}
{m(2*x + y, sp.Integer(10), block=True)}
<p>Переменные x и y принимают любые действительные значения. Также нужно выяснить,
существует ли максимум.</p>

<h2>2. Метод и проверка регулярности</h2>
<p>Переношу ограничение в левую часть: {m(h, constraints[0], sp.Integer(0))}.
Строю функцию L = f + λh со знаком плюс. Здесь λ является дополнительной неизвестной.
Приравниваю производные L по x и y к нулю и добавляю ограничение.
Получаю три уравнения для x, y и λ. Их решения пока являются только кандидатами:
нужно отдельно проверить, есть ли в них минимум или максимум.</p>
<p>Работать можно только с точками прямой 2x + y = 10. Такие точки существуют:
например, (0, 10), поскольку 2·0 + 10 - 10 = 0.
У f и h есть непрерывные производные. Градиент h, то есть пара её частных производных,
равен ∇h = (2, 1) и нигде не равен нулю. Это проверка регулярности:
для одного ограничения выполнено условие применимости метода Лагранжа.</p>

<h2>3. Функция Лагранжа и полная система</h2>
{m(L, res['L'], block=True)}
<p>Дифференцирую по всем трём неизвестным. Производная по λ возвращает ограничение:</p>
<div class="system">{system}</div>

<h2 class="pb">4. Ручное решение системы</h2>
<p>Из первого уравнения 2x + 2λ = 0 получаю x = -λ.
Из второго 2y + λ = 0 получаю y = -λ/2. Подставляю их в ограничение:</p>
<p style="text-align:center">2·(-λ) + (-λ/2) = 10.</p>
{m(-sp.Rational(5, 2)*lam, sp.Integer(10), block=True)}
{m(lam, sp.Integer(-4), block=True)}
<p>Тогда x = -(-4) = 4, y = -(-4)/2 = 2. При решении я делил только на числа 2 и 5,
которые не равны нулю, поэтому решения при делении не потерялись.
Для λ получилось одно значение, а x и y однозначно выражены через него.
Значит, других решений нет.</p>

<h3>Подстановка в исходные уравнения</h3>
<p>Ограничение: 2·4 + 2 - 10 = 0. Условия стационарности:
2·4 + 2·(-4) = 0 и 2·2 + (-4) = 0. Значение цели:</p>
{m(sp.Function('f')(4, 2), sp.Add(sp.Pow(4, 2, evaluate=False), sp.Pow(2, 2, evaluate=False), evaluate=False), sp.Integer(20), block=True)}
<p>Кандидат допустим. Самой подстановки недостаточно для вывода о минимуме,
поэтому исследую функцию на всей прямой.</p>

<h2>5. Проверка минимума и его глобальности</h2>
<p>Из ограничения y = 10 - 2x. Полагаю x = t, y = 10 - 2t,
где t принимает любые действительные значения. Так можно записать любую точку
прямой и получить функцию одной переменной:</p>
{m(phi, t**2 + (10 - 2*t)**2, 5*t**2 - 40*t + 100, block=True)}
{m(phi, 5*(t - 4)**2 + 20, block=True)}
<p>Квадрат неотрицателен при любом t. Поэтому φ(t) ≥ 20, причём равенство возможно
только при t = 4. Значит, в точке (4, 2) значение равно 20,
а в любой другой точке прямой оно больше 20. Поэтому минимум глобальный и единственный.
Проверка производными даёт φ′(t) = 10t - 40 и φ″(t) = 10 &gt; 0,
то есть кандидат также является строгим локальным минимумом.</p>
<p>При t → +∞ и t → -∞ значение φ(t) → +∞. Значит, на допустимой прямой
функция не ограничена сверху и глобального максимума нет.
Локальных максимумов тоже нет: у φ единственная стационарная точка,
и в ней достигается минимум.</p>
<div class="ans">Ответ: (x*, y*) = (4, 2), λ* = -4, f<sub>min</sub> = 20.
Максимума нет.</div>

<h2 class="pb">6. Геометрический смысл результата</h2>
<p>Цель f = x² + y² является квадратом расстояния до начала координат.
Поэтому требуется найти ближайшую к началу координат точку прямой 2x + y = 10.
Линии уровня цели являются окружностями с центром (0, 0). Наименьшая окружность,
имеющая общую точку с прямой, касается её в (4, 2), её радиус равен √20.</p>
<figure><img src="../img/variant12.png" alt="Линии уровня и функция на допустимой прямой">
<figcaption>Слева: прямая и линии уровня цели. Справа: φ(t) = 5(t - 4)² + 20.
Рисунок иллюстрирует аналитический результат.</figcaption></figure>
<p>В точке (4, 2) градиент цели ∇f = (8, 4) сонаправлен с ∇h = (2, 1).
Первый вектор в четыре раза больше второго. Условие Лагранжа выполняется:
∇f + λ∇h = (8, 4) + (-4)·(2, 1) = (0, 0).
Градиенты перпендикулярны соответствующим линиям уровня. В точке касания
у окружности и прямой одна и та же нормаль, поэтому градиенты параллельны.</p>

<h3>Смысл множителя Лагранжа</h3>
<p>Чтобы интерпретировать λ, заменяю правую часть ограничения 10 на параметр b:
2x + y = b. Та же система даёт x*(b) = 2b/5, y*(b) = b/5 и λ*(b) = -2b/5.</p>
{m(sp.Function('V')(b), b**2/5, block=True)}
<p>V(b) обозначает минимальное значение функции при правой части b.
Производная V′(b) = 2b/5 показывает, как быстро меняется этот минимум при изменении b.
При b = 10 она равна 4, то есть -λ*. Если немного увеличить правую часть на Δb,
минимум увеличится приблизительно на 4Δb. Здесь λ описывает чувствительность
ответа к изменению ограничения. Знак минус в V′(b) = -λ*(b) получается из выбранной
записи L = f + λ(2x + y - b). Для ограничения-равенства λ может быть отрицательным.</p>

<section class="program pb">
<h2>7. Программная проверка</h2>
<p>Проверку выполнил на Python с SymPy {sp.__version__}. В <code>lagrange.py</code>
функция <code>solve</code> строит L, вычисляет производные, решает систему через
<code>sympy.solve</code> и проверяет действительные корни подстановкой.
В <code>main.py</code> заданы исходные f и h. Ответ вычисляется из системы.</p>
<p>Ключевой фрагмент расчёта (полные исходники приложены):</p>
<pre>{html.escape(code)}</pre>
<p>Запуск: <code>python -m pip install -r requirements.txt</code>,
затем <code>python main.py</code> из папки L3. Часть фактического вывода:</p>
<pre>{html.escape(excerpt)}</pre>
<p>Невязка получается подстановкой найденного решения в левую часть уравнения,
записанного с нулём справа. Все невязки равны нулю: уравнения выполняются точно,
без округлений.
Полный вывод сохранён в <code>output.txt</code>. Программа также строит функцию
на прямой, вычисляет её производные и пределы при t → ±∞.</p>

<h3>Сравнение ручного и программного решения</h3>
<table class="cmp">
<tr><th>Способ</th><th>x</th><th>y</th><th>λ</th><th>f</th><th>h</th><th>(∂L/∂x, ∂L/∂y)</th></tr>
<tr><td>Вручную</td><td>4</td><td>2</td><td>-4</td><td>20</td><td>0</td><td>(0, 0)</td></tr>
<tr><td>SymPy</td>{program_row}</tr></table>

<h2>Выводы по работе</h2>
<p>Методом множителей Лагранжа я получил x = 4, y = 2 и λ = -4.
Проверил, что эта точка лежит на прямой 2x + y = 10.
После подстановки y = 10 - 2x получилось f = 5(x - 4)² + 20:
меньше 20 функция на прямой быть не может, а сверху её значения не ограничены.
Поэтому найден единственный глобальный минимум 20, максимума нет.
Расчёт в SymPy дал те же значения. Решение системы Лагранжа помогло найти точку,
а выделение квадрата доказало, что в ней действительно минимум.</p>
</section>
</body></html>'''


def run():
    (BASE / "report").mkdir(exist_ok=True)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        main()
    output = buffer.getvalue()
    (BASE / "output.txt").write_text(output, encoding="utf-8")
    path = BASE / "report/report.html"
    path.write_text(build(output), encoding="utf-8")
    if not EDGE.exists():
        raise SystemExit("Microsoft Edge не найден. HTML сохранён в report/report.html")
    with tempfile.TemporaryDirectory(prefix="edge-lab3-") as profile:
        subprocess.run([
            str(EDGE), "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={profile}", "--virtual-time-budget=3000",
            "--allow-file-access-from-files", f"--print-to-pdf={PDF}", str(path),
        ], check=True, capture_output=True, timeout=60)
    if not PDF.exists() or PDF.stat().st_size == 0:
        raise SystemExit("Edge не создал PDF")
    print(PDF)


if __name__ == "__main__":
    run()
