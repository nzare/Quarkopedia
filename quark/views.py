from django.shortcuts import render,redirect
from django.http import HttpResponse
import pyrebase
from django.contrib import auth
from collections import OrderedDict
from authy.api import AuthyApiClient
from django.conf import settings
config = {
	
	'apiKey': "*****************************",
        'authDomain': "quark-o-pedia.firebaseapp.com",
        'databaseURL': "https://quark-o-pedia.firebaseio.com",
        'projectId': "quark-o-pedia",
        'storageBucket': "quark-o-pedia.appspot.com",
        'messagingSenderId': "794989305019"
  }

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
database = firebase.database()
authy_api= AuthyApiClient("8x9UksoV9DMM6T1fzMD1tFxayRLrkQnX"
)
DEFAULT_BAL = 1000000

def signIn(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        passw = request.POST.get('pass')
        try:
            user = auth.sign_in_with_email_and_password(email,passw)
        except:
            message="invalid credentials"
            return render(request,"signIn.html",{"message":message})

        #print(user['idToken'])
        user = auth.refresh(user['refreshToken'])
        global session_id 
        session_id = user['idToken']
        print(auth.get_account_info(user['idToken']))
        request.session['uid']=str(session_id)
        return redirect('profile')

    return render(request, 'signIn.html')

def profile(request):
    if request.session['uid'] == str(session_id):
        idtoken= request.session['uid']
        a = auth.get_account_info(idtoken)
        a = a['users']
        a = a[0]
        a = a['localId']
        e = database.child("users").child(a).child("email").get().val()
        n = database.child("users").child(a).child("name").get().val()
        g = database.child("users").child(a).child("gender").get().val()
        p = database.child("users").child(a).child("phone").get().val()
        c = database.child("users").child(a).child("college").get().val()
        r = database.child("users").child(a).child("rank").get().val()
        ac = database.child("users").child(a).child("accBal").get().val()
        city = database.child("users").child(a).child("city").get().val()
        return render(request,'profile.html',{"e":e,"n":n,"g":g,"p":p,"c":c,"r":r,"ac":ac,"city":city})
        

    return render (request, 'homepage.html')

def home(request):
	return render(request, 'homepage.html', {"e":'sukdik'})

def news(request):
    newslist = []
    news = database.child("news").get()
    for i in news.each():
        newslist.append(i.val())
    return render(request, 'news.html', {'newsList': newslist })
def base(request):
    
    return render(request, 'base.html')

def ranking(request):
    ranklist = []
    new_ranklist=[]
    rank = database.child("users").get()
    for i in rank.each():
        balance=database.child("users").child(str(i.key())).get().val()['accBal']
        name_user=database.child("users").child(str(i.key())).get().val()['name']
        ranklist.append({'name_user':name_user,'accBal':accBal})
        new_ranklist=OrderedDict(sorted(ranklist.items()))
    return render(request, 'ranking.html', {'new_ranklist': new_ranklist })

def signOut(request):
    del request.session['uid']
    return render(request,'signOut.html')

def signUp(request):
    global uid
    if request.method == 'POST':
        name=request.POST.get('name')
        email=request.POST.get('email')
        passw=request.POST.get('pass')
        conf_passw=request.POST.get('conf_pass')
        phone=request.POST.get('phone')
        college=request.POST.get('college')
        city=request.POST.get('city')
        print(passw)
        print(conf_passw)

        if passw!=conf_passw:
            message="Password does not match"
            return render(request,'signUp.html',{"message":message})
        elif len(passw)<6:
            message="Password Should be min 6 charachters long"
            return render(request,'signUp.html',{"message":message})
        else:
            emailDB = database.child("users").get()
            for i in emailDB.each():
                temp2 = i.val()
                if email==temp2['email']:
                    message="Email Already Exists"
                    return render(request,'signUp.html',{"message":message})
                             
            if "@goa.bits-pilani.ac.in" in email:
                user=auth.create_user_with_email_and_password(email,passw)
                uid = user['localId']
                data={'name':name,'email':email,'phone': phone, 'college':college,'city':city,'accBal': DEFAULT_BAL, 'rank': 0,'user_verify':"Yes",'userVal':DEFAULT_BAL}
                database.child("users").child(uid).set(data)
                auth.send_email_verification(user['idToken'])
                return render(request,"thankyou.html")
            else:
                phnum = database.child("users").get()
                for i in phnum.each():
                    temp=i.val()
                    if phone==temp['phone']:
                        message="Phone Number Already Exists"
                        return render(request,'signUp.html', {"message":message})

                user=auth.create_user_with_email_and_password(email,passw)
                uid = user['localId']
                data={'name':name,'email':email,'phone': phone, 'college':college,'city':city,'accBal': DEFAULT_BAL, 'rank': 0,'user_verify':"No",'userVal':DEFAULT_BAL}
                database.child("users").child(uid).set(data)
                auth.send_email_verification(user['idToken'])
                return render(request,"verification.html")
        message="could not create account"
        return render(request,'signUp.html', {"message":message})

            
        
        
        	

    return render(request,"signUp.html")

def portfolio(request):
    stocksList = [] #list of dictionaries of each individual stock
    stocks = database.child("users").child("uid1").child("purchasedStocks").get() #replace uid1 with actual user's uid
    
    for i in stocks.each():
        #temp is a dictionary
        #stocksList is a list of dictionaries
        price = database.child("stocks").child( str(i.key()) ).get().val()['currPrice'] 
        temp = i.val()
        pPrice = temp['purchasedPrice']
        pPrice = (pPrice - price)/price
        temp.update({ 'change':  pPrice })
        stocksList.append(temp)

    return render(request, 'portfolio.html', { 'purchasedStocksList' : stocksList })
def verification(request):
    if request.method == 'POST':
        global ph
        ph = request.POST.get('ph')
        request.session['phone_number']=ph
        authy_api.phones.verification_start (
                ph,"91","sms"
        )
        return render(request,'otp.html')
    return render(request,'verification.html' )
        

def otp(request): 
    global ph
    global uid
    if request.method == 'POST':
        otp= request.POST.get('otp')
        request.session['otp']=otp
        print(otp)
        verification= authy_api.phones.verification_check (

            ph,"91",otp

        )
        if verification.ok():
            request.session['isverified']=True
            message="otp verified"
            database.child("users").child(uid).update({'user_verify' :'Yes'})
            return render(request,'thankyou.html')
        else:       
            return render(request,'otp.html')      
    return render(request,'otp.html')           
def thankyou(request):
    return render(request,'thankyou.html')   
def About(request):
    return render(request,'About.html')   
