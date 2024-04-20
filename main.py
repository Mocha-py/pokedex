import tkinter as tk
from tkinter import ttk
import hashlib
import pandas as pd
import requests
import re
import json
import os

# lambda to remove a user from a dataframe, takes the dataframe and current user as params
remove_user = lambda df, current_user : df.drop(current_user['id'])

# lambda to save data to the csv
save_data = lambda df : df.to_csv("UserData.csv", encoding="utf-8", index=False) 


def hash_password(password):
    '''
    Hashes password using sha256
    :param password: password to hash
    :returns: hashed password
    '''
    # encode the password as bytes
    password_bytes = password.encode('utf-8')
    
    # create a hash object with the password
    hashed_obj = hashlib.sha256(password_bytes)
    
    # get the hexadecimal representation of the hash
    hashed_password = hashed_obj.hexdigest()
    
    # return the now hashed password
    return hashed_password
    

def check_user_exists(df, name):
    '''
    Checks if a user exists in a dataframe by checking
    for the username
    :param df: pandas dataframe
    :param name: the name of the user you are searching for (str)
    :returns: True if user is found, False if not (bool)
    '''
    # if the user is located in the dataframe
    if len(df.index[df['username'] == name].tolist()) > 0: 
        #return that the user is found
        return True 
    # if the user is not found
    else: 
        # return that the user was not found
        return False 
        

def add_user(df, name, password):
    '''
    Adds a new user to a dataframe
    :param df: pandas dataframe
    :param name: desired name for new user (str)
    :param password: desired password for new user (str)
    :returns: the dataframe entered in the parameters updated with
    the new user.
    '''
    # hash the password
    hashed_password = hash_password(password)
    # create a dictionary of the new users data
    new_user_data = {
        'username': name,
        'password': hashed_password
    } 
    # add a new row of the new user's data
    df.loc[len(df)] = new_user_data 
    # fill the empty new slots with None
    df = df.fillna('None') 
    # return the dataframe
    return df

def rename_user(app, new_name):
    '''
    Function to rename the currently logged
    in user.
    :param app: instance of application
    :param new_name: The new name for the user (str)
    :returns: none
    '''
    #change the username of the current user to the new name
    app.user_data.loc[app.current_user['id'], 'username'] = new_name 
    
    # change current_user data to contain new name
    app.current_user['name'] = new_name 
    return

def change_password(app, new_pass):
    '''
    Function to change the password of the current user.
    :param app: instance of application
    :param new_pass: the new password for the user (str)
    :returns: none
    '''
    # hash the new password
    hashed_new_pass = hash_password(new_pass)
    # change the password of the current user to the new hashed password
    app.user_data.loc[app.current_user['id'], 'password'] = hashed_new_pass 
    
    return

def login(app, username, password):
    '''
    Attempts to login to a users account.
    :param app: instance of application
    :param username: the name of the user to log in (str)
    :param password: the attempted password of the user (str)
    :returns: True if successful and False if not (bool), this will
    also set the global dictionary current_user's "name" and "id"
    keys to the value of the username and the row of the users data on the
    dataframe.
    '''
    # check if user exists
    exists = check_user_exists(app.user_data, username)

    # if the user does not exist
    if exists == False: 
        # return that the login failed
        return False 
        
    # get the row in the dataframe of the user attempting to sign in
    row = app.user_data.index[app.user_data['username'] == username].tolist()[0] 
    
    # if the password matches
    if hash_password(password) == app.user_data.loc[row, 'password']: 
        # set current users name to the username
        app.current_user['name'] = username 
        
        # set the current users ID to the row the user was found on in the dataframe
        app.current_user['id'] = row 
        
        # return that the login was successful
        return True 
        
    # if failed: 
    else: 
        # return that the credentials did not match a user on the system
        return False 
        

def logout(app):
    '''
    Logs out of the current users
    account, setting the current user values
    of "name" and "id" to None.
    :param app: MainApplication class
    :returns: None
    '''
    # set the current_user data back to default (None)
    app.current_user = {
        'name': None,
        'id' : None
    } 
    return

def delete_user(app):
    '''
    Deletes the user given in the parameters
    from the dataframe
    :param app: instance of application
    :returns: none
    '''
    # removes the current user from the dataframe, deleting them
    app.user_data = app.user_data.drop(app.current_user['id'])

    # logout of the user's account to finalise this
    logout(app)
    

class MainApplication(tk.Tk):
    '''class for the main application (tkinter window)'''
    def __init__(self, dataframe):
        '''
        initialises application
        :param self: instance of application
        :param dataframe: pandas dataframe containing user data
        '''
        super().__init__()
        # sets the title of the application window
        self.title('Pokedex')

        # get screen dimensions information
        scr_width=self.winfo_screenwidth()
        scr_height=self.winfo_screenheight()

        # sets the application window size
        self.geometry(f"{scr_width}x{scr_height}")

        # sets the cursor to be ditto
        self.config(cursor="@132.cur")

        # stores the csv/dataframe/user data
        self.user_data = dataframe

        # stores whether or not passwords are to be hidden on the application
        self._password_hidden = True

        # stores the regular expression for a valid pokedex password
        self.password_regex = re.compile("^(?!.*[,])(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")

        # stores the current users name and row index
        self.current_user = {
            'name': None,
            'id': None
        }

        # stores pokemon image data when viewing party
        self.party = {
            'Pokemon1' : [],
            'Pokemon2' : [],
            'Pokemon3' : [],
            'Pokemon4' : [],
            'Pokemon5' : [],
            'Pokemon6' : []
        }
        
    def clear_keys(self):
        '''
        subroutine to empty the party attribute of the application
        :param self: instance of application
        :returns: None
        '''
        #for each dictionary key in the attribute
        for key in self.party:
            #set the key value to an empty list
            self.party[key] = []
           
    def clear_window(self):
        '''
        subroutine for clearing all widgets currently shown
        :param self: instance of application
        :returns: None
        '''
        # for each widget shown currently on the application
        for widgets in self.winfo_children():
            # destroy the widget
            widgets.destroy()
            
    def replace_pokemon(self, pokemon, slot):
        '''
        subroutine for replacing a party member
        :param self: instance of application
        :param pokemon: the pokemon to add to the party
        :param slot: the party slot to replace
        '''
        # locate the selected slot of the current user and set it equal to the pokemon to add
        self.user_data.loc[self.current_user['id'], 'Pokemon'+str(slot)] = pokemon

        # save the dataframe to the csv
        save_data(self.user_data)
        
    def single_search_pressed(self):
        '''
        subroutine for when a search for a single pokemon is started
        :param self: instance of application
        :returns: None
        '''
        # clear all grid slots where pokemon data is displayed to prevent overlap
        for widgets in self.winfo_children():
            if int(widgets.grid_info()["row"]) not in [2,3,4]:
                pass
            elif int(widgets.grid_info()['column']) not in [2,3,4]:
                pass
            else:    
                widgets.destroy()
        
        try:
            # get the search input and set it to lower case
            search_value = self.search_input.get().lower()
            
            # send a request to the pokeapi and store the response
            response = requests.get('https://pokeapi.co/api/v2/pokemon/'+search_value)
            
            # load the response
            data = json.loads(response.text)
            
            # create a request for the pokemons front facing default sprite and store the result
            image_req = requests.get(data['sprites']['front_default'], stream=True)
            
            # open a fresh image file
            with open('img.png','wb') as file:
                # write the image response content into the image file to copy the image
                file.write(image_req.content)
            
            # open the image in tkinter    
            self.poke_image = tk.PhotoImage(file='img.png')
            
            # delete the image file
            os.remove('img.png')
            
            # create a label to show the image
            image = ttk.Label(self, image=self.poke_image)
            
            # add the label to the grid
            image.grid(row=2,column=2)
            
            # create a label of the pokemons weight and add it to the grid
            self.weight = ttk.Label(self, text="Weight: "+str(data['weight']*100)+"g")
            self.weight.grid(row=2,column=4)
            
            # create a label of the pokemons height and add it to the grid
            self.height = ttk.Label(self, text="Height: "+str(data['height']*10)+"cm")
            self.height.grid(row=3,column=4)
            
            # create a label of the species name and id and add it to the grid
            ttk.Label(self, text=str(data['id'])+' - '+data['species']['name'].capitalize()).grid(row=3,column=2)
            
            # attempt to make a label of a pokemons two types, if it only has one, then make a label of its singular type
            try:
                ttk.Label(self, text=f"Types: {data['types'][0]['type']['name']}, {data['types'][1]['type']['name']}").grid(row=3,column=3)
            except:
                ttk.Label(self, text=f"Type: {data['types'][0]['type']['name']}").grid(row=3,column=3)
            
            # create a label of the pokemons ability
            ttk.Label(self, text=f"Ability: {data['abilities'][0]['ability']['name']}").grid(row=4,column=3)
            
            # create a label of the pokemons hidden ability
            ttk.Label(self, text=f"Hidden Ability: {data['abilities'][1]['ability']['name']}").grid(row=5,column=3)
            
            # store the name of the pokemon
            pokemon_name = data['species']['name']
            
            # request the species details of the current pokemon from the pokeapi and store the response
            response = requests.get('https://pokeapi.co/api/v2/pokemon-species/'+str(data['id']))
            
            # load the response
            data = json.loads(response.text)
            
            # create a button to for adding the pokemon to the party
            self.replace_button = ttk.Button(self, text='Add To Party', command=lambda:[self.clear_window(),self.change_party_page(pokemon_name)])
            
            # add this button to the grid
            self.replace_button.grid(row=4,column=2)
            
            # create a label for the english pokedex entry of the pokemon
            for counter in range(0,len(data['flavor_text_entries'])):
                if data['flavor_text_entries'][counter]['language']['name'] == 'en':
                    self.dex_entry = ttk.Label(self, text=data['flavor_text_entries'][counter]['flavor_text'].replace('',' '))
                    break
            
            # add this label to the grid
            self.dex_entry.grid(row=2,column=3)

        # ensures nothing will be shown if an error is thrown    
        except:
            pass
        
    def login_button_pressed(self):
        '''
        subroutine for when the "login" button is pressed
        :param self: instance of application
        :returns: None
        '''
        # get data from entry points
        username = self.username_entry.get()
        password = self.password_entry.get()

        # create a variable to represent if an empty slot is detected
        empty_slots = False

        # if an empty entry point slot is detected set empty_slots to true
        if len(username) == 0 or len(password) == 0:
            empty_slots = True

        # try to login the user
        status = login(self, username, password)

        # if the login failed or empty slots are detected
        if status == False or empty_slots == True:
            # clear the grid slot where the error message is to be displayed
            for widgets in self.winfo_children():
                if int(widgets.grid_info()["row"]) != 0:
                    pass
                elif int(widgets.grid_info()['column']) != 2:
                    pass
                else:    
                    widgets.destroy()

            # if empty slots are detected
            if empty_slots == True:
                # show an error message saying that there are empty entry slots and add it to the grid
                self.error = ttk.Label(self, text="Please make sure to fill in all of the required information.", foreground="red")
                self.error.grid(row=0,column=2)
                return

            # if the login failed
            if status == False:
                # show an error message saying the login failed and add it to the grid
                self.error = ttk.Label(self, text="Login failed, information is invalid.", foreground="red")
                self.error.grid(row=0,column=2)
                return

        # if the login was successful
        if status == True:
            # clear the window of its widgets
            self.clear_window()
            # show the now logged in user's party/party page
            self.party_page()

    def register_button_pressed(self):
        '''
        subroutine for when the "register" button is pressed
        :param self: instance of application
        :returns: None
        '''
        # get data from entry points
        username = self.username_entry.get()
        password = self.password_entry.get()
        password_confirm = self.password_entry_confirm.get()

        # create a variable for representing if there is an empty entry point
        empty_slots = False

        # if any entry point is empty set empty_slots to true
        if len(username) == 0 or len(password) == 0 or len(password_confirm) == 0:
            empty_slots = True

        # check if a user with the name submitted already exists
        exists = check_user_exists(self.user_data, username)

        # check if the password is valid
        valid_password = bool(self.password_regex.fullmatch(password))

        # if a user with the same name already exists, the password is invalid, passwords don't match or empty slots are detected
        if exists == True or valid_password == False or password != password_confirm or empty_slots == True:
            # clear the grid slot where an error will be displayed
            for widgets in self.winfo_children():
                if int(widgets.grid_info()["row"]) != 0:
                    pass
                elif int(widgets.grid_info()['column']) != 2:
                    pass
                else:    
                    widgets.destroy()

            # if empty slots are detected
            if empty_slots == True:
                # show an error message saying that empty slots have been detected and add it to the grid
                self.error = ttk.Label(self, text="Please make sure to fill in all of the required information.", foreground="red")
                self.error.grid(row=0,column=2)
                return

            # if a user with the same name already exists
            if exists == True:
                # show an error message saying that a user with the same name was found and add it to the grid
                self.error = ttk.Label(self, text="A user with this information already exists on the system, try logging in.", foreground="red")
                self.error.grid(row=0,column=2)
                return

            # if the passwords do not match
            if password != password_confirm:
                # show an error message saying that the passwords do not match and add it to the grid
                self.error = ttk.Label(self, text="Passwords do not match, please try again.", foreground="red")
                self.error.grid(row=0,column=2)
                return

            # if the password does not meet the needed criteria
            if valid_password == False:
                # show an error message saying that the password does not meet the needed criteria and add it to the grid
                self.error = ttk.Label(self, \
                text="For security reasons, passwords require at least 8 characters, including a number and a special character. No commas may be used.", foreground="red")
                self.error.grid(row=0,column=2)
                return

        # add the user to the dataframe
        self.user_data = add_user(self.user_data, username, password)
        # save the dataframe contents to the csv
        save_data(self.user_data)
        # login the new user
        login(self, username, password)
        # clear the windows widgets
        self.clear_window()
        # load the users party/party page
        self.party_page()

    def clear_error(self):
        '''
        subroutine to clear the error message location on the grid
        :param self: instance of application
        :returns: None
        '''
        for widget in self.winfo_children():
            if int(widget.grid_info()["row"]) != 0:
                pass
            elif int(widget.grid_info()["column"]) != 3:
                pass
            else:
                widget.destroy()

    def change_username_button_pressed(self):
        '''
        subroutine for when the "change username" button is pressed
        :param self: instance of application
        :returns: None
        '''
        # get data from entry points
        username = self.new_username_entry.get()
        password = self.password_entry.get()

        # check if the new username is the same as someone who already exists on the system
        exists = check_user_exists(self.user_data, username)

        # get the length of the new username
        length = len(username)

        # if another user with the same name already exists, or the username is empty, or the password is invalid
        if exists == True or length < 1 or self.user_data.loc[self.current_user['id'], 'password'] != password:
            # clear the grid slot where the error message will be shown
            self.clear_error()

            # if a user with the same name already exists
            if exists == True:
                # show an error message saying that someone with that name already exists and add it to the grid
                self.error = ttk.Label(self, text="A user already exists with that name, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the username isnt long enough/empty
            if length < 1:
                # show an error message saying that the username is too short and add it to the grid
                self.error = ttk.Label(self, text="Username is too short, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the given password does not match the current user
            if password != self.user_data.loc[self.current_user['id'], 'password']:
                # show an error message saying that the password is incorrect and add it to the grid
                self.error = ttk.Label(self, text="Password is incorrect, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return
        else:
            # rename the user
            rename_user(self, username)
            # create a message to inform the user that the name change was successful
            self.result = ttk.Label(self, text="Successfully changed your username!", foreground="green")
            # add this result message to the application grid
            self.result.grid(row=0,column=3)
            # save the data to the csv
            save_data(self.user_data)
            return

    def change_password_button_pressed(self):
        '''
        subroutine for when the "change password" button is pressed
        :param self: instance of application
        :returns: None
        '''
        # get data from entry points
        current_password = self.password_entry.get()
        new_password_confirm = self.password_entry_confirm.get()
        new_password = self.new_password_entry.get()

        # check whether password meets the needed criteria
        valid_password = bool(self.password_regex.fullmatch(new_password))

        # create a variable for whether the passwords match
        match = False
        if new_password == new_password_confirm:
            match = True

        # if the passwords dont match, the password doesnt meet criteria or if the current password is not of the current user
        if match == False or valid_password == False or self.user_data.loc[self.current_user['id'], "password"] != current_password:
            # clear the grid slot of the error message location
            self.clear_error()

            # if the passwords do not match
            if match == False:
                # show an error message saying that the passwords do not match and add it to the application grid
                self.error = ttk.Label(self, text="New passwords do not match, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the password does not meet the criteria
            if valid_password == False:
                # show an error message saying that the password does not meet the criteria and add it to the application grid
                self.error = ttk.Label(self, text="For security reasons, passwords require at least 8 characters, including a number and a special character. No commas may be used.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the current password is incorrect
            if self.user_data.loc[self.current_user['id'], "password"] != current_password:
                # show an error message saying that the password is incorrect and add it to the application grid
                self.error = ttk.Label(self, text="Current password is incorrect, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return
        else:
            # change the password
            change_password(self, new_password)
            # create a message to say the change was successful
            self.result = ttk.Label(self, text="Successfully changed your password!", foreground="green")
            # add this message to the application grid
            self.result.grid(row=0,column=3)
            # save the dataframe data to the csv
            save_data(self.user_data)

    def delete_account_button_pressed(self):
        '''
        subroutine for when the "delete account" button is pressed
        :param self: instance of application
        :returns: None
        '''
        # get needed data from the entry points
        username = self.username_entry.get()
        password = self.password_entry.get()
        password_confirm = self.password_entry_confirm.get()

        # create variables needed to validate whether account can be deleted or not
        match, correct_user, empty = False, False, False

        # if the password and password confirmation match set match to true
        if password == password_confirm:
            match = True

        # if the username matches the signed in user set correct_user as true
        if username == self.current_user['name']:
            correct_user = True

        # if any entry points were empty set empty as true
        if len(username) < 1 or len(password) < 1 or len(password_confirm) < 1:
            empty = True

        # if password does not match, an incorrect username is given, or the password is invalid
        if match == False or correct_user == False or empty == True or self.user_data.loc[self.current_user['id'], "password"] != password:
            # clear the grid slot where an error is to be placed
            self.clear_error()

            # if empty entry points is the error
            if empty == True:
                # show an error message stating that an entry point is empty and add it to the application grid
                self.error = ttk.Label(self, text="One box has been left empty, please fill out all the required information and try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the correct user not being given is the error
            if correct_user == False:
                # show an error message stating that the given username is incorrect and add it to the application grid
                self.error = ttk.Label(self, text="The username given is not for the current user, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the password and password confirmation entry points do not match
            if match == False:
                # show an error message stating that the passwords do not match and add it to the application grid
                self.error = ttk.Label(self, text="The passwords do not match, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return

            # if the password is incorrect
            if self.user_data.loc[self.current_user['id'], "password"] != password:
                # show an error message stating that the password is incorrect and add it to the application grid
                self.error = ttk.Label(self, text="This password is incorrect, please try again.", foreground="red")
                self.error.grid(row=0,column=3)
                return
        # delete the user
        delete_user(self, username)
        # save the dataframe to the csv file
        save_data(self.user_data)
        # clear the current page
        self.clear_window()
        # go back to the starting page
        self.start_page()

    def show_hide_password_pressed(self):
        '''
        subroutine to show or hide the password on password entry points
        :param self: instance of application
        :returns: None
        '''
        # if passwords are not hidden
        if self.password_hidden == False:
            # change the text on the show/hide password button to "show password"
            self.show_hide_button.configure(text="Show Password")

            # hide the password on the main password entry
            self.password_entry.configure(show='*')

            # attempt to hide the password on the confirmation entry if it exists currently
            try: 
                self.password_entry_confirm.configure(show='*')
            except:
                pass
            
            # attempt to hide the password on the new password entry point if it exists currently
            try:
                self.new_password_entry.configure(show="*")
            except:
                pass
            
            # set the password_hidden application attribute to True to show passwords are hidden
            self.password_hidden = True

            return

        # if passwords are already hidden
        if self.password_hidden == True:
            # change the show/hide button text to "hide password"
            self.show_hide_button.configure(text='Hide Password')

            # show the password in the main password entry
            self.password_entry.configure(show="")

            # attempt to show the password in the password confirmation entry point if it exists currently
            try:
                self.password_entry_confirm.configure(show='')
            except:
                pass
            
            # attempt to show the password in the new password entry point if it exists currently
            try:
                self.new_password_entry.configure(show='')
            except:
                pass
            
            # set the password_hidden attribute to False to show passwords are not hidden
            self.password_hidden = False

            return

    def side_bar(self):
        '''
        subroutine to generate the sidebar
        :param self: instance of application
        :returns: None
        '''
        # create a label displaying the users name
        tk.Label(self, font=('Kozuka Mincho Pro L',20), text=f"Welcome {self.current_user['name']}!").grid(row=0,column=0)

        # create a button to run the search pokemon page and add it to the grid
        self.search_button = ttk.Button(self, text='Search Pokemon', width=30,command=lambda:[self.clear_window(),self.search_page()])
        self.search_button.grid(row=1,column=0)

        # create a button to run the view party page and add it to the grid
        self.view_button = ttk.Button(self, text='View Party', width=30,command=lambda:[self.clear_window(),self.party_page()])
        self.view_button.grid(row=2,column=0)

        # add a button to run the account settings page and add it to the grid
        self.account_button = ttk.Button(self, text='Account Settings', width=30, command=lambda:[self.clear_window(),self.account_settings_page()])
        self.account_button.grid(row=3,column=0)

        # add a button for logging out and add it to the grid
        self.logout_button = ttk.Button(self, text='Log Out', width=30, command=lambda:[logout(self),self.clear_window(),self.start_page()])
        self.logout_button.grid(row=4,column=0)

    def account_settings_change(self, mode):
        '''
        subroutine to generate a page for the account settings
        mode selected
        :param self: instance of application
        :param mode: the selected account setting
        :returns: None
        '''
        # generate the side bar
        self.side_bar()

        # set the applications password_hidden attribute to true in order to not show passwords
        self.password_hidden = True

        # find the mode used
        match mode:
            # if change username mode selected
            case "username":
                # create an empty label to create space
                ttk.Label(self, width=15).grid(column=1)

                # create labels for each entry point
                ttk.Label(self, text="Change Username:").grid(row=0,column=2)
                ttk.Label(self, text="New Username:").grid(row=2, column=2)
                ttk.Label(self, text="Password:").grid(row=3,column=2)

                # create entry points for the new username and password
                self.new_username_entry = ttk.Entry(self)
                self.password_entry = ttk.Entry(self, show="*")

                # add these entry points to the application grid
                self.new_username_entry.grid(row=2,column=3)
                self.password_entry.grid(row=3,column=3)

                # create a button to confirm the username change
                self.change_username_button = ttk.Button(self, text="Change Username", width=30)

                # add this button to the application grid
                self.change_username_button.grid(row=4,column=3)

                # set the command of this button to the application subroutine change_username_button_pressed
                self.change_username_button['command'] = self.change_username_button_pressed

                # create a show/hide password button
                self.show_hide_button = ttk.Button(self, text="Show Password", width=30)

                # add this button to the application grid
                self.show_hide_button.grid(row=5,column=3)

                # set the command of this button to the application subroutine show_hide_password_pressed
                self.show_hide_button['command'] = self.show_hide_password_pressed

                # create a button to go back to the account settings page
                self.go_back = ttk.Button(self, text="Go Back", width=30, command=lambda:[self.clear_window(), self.account_settings_page()])

                # add this button to the grid
                self.go_back.grid(row=6,column=3)

            # if change password mode selected
            case "password":
                # create an empty label to create space
                ttk.Label(self, width=15).grid(column=1)

                # create a label for the page title
                ttk.Label(self, text="Change Password:").grid(row=0,column=2)
                ttk.Label(self, text="New Password:").grid(row=2, column=2)
                ttk.Label(self, text="Confirm New Password:").grid(row=3,column=2)
                ttk.Label(self, text="Current password:").grid(row=4,column=2)

                # create labels for the entry points to be created
                self.new_password_entry = ttk.Entry(self, show="*")
                self.password_entry_confirm = ttk.Entry(self, show="*")
                self.password_entry = ttk.Entry(self, show="*")

                # create the entry points for the new password, confirming the new password and the current password
                self.new_password_entry.grid(row=2,column=3)
                self.password_entry_confirm.grid(row=3,column=3)
                self.password_entry.grid(row=4,column=3)

                # create a button to confirm the password change
                self.change_password_button = ttk.Button(self, text="Change Password", width=30)

                # add this button to the grid
                self.change_password_button.grid(row=6,column=3)

                # set the command of this button to be the application subroutine change_password_button_pressed
                self.change_password_button['command'] = self.change_password_button_pressed

                # create a show/hide password button
                self.show_hide_button = ttk.Button(self, text="Show Password", width=30)

                # add this button to the application grid
                self.show_hide_button.grid(row=5,column=3)

                # set the command of this button to be the application subroutine show_hide_password_pressed
                self.show_hide_button['command'] = self.show_hide_password_pressed

                # create a button to go back to the account settings page
                self.go_back = ttk.Button(self, text="Go Back", width=30, command=lambda:[self.clear_window(), self.account_settings_page()])

                # add this button to the grid
                self.go_back.grid(row=7,column=3)

            # if delete account mode is selected
            case "delete":
                # create an empty label to create space
                ttk.Label(self,width=15).grid(column=1)

                # create a label to display the page title
                ttk.Label(self, text="Account Deletion:").grid(row=0,column=2)
                ttk.Label(self, text="Username:").grid(row=2,column=2)
                ttk.Label(self, text="Password:").grid(row=3,column=2)
                ttk.Label(self, text="Confirm Password:").grid(row=4,column=2)

                # create labels for the entry points to be created
                self.username_entry = ttk.Entry(self)
                self.password_entry = ttk.Entry(self, show="*")
                self.password_entry_confirm = ttk.Entry(self, show="*")

                # create the entry points for the username, password and password confirmation
                self.username_entry.grid(row=2,column=3)
                self.password_entry.grid(row=3,column=3)
                self.password_entry_confirm.grid(row=4,column=3)

                # create a button to confirm account deletion
                self.delete_account_button = ttk.Button(self, text="Delete Account", width=30)

                # set the command of the button to the application subroutine delete_account_button_pressed
                self.delete_account_button['command'] = self.delete_account_button_pressed

                # add this button to the grid
                self.delete_account_button.grid(row=6,column=3)

                # create a show/hide password button
                self.show_hide_button = ttk.Button(self, text="Show Password", width=30)

                # set the command of the button to be the application subroutine show_hide_password_pressed
                self.show_hide_button['command'] = self.show_hide_password_pressed

                # add this button to the grid
                self.show_hide_button.grid(row=5,column=3)

                # create a button to go back to the account settings page
                self.go_back = ttk.Button(self, text="Go Back", width=30, command=lambda:[self.clear_window(), self.account_settings_page()])

                # add this button to the grid
                self.go_back.grid(row=7,column=3)

    def account_settings_page(self):
        '''
        subroutine to generate the account settings page
        :param self: instance of application
        :returns: None
        '''
        # generate the side bar
        self.side_bar()

        # create an empty label to create space
        tk.Label(self, width=15).grid(column=1)

        # add a label with the page title
        tk.Label(self, text='Account Settings:').grid(row=0,column=2)

        # create buttons for each account option
        self.change_name_button = ttk.Button(self, text='Change Username', width=30, command=lambda:[self.clear_window(), self.account_settings_change("username")])
        self.change_pass_button = ttk.Button(self, text='Change Password', width=30, command=lambda:[self.clear_window(), self.account_settings_change("password")])
        self.delete_account_button = ttk.Button(self, text='Delete Account', width=30, command=lambda:[self.clear_window(), self.account_settings_change("delete")])

        # create an iteration counter
        i = 0

        # for each button created
        for item in [self.change_name_button, self.change_pass_button, self.delete_account_button]:
            # add them to the grid using the counter to change locations
            item.grid(row=1,column=2+i)
            # increment the counter by 1
            i+=1

    def change_party_page(self, pokemon):
        '''
        subroutine to generate the change party member page
        :param self: instance of application
        :returns: None
        '''
        # generate the images for party members
        self.party_page()

        # create buttons below each party member for replacing them and add these buttons to the grid
        button_1 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,1),self.clear_window(),self.party_page()])
        button_1.grid(row=4,column=2)
        button_2 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,2),self.clear_window(),self.party_page()])
        button_2.grid(row=4,column=3)
        button_3 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,3),self.clear_window(),self.party_page()])
        button_3.grid(row=4,column=4)
        button_4 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,4),self.clear_window(),self.party_page()])
        button_4.grid(row=4,column=5)
        button_5 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,5),self.clear_window(),self.party_page()])
        button_5.grid(row=4,column=6)
        button_6 = ttk.Button(self, text='replace', command=lambda:[self.replace_pokemon(pokemon,6),self.clear_window(),self.party_page()])
        button_6.grid(row=4,column=7)

    def search_page(self):
        '''
        subroutine to generate the search page
        :param self: instance of application
        :returns: None
        '''
        # generate the side bar
        self.side_bar()

        # add an empty label to create space
        tk.Label(self, width=15).grid(column=1)

        # create a label displaying the current page title
        tk.Label(self, text='Search:').grid(row=0,column=2)

        # add an entry point for search input
        self.search_input = ttk.Entry(self)

        # add this to the application grid
        self.search_input.grid(row=0,column=3)

        # add button to submit search
        self.searching_button = ttk.Button(self, text='Search', width=30)

        # set command of searching button to the applications single_search_pressed subroutine
        self.searching_button['command'] = self.single_search_pressed

        # add the button to the application grid
        self.searching_button.grid(row=0,column=4)

    def party_page(self):
        '''
        Subroutine to generate the party page, which is also
        the starting page upon signing in
        :param self: instance of application
        :returns: None
        '''
        # clear all party slots by running the applications clear_keys subroutine
        self.clear_keys()

        # generate the side bar with the applications side_bar subroutine
        self.side_bar()

        # generate an empty label to create an empty space
        tk.Label(self, width=15).grid(column=1)

        # add a title label
        tk.Label(self, text='Your party:').grid(row=0,column=2)

        # for each pokemon slot
        for counter in range(1,7):
            # if the dataframe has no pokemon in the current slot iteration for the current user
            if self.user_data.loc[self.current_user['id'], 'Pokemon'+str(counter)] == 'None':
                # create a label saying "None" to mark an empty pokemon slot
                tk.Label(self, text='None').grid(row=2,column=1+counter)
                # restart the loop
                continue
            
            # send a request to pokeapi for the pokemon in the current slot 
            response = requests.get('https://pokeapi.co/api/v2/pokemon/'+(self.user_data.loc[self.current_user['id'], 'Pokemon'+str(counter)]))
            # load the response
            data = json.loads(response.text)
            # request the pokemons default front sprite
            image_req = requests.get(data['sprites']['front_default'], stream=True)

            # open an empty image file
            with open('img.png','wb') as file:
                # write the requests content to the image to copy it
                file.write(image_req.content)

            # load and add the image to the applications party attribute
            self.party['Pokemon'+str(counter)].append(tk.PhotoImage(file='img.png'))

            # delete the image file
            os.remove('img.png')

            # add the label to display the image to the party attribute
            self.party['Pokemon'+str(counter)].append(tk.Label(self, image=self.party['Pokemon'+str(counter)][0]))

            # display the label created, showing the image
            self.party['Pokemon'+str(counter)][1].grid(row=2,column=1+counter)

            # display the pokemons name and ID
            tk.Label(self, text=str(data['id'])+" - "+data['species']['name'].capitalize()).grid(row=3,column=1+counter)

    def register_page(self):
        '''
        Subroutine to generate the register page
        :param self: instance of application
        :returns: None
        '''
        # set the application to not show passwords
        self.password_hidden = True

        # create labels for username, password, and password confirmation entry points
        tk.Label(self, text='username:').grid(row=0)
        tk.Label(self, text='password:').grid(row=1)
        tk.Label(self, text='confirm password:').grid(row=2)

        # create entry points for username, password, and password confirmation
        self.username_entry = ttk.Entry(self)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry_confirm = ttk.Entry(self, show="*")

        # add them all to the application grid
        self.username_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        self.password_entry_confirm.grid(row=2,column=1)

        # create the show/hide password button
        self.show_hide_button = ttk.Button(self, text="Show Password", width=30)

        # add this to the grid
        self.show_hide_button.grid(row=3,column=1)

        # set the command of the show/hide button to the applications show_hide_password_pressed subroutine
        self.show_hide_button['command'] = self.show_hide_password_pressed

        # create the register button
        self.register_button = ttk.Button(self, text='Register', width=30)

        # add this to the application grid
        self.register_button.grid(row=4,column=1)

        # set the command of the register button to the applications register_button_pressed subroutine
        self.register_button['command'] = self.register_button_pressed

        # create a button to return to the previous page
        self.return_button = ttk.Button(self, text='Go Back', width=30, command=lambda:[self.clear_window(),self.start_page()])

        # add this new button to the application grid
        self.return_button.grid(row=5,column=1)

    def login_page(self):
        '''
        Subroutine to generate the login page
        :param self: instance of application
        :returns: None
        '''
        # set the application to not show passwords
        self.password_hidden = True

        # create labels for username and password entry points
        tk.Label(self, text='username').grid(row=0)
        tk.Label(self, text='password').grid(row=1)

        # create entry points for username and password
        self.username_entry = ttk.Entry(self)
        self.password_entry = ttk.Entry(self, show="*")

        # add these to the applications grid
        self.username_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)

        # create the button to show/hide passwords
        self.show_hide_button = ttk.Button(self, text="Show Password", width=30, padding=10)

        # add this to the applications grid
        self.show_hide_button.grid(row=2,column=1)

        # set the command of the show/hide password button to the applications show_hide_password_pressed subroutine
        self.show_hide_button['command'] = self.show_hide_password_pressed

        # create the login button
        self.login_button = ttk.Button(self, text='Log in', width=30, padding=10)

        # add this to the application grid
        self.login_button.grid(row=3,column=1)

        # set the command of the login button to the applications login_button_pressed subroutine
        self.login_button['command'] = self.login_button_pressed

        # create a button to return to the previous page
        self.return_button = ttk.Button(self, text='Go Back', width=30, padding=10, command=lambda:[self.clear_window(),self.start_page()])

        # add this to the applications grid
        self.return_button.grid(row=4,column=1)

    def start_page(self):
        '''
        Subroutine to generate the start page
        :param self: instance of application
        :returns: None
        '''
        # create a spacer label
        self.spacer = ttk.Label(self, padding=150)

        # create login button
        self.login_button = ttk.Button(self, text='Login', width=30, padding=20, command=lambda:[self.clear_window(),self.login_page()])

        # create register button
        self.register_button = ttk.Button(self, text='Register', width=30, padding=20, command=lambda:[self.clear_window(),self.register_page()])

        # create quit button
        self.quit_button = ttk.Button(self, text='Quit', width=30, padding=20, command=exit)

        # pack each button created
        for item in [self.spacer, self.login_button, self.register_button, self.quit_button]:
            item.pack()

        # start the applications loop
        self.mainloop()


if __name__ == "__main__":
    # retrieve user data from csv file
    user_data = pd.read_csv('UserData.csv', index_col=False)

    # reset index of user data
    user_data.reset_index() 
    
    # fill all empty data with None
    user_data = user_data.fillna('None')
    
    # create an instance of the application with the retrieved user data
    application = MainApplication(dataframe=user_data)
    
    # start the application
    application.start_page()