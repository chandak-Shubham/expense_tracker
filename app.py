from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2

app = Flask(__name__)

app.secret_key = "splitwise"




def get_db():

    connection = psycopg2.connect(
        dbname="splitwise_clone",
        user="postgres",
        password="root",
        host="localhost",
        port="5432"
    )

    return connection


@app.route("/")
def home():

    return render_template("index.html")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(
        """
        INSERT INTO users(
        user_name,
        user_email,
        user_password
        )
        VALUES(%s,%s,%s)
        """,
        (name, email, password)
        )

        connection.commit()
        cursor.close()
        connection.close()
        return "Account Created"
    
    return render_template("signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
    
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(
        """
        SELECT user_id, user_name FROM users
        WHERE user_email=%s
        AND user_password=%s
        """,
        (email, password)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            session["user_id"]=user[0]
            session["user_name"]=user[1]
            return redirect(
                url_for(
                    "dashboard"
                )
            )
        return "Invalid Credentials"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    connection=get_db()
    cursor=connection.cursor()
    cursor.execute(
    """
    SELECT u.user_email FROM friends f
    JOIN users u 
    ON
    u.user_id=
    CASE
    WHEN f.user1_id=%s
    THEN f.user2_id
    ELSE f.user1_id
    END

    WHERE

    f.user1_id=%s
    OR
    f.user2_id=%s
    """,




    (

    session["user_id"],

    session["user_id"],

    session["user_id"]

    )

    )

    friends=cursor.fetchall()

    cursor.close()

    connection.close()

    return render_template(

    "dashboard.html",

    friends=friends

    )
# ---------------- ADD FRIEND ----------------

@app.route("/add_friend", methods=["GET", "POST"])
def add_friend():

    if request.method=="POST":

        friend_email=request.form["email"]

        connection=get_db()

        cursor=connection.cursor()


        # check user exists

        cursor.execute(
        """
        SELECT
        user_id

        FROM users

        WHERE user_email=%s
        """,

        (friend_email,)
        )

        friend=cursor.fetchone()


        if not friend:

            cursor.close()

            connection.close()

            return "User Not Found"



        # cannot add yourself

        if friend[0]==session["user_id"]:

            cursor.close()

            connection.close()

            return "Cannot Add Yourself"



        # already friend check

        cursor.execute(
        """
        SELECT *

        FROM friends

        WHERE

        (
        user1_id=%s
        AND
        user2_id=%s
        )

        OR

        (
        user1_id=%s
        AND
        user2_id=%s
        )
        """,

        (

        session["user_id"],
        friend[0],

        friend[0],
        session["user_id"]

        )

        )

        already=cursor.fetchone()



        if already:

            cursor.close()

            connection.close()

            return "Already Friends"



        # insert friendship

        cursor.execute(
        """
        INSERT INTO friends(

        user1_id,
        user2_id

        )

        VALUES(

        %s,
        %s

        )
        """,

        (

        session["user_id"],
        friend[0]

        )

        )

        connection.commit()

        cursor.close()

        connection.close()

        return "Friend Added Successfully"


    return render_template(
        "add_friend.html"
    )


# ---------------- ADD EXPENSE ----------------

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    connection=get_db()

    cursor=connection.cursor()


    # ---------------- GET ----------------

    cursor.execute(
    """
    SELECT

    u.user_email

    FROM friends f

    JOIN users u

    ON

    u.user_id=

    CASE

    WHEN f.user1_id=%s

    THEN f.user2_id

    ELSE f.user1_id

    END

    WHERE

    f.user1_id=%s

    OR

    f.user2_id=%s
    """,

    (

    session["user_id"],

    session["user_id"],

    session["user_id"]

    )

    )

    rows=cursor.fetchall()

    friends=[]

    for row in rows:

        friends.append(
            row[0]
        )


    # ---------------- POST ----------------

    if request.method=="POST":

        description=request.form["description"]

        amount=float(
            request.form["amount"]
        )

        friend_email=request.form["friend_email"]


        cursor.execute(
        """
        SELECT

        user_id

        FROM users

        WHERE user_email=%s
        """,

        (
            friend_email,
        )

        )

        friend=cursor.fetchone()


        if not friend:

            cursor.close()

            connection.close()

            return "Friend Not Found"


        split=amount/2


        cursor.execute(
        """
        INSERT INTO expenses(

        description,
        total_amount,
        created_by

        )

        VALUES(

        %s,
        %s,
        %s

        )

        RETURNING expense_id
        """,

        (

        description,

        amount,

        session["user_id"]

        )

        )

        expense_id=cursor.fetchone()[0]


        cursor.execute(
        """
        INSERT INTO expense_details(

        expense_id,
        user_id,
        paid_amount,
        owed_amount

        )

        VALUES

        (%s,%s,%s,%s),

        (%s,%s,%s,%s)
        """,

        (

        expense_id,
        session["user_id"],
        amount,
        split,

        expense_id,
        friend[0],
        0,
        split

        )

        )

        connection.commit()

        cursor.close()

        connection.close()

        return "Expense Added"


    cursor.close()

    connection.close()

    return render_template(
        "add_expense.html",

        friends=friends
    )


# ---------------- BALANCES ----------------

@app.route("/balances")
def balances():

    connection=get_db()

    cursor=connection.cursor()

    cursor.execute(
    """
    SELECT

    payer.user_name,

    borrower.user_name,

    ed2.owed_amount

    FROM expenses e

    JOIN users payer
    ON payer.user_id=e.created_by

    JOIN expense_details ed2
    ON e.expense_id=ed2.expense_id

    JOIN users borrower
    ON borrower.user_id=ed2.user_id

    WHERE borrower.user_id!=payer.user_id
    """
    )

    rows=cursor.fetchall()

    cursor.close()

    connection.close()

    balances={}

    me=session["user_name"]

    for row in rows:

        payer=row[0]
        borrower=row[1]
        amount=row[2]

        if me==payer:

            balances[borrower]=(
                balances.get(
                    borrower,
                    0
                )+amount
            )

        elif me==borrower:

            balances[payer]=(
                balances.get(
                    payer,
                    0
                )-amount
            )

    messages=[]

    for person,value in balances.items():

        if value>0:

            messages.append(
                f"{person} needs to pay you ₹{value}"
            )

        elif value<0:

            messages.append(
                f"You need to pay {person} ₹{-value}"
            )

        else:

            messages.append(
                f"Settled with {person}"
            )

    return render_template(
        "balances.html",

        messages=messages
    )
    


if __name__ == "__main__":
    app.run(debug=True)