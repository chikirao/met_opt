"""Вариант 12.

Z = 2x1 + 3x2 + x3 + 4x4 -> min
    x1 + 2x2 + x3       <= 7
         x2 + x3 + x4    = 5
    x1            + x4  >= 3
    x1, x2, x3, x4 >= 0
"""

from simplex import fmt, solve

c = [2, 3, 1, 4]
A = [
    [1, 2, 1, 0],
    [0, 1, 1, 1],
    [1, 0, 0, 1],
]
signs = ["<=", "=", ">="]
b = [7, 5, 3]
sense = "min"


def term(k, i, first):
    if k == 0:
        return ""
    sign = "-" if k < 0 else ("" if first else "+")
    k = abs(k)
    num = "" if k == 1 else fmt(k)
    return f"{' ' if not first else ''}{sign}{' ' if sign and not first else ''}{num}x{i}"


def expr(row):
    s, first = "", True
    for i, k in enumerate(row, 1):
        t = term(k, i, first)
        if t:
            s += t
            first = False
    return s


def main():
    print("Исходная задача:")
    print(f"  Z = {expr(c)} -> {sense}")
    for row, s, v in zip(A, signs, b):
        print(f"  {expr(row)} {s} {v}")
    print()

    res = solve(c, A, signs, b, sense)
    cc, AA, bb = res["canon"] if "canon" in res else (None, None, None)
    if cc:
        print("Канонический вид:")
        print(f"  W = {expr(cc)} -> min")
        for row, v in zip(AA, bb):
            print(f"  {expr(row)} = {fmt(v)}")
        print(f"  x1..x{len(cc)} >= 0")
        print()

    for entry in res["log"]:
        print(entry)
        print()

    if res["status"] != "optimal":
        print("Решений нет:", res["status"])
        return

    x, Z = res["x"], res["Z"]
    print("Ответ:")
    print("  x* = (" + ", ".join(fmt(v) for v in x) + ")")
    print(f"  Z(x*) = {fmt(Z)}")
    if res["alt"]:
        print("  в строке c есть нули при x" + ", x".join(map(str, res["alt"]))
              + ": оптимальных точек может быть несколько, значение Z то же")
    print()

    print("Проверка в исходных ограничениях:")
    ok = True
    for row, s, v in zip(A, signs, b):
        lhs = sum(a * xi for a, xi in zip(row, x))
        good = {"<=": lhs <= v, "=": lhs == v, ">=": lhs >= v}[s]
        ok &= good
        print(f"  {expr(row)} = {fmt(lhs)} {s} {v}  {'да' if good else 'НЕТ'}")
    print(f"  все x >= 0: {'да' if all(v >= 0 for v in x) else 'НЕТ'}")
    print(f"  Z = " + " + ".join(f"{k}*{fmt(v)}" for k, v in zip(c, x))
          + f" = {fmt(sum(k * v for k, v in zip(c, x)))}")


if __name__ == "__main__":
    main()
