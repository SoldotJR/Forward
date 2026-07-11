# Libraries
import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from datetime import datetime

# Load json files to store the data
BOOKS_FILE = 'books.json'
LOANS_FILE = 'loans.json'
USERS_FILE = 'users.json'


def load_data(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")


# UPDATED: Added an optional 'event' argument to handle keyboard triggers seamlessly
def handle_checkout(event=None):
    book_query = checkout_book_input.get().strip().lower()
    user_query = checkout_user_input.get().strip().lower()
    
    if not book_query:
        messagebox.showerror("Error", "Please enter or scan a Book ID or Book Title!")
        return
    if not user_query:
        messagebox.showerror("Error", "Please enter or scan a User ID or Username!")
        return
        
    books = load_data(BOOKS_FILE)
    loans = load_data(LOANS_FILE)
    users = load_data(USERS_FILE)

    target_user = None
    for u in users:
        if u["user_id"].lower() == user_query or u["username"].lower() == user_query:
            target_user = u
            break

    if target_user is None:
        messagebox.showerror("Error", "User record not found (Invalid ID or Username).")
        return

    target_book = None
    for book in books:
        if book['book_id'].lower() == book_query or book['title'].lower() == book_query:
            target_book = book
            break
            
    if target_book is None:
        messagebox.showerror("Error", "Book not found in inventory (Invalid ID or Title).")
        return

    if target_book['status'] == 'borrowed':
        messagebox.showwarning("Warning", f"⚠️ '{target_book['title']}' is already checked out!")
        return

    today = get_current_date()
    target_book['status'] = 'borrowed'
    
    loans.append({
        "book_id": target_book['book_id'],
        "title": target_book['title'],
        "user_id": target_user["user_id"],
        "username": target_user["username"],
        "checkout_date": today,
        "return_date": "Still Out"
    })
    
    save_data(BOOKS_FILE, books)
    save_data(LOANS_FILE, loans)
    messagebox.showinfo("Success", f"✅ '{target_book['title']}' checked out to {target_user['username']}!")
    
    checkout_book_input.delete(0, tk.END)
    checkout_user_input.delete(0, tk.END)
    checkout_book_input.focus() # Keeps your typing focus active here
    refresh_all_displays()


def handle_return():
    book_query = checkout_book_input.get().strip().lower()
    
    if not book_query:
        messagebox.showerror("Error", "Please enter or scan a Book ID or Book Title to return!")
        return
        
    books = load_data(BOOKS_FILE)
    loans = load_data(LOANS_FILE)
    
    target_book = None
    for book in books:
        if book['book_id'].lower() == book_query or book['title'].lower() == book_query:
            target_book = book
            break
            
    if target_book is None:
        messagebox.showerror("Error", "Book tracking records not found.")
        return

    if target_book['status'] == 'available':
        messagebox.showwarning("Warning", f"'{target_book['title']}' is already marked as available.")
        return

    target_book['status'] = 'available'

    today = get_current_date()
    for loan in reversed(loans):
        if loan['book_id'].lower() == target_book['book_id'].lower() and loan['return_date'] == "Still Out":
            loan['return_date'] = today
            break
            
    save_data(BOOKS_FILE, books)
    save_data(LOANS_FILE, loans)
    messagebox.showinfo("Success", f"✅ '{target_book['title']}' returned successfully!")
    checkout_book_input.delete(0, tk.END)
    checkout_user_input.delete(0, tk.END)
    checkout_book_input.focus()
    refresh_all_displays()


# UPDATED: Added event=None argument to accept keyboard triggers
def handle_add_book(event=None):
    title = add_title_input.get().strip()
    author = add_author_input.get().strip()
    
    if not title:
        messagebox.showerror("Error", "Book Title cannot be empty!")
        return
        
    books = load_data(BOOKS_FILE)
    
    if any(b['title'].lower() == title.lower() for b in books):
        if not messagebox.askyesno("Duplicate Warning", "A book with this title already exists. Add anyway?"):
            return
            
    next_num = 1
    if books:
        existing_ids = [int(b['book_id'].upper().replace('B', '')) for b in books if b['book_id'].upper().startswith('B')]
        if existing_ids:
            next_num = max(existing_ids) + 1
    auto_id = f"B{next_num:03d}"
    
    books.append({
        "book_id": auto_id,
        "title": title,
        "author": author if author else "Unknown",
        "status": "available"
    })
    
    save_data(BOOKS_FILE, books)
    messagebox.showinfo("Success", f"Added '{title}' with ID: {auto_id}")
    
    add_title_input.delete(0, tk.END)
    add_author_input.delete(0, tk.END)
    add_title_input.focus() # UPDATED: Automatically returns typing cursor to the first box
    refresh_all_displays()


def generate_user_id():
    users = load_data(USERS_FILE)
    next_num = 1
    if users:
        ids = [int(u["user_id"].upper().replace("U", "")) for u in users]
        next_num = max(ids) + 1
    return f"U{next_num:03d}"


# UPDATED: Added event=None argument to accept keyboard triggers
def handle_add_user(event=None):
    username = username_input.get().strip()

    if not username:
        messagebox.showerror("Error", "Please enter a username.")
        return

    users = load_data(USERS_FILE)
    
    if any(u['username'].lower() == username.lower() for u in users):
        messagebox.showerror("Error", f"The username '{username}' is already registered!")
        return

    user_id = generate_user_id()
    users.append({
        "user_id": user_id,
        "username": username
    })

    save_data(USERS_FILE, users)
    messagebox.showinfo("Success", f"User registered successfully!\n\nUser ID: {user_id}")
    
    username_input.delete(0, tk.END)
    username_input.focus() # UPDATED: Keeps typing cursor active in registration field
    refresh_all_displays()


displayed_books = []
displayed_users = []
displayed_loans = []

def update_catalog_display():
    global displayed_books
    catalog_listbox.delete(0, tk.END)
    books = load_data(BOOKS_FILE)
    query = catalog_search_input.get().strip().lower()
    
    displayed_books = []
    for b in books:
        if not query or query in b['book_id'].lower() or query in b['title'].lower() or query in b['author'].lower():
            displayed_books.append(b)
            icon = "🟢" if b['status'] == 'available' else "🔴"
            catalog_listbox.insert(tk.END, f" {icon} ID: {b['book_id']} | '{b['title']}' by {b['author']}")

def update_users_display():
    global displayed_users
    users_listbox.delete(0, tk.END)
    users = load_data(USERS_FILE)
    query = user_search_input.get().strip().lower()
    
    displayed_users = []
    for u in users:
        if not query or query in u['user_id'].lower() or query in u['username'].lower():
            displayed_users.append(u)
            users_listbox.insert(tk.END, f" 👤 ID: {u['user_id']}  |  Name: {u['username']}")

def update_transaction_display():
    global displayed_loans
    history_listbox.delete(0, tk.END)
    loans = load_data(LOANS_FILE)
    search_query = transaction_search_input.get().strip().lower()
    
    filtered_loans = []
    for l in loans:
        if (not search_query or 
            search_query in l.get('title', '').lower() or 
            search_query in l.get('book_id', '').lower() or 
            search_query in l.get('user_id', '').lower() or 
            search_query in l.get('username', '').lower() or 
            search_query in l.get('checkout_date', '').lower() or 
            search_query in l.get('return_date', '').lower()):
            filtered_loans.append(l)
            
    if transaction_sort.get() == "Newest First":
        filtered_loans.reverse()
        
    displayed_loans = filtered_loans
    for l in filtered_loans:
        ret_date = l.get('return_date', 'Still Out')
        ret_display = f"Returned: {ret_date}" if ret_date != "Still Out" else "❌ Still Out"
        history_listbox.insert(tk.END, f" 📖 '{l.get('title')}' (ID: {l.get('book_id')})  |  {l.get('user_id')} ({l.get('username')})  | Borrowed: {l.get('checkout_date')}  |  {ret_display}")


def delete_selected_book():
    selected_indices = catalog_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Missing", "Please select one or more books from the list first!")
        return
        
    books = load_data(BOOKS_FILE)
    
    books_to_delete = [displayed_books[i] for i in selected_indices]
    titles_string = "\n".join([b['title'] for b in books_to_delete[:5]])
    if len(books_to_delete) > 5:
        titles_string += f"\n... and {len(books_to_delete) - 5} more books"

    if messagebox.askyesno("Confirm Bulk Deletion", f"Permanently delete these {len(selected_indices)} book(s)?\n\n{titles_string}"):
        for target in books_to_delete:
            books = [b for b in books if b['book_id'] != target['book_id']]
        save_data(BOOKS_FILE, books)
        refresh_all_displays()

def delete_selected_user():
    selected_indices = users_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Missing", "Please select a user from the list first!")
        return
        
    users = load_data(USERS_FILE)
    users_to_delete = [displayed_users[i] for i in selected_indices]
    names_string = "\n".join([u['username'] for u in users_to_delete[:5]])

    if messagebox.askyesno("Confirm Deletion", f"Permanently delete these {len(selected_indices)} user(s)?\n\n{names_string}"):
        for target in users_to_delete:
            users = [u for u in users if u['user_id'] != target['user_id']]
        save_data(USERS_FILE, users)
        refresh_all_displays()

def delete_selected_transaction():
    selected_indices = history_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Missing", "Please select one or more log entries first!")
        return
        
    loans = load_data(LOANS_FILE)
    loans_to_delete = [displayed_loans[i] for i in selected_indices]
    
    if messagebox.askyesno("Confirm Deletion", f"Delete {len(selected_indices)} transaction log entry/entries?"):
        for target in loans_to_delete:
            loans = [l for l in loans if not (l['book_id'] == target['book_id'] and l['user_id'] == target['user_id'] and l['checkout_date'] == target['checkout_date'])]
        save_data(LOANS_FILE, loans)
        refresh_all_displays()


def refresh_all_displays():
    status_listbox.delete(0, tk.END)
    books = load_data(BOOKS_FILE)
    for b in books:
        icon = "🟢 AVAILABLE" if b['status'] == 'available' else "🔴 BORROWED "
        status_listbox.insert(tk.END, f" [{icon}]  ID: {b['book_id']}  |  '{b['title']}' by {b['author']}")
        
    update_catalog_display()
    update_users_display()
    update_transaction_display()


# UI Setup
root = tk.Tk()
root.title("Forward's Database Engine")
root.geometry("950x750")

title_font = font.Font(family="Arial", size=16, weight="bold")
label_font = font.Font(family="Arial", size=14)
input_font = font.Font(family="Courier", size=12)
btn_font = font.Font(family="Arial", size=14, weight="bold")
del_btn_font = font.Font(family="Arial", size=11, weight="bold")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

tab_loans = tk.Frame(notebook, bg="#f9f9f9")
tab_books = tk.Frame(notebook, bg="#f9f9f9")
tab_users = tk.Frame(notebook, bg="#f9f9f9") 
tab_history = tk.Frame(notebook, bg="#f9f9f9")

notebook.add(tab_loans, text="  📤 Check Out / In Desk  ")
notebook.add(tab_books, text="  📖 Inventory Catalog  ")
notebook.add(tab_users, text="  👥 Manage Users  ") 
notebook.add(tab_history, text="  📋 Transaction Logs  ")


# --- TAB 1: DESK INTERFACE ---
tk.Label(tab_loans, text="LIBRARY RECEPTION COUNTER", font=title_font, bg="#f9f9f9", fg="#333").pack(pady=10)

tk.Label(tab_loans, text="Book ID or Book Title:", font=label_font, bg="#f9f9f9").pack(anchor="w", padx=50)
checkout_book_input = tk.Entry(tab_loans, font=label_font, width=35)
checkout_book_input.pack(pady=5, padx=50, ipady=4, fill="x")
checkout_book_input.focus() 

tk.Label(tab_loans, text="User ID or Username (Required for Check Out):", font=label_font, bg="#f9f9f9").pack(anchor="w", padx=50, pady=(5, 0))
checkout_user_input = tk.Entry(tab_loans, font=label_font, width=35)
checkout_user_input.pack(pady=5, padx=50, ipady=4, fill="x")

# UPDATED: Pressing Enter in either checkout box processes checkout immediately
checkout_book_input.bind("<Return>", handle_checkout)
checkout_user_input.bind("<Return>", handle_checkout)

btn_frame = tk.Frame(tab_loans, bg="#f9f9f9")
btn_frame.pack(pady=15)
tk.Button(btn_frame, text="📤 CHECK OUT", font=btn_font, bg="#4CAF50", fg="white", padx=20, pady=8, command=handle_checkout).pack(side=tk.LEFT, padx=15)
tk.Button(btn_frame, text="📥 RETURN BOOK", font=btn_font, bg="#2196F3", fg="white", padx=20, pady=8, command=handle_return).pack(side=tk.LEFT, padx=15)

tk.Label(tab_loans, text="Live Book Availability status directory lookup:", font=label_font, bg="#f9f9f9", fg="#555").pack(anchor="w", padx=50, pady=(10,0))
status_listbox = tk.Listbox(tab_loans, font=input_font, width=85, height=14)
status_listbox.pack(pady=5, padx=50, fill=tk.BOTH, expand=True)


# --- TAB 2: INVENTORY CATALOG ---
tk.Label(tab_books, text="REGISTER NEW INVENTORY", font=title_font, bg="#f9f9f9").pack(pady=10)

tk.Label(tab_books, text="Book Title:", font=label_font, bg="#f9f9f9").pack(anchor="w", padx=50)
add_title_input = tk.Entry(tab_books, font=label_font, width=45)
add_title_input.pack(pady=5, padx=50, fill="x")

tk.Label(tab_books, text="Author Name:", font=label_font, bg="#f9f9f9").pack(anchor="w", padx=50)
add_author_input = tk.Entry(tab_books, font=label_font, width=45)
add_author_input.pack(pady=5, padx=50, fill="x")

# UPDATED: Pressing Enter in title or author entry saves the book immediately
add_title_input.bind("<Return>", handle_add_book)
add_author_input.bind("<Return>", handle_add_book)

tk.Button(tab_books, text="➕ Save to Library File", font=btn_font, bg="#e7e7e7", padx=10, pady=5, command=handle_add_book).pack(pady=10)

cat_search_frame = tk.Frame(tab_books, bg="#f9f9f9")
cat_search_frame.pack(fill="x", padx=50, pady=5)
tk.Label(cat_search_frame, text="🔍 Filter Catalog:", font=label_font, bg="#f9f9f9").pack(side=tk.LEFT)
catalog_search_input = tk.Entry(cat_search_frame, font=input_font, width=30)
catalog_search_input.pack(side=tk.LEFT, padx=10, ipady=2)
catalog_search_input.bind("<KeyRelease>", lambda e: update_catalog_display())

catalog_listbox = tk.Listbox(tab_books, font=input_font, width=85, height=12, selectmode=tk.EXTENDED)
catalog_listbox.pack(pady=5, padx=50, fill=tk.BOTH, expand=True)

tk.Button(tab_books, text="🗑️ Delete Selected Book(s) from System", font=del_btn_font, bg="#f44336", fg="white", padx=10, command=delete_selected_book).pack(pady=10)


# --- TAB 3: USER MANAGEMENT INTERFACE ---
tk.Label(tab_users, text="USER MANAGEMENT SYSTEM", font=title_font, bg="#f9f9f9", fg="#333").pack(pady=10)

tk.Label(tab_users, text="Register New Username:", font=label_font, bg="#f9f9f9").pack(anchor="w", padx=50, pady=(10, 0))
username_input = tk.Entry(tab_users, font=label_font, width=45)
username_input.pack(pady=5, padx=50, fill="x")

# UPDATED: Pressing Enter in registration entry registers the user immediately
username_input.bind("<Return>", handle_add_user)

tk.Button(tab_users, text="➕ Register User", font=btn_font, bg="#e7e7e7", padx=10, pady=5, command=handle_add_user).pack(pady=10)

user_search_frame = tk.Frame(tab_users, bg="#f9f9f9")
user_search_frame.pack(fill="x", padx=50, pady=5)
tk.Label(user_search_frame, text="🔍 Filter Members:", font=label_font, bg="#f9f9f9").pack(side=tk.LEFT)
user_search_input = tk.Entry(user_search_frame, font=input_font, width=30)
user_search_input.pack(side=tk.LEFT, padx=10, ipady=2)
user_search_input.bind("<KeyRelease>", lambda e: update_users_display())

users_listbox = tk.Listbox(tab_users, font=input_font, width=85, height=14, selectmode=tk.EXTENDED)
users_listbox.pack(pady=5, padx=50, fill=tk.BOTH, expand=True)

tk.Button(tab_users, text="🗑️ Delete Selected User(s) from System", font=del_btn_font, bg="#f44336", fg="white", padx=10, command=delete_selected_user).pack(pady=10)


# --- TAB 4: TRANSACTION TIMELINE ---
tk.Label(tab_history, text="LIBRARY TRANSACTION TIMELINE LOGS", font=title_font, bg="#f9f9f9", fg="#333").pack(pady=15)

search_frame = tk.Frame(tab_history, bg="#f9f9f9")
search_frame.pack(fill="x", padx=50, pady=5)

tk.Label(search_frame, text="Search:", bg="#f9f9f9", font=label_font).pack(side=tk.LEFT)
transaction_search_input = tk.Entry(search_frame, width=35, font=input_font)
transaction_search_input.pack(side=tk.LEFT, padx=5)

search_hint = tk.Label(tab_history, text="Search by: Book ID • Book Title • User Name • Check Out Date • Return Date", font=("Arial", 9), fg="gray", bg="#f9f9f9")
search_hint.pack(anchor="w", padx=50, pady=(0, 5))

transaction_search_input.bind("<KeyRelease>", lambda event: update_transaction_display())

tk.Label(search_frame, text="Sort:", bg="#f9f9f9", font=label_font).pack(side=tk.LEFT, padx=(20,5))
transaction_sort = ttk.Combobox(search_frame, values=["Newest First", "Oldest First"], width=15, state="readonly")
transaction_sort.current(0)
transaction_sort.pack(side=tk.LEFT)
transaction_sort.bind("<<ComboboxSelected>>", lambda event: update_transaction_display())

history_listbox = tk.Listbox(tab_history, font=input_font, width=90, height=16, selectmode=tk.EXTENDED)
history_listbox.pack(pady=5, padx=50, fill=tk.BOTH, expand=True)

tk.Button(tab_history, text="🗑️ Delete Selected Log Entry/Entries", font=del_btn_font, bg="#f44336", fg="white", padx=10, command=delete_selected_transaction).pack(pady=10)


refresh_all_displays()
root.mainloop()