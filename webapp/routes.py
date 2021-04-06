# import Flask to render web app
from flask import Flask
from flask import render_template, request, jsonify

from datetime import datetime

# import auxiliary functions
import sys
sys.path.insert(1, './')
from operaciones_geomap import *
import plotly

from webapp import app
#app = Flask(__name__)

# añadimos FileHandler y un ConsoleHandler par logs
import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler('app.log', 
                                   maxBytes=1024 * 1024 * 100, 
                                   backupCount=20)
console_handler = logging.StreamHandler(sys.stdout)
# nivel de log INFO para no saturar
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)


# cargamos la página principal
@app.route('/')
@app.route('/index')
def index():
    
    return render_template('master.html')


# cargamos la página con resultados
@app.route('/go')
def go():
    '''
    USAGE 
           Componemos los datos para mostrar los resultados.     
    OUTPUT
           Gráficos renderizados con plotly y demás información que 
           será mostrada en la página go.html 
           Si no se encuentra ninguna ubicación se llamará a la 
           página void.html                 
    '''
    # usuario para consultar la API
    user_name = 'jmiraal'

    # nombre de la ciudad
    city_name = request.args.get('query', '') 
    
    # limpiamos el nombre
    city_name = clean_name(city_name)
    
    # cambiamos espacios por '%20' par la query
    city_name_search = re.sub(' ', '%20', city_name)
    
    # obtener datos geográficos 
    data_geo = request_geo(city_name_search, user_name)
    df_data_geo = get_geographical_data(data_geo)
    # si hemos obtenido alguna localización nos quedamos con la primera
    elemento = 0
    if df_data_geo.shape[0] > 0:
        # si la primera localización tiene caja de coordenadas
        if df_data_geo.iloc[elemento]['bbox'] != '':
            # definimos un recuadro de coordenadas para 
            # la búsqueda de estaciones
            east = df_data_geo.iloc[elemento]['bbox']['east']
            south = df_data_geo.iloc[elemento]['bbox']['south']
            north = df_data_geo.iloc[elemento]['bbox']['north']
            west = df_data_geo.iloc[elemento]['bbox']['west']

            bbox =[north, south, east, west]
        else:
            # si no tiene caja de coordenadas usamos una por defecto
            # para que de todos modos se muestre el mapa
            bbox =[0, 0, 0, 0]
            
        # obetener datos meteorológicos de las estaciones
        data_meteo = request_meteo(bbox, user_name)
        df_data_meteo = get_weather_data(data_meteo)

        # representar el mapa
        fig = draw_weather_map(df_data_geo, df_data_meteo, elemento)
        
        graphs_str = fig.to_json()
        graphs_str = '[' + graphs_str + ']'
        graphs = json.loads(graphs_str)
    
        # codificamos el gráfico plotly en JSON
        ids = ["graph-0"]
        graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
       
        # si existe estacioens preparamos la tabla de estaciones para 
        # ser mostrada también eliminamos la últim fila con la media y las 
        # dos últimas columnas con las coordenadas
        if df_data_meteo.shape[0] > 1:
            columns_list = ['Date', 'Name', 'Temp.', 'Humid.', 
                            'Wind', 'Clouds', 'lat', 'lng']
            df_data_meteo.columns = columns_list
            table_html = df_data_meteo.iloc[:-1,:-2].to_html(classes='data', 
                                                             index = False)
            table_html = table_html.replace('table', 'table align="center"')
            
        else:
            # si no hay estacioenes mostramos un mensaje indicándolo
            table_html = '<h4 class="text-center">No se ha encontrado ninguna \
                                    estación.</h4>'
        
        # añadimos un registro al log con info de la consulta realizada
        now = datetime.now()
        ts = now.strftime("%d/%m/%Y %H:%M:%S")
        app.logger.info('%s %s %s %s %s CONSULTA REALIZADA\n%s',
                        ts,
                        request.remote_addr,
                        request.method,
                        request.scheme,
                        request.full_path,
                        city_name)
        
        # mostramos la página go.html con los resultados de la búsqueda
        return render_template('go.html', ids=ids, graphJSON=graphJSON, 
                                city_name=city_name,
                                wiki_link = df_data_geo.iloc[elemento]['wiki_link'],
                                tables=[table_html], 
                                titles=df_data_meteo.columns.values) 
                                        
    else:
        # si la búsqueda de localizaciones no ha dado resultado
        return render_template('void.html', 
                            message='No se ha encontrado ninguna localización.')    

