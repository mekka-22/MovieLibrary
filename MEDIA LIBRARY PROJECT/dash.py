import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QLabel, QWidget, QDialog)
from PyQt5.uic import loadUi
from load_movies import load_movies, paginate, download_poster
from API_medialib import get_movie

class Dash(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("dashboard.ui", self)  # Requires dashboard.ui file

        # Find UI elements safely
        self.homebutton = self.findChild(QPushButton, "home_button")
        self.logoutbutton = self.findChild(QPushButton, "logout_button")
        self.searchbar = self.findChild(QLineEdit, "search_bar")
        self.searchbutton = self.findChild(QPushButton, "search_button")
        self.moreButton = self.findChild(QPushButton, "more_button")

        # Find grid buttons dynamically
        all_buttons = self.findChildren(QPushButton)
        self.buttons = [b for b in all_buttons if b.objectName().startswith("viewButton_")]
        self.buttons.sort(key=lambda b: int(b.objectName().split("_")[-1]))

        # Connect signals
        for button in self.buttons:
            button.clicked.connect(self.view_details)

        if self.homebutton:
            self.homebutton.clicked.connect(self.home)
        if self.logoutbutton:
            self.logoutbutton.clicked.connect(self.logout)
        if self.searchbutton:
            self.searchbutton.clicked.connect(self.searchmovie)
        if self.moreButton:
            self.moreButton.clicked.connect(self.load_next_page)

        # Menu toggle
        self.menu_toggle_btn = self.findChild(QPushButton, "menu_button")
        self.menu_container = self.findChild(QWidget, "menu_container")
        if self.menu_toggle_btn and self.menu_container:
            self.menu_toggle_btn.clicked.connect(self.toggle_menu)
            self.menu_container.setVisible(False)
            self.menu_expanded = False

        # Load movies (handle if module missing)
        try:
            self.movies = load_movies()
            self.current_page = 1
            self.page_size = len(self.buttons)  # Dynamic to grid size
            self.load_posters(self.current_page, self.page_size)
        except ImportError:
            print("load_movies module missing - skipping movie load")
            self.movies = []

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        self.menu_container.setVisible(self.menu_expanded)

    def home(self):
        """Placeholder - replace with your home logic"""
        print("Home clicked")
        self.close()

    def logout(self):
        """Placeholder - replace with login screen"""
        print("Logout clicked")
        self.close()

    def searchmovie(self):
        """Placeholder search"""
        query = self.searchbar.text()
        print(f"Search: {query}")

    def load_posters(self, page, page_size):
        self.current_page = page
        self.page_size = page_size
        if hasattr(self, 'movies') and self.movies:
            page_movies = paginate(self.movies, page, page_size)
        else:
            page_movies = []

        for i, button in enumerate(self.buttons):
            if i < len(page_movies):
                movie = page_movies[i]
                poster_path = movie.get("Poster", "")
                pixmap = QtGui.QPixmap(poster_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        140, 210,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation
                    )
                    button.setIcon(QtGui.QIcon(pixmap))
                    button.setIconSize(QtCore.QSize(140, 210))
                    button.setText("")
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

        # Placeholder details dialog
        title = movie.get("Title", "Unknown")
        QtWidgets.QMessageBox.information(
            self, "Movie Details",
            f"Title: {title}\\nYear: {movie.get('Year', 'N/A')}"
        )

    def load_next_page(self):
        if not hasattr(self, 'movies') or not self.movies:
            return
        max_pages = (len(self.movies) + self.page_size - 1) // self.page_size
        if self.current_page < max_pages:
            self.load_posters(self.current_page + 1, self.page_size)
        else:
            self.load_posters(1, self.page_size)


def displaydash():
    """Launch the dashboard - FIXED: now properly defined"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    dialog = Dash()
    dialog.exec_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    displaydash()  # FIXED: call function, not class method
