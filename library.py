import sqlite3
from datetime import datetime

# ---------------------------
# Database Connection
# ---------------------------
def get_connection():
    return sqlite3.connect("library.db")

# ---------------------------
# Table Creation
# ---------------------------
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT CHECK(role IN ('Admin','Librarian','Member')) NOT NULL,
        password TEXT NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Borrow_Records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id INTEGER,
        borrow_date TEXT,
        return_date TEXT,
        status TEXT CHECK(status IN ('Borrowed','Returned')),
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
        FOREIGN KEY(book_id) REFERENCES Books(book_id)
    )""")

    conn.commit()
    conn.close()

# ---------------------------
# User Management
# ---------------------------
def register_user():
    print("\n--- Register New User ---")
    name = input("Enter name: ")
    email = input("Enter email: ")
    role = input("Enter role (Admin/Librarian/Member): ")
    password = input("Enter password: ")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (name, email, role, password) VALUES (?, ?, ?, ?)",
                       (name, email, role, password))
        conn.commit()
        print(f"✅ User '{name}' registered successfully.")
    except sqlite3.IntegrityError:
        print("⚠️ Email already exists!")
    finally:
        conn.close()

def login():
    print("\n--- User Login ---")
    email = input("Enter email: ")
    password = input("Enter password: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        print(f"👋 Welcome {user[1]} ({user[3]})")
        return user
    else:
        print("❌ Invalid credentials.")
        return None

# ---------------------------
# Book Management
# ---------------------------
def add_book():
    print("\n--- Add New Book ---")
    title = input("Enter book title: ")
    author = input("Enter author: ")
    category = input("Enter category: ")
    total = int(input("Enter total copies: "))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Books (title, author, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
                   (title, author, category, total, total))
    conn.commit()
    conn.close()
    print(f"📘 Book '{title}' added successfully.")

def search_books():
    print("\n--- Search Books ---")
    keyword = input("Enter keyword (title/author): ")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books WHERE title LIKE ? OR author LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    conn.close()
    if results:
        print("🔎 Search Results:")
        for r in results:
            print(f"ID: {r[0]} | Title: {r[1]} | Author: {r[2]} | Available: {r[5]}/{r[4]}")
    else:
        print("⚠️ No books found.")

# ---------------------------
# Borrow & Return
# ---------------------------
def borrow_book(user_id):
    print("\n--- Borrow Book ---")
    book_id = int(input("Enter book ID to borrow: "))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT available_copies FROM Books WHERE book_id=?", (book_id,))
    available = cursor.fetchone()

    if available and available[0] > 0:
        cursor.execute("INSERT INTO Borrow_Records (user_id, book_id, borrow_date, status) VALUES (?, ?, ?, 'Borrowed')",
                       (user_id, book_id, datetime.now().strftime("%Y-%m-%d")))
        cursor.execute("UPDATE Books SET available_copies = available_copies - 1 WHERE book_id=?", (book_id,))
        conn.commit()
        print("✅ Book borrowed successfully.")
    else:
        print("⚠️ Book not available.")
    conn.close()

def return_book():
    print("\n--- Return Book ---")
    record_id = int(input("Enter borrow record ID to return: "))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT book_id FROM Borrow_Records WHERE record_id=? AND status='Borrowed'", (record_id,))
    row = cursor.fetchone()

    if row:
        book_id = row[0]
        cursor.execute("UPDATE Borrow_Records SET status='Returned', return_date=? WHERE record_id=?",
                       (datetime.now().strftime("%Y-%m-%d"), record_id))
        cursor.execute("UPDATE Books SET available_copies = available_copies + 1 WHERE book_id=?", (book_id,))
        conn.commit()
        print("✅ Book returned successfully.")
    else:
        print("⚠️ Invalid record ID or already returned.")
    conn.close()

# ---------------------------
# Reports
# ---------------------------
def borrowed_books(user_id):
    print("\n--- Borrowed Books ---")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Borrow_Records WHERE user_id=?", (user_id,))
    records = cursor.fetchall()
    conn.close()

    if records:
        for r in records:
            print(f"RecordID: {r[0]} | BookID: {r[2]} | Borrowed: {r[3]} | Returned: {r[4]} | Status: {r[5]}")
    else:
        print("⚠️ No borrow records found.")

# ---------------------------
# Menu System
# ---------------------------
def main_menu():
    create_tables()
    print("===== 📚 Library Management System =====")

    while True:
        print("\n1. Register User\n2. Login\n3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            user = login()
            if user:
                if user[3] in ("Admin", "Librarian"):
                    admin_menu(user)
                else:
                    member_menu(user)
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️ Invalid choice.")

def admin_menu(user):
    while True:
        print("\n--- Admin/Librarian Menu ---")
        print("1. Add Book\n2. Search Books\n3. Borrow Book\n4. Return Book\n5. View Borrowed Books\n6. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            add_book()
        elif choice == "2":
            search_books()
        elif choice == "3":
            borrow_book(user[0])
        elif choice == "4":
            return_book()
        elif choice == "5":
            borrowed_books(user[0])
        elif choice == "6":
            break
        else:
            print("⚠️ Invalid choice.")

def member_menu(user):
    while True:
        print("\n--- Member Menu ---")
        print("1. Search Books\n2. Borrow Book\n3. Return Book\n4. View Borrowed Books\n5. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            search_books()
        elif choice == "2":
            borrow_book(user[0])
        elif choice == "3":
            return_book()
        elif choice == "4":
            borrowed_books(user[0])
        elif choice == "5":
            break
        else:
            print("⚠️ Invalid choice.")

# ---------------------------
# Run Program
# ---------------------------
if __name__ == "__main__":
    main_menu()
