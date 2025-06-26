import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import unicodedata
import holidays
import locale
import calendar
from datetime import datetime, timedelta
import argparse
import locale

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 

# === CONFIGURACIÓN ===
API_URL = "https://api.waiterio.com/api/v3/meals"
RESTAURANT_ID = "aee49d1fab0df0ab5e1644f7"

SMTP_SERVER = "vl54004.dns-privadas.es"
SMTP_PORT = 587
SMTP_USER = "info@hoteleriste.com"
SMTP_PASSWORD = "H3rist3"  # 🔒 Reemplaza por tu contraseña segura
DESTINATARIO = "info@hoteleriste.com"

eventos_especiales = {
    #Fiestas de Sahún
    "2023-06-23": "Fiestas Sahún 2023",
    "2023-06-24": "Fiestas Sahún 2023",
    "2024-06-22": "Fiestas Sahún 2024",
    "2024-06-23": "Fiestas Sahún 2024",
    "2024-06-24": "Fiestas Sahún 2024",
    "2025-06-21": "Fiestas Sahún 2025",
    "2025-06-22": "Fiestas Sahún 2025",
    "2025-06-23": "Fiestas Sahún 2025",
    "2025-06-24": "Fiestas Sahún 2025",
    #Fiestas de Eriste
    "2023-07-27": "Fiestas Eriste 2023",
    "2023-07-28": "Fiestas Eriste 2023",
    "2023-07-29": "Fiestas Eriste 2023",
    "2023-07-30": "Fiestas Eriste 2023",
    "2023-07-31": "Fiestas Eriste 2023",
    "2023-08-01": "Fiestas Eriste 2023",
    "2023-08-02": "Fiestas Eriste 2023",
    "2024-07-31": "Fiestas Eriste 2024",
    "2024-08-01": "Fiestas Eriste 2024",
    "2024-08-02": "Fiestas Eriste 2024",
    "2024-08-03": "Fiestas Eriste 2024",
    "2024-08-04": "Fiestas Eriste 2024",
    "2025-07-30": "Fiestas Eriste 2025",
    "2025-07-31": "Fiestas Eriste 2025",
    "2025-08-01": "Fiestas Eriste 2025",
    "2025-08-02": "Fiestas Eriste 2025",
    "2025-08-03": "Fiestas Eriste 2025",
    #Fiestas de Benasque
    "2023-06-28": "Fiestas Benasque 2023",
    "2023-06-28": "Fiestas Benasque 2023",
    "2023-06-29": "Fiestas Benasque 2023",
    "2023-07-01": "Fiestas Benasque 2023",
    "2023-07-02": "Fiestas Benasque 2023",
    "2024-06-27": "Fiestas Benasque 2024",
    "2024-06-28": "Fiestas Benasque 2024",
    "2024-06-29": "Fiestas Benasque 2024",
    "2024-06-30": "Fiestas Benasque 2024",
    "2024-07-01": "Fiestas Benasque 2024",
    "2025-06-27": "Fiestas Benasque 2025",
    "2025-06-28": "Fiestas Benasque 2025",
    "2025-06-29": "Fiestas Benasque 2025",
    "2025-06-30": "Fiestas Benasque 2025",
    "2025-07-01": "Fiestas Benasque 2025",
    #Torneo de Basquet Valle Escondido
    "2023-06-23": "Torneo Valle Escondido 2023",
    "2023-06-24": "Torneo Valle Escondido 2023",
    "2023-06-25": "Torneo Valle Escondido 2023",
    "2024-06-21": "Torneo Valle Escondido 2024",
    "2024-06-22": "Torneo Valle Escondido 2024",
    "2024-06-23": "Torneo Valle Escondido 2024",
    "2025-06-20": "Torneo Valle Escondido 2025",
    "2025-06-21": "Torneo Valle Escondido 2025",
    "2025-06-22": "Torneo Valle Escondido 2025",
    #GTTAP
    "2023-07-20": "GTTAP 2023",
    "2023-07-21": "GTTAP 2023",
    "2023-07-22": "GTTAP 2023",
    "2023-07-23": "GTTAP 2023",
    "2024-07-18": "GTTAP 2024",
    "2024-07-19": "GTTAP 2024",
    "2024-07-20": "GTTAP 2024",
    "2024-07-21": "GTTAP 2024",
    "2025-07-17": "GTTAP 2025",
    "2025-07-18": "GTTAP 2025",
    "2025-07-19": "GTTAP 2025",
    "2025-07-20": "GTTAP 2025",
    #GMMB
    "2023-06-10": "GMMB 2023",
    "2024-06-08": "GMMB 2024",
    "2025-06-14": "GMMB 2025",
    #Pitaroy
    "2023-03-04": "Trofeo Pitarroy 2023",
    "2025-03-01": "Trofeo Pitarroy 2025"
}

# === FUNCIONES ===
##############################
# Obtener pedidos de waiterio
def get_meals(start, end):
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    params = {
        "restaurantId": RESTAURANT_ID,
        "startTime": start_ms,
        "endTime": end_ms
    }
    response = requests.get(API_URL, params=params)
    return response.json() if response.status_code == 200 else []


##############################
# Eliminar tildes para tratar menu y menú
def eliminar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def parse_meals(data):
    registros = []
    for meal in data:
        ts = meal.get("creationTime")
        if not ts:
            continue
        fecha_hora = datetime.fromtimestamp(ts / 1000)

        itemstamps = meal.get("itemstamps", {})
        for item_id, item in itemstamps.items():
            nombre = item.get("item", {}).get("name", "").lower()
            nombre_normalizado = eliminar_tildes(nombre.lower())
            if "menu" in nombre_normalizado:
                tipo = "comida" if 12 <= fecha_hora.hour < 17 else "cena"
                registros.append({
                    "fecha": fecha_hora.date(),
                    "hora": fecha_hora.time(),
                    "tipo": tipo,
                    "cantidad": item.get("quantity", 1)
                })
    return pd.DataFrame(registros)


def predecir(fecha, modelo_comidas, modelo_cenas, eventos_especiales, es_holidays, temp_max, precip_mm):
    dia_semana = fecha.weekday()
    mes = fecha.month
    festivo = 1 if fecha in es_holidays else 0
    evento = 1 if fecha.strftime("%Y-%m-%d") in eventos_especiales else 0

    entrada = pd.DataFrame([[dia_semana, mes, festivo, evento, temp_max, precip_mm]],
        columns=["día_semana", "mes", "festivo", "evento_especial", "temp_max", "precipitacion_mm"]
    )

    pred_com = int(modelo_comidas.predict(entrada)[0])
    pred_cen = int(modelo_cenas.predict(entrada)[0])
    return pred_com, pred_cen


def obtener_pronostico_tiempo(fechas, lat=42.597, lon=0.515):
    fecha_inicio = min(fechas).strftime("%Y-%m-%d")
    fecha_fin = max(fechas).strftime("%Y-%m-%d")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "Europe/Madrid",
        "start_date": fecha_inicio,
        "end_date": fecha_fin
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Error al obtener datos meteorológicos")

    datos = response.json()["daily"]
    tiempo_df = pd.DataFrame({
        "fecha": datos["time"],
        "temp_max": datos["temperature_2m_max"],
        "precipitacion_mm": datos["precipitation_sum"]
    })
    tiempo_df["fecha"] = pd.to_datetime(tiempo_df["fecha"])
    return tiempo_df

def obtener_tiempo_pasado(inicio, fin, latitud, longitud):
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "start_date": inicio.strftime("%Y-%m-%d"),
        "end_date": fin.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "Europe/Madrid"
    }
    response = requests.get(url, params=params)
    datos = response.json()["daily"]
    return pd.DataFrame({
        "fecha": pd.to_datetime(datos["time"]),
        "temp_max": datos["temperature_2m_max"],
        "precipitacion_mm": datos["precipitation_sum"]
    })

def enviar_email(resumen_df, pivot):
    from email.mime.text import MIMEText  # por si no lo tienes arriba
    import calendar

    # Convertir índice en columna, por si 'fecha' es el índice
    if "fecha" not in resumen_df.columns:
        resumen_df = resumen_df.reset_index()

    # Asegurar que "fecha" es columna
    if resumen_df.index.name == "fecha":
        resumen_df = resumen_df.reset_index()

    # Calcular percentiles de comidas y cenas a partir del histórico (pivot)
    comida_p33 = pivot["n_comidas"].quantile(0.40)
    comida_p66 = pivot["n_comidas"].quantile(0.70)
    cena_p33 = pivot["n_cenas"].quantile(0.40)
    cena_p66 = pivot["n_cenas"].quantile(0.70)

    # Función para pintar fondo según valor y percentiles
    def color_celda(valor, p33, p66):
        if valor <= p33:
            return "#c8e6c9"  # verde claro
        elif valor <= p66:
            return "#fff9c4"  # amarillo claro
        else:
            return "#ffcdd2"  # rojo claro

    # Construir HTML
    html = """
    <html><body>
    <p>Hola, aquí tienes la predicción de comidas y cenas para la próxima semana:</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; text-align: center;">
        <tr>
            <th>Día</th><th>Fecha</th><th>Comidas</th><th>Cenas</th>
        </tr>
    """

    for _, fila in resumen_df.iterrows():
        fecha = pd.to_datetime(fila["fecha"])
        dia_semana = calendar.day_name[fecha.weekday()]  # Ej: 'Monday'
        comidas = int(fila["Comidas"])
        cenas = int(fila["Cenas"])

        color_comida = color_celda(comidas, comida_p33, comida_p66)
        color_cena = color_celda(cenas, cena_p33, cena_p66)

        html += f"""
        <tr>
            <td>{dia_semana}</td>
            <td>{fecha.strftime('%d/%m/%Y')}</td>
            <td style="background-color: {color_comida};">{comidas}</td>
            <td style="background-color: {color_cena};">{cenas}</td>
        </tr>
        """

    html += "</table></body></html>"

    # Crear mensaje
    mensaje = MIMEMultipart("alternative")
    mensaje["From"] = SMTP_USER
    mensaje["To"] = DESTINATARIO
    mensaje["Subject"] = "📅 Predicción semanal de comidas y cenas - Hotel Eriste"
    mensaje.attach(MIMEText(html, "html"))

    # Enviar email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(mensaje)
        print("✅ Email enviado correctamente.")
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")





# === PROCESAMIENTO HISTÓRICO ===
inicio = datetime(2023, 3, 1)
#inicio = datetime(2025, 5, 1)
fin = datetime.today()
periodo = timedelta(days=31)

df_full = pd.DataFrame()
fecha_actual = inicio
while fecha_actual < fin:
    fecha_fin = min(fecha_actual + periodo, fin)
    print(f"Descargando desde {fecha_actual.date()} hasta {fecha_fin.date()}...")
    meals = get_meals(fecha_actual, fecha_fin)
    df_mes = parse_meals(meals)
    df_full = pd.concat([df_full, df_mes], ignore_index=True)
    fecha_actual = fecha_fin

resumen = df_full.groupby(["fecha", "tipo"]).agg({"cantidad": "sum"}).reset_index()
pivot = resumen.pivot(index="fecha", columns="tipo", values="cantidad").fillna(0)
pivot.columns = ["n_cenas" if c == "cena" else "n_comidas" for c in pivot.columns]

pivot["día_semana"] = pd.to_datetime(pivot.index).dayofweek
pivot["mes"] = pd.to_datetime(pivot.index).month

# Festivos de España - ajusta subdiv según tu comunidad, por ejemplo: 'AR' para Aragón
es_holidays = holidays.country_holidays('ES', subdiv='AR')

pivot["festivo"] = pivot.index.to_series().apply(lambda x: 1 if x in es_holidays else 0)

# eventos especiales
pivot["evento_especial"] = pivot.index.astype(str).map(lambda x: 1 if x in eventos_especiales else 0)

# Obtener datos meteorológicos históricos
tiempo_historico = obtener_tiempo_pasado(inicio, fin, latitud=42.63, longitud=0.51)

# Unir con el pivot
pivot = pivot.reset_index()  # Esto moverá 'fecha' del índice a columna
pivot["fecha"] = pd.to_datetime(pivot["fecha"])  # Convierte a datetime
pivot = pivot.merge(tiempo_historico, on="fecha", how="left")

X = pivot[["día_semana", "mes", "festivo", "evento_especial", "temp_max", "precipitacion_mm"]]
y_comidas = pivot["n_comidas"]
y_cenas = pivot["n_cenas"]

X_train, _, y_train_com, _ = train_test_split(X, y_comidas, test_size=0.2, random_state=42)
_, _, y_train_cen, _ = train_test_split(X, y_cenas, test_size=0.2, random_state=42)

modelo_comidas = RandomForestRegressor(random_state=42)
modelo_cenas = RandomForestRegressor(random_state=42)
modelo_comidas.fit(X_train, y_train_com)
modelo_cenas.fit(X_train, y_train_cen)

# === PREDICCIÓN DE LA SEMANA SIGUIENTE (lunes a domingo) ===
# Parámetro opcional: poner aquí una fecha como string 'YYYY-MM-DD' o dejar como None
parser = argparse.ArgumentParser(description="Predicción de comidas y cenas para una semana.")
parser.add_argument("--fecha_inicio", type=str, help="Fecha opcional de inicio en formato YYYY-MM-DD")
args = parser.parse_args()

fecha_inicio_str = args.fecha_inicio

if fecha_inicio_str:
    fecha_base = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
else:
    hoy = datetime.now().date()
    dias_hasta_lunes = (7 - hoy.weekday()) % 7
    fecha_base = hoy + timedelta(days=dias_hasta_lunes)

fechas_prediccion = [fecha_base  + timedelta(days=i) for i in range(7)]
#fechas_prediccion = [hoy + timedelta(days=i) for i in range(7)]
predicciones = []

tiempo_df = obtener_pronostico_tiempo(fechas_prediccion)

for fecha in fechas_prediccion:
    fila_tiempo = tiempo_df[tiempo_df["fecha"] == pd.to_datetime(fecha)]
    temp_max = fila_tiempo["temp_max"].values[0]
    precip_mm = fila_tiempo["precipitacion_mm"].values[0]

    comidas, cenas = predecir(datetime.combine(fecha, datetime.min.time()), modelo_comidas, modelo_cenas, eventos_especiales, es_holidays, temp_max, precip_mm)
    predicciones.append({"fecha": fecha.strftime("%Y-%m-%d"), "Comidas": comidas, "Cenas": cenas})

resumen_df = pd.DataFrame(predicciones)
resumen_df["Día"] = pd.to_datetime(resumen_df["fecha"]).dt.strftime("%A").str.capitalize()
resumen_df["Temp (°C)"] = tiempo_df["temp_max"].values
resumen_df["Lluvia (mm)"] = tiempo_df["precipitacion_mm"].values
resumen_df = resumen_df[["fecha", "Día", "Comidas", "Cenas", "Temp (°C)", "Lluvia (mm)"]]
#resumen_df = resumen_df[["fecha", "Comidas", "Cenas", "Día"]]

# === ENVÍO DE EMAIL ===
enviar_email(resumen_df, pivot)
#print(resumen_df.to_string(index=False))
