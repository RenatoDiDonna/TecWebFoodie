from datetime import datetime,timedelta,time
from flask import Flask,jsonify, request, redirect, url_for, render_template,flash,session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
from fuzzywuzzy import fuzz


app = Flask(__name__,static_folder='static')


#configuro l'Url del database per l'applicazione Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/pysql'

# Bcrypt fornisce la funzionalità per la crittografia della password
bcrypt = Bcrypt()

# fornisce funzionalità per lavorare con il database
db = SQLAlchemy()
#  è una chiamata per inizializzare l'oggetto Bcrypt con l'applicazione Flask
bcrypt.init_app(app)

#imposta l'indirizzo del database che verrà usato dall'applicazione
db.init_app(app)

#crea un'istanza di un oggetto LoginManager. è una classe fornita da Flask-Login che permette di gestire l'utente
login_manager = LoginManager()

#inizializza il login manager. Gestisce la sessione di login dell'utente , vede se l'utente è connesso  attualmente e permette di caricare l'oggetto utente corrente
login_manager.init_app(app)


with app.app_context():
    # crea tutte le tabelle nel database specificato
    db.create_all()


class Ristorante(UserMixin, db.Model):
     __tablename__ = 'Ristorante'
     IdRistorante = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
     Nome = db.Column(db.String(45),  nullable=False)
     Citta = db.Column(db.String(45),  nullable=False)
     Via = db.Column(db.String(45),     nullable=False)
     NumeroCivico=db.Column(db.Integer, nullable=False)
     categorie = db.relationship("Categoria", backref="ristorante", lazy=True)
     tavoli = db.relationship("Tavolo", backref="ristorante", lazy=True)

     #creo metodo costruttore classe
     def __init__(self, IdRistorante, Nome, Citta, Via, NumeroCivico):
        self.IdRistorante = IdRistorante
        self.Nome = Nome
        self.Citta = Citta
        self.Via = Via
        self.NumeroCivico = NumeroCivico



class Categoria(UserMixin,db.Model):
    __tablename__ = 'Categoria'
    CodiceCategoria = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Tipologia = db.Column(db.String(45), nullable=False)
    ID_Ristorante = db.Column(db.Integer, db.ForeignKey("Ristorante.IdRistorante"), nullable=False)



#creo metodo costruttore categoria
    def __init__(self, CodiceCategoria,Tipologia):
        self.CodiceCategoria= CodiceCategoria
        self.Tipologia= Tipologia




#viene creata una classe User,classe fornita da Flask-SqlAlchemy. La classe user definisce 3 colonne
class User(UserMixin,db.Model):
    __tablename__ = 'Profilo'
    username = db.Column(db.String(100), primary_key=True, unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    Nome = db.Column(db.String(40), nullable=False)
    Cognome = db.Column(db.String(40), nullable=False)
    Data_Nascita = db.Column(db.Date, nullable=False)
    Cellulare = db.Column(db.String(10), nullable=False)
    prenotazioni_persona = db.relationship("Prenota", backref="Profilo", lazy=True)


    # creo un metodo costruttore della classe User , viene utilizzato per inizializzare un nuovo oggetto di tipo user
    def __init__(self, username, email, password,Nome,Cognome,Data_Nascita,Cellulare):
        self.username = username
        self.email = email
        # Questa funzione viene utilizzata per creare una versione hash della password , in modo da poterla memorizzare in modo sicuro
        self.password = bcrypt.generate_password_hash(password)
        self.Nome = Nome
        self.Cognome=Cognome
        self.Data_Nascita=Data_Nascita
        self.Cellulare=Cellulare

        # restituisce username,identifico utente che ha effettuato l'accesso

    def get_id(self):
      return self.username

            # funzione che verifica se la password fornita dall'utente corrisponde a quella memorizzata
    def check_password(self, password):
       return bcrypt.check_password_hash(self.password, password)

    # dobbiamo dire che l'utente è sempre attivo per non riscontrare errori
    def is_active(self):
         return True


class Tavolo(UserMixin,db.Model):
    __tablename__ = 'Tavolo'
    NumTavolo = db.Column(db.Integer, primary_key=True, nullable=False)
    ID_RistoranteTav = db.Column(db.Integer, db.ForeignKey('Ristorante.IdRistorante'), primary_key=True)
    NumPosti = db.Column(db.Integer, nullable=False)
    Disponibile = db.Column(db.Boolean, default=True, nullable=False)
#controlla se esiste una prenotazione già esistente che si sovrappone alla prenotazione corrente
#se esiste una prenotazione in quell'intervallo d'orario
    def disponibile(self, data, ora):
        prenotazioni = Prenota.query.filter_by(Num_Tavolo=self.NumTavolo, Data_prenotazione=data).all()
        momento = datetime.combine(datetime.strptime(data, "%Y-%m-%d").date(),
                                   datetime.strptime(ora, "%H:%M").time())

        for prenotazione in prenotazioni:
            orario_prenotazione = datetime.combine(prenotazione.Data_prenotazione, prenotazione.Orario)
            ora_fine_prenotazione = datetime.combine(prenotazione.Data_prenotazione, prenotazione.ora_fine)
            # se la nostra prenotazione è
            if orario_prenotazione <= momento <= ora_fine_prenotazione:
                return False
        return True

    def __init__(self, NumTavolo, Id_RistoranteTav, NumPosti,Disponibile):
        self.NumTavolo = NumTavolo
        self.Id_RistoranteTav = Id_RistoranteTav
        self.NumPosti = NumPosti
        self.Disponibile=Disponibile



class Prenota(UserMixin, db.Model):
    __tablename__ = 'Prenota'
    Username_profilo = db.Column(db.String(20), db.ForeignKey('Profilo.username'), primary_key=True)
    Num_Tavolo = db.Column(db.Integer, db.ForeignKey('Tavolo.NumTavolo'), primary_key=True)
    Orario = db.Column(db.Time, nullable=False)
    Data_prenotazione=db.Column(db.Date, nullable=False)
    ora_fine = db.Column(db.Time, nullable=False)

    def __init__(self, Username_profilo, Num_Tavolo, Orario, Data_prenotazione,ora_fine):
        self.Username_profilo = Username_profilo
        self.Num_Tavolo = Num_Tavolo
        self.Orario = Orario
        self.Data_prenotazione = Data_prenotazione
        self.ora_fine= ora_fine

class Recensione(UserMixin,db.Model):
    __tablename__ = 'Recensione'
    IDRecensione = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Titolo = db.Column(db.String(100))
    Voto = db.Column(db.Integer, nullable=False)
    Descrizione = db.Column(db.String(100))
    Autore_recensione = db.Column(db.String(20), db.ForeignKey('Profilo.username'))
    Ristorante_Rec=db.Column(db.Integer, db.ForeignKey('Ristorante.IdRistorante'))

#creo metodo costruttore recensione
    def __init__(self,Titolo,Voto,Descrizione,Autore_recensione,Ristorante_Rec):
        self.Titolo= Titolo
        self.Voto=Voto
        self.Descrizione=Descrizione
        self.Autore_recensione=Autore_recensione
        self.Ristorante_Rec=Ristorante_Rec

# funzione che indica a Flask-Login quale funzione utilizzare per caricare un utente dal database
@login_manager.user_loader



#riceve come argomento l'id dell'utente che si vuole caricare dal database e restituisce un oggetto User corrispondente all'username
def load_user(user_id):
    return User.query.get(user_id)



@app.before_request
def before_request():
    if request.path == '/fudy' and not current_user.is_authenticated:
        return redirect(url_for('login'))



@app.route('/', methods=['GET', 'POST'])
def login():
#se è un metodo post , l'utente ha inviato i dati di username e password ,la funzione recupera i dati con
#request form
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        #viene cercato un utente nel database che abbia quell'username
        Profilo = User.query.filter_by(username=username).first()
#se l'utente esiste e la password inserita è corretta
        if Profilo and Profilo.check_password(password):
            #viene effettuato l'accesso dell'utente
            login_user(Profilo)
            return redirect(url_for('fudy'))

        else:
            flash("Errore di autenticazione, controlla le tue credenziali")
            return redirect(url_for('login'))
    else:
        #se il metodo non è post,l'utente sta solo visitando la pagina di login
        return render_template("login.html")

@app.route('/fudy')
@login_required
def fudy():
    return render_template("fudy.html")


@app.route('/logout')
#login required garantisce che solo gli utenti autenticati possono accedere a questa pagina
@login_required
#funzione per il logout utente che lo riporta alla prima pagina
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profilo')
@login_required
def profilo():
  user= current_user
  ultima_prenotazione = Prenota.query.filter_by(Username_profilo=user.username).order_by(Prenota.Data_prenotazione.desc()).first()
  if ultima_prenotazione:
   data_formattata = ultima_prenotazione.Data_prenotazione.strftime("%d/%m/%Y")
   orario=ultima_prenotazione.Orario
  else:
   data_formattata = None
   orario = None
  return render_template('Profilo.html',user=user,data_formattata=data_formattata,orario=orario)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('registrazione.html')
    #quando viene effettuata una richiesta , il codice raccoglie i dati inviati dal form di registrazione
    #e li utilizza per creare un nuovo utente
    if request.method == 'POST':
        #dati profilo
        Nome= request.form['Nome']
        Cognome= request.form['Cognome']
        Data_Nascita= request.form['Data_Nascita']
        username = request.form['username']
        email = request.form['email']
        Cellulare= request.form['Cellulare']
        password = request.form['password']
        confirm_password = request.form['confirm_password']




        if not all([Nome,Cognome,Data_Nascita,username, email,Cellulare, password, confirm_password]):
            flash("Devi compilare tutti i campi del form per registrarti!")
            return render_template('registrazione.html')
 #se password diversa da conferma password,errore
        if password != confirm_password:
            flash("Le password non coincidono! Attenzione")
            return render_template('registrazione.html')
        #se l'username è già presente nel database , errore
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Attenzione! Username già inserito nel database!")
            return  render_template('registrazione.html')
   #viene creato nuovo oggetto user
        new_user = User(username=username,Nome=Nome,Cognome=Cognome,Data_Nascita=Data_Nascita, email=email, Cellulare=Cellulare,password=password)
        db.session.add(new_user)
        db.session.commit()




        #dopo aver fatto il login , accediamo alla pagina principale
        return redirect(url_for('login'))



@app.route('/ristoranti', methods=['GET', 'POST'])
@login_required
def ristoranti():
    categorie = Categoria.query.all()
    ristoranti = Ristorante.query.all()
    if request.method == 'POST':
        nome = request.form.get('nome')
        citta = request.form.get('citta')
        categoria = request.form.get('categoria')
        ristoranti = []
        for ristorante in Ristorante.query.all():
            if nome:
                if (
                        fuzz.token_set_ratio(nome, ristorante.Nome) >= 50
                        and (citta in ristorante.Citta if citta else True)
                        and (categoria in [c.Tipologia for c in ristorante.categorie] if categoria else True)
                ):
                    ristoranti.append(ristorante)

            elif citta or categoria:
                if (citta in ristorante.Citta if citta else True) and (
                categoria in [c.Tipologia for c in ristorante.categorie] if categoria else True):
                    ristoranti.append(ristorante)

    return render_template("ristoranti.html", ristoranti=ristoranti, categorie=categorie)


@app.route('/ristoranti/<int:IdRistorante>/prenota', methods=['GET', 'POST'])
@login_required
def ristorante_detailed(IdRistorante):
    ristorante = Ristorante.query.get(IdRistorante)
    recensioni = Recensione.query.join(User).filter(User.username == Recensione.Autore_recensione).filter(
        Recensione.Ristorante_Rec == IdRistorante).all()

    if request.method == 'POST':
        data = request.form.get('Data_prenotazione')
        ora = request.form.get('Orario')
        num_posti = request.form.get('NumPosti')

        if data and ora and num_posti:
            # Verifica se ci sono tavoli disponibili
            num_posti = int(num_posti)
            tavoli_disponibili = []
            for tavolo in ristorante.tavoli:
                if tavolo.disponibile(data, ora) and tavolo.NumPosti >= num_posti:
                    tavoli_disponibili.append(tavolo)

            if tavoli_disponibili:
                # Mostra i tavoli disponibili
                return render_template('tavoli_disponibili.html', tavoli=tavoli_disponibili, IdRistorante=IdRistorante, data=data, ora=ora)

            # Nessun tavolo disponibile
            flash('Non ci sono tavoli disponibili per questa prenotazione. Si prega di selezionare una data diversa o un altro orario.')
        else:
            # Salvare la recensione
            titolo = request.form.get('titolo')
            descrizione = request.form.get('descrizione')
            voto = request.form.get('voto')

            if voto:
                recensione = Recensione(Titolo=titolo, Descrizione=descrizione, Voto=voto, Autore_recensione=current_user.username,Ristorante_Rec=ristorante.IdRistorante)
                db.session.add(recensione)
                db.session.commit()




                # Aggiornare la lista delle recensioni
                recensioni =  Recensione.query.join(User).filter(User.username == Recensione.Autore_recensione).filter(Recensione.Ristorante_Rec == IdRistorante).all()


            else:
                flash('Per favore, completa tutti i campi della recensione.')

        return redirect(url_for('ristorante_detailed', IdRistorante=IdRistorante))

    return render_template('ristorante_dettagli.html', ristorante=ristorante, recensioni=recensioni)


@app.route('/ristoranti/<int:IdRistorante>/prenota/confirm/<string:data>/<string:ora>', methods=['POST'])
@login_required

def prenota_confirm(IdRistorante,data,ora):

  if request.method == 'POST':

    num_tavolo = int(request.form.get('NumTavolo'))



    ora_iniziale = datetime.strptime(ora, '%H:%M')
    ora_fine = ora_iniziale + timedelta(hours=2)


    prenotazione = Prenota(Data_prenotazione=data, Orario=ora, Num_Tavolo=num_tavolo,Username_profilo=current_user.username,ora_fine=ora_fine.strftime('%H:%M'))
    db.session.add(prenotazione)
    db.session.commit()

    # Aggiorna lo stato del tavolo nel database
    db.session.execute("UPDATE tavolo SET Disponibile = 0 WHERE NumTavolo = :num_tavolo", {"num_tavolo": num_tavolo})
    db.session.commit()

    flash("Prenotazione effettuata con successo")
    return redirect(url_for('fudy'))


app.secret_key = '392741'


