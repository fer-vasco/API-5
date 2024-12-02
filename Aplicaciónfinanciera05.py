import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf


def Descargar_datos(tickers, período, intervalo):
	"""
    Descarga valores de cierre de múltiples tickers con la API yfinance.

    Parameters:
    tickers (str): Los tickers de las compañías.
    período (int): El período de tiempo que se va a traer para los valores de close.
    intervalo (str): La granularidad de los datos.

    Returns:
    dataframe: Un dataframe con los valores de cierre para múltiples tickers
    """

	end_date = datetime.now().strftime('%Y-%m-%d')
	tickers = yf.Tickers(tickers)
	tickers_hist = tickers.history(period=período,interval=intervalo)
	df_close = tickers_hist['Close'].copy()

	return df_close



def Crear_recta(df_original, columna):
	"""
    Agrega una columna al df_close que representa una recta que pasa por el primer y último close de un ticker consultado (columna).
    Además calcula la variación porcentual entre el último close y el primero para el ticker consultado (columna).

    Parameters:
    df_original (dataframe): El dataframe de close incluyendo la columna con la recta.
    columna (str): Es el ticker que se quiere consultar. El df contiene múltiples tickers.

    Returns:
    dataframe: Un dataframe con los valores de cierre de múltiples tickers.
    float: La variación porcentual entre el último close y el primero.
    """

	primer_valor = df_original[columna].iloc[0]
	ultimo_valor = df_original[columna].iloc[-1]
	variación = round((ultimo_valor / primer_valor -1) * 100, 1)
	delta_y = ultimo_valor - primer_valor
	delta_x = len(df_original) - 1
	pendiente = delta_y / delta_x
	secuencia = list(range(0, len(df_original)))	

	df_con_recta = df_original.copy()
	df_con_recta['secuencia'] = secuencia
	df_con_recta['recta'] = primer_valor + df_con_recta['secuencia'] * pendiente
	df_con_recta.drop(columns=['secuencia'], inplace=True)
	
	return df_con_recta, variación



def Calcular_desvío(df, Col_A, desde, hasta):
	"""
    Calcula el desvío porcentual entre la curva de close de un ticker y una recta que pasa entre el primer y último close.
    Además calcula la varación porcentual entre el último close y el primero.

    Parameters:
    df (dataframe): El dataframe que contiene los valores de close para múltiples tickers.
    Col_A (str): Es el ticker que se quiere consultar. El df contiene múltiples tickers.
    desde: El primer valor del intervalo a calcular. Se indica como la cantidad de intervalos antes del último intervalo registrado en el df.
    hasta: El último valor del intervalo a calcular. Se indica como la cantidad de intervalos antes del último intervalo registrado en el df.

    Returns:
    dataframe: El mismo dataframe de input más una columna con los valores absolutos de los desvíos porcentuales.
    float: La suma de dos desvíos porcentuales.
    float: La variación porcentual entre el último close y el primero.
    """

	ult = len(df)
	i1 = ult-1 + desde
	i2 = ult + hasta
	df_ajust = df.iloc[i1:i2]
	
	df, variación = Crear_recta(df_ajust, Col_A)
	df['desvios'] = abs((df[Col_A] / df['recta']) - 1)
	desvío = df['desvios'].sum()
	desvío = round(df['desvios'].sum() * 100,1)

	return df, desvío, variación 



def Graficar_df(df_a_graficar, columna_1, columna_2, desvío, variación):
	"""
    Grafica dos líneas, la de close y la recta que pasa por el primero y el último close.
    En el título indica el valor de la variación total de close y el desvío porcencual de close sobre la recta.

    Parameters:
    df_a_graficar (dataframe): El dataframe que contiene los valores de close y la recta.
    columna_1 (str): La columna con los valores de close a graficar.
    columna_2 (str): La columna con la recta a graficar
    desvío (float): La suma de dos desvíos porcentuales.
    variación (float): La variación porcentual entre el último close y el primero.

    Returns:
	No devuelve nada, solo genera el gráfico.
    """

	df_a_graficar.plot(y=[columna_1, columna_2], kind='line')
	plt.xlabel('Índice')
	plt.ylabel('Close')
	plt.title(f'Close. Var./Desvío: {variación}%/{desvío}%')
	plt.legend(title='Legend')
	plt.grid()
	plt.show()



def Generar_resultados(df_close, ticker, período, intervalo, desde):
	"""
    Ejecuta la función Calcular_desvío y crea un diccionario con los valores de resultado.

    Parameters:
    df_close (dataframe): El dataframe que contiene los valores de close.
    ticker (str): El ticker que se quiere consultar.
    período (str): El período a analizar.
    intervalo (str): La granularidad de los datos.
    desde (int): El intervalo inicial del período a calcular. Se indica como la cantidad de períodos antes del último.

    Returns:
	resultado (diccionario): Devuelve un diccionario con el ticker, el intervalo, el valor desde, la variación y el desvío.
    """

	df, desvío, variación = Calcular_desvío(df_close, ticker, desde, 0)
	# Graficar_df(df, ticker, 'recta', desvío, variación)

	resultados = {
	'Ticker': ticker,
	'Intervalo': intervalo,
	'Desde': desde,
	'Variación': variación,
	'Desvío': desvío
	}

	return resultados



def Resultados_para_distintos_intervalos(tickers, período, intervalo, desde):
	"""
    Genera una lista con desvíos y variaciones del valor de close para un grupo de tickers en un determinado período.

    Parameters:
    tickers (str): El grupo de tickers que se quiere consultar.
    período (str): El período a analizar.
    intervalo (str): La granularidad de los datos.
    desde (int): El intervalo inicial del período a calcular. Se indica como la cantidad de períodos antes del último.

    Returns:
	lista: Devuelve una lista con desvíos y variaciones del valor de close para un grupo de tickers en un determinado período.
    """

	lista = []
	df_close = Descargar_datos(tickers, período=período, intervalo=intervalo)

	for ticker in tickers:
		resultados = Generar_resultados(df_close=df_close, ticker=ticker, período=período, intervalo=intervalo, desde=desde)
		lista.append(resultados)

	return lista



def y_market_cap(ticker):
	"""
    Descarga el valor de capitalización bursátil de un ticker determinado.
    Usa la API de yfinance

    Parameters:
    ticker (str): El ticker que se quiere consultar.

    Returns:
	float: Devuelve el valor de capitalización bursátil del ticker.
    """
	info = yf.Ticker(ticker).fast_info
	
	return info['market_cap']



def fetch_gainers(api_key): 
	"""
    Descarga los tickers que tuvieron mayor variación porcentual positiva en el último día.
    Usa la API de financialmodelingprep.

    Parameters:
    api_key (str): La clave de la API.

    Returns:
	dataframe: Devuelve un dataframe con el ticker, el nombre de la empresa, el cambio porcentual en close y el capital de la empresa.
	"""

	url = f'https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}'
	response = requests.get(url)
	gainers = response.json()

	df_empresas = pd.DataFrame()
	simbolos = []
	nombres = []
	cambios = []
	capitales = []
    
	for gainer in gainers:

	    simbolos.append(gainer['symbol'])
	    nombres.append(gainer['name'])
	    cambios.append(gainer['changesPercentage'])
	    capitales.append(y_market_cap(gainer['symbol']))
	    

	df_empresas = pd.DataFrame(list(zip(simbolos, nombres, cambios, capitales)),
	       columns =['Ticker', 'Empresa', 'Cambio', 'Capital'])

	df_empresas.sort_values(by=['Capital'], ascending=False, inplace=True)
	df_empresas['Capital'] = round(df_empresas['Capital']/1000000,1).astype('str') + ' M'
	df_empresas['Cambio'] = round(df_empresas['Cambio'],1).astype('str') + '%'
	df_empresas.set_index('Ticker', inplace=True)

	return df_empresas



def Transformar_dict_a_df(lista_de_diccionarios):
	"""
    Genera un dataframe a partir de una lista cuyos elementos son diccionarios.

    Parameters:
    diccionario (lista): Irónicamente el parámetro que se llama diccionario, es una lista.

    Returns:
	df_final: Devuelve un dataframe con los elementos de cada diccionario.
    """

	merged_dict = {}

	for d in lista_de_diccionarios:
	    for key, value in d.items():
	        if key not in merged_dict:
	            merged_dict[key] = []

	        merged_dict[key].append(value)


	df_final = pd.DataFrame(merged_dict)

	return df_final



def Parametros_de_visualizacion():
	"""
    Ajusta los parámetros de visualización de los elementos de pandas.
    Es para ver mejor los datos de los dataframes.
	"""
	pd.set_option('display.max_columns', None)
	pd.set_option('display.max_rows', None)
	pd.set_option('display.width', 1000)
	


def Generar_df_con_variaciones_y_desvíos(empresas, período, intervalo, desde, variación, desvío):
	"""
    Toma el df de tickers y le agrega la variación y desvío.

    Parameters:
    empresas (dataframe): El dataframe generado con los tickers que tuvieron la mayor variación.
    período (str): El período a analizar.
    intervalo (str): La granularidad de los datos.
    desde (int): El intervalo inicial del período a calcular. Se indica como la cantidad de períodos antes del último.
    variación (float): Es la varaición mínima que se va a usar para filtrar los resultados.
    desvío (float): Es el desvío mínimo que se va a usar para filtrar los resultados.

    Returns:
	df_para_app: Devuelve el dataframe que se va a mostrar en la app.
    """	

	tickers = [] 
	lista_resultados = []

	for ticker in empresas.index:
		tickers.append(ticker)

	try:
		lista_r = Resultados_para_distintos_intervalos(tickers=tickers, período=período, intervalo=intervalo, desde=desde)
		for resultado in lista_r:
			lista_resultados.append(resultado)

	except Exception as e:
		print(f"Ocurrió el siguiente error: {e}")


	df = Transformar_dict_a_df(lista_resultados)
	# print(df)


	merged_df = empresas.merge(df[['Ticker', 'Intervalo', 'Variación', 'Desvío']], left_index=True, right_on='Ticker', how='left')
	merged_df.set_index('Ticker', inplace=True)

	df_para_app = merged_df

	return df_para_app



# Inicio del programa
# ===================


# Primero se obtienen y calculan los datos.


Parametros_de_visualizacion()
api_key = 'BKewxsq6oAF5okFIZ5b84WGWGiy3kiOm'
empresas = fetch_gainers(api_key)
# print(empresas)

variación_min = 0
desvío_min = 30
período = '1mo'
intervalo = '1d'
cant_desde = -5


df_app = Generar_df_con_variaciones_y_desvíos(empresas=empresas, período=período, intervalo=intervalo, desde=cant_desde, variación=variación_min, desvío=desvío_min)
# print(df_app)


# Con los datos, se corre el proceso de presentación en la app.


clave = str(123)
st.title('🍁 Resultados v5.03')
text_input = st.text_input("Clave 👇", type="password")

if text_input:
    if str(text_input) == clave:

        corrida = datetime.now() - timedelta(hours=3)
        corrida = corrida.strftime('%d-%m-%y %H:%M')
        st.write(f'Actualización de datos:')
        st.write(corrida)
        st.dataframe(df_app)

    else:
        st.write("Clave incorrecta")
