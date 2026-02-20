import sqlite3
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap


from API_medialib import get_movie
from database_medialib import connect, initialize_db, save_movies
import re
import sys
import os
from load_movies import load_movies, paginate, download_poster

current_user = {"name": "", "email":""}

connect()
initialize_db()


class Login(QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        loadUi("loginpage.ui", self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.loginbutton = self.findChild(QPushButton, "login_button")
        self.username = self.findChild(QLineEdit, "usern_ent")
        self.password = self.findChild(QLineEdit, "passw_ent")
        self.passworderror = self.findChild(QLabel, "userpass_err")
        self.signupbutton = self.findChild(QPushButton, "signup_button")
        self.secondwindow = Dash()
        self.secondwindow.hide()
        self.signupwindow = Signup()
        self.signupwindow.hide()

        self.loginbutton.clicked.connect(self.gotonextpage)
        self.open()

        self.signupbutton.clicked.connect(self.signup)

    def gotonextpage(self):
        global current_user
        con = connect()
        cur = con.cursor()
        username = self.username.text().lower()
        password = self.password.text()
        username_regex = ("\S+@\S+\.[a-zA-Z]{2,}")
        password_regex = "^(?=.*[a-zA-Z0-9])(?=.*[\W_]).{8,}$"
        if re.match(password_regex, password) and re.match(username_regex, username):
            query = cur.execute(f'SELECT * FROM Users WHERE Email="{username}" and Password="{password}"')
            if query.fetchall():
                query = cur.execute(f'SELECT First_name, Last_name FROM Users WHERE Email="{username}"')
                fullname = query.fetchall()
                for name, name2 in fullname:
                    current_user["name"] = f"{name} {name2}"
                    current_user["email"] = username
                self.hide()
                self.secondwindow.displaydash()
            else:
                self.passworderror.setText("Invalid Username or Password")
                self.username.setText(None)
                self.password.setText(None)
        else:
            self.passworderror.setText("Invalid Username or Password")
            self.username.setText(None)
            self.password.setText(None)
        con.close()

    def signup(self):
        self.hide()
        self.signupwindow.show()
        self.signupwindow.exec()

class Signup(QDialog):
    def __init__(self, parent=None):
        super(Signup, self).__init__(parent)
        loadUi("signup_page.ui", self)
        self.firstname = self.findChild(QLineEdit, "first_name")
        self.lastname = self.findChild(QLineEdit, "last_name")
        self.gender = self.findChild(QComboBox, "gender_combo")
        self.date_edit = self.findChild(QDateEdit, "birth_date")
        self.email = self.findChild(QLineEdit, "email")
        self.password = self.findChild(QLineEdit, "password")
        self.confirm_pass = self.findChild(QLineEdit, "confirm_pass")
        self.error = self.findChild(QLabel, "err_display")
        self.back_button = self.findChild(QPushButton, "back_button")
        self.create_button = self.findChild(QPushButton, "create_account_button")


        self.create_button.clicked.connect(self.register_user)
        self.back_button.clicked.connect(self.gobacktologin)
        self.open()

    def gobacktologin(self):
        self.hide()
        loginpage = Login()
        loginpage.show()
        loginpage.exec_()

    def register_user(self):
        con = connect()
        cur = con.cursor()
        firstName = self.firstname.text().capitalize()
        lastName = self.lastname.text().capitalize()
        gender = self.gender.currentText()
        dob = self.date_edit.date().toPyDate()  # date widget changed to pydate
        email = self.email.text().lower()
        password = self.password.text()
        confirm_password = self.confirm_pass.text()
        email_regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        password_regex = re.compile(r'^(?=.*[a-zA-Z0-9])(?=.*[\W_]).{8,}$')

        if firstName == "" or lastName == ""  or email == "" or password == "" or confirm_password == "" :
            self.error.setText("\tMissing Details")
        elif not re.match(password_regex, password):
            self.error.setText("\tPassword must contain at least a lowercase, an uppercase"
                                    "\n\ta number, a special character\n\tand must not be less than 8 characters")
            self.password.clear()
            self.confirm_pass.clear()
        elif not re.match(password_regex, confirm_password):
            self.error.setText("\tPassword must contain at least a lowercase, an uppercase"
                               "\n\ta number, a special character\n\tand must not be less than 8 characters")
            self.confirm_pass.clear()
            self.password.clear()
        elif password != confirm_password:
            self.error.setText("\tPasswords do not match")
            self.confirm_pass.clear()
            self.password.clear()
        elif not re.match(email_regex, email):
            self.error.setText("\tInvalid Email")
            self.email.setText(None)
        else:
            try:
                cur.execute(
                    "INSERT INTO Users(First_name, Last_name, Gender, Date_of_birth,"
                    "Email,Password) VALUES(?,?,?,?,?,?)",
                    (firstName, lastName, gender, dob, email, password))
                con.commit()
                QMessageBox.information(self, "Success", "registration successful!")

            except sqlite3.IntegrityError:
                self.error.setText("User with email already exists.")




class Dash(QDialog):
    def __init__(self, parent=None):
        super(Dash,self).__init__(parent)
        loadUi("dashboard.ui", self)
        self.homebutton = self.findChild(QPushButton, "home_button")
        self.logoutbutton = self.findChild(QPushButton, "logout_button")
        self.searchbar = self.findChild(QLineEdit, "search_bar")
        self.searchbutton = self.findChild(QPushButton, "search_button")
        self.moreButton = self.findChild(QPushButton, "more_button")
        self.page_counter = self.findChild(QLabel, "page_counter")

        self.buttons = []
        for i in range(1, 11):
            btn = self.findChild(QPushButton, f"viewButton_{i}")
            if btn:
                self.buttons.append(btn)

        for button in self.buttons:
            button.clicked.connect(self.view_details)


        self.searchbutton.clicked.connect(self.search_movie)

        self.movies = load_movies()
        self.current_page = 1
        self.page_size = 10
        self.load_posters(self.current_page,self.page_size)
        self.moreButton.clicked.connect(self.load_next_page)
        self.page_counter.setText(str(self.current_page))

        self.menu_toggle_btn = self.findChild(QPushButton, "menu_button")
        self.menu_container = self.findChild(QWidget, "menu_container")
        self.menu_toggle_btn.clicked.connect(self.toggle_menu)
        self.setup_menu_buttons()
        if self.menu_container:
            self.menu_container.setVisible(True)
        self.menu_expanded = True

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        self.menu_container.setVisible(self.menu_expanded)

    def setup_menu_buttons(self):
        menu_buttons = self.menu_container.findChildren(QPushButton)
        for btn in menu_buttons:
            if btn.objectName() == "home_button":
                btn.clicked.connect(self.home)
            elif btn.objectName() == "favourites_button":
                btn.clicked.connect(self.favourites)
            elif btn.objectName() == "logout_button":
                btn.clicked.connect(self.logout)
            elif btn.objectName() == "watched_button":
                btn.clicked.connect(self.watched)
            elif btn.objectName() == "allmovies_button":
                btn.clicked.connect(self.movies_window)

    def displaydash(self):
        dialog = Dash()
        dialog.show()
        dialog.exec_()


    def home(self):
        self.movies = load_movies()
        self.current_page = 1
        self.load_posters(self.current_page, self.page_size)


    def logout(self):
        self.hide()
        logout = Login(self)
        logout.show()
        logout.exec_()

    def favourites(self):
        self.hide()
        favourite_window = Favourites(self)
        favourite_window.show()
        favourite_window.exec_()

    def watched(self):
        self.hide()
        dlg = Watched(self)
        dlg.show()
        dlg.exec_()

    def movies_window(self):
        self.hide()
        dlg = Movies(self)
        dlg.show()
        dlg.exec_()

    def search_movie(self):
        if not (self.searchbar and self.searchbar.text().strip()):
            QMessageBox.warning(self, "Search", "Please enter a movie title")
            return

        movie_title = self.searchbar.text().strip()
        search_results = get_movie(movie_title)

        if not search_results:
            QMessageBox.information(self, "Title", "No movie found")
            return


        if search_results['Poster'] and search_results['Poster'] != 'N/A':
            poster = search_results['Poster']
            new_poster = download_poster(movie_title, poster)
            if new_poster:
                search_results['Poster'] = new_poster
            else:
                print(f"Failed to download poster for {movie_title}")


        movie_details = MovieDetails(search_results, self)
        movie_details.exec_()

    def load_posters(self, page,page_size):
        self.current_page = page
        self.page_size = page_size
        page_movies = paginate(self.movies, self.current_page, page_size)

        for i,button in enumerate(self.buttons):
            if i < len(page_movies):
                movie = page_movies[i]
                poster_path = movie.get("Poster","")
                pixmap = QtGui.QPixmap(poster_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(120,200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    button.setIcon(QtGui.QIcon(pixmap))
                    button.setIconSize(QtCore.QSize(120,200))
                else:
                    button.setIcon(QtGui.QIcon())
                    button.setText(movie.get("Title", "No title"))

                button.movie_info = movie
            else:
                button.setIcon(QtGui.QIcon())
                button.setText("")
                button.movie_info = None

    def view_details(self):
        button = self.sender()
        movie = getattr(button, "movie_info", None)
        if not movie:
            return

        movie_details = MovieDetails(movie, self)
        movie_details.exec_()


    def load_next_page(self):
        max_pages = (len(self.movies) + self.page_size -1) // self.page_size
        if self.current_page < max_pages:
            self.load_posters(self.current_page + 1, self.page_size)
            self.page_counter.setText(str(self.current_page))
        else:
            self.load_posters(1,self.page_size)
            self.page_counter.setText(str(self.current_page))

class MovieDetails(QDialog):
    def __init__(self, movie_data, parent=None):
        super().__init__(parent)
        self.dash_parent = parent
        loadUi( "view_details screen.ui",self)
        self.title_label = self.findChild(QLabel, "title_label")
        self.genre_label = self.findChild(QLabel, "genre_label")
        self.year_label = self.findChild(QLabel, "year_label")
        self.runtime_label = self.findChild(QLabel, "runtime_label")
        self.rating_label = self.findChild(QLabel, "rating_label")
        self.plot_textedit = self.findChild(QTextEdit, "plot_textedit")
        self.actors_label = self.findChild(QLabel, "actors_label")
        self.director_label = self.findChild(QLabel, "director_label")
        self.poster_label = self.findChild(QLabel, "poster_label")
        self.save_button = self.findChild(QPushButton, "save_button")
        self.favourite_button = self.findChild(QPushButton, "favourites_button")
        self.watched_button = self.findChild(QPushButton, "watched_button")
        self.back_button = self.findChild(QPushButton, "back_button")


        self.save_button.clicked.connect(self.save_movie)
        self.favourite_button.clicked.connect(self.favourite_movie)
        self.watched_button.clicked.connect(self.watched_movie)
        self.back_button.clicked.connect(self.back_to_dash)


        self.user_email = current_user["email"]
        self.movie_data = movie_data
        self.load_movie_data(movie_data)

    def load_movie_data(self, movie_data):

        self.setWindowTitle(f"Details: {movie_data.get('Title', 'Unknown')}")

        self.title_label.setText(movie_data.get('Title', 'N/A'))
        self.genre_label.setText(movie_data.get('Genre', 'N/A'))
        self.year_label.setText(movie_data.get('Year', 'N/A'))
        self.runtime_label.setText(movie_data.get('Runtime', 'N/A'))
        self.rating_label.setText(movie_data.get('imdbRating', 'N/A'))
        self.actors_label.setText(movie_data.get('Actors', 'N/A'))
        self.director_label.setText(movie_data.get('Director', 'N/A'))
        if self.plot_textedit:
            self.plot_textedit.setPlainText(movie_data.get('Plot', 'No plot available'))
            self.plot_textedit.setReadOnly(True)


        self.load_poster(movie_data.get('Poster'))

    def load_poster(self, poster_path):
        """Load poster image from local file path"""
        if not self.poster_label:
            return

        if not poster_path or not os.path.exists(poster_path):
            self.poster_label.setText("No Poster")
            return

        try:
            # Load image file
            pixmap = QPixmap(poster_path)

            # Check if loaded successfully
            if pixmap.isNull():
                self.poster_label.setText("Invalid Image")
                return

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                self.poster_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Display
            self.poster_label.setPixmap(scaled_pixmap)
            self.poster_label.setScaledContents(True)

        except Exception :
            self.poster_label.setText("Poster Load Error")

    def save_movie(self):
        movie_title = self.movie_data.get('Title', 'N/A')

        try:

            result = save_movies(self.movie_data, movie_title ,self.user_email)
            if result:
                QMessageBox.information(self, "Success", f"Successfully saved {movie_title}")
            else:
                QMessageBox.warning(self, "Failed", f" {movie_title} already in library")

        except Exception as e :
            QMessageBox.critical(self, "Error", f"Failed to save {movie_title}!, Error: {e}")

    def get_movie_id(self):
        try:
            con = connect()
            cur = con.cursor()

            cur.execute("""
                SELECT Movie_ID FROM Movies
                JOIN Users ON Movies.User_ID = Users.User_ID
                WHERE Users.Email = ? AND Movies.Title = ?
            """, (self.user_email, self.movie_data.get('Title', 'N/A')))
            row = cur.fetchone()

            if row:
                movie_id = row[0]
                con.close()
                return movie_id
            else:
                con.close()
                QMessageBox.warning(self, "Warning", "Movie does not exist in library! Save movie first!")
                return None

        except Exception as e:
            con.close()
            QMessageBox.critical(self, "Error", f"Error: {e}")
            return None

    def update_status(self, movie_id, Favourites=None, Watched=None):

        try:
            con = connect()
            cur = con.cursor()

            if Favourites is True:
                cur.execute("""
                    UPDATE Movies 
                    SET Favourites = ? WHERE Movie_ID = ?
                """, (1, movie_id))
                con.commit()
                QMessageBox.information(self, "Success", "Movie marked as favourite")
                con.close()
            elif Watched is True:
                cur.execute("""
                    UPDATE Movies 
                    SET Watched = ? WHERE Movie_ID = ?
                """, (1, movie_id))
                con.commit()
                QMessageBox.information(self, "Success", "Movie marked as watched")
                con.close()
            else:
                QMessageBox.warning(self, "Warning", "No valid status specified!")


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {e}")


    def favourite_movie(self):
        movie_id = self.get_movie_id()
        if movie_id:
            con = connect()
            cur = con.cursor()
            cur.execute("""
            SELECT Favourites FROM Movies WHERE Movie_ID = ?
            """, (movie_id,))
            row = cur.fetchone()
            if row[0]==1:
                QMessageBox.warning(self, "Warning", "Movie already marked as favourite")
            else:
                self.update_status(movie_id, Favourites=True)
        else:
            return

    def watched_movie(self):
        movie_id = self.get_movie_id()
        if movie_id:
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        SELECT Watched FROM Movies WHERE Movie_ID = ?
                        """, (movie_id,))
            row = cur.fetchone()
            if row[0] == 1:
                QMessageBox.warning(self, "Warning", "Movie already marked as watched")
            else:
                self.update_status(movie_id, Watched=True)
        else:
            return

    def back_to_dash(self):
        self.close()

class Favourites(QDialog):
    def __init__(self, parent=None):
        super(Favourites, self).__init__(parent)
        loadUi("favourites.ui", self)
        self.home_button = self.findChild(QPushButton, "home_button")
        self.logout_button = self.findChild(QPushButton, "logout_button")
        self.menu_toggle_btn = self.findChild(QPushButton, "menu_button")
        self.menu_container = self.findChild(QWidget, "menu_container")
        self.favourite_table = self.findChild(QTableWidget, "favourite_table")
        self.genre_combo = self.findChild(QComboBox, "genre_combo")
        self.ratings_spinbox_1 = self.findChild(QDoubleSpinBox, "ratings_spinbox_1")
        self.ratings_spinbox_2 = self.findChild(QDoubleSpinBox, "ratings_spinbox_2")
        self.filter_button = self.findChild(QPushButton, "filter_button")
        self.genre_checkbox = self.findChild(QCheckBox, "genre_checkbox")
        self.ratings_checkbox = self.findChild(QCheckBox, "ratings_checkbox")


        self.genre_combo.setEnabled(False)
        self.ratings_spinbox_1.setEnabled(False)
        self.ratings_spinbox_2.setEnabled(False)

        self.home_button.clicked.connect(self.home)
        self.logout_button.clicked.connect(self.logout)
        self.filter_button.clicked.connect(self.apply_filter)

        self.user_email = current_user["email"]

        self.favourite_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.favourite_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.favourite_table.itemClicked.connect(self.open_movie_details)

        self.genre_checkbox.stateChanged.connect(self.toggle_genre_filter)
        self.ratings_checkbox.stateChanged.connect(self.toggle_ratings_filter)

        self.load_all_favourites()

        self.menu_toggle_btn.clicked.connect(self.toggle_menu)

        if self.menu_container:
            self.menu_container.setVisible(True)
        self.menu_expanded = True

        self.setup_menu_buttons()

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        self.menu_container.setVisible(self.menu_expanded)

    def setup_menu_buttons(self):
        menu_buttons = self.menu_container.findChildren(QPushButton)
        for btn in menu_buttons:
            if btn.objectName() == "home_button":
                btn.clicked.connect(self.home)
            elif btn.objectName() == "watched_button":
                btn.clicked.connect(self.watched)
            elif btn.objectName() == "logout_button":
                btn.clicked.connect(self.logout)
            elif btn.objectName() == "allmovies_button":
                btn.clicked.connect(self.movies)


    def home(self):
        self.hide()
        dlg = Dash()
        dlg.show()
        dlg.exec_()

    def logout(self):
        self.hide()
        dlg = Login()
        dlg.show()
        dlg.exec_()

    def watched(self):
        self.hide()
        dlg = Watched()
        dlg.show()
        dlg.exec_()

    def movies(self):
        self.hide()
        dlg = Movies()
        dlg.show()
        dlg.exec_()

    def open_movie_details(self, item):

        row = item.row()

        title = self.favourite_table.item(row, 0).text()
        year = self.favourite_table.item(row, 2).text()

        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT * FROM Movies 
                    JOIN Users ON Movies.User_ID = Users.User_ID 
                    WHERE Title = ? AND Year = ? AND Users.Email = ?""", (title,year, self.user_email))
        row = cur.fetchall()
        for details in row:
            movie_data = {
                "Movie_ID": details[0],"Title": details[2],"Genre": details[3],
                "Year": details[4],"Runtime": details[5],
                "Rating":details[6],"Plot":details[7],
                "Actors":details[8],"Director":details[9],
                "Poster":details[10],"Notes":details[11]
            }
        con.close()
        self.setEnabled(False)
        details_window = SavedMovieDetails(movie_data, self)
        details_window.exec_()
        self.setEnabled(True)

    def populate_table(self,movies):
        self.favourite_table.setRowCount(0)
        if movies:

            table_row = 0
            self.favourite_table.setRowCount(len(movies))
            for movie in movies:
                self.favourite_table.setItem(table_row, 0, QTableWidgetItem(movie[0]))
                self.favourite_table.setItem(table_row, 1, QTableWidgetItem(movie[1]))
                self.favourite_table.setItem(table_row, 2, QTableWidgetItem(movie[2]))

                try:
                    runtime_text = movie[3].strip()
                    if runtime_text != "" and runtime_text != "N/A":
                        runtime_min = int(runtime_text.split()[0])
                        if runtime_min >= 60:
                            runtime_display = f"{runtime_min // 60}hr {runtime_min % 60}min"
                        else:
                            runtime_display = f"{runtime_min}min"
                    else:
                        runtime_display = "N/A"
                except Exception:
                    runtime_display = "N/A"


                self.favourite_table.setItem(table_row, 3, QTableWidgetItem(runtime_display))
                self.favourite_table.setItem(table_row, 4, QTableWidgetItem(str(movie[4])))
                table_row += 1
        else:
            self.favourite_table.setRowCount(1)  # 1 empty row
            self.favourite_table.setItem(0, 0, QTableWidgetItem("No movies found"))
            self.favourite_table.setSpan(0, 0, 1, 5)  # Span across all columns
            self.favourite_table.item(0, 0).setTextAlignment(Qt.AlignCenter)


    def toggle_genre_filter(self, state):
        self.genre_combo.setEnabled(state == Qt.Checked)

    def toggle_ratings_filter(self, state):
        self.ratings_spinbox_1.setEnabled(state == Qt.Checked)
        self.ratings_spinbox_2.setEnabled(state == Qt.Checked)

    def apply_filter(self):

            self.favourite_table.setRowCount(0)
            con = connect()
            cur = con.cursor()

            try:
                genre = self.genre_combo.currentText()
                min_rating = self.ratings_spinbox_1.value()
                max_rating = self.ratings_spinbox_2.value()

                if self.genre_checkbox.isChecked() and self.ratings_checkbox.isChecked():

                    if genre and min_rating <= max_rating:
                        cur.execute("""
                            SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                            JOIN Users ON Movies.User_ID = Users.User_ID
                            WHERE Users.Email = ? 
                            AND Movies.Genre = ? 
                            AND Movies.Rating BETWEEN ? AND ?
                            AND Movies.Favourites = ?
                        """, (self.user_email, genre, min_rating, max_rating, 1))

                elif self.genre_checkbox.isChecked():
                    cur.execute("""
                        SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                        JOIN Users ON Movies.User_ID = Users.User_ID
                        WHERE Users.Email = ? AND Movies.Genre = ? AND Movies.Favourites = ?
                    """, (self.user_email, genre, 1))


                elif self.ratings_checkbox.isChecked():
                    if min_rating <= max_rating:
                        cur.execute("""
                            SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                            JOIN Users ON Movies.User_ID = Users.User_ID
                            WHERE Users.Email = ? 
                              AND Movies.Rating BETWEEN ? AND ? 
                              AND Movies.Favourites = ?
                        """, (self.user_email, min_rating, max_rating, 1))

                row = cur.fetchall()
                self.populate_table(row)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error found: {e}")
            finally:
                con.close()

    def load_all_favourites(self):
        con = connect()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                JOIN Users ON Movies.User_ID = Users.User_ID
                WHERE Users.Email = ? AND Movies.Favourites = ?
            """, (self.user_email, 1))
            row = cur.fetchall()
            self.populate_table(row)
        finally:
            con.close()


class Watched(QDialog):
    def __init__(self, parent=None):
        super(Watched, self).__init__(parent)
        loadUi("watched.ui", self)
        self.home_button = self.findChild(QPushButton, "home_button")
        self.logout_button = self.findChild(QPushButton, "logout_button")
        self.menu_toggle_btn = self.findChild(QPushButton, "menu_button")
        self.menu_container = self.findChild(QWidget, "menu_container")
        self.watched_table = self.findChild(QTableWidget, "watched_table")
        self.genre_combo = self.findChild(QComboBox, "genre_combo")
        self.ratings_spinbox_1 = self.findChild(QDoubleSpinBox, "ratings_spinbox_1")
        self.ratings_spinbox_2 = self.findChild(QDoubleSpinBox, "ratings_spinbox_2")
        self.filter_button = self.findChild(QPushButton, "filter_button")
        self.genre_checkbox = self.findChild(QCheckBox, "genre_checkbox")
        self.ratings_checkbox = self.findChild(QCheckBox, "ratings_checkbox")
        self.watchlist_combo = self.findChild(QComboBox, "watchlist_combo")

        self.genre_combo.setEnabled(False)
        self.ratings_spinbox_1.setEnabled(False)
        self.ratings_spinbox_2.setEnabled(False)

        self.home_button.clicked.connect(self.home)
        self.logout_button.clicked.connect(self.logout)
        self.filter_button.clicked.connect(self.apply_filter)

        self.user_email = current_user["email"]

        self.watched_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.watched_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.watched_table.itemClicked.connect(self.open_movie_details)

        self.genre_checkbox.stateChanged.connect(self.toggle_genre_filter)
        self.ratings_checkbox.stateChanged.connect(self.toggle_ratings_filter)

        self.load_all_watched()

        self.menu_toggle_btn.clicked.connect(self.toggle_menu)

        if self.menu_container:
            self.menu_container.setVisible(True)
        self.menu_expanded = True

        self.setup_menu_buttons()

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        self.menu_container.setVisible(self.menu_expanded)

    def setup_menu_buttons(self):
        menu_buttons = self.menu_container.findChildren(QPushButton)
        for btn in menu_buttons:
            if btn.objectName() == "home_button":
                btn.clicked.connect(self.home)
            elif btn.objectName() == "favourites_button":
                btn.clicked.connect(self.favourite)
            elif btn.objectName() == "logout_button":
                btn.clicked.connect(self.logout)
            elif btn.objectName() == "allmovies_button":
                btn.clicked.connect(self.movies)

    def home(self):
        self.hide()
        dlg = Dash()
        dlg.show()
        dlg.exec_()

    def logout(self):
        self.hide()
        dlg = Login()
        dlg.show()
        dlg.exec_()

    def favourite(self):
        self.hide()
        dlg = Favourites()
        dlg.show()
        dlg.exec_()

    def movies(self):
        self.hide()
        dlg = Movies()
        dlg.show()
        dlg.exec_()

    def open_movie_details(self, item):

        row = item.row()

        title = self.watched_table.item(row, 0).text()
        year = self.watched_table.item(row, 2).text()

        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT * FROM Movies 
                            JOIN Users ON Movies.User_ID = Users.User_ID 
                            WHERE Title = ? AND Year = ? AND Users.Email = ?""", (title, year, self.user_email))
        row = cur.fetchall()
        for details in row:
            movie_data = {
                "Movie_ID": details[0], "Title": details[2], "Genre": details[3],
                "Year": details[4], "Runtime": details[5],
                "Rating": details[6], "Plot": details[7],
                "Actors": details[8], "Director": details[9],
                "Poster": details[10], "Notes": details[11]
            }
        con.close()
        self.setEnabled(False)
        details_window = SavedMovieDetails(movie_data, self)
        details_window.exec_()
        self.setEnabled(True)

    def populate_table(self, movies):
        self.watched_table.setRowCount(0)
        if movies:

            table_row = 0
            self.watched_table.setRowCount(len(movies))
            for movie in movies:
                self.watched_table.setItem(table_row, 0, QTableWidgetItem(movie[0]))
                self.watched_table.setItem(table_row, 1, QTableWidgetItem(movie[1]))
                self.watched_table.setItem(table_row, 2, QTableWidgetItem(movie[2]))

                try:
                    runtime_text = movie[3].strip()
                    if runtime_text != "" and runtime_text != "N/A":
                        runtime_min = int(runtime_text.split()[0])
                        if runtime_min >= 60:
                            runtime_display = f"{runtime_min // 60}hr {runtime_min % 60}min"
                        else:
                            runtime_display = f"{runtime_min}min"
                    else:
                        runtime_display = "N/A"
                except Exception:
                    runtime_display = "N/A"

                self.watched_table.setItem(table_row, 3, QTableWidgetItem(runtime_display))
                self.watched_table.setItem(table_row, 4, QTableWidgetItem(str(movie[4])))
                table_row += 1
        else:
            self.watched_table.setRowCount(1)  # 1 empty row
            self.watched_table.setItem(0, 0, QTableWidgetItem("No watched movies found"))
            self.watched_table.setSpan(0, 0, 1, 5)  # Span across all columns
            self.watched_table.item(0, 0).setTextAlignment(Qt.AlignCenter)



    def toggle_genre_filter(self, state):
        self.genre_combo.setEnabled(state == Qt.Checked)

    def toggle_ratings_filter(self, state):
        self.ratings_spinbox_1.setEnabled(state == Qt.Checked)
        self.ratings_spinbox_2.setEnabled(state == Qt.Checked)

    def apply_filter(self):

        self.watched_table.setRowCount(0)
        con = connect()
        cur = con.cursor()

        try:
            genre = self.genre_combo.currentText()
            min_rating = self.ratings_spinbox_1.value()
            max_rating = self.ratings_spinbox_2.value()
            watch_status = self.watchlist_combo.currentText()

            if self.genre_checkbox.isChecked() and self.ratings_checkbox.isChecked():
                if watch_status == "Watched":
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Genre = ? 
                                      AND Movies.Rating BETWEEN ? AND ?
                                      AND Movies.Watched = ?
                                """, (self.user_email, genre, min_rating, max_rating, 1))

                elif watch_status == "To Watch":
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Genre = ? 
                                      AND Movies.Rating BETWEEN ? AND ?
                                      AND Movies.Watched = ?
                                """, (self.user_email, genre, min_rating, max_rating, 0))




            elif self.genre_checkbox.isChecked():
                if genre and watch_status == "To Watch":
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? AND Movies.Genre = ? AND Movies.Watched = ?
                                """, (self.user_email, genre, 0))
                elif genre  and watch_status == "Watched":
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? AND Movies.Genre = ? AND Movies.Watched = ?
                                """, (self.user_email, genre, 1))


            elif self.ratings_checkbox.isChecked():

                if (min_rating <= max_rating) and watch_status == "Watched" :
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Rating BETWEEN ? AND ? 
                                      AND Movies.Watched = ?
                                """, (self.user_email, min_rating, max_rating, 1))
                elif (min_rating <= max_rating) and watch_status == "To Watch":
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Rating BETWEEN ? AND ? 
                                      AND Movies.Watched = ?
                                """, (self.user_email, min_rating, max_rating, 0))

            else:

                if watch_status == "Watched":
                    cur.execute("""
                        SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                        JOIN Users ON Movies.User_ID = Users.User_ID
                        WHERE Users.Email = ? AND Movies.Watched = ?
                    """, (self.user_email, 1))
                elif watch_status == "To Watch":
                    cur.execute("""
                        SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                        JOIN Users ON Movies.User_ID = Users.User_ID
                        WHERE Users.Email = ? AND Movies.Watched = ?
                    """, (self.user_email, 0))

            row = cur.fetchall()
            self.populate_table(row)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error found: {e}")
        finally:
            con.close()

    def load_all_watched(self):
        con = connect()
        cur = con.cursor()
        try:
            cur.execute("""
                        SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                        JOIN Users ON Movies.User_ID = Users.User_ID
                        WHERE Users.Email = ? AND Movies.Watched = ? 
                    """, (self.user_email, 1))
            row = cur.fetchall()
            self.populate_table(row)
        finally:
            con.close()
class Movies(QDialog):
    def __init__(self, parent=None):
        super(Movies, self).__init__(parent)
        loadUi("all_movies.ui", self)
        self.home_button = self.findChild(QPushButton, "home_button")
        self.logout_button = self.findChild(QPushButton, "logout_button")
        self.menu_toggle_btn = self.findChild(QPushButton, "menu_button")
        self.menu_container = self.findChild(QWidget, "menu_container")
        self.allmovies_table = self.findChild(QTableWidget, "allmovies_table")
        self.genre_combo = self.findChild(QComboBox, "genre_combo")
        self.ratings_spinbox_1 = self.findChild(QDoubleSpinBox, "ratings_spinbox_1")
        self.ratings_spinbox_2 = self.findChild(QDoubleSpinBox, "ratings_spinbox_2")
        self.filter_button = self.findChild(QPushButton, "filter_button")
        self.genre_checkbox = self.findChild(QCheckBox, "genre_checkbox")
        self.ratings_checkbox = self.findChild(QCheckBox, "ratings_checkbox")

        self.genre_combo.setEnabled(False)
        self.ratings_spinbox_1.setEnabled(False)
        self.ratings_spinbox_2.setEnabled(False)

        self.home_button.clicked.connect(self.home)
        self.logout_button.clicked.connect(self.logout)
        self.filter_button.clicked.connect(self.apply_filter)

        self.user_email = current_user["email"]

        self.allmovies_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.allmovies_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.allmovies_table.itemClicked.connect(self.open_movie_details)

        self.genre_checkbox.stateChanged.connect(self.toggle_genre_filter)
        self.ratings_checkbox.stateChanged.connect(self.toggle_ratings_filter)

        self.load_all_movies()

        self.menu_toggle_btn.clicked.connect(self.toggle_menu)

        if self.menu_container:
            self.menu_container.setVisible(True)
        self.menu_expanded = True

        self.setup_menu_buttons()

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        self.menu_container.setVisible(self.menu_expanded)

    def setup_menu_buttons(self):
        menu_buttons = self.menu_container.findChildren(QPushButton)
        for btn in menu_buttons:
            if btn.objectName() == "home_button":
                btn.clicked.connect(self.home)
            elif btn.objectName() == "watched_button":
                btn.clicked.connect(self.watched)
            elif btn.objectName() == "logout_button":
                btn.clicked.connect(self.logout)
            elif btn.objectName() == "favourites_button":
                btn.clicked.connect(self.favourite)

    def home(self):
        self.hide()
        dlg = Dash()
        dlg.show()
        dlg.exec_()

    def logout(self):
        self.hide()
        dlg = Login()
        dlg.show()
        dlg.exec_()

    def watched(self):
        self.hide()
        dlg = Watched()
        dlg.show()
        dlg.exec_()

    def favourite(self):
        self.hide()
        dlg = Favourites()
        dlg.show()
        dlg.exec_()

    def open_movie_details(self, item):

        row = item.row()

        title = self.allmovies_table.item(row, 0).text()
        year = self.allmovies_table.item(row, 2).text()

        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT * FROM Movies 
                            JOIN Users ON Movies.User_ID = Users.User_ID 
                            WHERE Title = ? AND Year = ? AND Users.Email = ?""", (title, year, self.user_email))
        row = cur.fetchall()
        for details in row:
            movie_data = {
                "Movie_ID": details[0], "Title": details[2], "Genre": details[3],
                "Year": details[4], "Runtime": details[5],
                "Rating": details[6], "Plot": details[7],
                "Actors": details[8], "Director": details[9],
                "Poster": details[10], "Notes": details[11]
            }
        con.close()
        self.setEnabled(False)
        details_window = SavedMovieDetails(movie_data, self)
        details_window.exec_()
        self.setEnabled(True)

    def populate_table(self, movies):
        self.allmovies_table.setRowCount(0)
        if movies:

            table_row = 0
            self.allmovies_table.setRowCount(len(movies))
            for movie in movies:
                self.allmovies_table.setItem(table_row, 0, QTableWidgetItem(movie[0]))
                self.allmovies_table.setItem(table_row, 1, QTableWidgetItem(movie[1]))
                self.allmovies_table.setItem(table_row, 2, QTableWidgetItem(movie[2]))

                try:
                    runtime_text = movie[3].strip()
                    if runtime_text != "" and runtime_text != "N/A":
                        runtime_min = int(runtime_text.split()[0])
                        if runtime_min >= 60:
                            runtime_display = f"{runtime_min // 60}hr {runtime_min % 60}min"
                        else:
                            runtime_display = f"{runtime_min}min"
                    else:
                        runtime_display = "N/A"
                except Exception:
                    runtime_display = "N/A"

                self.allmovies_table.setItem(table_row, 3, QTableWidgetItem(runtime_display))
                self.allmovies_table.setItem(table_row, 4, QTableWidgetItem(str(movie[4])))
                table_row += 1
        else:
            self.allmovies_table.setRowCount(1)  # 1 empty row
            self.allmovies_table.setItem(0, 0, QTableWidgetItem("No movies found"))
            self.allmovies_table.setSpan(0, 0, 1, 5)  # Span across all columns
            self.allmovies_table.item(0, 0).setTextAlignment(Qt.AlignCenter)



    def toggle_genre_filter(self, state):
        self.genre_combo.setEnabled(state == Qt.Checked)

    def toggle_ratings_filter(self, state):
        self.ratings_spinbox_1.setEnabled(state == Qt.Checked)
        self.ratings_spinbox_2.setEnabled(state == Qt.Checked)

    def apply_filter(self):

        self.allmovies_table.setRowCount(0)
        con = connect()
        cur = con.cursor()

        try:
            genre = self.genre_combo.currentText()
            min_rating = self.ratings_spinbox_1.value()
            max_rating = self.ratings_spinbox_2.value()

            if self.genre_checkbox.isChecked() and self.ratings_checkbox.isChecked():
                if genre and min_rating <= max_rating:
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Genre = ? 
                                      AND Movies.Rating BETWEEN ? AND ?
                                """, (self.user_email, genre, min_rating, max_rating))

            elif self.genre_checkbox.isChecked():
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? AND Movies.Genre = ? 
                                """, (self.user_email, genre))


            elif self.ratings_checkbox.isChecked():
                min_rating = self.ratings_spinbox_1.value()
                max_rating = self.ratings_spinbox_2.value()
                if min_rating <= max_rating:
                    cur.execute("""
                                    SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                                    JOIN Users ON Movies.User_ID = Users.User_ID
                                    WHERE Users.Email = ? 
                                      AND Movies.Rating BETWEEN ? AND ? 
                                """, (self.user_email, min_rating, max_rating))

            row = cur.fetchall()
            self.populate_table(row)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error found: {e}")
        finally:
            con.close()

    def load_all_movies(self):
        con = connect()
        cur = con.cursor()
        try:
            cur.execute("""
                        SELECT Title,Genre,Year,Runtime,Rating FROM Movies
                        JOIN Users ON Movies.User_ID = Users.User_ID
                        WHERE Users.Email = ? 
                    """, (self.user_email,))
            row = cur.fetchall()
            self.populate_table(row)
        finally:
            con.close()


class SavedMovieDetails(QDialog):
    def __init__(self, movie_data, parent=None):
        super().__init__(parent)
        loadUi( "view_details screen_saved.ui",self)
        self.title_label = self.findChild(QLabel, "title_label")
        self.genre_label = self.findChild(QLabel, "genre_label")
        self.year_label = self.findChild(QLabel, "year_label")
        self.runtime_label = self.findChild(QLabel, "runtime_label")
        self.rating_label = self.findChild(QLabel, "rating_label")
        self.plot_textedit = self.findChild(QTextEdit, "plot_textedit")
        self.actors_label = self.findChild(QLabel, "actors_label")
        self.director_label = self.findChild(QLabel, "director_label")
        self.poster_label = self.findChild(QLabel, "poster_label")
        self.save_button = self.findChild(QPushButton, "save_button")
        self.back_button = self.findChild(QPushButton, "back_button")
        self.personalnote = self.findChild(QLineEdit, "personal_notes")
        self.addbutton = self.findChild(QPushButton, "add_button")
        self.deletebutton = self.findChild(QPushButton, "delete_button")

        self.addbutton.clicked.connect(self.save_personal_note)
        self.deletebutton.clicked.connect(self.clear_personal_note)




        self.back_button.clicked.connect(self.back_to_parent)


        self.user_email = current_user["email"]
        self.movie_id = movie_data.get('Movie_ID', None)
        self.movie_data = movie_data
        self.load_movie_data(movie_data)

    def load_movie_data(self, movie_data):

        self.setWindowTitle(f"Details: {movie_data.get('Title', 'Unknown')}")

        self.title_label.setText(movie_data.get('Title', 'N/A'))
        self.genre_label.setText(movie_data.get('Genre', 'N/A'))
        self.year_label.setText(movie_data.get('Year', 'N/A'))
        self.runtime_label.setText(movie_data.get('Runtime', 'N/A'))
        self.rating_label.setText(movie_data.get('imdbRating', 'N/A'))
        self.actors_label.setText(movie_data.get('Actors', 'N/A'))
        self.director_label.setText(movie_data.get('Director', 'N/A'))

        self.plot_textedit.setPlainText(movie_data.get('Plot', 'No plot available'))
        self.plot_textedit.setReadOnly(True)

        self.personalnote.setText(movie_data.get('Notes', ''))

        self.load_poster(movie_data.get('Poster'))

    def load_poster(self, poster_path):
        """Load poster image from local file path"""
        if not self.poster_label:
            return

        if not poster_path or not os.path.exists(poster_path):
            self.poster_label.setText("No Poster")
            return

        try:
            # Load image file
            pixmap = QPixmap(poster_path)

            # Check if loaded successfully
            if pixmap.isNull():
                self.poster_label.setText("Invalid Image")
                return

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                self.poster_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Display
            self.poster_label.setPixmap(scaled_pixmap)
            self.poster_label.setScaledContents(True)

        except Exception :
            self.poster_label.setText("Poster Load Error")

    def back_to_parent(self):
        self.close()

    def save_personal_note(self):

        if not self.personalnote or not self.movie_id:
            QMessageBox.warning(self, "Error", "No note or movie ID!")
            return

        note = self.personalnote.text().strip()
        con = connect()
        cur = con.cursor()

        try:
            cur.execute("""
                UPDATE Movies SET Notes = ? 
                WHERE Movie_ID = ?
            """, (note, self.movie_id))
            con.commit()
            QMessageBox.information(self, "Success", "Note saved!")

        except Exception:
            QMessageBox.warning(self, "Error", "Failed to save note!")

    def clear_personal_note(self):

        if not self.personalnote or not self.movie_id:
            QMessageBox.warning(self, "Error", "No note field or movie ID!")
            return

        con = connect()
        cur = con.cursor()

        try:
            # DELETE note from database (set to empty string)
            cur.execute("UPDATE Movies SET Notes = ? WHERE Movie_ID = ?", ('', self.movie_id))
            con.commit()

            # Clear the text field
            self.personalnote.clear()

            QMessageBox.information(self, "Deleted", "Personal note removed from database!")

        except Exception:
            QMessageBox.warning(self, "Error", "Failed to delete note from database!")
        finally:
            con.close()







if __name__ == '__main__':
    app = QApplication(sys.argv)
    Load_Screen = Login()
    Load_Screen.exec_()
    sys.exit(app.exec_())