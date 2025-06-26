import sys
import pyodbc
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

# Load the UI file
app = QtWidgets.QApplication(sys.argv)
ui = uic.loadUi("C:\\Users\\Adilg\\Desktop\\New Folder (3)\\Gamingsystem.ui")

# Set up the database connection
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=ADIL-KA-LAPTOP\\ADILSQLSERVER;"
    "Database=gamingzone;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

# Function to show the login page
def show_login_page():
    ui.stackedWidget.setCurrentIndex(1)  # Show login index

# Function to show the signup page
def show_signup_page():
    ui.stackedWidget.setCurrentIndex(2)  # Show signup index

def get_user_id_from_username(username):
    cursor.execute("SELECT UserID FROM Users WHERE Name = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        print(f"User ID: {result[0]}")  # Add this to verify the returned UserID
        return result[0]  # Return the UserID
    else:
        print("User not found!")
        return None


def user_login():
    username = ui.usernameInput.text()  # Username input from login page
    password = ui.passwordInput.text()  # Password input from login page

    # Check if username and password are empty
    if not username or not password:
        QMessageBox.warning(ui, "Login Error", "Please enter both username and password.")
        return

    # Query the database to check for valid user credentials
    cursor.execute("SELECT UserID, Name, password, Role FROM Users WHERE Name = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        user_id, username, password, role = user  #find out role as well
        
        if role == 'Manager':
            QMessageBox.information(ui, "Login Successful", "Welcome, Manager!")
            # Switch to the admin screen
            ui.stackedWidget.setCurrentIndex(5) 
            refresh_admin_games_table() 
            populate_Admin_booking()
        else:
            QMessageBox.information(ui, "Login Successful", f"Welcome, {username}!")
            # Proceed to the user screen
            ui.stackedWidget.setCurrentIndex(3)  
            load_games()

        # After successful login, load current bookings for user
        load_current_bookings(user_id)  
    else:
        QMessageBox.warning(ui, "Login Error", "Invalid username or password.")





# Function to handle signup
def user_signup():
    username = ui.signupUsernameInput.text()  # Username input from signup page
    email = ui.emailInput.text()  # Email input from signup page
    password = ui.passwordSignupInput.text()  # Password input from signup page
    confirm_password = ui.confirmPasswordInput.text()  # Confirm password input from signup page
    role = ui.roleComboBox.currentText()  # Get selected role from combo box
    contact = ui.contactInput.text()  # Get contact number from new line edit


    # Check if all fields are filled
    if not username or not email or not password or not confirm_password:
        QMessageBox.warning(ui, "Signup Error", "Please fill all fields.")
        return

    # Check if passwords match
    if password != confirm_password:
        QMessageBox.warning(ui, "Signup Error", "Passwords do not match.")
        return

    # Insert new user into the database
    cursor.execute("INSERT INTO Users (Name, email, contact, password, role) VALUES (?, ?, ?, ?, ?)", (username, email, contact, password, role))
    conn.commit()

    QMessageBox.information(ui, "Signup Successful", "Account created successfully. Please log in.")
    
    # Return to the login page
    ui.stackedWidget.setCurrentIndex(1)

# Connect the buttons to their respective functions
ui.adminButton.clicked.connect(show_login_page)
ui.userButton.clicked.connect(show_login_page)
ui.loginButton.clicked.connect(user_login)  # Login button
ui.signupButton.clicked.connect(show_signup_page)  # Show signup page
ui.submitSignupButton.clicked.connect(user_signup)  # Submit signup form


def load_games():
    cursor.execute("SELECT GameTitle FROM Games")
    games = cursor.fetchall()
    ui.gamesTable.setRowCount(0)  # Clear previous rows
    for row_index, game in enumerate(games):
        ui.gamesTable.insertRow(row_index)
        ui.gamesTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(game[0]))


def load_current_bookings(user_id):
    query = """
    SELECT G.GameTitle, T.Date, T.Time, B.DeviceID
    FROM Bookings AS B
    INNER JOIN Games AS G ON B.GameID = G.GameID
    INNER JOIN Timeslots AS T ON B.TimeslotID = T.TimeslotID
    WHERE B.UserID = ?
    """
    
    # Execute the query with the user_id as a parameter
    cursor.execute(query, (user_id,))  # Pass user_id as a parameter to the query
    
    # find the results
    bookings = cursor.fetchall()



    # Update the UI with the fetched data
    ui.currentBookingsTable.setRowCount(0)  # Clear previous rows
    for row_index, booking in enumerate(bookings):
        ui.currentBookingsTable.insertRow(row_index)
        ui.currentBookingsTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(booking[0]))  # Game Title
        ui.currentBookingsTable.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(booking[1])))  # Date
        ui.currentBookingsTable.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(booking[2])))  # Time
        ui.currentBookingsTable.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(booking[3])))  # Device ID



def on_book_button_click():
    # Switch to booking screen from user menu
    ui.stackedWidget.setCurrentWidget(ui.bookingPage)  # Assuming you're using a stacked widget for different screens
    
    # Populate the game combo box with available games
    populate_games_combo()
    
    # Populate devices combo box based on the selected game
    populate_devices_combo(ui.gameSelectionComboBox.currentText())

    # Connect the game selection to update the device combo box when the selected game changes
    ui.gameSelectionComboBox.currentTextChanged.connect(lambda: populate_devices_combo(ui.gameSelectionComboBox.currentText()))
    
    # Connect the date and time edit widgets to refresh the current bookings based on the date and time
    ui.dateEdit.dateChanged.connect(lambda: update_booking_table_based_on_date_time())
    ui.timeEdit.timeChanged.connect(lambda: update_booking_table_based_on_date_time())

    # Connect the confirm booking button to handle the booking process
    ui.confirmBookingButton.clicked.connect(on_confirm_booking_button_click)


def populate_games_combo():
    cursor.execute("SELECT GameTitle FROM Games")
    games = cursor.fetchall()
    
    ui.gameSelectionComboBox.clear()  # Clear existing items
    for game in games:
        ui.gameSelectionComboBox.addItem(game[0])  # Add game titles to the combo box

def populate_devices_combo(selected_game):
    # Check if selected_game is not empty
    if not selected_game:
        print("No game selected.")
        return

    cursor.execute("SELECT GameID FROM Games WHERE GameTitle = ?", (selected_game,))
    game_id = cursor.fetchone()

    # If the game ID is not found, handle the error
    if game_id is None:
        print(f"Error: Game '{selected_game}' not found in the database.")
        ui.stationComboBox.clear()  # Clear the combo box
        ui.stationComboBox.addItem("No devices available")
        return  # Exit the function

    game_id = game_id[0]  # Get the GameID for the selected game
    
    # Now get the available devices for the selected game
    cursor.execute("""
    SELECT GA.DeviceID
    FROM GameAvailability GA
    WHERE GA.GameID = ?
    """, (game_id,))
    
    devices = cursor.fetchall()

    # Clear existing devices in the combo box
    ui.stationComboBox.clear()
    
    # If no devices are found, notify the user
    if not devices:
        ui.stationComboBox.addItem("No devices available")
    else:
        # Add each device to the combo box
        for device in devices:
            ui.stationComboBox.addItem(str(device[0]))  # Add device IDs to the combo box


def add_booking(selected_game, selected_date, selected_time, selected_device, current_user_id):
    # Insert the timeslot into the Timeslots table if it doesn't exist
    cursor.execute("""
    IF NOT EXISTS (
        SELECT 1
        FROM Timeslots
        WHERE Date = ? AND Time = ?
    )
    BEGIN
        INSERT INTO Timeslots (Date, Time)
        VALUES (?, ?);
    END;
    """, (selected_date, selected_time, selected_date, selected_time))

    # Commit the timeslot insertion
    cursor.commit()

    # Retrieve the TimeslotID for the selected date and time
    cursor.execute("""
    SELECT TimeslotID
    FROM Timeslots
    WHERE Date = ? AND Time = ?;
    """, (selected_date, selected_time))
    timeslot_id = cursor.fetchone()[0]

    # Insert the booking into the Bookings table
    cursor.execute("""
    INSERT INTO Bookings (GameID, TimeslotID, UserID, DeviceID)
    SELECT 
        (SELECT GameID FROM Games WHERE GameTitle = ?),
        ?,  -- TimeslotID
        ?,  -- UserID
        (SELECT DeviceID FROM GameAvailability WHERE GameID = (SELECT GameID FROM Games WHERE GameTitle = ?) AND DeviceID = ?)
    WHERE NOT EXISTS (
        SELECT 1
        FROM Bookings
        WHERE TimeslotID = ?
        AND DeviceID = ?
    );
    """, (selected_game, timeslot_id, current_user_id, selected_game, selected_device, timeslot_id, selected_device))

    # Commit the booking insertion
    cursor.commit()

    # Refresh the bookings table
    populate_current_bookings(current_user_id)

    # Inform the user of a successful booking

def populate_current_bookings(user_id, selected_date=None, selected_time=None):
    query = """
    SELECT G.GameTitle, T.Date, T.Time, B.DeviceID
    FROM Bookings AS B
    INNER JOIN Games AS G ON B.GameID = G.GameID
    INNER JOIN Timeslots AS T ON B.TimeslotID = T.TimeslotID
    WHERE B.UserID = ?
    """
    cursor.execute(query, (user_id,))

    bookings = cursor.fetchall()

    # Debugging: Check if any bookings are returned
    print(f"Bookings fetched: {bookings}")  # This will print the bookings list

    ui.currentBookingsTable.setRowCount(0)  # Clear previous rows
    for row_index, booking in enumerate(bookings):
        ui.currentBookingsTable.insertRow(row_index)
        ui.currentBookingsTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(booking[0]))  # Game Title
        ui.currentBookingsTable.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(booking[1])))  # Date
        ui.currentBookingsTable.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(booking[2])))  # Time
        ui.currentBookingsTable.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(booking[3])))  # Device ID



def update_booking_table_based_on_date_time():
    selected_date = ui.dateEdit.date().toString('yyyy-MM-dd')
    selected_time = ui.timeEdit.time().toString('HH:mm')
    populate_current_bookings(get_user_id_from_username(ui.usernameInput.text()), selected_date, selected_time)



def on_confirm_booking_button_click():
    selected_game = ui.gameSelectionComboBox.currentText()  # Get the selected game
    selected_date = ui.dateEdit.date().toString('yyyy-MM-dd')  # Ensure the format is correct
    selected_time = ui.timeEdit.time().toString('HH:mm')  # Ensure the format is correct
    selected_device = ui.stationComboBox.currentText()  # Get the selected device
    current_user_id = get_user_id_from_username(ui.usernameInput.text())  # Get the current user ID
    
    # Add the booking
    add_booking(selected_game, selected_date, selected_time, selected_device, current_user_id)
    
    # Show a success message
    QtWidgets.QMessageBox.information(ui, "Success", "Booking made successfully!")

    # Update the bookings table on the user menu
    populate_current_bookings(current_user_id)
    ui.stackedWidget.setCurrentIndex(3)  # Assuming index 3 is the user screen


def delete_all_bookings(user_id):
    cursor.execute("""
    DELETE FROM Bookings
    WHERE UserID = ?
    """, (user_id,))
    cursor.commit()
    QtWidgets.QMessageBox.information(ui, "Success", "All bookings deleted successfully.")
    populate_current_bookings(user_id)  # Refresh the booking table

def delete_selected_booking(user_id):
    selected_row = ui.currentBookingsTable.currentRow()  # Get the currently selected row
    if selected_row == -1:  # No row is selected
        QtWidgets.QMessageBox.warning(ui, "Warning", "Please select a booking to delete.")
        return

    # Extract booking details from the selected row
    game_title = ui.currentBookingsTable.item(selected_row, 0).text() if ui.currentBookingsTable.item(selected_row, 0) else None
    booking_date = ui.currentBookingsTable.item(selected_row, 1).text() if ui.currentBookingsTable.item(selected_row, 1) else None
    booking_time = ui.currentBookingsTable.item(selected_row, 2).text() if ui.currentBookingsTable.item(selected_row, 2) else None
    device_id = ui.currentBookingsTable.item(selected_row, 3).text() if ui.currentBookingsTable.item(selected_row, 3) else None

    # Ensure that all necessary data was extracted
    if None in (game_title, booking_date, booking_time, device_id):
        QtWidgets.QMessageBox.warning(ui, "Warning", "Incomplete booking data. Please select a valid booking.")
        return

    # Fetch the corresponding TimeslotID for the selected date and time
    cursor.execute("""
    SELECT TimeslotID
    FROM Timeslots
    WHERE Date = ? AND Time = ?
    """, (booking_date, booking_time))
    
    timeslot_id = cursor.fetchone()
    
    if not timeslot_id:
        QtWidgets.QMessageBox.warning(ui, "Warning", "Timeslot not found. Unable to delete booking.")
        return
    
    timeslot_id = timeslot_id[0]  # Extract the TimeslotID



    # Delete the booking from the database using TimeslotID, GameID, DeviceID, and UserID
    cursor.execute("""
    DELETE FROM Bookings
    WHERE UserID = ?
      AND GameID = (SELECT GameID FROM Games WHERE GameTitle = ?)
      AND TimeslotID = ?
      AND DeviceID = ?
    """, (user_id, game_title, timeslot_id, device_id))

    cursor.commit()  # Commit changes to the database

    # Refresh the booking table
    populate_current_bookings(user_id)
    QtWidgets.QMessageBox.information(ui, "Success", "Selected booking has been deleted.")



def logout():
    ui.stackedWidget.setCurrentIndex(1)  # Switch back to login page
    ui.usernameInput.clear()  # Clear username input for security


ui.cancelSelectedBookingButton.clicked.connect(lambda: delete_selected_booking(get_user_id_from_username(ui.usernameInput.text())))
ui.cancelBookingButton.clicked.connect(lambda: delete_all_bookings(get_user_id_from_username(ui.usernameInput.text())))
ui.bookButton.clicked.connect(on_book_button_click)
ui.logoutButton.clicked.connect(logout)

# Initialize the user page by loading available games and current bookings
load_games()


def go_to_add_game_page():
    # Navigate to the add game page
    ui.stackedWidget.setCurrentIndex(6) 

def add_game():
    # Get the values from the UI inputs
    game_name = ui.gameNameInput.text()
    game_genre = ui.gameGenreInput.text()
    game_stations = ui.gameStationsInput.text()  # DeviceNum (comma-separated)
    game_time_slots = ui.gameTimeSlotsInput.text()  # Time slots (comma-separated)

    # Check if the required fields are filled
    if not game_name or not game_genre or not game_stations or not game_time_slots:
        QMessageBox.warning(ui, "Input Error", "Please fill out all fields.")
        return

    # Split the stations and time slots by commas
    stations_list = [station.strip() for station in game_stations.split(',')]
    time_slots_list = [time.strip() for time in game_time_slots.split(',')]

    # Insert the game into the Games table
    cursor.execute("""
        INSERT INTO Games (GameTitle)
        VALUES (?)
    """, (game_name))

    # Get the GameID of the newly inserted game
    cursor.execute("SELECT GameID FROM Games WHERE GameTitle = ?", (game_name,))
    game_id = cursor.fetchone()[0]

    # Cross-check inputted device numbers with existing Devices
    for station in stations_list:
        cursor.execute("SELECT DeviceID FROM Devices WHERE DeviceNum = ?", (station,))
        device_data = cursor.fetchone()

        if device_data:
            device_id = device_data[0]  # Get the existing DeviceID
            # Add entry to GameAvailability
            cursor.execute("""
                INSERT INTO GameAvailability (GameID, DeviceID)
                VALUES (?, ?)
            """, (game_id, device_id))
        else:
            # Handle the case where the station/device does not exist
            QMessageBox.warning(ui, "Error", f"Device {station} does not exist in the system.")
            return

    # Commit the changes to the database
    cursor.commit()

    # Show success message
    QMessageBox.information(ui, "Success", "Game added successfully!")

    # Optionally, reset the input fields
    ui.gameNameInput.clear()
    ui.gameGenreInput.clear()
    ui.gameStationsInput.clear()
    ui.gameTimeSlotsInput.clear()
    ui.stackedWidget.setCurrentIndex(5) 
    refresh_admin_games_table()

def delete_game():
    # Get the selected row from the admin games table
    selected_row = ui.adminGamesTable.currentRow()  # Assuming this is the games table
    if selected_row == -1:  # No row is selected
        QMessageBox.warning(ui, "Warning", "Please select a game to delete.")
        return

    # Extract the game title from the selected row
    game_title = ui.adminGamesTable.item(selected_row, 0).text() if ui.adminGamesTable.item(selected_row, 0) else None

    if not game_title:
        QMessageBox.warning(ui, "Warning", "Invalid selection. Game title not found.")
        return


    # Fetch the GameID of the selected game
    cursor.execute("SELECT GameID FROM Games WHERE GameTitle = ?", (game_title,))
    game_data = cursor.fetchone()

    if not game_data:
        QMessageBox.warning(ui, "Error", f"Game '{game_title}' does not exist in the database.")
        return

    game_id = game_data[0]

    # Begin deletion: remove references in related tables first
    try:
        # Delete from GameAvailability
        cursor.execute("DELETE FROM GameAvailability WHERE GameID = ?", (game_id,))

        # Delete from Bookings (if required)
        cursor.execute("DELETE FROM Bookings WHERE GameID = ?", (game_id,))

        # Delete from Games
        cursor.execute("DELETE FROM Games WHERE GameID = ?", (game_id,))

        # Commit the changes
        cursor.commit()

        # Refresh the admin games table
        refresh_admin_games_table()

        QMessageBox.information(ui, "Success", f"Game '{game_title}' has been deleted successfully!")

    except Exception as e:
        # Rollback in case of error
        cursor.rollback()
        QMessageBox.critical(ui, "Error", f"An error occurred while deleting the game: {str(e)}")



def refresh_admin_games_table():
    # Clear the existing rows in the table
    ui.adminGamesTable.setRowCount(0)

    cursor.execute("SELECT GameTitle FROM Games")
    games = cursor.fetchall()

    for row_index, game in enumerate(games):
        ui.adminGamesTable.insertRow(row_index)
        ui.adminGamesTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(game[0]))  # Game Title


def populate_Admin_booking():
    query = """
    SELECT G.GameTitle, T.Date, T.Time, B.DeviceID, B.UserID
    FROM Bookings AS B
    INNER JOIN Games AS G ON B.GameID = G.GameID
    INNER JOIN Timeslots AS T ON B.TimeslotID = T.TimeslotID
    """
    cursor.execute(query, ())

    bookings = cursor.fetchall()

    ui.adminBookingsTable.setRowCount(0)  # Clear previous rows
    for row_index, booking in enumerate(bookings):
        ui.adminBookingsTable.insertRow(row_index)
        ui.adminBookingsTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(booking[0]))  # Game Title
        ui.adminBookingsTable.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(booking[1])))  # Date
        ui.adminBookingsTable.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(booking[2])))  # Time
        ui.adminBookingsTable.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(booking[3])))  # Device ID
        ui.adminBookingsTable.setItem(row_index, 4, QtWidgets.QTableWidgetItem(str(booking[4])))  # UserID


def delete_all_bookings_Admin():
    cursor.execute("""
    DELETE FROM Bookings
=    """, ())
    cursor.commit()
    QtWidgets.QMessageBox.information(ui, "Success", "All bookings deleted successfully.")
    populate_Admin_booking()  # Refresh the booking table


def delete_selected_Admin_booking():
    selected_row = ui.adminBookingsTable.currentRow()  # Get the currently selected row
    if selected_row == -1:  # No row is selected
        QtWidgets.QMessageBox.warning(ui, "Warning", "Please select a booking to delete.")
        return

    # Extract booking details from the selected row
    game_title = ui.adminBookingsTable.item(selected_row, 0).text() if ui.adminBookingsTable.item(selected_row, 0) else None
    booking_date = ui.adminBookingsTable.item(selected_row, 1).text() if ui.adminBookingsTable.item(selected_row, 1) else None
    booking_time = ui.adminBookingsTable.item(selected_row, 2).text() if ui.adminBookingsTable.item(selected_row, 2) else None
    device_id = ui.adminBookingsTable.item(selected_row, 3).text() if ui.adminBookingsTable.item(selected_row, 3) else None
    user_id = ui.adminBookingsTable.item(selected_row, 4).text() if ui.adminBookingsTable.item(selected_row, 4) else None

    # Debugging: Print extracted values to check if they are valid
    print(f"Game Title: {game_title}, Booking Date: {booking_date}, Booking Time: {booking_time}, Device ID: {device_id}, User ID: {user_id}")

    # Ensure that all necessary data was extracted
    if None in (game_title, booking_date, booking_time, device_id, user_id):
        QtWidgets.QMessageBox.warning(ui, "Warning", "Incomplete booking data. Please select a valid booking.")
        return

    # Fetch the corresponding TimeslotID for the selected date and time
    cursor.execute("""
    SELECT TimeslotID
    FROM Timeslots
    WHERE Date = ? AND Time = ?
    """, (booking_date, booking_time))
    
    timeslot_id = cursor.fetchone()
    
    if not timeslot_id:
        QtWidgets.QMessageBox.warning(ui, "Warning", "Timeslot not found. Unable to delete booking.")
        return
    
    timeslot_id = timeslot_id[0]  # Extract the TimeslotID

    # Delete the booking from the database using TimeslotID, GameID, DeviceID, and UserID
    cursor.execute("""
    DELETE FROM Bookings
    WHERE UserID = ?
      AND GameID = (SELECT GameID FROM Games WHERE GameTitle = ?)
      AND TimeslotID = ?
      AND DeviceID = ?
    """, (user_id, game_title, timeslot_id, device_id))

    cursor.commit()  # Commit changes to the database

    # Refresh the booking table
    populate_Admin_booking()
    QtWidgets.QMessageBox.information(ui, "Success", "Selected booking has been deleted.")




ui.deleteBookingButton.clicked.connect(lambda: delete_selected_Admin_booking())
ui.deleteAllBookingsButton.clicked.connect(lambda: delete_all_bookings_Admin())
ui.deleteGameButton.clicked.connect(delete_game)
ui.addGameButton.clicked.connect(go_to_add_game_page)
ui.submitGameButton.clicked.connect(add_game)
ui.AdminlogoutButton.clicked.connect(logout)


# Start the application
ui.stackedWidget.setCurrentIndex(0)
ui.show()
sys.exit(app.exec())
