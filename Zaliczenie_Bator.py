# -*- coding: cp1250 -*-

# Skrypt zaliczeniowy realizuj�cy generalizacj� budynk�w

#Wyja�nienia:

# Program nie dzia�a poprawnie dla multipoligon�w oraz niekt�rych budynk�w z lukami
# Budynki dla kt�rych program nie dzia�a poprawnie zostaj� wypisane w postaci listy identyfikator�w

# Parametry programu:
#    tolerancja - tolerancja k�towa s�u��ca do eliminacji dodatkowych punkt�w w budynkach
#             k - ilosc wierzcholkow usuwanych podczas iteracji
#            k2 - docelowa ilosc wierzcholkow w wynikowym budynku

# id_field_name - nazwa pola z tabeli atrybut�w z unikalnym ID 

#import funkcji z biblioteki arcpy
import arcpy
from math import sqrt, atan, acos, cos, sin, pi
#nadpisywanie wynik�w
arcpy.env.overwriteOutput = True


#Funkcja na azymut
def az(p,q):
    try:
        dy = q[1]-p[1]
        dx = q[0]-p[0]
        if dx == 0:
            czwartak = 0
            if dy>0:
                azymut=100
            if dy<0:
                azymut=300                
        else:
            czwartak=atan(float(abs(dy))/float(abs(dx)))
            czwartak=czwartak*200/math.pi
            if dx>0:
                if dy>0:
                    azymut = czwartak
                if dy<0:
                    azymut = 400 - czwartak
                if dy==0:
                    azymut = 0
            if dx<0:
                if dy>0:
                    azymut = 200 - czwartak
                if dy<0:
                    azymut = 200 + czwartak
                if dy==0:
                    azymut = 200
        return azymut
    except Exception, err:
        arcpy.AddError("blad azymut")
        arcpy.AddError(sys.exc_traceback.tb_lineno)
        arcpy.AddError(err.message)
    finally:
        del(dx,dy,czwartak)
        

#Funkcja obliczaj�ca k�t z azymut�w
def angle(az1,az2):
    angle = az2 - az1
    return(angle)

#Funkcja licz�ca odleg�o�� mi�dzy punktami
# input - lista w postaci [ [X1,Y1] , [X2,Y2] ]
# output - odleg�o��
def length(a,b):
    length = sqrt((a[1]-b[1])**2+(a[0]-b[0])**2)
    return(length)

#Funkcja do czytania geometrii
def czytaj2(geometria):
    try:
        lista = []
        i = 0
        for part in geometria:
            for pnt in part:
                if pnt:
                    lista.append([pnt.X, pnt.Y])
        i += 1
        return lista
    finally:
        del(i, part, pnt, geometria, lista)


#Funkcja ograniczaj�ca liczb� punkt�w budynku 
# input - lista w postaci [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ]
# output - wyczyszczona lista w takiej samej postaci
def clear_list(lista1):
    do_usuniecia = []
    for i1 in range(len(lista1)):
        
        poprzedni = i1-1
        nastepny = i1+1
        
        if poprzedni == -1:
            poprzedni = len(lista1)-2

        if nastepny > len(lista1)-1:
            nastepny = 1
            
        angle1=abs(angle(az(lista1[i1],lista1[poprzedni]),az(lista1[i1],lista1[nastepny])))
        
        if (angle1>(200-tolerancja) and angle1<(200+tolerancja)):
            do_usuniecia.append(i1)

    if len(do_usuniecia) == 0:
        return(lista1)
    else:   
        do_usuniecia.reverse()
           
        for index in do_usuniecia:
            lista1.pop(index)

        if do_usuniecia[-1] == 0: lista1.append(lista1[0])

        return(lista1)


#Funkcja licz�ca ilo�� obiekt�w na li�cie w podanym zakresie
# input - d�ugo�� listy , pocz�tkowy index , ko�cowy index
# output - liczba
def compute_range(length_of_list,x1,x2):
    if x2 - x1 < 0:
        output_range = length_of_list - x1 - 1 + x2
    else:
        output_range = x2 - x1 - 1
    return(output_range)



#Funkcja buduj�ca list� przek�tnych
# input - lista w postaci [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ]
# output - lista przek�tnych w postaci [ [ d�ugo�� przek�tnej , index punktu startowego , index punktu ko�cowego ] , ... ]
def create_lista_przek(lista1):
    poligon = create_arcpy_polygon(lista1)
    length1 = len(lista1)-1
    lista_przekatnych = []
    for i1 in range(len(lista1)-1):
        for i2 in range(i1+2,len(lista1)-1):
            
            # sprawdzanie warunku o ilosci odci�tych punkt�w
          
            if (((compute_range(length1,i1,i2) == k) and ((length1 - compute_range(length1,i1,i2)) >= k2)) or ((compute_range(length1,i2,i1) == k) and ((length1 - compute_range(length1,i2,i1)) >= k2))):

                # sprawdzenie czy przek�tna przecina kraw�dzie poligonu
                
                if not create_arcpy_line([lista1[i1],lista1[i2]]).crosses(poligon):
                    lista_przekatnych.append([length(lista1[i1],lista1[i2]),i1,i2])                
    return(lista_przekatnych)



#Funkcja do wyszukiwania najkr�tszej przek�tnej
# input - lista przek�tnych w postaci [ [ d�ugo�� przek�tnej , index punktu startowego , index punktu ko�cowego ] , ... ]
# output - przek�tna w postaci [ d�ugo�� przek�tnej , index punktu startowego , index punktu ko�cowego ]
def search_min_przekatna(lista):
    minimum = lista
    for przekatna in lista:
        if przekatna[0] < minimum[0]:
            minimum = przekatna
            
    return(minimum)



#Funkcja tworzenia obiektu wynikowego oraz cz�ci odci�tej
# input - lista wsp�rz�dnych budynku w postaci [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ]
# output - listy obiektu g��wnego i odci�tego w postaci [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ] oraz najkr�szej przek�tnej
def delete_points(lista):
    najkrotsza = search_min_przekatna(create_lista_przek(lista))
    object1 = range(najkrotsza[1],najkrotsza[2]+1)+[najkrotsza[1]]
    object1_1 = [lista[index] for index in object1]
    object2 = range(najkrotsza[2],len(lista)-1)+range(0,najkrotsza[1]+1)+[najkrotsza[2]]
    object2_2 = [lista[index] for index in object2]

    
    if create_arcpy_polygon(object2_2).area > create_arcpy_polygon(object1_1).area:
        odciete = object1_1
        glowny = object2_2
    else:
        odciete = object2_2
        glowny = object1_1
    return([glowny,odciete,najkrotsza])
        


#Funkcja generalizuj�ca
# input - budynek w postaci [ [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ], ID ]
# output - zgeneralizowany budynek w postaci  [ [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ], ID ] , lista odci�tych obiekt�w w postaci [ [ [ [X1,Y1] , [X2,Y2], ... , [X1,Y1] ] , ID_odcietego ], ID_budynku ]
def generalizacja(budynek):
    
    ID = budynek[1]
    budynek = budynek[0]
    w = len(budynek)-1
    nr_odcietego = 1 
    lista_odcietych = []
    
    if not len(create_lista_przek(budynek)) == 0:
        while w > k2:
            budynek = clear_list(budynek)
            temp_budynek = budynek            
            w = len(budynek)-1

            
            if not len(create_lista_przek(budynek)) == 0:

                 
                if w > k2:
                    
                        
                        budynek,odciety,przekatna = delete_points(budynek)[0],delete_points(budynek)[1],delete_points(budynek)[2]
                        
                        # sprawdzanie czy odcinany obiekt jest wewnatrz czy na zewnatrz poligonu
                        if create_arcpy_line([temp_budynek[przekatna[1]],temp_budynek[przekatna[2]]]).within(create_arcpy_polygon(temp_budynek)):    
                            odciety = [odciety,nr_odcietego,1]
                        else:
                            odciety = [odciety,nr_odcietego,0]

                        # dodanie odci�tego fragmentu do listy odci�tych fragment�w
                        lista_odcietych.append(odciety)
                        
                        #dodanie 1 do licznika odci�tych fragment�w
                        nr_odcietego = nr_odcietego + 1
            else:
                break
            w = len(budynek)-1

    budynek = [budynek,ID]
    lista_odcietych = [lista_odcietych,ID]
    return(budynek,lista_odcietych)



#tworzenie polilinii
def create_arcpy_line(line):
    arcpy_line = arcpy.Polyline(arcpy.Array([arcpy.Point(line[0][0],line[0][1]),arcpy.Point(line[1][0],line[1][1])]))
    return(arcpy_line)



#tworzenie poligonu
def create_arcpy_polygon(polygon):
    arcpy_polygon = arcpy.Polygon(arcpy.Array([arcpy.Point(ppoint[0],ppoint[1]) for ppoint in polygon]))
    return(arcpy_polygon) 



    

#Parametry deteminuj�ce dzia�anie programu


#ilosc punktow w ostatecznym wyniku:
k2=4
#nazwa pola z ID w wejsciowym pliku
id_field_name = 'OBJECTID'
#Tolerancja k�ta u�ywana do usuwania wierzcho�k�w dla kontur�w budynk�w
tolerancja = 10
#ilosc usuwanych wierzcho�k�w
k=1





#Plik wejsciowy zawieraj�cy budynki

budynki = r'C:\Users\Gracjan\Desktop\PPG2\Proba.shp'



#Czytanie geometrii

kursor_czytania = arcpy.da.SearchCursor(budynki, ['SHAPE@', id_field_name])
lista_budynkow = []
lista_odrzuconych = []
for row_czy in kursor_czytania:
    try:
        geometria = czytaj2(row_czy[0])
        lista2 = [geometria,row_czy[1]]
        lista_budynkow.append(lista2)
    except:
        lista_odrzuconych.append(row_czy[1])



#W�a�ciwa generalizacja


wynik_lista = []
wynik_lista_odcietych = []
for poligon in lista_budynkow:
    try:
        wynik_lista.append(generalizacja(poligon)[0])
        wynik_lista_odcietych.append(generalizacja(poligon)[1])
    except:
        lista_odrzuconych.append(poligon[1])

#Tworzenie warstw wynikowych
#�cie�ki do folder�w 
wynik_shp = arcpy.CreateFeatureclass_management(r'C:\Users\Gracjan\Desktop\PPG2','wynik_gen.shp','POLYGON',budynki)
wynik_shp_odciete = arcpy.CreateFeatureclass_management(r'C:\Users\Gracjan\Desktop\PPG2','wynik_odciete.shp','POLYGON')
arcpy.AddField_management(wynik_shp_odciete,'id_budynku','SHORT')
arcpy.AddField_management(wynik_shp_odciete,'id_fragm','SHORT')
arcpy.AddField_management(wynik_shp_odciete,'In_Out','SHORT')


#Uzupe�nianie geometrii i artybut�w warstw
with arcpy.da.InsertCursor(wynik_shp, ['SHAPE@', id_field_name]) as cursor:
    for poligon in wynik_lista:
        cursor.insertRow([poligon[0],poligon[1]])

with arcpy.da.InsertCursor(wynik_shp_odciete, ['SHAPE@', 'id_budynku', 'id_fragm','In_Out']) as cursor:
    for budynek in wynik_lista_odcietych:
        for odciety in budynek[0]:
            id_budynku = budynek[1]
            cursor.insertRow([odciety[0],id_budynku,odciety[1],odciety[2]])


#Lista bydynk�w dla kt�rych wyst�pi� b��d
print('Bydynki dla kt�rych program napotka� b��d: ' + str(lista_odrzuconych))

