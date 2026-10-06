"""Симплекс-метод с искусственным базисом (двухэтапный).

Таблица хранится так же, как на бумаге:
    сверху номера свободных переменных, слева номера базисных,
    в середине матрица A, справа столбец b,
    внизу коэффициенты цели при свободных (c) и в углу -Q.

Все числа - Fraction, чтобы 1/3 оставалась 1/3.
"""

from fractions import Fraction


def fmt(v):
    """Дробь в строку: 5, -1/3."""
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


class Table:
    def __init__(self, cols, rows, A, b, c, mQ):
        self.cols = cols  # номера свободных переменных (столбцы)
        self.rows = rows  # номера базисных переменных (строки)
        self.A = A
        self.b = b
        self.c = c  # нижняя строка
        self.mQ = mQ  # правый нижний угол, равен -Q

    def show(self, pivot=None):
        w = 7
        line = " " * 5 + "".join(f"{'x' + str(j):>{w}}" for j in self.cols) + f"{'b':>{w}}"
        out = [line]
        for i, r in enumerate(self.rows):
            cells = "".join(f"{fmt(a):>{w}}" for a in self.A[i])
            mark = ""
            if pivot and pivot[0] == i:
                mark = f"   <- выходит x{r}"
            out.append(f"{'x' + str(r):>5}" + cells + f"{fmt(self.b[i]):>{w}}" + mark)
        out.append(f"{'c':>5}" + "".join(f"{fmt(v):>{w}}" for v in self.c) + f"{fmt(self.mQ):>{w}}")
        if pivot:
            i, j = pivot
            out.append(f"     входит x{self.cols[j]}, разрешающий элемент {fmt(self.A[i][j])}")
        return "\n".join(out)


def canon(c, A, signs, b, sense):
    """Приводит задачу к каноническому виду.

    sense: 'min' или 'max'. Для max цель умножается на -1.
    signs: '<=', '=', '>=' для каждой строки.
    Возвращает (c, A, b, n, slack) где n - число исходных переменных,
    slack[i] - номер добавленной переменной в строке i и её знак (+1/-1) или None.
    """
    c = [Fraction(v) for v in c]
    if sense == "max":
        c = [-v for v in c]
    A = [[Fraction(v) for v in row] for row in A]
    b = [Fraction(v) for v in b]
    signs = list(signs)
    n = len(c)

    # правая часть должна быть >= 0
    flip = {"<=": ">=", ">=": "<=", "=": "="}
    for i in range(len(A)):
        if b[i] < 0:
            A[i] = [-v for v in A[i]]
            b[i] = -b[i]
            signs[i] = flip[signs[i]]

    slack = []
    k = n
    for i, s in enumerate(signs):
        if s == "=":
            slack.append(None)
            continue
        k += 1
        sign = 1 if s == "<=" else -1
        for r in range(len(A)):
            A[r].append(Fraction(sign) if r == i else Fraction(0))
        c.append(Fraction(0))
        slack.append((k, sign))
    return c, A, b, n, slack


def start_aux(A, b, slack):
    """Вспомогательная задача.

    Строки с остатком "+1" (из "<=") уже имеют свою базисную переменную.
    В остальные строки добавляем искусственные переменные.
    Wa = сумма искусственных, выраженная через свободные.
    """
    m, total = len(A), len(A[0])
    basis = []
    art = []
    k = total
    for i in range(m):
        if slack[i] and slack[i][1] == 1:
            basis.append(slack[i][0])
        else:
            k += 1
            basis.append(k)
            art.append(k)

    free = [j for j in range(1, total + 1) if j not in basis]
    T = Table(
        cols=free,
        rows=basis,
        A=[[A[i][j - 1] for j in free] for i in range(m)],
        b=b[:],
        c=[Fraction(0)] * len(free),
        mQ=Fraction(0),
    )
    # Wa = sum(x_art) = sum(b_i - sum a_ij x_j) по строкам с искусственной
    for i, r in enumerate(basis):
        if r in art:
            for j in range(len(free)):
                T.c[j] -= T.A[i][j]
            T.mQ -= T.b[i]
    return T, art


def choose(T):
    """Возвращает (строка, столбец) разрешающего элемента.

    Столбец: самый отрицательный c (при равенстве - меньший номер переменной).
    Строка: минимум b/a среди a > 0 (при равенстве - меньший номер переменной).
    None, None - оптимум; i=None, j - цель не ограничена.
    """
    neg = [j for j, v in enumerate(T.c) if v < 0]
    if not neg:
        return None, None
    j = min(neg, key=lambda j: (T.c[j], T.cols[j]))
    cand = [i for i in range(len(T.rows)) if T.A[i][j] > 0]
    if not cand:
        return None, j
    i = min(cand, key=lambda i: (T.b[i] / T.A[i][j], T.rows[i]))
    return i, j


def step(T, i, j):
    """Пересчёт таблицы по правилу прямоугольника."""
    p = T.A[i][j]
    m, n = len(T.rows), len(T.cols)
    A = [[Fraction(0)] * n for _ in range(m)]
    b = [Fraction(0)] * m
    c = [Fraction(0)] * n

    for r in range(m):
        for s in range(n):
            if r == i and s == j:
                A[r][s] = 1 / p
            elif r == i:
                A[r][s] = T.A[i][s] / p
            elif s == j:
                A[r][s] = -T.A[r][j] / p
            else:
                A[r][s] = T.A[r][s] - T.A[i][s] * T.A[r][j] / p
        b[r] = T.b[i] / p if r == i else T.b[r] - T.b[i] * T.A[r][j] / p
    for s in range(n):
        c[s] = -T.c[j] / p if s == j else T.c[s] - T.A[i][s] * T.c[j] / p
    mQ = T.mQ - T.b[i] * T.c[j] / p

    cols, rows = T.cols[:], T.rows[:]
    cols[j], rows[i] = rows[i], cols[j]
    return Table(cols, rows, A, b, c, mQ)


def drop(T, names):
    """Вычёркивает столбцы искусственных переменных, которые стали свободными."""
    keep = [s for s, v in enumerate(T.cols) if v not in names]
    return Table(
        [T.cols[s] for s in keep],
        T.rows[:],
        [[row[s] for s in keep] for row in T.A],
        T.b[:],
        [T.c[s] for s in keep],
        T.mQ,
    )


def phase(T, title, log, art=()):
    """Крутит шаги симплекса до остановки. Возвращает (таблица, статус)."""
    k = 0
    while True:
        i, j = choose(T)
        if j is None:
            log.append(f"{title}, таблица {k} (оптимум: в строке c нет отрицательных):\n{T.show()}")
            return T, "optimal"
        if i is None:
            log.append(f"{title}, таблица {k}:\n{T.show()}")
            log.append(f"В столбце x{T.cols[j]} нет положительных элементов: цель не ограничена.")
            return T, "unbounded"
        log.append(f"{title}, таблица {k}:\n{T.show(pivot=(i, j))}")
        T = step(T, i, j)
        gone = [v for v in T.cols if v in art]
        if gone:
            T = drop(T, gone)
            log.append(f"x{gone[0]} - искусственная, её столбец вычёркиваем.")
        k += 1


def to_main(T, c, art, log):
    """Переход к основной задаче: искусственные убраны, цель выражается через свободные."""
    # если искусственная осталась в базисе с нулём - выводим её
    for i, r in enumerate(T.rows):
        if r in art:
            j = next((s for s, v in enumerate(T.A[i]) if v != 0), None)
            if j is None:
                continue  # строка - линейная комбинация остальных
            log.append(f"x{r} осталась в базисе с нулём, выводим её через x{T.cols[j]}.")
            T = drop(step(T, i, j), [r])

    # W = sum c_j x_j, базисные x_r = b_r - sum a_rj x_j
    newc = [c[v - 1] for v in T.cols]
    Q = Fraction(0)
    for i, r in enumerate(T.rows):
        cr = c[r - 1]
        if cr == 0:
            continue
        Q += cr * T.b[i]
        for s in range(len(T.cols)):
            newc[s] -= cr * T.A[i][s]
    return Table(T.cols[:], T.rows[:], [row[:] for row in T.A], T.b[:], newc, -Q)


def read(T, total):
    """Точка из таблицы: свободные = 0, базисные = b."""
    x = [Fraction(0)] * total
    for i, r in enumerate(T.rows):
        if r <= total:
            x[r - 1] = T.b[i]
    return x


def solve(c, A, signs, b, sense="min"):
    """Полный путь решения. Возвращает словарь с ответом и журналом шагов."""
    log = []
    cc, AA, bb, n, slack = canon(c, A, signs, b, sense)
    total = len(cc)

    T, art = start_aux(AA, bb, slack)
    T, status = phase(T, "Вспомогательная задача", log, art)
    if -T.mQ != 0:
        log.append(f"Wa = {fmt(-T.mQ)} > 0: область допустимых решений пуста.")
        return {"status": "infeasible", "log": log}
    log.append("Wa = 0: допустимая точка найдена, переходим к основной задаче.")

    T = to_main(T, cc, art, log)
    T, status = phase(T, "Основная задача", log)
    if status == "unbounded":
        return {"status": "unbounded", "log": log}

    x = read(T, total)
    W = -T.mQ  # значение канонической цели (всегда min)
    Z = -W if sense == "max" else W
    alt = [T.cols[s] for s, v in enumerate(T.c) if v == 0]
    return {
        "status": "optimal",
        "x": x[:n],
        "x_full": x,
        "Z": Z,
        "alt": alt,
        "canon": (cc, AA, bb),
        "log": log,
    }
