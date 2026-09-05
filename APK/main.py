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
    except Exception as e:
        raise RuntimeError(f"Failed to load {filename}: {str(e)}")

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save {filename}: {str(e)}")

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def generate_user_id():
    users = load_data(USERS_FILE)
    next_num = 1
    if users:
        ids = [int(u["user_id"].upper().replace("U", "")) for u in users if u.get("user_id", "").upper().startswith("U")]
        if ids:
            next_num = max(ids) + 1
    return f"U{next_num:03d}"


# --- MAIN APP UI ---
def main(page: ft.Page):
    page.title = "Mobile Library Engine"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # --- DIALOG & NOTIFICATION SYSTEM ---
    dialog_text = ft.Text("")

    def close_dialog(e=None):
        error_dialog.open = False
        page.update()

    error_dialog = ft.AlertDialog(
        title=ft.Text("⚠️ Action Required"),
        content=dialog_text,
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def show_message(message, is_error=False):
        clean_msg = str(message)
        if is_error:
            dialog_text.value = clean_msg
            if error_dialog not in page.overlay:
                page.overlay.append(error_dialog)
            error_dialog.open = True
            page.update()
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text(clean_msg), bgcolor="green")
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
    checkout_book_input = ft.TextField(label="Book ID or Title")
    checkout_user_input = ft.TextField(label="User ID or Username")
    status_listview = ft.ListView(spacing=5, height=280)

    def refresh_desk_status():
        try:
            status_listview.controls.clear()
            books = load_data(BOOKS_FILE)
            for b in books:
                icon = "🟢 AVAILABLE" if b.get('status') == 'available' else "🔴 BORROWED"
                status_listview.controls.append(
                    ft.Text(f"[{icon}] {b.get('book_id', '')} | '{b.get('title', '')}'", size=13)
                )
            page.update()
        except Exception as ex:
            show_message(f"Status Refresh Error: {str(ex)}", True)

    def handle_checkout(e=None):
        try:
            raw_book = checkout_book_input.value or ""
            raw_user = checkout_user_input.value or ""
            
            book_query = raw_book.strip().lower()
            user_query = raw_user.strip().lower()
            
            if not book_query or not user_query:
                show_message("Error: Please enter both a valid Book ID/Title and User ID/Name before checking out.", True)
                return
                
            books = load_data(BOOKS_FILE)
            loans = load_data(LOANS_FILE)
            users = load_data(USERS_FILE)
            
            target_user = next((u for u in users if u.get("user_id", "").lower() == user_query or u.get("username", "").lower() == user_query), None)
            if not target_user:
                show_message("Error: Specified user record could not be found.", True)
                return

            target_book = None
            for book in books:
                if (book.get('book_id', '').lower() == book_query or book.get('title', '').lower() == book_query):
                    if book.get('status') == 'borrowed':
                        target_book = book
                        break
                    elif target_book is None:
                        target_book = book

            if not target_book:
                show_message("Error: Specified book not found in inventory.", True)
                return

            if target_book.get('status') == 'borrowed':
                show_message(f"Error: '{target_book.get('title')}' is already checked out!", True)
                return

            target_book['status'] = 'borrowed'
            loans.append({
                "book_id": target_book.get('book_id'),
                "title": target_book.get('title'),
                "user_id": target_user.get("user_id"),
                "username": target_user.get("username"),
                "checkout_date": get_current_date(),
                "return_date": "Still Out"
            })
            
            save_data(BOOKS_FILE, books)
            save_data(LOANS_FILE, loans)
            show_message(f"✅ '{target_book.get('title')}' checked out to {target_user.get('username')}!")
            
            checkout_book_input.value = ""
            checkout_user_input.value = ""
            refresh_all()
        except Exception as ex:
            show_message(f"Checkout Error: {str(ex)}", True)

    def handle_return(e=None):
        try:
            raw_book = checkout_book_input.value or ""
            book_query = raw_book.strip().lower()
            
            if not book_query:
                show_message("Error: Please enter a Book ID or Title to proceed with return.", True)
                return
                
            books = load_data(BOOKS_FILE)
            loans = load_data(LOANS_FILE)
            
            target_book = next((b for b in books if b.get('book_id', '').lower() == book_query or b.get('title', '').lower() == book_query), None)
            
            if not target_book:
                show_message("Error: Book tracking records not found.", True)
                return

            if target_book.get('status') == 'available':
                show_message(f"Error: '{target_book.get('title')}' is already marked as available.", True)
                return

            target_book['status'] = 'available'
            today = get_current_date()
            for loan in reversed(loans):
                if loan.get('book_id', '').lower() == target_book.get('book_id', '').lower() and loan.get('return_date') == "Still Out":
                    loan['return_date'] = today
                    break
                    
            save_data(BOOKS_FILE, books)
            save_data(LOANS_FILE, loans)
            show_message(f"✅ '{target_book.get('title')}' returned successfully!")
            checkout_book_input.value = ""
            refresh_all()
        except Exception as ex:
            show_message(f"Return Error: {str(ex)}", True)

    desk_view = ft.ListView([
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
    ], visible=True, expand=True, spacing=10)


    # ==========================================
    # --- TAB 2: INVENTORY CATALOG ---
    # ==========================================
    add_title_input = ft.TextField(label="Book Title")
    add_author_input = ft.TextField(label="Author Name")
    catalog_search_input = ft.TextField(label="🔍 Search Catalog", on_change=lambda e: refresh_catalog())
    catalog_listview = ft.ListView(spacing=5, height=250)

    def delete_book(book_id):
        try:
            books = load_data(BOOKS_FILE)
            books = [b for b in books if b.get('book_id') != book_id]
            save_data(BOOKS_FILE, books)
            show_message(f"Deleted book {book_id}")
            refresh_all()
        except Exception as ex:
            show_message(f"Delete Error: {str(ex)}", True)

    def refresh_catalog():
        try:
            catalog_listview.controls.clear()
            books = load_data(BOOKS_FILE)
            raw_query = catalog_search_input.value or ""
            query = raw_query.strip().lower()
            
            for b in books:
                b_id = b.get('book_id', '')
                title = b.get('title', '')
                author = b.get('author', '')
                status = b.get('status', 'available')

                if not query or query in b_id.lower() or query in title.lower() or query in author.lower():
                    icon = "🟢" if status == 'available' else "🔴"
                    catalog_listview.controls.append(
                        ft.Row([
                            ft.Text(f"{icon} ID: {b_id} | '{title}' by {author}", size=12, expand=True),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=b_id: delete_book(id))
                        ])
                    )
            page.update()
        except Exception as ex:
            show_message(f"Catalog Load Error: {str(ex)}", True)

    def handle_add_book(e=None):
        try:
            raw_title = add_title_input.value or ""
            raw_author = add_author_input.value or ""
            title = raw_title.strip()
            author = raw_author.strip()
            
            if not title:
                show_message("Error: Book Title cannot be empty!", True)
                return
                
            books = load_data(BOOKS_FILE)
            existing_ids = [int(b.get('book_id', '').upper().replace('B', '')) for b in books if b.get('book_id', '').upper().startswith('B')]
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
        except Exception as ex:
            show_message(f"Add Book Error: {str(ex)}", True)

    inventory_view = ft.ListView([
        ft.Text("REGISTER NEW INVENTORY", size=18, weight=ft.FontWeight.BOLD),
        add_title_input, 
        add_author_input,
        ft.ElevatedButton("➕ Save to Library File", on_click=handle_add_book),
        ft.Divider(),
        catalog_search_input,
        catalog_listview
    ], visible=False, expand=True, spacing=10)


    # ==========================================
    # --- TAB 3: USER MANAGEMENT ---
    # ==========================================
    username_input = ft.TextField(label="Register New Username")
    user_search_input = ft.TextField(label="🔍 Filter Members", on_change=lambda e: refresh_users())
    users_listview = ft.ListView(spacing=5, height=280)

    def delete_user(user_id):
        try:
            users = load_data(USERS_FILE)
            users = [u for u in users if u.get('user_id') != user_id]
            save_data(USERS_FILE, users)
            show_message(f"Deleted user {user_id}")
            refresh_all()
        except Exception as ex:
            show_message(f"Delete User Error: {str(ex)}", True)

    def refresh_users():
        try:
            users_listview.controls.clear()
            users = load_data(USERS_FILE)
            raw_query = user_search_input.value or ""
            query = raw_query.strip().lower()
            
            for u in users:
                u_id = u.get('user_id', '')
                uname = u.get('username', '')
                if not query or query in u_id.lower() or query in uname.lower():
                    users_listview.controls.append(
                        ft.Row([
                            ft.Text(f"👤 ID: {u_id} | Name: {uname}", size=13, expand=True),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=u_id: delete_user(id))
                        ])
                    )
            page.update()
        except Exception as ex:
            show_message(f"User Refresh Error: {str(ex)}", True)

    def handle_add_user(e=None):
        try:
            raw_username = username_input.value or ""
            username = raw_username.strip()

            if not username:
                show_message("Error: Please enter a username.", True)
                return

            users = load_data(USERS_FILE)
            if any(u.get('username', '').lower() == username.lower() for u in users):
                show_message(f"Error: Username '{username}' is already registered!", True)
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
        except Exception as ex:
            show_message(f"User Add Error: {str(ex)}", True)

    users_view = ft.ListView([
        ft.Text("USER MANAGEMENT", size=18, weight=ft.FontWeight.BOLD),
        username_input,
        ft.ElevatedButton("➕ Register User", on_click=handle_add_user),
        ft.Divider(),
        user_search_input,
        users_listview
    ], visible=False, expand=True, spacing=10)


    # ==========================================
    # --- TAB 4: TRANSACTION TIMELINE LOGS ---
    # ==========================================
    history_search_input = ft.TextField(label="🔍 Search Logs", on_change=lambda e: refresh_history())
    sort_dropdown = ft.Dropdown(
        value="Newest First",
        options=[ft.dropdown.Option("Newest First"), ft.dropdown.Option("Oldest First")]
    )
    sort_dropdown.on_change = lambda e: refresh_history()
    history_listview = ft.ListView(spacing=5, height=280)

    def delete_transaction(log):
        try:
            loans = load_data(LOANS_FILE)
            loans = [l for l in loans if not (l.get('book_id') == log.get('book_id') and l.get('user_id') == log.get('user_id') and l.get('checkout_date') == log.get('checkout_date'))]
            save_data(LOANS_FILE, loans)
            show_message("Deleted log entry.")
            refresh_all()
        except Exception as ex:
            show_message(f"Delete Log Error: {str(ex)}", True)

    def refresh_history():
        try:
            history_listview.controls.clear()
            loans = load_data(LOANS_FILE)
            raw_search = history_search_input.value or ""
            search_query = raw_search.strip().lower()
            
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
        except Exception as ex:
            show_message(f"History Refresh Error: {str(ex)}", True)

    history_view = ft.ListView([
        ft.Text("TRANSACTION TIMELINE", size=18, weight=ft.FontWeight.BOLD),
        ft.ResponsiveRow([
            ft.Column([history_search_input], col={"xs": 12, "sm": 7}),
            ft.Column([sort_dropdown], col={"xs": 12, "sm": 5})
        ]),
        history_listview
    ], visible=False, expand=True, spacing=10)


    # ==========================================
    # --- TOP NAVIGATION BAR ---
    # ==========================================
    buttons = []

    def set_tab(idx):
        desk_view.visible = (idx == 0)
        inventory_view.visible = (idx == 1)
        users_view.visible = (idx == 2)
        history_view.visible = (idx == 3)

        for i, btn in enumerate(buttons):
            btn.bgcolor = "blue" if i == idx else "grey_300"
            btn.color = "white" if i == idx else "black"

        page.update()

    btn_desk = ft.ElevatedButton("📤 Desk", on_click=lambda e: set_tab(0), bgcolor="blue", color="white")
    btn_inventory = ft.ElevatedButton("📖 Inventory", on_click=lambda e: set_tab(1), bgcolor="grey_300", color="black")
    btn_users = ft.ElevatedButton("👤 Users", on_click=lambda e: set_tab(2), bgcolor="grey_300", color="black")
    btn_logs = ft.ElevatedButton("📋 Logs", on_click=lambda e: set_tab(3), bgcolor="grey_300", color="black")

    buttons = [btn_desk, btn_inventory, btn_users, btn_logs]

    top_nav = ft.Row(buttons, scroll=ft.ScrollMode.AUTO)

    page.add(
        top_nav,
        ft.Divider(),
        desk_view,
        inventory_view,
        users_view,
        history_view
    )
    
    refresh_all()

ft.app(target=main)
