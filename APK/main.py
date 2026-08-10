import flet as ft
import json
import os
from datetime import datetime

# --- DATA MANAGEMENT ---
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

def generate_user_id():
    users = load_data(USERS_FILE)
    next_num = 1
    if users:
        ids = [int(u["user_id"].upper().replace("U", "")) for u in users if u["user_id"].upper().startswith("U")]
        if ids:
            next_num = max(ids) + 1
    return f"U{next_num:03d}"


# --- MAIN APP UI ---
def main(page: ft.Page):
    page.title = "Mobile Library Engine"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15

    def show_message(message, is_error=False):
        color = "red" if is_error else "green"
        page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def refresh_all():
        refresh_desk_status()
        refresh_catalog()
        refresh_users()
        refresh_history()

    # ==========================================
    # --- TAB 1: RECEPTION DESK ---
    # ==========================================
    checkout_book_input = ft.TextField(label="Book ID or Title", width=350)
    checkout_user_input = ft.TextField(label="User ID or Username", width=350)
    status_listview = ft.ListView(expand=True, spacing=5, height=280)

    def refresh_desk_status():
        status_listview.controls.clear()
        books = load_data(BOOKS_FILE)
        for b in books:
            icon = "🟢 AVAILABLE" if b['status'] == 'available' else "🔴 BORROWED"
            status_listview.controls.append(
                ft.Text(f"[{icon}] {b['book_id']} | '{b['title']}'", size=13)
            )
        page.update()

    def handle_checkout(e):
        book_query = checkout_book_input.value.strip().lower()
        user_query = checkout_user_input.value.strip().lower()
        
        if not book_query or not user_query:
            show_message("Please enter both Book ID/Title and User ID/Name!", True)
            return
            
        books, loans, users = load_data(BOOKS_FILE), load_data(LOANS_FILE), load_data(USERS_FILE)
        
        target_user = next((u for u in users if u["user_id"].lower() == user_query or u["username"].lower() == user_query), None)
        if not target_user:
            show_message("User record not found.", True)
            return

        target_book = None
        for book in books:
            if (book['book_id'].lower() == book_query or book['title'].lower() == book_query):
                if book['status'] == 'borrowed':
                    target_book = book
                    break
                elif target_book is None:
                    target_book = book

        if not target_book:
            show_message("Book not found in inventory.", True)
            return

        if target_book['status'] == 'borrowed':
            show_message(f"'{target_book['title']}' is already checked out!", True)
            return

        target_book['status'] = 'borrowed'
        loans.append({
            "book_id": target_book['book_id'],
            "title": target_book['title'],
            "user_id": target_user["user_id"],
            "username": target_user["username"],
            "checkout_date": get_current_date(),
            "return_date": "Still Out"
        })
        
        save_data(BOOKS_FILE, books)
        save_data(LOANS_FILE, loans)
        show_message(f"✅ '{target_book['title']}' checked out to {target_user['username']}!")
        
        checkout_book_input.value = ""
        checkout_user_input.value = ""
        refresh_all()

    def handle_return(e):
        book_query = checkout_book_input.value.strip().lower()
        if not book_query:
            show_message("Please enter a Book ID or Title to return!", True)
            return
            
        books, loans = load_data(BOOKS_FILE), load_data(LOANS_FILE)
        target_book = next((b for b in books if b['book_id'].lower() == book_query or b['title'].lower() == book_query), None)
        
        if not target_book:
            show_message("Book tracking records not found.", True)
            return

        if target_book['status'] == 'available':
            show_message(f"'{target_book['title']}' is already available.", True)
            return

        target_book['status'] = 'available'
        today = get_current_date()
        for loan in reversed(loans):
            if loan['book_id'].lower() == target_book['book_id'].lower() and loan['return_date'] == "Still Out":
                loan['return_date'] = today
                break
                
        save_data(BOOKS_FILE, books)
        save_data(LOANS_FILE, loans)
        show_message(f"✅ '{target_book['title']}' returned successfully!")
        checkout_book_input.value = ""
        refresh_all()

    desk_view = ft.Column([
        ft.Text("RECEPTION COUNTER", size=18, weight=ft.FontWeight.BOLD),
        checkout_book_input,
        checkout_user_input,
        ft.Row([
            ft.ElevatedButton("📤 Check Out", on_click=handle_checkout, bgcolor="green", color="white"),
            ft.ElevatedButton("📥 Return Book", on_click=handle_return, bgcolor="blue", color="white"),
        ]),
        ft.Divider(),
        ft.Text("Live Book Directory:", weight=ft.FontWeight.BOLD),
        status_listview
    ], visible=True, expand=True)


    # ==========================================
    # --- TAB 2: INVENTORY CATALOG ---
    # ==========================================
    add_title_input = ft.TextField(label="Book Title", width=350)
    add_author_input = ft.TextField(label="Author Name", width=350)
    catalog_search_input = ft.TextField(label="🔍 Search Catalog", width=350, on_change=lambda e: refresh_catalog())
    catalog_listview = ft.ListView(expand=True, spacing=5, height=250)

    def delete_book(book_id):
        books = load_data(BOOKS_FILE)
        books = [b for b in books if b['book_id'] != book_id]
        save_data(BOOKS_FILE, books)
        show_message(f"Deleted book {book_id}")
        refresh_all()

    def refresh_catalog():
        catalog_listview.controls.clear()
        books = load_data(BOOKS_FILE)
        query = catalog_search_input.value.strip().lower()
        
        for b in books:
            if not query or query in b['book_id'].lower() or query in b['title'].lower() or query in b['author'].lower():
                b_id = b['book_id']
                icon = "🟢" if b['status'] == 'available' else "🔴"
                catalog_listview.controls.append(
                    ft.Row([
                        ft.Text(f"{icon} ID: {b['book_id']} | '{b['title']}' by {b['author']}", size=12, expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=b_id: delete_book(id))
                    ])
                )
        page.update()

    def handle_add_book(e):
        title = add_title_input.value.strip()
        author = add_author_input.value.strip()
        
        if not title:
            show_message("Book Title cannot be empty!", True)
            return
            
        books = load_data(BOOKS_FILE)
        existing_ids = [int(b['book_id'].upper().replace('B', '')) for b in books if b['book_id'].upper().startswith('B')]
        next_num = max(existing_ids) + 1 if existing_ids else 1
        auto_id = f"B{next_num:03d}"
        
        books.append({
            "book_id": auto_id,
            "title": title,
            "author": author if author else "Unknown",
            "status": "available"
        })
        
        save_data(BOOKS_FILE, books)
        show_message(f"Added '{title}' with ID: {auto_id}")
        
        add_title_input.value = ""
        add_author_input.value = ""
        refresh_all()

    inventory_view = ft.Column([
        ft.Text("REGISTER NEW INVENTORY", size=18, weight=ft.FontWeight.BOLD),
        add_title_input, add_author_input,
        ft.ElevatedButton("➕ Save to Library File", on_click=handle_add_book),
        ft.Divider(),
        catalog_search_input,
        catalog_listview
    ], visible=False, expand=True)


    # ==========================================
    # --- TAB 3: USER MANAGEMENT ---
    # ==========================================
    username_input = ft.TextField(label="Register New Username", width=350)
    user_search_input = ft.TextField(label="🔍 Filter Members", width=350, on_change=lambda e: refresh_users())
    users_listview = ft.ListView(expand=True, spacing=5, height=280)

    def delete_user(user_id):
        users = load_data(USERS_FILE)
        users = [u for u in users if u['user_id'] != user_id]
        save_data(USERS_FILE, users)
        show_message(f"Deleted user {user_id}")
        refresh_all()

    def refresh_users():
        users_listview.controls.clear()
        users = load_data(USERS_FILE)
        query = user_search_input.value.strip().lower()
        
        for u in users:
            if not query or query in u['user_id'].lower() or query in u['username'].lower():
                u_id = u['user_id']
                users_listview.controls.append(
                    ft.Row([
                        ft.Text(f"👤 ID: {u['user_id']} | Name: {u['username']}", size=13, expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=u_id: delete_user(id))
                    ])
                )
        page.update()

    def handle_add_user(e):
        username = username_input.value.strip()

        if not username:
            show_message("Please enter a username.", True)
            return

        users = load_data(USERS_FILE)
        if any(u['username'].lower() == username.lower() for u in users):
            show_message(f"The username '{username}' is already registered!", True)
            return

        user_id = generate_user_id()
        users.append({
            "user_id": user_id,
            "username": username
        })

        save_data(USERS_FILE, users)
        show_message(f"Registered User ID: {user_id}")
        
        username_input.value = ""
        refresh_all()

    users_view = ft.Column([
        ft.Text("USER MANAGEMENT", size=18, weight=ft.FontWeight.BOLD),
        username_input,
        ft.ElevatedButton("➕ Register User", on_click=handle_add_user),
        ft.Divider(),
        user_search_input,
        users_listview
    ], visible=False, expand=True)


    # ==========================================
    # --- TAB 4: TRANSACTION TIMELINE LOGS ---
    # ==========================================
    history_search_input = ft.TextField(label="🔍 Search Logs", width=200, on_change=lambda e: refresh_history())
    sort_dropdown = ft.Dropdown(
        width=140,
        value="Newest First",
        options=[ft.dropdown.Option("Newest First"), ft.dropdown.Option("Oldest First")]
    )
    sort_dropdown.on_change = lambda e: refresh_history()
    history_listview = ft.ListView(expand=True, spacing=5, height=280)

    def delete_transaction(log):
        loans = load_data(LOANS_FILE)
        loans = [l for l in loans if not (l['book_id'] == log['book_id'] and l['user_id'] == log['user_id'] and l['checkout_date'] == log['checkout_date'])]
        save_data(LOANS_FILE, loans)
        show_message("Deleted log entry.")
        refresh_all()

    def refresh_history():
        history_listview.controls.clear()
        loans = load_data(LOANS_FILE)
        search_query = history_search_input.value.strip().lower()
        
        filtered = []
        for l in loans:
            if (not search_query or 
                search_query in l.get('title', '').lower() or 
                search_query in l.get('book_id', '').lower() or 
                search_query in l.get('user_id', '').lower() or 
                search_query in l.get('username', '').lower() or 
                search_query in l.get('checkout_date', '').lower() or 
                search_query in l.get('return_date', '').lower()):
                filtered.append(l)

        if sort_dropdown.value == "Newest First":
            filtered.reverse()

        for l in filtered:
            ret_date = l.get('return_date', 'Still Out')
            ret_display = f"Returned: {ret_date}" if ret_date != "Still Out" else "❌ Still Out"
            log_item = l
            history_listview.controls.append(
                ft.Row([
                    ft.Text(f"📖 '{l.get('title')}' ({l.get('book_id')})\n👤 {l.get('username')} ({l.get('user_id')})\n📅 Out: {l.get('checkout_date')} | {ret_display}", size=11, expand=True),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, item=log_item: delete_transaction(item))
                ])
            )
        page.update()

    history_view = ft.Column([
        ft.Text("TRANSACTION TIMELINE", size=18, weight=ft.FontWeight.BOLD),
        ft.Row([history_search_input, sort_dropdown]),
        history_listview
    ], visible=False, expand=True)


    # ==========================================
    # --- TOP NAVIGATION BAR ---
    # ==========================================
    def set_tab(idx):
        desk_view.visible = (idx == 0)
        inventory_view.visible = (idx == 1)
        users_view.visible = (idx == 2)
        history_view.visible = (idx == 3)

        btn_desk.bgcolor = "blue" if idx == 0 else "grey_300"
        btn_desk.color = "white" if idx == 0 else "black"

        btn_inventory.bgcolor = "blue" if idx == 1 else "grey_300"
        btn_inventory.color = "white" if idx == 1 else "black"

        btn_users.bgcolor = "blue" if idx == 2 else "grey_300"
        btn_users.color = "white" if idx == 2 else "black"

        btn_logs.bgcolor = "blue" if idx == 3 else "grey_300"
        btn_logs.color = "white" if idx == 3 else "black"

        page.update()

    btn_desk = ft.ElevatedButton("📤 Desk", on_click=lambda e: set_tab(0), bgcolor="grey_300", color="black")
    btn_inventory = ft.ElevatedButton("📖 Inventory", on_click=lambda e: set_tab(1), bgcolor="blue", color="white")
    btn_users = ft.ElevatedButton("👤 Users", on_click=lambda e: set_tab(2), bgcolor="grey_300", color="black")
    btn_logs = ft.ElevatedButton("📋 Logs", on_click=lambda e: set_tab(3), bgcolor="grey_300", color="black")

    top_nav = ft.Row([btn_desk, btn_inventory, btn_users, btn_logs], scroll=ft.ScrollMode.AUTO)

    page.add(
        top_nav,
        ft.Divider(),
        desk_view,
        inventory_view,
        users_view,
        history_view
    )
    
    refresh_all()

# Run application
ft.app(target=main)
