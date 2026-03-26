from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# 🔥 Formato dinero
def format_money(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value).replace(",", ".")
    except:
        return value

app.jinja_env.filters['money'] = format_money

# 🔥 Crear DB
def crear_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos_fijos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nombre TEXT,
        categoria TEXT,
        monto REAL,
        fecha_pago TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS presupuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        categoria TEXT,
        limite REAL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        email TEXT,
        password TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ingresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        categoria TEXT,
        monto REAL,
        descripcion TEXT,
        fecha TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        categoria TEXT,
        monto REAL,
        descripcion TEXT,
        fecha TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nombre TEXT,
        objetivo REAL,
        ahorro REAL DEFAULT 0
    )''')

    conn.commit()
    conn.close()

crear_db()

# 🔐 LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE email=?",
                       (request.form["email"],))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], request.form["password"]):
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")


# 📝 REGISTRO
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        password_hash = generate_password_hash(request.form["password"])

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO usuarios (nombre,email,password) VALUES (?,?,?)",
            (request.form["nombre"], request.form["email"], password_hash)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# 🏠 DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(monto) FROM ingresos WHERE usuario_id=?", (session["user_id"],))
    ingresos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM gastos WHERE usuario_id=?", (session["user_id"],))
    gastos = cursor.fetchone()[0] or 0

    balance = ingresos - gastos

    cursor.execute("""
    SELECT 'Ingreso', monto, descripcion, fecha FROM ingresos WHERE usuario_id=?
    UNION ALL
    SELECT 'Gasto', monto, descripcion, fecha FROM gastos WHERE usuario_id=?
    ORDER BY fecha DESC
    """, (session["user_id"], session["user_id"]))

    movimientos = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           ingresos=ingresos,
                           gastos=gastos,
                           balance=balance,
                           movimientos=movimientos)


# ➕ AGREGAR INGRESO
@app.route("/add_ingreso", methods=["POST"])
def add_ingreso():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO ingresos (usuario_id, categoria, monto, descripcion, fecha)
    VALUES (?, ?, ?, ?, date('now'))
    """, (
        session["user_id"],
        request.form["categoria"],
        float(request.form["monto"]),
        request.form["descripcion"]
    ))

    conn.commit()
    conn.close()
    return redirect("/dashboard")


# ➖ AGREGAR GASTO
@app.route("/add_gasto", methods=["POST"])
def add_gasto():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO gastos (usuario_id, categoria, monto, descripcion, fecha)
    VALUES (?, ?, ?, ?, date('now'))
    """, (
        session["user_id"],
        request.form["categoria"],
        float(request.form["monto"]),
        request.form["descripcion"]
    ))

    conn.commit()
    conn.close()
    return redirect("/dashboard")


@app.route("/gastos_fijos")
def gastos_fijos():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, categoria, monto, fecha_pago
        FROM gastos_fijos
        WHERE usuario_id=?
        ORDER BY fecha_pago
    """, (session["user_id"],))

    gastos = cursor.fetchall()

    from datetime import datetime

    alertas = []

    for g in gastos:
        fecha = datetime.strptime(g[4], "%Y-%m-%d")
        hoy = datetime.now()

        dias = (fecha - hoy).days

        if dias <= 3:
            alertas.append((g[1], dias))

    conn.close()

    return render_template("gastos_fijos.html", gastos=gastos, alertas=alertas)


@app.route("/add_gasto_fijo", methods=["POST"])
def add_gasto_fijo():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO gastos_fijos (usuario_id, nombre, categoria, monto, fecha_pago)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        request.form["nombre"],
        request.form["categoria"],
        float(request.form["monto"]),
        request.form["fecha_pago"]
    ))

    conn.commit()
    conn.close()

    return redirect("/gastos_fijos")

# 📊 GRÁFICAS
@app.route("/graficas")
def graficas():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(monto) FROM ingresos WHERE usuario_id=?", (session["user_id"],))
    ingresos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM gastos WHERE usuario_id=?", (session["user_id"],))
    gastos = cursor.fetchone()[0] or 0

    conn.close()

    return render_template("graficas.html", ingresos=ingresos, gastos=gastos)


# 🎯 METAS
@app.route("/metas")
def metas():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM metas WHERE usuario_id=?", (session["user_id"],))
    metas = cursor.fetchall()

    conn.close()

    return render_template("metas.html", metas=metas)


@app.route("/crear_meta", methods=["POST"])
def crear_meta():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO metas (usuario_id,nombre,objetivo) VALUES (?,?,?)",
        (session["user_id"], request.form["nombre"], float(request.form["objetivo"]))
    )

    conn.commit()
    conn.close()
    return redirect("/metas")


@app.route("/ahorrar", methods=["POST"])
def ahorrar():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE metas SET ahorro = ahorro + ? WHERE id=?",
        (float(request.form["monto"]), request.form["meta_id"])
    )

    conn.commit()
    conn.close()
    return redirect("/metas")

    # 📊 VER PRESUPUESTO
@app.route("/presupuesto")
def presupuesto():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    # Presupuestos
    cursor.execute("SELECT * FROM presupuestos WHERE usuario_id=?", (session["user_id"],))
    presupuestos = cursor.fetchall()

    data = []

    for p in presupuestos:
        categoria = p[2]
        limite = p[3]

        cursor.execute("""
        SELECT SUM(monto) FROM gastos 
        WHERE usuario_id=? AND categoria=?
        """, (session["user_id"], categoria))

        gastado = cursor.fetchone()[0] or 0

        data.append((categoria, limite, gastado))

    conn.close()

    return render_template("presupuesto.html", data=data)


# ➕ AGREGAR PRESUPUESTO
@app.route("/add_presupuesto", methods=["POST"])
def add_presupuesto():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO presupuestos (usuario_id, categoria, limite)
    VALUES (?, ?, ?)
    """, (
        session["user_id"],
        request.form["categoria"],
        float(request.form["limite"])
    ))

    conn.commit()
    conn.close()

    return redirect("/presupuesto")

#analisis avanzado
@app.route("/analisis")
def analisis():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    # INGRESOS
    cursor.execute("SELECT SUM(monto) FROM ingresos WHERE usuario_id=?", (session["user_id"],))
    ingresos = cursor.fetchone()[0] or 0

    # GASTOS
    cursor.execute("SELECT SUM(monto) FROM gastos WHERE usuario_id=?", (session["user_id"],))
    gastos = cursor.fetchone()[0] or 0

    balance = ingresos - gastos

    # GASTO POR CATEGORIA
    cursor.execute("""
        SELECT categoria, SUM(monto)
        FROM gastos
        WHERE usuario_id=?
        GROUP BY categoria
    """, (session["user_id"],))

    categorias = cursor.fetchall()

    top_categoria = None
    max_gasto = 0

    for c in categorias:
        if c[1] > max_gasto:
            max_gasto = c[1]
            top_categoria = c[0]

    # PORCENTAJE
    porcentaje_gasto = (gastos / ingresos * 100) if ingresos > 0 else 0

    # ESTADO
    if porcentaje_gasto < 50:
        estado = "Excelente"
        color = "success"
    elif porcentaje_gasto < 80:
        estado = "Estable"
        color = "warning"
    else:
        estado = "Riesgoso"
        color = "danger"

    # PREDICCIÓN
    cursor.execute("""
        SELECT fecha, monto FROM gastos
        WHERE usuario_id=?
        ORDER BY fecha
    """, (session["user_id"],))

    datos = cursor.fetchall()
    total_gastos = [d[1] for d in datos]

    prediccion = 0
    tendencia = "Estable"

    if len(total_gastos) >= 2:
        promedio = sum(total_gastos) / len(total_gastos)
        prediccion = promedio

        if total_gastos[-1] > total_gastos[0]:
            tendencia = "Subiendo 📈"
        elif total_gastos[-1] < total_gastos[0]:
            tendencia = "Bajando 📉"
    else:
        prediccion = sum(total_gastos) if total_gastos else 0

    # SCORE
    score = 100

    if porcentaje_gasto > 80:
        score -= 40
    elif porcentaje_gasto > 60:
        score -= 20

    if balance < 0:
        score -= 30

    if balance > 0:
        score += 10

    score = max(0, min(100, score))

    # NIVEL SCORE
    if score >= 80:
        nivel_score = "Excelente"
        color_score = "success"
    elif score >= 50:
        nivel_score = "Aceptable"
        color_score = "warning"
    else:
        nivel_score = "Crítico"
        color_score = "danger"

    conn.close()

    return render_template("analisis.html",
        ingresos=ingresos,
        gastos=gastos,
        balance=balance,
        top_categoria=top_categoria,
        max_gasto=max_gasto,
        porcentaje=porcentaje_gasto,
        estado=estado,
        color=color,
        prediccion=prediccion,
        tendencia=tendencia,
        score=score,
        nivel_score=nivel_score,
        color_score=color_score
    )

# 📄 REPORTES
@app.route("/reportes")
def reportes():
    return render_template("reportes.html")


@app.route("/exportar_pdf", methods=["GET","POST"])
def exportar_pdf():
    if request.method == "GET":
        return redirect("/reportes")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 'Ingreso', monto, descripcion, fecha FROM ingresos WHERE usuario_id=?
    UNION ALL
    SELECT 'Gasto', monto, descripcion, fecha FROM gastos WHERE usuario_id=?
    """, (session["user_id"], session["user_id"]))

    datos = cursor.fetchall()
    conn.close()

    doc = SimpleDocTemplate("reporte.pdf")
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Reporte Financiero", styles["Title"]))

    for d in datos:
        linea = f"{d[0]} - ${format_money(d[1])} - {d[2]} - {d[3]}"
        content.append(Paragraph(linea, styles["Normal"]))

    doc.build(content)

    return send_file("reporte.pdf", as_attachment=True)




# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)