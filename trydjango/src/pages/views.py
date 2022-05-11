from time import time
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from collections import defaultdict
from heapq import *
# import pandas as pd  #This is just for reading the csv.
import geopandas as gpds
from shapely.geometry import Point

from PIL import Image, ImageTk #pip install pillow
# from tkinter import messagebox
# from tkinter import *
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
import json

from plpygis import Geometry  ## encoded geometry için 
from shapely import wkt, geometry as sheplygeometry, ops ## yine encoded geometry için

import psycopg2
## Veritabanı bağlantısı

# Create your views here.
def index_view(request):
    # text = request.GET.get('button_text')

    if request.is_ajax():
        t = time()
        return JsonResponse({'seconds': t}, status=200)

    
    return render(request,"index.html",{})
    #return HttpResponse(template)

def SemtServisi(request):
    
    return render(request,"SemtServisi.html",{})

def showResult(request):
    
    baslangic = request.GET['baslangic']
    bitis = request.GET['bitis']
    total = baslangic +" "+ bitis

    User_type = request.GET.get('user_type')

    #########################################################################################

    ##  out = shortest_path(603,87, "Engelli")
    start = int(baslangic)
    end = int(bitis)
    user_type = User_type
    
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="159753",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="GIS_Project")
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from beytepe_roads_rev2;"
    
        cursor.execute(postgreSQL_select_Query)
    
    

    
    
    
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    
    ## Veritabanından pandas dataframe e geçiş
    sql_road = "select * from beytepe_roads_rev2;"
    sql_node = "select * from beytepenodesrev4;"
    sql_park = "select * from otopark;"
    
    roads = pd.read_sql_query(sql_road, connection)
    nodes = pd.read_sql_query(sql_node, connection)
    park = pd.read_sql_query(sql_park, connection)

    
    def dijkstra(edges, f, t):
        g = defaultdict(list)
        for l,r,c,road_id, GEOM, yol_turu in edges:
            g[l].append((c,r))

        q, seen, mins = [(0,f,())], set(), {f: 0}
        while q:
            (cost,v1,path) = heappop(q)
            if v1 not in seen:
                seen.add(v1)
                path = (v1, path)
                if v1 == t: return (cost,path) #if you want to see the path (cost, path)
    
                for c, v2 in g.get(v1, ()):
                    if v2 in seen: continue
                    prev = mins.get(v2, None)
                    next = cost + c
                    if prev is None or next < prev:
                        mins[v2] = next
                        heappush(q, (next, v2, path))

        return float("inf"), None

    
              
    

    
    sayac = [] # Başlangıçta yanlış düğüm girildiyse kodu hiç başlatmaması için
    for i in range (len(nodes.id)):
        alex3 = int(nodes.id.iloc[i])
        sayac.append(alex3)


    ## Otopark işlemleri 1
    otoparkList = []
    for i in range(len(park.nodeid)):

        if(park.doluluk[i] == True):
            otoparkList.append(park.nodeid[i])

    # otoparkList = [1028, 1659, 1609, 959, 942, 1699, 1697, 1183, 262, 335, 29, 1469, 822, 711, 688, 627, 256, 53, 319, 1679, 1213]
    otoparkX = []
    otoparkY = []
    for otoparkNode in otoparkList:
        otopark_X = (Geometry(nodes[nodes.id==otoparkNode]['geom'].values[0]).shapely.x)
        otopark_Y = (Geometry(nodes[nodes.id==otoparkNode]['geom'].values[0]).shapely.y)
        otoparkX.append(otopark_X)
        otoparkY.append(otopark_Y)

    
  
    start_int = start
    end_int = end
    
    start_str = str(start)
    end_str = str(end)

    ## Otopark işlemleri 2
    dest_X = (Geometry(nodes[nodes.id==end]['geom'].values[0]).shapely.x)
    dest_Y = (Geometry(nodes[nodes.id==end]['geom'].values[0]).shapely.y)
    
    otoparkIndex = 0
    currDistToPark = 99999999999999999999999999999999999999
    for oto in range(len(otoparkList)):
        distToPark = ((dest_X - otoparkX[oto])**2 + (dest_Y - otoparkY[oto])**2)**(1/2)
        
        if (distToPark < currDistToPark):
            currDistToPark = distToPark
            otoparkIndex = oto

        # currDistToPark = distToPark
    
    edges_distance = []
    edges_speed = []
        
    for i in range (len(roads.start_id)):
        EDGEID_str = str(roads.id.iloc[i])
        STARTID_str = str(roads.start_id.iloc[i])
        ENDID_str = str(roads.end_id.iloc[i])
        LENGTH_float = float(roads.yol_uzunlk.iloc[i])
        ID_int = int(roads.id.iloc[i])
        GEOM = Geometry(roads.geom.iloc[i]).shapely
        yol_turu = str(roads.yol_turu.iloc[i])
        yol_yonu = str(roads.yol_yonu.iloc[i])
        
        if (roads.hd1z_limit.iloc[i] == None):
            SPD_float = 5
        else:
            SPD_float = float(roads.hd1z_limit.iloc[i])
        
        Time = LENGTH_float/SPD_float # t = x/v
        edges_speed.append([STARTID_str, ENDID_str, Time])
        
        
        # yayaController = "1" ### def moduna geçtiğin için yazdın bunu inputlarda alman gerekecek.
        if (user_type == "Yaya"):
            edges_distance.append([ENDID_str, STARTID_str,  LENGTH_float, ID_int, GEOM, yol_turu]) ## Bütün yolları çift yönlü yapıyor
            edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])
            
        elif (user_type == "Bisikletli" or user_type == "Engelli"):
            if (yol_turu == "araba" or yol_turu == "yaya" or yol_turu == "engelli_rampası"):
                edges_distance.append([ENDID_str, STARTID_str,  LENGTH_float, ID_int, GEOM, yol_turu]) ## Bütün yolları çift yönlü yapıyor
                edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])
                
        elif (user_type == "Araba"):
            if (yol_turu == "araba" and yol_yonu == "tek_yon"):
                edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])
            elif (yol_turu == "araba" and yol_yonu == "cift_yon"):
                edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])
                edges_distance.append([ENDID_str, STARTID_str, LENGTH_float, ID_int, GEOM, yol_turu])
            elif (yol_turu == "araba" and yol_yonu == "ters_yon"):
                edges_distance.append([ENDID_str, STARTID_str, LENGTH_float, ID_int, GEOM, yol_turu])

            
        else:
            edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])


    if (start_int in sayac ) and ((end_int in sayac)) :
        
    

        if(user_type == "Araba"):
    
            # result1,result2 = (dijkstra (edges_distance , start_str, end_str))
            
            #otoparka giden kısım
            print(str(otoparkList[otoparkIndex]))
            result1,result2 = (dijkstra (edges_distance , start_str, str(otoparkList[otoparkIndex])))
    
            f = (str(result2).replace('(','').replace(')',''))
            t = (str(f).replace("'",'').replace("'",''))
            ints=[]
            g = t.split(",")
            for item in range(len(g) - 1):
                ints.append(int(g[item]))
            
            
            
            
            
            Lon_List = []
            Lat_List = []
            for k in range(len(nodes)):
    
    
                Lon_List.append(Geometry(nodes['geom'].iloc[k]).shapely.x)
                Lat_List.append(Geometry(nodes['geom'].iloc[k]).shapely.y)
            nodes['lon'] = Lon_List
            nodes['lat'] = Lat_List
    
            
            
            lat=[]
            lon=[]
            for item in ints:
                nodeslat=nodes[nodes.id==item]["lat"].values
                nodeslon=nodes[nodes.id==item]["lon"].values
                lat.append(nodeslat)
                lon.append(nodeslon)
                
    
            print(ints)
            road_IDS = []
            road_Multiline_List = []
            for i in range(len(ints)-1):
                flag = True
                road_index = 0
                startid = ints[i]
                endid = ints[i+1]
    
                while (flag):
                    road_index += 1
                    if((int(edges_distance[road_index][1]) == endid and int(edges_distance[road_index][0]) == startid) or (int(edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) ): #or int((edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) 
                        road_IDS.append(edges_distance[road_index][3])
                        
                        roadLineString = edges_distance[road_index][4][0]
    
                        road_Multiline_List.append(roadLineString)
                        
                        flag = False
            # print(road_IDS, "rota")
            # print(road_Multiline_List[0])
            
            otoMultiLine = sheplygeometry.MultiLineString(road_Multiline_List)
            
            
        
            
            ## otoparktan sonrası için önce veri sıfırlama sonrasında rotalama için.
            edges_distance = []
            
            for i in range (len(roads.start_id)):
                EDGEID_str = str(roads.id.iloc[i])
                STARTID_str = str(roads.start_id.iloc[i])
                ENDID_str = str(roads.end_id.iloc[i])
                LENGTH_float = float(roads.yol_uzunlk.iloc[i])
                ID_int = int(roads.id.iloc[i])
                GEOM = Geometry(roads.geom.iloc[i]).shapely
                yol_turu = str(roads.yol_turu.iloc[i])
                yol_yonu = str(roads.yol_yonu.iloc[i])
                
                edges_distance.append([ENDID_str, STARTID_str,  LENGTH_float, ID_int, GEOM, yol_turu]) ## Bütün yolları çift yönlü yapıyor
                edges_distance.append([STARTID_str, ENDID_str, LENGTH_float, ID_int, GEOM, yol_turu])


            result1,result2 = (dijkstra (edges_distance , str(otoparkList[otoparkIndex]), end_str))
    
            f = (str(result2).replace('(','').replace(')',''))
            t = (str(f).replace("'",'').replace("'",''))
            ints=[]
            g = t.split(",")
            for item in range(len(g) - 1):
                ints.append(int(g[item]))
            
            
            
            
            
            Lon_List = []
            Lat_List = []
            for k in range(len(nodes)):
    
    
                Lon_List.append(Geometry(nodes['geom'].iloc[k]).shapely.x)
                Lat_List.append(Geometry(nodes['geom'].iloc[k]).shapely.y)
            nodes['lon'] = Lon_List
            nodes['lat'] = Lat_List
    
            
            
            lat=[]
            lon=[]
            for item in ints:
                nodeslat=nodes[nodes.id==item]["lat"].values
                nodeslon=nodes[nodes.id==item]["lon"].values
                lat.append(nodeslat)
                lon.append(nodeslon)
                
    
            print(ints)
            road_IDS = []
            road_Multiline_List = []
            for i in range(len(ints)-1):
                flag = True
                road_index = 0
                startid = ints[i]
                endid = ints[i+1]
    
                while (flag):
                    road_index += 1
                    if((int(edges_distance[road_index][1]) == endid and int(edges_distance[road_index][0]) == startid) or (int(edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) ): #or int((edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) 
                        road_IDS.append(edges_distance[road_index][3])
                        
                        roadLineString = edges_distance[road_index][4][0]
    
                        road_Multiline_List.append(roadLineString)
                        
                        flag = False
            
            nextMultiLine = sheplygeometry.MultiLineString(road_Multiline_List)
            
        if (user_type == "Yaya"):
            
            otoMultiLine = "LINESTRING (0 0, 5 5, 10 10, 8.646 50.4654)"
            
            result1,result2 = (dijkstra (edges_distance , start_str, end_str))
    
            f = (str(result2).replace('(','').replace(')',''))
            t = (str(f).replace("'",'').replace("'",''))
            ints=[]
            g = t.split(",")
            for item in range(len(g) - 1):
                ints.append(int(g[item]))
            
            
            
            
            
            Lon_List = []
            Lat_List = []
            for k in range(len(nodes)):
    
    
                Lon_List.append(Geometry(nodes['geom'].iloc[k]).shapely.x)
                Lat_List.append(Geometry(nodes['geom'].iloc[k]).shapely.y)
            nodes['lon'] = Lon_List
            nodes['lat'] = Lat_List
    
            
            
            lat=[]
            lon=[]
            for item in ints:
                nodeslat=nodes[nodes.id==item]["lat"].values
                nodeslon=nodes[nodes.id==item]["lon"].values
                lat.append(nodeslat)
                lon.append(nodeslon)
                
    
            print(ints)
            road_IDS = []
            road_Multiline_List = []
            for i in range(len(ints)-1):
                flag = True
                road_index = 0
                startid = ints[i]
                endid = ints[i+1]
    
                while (flag):
                    road_index += 1
                    if((int(edges_distance[road_index][1]) == endid and int(edges_distance[road_index][0]) == startid) or (int(edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) ): #or int((edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) 
                        road_IDS.append(edges_distance[road_index][3])
                        
                        roadLineString = edges_distance[road_index][4][0]
    
                        road_Multiline_List.append(roadLineString)
                        
                        flag = False
            # print(road_IDS, "rota")
            # print(road_Multiline_List[0])
            
            nextMultiLine = sheplygeometry.MultiLineString(road_Multiline_List)
            
        if (user_type == "Bisikletli"):
            
            otoMultiLine = "LINESTRING (0 0, 5 5, 10 10, 8.646 50.4654)"
            
            result1,result2 = (dijkstra (edges_distance , start_str, end_str))
    
            f = (str(result2).replace('(','').replace(')',''))
            t = (str(f).replace("'",'').replace("'",''))
            ints=[]
            g = t.split(",")
            for item in range(len(g) - 1):
                ints.append(int(g[item]))
            
            
            
            
            
            Lon_List = []
            Lat_List = []
            for k in range(len(nodes)):
    
    
                Lon_List.append(Geometry(nodes['geom'].iloc[k]).shapely.x)
                Lat_List.append(Geometry(nodes['geom'].iloc[k]).shapely.y)
            nodes['lon'] = Lon_List
            nodes['lat'] = Lat_List
    
            
            
            lat=[]
            lon=[]
            for item in ints:
                nodeslat=nodes[nodes.id==item]["lat"].values
                nodeslon=nodes[nodes.id==item]["lon"].values
                lat.append(nodeslat)
                lon.append(nodeslon)
                
    
            print(ints)
            road_IDS = []
            road_Multiline_List = []
            for i in range(len(ints)-1):
                flag = True
                road_index = 0
                startid = ints[i]
                endid = ints[i+1]
    
                while (flag):
                    road_index += 1
                    if((int(edges_distance[road_index][1]) == endid and int(edges_distance[road_index][0]) == startid) or (int(edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) ): #or int((edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) 
                        road_IDS.append(edges_distance[road_index][3])
                        
                        roadLineString = edges_distance[road_index][4][0]
    
                        road_Multiline_List.append(roadLineString)
                        
                        flag = False
            # print(road_IDS, "rota")
            # print(road_Multiline_List[0])
            
            nextMultiLine = sheplygeometry.MultiLineString(road_Multiline_List)
            
        if (user_type == "Engelli"):
            otoMultiLine = "LINESTRING (0 0, 5 5, 10 10, 8.646 50.4654)"
            
            result1,result2 = (dijkstra (edges_distance , start_str, end_str))
    
            f = (str(result2).replace('(','').replace(')',''))
            t = (str(f).replace("'",'').replace("'",''))
            ints=[]
            g = t.split(",")
            for item in range(len(g) - 1):
                ints.append(int(g[item]))
            
            
            
            
            
            Lon_List = []
            Lat_List = []
            for k in range(len(nodes)):
    
    
                Lon_List.append(Geometry(nodes['geom'].iloc[k]).shapely.x)
                Lat_List.append(Geometry(nodes['geom'].iloc[k]).shapely.y)
            nodes['lon'] = Lon_List
            nodes['lat'] = Lat_List
    
            
            
            lat=[]
            lon=[]
            for item in ints:
                nodeslat=nodes[nodes.id==item]["lat"].values
                nodeslon=nodes[nodes.id==item]["lon"].values
                lat.append(nodeslat)
                lon.append(nodeslon)
                
    
            print(ints)
            road_IDS = []
            road_Multiline_List = []
            for i in range(len(ints)-1):
                flag = True
                road_index = 0
                startid = ints[i]
                endid = ints[i+1]
    
                while (flag):
                    road_index += 1
                    if((int(edges_distance[road_index][1]) == endid and int(edges_distance[road_index][0]) == startid) or (int(edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) ): #or int((edges_distance[road_index][1]) == startid and int(edges_distance[road_index][0]) == endid) 
                        road_IDS.append(edges_distance[road_index][3])
                        
                        roadLineString = edges_distance[road_index][4][0]
    
                        road_Multiline_List.append(roadLineString)
                        
                        flag = False
            # print(road_IDS, "rota")
            # print(road_Multiline_List[0])
            
            nextMultiLine = sheplygeometry.MultiLineString(road_Multiline_List)

            

    return render(request, 'index.html', {'name': otoMultiLine , 'name2': nextMultiLine})
    # return render(request, 'showResult.html', {'name': total})

