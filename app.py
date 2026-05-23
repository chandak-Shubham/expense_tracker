from unicodedata import name

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
        
        return redirect(url_for("dashboard"))
    
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
        SELECT user_id FROM users
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
            return redirect(url_for("dashboard")
            )
        return "Invalid Credentials"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    connection=get_db()
    cursor=connection.cursor()
    cursor.execute(
    """
    SELECT u.user_email 
    FROM friends f JOIN users u 
    ON
    u.user_id=
    CASE
    WHEN f.user1_id=%s THEN f.user2_id ELSE f.user1_id
    END
    WHERE f.user1_id=%s OR f.user2_id=%s
    """,
    (session["user_id"], session["user_id"], session["user_id"])
    )
    friends=cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("dashboard.html",friends=friends)
# ---------------- ADD FRIEND ----------------

@app.route("/add_friend", methods=["GET", "POST"])
def add_friend():

    if request.method=="POST":
        friend_email=request.form["email"]

        connection=get_db()
        cursor=connection.cursor()
        cursor.execute(
        """
        SELECT user_id FROM users
        WHERE user_email=%s
        """,
        (friend_email,)
        )
        friend=cursor.fetchone()

        if not friend:
            cursor.close()
            connection.close()
            return "User Not Found"

        if friend[0]==session["user_id"]:
            cursor.close()
            connection.close()
            return "Cannot Add Yourself"

        cursor.execute(
        """
        SELECT * FROM friends
        WHERE (user1_id=%s AND user2_id=%s) OR (user1_id=%s AND user2_id=%s)
        """,
        (session["user_id"],friend[0],friend[0],session["user_id"])
        )

        already=cursor.fetchone()
        if already:
            cursor.close()
            connection.close()
            return "Already Friends"

        cursor.execute(
        """
        INSERT INTO friends(user1_id,user2_id)
        VALUES(%s,%s)
        """,
        (session["user_id"],friend[0])
        )

        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for("dashboard"))
    return render_template("add_friend.html")


# ---------------- ADD EXPENSE ----------------

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    connection=get_db()
    cursor=connection.cursor()
    cursor.execute(
    """
    SELECT u.user_email FROM friends f
    JOIN users u ON
    u.user_id=
    CASE
    WHEN f.user1_id=%s THEN f.user2_id
    ELSE f.user1_id
    END
    WHERE f.user1_id=%s OR f.user2_id=%s
    """,
    (session["user_id"],session["user_id"],session["user_id"])
    )

    rows=cursor.fetchall()
    friends=[]
    for row in rows:
        friends.append(
            row[0]
        )

    if request.method=="POST":
        description=request.form["description"]
        amount=float(request.form["amount"])
        split_type=request.form["split_type"]
        friend_email=request.form["friend_email"]

        cursor.execute(
        """
        SELECT user_id FROM users
        WHERE user_email=%s
        """,
        (friend_email,)
        )

        friend=cursor.fetchone()


        if not friend:
            cursor.close()
            connection.close()
            return "Friend Not Found"


        if split_type=="equal":
            my_share=amount/2
            friend_share=amount/2
        else:
            my_share=0
            friend_share=amount


        cursor.execute(
        """
        INSERT INTO expenses(description,total_amount,created_by)
        VALUES(%s,%s,%s)
        RETURNING expense_id
        """,
        (description,amount,session["user_id"])
        )

        expense_id=cursor.fetchone()[0]
        cursor.execute(
        """
        INSERT INTO expense_details(expense_id,user_id,paid_amount,owed_amount)
        VALUES(%s,%s,%s,%s),(%s,%s,%s,%s)
        """,
        (
        expense_id,
        session["user_id"],
        amount,
        my_share,

        expense_id,
        friend[0],
        0,
        friend_share
        )
        )

        connection.commit()
        cursor.close()
        connection.close()
        return "Expense Added"

    cursor.close()
    connection.close()
    return render_template("add_expense.html",friends=friends)


# ---------------- BALANCES ----------------

@app.route("/balances")
def balances():

    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(
    """
    SELECT payer.user_id,payer.user_name,borrower.user_id,borrower.user_name,ed2.owed_amount FROM expenses e
    JOIN users payer ON payer.user_id=e.created_by
    JOIN expense_details ed2 ON e.expense_id=ed2.expense_id
    JOIN users borrower ON borrower.user_id=ed2.user_id
    WHERE borrower.user_id!=payer.user_id
    """
    )

    rows=cursor.fetchall()
    cursor.close()
    connection.close()

    balances={}
    me=session["user_id"]
    for row in rows:
        payer_id=row[0]
        payer_name=row[1]
        borrower_id=row[2]
        borrower_name=row[3]
        amount=row[4]

        if me==payer_id: 
            balances[borrower_name]=(balances.get(borrower_name,0)+amount)

        elif me==borrower_id:
            balances[payer_name]=(balances.get(payer_name,0)-amount)

    messages=[]
    for person,value in balances.items():
        if value>0:
            messages.append(f"{person} needs to pay you ₹{value}")
        elif value<0:
            messages.append(f"You need to pay {person} ₹{-value}")
        else:
            messages.append(f"Settled with {person}")

    return render_template("balances.html",messages=messages)

@app.route("/history/<friend_email>")
def history(friend_email):

    connection=get_db()

    cursor=connection.cursor()


    # GET FRIEND ID

    cursor.execute(
    """
    SELECT user_id

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

        return "Friend not found"


    friend_id=friend[0]



    # GET ONLY HISTORY BETWEEN YOU AND FRIEND

    cursor.execute(
    """
    SELECT

    e.created_by,

    creator.user_name,

    ed.owed_amount,

    e.description


    FROM expenses e


    JOIN expense_details ed

    ON
    e.expense_id=ed.expense_id


    JOIN users creator

    ON
    creator.user_id=e.created_by


    WHERE


    (

    e.created_by=%s

    AND

    ed.user_id=%s

    )


    OR


    (

    e.created_by=%s

    AND

    ed.user_id=%s

    )


    ORDER BY

    e.expense_id DESC

    """,

    (

    session["user_id"],
    friend_id,

    friend_id,
    session["user_id"]

    )

    )


    rows=cursor.fetchall()


    cursor.close()

    connection.close()



    history=[]


    for row in rows:

        creator=row[0]

        name=row[1]

        amount=row[2]

        desc=row[3]


        if creator==session["user_id"]:

            history.append(

                f"{friend_email.split('@')[0]} owes you ₹{amount:.2f} ({desc})"

            )


        else:

            history.append(

                f"You owe {name} ₹{amount:.2f} ({desc})"

            )



    return render_template(

        "history.html",

        history=history

    )

if __name__ == "__main__":
    app.run(debug=True)