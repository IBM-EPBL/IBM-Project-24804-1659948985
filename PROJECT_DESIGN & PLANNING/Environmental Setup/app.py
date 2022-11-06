from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, Welcome to IBM Project</p>"


@app.route("/home")
def home():
    return "<p><b>Welcome to Customer Care Registry Project!!!</b></p><p>Team members: <br>Pradeep B<br>Navin S<br>Naveen Kumar C<br>Mohammed Asshar<br><p>>"


@app.route("/about")
def aboutus():
    return "<p>CUSTOMER CARE REGISTRY</p><p>This Application has been developed to help the customer in processing their complaints. <br>The customers can raise the ticket with a detailed description of the issue. <br>An Agent will be assigned to the Customer to solve the problem. <br>Whenever the agent is assigned to a customer they will be notified with an email alert. <br>Customers can view the status of the ticket till the service is provided.</p>"

