from flask import Flask, render_template, request, redirect, send_file, url_for, jsonify
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  "sqlite:///users.db"
app.config['SECRET_KEY'] = "SECRET_KEY"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    livello = db.Column(db.Integer, nullable=False)

base_decollo = {
        "id": False,
        "tandem": [],
        "aff": [],
        "paracadutisti": []
    }

ialjc_path = "/home/AlbatrosManifest/mysite/I-ALJC.db"
datiDB_path = "/home/AlbatrosManifest/mysite/datiDB.db"
tmp_json_path = "/home/AlbatrosManifest/mysite/tmp_decollo.json"
tmp_api_path = "/home/AlbatrosManifest/mysite/api.json"
export_path = "/home/AlbatrosManifest/mysite/export/"

@app.route("/")
def homepage():
    if current_user.is_authenticated:
        return redirect(url_for("gestione"))
    return render_template("index.html")

@app.route("/manifest")
@login_required
def manifest():
    num_volo = 0
    try:
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        decoded_decolli = []
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            decoded_decolli.append(decollo)
        decolli = []
        for i in range(len(decoded_decolli)+1):
            for y in decoded_decolli:
                if y["num_decollo"] == i:
                    if y["stato"] == "prossimo":
                        num_volo = int(y["num_decollo"]) - 1
                    decolli.append(y)
        ialjc.commit()
        ialjc.close()
        data = str(datetime.now())[0:10]
    except:
        return render_template("no_manifest.html")
    return render_template("manifest.html", data=data, decoded_decolli=decolli, num_volo=num_volo)

@app.route("/crea-giornata", methods=("GET", "POST"))
@login_required
def crea_giornata():
    if current_user.livello < 2:
        return render_template(url_for("manifest"))
    ialjc = sqlite3.connect(ialjc_path)
    cur = ialjc.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS decolli_" + str(datetime.now())[0:10].replace("-", "_") + " (id_decollo INTEGER PRIMARY KEY AUTOINCREMENT, num_decollo INTEGER, rifornimento TEXT, stato TEXT, tandem json, aff json, paracadutisti json)")
    ialjc.commit()
    ialjc.close()
    return redirect(url_for("gestione"))

@app.route("/gestione", methods=("GET", "POST"))
@login_required
def gestione():
    if current_user.livello < 2:
        return redirect(url_for("manifest"))
    data = str(datetime.now())[0:10]
    try:
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        decoded_decolli = []
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            decoded_decolli.append(decollo)
        decolli = []
        for i in range(len(decoded_decolli)+1):
            for y in decoded_decolli:
                if y["num_decollo"] == i:
                    decolli.append(y)
        ialjc.commit()
        ialjc.close()
    except:
        return render_template("gestione.html", data=data, giornata=False)
    return render_template("gestione.html", data=data, decoded_decolli=decolli, num_decolli=len(decolli), giornata=True)

@app.route("/modifica-decollo", methods=("GET", "POST"))
@login_required
def nuovo_decollo():
    try:
        with open(tmp_json_path, "r") as decollo:
            tmp_decollo = json.load(decollo)
    except:
        with open(tmp_json_path, "w") as decollo:
            json.dump(base_decollo, decollo)
            tmp_decollo = base_decollo
    return render_template("nuovo_decollo.html", tmp_decollo=tmp_decollo)

@app.route("/modifica-decollo/modifica-tandem", methods=("GET", "POST"))
@login_required
def nuovo_tandem():
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("select * from staff")
    staff = cur.fetchall()
    datiDB.commit()
    datiDB.close()
    decoded_staff = []
    for i in range(len(staff)):
        membro = {
                "id": staff[i][0],
                "nome": staff[i][1],
                "tandem": staff[i][2],
                "aff": staff[i][3],
                "videoman": staff[i][4]
            }
        decoded_staff.append(membro)
    if request.method == "POST":
        try:
            with open(tmp_json_path, "r") as decollo:
                tmp_decollo = json.load(decollo)
        except:
            return redirect(url_for("nuovo_decollo"))
        try:
            idx = tmp_decollo["tandem"][-1]["id"] + 1
        except:
            idx = 0
        try:
            if request.form["video-polso"] == "true":
                tmp_video_polso = True
        except:
            tmp_video_polso = False
        if request.form["videoman"] == "no-video":
                tmp_video_ext = False
        else:
            tmp_video_ext = True
        try:
            if request.form["foto"] == "true":
                tmp_foto = True
        except:
            tmp_foto = False
        if request.form["istruttore"] == "Altro":
            tmp_istruttore = [False, request.form["altroIstruttore"]]
        else:
            tmp_istruttore = [True, request.form["istruttore"]]
        if request.form["videoman"] == "Altro":
            tmp_videoman = [False, request.form["altroVideo"]]
        else:
            tmp_videoman = [True, request.form["videoman"]]
        tmp_tandem = {
                    "id": idx,
                    "istruttore": tmp_istruttore,
                    "passeggero": request.form["passeggero"],
                    "video_polso": tmp_video_polso,
                    "videoman": tmp_videoman,
                    "video_ext": tmp_video_ext,
                    "foto": tmp_foto
                    }
        tmp_decollo["tandem"].append(tmp_tandem)
        with open(tmp_json_path, "w") as decollo:
            json.dump(tmp_decollo, decollo)
        return redirect(url_for("nuovo_decollo"))

    return render_template("new_tandem.html", decoded_staff=decoded_staff)

@app.route("/modifica-decollo/modifica-aff", methods=("GET", "POST"))
@login_required
def nuovo_aff():
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("select * from staff")
    staff = cur.fetchall()
    datiDB.commit()
    datiDB.close()
    decoded_staff = []
    for i in range(len(staff)):
        membro = {
                "id": staff[i][0],
                "nome": staff[i][1],
                "tandem": staff[i][2],
                "aff": staff[i][3],
                "videoman": staff[i][4]
            }
        decoded_staff.append(membro)
    if request.method == "POST":
        try:
            with open(tmp_json_path, "r") as decollo:
                tmp_decollo = json.load(decollo)
        except:
            return redirect(url_for("nuovo_decollo"))
        try:
            idx = tmp_decollo["aff"][-1]["id"] + 1
        except:
            idx = 0
        if request.form["istruttore1"] == "Altro":
            tmp_istruttore1 = [False, request.form["altroIstruttore1"]]
        else:
            tmp_istruttore1 = [True, request.form["istruttore1"]]
        if request.form["istruttore2"] == "Altro":
            tmp_istruttore2 = [False, request.form["altroIstruttore2"]]
        else:
            tmp_istruttore2 = [True, request.form["istruttore2"]]
        tmp_aff = {
                "id": idx,
                "livello": request.form["livello"],
                "istruttore1": tmp_istruttore1,
                "istruttore2": tmp_istruttore2,
                "allievo": request.form["allievo"]
                }
        tmp_decollo["aff"].append(tmp_aff)
        with open(tmp_json_path, "w") as decollo:
            json.dump(tmp_decollo, decollo)
        return redirect(url_for("nuovo_decollo"))

    return render_template("new_aff.html", decoded_staff=decoded_staff)

@app.route("/modifica-decollo/modifica-skydiver", methods=("GET", "POST"))
@login_required
def nuovo_skydiver():
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("select * from skydiver")
    skydiver = cur.fetchall()
    decoded_skydiver = []
    for i in range(len(skydiver)):
        membro = {
                "id": skydiver[i][0],
                "nome": skydiver[i][1],
                "allievo": skydiver[i][2],
                "dl": skydiver[i][3],
                "istruttore": skydiver[i][4]
            }
        decoded_skydiver.append(membro)
    cur.execute("select * from discipline")
    discipline = cur.fetchall()
    decoded_disciplina = []
    for i in range(len(discipline)):
        membro = {
                "id": discipline[i][0],
                "nome": discipline[i][1],
                "key": discipline[i][2]
            }
        decoded_disciplina.append(membro)
    datiDB.commit()
    datiDB.close()
    if request.method == "POST":
        try:
            with open(tmp_json_path, "r") as decollo:
                tmp_decollo = json.load(decollo)
        except:
            return redirect("/modifica-decollo")
        try:
            idx = tmp_decollo["paracadutisti"][-1]["id"] + 1
        except:
            idx = 0
        try:
            if request.form["noleggio"] == "true":
                tmp_noleggio = True
        except:
            tmp_noleggio = False
        if request.form["skydiver"] == "Altro":
            tmp_paracadutista = [False, request.form["altroskydiver"]]
        else:
            tmp_paracadutista = [True, request.form["skydiver"]]
        tmp_skydiver = {
                "id": idx,
                "skydiver": tmp_paracadutista,
                "disciplina": request.form["tipo_lancio"],
                "noleggio": tmp_noleggio
                }
        tmp_decollo["paracadutisti"].append(tmp_skydiver)
        with open(tmp_json_path, "w") as decollo:
            json.dump(tmp_decollo, decollo)
        return redirect(url_for("nuovo_decollo"))

    return render_template("new_skydiver.html", decoded_skydiver=decoded_skydiver, decoded_disciplina=decoded_disciplina)

@app.route("/modifica-decollo/<string:azione>/<string:tipo>/<int:idx>", methods=("POST","GET"))
@login_required
def modifiche(azione, tipo, idx):
    if azione == "elimina":
        with open(tmp_json_path, "r") as decollo:
            tmp_decollo = json.load(decollo)
        tmp = []
        for i in tmp_decollo[tipo]:
            if idx == i["id"]:
                pass
            else:
                tmp.append(i)
        if tipo == "tandem":
            new_decollo = {
                    "id": tmp_decollo["id"],
                    "tandem": tmp,
                    "aff": tmp_decollo["aff"],
                    "paracadutisti": tmp_decollo["paracadutisti"]
                }
        elif tipo == "aff":
            new_decollo = {
                    "id": tmp_decollo["id"],
                    "tandem": tmp_decollo["tandem"],
                    "aff": tmp,
                    "paracadutisti": tmp_decollo["paracadutisti"]
                }
        elif tipo == "paracadutisti":
            new_decollo = {
                    "id": tmp_decollo["id"],
                    "tandem": tmp_decollo["tandem"],
                    "aff": tmp_decollo["aff"],
                    "paracadutisti": tmp
                }

        with open(tmp_json_path, "w") as decollo:
            json.dump(new_decollo, decollo)
        return redirect(url_for("nuovo_decollo"))

    elif azione == "modifica":
        if request.method == "POST":
            with open(tmp_json_path, "r") as decollo:
                tmp_decollo = json.load(decollo)
            tmp = []
            for i in tmp_decollo[tipo]:
                if idx == i["id"]:
                    if tipo == "tandem":
                        try:
                            if request.form["video-polso"] == "true":
                                tmp_video_polso = True
                        except:
                            tmp_video_polso = False
                        if request.form["videoman"] == "no-video":
                                tmp_video_ext = False
                        else:
                            tmp_video_ext = True
                        try:
                            if request.form["foto"] == "true":
                                tmp_foto = True
                        except:
                            tmp_foto = False
                        if request.form["istruttore"] == "Altro":
                            tmp_istruttore = [False, request.form["altroIstruttore"]]
                        else:
                            tmp_istruttore = [True, request.form["istruttore"]]
                        if request.form["videoman"] == "Altro":
                            tmp_videoman = [False, request.form["altroVideo"]]
                        else:
                            tmp_videoman = [True, request.form["videoman"]]
                        new = {
                                "id": idx,
                                "istruttore": tmp_istruttore,
                                "passeggero": request.form["passeggero"],
                                "video_polso": tmp_video_polso,
                                "videoman": tmp_videoman,
                                "video_ext": tmp_video_ext,
                                "foto": tmp_foto
                                }
                        tmp.append(new)
                    elif tipo == "aff":
                        if request.form["istruttore1"] == "Altro":
                            tmp_istruttore1 = [False, request.form["altroIstruttore1"]]
                        else:
                            tmp_istruttore1 = [True, request.form["istruttore1"]]
                        if request.form["istruttore2"] == "Altro":
                            tmp_istruttore2 = [False, request.form["altroIstruttore2"]]
                        else:
                            tmp_istruttore2 = [True, request.form["istruttore2"]]
                        new = {
                                "id": idx,
                                "livello": request.form["livello"],
                                "istruttore1": tmp_istruttore1,
                                "istruttore2": tmp_istruttore2,
                                "allievo": request.form["allievo"]
                                }
                        tmp.append(new)
                    elif tipo == "paracadutisti":
                        try:
                            if request.form["noleggio"] == "true":
                                tmp_noleggio = True
                        except:
                            tmp_noleggio = False
                        if request.form["skydiver"] == "Altro":
                            tmp_paracadutista = [False, request.form["altroskydiver"]]
                        else:
                            tmp_paracadutista = [True, request.form["skydiver"]]
                        new = {
                                "id": idx,
                                "skydiver": tmp_paracadutista,
                                "disciplina": request.form["tipo_lancio"],
                                "noleggio": tmp_noleggio
                                }
                        tmp.append(new)
                else:
                    tmp.append(i)
            if tipo == "tandem":
                new_decollo = {
                        "id": tmp_decollo["id"],
                        "tandem": tmp,
                        "aff": tmp_decollo["aff"],
                        "paracadutisti": tmp_decollo["paracadutisti"]
                    }
            elif tipo == "aff":
                new_decollo = {
                        "id": tmp_decollo["id"],
                        "tandem": tmp_decollo["tandem"],
                        "aff": tmp,
                        "paracadutisti": tmp_decollo["paracadutisti"]
                    }
            elif tipo == "paracadutisti":
                new_decollo = {
                        "id": tmp_decollo["id"],
                        "tandem": tmp_decollo["tandem"],
                        "aff": tmp_decollo["aff"],
                        "paracadutisti": tmp
                    }

            with open(tmp_json_path, "w") as decollo:
                json.dump(new_decollo, decollo)
            return redirect("/modifica-decollo")
        datiDB = sqlite3.connect(datiDB_path)
        cur = datiDB.cursor()
        cur.execute("select * from staff")
        staff = cur.fetchall()
        cur.execute("select * from skydiver")
        skydivers = cur.fetchall()
        cur.execute("select * from discipline")
        discipline = cur.fetchall()
        datiDB.commit()
        datiDB.close()
        decoded_staff = []
        for i in range(len(staff)):
            membro = {
                    "id": staff[i][0],
                    "nome": staff[i][1],
                    "tandem": staff[i][2],
                    "aff": staff[i][3],
                    "videoman": staff[i][4]
                }
            decoded_staff.append(membro)
        decoded_skydivers = []
        for i in range(len(skydivers)):
            skydiver = {
                    "id": skydivers[i][0],
                    "nome": skydivers[i][1],
                    "allievo": skydivers[i][2],
                    "dl": skydivers[i][3],
                    "istruttore": skydivers[i][4]
                }
            decoded_skydivers.append(skydiver)
        decoded_disciplina = []
        for i in range(len(discipline)):
            disciplina = {
                    "id": discipline[i][0],
                    "nome": discipline[i][1],
                    "key": discipline[i][2]
                }
            decoded_disciplina.append(disciplina)
        with open(tmp_json_path, "r") as decollo:
            tmp_decollo = json.load(decollo)
        tmp = False
        for i in tmp_decollo[tipo]:
            if idx == i["id"]:
                tmp = i
        if tipo == "tandem":
            return render_template("new_tandem.html", decoded_staff=decoded_staff, tmp=tmp)
        elif tipo == "aff":
            return render_template("new_aff.html", decoded_staff=decoded_staff, tmp=tmp)
        elif tipo == "paracadutisti":
            return render_template("new_skydiver.html", decoded_skydiver=decoded_skydivers, decoded_disciplina=decoded_disciplina, tmp=tmp)

@app.route("/annulla-decollo")
@login_required
def annulla_decollo():
    try:
        os.remove(tmp_json_path)
    except:
        pass
    return redirect(url_for("gestione"))

@app.route("/conferma-decollo")
@login_required
def conferma_decollo():
    with open(tmp_json_path, "r") as decollo:
        tmp_decollo = json.load(decollo)
    ialjc = sqlite3.connect(ialjc_path)
    cur = ialjc.cursor()
    cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
    decolli = cur.fetchall()
    num_decollo = 1
    pronto = False
    for i in range(len(decolli)):
        decollo = {
                "id": decolli[i][0],
                "num_decollo": decolli[i][1],
                "rifornimento": decolli[i][2],
                "stato": decolli[i][3],
                "tandem": json.loads(decolli[i][4]),
                "aff": json.loads(decolli[i][5]),
                "paracadutisti": json.loads(decolli[i][6])
            }
        if decollo["num_decollo"] >= num_decollo:
            num_decollo = decollo["num_decollo"] + 1
        if decollo["stato"] == "prossimo":
            pronto = True
    rifornimento = "false"
    if num_decollo == 1 or pronto == False:
        stato = "prossimo"
    else:
        stato = "preparazione"
    if tmp_decollo["id"] == False:
        cur.execute("INSERT INTO decolli_" + str(datetime.now())[0:10].replace("-", "_") + " (num_decollo, rifornimento, stato, tandem, aff, paracadutisti) VALUES (?,?,?,?,?,?)", [num_decollo, rifornimento, stato, json.dumps(tmp_decollo["tandem"]), json.dumps(tmp_decollo["aff"]), json.dumps(tmp_decollo["paracadutisti"])])
    else:
        try:
            cur.execute("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET tandem = ?, aff = ?, paracadutisti = ? WHERE id_decollo = ?", [json.dumps(tmp_decollo["tandem"]), json.dumps(tmp_decollo["aff"]), json.dumps(tmp_decollo["paracadutisti"]), tmp_decollo["id"]])
        except:
            pass
    ialjc.commit()
    ialjc.close()
    os.remove(tmp_json_path)
    return redirect(url_for("gestione"))

@app.route("/gestione/modifica-decollo/<string:azione>/<int:idx>", methods=("POST","GET"))
@login_required
def modifica_decollo_gestione(azione, idx):
    if azione == "elimina":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute(("select num_decollo, stato from decolli_" + str(datetime.now())[0:10].replace("-", "_") + " WHERE id_decollo = ?"), [idx])
        dec = cur.fetchall()
        num_decollo = dec[0][0]
        stato_decollo = dec[0][1]
        cur.execute("DELETE FROM decolli_" + str(datetime.now())[0:10].replace("-", "_") + " WHERE id_decollo = ?", [idx])
        ialjc.commit()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        decoded_decolli = []
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            if decollo["num_decollo"] > num_decollo:
                decollo["num_decollo"] = decollo["num_decollo"] - 1
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ? WHERE id_decollo = ?"), [decollo["num_decollo"], decollo["id"]])
        ialjc.commit()
        if stato_decollo == "prossimo":
            try:
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), [stato_decollo, num_decollo])
            except:
                pass
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "anticipa":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            if decollo["id"] == idx:
                new_num = decollo["num_decollo"] - 1
                if decollo["stato"] == "prossimo":
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ?, stato = ? WHERE num_decollo = ?"), [decollo["num_decollo"], "preparazione", new_num])
                else:
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ? WHERE num_decollo = ?"), [decollo["num_decollo"], new_num])
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ? WHERE id_decollo = ?"), [new_num, decollo["id"]])
                ialjc.commit()
                cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
                decolli = cur.fetchall()
                for y in range(len(decolli)):
                    decollo = {
                            "id": decolli[y][0],
                            "num_decollo": decolli[y][1],
                            "rifornimento": decolli[y][2],
                            "stato": decolli[y][3],
                            "tandem": json.loads(decolli[y][4]),
                            "aff": json.loads(decolli[y][5]),
                            "paracadutisti": json.loads(decolli[y][6])
                        }
                    if decollo["num_decollo"] == new_num + 1:
                        if decollo["stato"] == "prossimo":
                            cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["preparazione", new_num + 1])
                            cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["prossimo", new_num])
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "posticipa":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            if decollo["id"] == idx:
                new_num = decollo["num_decollo"] + 1
                if decollo["stato"] == "prossimo":
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ?, stato = ? WHERE num_decollo = ?"), [decollo["num_decollo"], "prossimo", new_num])
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ?, stato = ? WHERE id_decollo = ?"), [new_num, "preparazione", decollo["id"]])
                else:
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ? WHERE num_decollo = ?"), [decollo["num_decollo"], new_num])
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET num_decollo = ? WHERE id_decollo = ?"), [new_num, decollo["id"]])
                ialjc.commit()
                cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
                decolli = cur.fetchall()
                for y in range(len(decolli)):
                    decollo = {
                            "id": decolli[y][0],
                            "num_decollo": decolli[y][1],
                            "rifornimento": decolli[y][2],
                            "stato": decolli[y][3],
                            "tandem": json.loads(decolli[y][4]),
                            "aff": json.loads(decolli[y][5]),
                            "paracadutisti": json.loads(decolli[y][6])
                        }
                    if decollo["num_decollo"] == new_num:
                        if decollo["stato"] == "fatto":
                            cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["preparazione", new_num])
                            cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["prossimo", new_num - 1])
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "rifornimento":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            if decollo["id"] == idx:
                if decollo["rifornimento"] == "false":
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET rifornimento = ? WHERE id_decollo = ?"), ["true", decollo["id"]])
                if decollo["rifornimento"] == "true":
                    cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET rifornimento = ? WHERE id_decollo = ?"), ["false", decollo["id"]])
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "decollo":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["fatto", idx])
        cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE num_decollo = ?"), ["prossimo", idx + 1])
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "start":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_"))
        decolli = cur.fetchall()
        for i in range(len(decolli)):
            decollo = {
                    "id": decolli[i][0],
                    "num_decollo": decolli[i][1],
                    "rifornimento": decolli[i][2],
                    "stato": decolli[i][3],
                    "tandem": json.loads(decolli[i][4]),
                    "aff": json.loads(decolli[i][5]),
                    "paracadutisti": json.loads(decolli[i][6])
                }
            if decollo["num_decollo"] == idx:
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE id_decollo = ?"), ["prossimo", decollo["id"]])
            elif decollo["num_decollo"] > idx:
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE id_decollo = ?"), ["preparazione", decollo["id"]])
            elif decollo["num_decollo"] < idx:
                cur.execute(("UPDATE decolli_" + str(datetime.now())[0:10].replace("-", "_") + " SET stato = ? WHERE id_decollo = ?"), ["fatto", decollo["id"]])

        ialjc.commit()
        ialjc.close()
        return redirect(url_for("gestione"))
    elif azione == "modifica":
        ialjc = sqlite3.connect(ialjc_path)
        cur = ialjc.cursor()
        try:
            os.remove("tmp_decollo.json")
        except:
            pass
        cur.execute("select * from decolli_" + str(datetime.now())[0:10].replace("-", "_") + " WHERE id_decollo = ?", [idx])
        decollo = cur.fetchall()
        tmp_decollo = {
                    "id": decollo[0][0],
                    "tandem": json.loads(decollo[0][4]),
                    "aff": json.loads(decollo[0][5]),
                    "paracadutisti": json.loads(decollo[0][6])
                }
        with open(tmp_json_path, "w") as decollo:
            json.dump(tmp_decollo, decollo)
        ialjc.commit()
        ialjc.close()
        return redirect(url_for("nuovo_decollo"))

@app.route("/admin")
@login_required
def admin():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    return redirect(url_for("admin_staff"))

@app.route("/admin/staff")
@login_required
def admin_staff():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, tandem TEXT, aff TEXT, videoman TEXT)")
    cur.execute("select * from staff")
    staff = cur.fetchall()
    datiDB.commit()
    datiDB.close()
    decoded_staff = []
    for i in range(len(staff)):
        membro = {
                "id": staff[i][0],
                "nome": staff[i][1],
                "tandem": staff[i][2],
                "aff": staff[i][3],
                "videoman": staff[i][4]
            }
        decoded_staff.append(membro)
    return render_template("admin_staff.html", decoded_staff=decoded_staff)

@app.route("/admin/skydiver")
@login_required
def admin_skydiver():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS skydiver (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, allievo TEXT, dl TEXT, istruttore TEXT)")
    cur.execute("select * from skydiver")
    skydivers = cur.fetchall()
    datiDB.commit()
    datiDB.close()
    decoded_skydivers = []
    for i in range(len(skydivers)):
        skydiver = {
                "id": skydivers[i][0],
                "nome": skydivers[i][1],
                "allievo": skydivers[i][2],
                "dl": skydivers[i][3],
                "istruttore": skydivers[i][4]
            }
        decoded_skydivers.append(skydiver)
    return render_template("admin_skydiver.html", decoded_skydivers=decoded_skydivers)

@app.route("/admin/discipline")
@login_required
def admin_discipline():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    datiDB = sqlite3.connect(datiDB_path)
    cur = datiDB.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS discipline (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, key TEXT)")
    cur.execute("select * from discipline")
    discipline = cur.fetchall()
    datiDB.commit()
    datiDB.close()
    decoded_disciplina = []
    for i in range(len(discipline)):
        disciplina = {
                "id": discipline[i][0],
                "nome": discipline[i][1],
                "key": discipline[i][2]
            }
        decoded_disciplina.append(disciplina)
    return render_template("admin_discipline.html", decoded_discipline=decoded_disciplina)

@app.route("/admin/giornate")
@login_required
def admin_giornate():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    ialjc = sqlite3.connect(ialjc_path)
    cur = ialjc.cursor()
    cur.execute("SELECT * FROM sqlite_sequence")
    giornate = cur.fetchall()
    ialjc.commit()
    ialjc.close()
    decoded_giornate = []
    for i in range(len(giornate)):
        giornata = giornate[i][0].lstrip("decolli_").replace("_", "-")
        decoded_giornate.append(giornata)
    return render_template("admin_giornate.html", decoded_giornate=decoded_giornate)

@app.route("/login", methods=("POST","GET"))
def login():
    if request.method == "POST":
        utente = User.query.filter_by(username=request.form["username"]).first()
        if utente:
            if check_password_hash(utente.password, request.form["pw"]):
                login_user(utente)
                return redirect(url_for("homepage"))
    return render_template("login.html")

@app.route("/logout", methods=("POST","GET"))
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage"))

@app.route("/admin/add-user", methods=("POST","GET"))
@login_required
def add_user():
    if current_user.livello < 3:
        return redirect(url_for("homepage"))
    if request.method == "POST":
        utente = User.query.filter_by(username=request.form["username"]).first()
        if utente is None:
            if request.form["pw"] == request.form["cpw"] and request.form["pw"] != "":
                password = generate_password_hash(request.form["pw"])
                utente = User(username=request.form["username"], password=password, livello=request.form["livello"])
                db.session.add(utente)
                db.session.commit()
    return render_template("add_user.html")

@app.route("/download/<string:data>")
@login_required
def download(data):
    ialjc = sqlite3.connect(ialjc_path)
    cur = ialjc.cursor()
    cur.execute("select * from decolli_" + data.replace("-", "_"))
    decolli = cur.fetchall()
    decoded_decolli = []
    for i in range(len(decolli)):
        decollo = {
                "id": decolli[i][0],
                "num_decollo": decolli[i][1],
                "rifornimento": decolli[i][2],
                "stato": decolli[i][3],
                "tandem": json.loads(decolli[i][4]),
                "aff": json.loads(decolli[i][5]),
                "paracadutisti": json.loads(decolli[i][6])
            }
        decoded_decolli.append(decollo)
    decolli = []
    for i in range(len(decoded_decolli)+1):
        for y in decoded_decolli:
            if y["num_decollo"] == i:
                decolli.append(y)
    ialjc.commit()
    ialjc.close()
    dati_giornata = {
            "data": data,
            "decolli": decolli
        }
    with open(export_path+data+".json", "w") as f:
        json.dump(dati_giornata, f)
    f = export_path+data+".json"
    return send_file(f, as_attachment=True)

@app.route("/api/<string:api_code>/<string:data>")
def ritorna_data(api_code, data):
    with open(tmp_api_path, "r") as api_cred:
        cred = json.load(api_cred)
    if cred["api"] != api_code:
        return jsonify({"errore": "API_CODE errato"})
    ialjc = sqlite3.connect(ialjc_path)
    cur = ialjc.cursor()
    cur.execute("select * from decolli_" + data.replace("-", "_"))
    decolli = cur.fetchall()
    decoded_decolli = []
    for i in range(len(decolli)):
        decollo = {
                "id": decolli[i][0],
                "num_decollo": decolli[i][1],
                "rifornimento": decolli[i][2],
                "stato": decolli[i][3],
                "tandem": json.loads(decolli[i][4]),
                "aff": json.loads(decolli[i][5]),
                "paracadutisti": json.loads(decolli[i][6])
            }
        decoded_decolli.append(decollo)
    decolli = []
    for i in range(len(decoded_decolli)+1):
        for y in decoded_decolli:
            if y["num_decollo"] == i:
                decolli.append(y)
    ialjc.commit()
    ialjc.close()
    dati_giornata = {
            "data": data,
            "decolli": decolli
        }
    return jsonify(dati_giornata)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
