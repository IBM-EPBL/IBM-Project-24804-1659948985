from flask import Blueprint, render_template, request, redirect, session, url_for
import hashlib
import re
from flask_login import login_required, login_user, logout_user
import ibm_db
import uuid
from datetime import date
from .model import Customer, Agent, Admin

views = Blueprint("blue_print", __name__)
email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
pass_regex = r"^[A-Za-z0-9_-]*$"

customer = Customer()
agent = Agent()
admin = Admin()

conn = ibm_db.connect('DATABASE=bludb;HOSTNAME=815fa4db-dc03-4c70-869a-a9cc13f33084.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30367;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=mxx40464;PWD=9xoG1eDiCcNIrouX', '', '')


@views.route('/logout')
@login_required
def logout():
    session.pop('LOGGED_IN_AS')
    logout_user()

    return redirect(url_for('blue_print.login'))

@views.route('/', methods = ['GET', 'POST'])
@views.route('/login', methods = ['GET', 'POST'])
def login():
    # if method is POST
    if request.method == 'POST':
        # getting the data entered by the user 
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role-check')

        msg = ""
        to_show = False

        # validating the inputs entered by the user
        if(not (re.fullmatch(email_regex, email))):
            msg = "Enter a valid email"
            to_show = True

        elif (len(password) < 8):
            msg = "Password must be atleast 8 characters long!"
            to_show = True

        # Admin login
        if email == "admin.ccr@gmail.com":
            if password == "admin.ccr@2022":
                # initialising admin object
                admin.set(email, password)

                session.permanent = False
                session['LOGGED_IN_AS'] = "ADMIN"                            
                login_user(admin, remember=True)
                
                return redirect(url_for('admin.tickets'))

            else:
                to_show = True
                password = ""
                msg = "Invalid password!"

        # Customer or Agent
        else:
            if to_show:
                # there is something fishy with the user's inputs
                password = ""

            elif (not to_show):
                # the user's inputs are valid
                # checking if the login credentials are valid
                if role == "Customer":
                    # checking if the entry of the mail entered is present in the database
                    mail_check_query = "SELECT * FROM customer WHERE email = ?"
                    stmt = ibm_db.prepare(conn, mail_check_query)
                    ibm_db.bind_param(stmt, 1, email)
                    ibm_db.execute(stmt)

                    account = ibm_db.fetch_assoc(stmt)

                    if account:
                        # valid customer
                        # i.e, mail is present in the database

                        # checking if the customer entered a valid password now
                        # encrypting the entered password
                        passcode = str(hashlib.sha256(password.encode()).hexdigest())

                        # now checking if the encrypted string is same as that of the one in database
                        if (account['PASSCODE'] == passcode):
                            msg = "Valid Login"
                            to_show = True

                            # creating a customer object
                            customer.set(
                                account['CUST_ID'],
                                account['FIRST_NAME'],
                                account['LAST_NAME'],
                                account['EMAIL'],
                                account['PASSCODE'],
                                account['DATE_JOINED']
                            )

                            session.permanent = False
                            session['LOGGED_IN_AS'] = "CUSTOMER"
                            login_user(customer, remember=True)

                            return redirect(url_for('customer.profile'))

                        else:
                            # customer entered invalid password
                            msg = "Invalid password"
                            password = ""
                            to_show = True

                    else:
                        # invalid customer
                        # i.e, entered mail is not present in the database
                        msg = "User does not exist"
                        email = ""
                        password = ""
                        to_show = True

                else:
                    # user is an Agent
                    # checking if the entry of the mail entered is present in the agent's table
                    mail_check_query = "SELECT * FROM agent WHERE email = ?"
                    stmt = ibm_db.prepare(conn, mail_check_query)
                    ibm_db.bind_param(stmt, 1, email)
                    ibm_db.execute(stmt)

                    account = ibm_db.fetch_assoc(stmt)

                    if account:
                        # the mail entered by the agent is in the database

                        # checking if the customer entered a valid password now
                        # encrypting the entered password
                        passcode = str(hashlib.sha256(password.encode()).hexdigest())

                        # now checking if this passcode is equal to that of the password in database
                        if(account['PASSCODE'] == passcode):
                            # valid password
                            msg = "Valid Login"
                            to_show = True

                            # initialising the agent object
                            agent.set(
                                account['AGENT_ID'],
                                account['FIRST_NAME'],
                                account['LAST_NAME'],
                                account['EMAIL'],
                                account['PASSCODE'],
                                account['DATE_JOINED'],
                                account['CONFIRMED']
                            )

                            session.permanent = False
                            session['LOGGED_IN_AS'] = "AGENT"
                            login_user(agent, remember=True)

                            if agent.confirm:
                                # the agent is confirmed by the admin
                                # so, re-directing the agent to his/her profile page
                                return redirect(url_for('agent.profile'))

                            else:
                                # the agent is not yet verified by the admin
                                # re-directing the agent to the agent no show page
                                return redirect(url_for('agent.no_show'))

                        else:
                            # invalid password
                            msg = "Invalid password"
                            password = ""
                            to_show = True

                    else:
                        # invalid agent 
                        # i.e, entered mail is not present in the database
                        msg = "Agent does not exist"
                        email = ""
                        password = ""
                        to_show = True

        return render_template(
            'login.html',
            to_show = to_show,
            message = msg,
            email = email,
            password = password
        )

    return render_template('login.html')

@views.route('/register', methods = ['GET', 'POST'])
def register():
    # if method is POST
    if request.method == 'POST':
        # getting all the data entered by the user
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role-check')

        msg = ""
        to_show = False

        # validating the inputs 
        if len(first_name) < 3:
            msg = "First Name must be atleast 3 characters long!"
            to_show = True

        elif len(last_name) < 1:
            msg = "Last Name must be atleast 1 characters long!"
            to_show = True

        elif(not (re.fullmatch(email_regex, email))):
            msg = "Please enter valid email"
            to_show = True

        elif((len(password) < 8) or (len(confirm_password) < 8)):
            msg = "Password must be atleast 8 characters long!"
            to_show = True

        elif (password != confirm_password):
            msg = "Passwords do not match"
            to_show = True

        elif (not (re.fullmatch(pass_regex, password))):
            msg = "Enter valid password"
            to_show = True

        if to_show:
            # there is something fishy with the inputs
            password = confirm_password = ""

        # by here the inputs are validated, because to_show is False
        # registering the user / agent with the database
        elif (not to_show):
            if role == "Customer":
                # the user is a Customer
                # checking whether the user with the same email already there
                check_mail_query = "SELECT * FROM customer WHERE email = ?"
                stmt = ibm_db.prepare(conn, check_mail_query)
                ibm_db.bind_param(stmt, 1, email)
                ibm_db.execute(stmt)

                account = ibm_db.fetch_assoc(stmt)

                if account:
                    # user already exists
                    msg = "Email already exists!"
                    email = ""
                    password = ""
                    confirm_password = ""
                    to_show = True

                else:
                    # new customer
                    # adding the customer details to the detabase
                    user_insert_query ='''INSERT INTO customer
                            (cust_id, first_name, last_name, email, passcode, date_joined,role) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)'''

                    # creating a UUID for the customer
                    user_uuid = str(uuid.uuid4())

                    # encrypting the customer's password using SHA-256
                    passcode = str(hashlib.sha256(password.encode()).hexdigest())
                    date_joined = date.today()

                    try:
                        stmt = ibm_db.prepare(conn, user_insert_query)
                        ibm_db.bind_param(stmt, 1, user_uuid)
                        ibm_db.bind_param(stmt, 2, first_name)
                        ibm_db.bind_param(stmt, 3, last_name)
                        ibm_db.bind_param(stmt, 4, email)
                        ibm_db.bind_param(stmt, 5, passcode)
                        ibm_db.bind_param(stmt, 6, date_joined)
                        ibm_db.bind_param(stmt, 7, role)
                        ibm_db.execute(stmt)

                        # redirecting the customer to the login page
                        msg = "Account created. Please Login!"
                        to_show = True

                        return render_template('login.html', message = msg, to_show = to_show)

                    except:
                        msg = "Something went wrong!"
                        to_show = True
                
            else:
                # the role is Agent
                # checking whether the user with the same email already there
                check_mail_query = "SELECT * FROM agent WHERE email = ?"
                stmt = ibm_db.prepare(conn, check_mail_query)
                ibm_db.bind_param(stmt, 1, email)
                ibm_db.execute(stmt)

                account = ibm_db.fetch_assoc(stmt)

                if account:
                    # means an agent with the email exists already!
                    msg = "Email already exists!"
                    email = ""
                    password = ""
                    confirm_password = ""
                    to_show = True

                else:
                    # new Agent
                    # adding the customer details to the detabase
                    agent_input_query = '''
                        INSERT INTO agent 
                        (agent_id, first_name, last_name, email, passcode, date_joined, confirmed)
                        VALUES (?, ?, ?, ?, ?, ?, ?) 
                    '''

                    # creating a unique id for the agent
                    agent_id = str(uuid.uuid4())
                    date_joined = date.today()
                    confirmed = False

                    # encrypting the agent's password with SHA-256
                    passcode = str(hashlib.sha256(password.encode()).hexdigest())

                    try:
                        stmt = ibm_db.prepare(conn, agent_input_query)
                        
                        ibm_db.bind_param(stmt, 1, agent_id)
                        ibm_db.bind_param(stmt, 2, first_name)
                        ibm_db.bind_param(stmt, 3, last_name)
                        ibm_db.bind_param(stmt, 4, email)
                        ibm_db.bind_param(stmt, 5, passcode)
                        ibm_db.bind_param(stmt, 6, date_joined)
                        ibm_db.bind_param(stmt, 7, confirmed)

                        ibm_db.execute(stmt)

                        msg = "Account created! Please login"
                        to_show = True

                        # re-directing the agent to the login page
                        return render_template('login.html', message = msg, to_show = to_show)

                    except:
                        msg = "Something went wrong!"
                        to_show = True

        return render_template(
            'register.html',
            to_show = to_show,
            message = msg,
            first_name = first_name,
            last_name = last_name,
            email = email,
            password = password,
            confirm_password = confirm_password,
            role = role
        )
    
    return render_template('register.html')

