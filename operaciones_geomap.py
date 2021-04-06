# hacer consultas y precesar el resultado json
import urllib.request, json
# aglutinar datos como dataframes
import pandas as pd
import numpy as np
# librerias de visualización
import plotly.graph_objects as go
import plotly.express as px
# para aplicar regular expresions
import re


def clean_name(name):
    '''
    USAGE: 
        Limpia el nombre de caracteres extraños.
    INPUT
        name (String): nombre que queremos limpiar
    OUTPUT
        name_clean (String): Nombre limpio
    ''' 
    name_clean = re.sub(r"[^a-z A-Z0-9]+", '', name)
    
    return name_clean
    

def request_geo(name, username):
    '''
    USAGE: 
        Ejecuta una consulta de información geográfica sobre 
        'http://api.geonames.org'.
        El texto a buscar se introducirá en la variable name.
        Se introduce también el usuario con el que queremos ejecutar la API.
    INPUT
        name (String): Nombre de la ciudad o ubicación.
        username (String): Usuario para la consulta.
    OUTPUT
        data (dict): Diccionario con 20 elementos con la información de la 
                     respuesta.
    ''' 
    
    # construimos la url de consulta con el nombre de la ubicación
    url_geo = 'http://api.geonames.org/searchJSON?q=' + \
               str(name) + \
               '&fuzzy=0.8&maxRows=20&startRow=0&lang=en&isNameRequired=true&' +\
               'style=FULL&username=' + \
               str(username)
    
    # ejecutamos la consulta
    response = urllib.request.urlopen(url_geo)
    # interpretamos el resultado json y lo reportamos
    data = json.loads(response.read())
    
    return data
    
    
def get_element(dictionary, element_name, element_type = 'str'):
    '''
    USAGE: 
        Busca una clave en un diccionario de entrada. Si encuetra ese valor lo 
        devolverá, si no, devuleve un '' si el element_type vale 'str' o un NaN
        si vale 'num'. 
    INPUT
        dictionary (dict): Diccionario en el que queremos realizar la búsqueda.
        element_name (String): Clave que queremos buscar.
        element_type (String): Tipo de dato esperado, string o numérico.
    OUTPUT
        element: Valor correspondiente a esa clave.
    '''   
    try:
        element = dictionary[element_name]
        if element_type == 'num' and element == '':
            element = np.NaN
    except:
        if element_type == 'num':
            element = np.NaN
        else:
            element = ''
    return element


def get_geographical_data(data):
    '''
    USAGE: 
        Obtiene información geográfica relevante de las distintas localizaciones 
        reportadas por 'http://api.geonames.org'.
        Recibirá el diccionario original de la consulta y devolverá un DataFrame 
        con tantas filas como localizaciones y tantas columnas como datos 
        reportados.
    INPUT
        data (dict): Diccionario obtenido tras consultar la API.
    OUTPUT
        df_geo (DataFrame): DataFrame con tantas filas como elementos en la 
                            lista contenida en 'geonames' y las siguientes 
                            columnas:
            - 'asciiName': Nombre completo de la ubicación.
            - 'bbox': Caja de coordenadas en la que se encuadra la ubicación.
            - 'adminName1': Información adicional de la ubicación. Ciudad en 
                            la que se encuentra, si la ubicación original no 
                            fuese una ciudad.
            - 'countryName': País de la ubicación.
            - 'score': Similitud o probabilidad de la ubicación en referencia 
                       al nombre buscado.
            - 'lat': Latitud central de la ubicación.
            - 'lng': Longitud central de la ubicación.
            - 'wiki_link': Enlace de wikipedia en el caso de que exista.
    '''
    
    # definimos un DataFrame vacío con los campos que vamos a reportar.
    columns_list = ['asciiName', 'bbox', 'adminName1', 'countryName', 
                    'score', 'lat', 'lng', 'wiki_link']
    df_geo = pd.DataFrame(columns = columns_list)
    
    # convertimos el diccionario de entrada a DataFrame e iteramos a lo largo 
    # de sus filas.
    df_geo_search = pd.DataFrame(data)
    
    for index, row in df_geo_search.iterrows():
        
        # obtenemos el enlace de Wikipedia si existe. Necesitamos extraerlo 
        # a parte porque se encuentra a su vez contenido en una lista de 
        # diccionarios incluida en la clave 'alternateNames'.
        try:
            wiki_link = next(item['name'] 
                             for item in row['geonames']['alternateNames'] 
                             if item['lang'] == 'link')
        except:
            wiki_link = ''
        
        # creamos una serie con los datos obtenidos del diccionario para 
        # cada ubicación. 
        new_row = pd.Series({'asciiName': get_element(row['geonames'], 
                                                      'asciiName'), 
                             'bbox': get_element(row['geonames'], 
                                                 'bbox'), 
                             'adminName1': get_element(row['geonames'], 
                                                       'adminName1'),
                             'countryName': get_element(row['geonames'], 
                                                        'countryName'),
                             'score': get_element(row['geonames'], 
                                                  'score'),
                             'lat': get_element(row['geonames'], 
                                                'lat'),
                             'lng': get_element(row['geonames'], 
                                                'lng'),
                             'wiki_link': wiki_link
                            })
        # añadimos la serie al DataFrame inicial df_geo
        df_geo = df_geo.append(new_row, ignore_index=True)
    # ordenamos por score por si no se hubiese reportado ordenado previamente
    df_geo = df_geo.sort_values(by=['score'], ascending=False)
    return df_geo
    
    
def request_meteo(bbox, username):
    '''
    USAGE: 
        Ejecuta una consulta de información meteorológica sobre 
        'http://api.geonames.org'.
        Introduciremos una lista 'bbox' con cuatro valores de cooredenadas que 
        delimitarán un recuadro sobre el que buscar las estaciones 
        meteorológicas cuyos datos queremos obtener.
        Nos devolverá un diccionario con el resultado de la consulta
    INPUT
        bbox (list): Lista con cuatro coordenadas [north, south, east, west]
                     que delimitarán una caja:
                     
            -north: latitud superior de la caja.
            -south: latitud inferior de la caja.
            -east: longitud oriental de la caja.
            -west: longitud occidental de la caja.
                     
        username (String): Usuario para la consulta.
    OUTPUT
        data (dict): Diccionario con la información de las estaciones 
                     meteorológicas contenidas dentro de la caja.
    ''' 
    
    # construimos la url utilizando el usuario y los límites de la caja
    url_weather = "http://api.geonames.org/weatherJSON?north=" + str(bbox[0]) +\
                  "&south=" + str(bbox[1]) + \
                  "&east=" + str(bbox[2]) + \
                  "&west=" + str(bbox[3]) + \
                  "&username=" + username
    
    # ejecutamos la consulta
    response = urllib.request.urlopen(url_weather)
    # interpretamos el resultado json y lo reportamos
    data = json.loads(response.read())
    
    return data


def get_weather_data(data):
    '''
    USAGE: 
        Obtiene información meteorológica relevante de estaciones meteorológicas 
        en 'http://api.geonames.org'.
        Recibirá el diccionario original de la consulta y devolverá un DataFrame 
        con tantas filas como estaciones y tantas columnas como datos reportados
        Al final del dataframe se añade una fila más con la media de todas las 
        estaciones para los valores numéricos.
    INPUT
        data (dict): Diccionario obtenido tras consultar a la API.
    OUTPUT
        df_geo (DataFrame): DataFrame con tantas filas como estaciones 
                            reportadas y con las siguientes columnas:

             - 'datetime': Nombre completo de la ubicación.
             - 'stationName': Caja de coordenadas en la que se encuadra la 
                              ubicación.
             - 'temperature': Información adicional de la ubicación. Ciudad en 
                              la que se encuentra, si la ubicación original no 
                              fuese una ciudad.
             - 'humidity': País de la ubicación.
             - 'windSpeed': Similitud o probabilidad de la ubicación en 
                            referencia al nombre buscado.
             - 'clouds': Latitud central de la ubicación.
             - 'lat': Longitud central de la ubicación.
             - 'lng': Enlace de wikipedia en el caso de que exista.
             
             Al final del dataframe se añade una fila más con la media de todas 
             las estaciones.
    '''
    # iniciamos un dataframe vacío para almacenar los resultados
    columns_list = ['datetime', 'stationName', 'temperature', 'humidity', 
                    'windSpeed', 'clouds', 'lat', 'lng']
    df_meteo = pd.DataFrame(columns = columns_list)
    # convertimos el diccionario de entrada a DataFrame e iteramos a lo largo de 
    # sus filas.
    df_meteo_aux = pd.DataFrame(data)
    
    for index, row in df_meteo_aux.iterrows():
        # en cada fila creamos una Serie con los datos relevantes de cada 
        # estación
        new_row = pd.Series({'datetime': 
                             get_element(row['weatherObservations'], 
                                                     'datetime'), 
                             'stationName': 
                             get_element(row['weatherObservations'], 
                                                        'stationName'), 
                             'temperature': 
                             float(get_element(row['weatherObservations'], 
                                                              'temperature', 'num')),
                             'humidity': 
                             float(get_element(row['weatherObservations'], 
                                                           'humidity', 'num')),
                             'windSpeed': 
                             float(get_element(row['weatherObservations'], 
                                                            'windSpeed', 'num')),
                             'clouds': 
                             get_element(row['weatherObservations'], 
                                                   'clouds'),
                             'lat': 
                             get_element(row['weatherObservations'], 
                                                'lat'),
                             'lng': 
                             get_element(row['weatherObservations'], 
                                                'lng')
                            })
        
        # añadimos la serie al dataframe resultado
        df_meteo = df_meteo.append(new_row, ignore_index=True)
    
    # finalmente añadimos una fila más con la media de las columnas numéricas
    # y la añadimos también al resultado
    new_row = pd.Series({'datetime': '', 
                          'stationName': '', 
                          'temperature': 
                          round(np.mean(df_meteo['temperature'].dropna()), 1),
                          'humidity': 
                          round(np.mean(df_meteo['humidity'].dropna()), 1),
                          'windSpeed': 
                          round(np.mean(df_meteo['windSpeed'].dropna()), 1),
                          'clouds': '',
                          'lat': '',
                          'lng': ''
                         })
    df_meteo = df_meteo.append(new_row, ignore_index=True)

    return df_meteo
    
    
class Figure_Custom(go.Figure):
    ''' 
    Extensión de la clase plotly.graph_objects.Figure a la que se añade una
    nueva función, 'draw_termometer', para definir una barra de colores vertical 
    a la derecha de la figura a modo de termómetro.
    
    ATTRIBUTES:
        No se ha añadido ningún atributo nuevo.
            
    '''
    
    def __init__(self):
        go.Figure.__init__(self)
    
    
    def draw_termometer(self, temperature, text_info):
        '''
        USAGE: 
            Añade un termómetro en el lado derecho de la figura. 
            Este termómetro se consigue apilando 10 cajas de colores siguiendo 
            una escala del azul al rojo hasta llegar a la temperatura indicada 
            en los parámetros de la función. Además se representa una línea roja 
            señalando la temperatura exacata y al lado de la línea se añade una 
            anotación con la información recibida en 'text_info'. El rango de 
            temperaturas del termómetro irá de -15ºC a 45ºC. Cada caja de color 
            representará 60/10=6 grados.
        INPUT
            temperature (Float): Valor de la temperatura que queremos 
                                 representar. 
            text_info (String): Texto que queremos mostrar al lado de la 
                                temperatura.
        OUTPUT
            No devuelve ningún parámetro.
        ''' 
        
        # como solo representamos entre -15 y 45 tenemos que acotar la 
        # visualización si el valor de temperatura está fuera de estos márgenes.
        # Esto se podría modificar.
        if temperature >= 45:
            temp_position = 45
        elif temperature <= -15:
            temp_position = -15
        else:
            temp_position = temperature
        
        # número de cajas de colores que debemos apilar.
        # (temp-(-15))/6   (seis grados por caja)
        steps_temp = (temp_position + 15) / 6
        steps_temp = int(np.ceil(steps_temp))
        # de 0 a 10
        for i in range(11):
            # si i < steps_temp asignamos un color de  RdYlBu_r
            # si i >= steps_temp el color de la caja será blanco
            if i < steps_temp:
                color = px.colors.diverging.RdYlBu_r[i]
            else:
                color = 'white'
            
            # pintamos sólo 10 cajas
            if i < 10:
                self.add_shape(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0.92,
                    # 0.09% altura de la imagen cada caja
                    y0=0.09*i,
                    x1=0.96,
                    y1=0.09*(i+1),
                    line=dict(
                        color=color,
                        width=2,
                     ),
                    fillcolor=color,
                 )
            # necesitamos pintar 11 anotaciones de temperatura cada 6ºC.
            # primera y última incluidas. Por eso usamos range(11) para 
            # el for e if i<10 para las cajas 
            self.add_annotation(
                xref="paper",
                yref="paper",
                x=1,
                y=0.09*i,
                font=dict(
                    color='darkblue'
                ),
                showarrow=False,
                text=str(-15+i*6)+' ºC'
             )
        
        # añadimos una etiqueta con la palabra temperatura
        # encima de la barra
        self.add_annotation(
            xref="paper",
            yref="paper",
            x=1,
            y=0.95,
            font=dict(
                color='darkblue'
            ),
            showarrow=False,
            text='Temperatura'
        )

        # añadimos una lína roja en la temperatura exacta
        self.add_shape(
            type="line",
            xref="paper",
            yref="paper",
            x0=0.92,
            # (temp-(-15ºC)/rango_total_temp*0.9%  (el termómetro ocupa el 90%
            # de la altura de la imagen)
            y0=(temp_position + 15) / 60 * 0.9,
            x1=0.96,
            y1=(temp_position + 15) / 60 * 0.9,
            line=dict(
                color='red',
                width=2,
            ),
        )
        
        # añadimos la anotación indicada en el parámetro 'text_info' con los
        # datos medios de las estaciones.
        # movemos el anchor para que la anotación se vea siempre dentro
        # de los márgenes de la imagen.
        if temp_position > 40:
            anchor = "top"
        elif temp_position < -10:
            anchor = "botton"
        else:
            anchor = "middle"
            
        x_pos = 0.92
        y_pos = (temp_position + 15) / 60 * 0.9
            
        self.add_annotation(
            xref="paper",
            yref="paper",
            x=x_pos,
            y=y_pos,           
            font=dict(
                color='white'
            ),
            arrowcolor="royalblue",
            showarrow=True,
            align="left",
            xanchor="right",
            yanchor=anchor,
            bgcolor="royalblue",
            bordercolor="white",
            text=text_info
        )


def add_markers(fig, lat_list, long_list, text_list, size, color):   
    '''
    USAGE: 
        Añade una capa de marcadores Scattermapbox a la figura 'fig'. 
        Recibe además tres listas con las latitudes, longitudes y texto a 
        mostrar en cada marcador. Se indicará también el tamaño y el color 
        de los marcadores.
    INPUT
        fig (plotly.graph_objects.Figure): Figura sobre la que queremos 
                                           representar los marcadores. 
        lat_list (list): Lista de latitudes.
        lng_list (list): Lista de longitudes.
        text_list (list): Lista de textos.
        size (int): Tamaño de los marcadores.
        color (String): Color de los marcadores.
        
    OUTPUT
        No devuelve ningún parámetro.
    '''
    fig.add_trace(
        go.Scattermapbox(
            # la latitud y la longitud serán las listas obtenidas antes excepto 
            # el último valor, que en el dataframe original se corresponde 
            # con el valor medio de todas las estaciones.
            lat=lat_list,
            lon=long_list,
            mode='markers+text',
            textposition='top right',
            marker=go.scattermapbox.Marker(
                color= color,
                size=size
            ),
            textfont=dict(
                family="sans serif",
                size=18,
                color="LightSeaGreen"
            ),
            # componemos el texto que se mostrará al pasar el raton por los 
            # marcadores. Usaremos las listas generadas al principio de la 
            # función excepto el últmo valor, que representa la media de las 
            # estaciones.
            text=text_list,
            hoverinfo='text',
            subplot='mapbox'
        )
    
    )
    
    
def draw_weather_map(df_data_geo, df_data_meteo, elemento):
    '''
    USAGE: 
        Genera una figura en plotly centrada en la localización almacenada 
        en los campos lat y lng de la línea 'elemento' de df_geo_data. 
        Representa con puntos verdes las estaciones almacenadas en 
        df_data_meteo. 
        Para cada estación muestra la temperatura, la velocidad del viento y la 
        humedad. 
        Representa además con un punto azul el centro de la localización con 
        los valores medios de esos parámtros.
        En el margen derecho se representa un termómetro con el nivel alcanzado 
        por la temperatura media. Junto a este nivel se representa también una 
        anotación con los valores medios de temperatura, humedad y velocidad del 
        viento.
    INPUT
        df_geo_data (DataFrame): Dataframe con información geográfica generado 
                                 en 'get_geographical_data'. 
        df_data_meteo (DataFrame): Dataframe con información meteorológica 
                                   generado en 'get_weather_data'.
    OUTPUT
        fig (plotly.graph_objects.Figure): Figura con la composición explicada 
                                           en 'USAGE' lista para ser mostrada.
    ''' 
        

    # inicializamos la clase Figure_Custom
    fig = Figure_Custom()
    
    # generamos cuatro listas con los nombres y valores de temperatura, humedad 
    # y viento para todas las estaciones
    name = list(df_data_meteo['stationName'])
    temperature = list(df_data_meteo['temperature'])
    humidity = list(df_data_meteo['humidity'])
    windspeed = list(df_data_meteo['windSpeed'])
    
    # obtenemo también dos listas con los valores de latitud y longitud de las 
    # estaciones
    lat_est = list(df_data_meteo['lat'])
    lng_est = list(df_data_meteo['lng'])
    
    # valores de latitud y longitud para el punto central
    lat_central = float(df_data_geo.iloc[elemento]['lat'])
    long_central = float(df_data_geo.iloc[elemento]['lng'])
    
    # si hay información de temperatura disponible, añadimos el termómetro a la 
    # derecha además generamos el texto para mostrar en el termómetro y en el 
    # marcador central
    if np.isnan(temperature[-1]):
        text_info =  'No hay información <br> meteorológica disponible'
    else:
        text_info =str(df_data_geo.iloc[elemento]['asciiName']) + ' (Media)' + \
                 ':<br>Temp: ' + str(temperature[-1]) + ' ºC' + \
                 '<br>Humedad: ' + str(humidity[-1]) + ' %' + \
                 '<br>Viento: ' + str(windspeed[-1]) + ' knots'
        fig.draw_termometer(temperature[-1], text_info)
        
    
    # añadimos una capa Scattermapbox a la figura con el marcador 
    # central de color azul y tamaño 25. Utilizamos la función 'add_markers'. 
    # En este caso las listas sólo tienen un elemento.
    lat_aux=[lat_central]
    lon_aux=[long_central]
    color= 'royalblue'
    size = 25
    add_markers(fig, lat_aux, lon_aux, [text_info], size, color)
    
    # si existen estaciones meteorológicas añadimos la lista de marcadores de 
    # las estaciones en verde, para ello añadiremos otra capa Scattermapbox. 
    # Volvemos a llamar a la función add_markers con las listas de longitudes y 
    # latitudes de las estaciones, la lista con los textos que queremso mostrar, 
    # el color y el tamaño de los marcadores.
    if df_data_meteo.shape[0] > 1:
        lat_aux=lat_est[:-1]
        lon_aux=lng_est[:-1]
        text=[f'Estación: {x}<br>Temperatura: {y} ºC \
                <br>Humedad: {z} %<br>Viento: {w} knots' 
              for x,y,z,w in list(zip(name[:-1], 
                                      temperature[:-1], 
                                      humidity[:-1], 
                                      windspeed[:-1]))]
        color = 'lightgreen'
        size = 13
        add_markers(fig, lat_aux, lon_aux, text, size, color)
    
    # características generales de visualización: tipo  de mapa, punto central, 
    # zoom, título, etc.
    fig.update_layout(
        title={
            'text': df_data_geo.iloc[elemento]['asciiName'] + '<br>' +
                    df_data_geo.iloc[elemento]['adminName1'] + '/' +
                    df_data_geo.iloc[elemento]['countryName'],
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'auto',
            'font': {'color':'red'}
            },
        autosize=True,
        margin ={'l':0,'t':0,'b':0,'r':0},
        mapbox = {
            'style': "open-street-map",
            'center': {'lon': long_central, 'lat': lat_central},
            'zoom': 8
            },
        
        showlegend=False
    )
    return fig
    
    
    

    
    
    