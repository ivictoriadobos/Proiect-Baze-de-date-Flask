from flask import Flask, render_template, jsonify, request, redirect, url_for
import cx_Oracle
import re
from datetime import datetime

cx_Oracle.init_oracle_client(
    lib_dir=r"E:\installuri\instantclient-basiclite-windows.x64-18.5.0.0.0dbru\instantclient_18_5")

app = Flask(__name__)

dsn = cx_Oracle.makedsn("bd-dc.cs.tuiasi.ro", 1539, service_name="orcl")
con = cx_Oracle.connect("bd119", "bd119", dsn, encoding="UTF-8")

success = False
redrct = False

@app.route('/')
def redirect_acasa():
    """
    Functie ce redirecteaza url-ul simplu catre o pagina fixata, aici pagina acasa (daca se acceseaza localhost:5000/ ea nu e atribuita niciunei pagini si genereaza eroare)
    """
    return redirect(url_for('acasa'))

@app.route('/vezi_programari', methods=["POST", "GET"])
def vezi_programari():
    """
    Functia returneaza un dictionar unde cheile sunt medicii ce au programari in acea luna aleasa de user, iar valorile sunt datele programarilor.
    """
    afiseaza = False
    medici = dict()
    global redrct
    global success
    redir = redrct
    redrct = False

    if request.method == "POST":

        show = request.form["vezi_programari_luna"]

        if show != "Alege..." :
            afiseaza = True

            cur = con.cursor()

            query = '''select m.id_medic, m.nume "Nume medic", p.id_programare, TO_CHAR(data, 'fmDD Day "of" Month HH24:MI:SS AM') "Data programarii" from medic m
                    left outer join programare p
                    on m.id_medic = p.id_medic
                    WHERE TO_CHAR(p.data, 'MM') =  ''' + show + " order by m.nume, data"
            print(query)
            cur.execute(query)
            for medic_programare in cur: #pentru fiecare intrare medic - programare
                lista_medic = [medic_programare[0], medic_programare[1]]
                tupla_medic = tuple(lista_medic)  #o cheie din dictionar. are forma (id_medic, nume_medic)

                programare = [medic_programare[2], medic_programare[3]] #o valoare asociata unei chei (unui medic) are forma [id_programare, data]
                if tupla_medic in medici.keys(): #daca avem deja medicul in dictionarul nostru ii adaugam inca o programare pentru luna ce s-a selectat
                    medici[tupla_medic].append(programare)
                else: #daca medicul nu e trecut inca in dictionarul nostru il inregistram si ii atasam prima programare, medic[1]
                    medici[tupla_medic] = [programare]
            #la final avem un dictionar cu toti medicii ce au programari in luna ceruta, iar pentru fiecare medic exista un nr variabil de programari
            #numele medicului e cheia dictionarului, iar valorile sunt programarile

            cur.close()
            print(medici)

    return render_template('vezi_programari.html', afiseaza = afiseaza, medici = medici, redir = redir, success = success)

@app.route('/acasa')
def acasa():
    cur = con.cursor()
    cur.execute('select program from cabinet')
    program = cur.fetchone()[0]
    cur.close()
    return render_template('acasa.html', program = program)

@app.route("/clienti", methods = ["POST", "GET"])
def clienti():
    global redrct
    global success
    redirect = redrct
    redrct = False

    clienti = []
    cur = con.cursor()
    cur.execute('select * from client')
    for result in cur:
        client = {'id_client': result[0], 'nume': result[1], 'nr_telefon': result[2], 'adresa': result[3]}
        clienti.append(client)
    cur.close()

    print("Redirect : " + str(redirect) + "Success : " + str(success))
    return render_template('clienti.html', clienti=clienti, redirect = redirect, success = success)


@app.route("/editeazaClient", methods=["POST", "GET"])
def editClient():
    """
    Functia trimite pentru autofill o lista cu detaliile clientului ce se vrea a fi modificat
    """
    id_client = request.form['editeaza_buton']
    cur = con.cursor()
    cur.execute('select * from client where id_client= ' + id_client)

    client = cur.fetchone()
    nume_client = client[1]
    nr_telefon_client = client[2]
    adresa_client = client[3]
    client_detalii = [id_client, nume_client, nr_telefon_client, adresa_client]

    cur.close()
    return render_template("editeazaClient.html", client_detalii = client_detalii)


@app.route("/stergeClient", methods=["POST"])
def stergeClient():
    global con
    global success
    global redrct
    redrct = True
    id_client = request.form['sterge_buton']
    cur = con.cursor()
    try:
        cur.execute('delete from client where id_client = ' + id_client)
        con.commit()
        success = True
    except cx_Oracle.Error as error:
        print(error)
        success = False
    cur.close()
    return redirect('/clienti')


@app.route("/stergeProgramare", methods=["POST"]) #trebuie sa stiu deci ce programare
def stergeProgramare():
    global con
    global success
    global redrct
    redrct = True
    id_programare = request.form['sterge_programare_buton']
    cur = con.cursor()

    ### TRANZACTIE
    try:
        cur.execute('delete from tratament_medicament_fk where id_programare = ' + id_programare)
        # print("\n\nDupa delete from tratament_medicament_fk")
        cur = con.cursor()
        cur.execute('delete from tratament where id_programare = ' + id_programare)
        # print("\n\nDupa delete from tratament")
        cur = con.cursor()
        cur.execute('delete from programare where id_programare = ' + id_programare)
        success = True
        # print("\n\nAM STERSSSS \n\n")
        #con.commit()

    except cx_Oracle.Error as error:
        print(error)
        cur = con.cursor()
        cur.execute('rollback')
        success = False
    cur.close()
    return redirect('/vezi_programari')


@app.route("/adaugaClient", methods=["GET", "POST"])
def adauga_Client():
    global redrct
    global success
    redrct = True

    if request.method == "POST":
        nume_client = "'" + request.form["nume"] + "'"
        nr_telefon = "'" + request.form["nr_telefon"] + "'"
        adresa = request.form["adresa"]
        if adresa != None:
            adresa = "'" + adresa + "'"
        else:
            adresa = "null"

        # ex de query : insert into client (nume, nr_telefon, adresa) values ('Popescu Mioara', '0711223344', null);

        cur = con.cursor()
        query = "insert into client (nume, nr_telefon, adresa) values (" + nume_client + ", " + nr_telefon + "," + adresa + ")"
        # print(query)
        try:
            cur.execute(query)
            con.commit()
            success = True
        except cx_Oracle.Error as e:
            print(e)
            success = False
        cur.close()
        return redirect("/clienti")

    return render_template("adaugaClient.html")


@app.route("/valideazaEditareClient", methods=["POST", "GET"])
def valideazaEditareClient():

    global con
    global success
    global redrct
    redrct = True
    success = False
    id_client = request.form["id_client"]
    nume_client ="'" +  request.form["nume"] + "'"
    nr_telefon_client = "'" + request.form["nr_telefon"]+ "'"
    adresa_client = request.form["adresa"]
    if adresa_client is None:
        adresa_client = "null"
    else:
        adresa_client = "'" + adresa_client + "'"


    cur = con.cursor()
    try:


        cur.execute("update client set nume = " + nume_client + ", nr_telefon = " + nr_telefon_client + ", adresa = " + adresa_client + " where id_client = " + id_client)

        cur = con.cursor()

        con.commit()
        success = True
    except cx_Oracle.Error as error :

        # Rollback in case there is any error
        success = False
        cur.execute("rollback")

    cur.close()
    return redirect('/clienti')

@app.route("/editeazaProgramare", methods=["POST", "GET"])
def editeazaProgramare():

    #luam id-ul programarii ce se vrea a fi editata
    id_programare = request.form['editeaza_programare_buton']

    cur = con.cursor()

    #luam data programarii, id-ul animalului si id-ul medicului pentru a putea intr-un final sa obtinem date pentru autofill cu detaliile programarii de editat nemodificate momentan
    cur.execute('''select to_char(p.data, 'fmDD-MM-YYYY HH24:MI:SS'), a.id_animal, p.id_medic from programare p 
     join animal a on p.id_animal = a.id_animal where id_programare= ''' + str(id_programare))


    #data programarii
    data_idAnimal_idMedic = cur.fetchone()
    data_curenta = data_idAnimal_idMedic[0]

    #id-ul animalului
    id_animal = data_idAnimal_idMedic[1]

    #id-ul medicului
    id_medic = data_idAnimal_idMedic[2]

    #obtinem tupla numeAnimal:numeStapan a programarii ce se vrea editata
    cur = con.cursor()
    cur.execute("select a.nume, c.nume from animal a join client c on c.id_client = a.id_client where a.id_animal = " + str(id_animal))
    animal_client = cur.fetchone()
    animal_client = animal_client[0] + ":" + animal_client[1]  #ex : animal_client =  "Tomita:Popescu Mioara"

    #obtinem toate tuplele de felul numeAnimal:numeStapan pentru a putea oferi optiuni userului
    cur = con.cursor()
    cur.execute("select a.nume, c.nume from animal a join client c on c.id_client = a.id_client order by c.nume")
    lista_animal_client = []
    for result in cur:
        lista_animal_client.append([result[0] + ":" + result[1]])  #toate animalele cu toti stapanii ( ":" = separator )

    #analog animal_client   numeMedic:nr_telefonMedic
    cur = con.cursor()
    cur.execute("select nume, nr_telefon from medic where id_medic = " + str(id_medic))
    medic = cur.fetchone()
    nume_nr_telefon_medic = medic[0]+ ":" + medic[1]

    #analog lista_animal_client    lista cu numeMedic:nr_telefonMedic pt toti medicii
    cur = con.cursor()
    cur.execute("select nume, nr_telefon from medic")
    lista_medici = []
    for result in cur:
        lista_medici.append([result[0] + ":" + result[1]])

    cur.close()
    return render_template("editeazaProgramare.html", id_programare = id_programare, data_curenta = data_curenta, animal_client = animal_client, nume_nr_telefon_medic=nume_nr_telefon_medic,
                           lista_medici=lista_medici, lista_animal_client=lista_animal_client)




@app.route("/faoprogramare", methods=["POST", "GET"])   #doar o incercare, not finished
def fao_programare():
    #daca se apeleaza cu metoda get trebuie sa trimit tuple de medici, animale + stapan
    cur = con.cursor()
    medici = []

    #cream o lista de dictionare cu fiecare medic pentru a-i da posibilitatea userului sa aleaga ce medic va efectua programarea ce se incearca a fi inregistrata
    cur.execute('select * from medic')
    for medic in cur:
        medicc = {'id_medic' : medic[0] , 'nr_telefon_medic' : medic[1], 'nume_medic' : medic[2]}
    cur = con.cursor()

    #luam toate animalele cu stapanul sau
    #exemplu de output:
    # id_client nr_telefon nume                 id_animal nume_1
    # 	  1     0711223344	Popescu Mioara	    1	        Mimi
    #     1	    0711223344	Popescu Mioara	    2	        Tomita
    #     2	    0789234567	Vasile Alexandru	3	        Bella
    #     3	    0734567812	Stefanescu Gabriel	4	        Sheila
    cur.execute(' select c.id_client , c.nr_telefon, c.nume, a.id_animal, a.nume from animal a join client c on a.id_client = c.id_client')


    for stapan_animal in cur:
        id_client = stapan_animal[0]
        nr_telefon_client = stapan_animal[1]
        nume_client = stapan_animal[2]
        id_animal = stapan_animal[3]
        nume_animal = stapan_animal[4]


        animall = {'id_medic' : medic[0] , 'nr_telefon_medic' : medic[1], 'nume_medic' : medic[2]}
    cur = con.cursor()

    cur.execute('select * from medic')
    for medic in cur:
        medicc = {'id_medic' : medic[0] , 'nr_telefon_medic' : medic[1], 'nume_medic' : medic[2]}
    cur = con.cursor()

@app.route("/valideazaEditareProgramare", methods=["POST", "GET"])
def valideazaEditareProgramare():

    global con
    global success
    global redrct
    redrct = True
    success = False
    data = request.form["data"]
    id_programare = request.form["id_programare"]

    #numeMedic:nr_telefonMedic
    medic = request.form["alege_medic"]
    nume_medic = medic.split(":")[0]  #not used in this function but it was necessary to show it in the application for user
    nr_telefon_medic = medic.split(":")[1]

    #numeAnimal:numeClient
    animal_client = request.form["alege_animal_client"]
    animal_nume = animal_client.split(":")[0]
    client_nume = animal_client.split(":")[1]

    #selectam id-ul animalului ce se numeste animal_nume si are stapan pe clientul client_nume
    query = "select a.id_animal from animal a join client c on a.id_client = c.id_client where a.nume = '" + animal_nume + "' and c.nume = '" + client_nume + "'"
    cur = con.cursor()
    cur.execute(query)
    id_animal = cur.fetchone()[0]

    #selectam id-ul medicului ce are numarul de telefon nr_telefon parsat mai sus
    cur = con.cursor()
    cur.execute("select * from medic where nr_telefon = '" + nr_telefon_medic + "'" )
    # print("select * from medic where nr_telefon = '" + nr_telefon_medic + "'")
    id_medic = cur.fetchone()[0]

    try:
        cur = con.cursor()
        query = "update programare set data = to_date( '" + data  + "','DD-MM-YYYY HH24:MI:SS'), id_medic = " + str(id_medic) + ", id_animal = " + str(id_animal) + " where id_programare = " + str(id_programare)
        cur.execute(query)

        cur = con.cursor()
        # con.commit()
        success = True
    except cx_Oracle.Error as error :

        # Rollback in case there is any error
        success = False
        cur.execute("rollback")

    cur.close()
    return redirect('/vezi_programari')



# main
if __name__ == '__main__':
    app.run(debug=True)
    con.close()
