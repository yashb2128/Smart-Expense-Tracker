from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)


def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    connection = get_db_connection()

    expenses = connection.execute(
        "SELECT * FROM expenses ORDER BY date DESC, id DESC"
    ).fetchall()

    total = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses"
    ).fetchone()[0]

    today = date.today().isoformat()

    today_total = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?",
        (today,)
    ).fetchone()[0]

    count = connection.execute(
        "SELECT COUNT(*) FROM expenses"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        today_total=today_total,
        count=count,
        today=today
    )


@app.route("/api/category-data")
def category_data():
    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()

    connection.close()

    data = []

    for row in rows:
        data.append({
            "category": row["category"],
            "total": row["total"]
        })

    return jsonify(data)


@app.route("/api/monthly-data")
def monthly_data():
    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            strftime('%Y-%m', date) AS month,
            SUM(amount) AS total
        FROM expenses
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()

    connection.close()

    data = []

    for row in rows:
        data.append({
            "month": row["month"],
            "total": row["total"]
        })

    return jsonify(data)


@app.route("/add", methods=["POST"])
def add_expense():

    try:
        amount = float(request.form["amount"])
    except (ValueError, TypeError):
        return redirect("/")

    category = request.form["category"].strip()
    description = request.form["description"].strip()
    expense_date = request.form["date"]

    allowed_categories = [
        "Food",
        "Travel",
        "Shopping",
        "Bills",
        "Education",
        "Entertainment",
        "Healthcare",
        "Other"
    ]

    if amount <= 0:
        return redirect("/")

    if category not in allowed_categories:
        return redirect("/")

    if not description:
        return redirect("/")

    if not expense_date:
        return redirect("/")

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO expenses (amount, category, description, date)
        VALUES (?, ?, ?, ?)
        """,
        (amount, category, description, expense_date)
    )

    connection.commit()
    connection.close()

    return redirect("/")


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/")


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    connection = get_db_connection()

    if request.method == "POST":

        try:
            amount = float(request.form["amount"])
        except (ValueError, TypeError):
            connection.close()
            return redirect("/")

        category = request.form["category"].strip()
        description = request.form["description"].strip()
        expense_date = request.form["date"]

        allowed_categories = [
            "Food",
            "Travel",
            "Shopping",
            "Bills",
            "Education",
            "Entertainment",
            "Healthcare",
            "Other"
        ]

        if amount <= 0:
            connection.close()
            return redirect("/")

        if category not in allowed_categories:
            connection.close()
            return redirect("/")

        if not description:
            connection.close()
            return redirect("/")

        if not expense_date:
            connection.close()
            return redirect("/")

        connection.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, description = ?, date = ?
            WHERE id = ?
            """,
            (
                amount,
                category,
                description,
                expense_date,
                expense_id
            )
        )

        connection.commit()
        connection.close()

        return redirect("/")

    expense = connection.execute(
        "SELECT * FROM expenses WHERE id = ?",
        (expense_id,)
    ).fetchone()

    connection.close()

    if expense is None:
        return redirect("/")

    return render_template(
        "edit_expense.html",
        expense=expense
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True)