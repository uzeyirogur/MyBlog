from flask import Flask , render_template , flash , redirect , url_for , session , logging , request 
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators        #tabloda ki özellikler için gerekli
from passlib.hash import sha256_crypt
from functools import wraps 

#KULLANICI GİRİŞ DECRATOR'I
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session :                        # bu koşulun true dönmesi kullanıcı giriş yaptı demek nerede kullanılmışsa o sayfaya gider
            return f(*args, **kwargs) 
        else :                                                                          #else durumu giriş yapmamış demek giriş yapmaya zorlar
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın...","danger")
            return redirect(url_for("login"))
    return decorated_function

#KULLANICI KAYIT FORMU WTFFORMS İLE 
class RegisterForm(Form) :
    name = StringField("Ad Soyad : " , validators = [validators.Length(min = 5 , max = 25) , validators.DataRequired(message = "Lütfen bu alanı doldurunuz.")])
    username = StringField("Kullanıcı Adı : " , validators = [validators.Length(min = 6 , max = 20) , validators.DataRequired(message = "Lütfen bu alanı doldurunuz.")])
    email = StringField("E-mail : " , validators = [validators.Email(message = "Lütfen geçerli bir email adresi giriniz"),validators.DataRequired(message = "Lütfen bu alanı doldurunuz.")])
    password = PasswordField("Şifre : " , validators = [
        validators.Length(min = 6 , max = 15) ,
        validators.DataRequired("Lütfen bu alanı doldurunuz. "),
        validators.EqualTo(fieldname = "confirm_password", message = "Parolalar uyuşmuyor" )])
    coding_language = StringField("Çalıştığınız Kodlama Dili : ") 
    confirm_password = PasswordField("Parola Doğrula : ")

#LOGİN FORMU 
class LoginForm(Form) :
    username = StringField("Kullanıcı adı :")
    password = PasswordField("Şifre : ")

app = Flask(__name__)
app.secret_key = "uzoblog"                #flash mesajları için secret_key şart yoksa çalışmaz!!!!
#MYSQL VERİTABANI BİLGİLERİMİZ
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "uzoblogg"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

myqsl = MySQL(app)




@app.route("/")
def homepage() :
    return render_template("homepages2.html")

@app.route("/aboutme")
def aboutme() :
    return render_template("aboutme2.html")


@app.route("/myschoollife")
def myschoollife() :
    return render_template("myschoollife2.html")


@app.route("/messages")
def message() :
    return render_template("message.html")

@app.route("/dashboard")
@login_required                                          #yukarıdaki giriş yapılmış mı kontrolü yapan decorator
def dashboard() :
    cursor = myqsl.connection.cursor()
    sorgu = "Select * from articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0 :
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else : 
        return render_template("dashboard.html")

#KAYIT OLMA SAYFASI
@app.route("/register",methods = ["GET","POST"] )
def register() :
    formm = RegisterForm(request.form)                    #form adında RegisterForm dan bir obje oluşturduk burada kullanabilmek için içine request.form yazdık (objeyle tamamen farklı şeyler)
                                                          #request.form yazdık çünkü sayfamıza post reuquest atılmışsa bütün bilgiler RegisterFormdaki değişkenlere atanıcak
    
    if  request.method == "POST" and formm.validate():
        name = formm.name.data 
        username = formm.username.data
        email = formm.email.data
        password = sha256_crypt.encrypt(formm.password.data)
        coding_language = formm.coding_language.data

        cursor = myqsl.connection.cursor()
        sorgu = "Insert into student(name,username,email,password,coding_language) VALUES(%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password,coding_language))
        myqsl.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))              #redirect yönlendirmek demek istediğimiz sayfaya kayıt olduktan sonra atıyor bizi url_for ise o gitmek istediğimiz sayfanın içindeki fonksiyonu yazıyoruz
    else :
        return render_template("register.html",form = formm)

#Login İşlemi
@app.route("/login",methods = ["GET","POST"])
def login() :
    loginform = LoginForm(request.form)
    if request.method == "POST" :
        username = loginform.username.data
        password = loginform.password.data 

        cursor = myqsl.connection.cursor()
        sorgu = "Select * From student where username = %s"
        
        result = cursor.execute(sorgu,(username,))
        
        if result > 0 :
            data = cursor.fetchone()    #sql in veriyi al fonk bütün verileri alır email dil vb ne varsa
            real_password = data["password"]      #tablodaki passwordu alıp real_passworda atadık şimdi aşağıda kullanıcnın giriş yap ekranındaki parolayla kıyaslıcaz doğru mu diye
            if sha256_crypt.verify(password,real_password) : #burda aynı mı diye bakıyoruz fakat verify fonk kullanma amacımız listemize biz güvenlik sebebiyle şifreli almıştık ve bunu eski haline getirip karşılaştırıyoruz ama biz yine görmüyoruz tabiki
                flash("Giriş Başarılı...","success")

                session["logged_in"] = True            #session giriş yaptıktan sonra oturumun açık kalması için önemli ve buna bir anahtar kelime verdik = logged_in
                session["username"] = username         #giriş yaptıktan sonraki kullancı değeri için 

                return redirect(url_for("homepage"))
            else :
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else :
            flash("Böyle bir kullanıcı yok...","danger")
            return redirect(url_for("login"))


    return render_template("login.html" , form = loginform)

#Logout işlemi
@app.route("/logout")            
def logout() :                                                       #burada logout sayfasını oluşturduk çıkış yapa bastığımız az session temizlenicek ve giriş yap butonu çıkıcak
    session.clear()
    return redirect(url_for("homepage"))

#makale sayfasını oluşturma
@app.route("/articles")
def articles() :
    cursor = myqsl.connection.cursor()
    sorgu = "Select * from articles"
    result = cursor.execute(sorgu)
    if result > 0 :
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    
    else :
        return render_template("articles.html")

#Makale Ekleme işlemi
@app.route("/addarticle",methods = ["GET","POST"])
def article() :
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = myqsl.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        myqsl.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html" , form = form)

#MAKALE SİLME 
@app.route("/deletearticle/<string:id>")
@login_required
def delete(id) :
    cursor = myqsl.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0 :
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        myqsl.connection.commit()
        return redirect(url_for("dashboard"))
    else :
        flash("Böyle bir makale yok veya böyle bir makaleyi silme yetkiniz yok","danger")
        return redirect(url_for("homepage"))

#MAKALE GÜNCELLEME
@app.route("/editarticle/<string:id>",methods = ["GET","POST"])
@login_required
def update(id) :
    if request.method == "GET" :
        cursor = myqsl.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0 :
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("homepage"))
        else :
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form )
    else :
        #POST REQUEST KISMI
        form = ArticleForm(request.form)

        newtitle = form.title.data
        newcontent = form.content.data

        sorgu2 ="Update articles Set title = %s , content = %s where id = %s"
        cursor = myqsl.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        myqsl.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))


#MAKALE OLUŞTURMA FORMU
class ArticleForm(Form) :
    title = StringField("Makale Başlığı")
    content = TextAreaField("Makale İçeriği" , validators = [validators.Length(min = 10)] )                 #textareafield yaptık büyük alan gerekiyor çünki makale yazmak için

#Makale Detay Sayfası
@app.route("/article/<string:id>")
def detailarticle(id) :
    cursor = myqsl.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0 :
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else :
        return render_template("article.html")

#MAKALE ARAMA 
@app.route("/search",methods = ["GET","POST"])
def search() :
    if request.method == "GET" :
        return redirect(url_for("homepage"))
    else : 
        keyword = request.form.get("keyword")
        cursor = myqsl.connection.cursor()
        sorgu3 = "Select * from articles where title like '%"+ keyword +"%'"              #bu sorgu searche yazdığımız kelimeyi bulmaya yarıyor title larda 
        result = cursor.execute(sorgu3)

        if result == 0 :
            flash("Aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else :
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)
if __name__ == "__main__" :
    app.run(debug=True)

