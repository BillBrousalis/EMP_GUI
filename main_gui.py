#--------------------------------------------IMPORTS--------------------------------------------
import serial
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import tkinter.messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from PIL import Image, ImageTk
import time
import threading
import functools
import webbrowser



#--------------------------------------------MODULES--------------------------------------------
import serial_comms
import orientation_graphics_3d as mygraphics


#--------------------------------------------CREATING THE APPLICATION CLASS--------------------------------------------
class Application(tk.Tk):
    #--------------------------------------------GENERIC VARIABLES - PATHS - WINDOW SIZE / COLORS--------------------------------------------
    
    HEIGHT = 500
    WIDTH = 480

    colors = {
        "white": '#f2f2f2',
        "light grey": '#e8e8e8',
        "blue": '#82b5c4',
        "black": '#212121',
        "highlight": '#e3f7ff'
    }
    # **************
    font = 'Helvetica '

    graph_color_list = ['r','b', 'g', 'm', 'k']

    #---------------------DEFAULT / MIN / MAX VALUES OF ADJUSTABLE VARIABLES---------------------
    # what the fuck is this for 
    default_servo_speed = 50

    #--------------------------------------------INITIALIZING CLASS--------------------------------------------
    def __init__(self):
        super().__init__()
        self.title("NAVI-TUNING")
        # add icon to the top left of the window
        self.iconbitmap(default='files\\pictures-icon\\boat_icon.ico')

        self.min_max_defaults_list = []

        self.myserial = serial_comms.ser
        self.myserial.refresh_ports()
        self.setup3D_complete = False
        self.reading_thread = False
        self.create_GUI()
        self.default_servo_speed = self.myserial.return_default_servo_speed()
        self.servo_speed_scale.set(self.default_servo_speed)
 






    #--------------------------------------------CREATING GUI FRAME / TABS AND THREAD TO KEEP REFRESHING IT--------------------------------------------
    def create_GUI(self):
        self.mainFrame = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT)
        self.mainFrame.pack()
        self.create_serial_gui()

        self.tab_parent = ttk.Notebook(self.mainFrame)

        self.tabs_to_be_updated = [1,2]

        self.create_tuning_tab()
        self.create_monitor_tab()                       
        self.create_graph_tab()
        self.create_settings_tab()
        self.create_about_tab()

        self.tab_parent.bind("<<NotebookTabChanged>>", self.on_tab_switch)
        self.previous_tab = ''
        self.tab_parent.place(anchor='n', relx=0.5, rely=0.07, relwidth=1, relheight=0.93)

        updateGUI_thread = threading.Thread(target=self.update_gui)
        updateGUI_thread.daemon = True
        updateGUI_thread.start()






        
    #--------------------------------------------TOP OF THE FRAME / WIDGETS TO HANDLE SERIAL CONNECTIONS--------------------------------------------
    def create_serial_gui(self):
        self.serial_canvas = tk.Canvas(self.mainFrame, width=self.WIDTH, height=self.HEIGHT/6, bg=self.colors["light grey"], relief='groove')
        self.serial_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=0.08)

        Helvetica_10_bold = tkFont.Font(family='Helvetica', size=10, weight='bold')

        self.port_label = tk.Label(self.serial_canvas, text='Com port:', font=Helvetica_10_bold, bg = self.colors["light grey"])
        self.port_label.place(anchor='n', relx=0.1, rely=0.15, relwidth=0.15, relheight=0.7)

        self.com_port_var = tk.StringVar(self.serial_canvas)
        self.com_port_var.set(self.myserial.default_com)

        self.com_port_menu = tk.OptionMenu(self.serial_canvas, self.com_port_var, *self.myserial.available_ports_list)
        self.com_port_menu.config(font=Helvetica_10_bold, bg=self.colors["light grey"], relief='groove')
        self.com_port_menu.place(anchor='n', relx=0.25, rely=0.155, relwidth=0.17, relheight=0.7)

        self.refresh_com_ports_button = tk.Button(self.serial_canvas, text='Refresh', bg=self.colors["light grey"], relief='groove',
            command=functools.partial(self.update_port_OptionMenu))
        self.refresh_com_ports_button.bind('<Enter>', lambda event, x=self.refresh_com_ports_button : self.on_hover(x))
        self.refresh_com_ports_button.bind('<Leave>', lambda event, x=self.refresh_com_ports_button : self.on_hover_leave(x))
        self.refresh_com_ports_button.place(anchor='n', relx=0.385, rely=0.205, relwidth=0.1, relheight=0.6)

        self.baud_rate_var = tk.StringVar(self.serial_canvas) 
        self.baud_rate_var.set(str(self.myserial.default_baud))

        self.baud_label = tk.Label(self.serial_canvas, text='Baud Rate:', font=Helvetica_10_bold, bg=self.colors["light grey"])
        self.baud_label.place(anchor='n', relx=0.52, rely=0.15, relwidth=0.15, relheight=0.7)

        self.baud_menu = tk.OptionMenu(self.serial_canvas, self.baud_rate_var, *self.myserial.baud_rate_list)
        self.baud_menu.config(font=Helvetica_10_bold, bg=self.colors["light grey"], relief='groove')
        self.baud_menu.place(anchor='n', relx=0.68, rely=0.15, relwidth=0.17, relheight=0.7)

        self.connect_button = tk.Button(self.serial_canvas, text='Connect', font=Helvetica_10_bold, relief='groove',
            bg=self.colors["black"], activebackground=self.colors["light grey"], fg='white', command=functools.partial(self.connect_button_func))
        self.connect_button.place(anchor='n', relx=0.875, rely=0.15, relwidth=0.17, relheight=0.7)


    #--------------------------------------------HANDLE SERIAL_GUI'S CONNECT BUTTON--------------------------------------------
    def connect_button_func(self):
        if self.connect_button['text'] == "Connect":
            self.connect_button['text'] = "Close"
            self.myserial.connect_func()
            time.sleep(0.01)
            if self.myserial.connect_state == "Connected":
                self.abs_rel_states_list = self.myserial.abs_rel_toggle_states
                self.rel_zero_values_list = self.myserial.rel_zero_values_list
                self.update_rel_abs_button_text()
                # SHOW VERSION ON SETTINGS TAB
                self.firmware_version_label['text'] = f'version : {self.myserial.get_firmware_version()}'
                # get first tab's values
                self.update_vane_values()
                if self.current_tab in self.tabs_to_be_updated:
                    self.myserial.send_data("vmon 8 100\n")

                elif self.current_tab == 3:
                    self.myserial.quat = True
                    self.myserial.send_data("vmon 7 100\n")
            else:
                self.connect_button['text'] = "Connect"
                tkinter.messagebox.showinfo("Error", message="Error connecting to serial port")

            if self.myserial.connect_state == "Connected":
                self.read_serial_thread()
            
            if self.current_tab == 3:
                self.setup3D()

        else:
            if self.start_graph_button['text'] == "Stop Graph":
                self.start_graph_button_func()
            self.connect_button['text'] = "Connect"
            self.myserial.send_data("vmon 0 0\n")
            time.sleep(0.01)
            self.myserial.connect_func()
            




    # handling the refresh button for the available ports
    def update_port_OptionMenu(self):     
        self.myserial.refresh_ports()
        menu = self.com_port_menu.children['menu']
        menu.delete(0, 'end')
        for port in self.myserial.available_ports_list:
            menu.add_command(label=port, command=lambda p=port: self.com_port_var.set(p))








    #--------------------------------------------CREATING THE 'VANE / SERVO' TAB - ADDING WIDGETS--------------------------------------------
    def create_tuning_tab(self):
        self.tuning_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.tuning_tab, text='Tuning')
        self.tuning_canvas = tk.Canvas(self.tuning_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        self.tuning_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)


        self.vane_values = dict()

        self.vane_entry_widgets_list = []

        self.tuning_values = [{"text": "Offset :", "min": -20, "max": 20, "default": 0, "id": "voffs", "type": float},
                              {"text": "Gain(Deg/Deg) :", "min": -5000, "max": 5000, "default": 0.00, "id": "vgain", "type": float},
                              {"text": "Vane Scale(Deg/V) :", "min": -5000, "max": 5000, "default": 0.00, "id": "vscale", "type": float},
                              {"text": "Delay(ms) :", "min": 0, "max": 2000, "default": 0, "id": "vdelay", "type": int},
                              {"text": "Velocity :", "min": 0, "max": 5000000, "default": 0, "id": "vvel", "type": int},
                              {"text": "Acceleration :", "min": 0, "max": 5000000, "default": 0, "id": "vacc", "type": int}, 
                              {"text": "Kp :", "min": 0, "max": 32767, "default": 0, "id": "kp", "type": int},
                              {"text": "Ki :", "min": 0, "max": 32767, "default": 0, "id": "ki", "type": int},
                              {"text": "Kd :", "min": 0, "max": 32767, "default": 0, "id": "kd", "type": int},
                              {"text": "Kv :", "min": 0, "max": 32767, "default": 0, "id": "kv", "type": int},
                              {"text": "Power Limit(%) :", "min": 0, "max": 100, "default": 0, "id": "power", "type": int}]


        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        #using a for loop to avoid massive block of repeating code
        
        #for i, (text, minimum, maximum, defaultval) in enumerate(zip(self.vane_text_list, self.min_values_list, self.max_values_list, self.default_values_list)):
        for i, config in enumerate(self.tuning_values): 
            y = (0.03+i*0.08)
            self.mylabel = tk.Label(self.tuning_canvas, text=config["text"], font=Helvetica_11_bold, bg = self.colors["white"], anchor='e')
            self.mylabel.place(anchor='n', relx=0.17, rely=y, relwidth=0.3, relheight=0.065)  

            self.myentry = tk.Entry(self.tuning_canvas, font=Helvetica_11_bold, bg=self.colors["light grey"], justify='center', relief='groove')
            self.myentry.insert(0, config["default"])
            self.myentry.bind('<Return>', lambda event, x=self.myentry: self.on_enter_press(x))
            self.myentry.bind('<Enter>', lambda event, x=self.myentry : self.on_hover(x))
            self.myentry.bind('<Leave>', lambda event, x=self.myentry : self.on_hover_leave(x))
            self.myentry.place(anchor='n', relx=0.54, rely=y+0.005, relwidth=0.42, relheight=0.055)

            #append entry widget to a list of the vane/servo 's tab entry widgets ------ access individual widget by using self.vane_entry_widgets_list[i]
            # ***** jesus christ no *****
            self.vane_entry_widgets_list.append(self.myentry)

            self.mydownbutton = tk.Button(self.tuning_canvas, text='-', font='Helvetica 14 bold', bg=self.colors["light grey"],
                relief='groove', command=functools.partial(self.adjust_value, 'down', self.myentry, config["min"], config["max"]))
            self.mydownbutton.bind('<Enter>', lambda event, x=self.mydownbutton : self.on_hover(x))
            self.mydownbutton.bind('<Leave>', lambda event, x=self.mydownbutton : self.on_hover_leave(x))    
            self.mydownbutton.place(anchor='n', relx=0.82, rely=y+0.005, relwidth=0.095, relheight=0.05)

            self.myupbutton = tk.Button(self.tuning_canvas, text='+', font='Helvetica 13 bold', bg=self.colors["light grey"],
                relief='groove', command=functools.partial(self.adjust_value, 'up', self.myentry, config["min"], config["max"]))
            self.myupbutton.bind('<Enter>', lambda event, x=self.myupbutton : self.on_hover(x))
            self.myupbutton.bind('<Leave>', lambda event, x=self.myupbutton : self.on_hover_leave(x))
            self.myupbutton.place(anchor='n', relx=0.92, rely=y+0.005, relwidth=0.095, relheight=0.05)



        # SAVE - RESET DEFAULT VALUES BUTTONS
        self.save_button = tk.Button(self.tuning_canvas, text='Save', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=functools.partial(self.save_values))
        self.save_button.bind('<Enter>', lambda event, x=self.save_button : self.on_hover(x))
        self.save_button.bind('<Leave>', lambda event, x=self.save_button : self.on_hover_leave(x))
        self.save_button.place(anchor='n', relx=0.844, rely=0.92, relwidth=0.25, relheight=0.06)

        # list of entries that require their value to remain an integer - store here for later use
        self.int_entries = [self.vane_entry_widgets_list[i] for i in range(3,len(self.vane_entry_widgets_list))]
        




    #--------------------------------------------SEND VALUE (ON ENTER PRESS) OF THE ENTRY WIDGET IN FOCUS--------------------------------------------
    def on_enter_press(self, parent):
        #check if text is numeric:
        if parent.get().replace('.', '').replace(' ', '').replace('-', '').isdigit():
            #check if text is within bounds:
            check = self.check_value_bounds()
            if check: 
                identifier = self.vane_entry_widgets_list.index(parent)
                identifier = self.vane_id_list[identifier]
                if parent in self.int_entries:
                    try:
                        #check if given value is an integer
                        int(parent.get())
        # show error message if value is not : integer / in bounds / numeric
                    except:
                        tk.messagebox.showinfo(title="Error", message="Value is not an integer.")
                        return 0
                self.myserial.send_data(f'{identifier}{parent.get()}\n')
                time.sleep(0.05)
                self.update_vane_values()
            else:
                tk.messagebox.showinfo(title="Error", message="Values are out of bounds.")    
        else:
            tk.messagebox.showinfo(title="Error", message="Values are not numeric.")



    # update 'vane/servo' tab's values after using the 'dump1' command
    def update_vane_values(self):
        try:
            self.vane_values = self.myserial.receive_dump()
            for key, entry in zip(self.vane_values, self.vane_entry_widgets_list):
                val = self.vane_values[key]
                val = str(val)
                if " " in val: val = val.replace(" ", "")
                entry.delete(0, 'end')
                entry.insert(0, val)
        except Exception as e:
            print(f'error in update_vane_values : {e}')        







    # function handling the adjustment button of the 'vane/servo' tab
    def adjust_value(self, direction, entry, min, max):
        # validate that input is a number
        try:
            assert entry.get().replace('.', '').replace('-', '').isdigit()
        except:
            tkinter.messagebox.showinfo(title="Error", message="Input is not a number.")
            raise Exception("Boo! Not a number...")

        # for floating point entries
        if entry not in self.int_entries:
            val = float(entry.get())
            if direction == 'up' and val<max:
                val += 0.01
            elif direction == 'down' and val>min:
                val -= 0.01
            if val > max:
                val = max
            elif val < min:
                val = min
            val = '{:.2f}'.format(val)

        # for integer-only entries
        else:
            # flooring the value
            val = int(float(entry.get()))         
            if direction == 'up' and val < max:
                val += 1
            elif direction == 'down' and val > min:
                val -= 1
            if val > max:
                val = max
            elif val < min:
                val = min
            val = str(val)

        if self.myserial.connect_state == "Connected":
            index = self.vane_entry_widgets_list.index(entry)
            identifier = self.vane_id_list[index]
            self.myserial.send_data(f'{identifier}{val.strip()}\n')
            time.sleep(0.01)
            self.update_vane_values()
        else:
            print("not connected")



    # handling the 'save' button function
    def save_values(self):
        if self.myserial.connect_state == "Connected":
            self.myserial.send_data("save\n")
        else:
            tkinter.messagebox.showinfo(title="Error", message="You are not connected to a serial port.")




    # determining if given values are inside their min/max bounds
    def check_value_bounds(self):
        for val, minim, maxim in zip(self.vane_entry_widgets_list, self.min_values_list, self.max_values_list):
            val = float(val.get())
            if val > maxim or val < minim:
                return False
        return True










    #--------------------------------------------CREATING THE 'MONITOR' TAB - ADDING WIDGETS--------------------------------------------
    def create_monitor_tab(self):
        self.monitor_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.monitor_tab, text='Monitor')
        self.monitor_canvas = tk.Canvas(self.monitor_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        self.monitor_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)


        self.monitor_text_list = ['Roll :', 'Pitch :', 'Yaw :', 'Vane :', 'Wing :']
        self.monitor_label_list = []
        self.monitor_value_label_list = []
        self.abs_rel_toggle_buttons_list = []
        self.zero_buttons_list = []

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        #--------------------------------------------AGAIN USING A FOR LOOP TO AVOID BIG BLOCK OF REPEATING CODE--------------------------------------------
        
        for i, text in enumerate(self.monitor_text_list):
            y = (0.05+i*0.11)
            defaultval = '0.00'
            self.monitor_label = tk.Label(self.monitor_canvas, text=text, font=Helvetica_11_bold, bg = self.colors["white"], anchor='e')
            self.monitor_label.place(anchor='n', relx=0.13, rely=y, relwidth=0.11, relheight=0.06)  
            self.monitor_label_list.append(self.monitor_label)

            self.monitor_value_label = tk.Label(self.monitor_canvas, text=defaultval, font=Helvetica_11_bold, bg=self.colors["light grey"], justify='center', relief='groove')
            self.monitor_value_label.place(anchor='n', relx=0.45, rely=y, relwidth=0.45, relheight=0.06)

            # like the vane/servo tab, store the monitor tab's label widgets in a list to access them individually with ease 
            self.monitor_value_label_list.append(self.monitor_value_label)

            self.abs_rel_toggle_button = tk.Button(self.monitor_canvas, text='Abs', font=Helvetica_11_bold, bg=self.colors["light grey"])
            self.abs_rel_toggle_button.configure(relief='groove', command=lambda x = self.abs_rel_toggle_button : self.abs_rel_toggle_button_func(x))
            self.abs_rel_toggle_button.bind('<Enter>', lambda event, x=self.abs_rel_toggle_button : self.on_hover(x))
            self.abs_rel_toggle_button.bind('<Leave>', lambda event, x=self.abs_rel_toggle_button : self.on_hover_leave(x))
            self.abs_rel_toggle_button.place(anchor='n', relx=0.76, rely=y, relwidth=0.1, relheight=0.06)
        
            self.zero_button = tk.Button(self.monitor_canvas, text='Zero', font=Helvetica_11_bold, bg=self.colors["light grey"])
            self.zero_button.configure(relief='groove', command=lambda x = self.zero_button: self.zero_button_func(x))
            self.zero_button.bind('<Enter>', lambda event, x=self.zero_button : self.on_hover(x))
            self.zero_button.bind('<Leave>', lambda event, x=self.zero_button : self.on_hover_leave(x))
            self.zero_button.place(anchor='n', relx=0.88, rely=y, relwidth=0.1, relheight=0.06)
            
            self.abs_rel_toggle_buttons_list.append(self.abs_rel_toggle_button)
            self.zero_buttons_list.append(self.zero_button)

            self.abs_rel_states_list = [val['text'] for val in self.abs_rel_toggle_buttons_list]
            self.rel_zero_values_list = [0 for i in range(len(self.monitor_value_label_list))]

        for i in range(len(self.monitor_text_list)):
            y = (0.135+i*0.11)
            self.valSeparator = ttk.Separator(self.monitor_canvas)
            self.valSeparator.place(anchor='n', relx=0.5, rely=y, relwidth=0.8)


        self.start_stop_state = 'start'
            
        self.start_stop_button = tk.Button(self.monitor_canvas, text='Start', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=lambda: self.start_stop_button_func())
        self.start_stop_button.bind('<Enter>', lambda event, x=self.start_stop_button : self.on_hover(x))
        self.start_stop_button.bind('<Leave>', lambda event, x=self.start_stop_button : self.on_hover_leave(x))
        self.start_stop_button.place(anchor='n', relx=0.48, rely=0.73, relwidth=0.17, relheight=0.07)
        

        self.home_button = tk.Button(self.monitor_canvas, text='Home', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=lambda: self.home_button_func())
        self.home_button.bind('<Enter>', lambda event, x=self.home_button : self.on_hover(x))
        self.home_button.bind('<Leave>', lambda event, x=self.home_button : self.on_hover_leave(x))
        self.home_button.place(anchor='n', relx=0.68, rely=0.73, relwidth=0.17, relheight=0.07)

        self.servo_reset_button = tk.Button(self.monitor_canvas, text='Reset', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=self.servo_reset_button_func)
        self.servo_reset_button.bind('<Enter>', lambda event, x=self.servo_reset_button : self.on_hover(x))
        self.servo_reset_button.bind('<Leave>', lambda event, x=self.servo_reset_button : self.on_hover_leave(x))
        self.servo_reset_button.place(anchor='n', relx=0.88, rely=0.73, relwidth=0.17, relheight=0.07)


        self.jog_plus_button = tk.Button(self.monitor_canvas, text='Jog +', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.jog_plus_button.bind("<ButtonPress>", lambda event, parent=self.jog_plus_button: self.button_press(parent))
        self.jog_plus_button.bind("<ButtonRelease>", lambda event, parent=self.jog_plus_button: self.button_release(parent))
        self.jog_plus_button.bind('<Enter>', lambda event, x=self.jog_plus_button : self.on_hover(x))
        self.jog_plus_button.bind('<Leave>', lambda event, x=self.jog_plus_button : self.on_hover_leave(x))
        self.jog_plus_button.place(anchor='n', relx=0.28, rely=0.68, relwidth=0.17, relheight=0.07)

        self.jog_minus_button = tk.Button(self.monitor_canvas, text='Jog -', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.jog_minus_button.bind("<ButtonPress>", lambda event, parent=self.jog_minus_button: self.button_press(parent))
        self.jog_minus_button.bind("<ButtonRelease>", lambda event, parent=self.jog_minus_button: self.button_release(parent))
        self.jog_minus_button.bind('<Enter>', lambda event, x=self.jog_minus_button : self.on_hover(x))
        self.jog_minus_button.bind('<Leave>', lambda event, x=self.jog_minus_button : self.on_hover_leave(x))
        self.jog_minus_button.place(anchor='n', relx=0.28, rely=0.78, relwidth=0.17, relheight=0.07)


        self.servo_speed_label = tk.Label(self.monitor_canvas, text='speed', font='Helvetica 10 bold', bg=self.colors["white"], relief='groove')
        self.servo_speed_label.place(anchor='n', relx=0.08, rely=0.63, relwidth=0.1, relheight=0.05)  

        self.servo_speed_scale = tk.Scale(self.monitor_canvas, from_=0, to=100, tickinterval=100, orient='vertical', bg=self.colors["light grey"], relief='groove')
        self.servo_speed_scale.set(self.default_servo_speed)
        self.servo_speed_scale.bind('<Enter>', lambda event, x=self.servo_speed_scale : self.on_hover(x))
        self.servo_speed_scale.bind('<Leave>', lambda event, x=self.servo_speed_scale : self.on_hover_leave(x))
        self.servo_speed_scale.place(anchor='n', relx=0.1, rely=0.675, relwidth=0.15, relheight=0.18)

        self.logging_toggle_button = tk.Button(self.monitor_canvas, text='Record', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.logging_toggle_button.configure(command=self.logging_toggle_button_func)
        self.logging_toggle_button.bind('<Enter>', lambda event, x=self.logging_toggle_button : self.on_hover(x))
        self.logging_toggle_button.bind('<Leave>', lambda event, x=self.logging_toggle_button : self.on_hover_leave(x))
        self.logging_toggle_button.place(anchor='n', relx=0.813, rely=0.85, relwidth=0.3, relheight=0.07)





    def button_press(self, parent):
        print("pressed")
        self.button_is_pressed = True
        if self.myserial.connect_state == "Connected":
            if parent == self.jog_plus_button:
                self.jog_plus_button_func()
            elif parent == self.jog_minus_button:
                self.jog_minus_button_func()
            


    def button_release(self, parent):
        print("released")
        self.button_is_pressed = False
        if self.myserial.connect_state == "Connected":
            if parent == self.jog_plus_button:
                self.jog_plus_button_func()
            elif parent == self.jog_minus_button:
                self.jog_minus_button_func()
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')


    def jog_plus_button_func(self):
        if self.button_is_pressed:
            speed = self.servo_speed_scale.get()
            self.myserial.send_data(f'jog 1 {speed}\n')
        else:
            self.myserial.send_data('srvstop\n')
        time.sleep(0.05)
        self.myserial.send_data('vmon 8 100\n')

    
    def jog_minus_button_func(self):
        if self.button_is_pressed:
            speed = self.servo_speed_scale.get()
            self.myserial.send_data(f'jog 0 {speed}\n')
        else:
            self.myserial.send_data('srvstop\n')
        time.sleep(0.05)
        self.myserial.send_data('vmon 8 100\n')
    
        




    # handling the 'home' button function
    def home_button_func(self):
        if self.myserial.connect_state == "Connected":
            self.myserial.send_data('home\n')
            time.sleep(0.05)
            self.myserial.send_data('vmon 8 100\n')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    # handling the start / stop button function - keeping track of its state
    def start_stop_button_func(self):
        if self.myserial.connect_state == "Connected":
            if self.start_stop_state == 'start':
                self.start_stop_state = 'stop'
                self.start_stop_button['text'] = 'Stop'
                self.myserial.send_data('start\n')
            else:
                self.start_stop_state = 'start'
                self.start_stop_button['text'] = 'Start'
                self.myserial.send_data('stop\n')
            time.sleep(0.05)
            self.myserial.send_data('vmon 8 100\n')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    # handling the 'servo reset' button function
    def servo_reset_button_func(self):
        if self.myserial.connect_state == "Connected":
            self.myserial.send_data('srvreset\n')
            time.sleep(0.05)
            self.myserial.send_data('vmon 8 100\n')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    
    def abs_rel_toggle_button_func(self, button):
        if self.myserial.connect_state == 'Connected':
            button_index = self.abs_rel_toggle_buttons_list.index(button)
            current_state = button['text']
            if current_state == 'Abs':
                button['text'] = 'Rel'
            elif current_state == 'Rel':
                button['text'] = 'Abs'
            self.abs_rel_states_list[button_index] = button['text']
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    def zero_button_func(self, button):
        if self.myserial.connect_state == 'Connected':
            button_index = self.zero_buttons_list.index(button)
            if self.abs_rel_states_list[button_index] == 'Abs':
                self.rel_zero_values_list[button_index] = float('{:.2f}'.format(float(self.monitor_value_label_list[button_index]['text'])))
            else:
                tk.messagebox.showinfo(title='Warning', message='Need to be in "Abs" mode to use Zero.')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")

    
    def update_rel_abs_button_text(self):
        for index, button in enumerate(self.abs_rel_toggle_buttons_list):
            button['text'] = self.abs_rel_states_list[index]


    def logging_toggle_button_func(self):
        if self.myserial.connect_state == 'Connected':
            if self.logging_toggle_button['text'] == 'Record':
                self.logging_toggle_button['text'] = 'Stop Recording'
                self.myserial.toggle_record('on')
            else:
                self.logging_toggle_button['text'] = 'Record'
                self.myserial.toggle_record('off')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')




    #--------------------------------------------CREATING THE 'GRAPH' TAB USING MATPLOTLIB FIGURES--------------------------------------------
    def create_graph_tab(self):
        self.graph_data = self.myserial.data
        self.graph_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.graph_tab, text='Graph')

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        self.parent_canvas = tk.Canvas(self.graph_tab, bg=self.colors["white"], relief='groove')
        self.parent_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)
        
        self.start_graph_button = tk.Button(self.parent_canvas, text='Start Graph', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=functools.partial(self.start_graph_button_func))
        self.start_graph_button.bind('<Enter>', lambda event, x=self.start_graph_button : self.on_hover(x))
        self.start_graph_button.bind('<Leave>', lambda event, x=self.start_graph_button : self.on_hover_leave(x))
        self.start_graph_button.place(anchor='n', relx=0.77, rely=0.9, relwidth=0.22, relheight=0.07)
        
        self.clear_graph_button = tk.Button(self.parent_canvas, text='Clear Data', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=functools.partial(self.myserial.clear_data))
        self.clear_graph_button.bind('<Enter>', lambda event, x=self.clear_graph_button : self.on_hover(x))
        self.clear_graph_button.bind('<Leave>', lambda event, x=self.clear_graph_button : self.on_hover_leave(x))
        self.clear_graph_button.place(anchor='n', relx=0.52, rely=0.9, relwidth=0.22, relheight=0.07)

        #USE PREFIXED COLORS FOR OUR VALUES SO NO LABELING IS NEEDING INSIDE THE GRAPH
        self.roll_color_label = tk.Label(self.parent_canvas, text='Roll', fg='red', bg=self.colors["white"], font=Helvetica_11_bold)
        self.roll_color_label.place(anchor='n', relx=0.3, rely=0.01)

        self.pitch_color_label = tk.Label(self.parent_canvas, text='Pitch', fg='blue', bg=self.colors["white"], font=Helvetica_11_bold)
        self.pitch_color_label.place(anchor='n', relx=0.4, rely=0.01)

        self.yaw_color_label = tk.Label(self.parent_canvas, text='Yaw', fg='green', bg=self.colors["white"], font=Helvetica_11_bold)
        self.yaw_color_label.place(anchor='n', relx=0.5, rely=0.01)

        self.vane_color_label = tk.Label(self.parent_canvas, text='Vane', fg='purple', bg=self.colors["white"], font=Helvetica_11_bold)
        self.vane_color_label.place(anchor='n', relx=0.6, rely=0.01)

        self.wing_color_label = tk.Label(self.parent_canvas, text='Wing', fg='black', bg=self.colors["white"], font=Helvetica_11_bold)
        self.wing_color_label.place(anchor='n', relx=0.7, rely=0.01)

        self.graph_Separator = ttk.Separator(self.parent_canvas)
        self.graph_Separator.place(anchor='n', relx=0.5, rely=0.058, relwidth=0.5)

        #CREATING MATPLOTLIB PLT FIGURE - DRAW INSIDE THE GRAPH CANVAS CREATED
        self.figure = plt.Figure()
        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=self.parent_canvas)
        self.graph_canvas.get_tk_widget().place(anchor='n', relx=0.5, rely=0.06, relwidth=0.95, relheight=0.82)
        self.graph_canvas.draw()
        
        self.ax = self.figure.add_subplot(111)
        self.ax.grid()
        self.show_coords_event = self.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move_graph)
        self.figure.set_facecolor(self.colors["white"])

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(-40,40),textcoords="offset points",
                    bbox=dict(boxstyle='round', fc='white', ec='k', lw=1),
                    arrowprops=dict(arrowstyle='->'))
        #self.annot.set_visible(False)
        
        #SETTING THE UPDATE RATE OF THE GRAPHING FUNCTION - GRAPHS EVERY 300 MSECS
        self.interval = 300



    def on_mouse_move_graph(self, event):
        try:
            x = event.xdata
            y = event.ydata
            self.annot.xy = (x,y)
            text = "({:.2f}, {:.2f})".format(x,y)
        except:
            text = "None, None"
        self.annot.set_text(text)
        self.annot.set_visible(True)
        self.figure.canvas.draw()
        time.sleep(0.005)




    
    #HANDLE THE 'START/STOP GRAPH' BUTTON
    def start_graph_button_func(self):
        if self.myserial.connect_state == 'Connected':
            if self.start_graph_button['text'] == 'Start Graph':
                self.start_graph_button['text'] = 'Stop Graph'
                try:
                    #restart animation without recreating animation obj
                    self.figure.canvas.mpl_disconnect(self.show_coords_event)
                    self.ani.event_source.start()
                except:
                    #create thread for graphing - avoiding laggy interface with threading
                    print('creating process for graph...')
                    self.graph_thread = threading.Thread(target = self.animation_thread)
                    self.graph_thread.daemon = True
                    self.graph_thread.start()
            else:
                self.start_graph_button['text'] = 'Start Graph'
                self.ani.event_source.stop()
                try:
                    self.enable_coords()
                except:
                    print('error caught in <start_graph_button_func>')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')
        


    def enable_coords(self):
        self.show_coords_event = self.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move_graph)

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(-40,40),textcoords="offset points",
                    bbox=dict(boxstyle='round', fc='white', ec='k', lw=1),
                    arrowprops=dict(arrowstyle='->'))





    #create the animation object and start animating
    def animation_thread(self):
        self.ani = FuncAnimation(self.figure, self.update_graph_gui, interval=self.interval)
        self.ani._start()





    #--------------------------------------------CREATE THE '3D' TAB - REAL TIME 3D ORIENTATION OF OBJECT--------------------------------------------
    def create_3D_tab(self):
        self.my3D_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.my3D_tab, text='Real Time 3D')

        self.my3D_canvas = tk.Canvas(self.my3D_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["black"])
        self.my3D_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        Helvetica_10_bold = tkFont.Font(family='Helvetica', size=10, weight='bold')

        self.tk_rpy_label = tk.Label(self.my3D_canvas, text='Connect to view real time 3D orientation of object', 
            font=Helvetica_10_bold, bg=self.colors["black"], fg='white')
        self.tk_rpy_label.place(anchor='n', relx=0.5, rely=0.85, relwidth=0.7, relheight=0.05)



    # setting up the graphics
    def setup3D(self):
        #if object hasn't been created yet
        if self.setup3D_complete == False:
            self.myobject = mygraphics.ObjectClass(self, self.my3D_canvas, self.WIDTH, self.HEIGHT)
            self.setup3D_complete = True
            self.myobject.main()

            self.update_3D_gui()
        else:
            # re-use already existing object
            self.myobject.update3d()

        






#--------------------------------------------CREATING THE 'SETTINGS' TAB --------------------------------------------
    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.settings_tab, text='Advanced')

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        self.settings_canvas = tk.Canvas(self.settings_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        self.settings_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)


        self.settings_info_label = tk.Label(self.settings_canvas, text='< testing >', font=Helvetica_11_bold, justify='center', relief='groove')
        self.settings_info_label.place(anchor='n', relx=0.7, rely=0.02, relwidth=0.5, relheight=0.7)

        self.gyro_calibration_button = tk.Button(self.settings_canvas, text='Start Gyro\nCalibration', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=self.gyro_calibration_button_func)
        self.gyro_calibration_button.bind('<Enter>', lambda event, x=self.gyro_calibration_button : self.on_hover(x))
        self.gyro_calibration_button.bind('<Leave>', lambda event, x=self.gyro_calibration_button : self.on_hover_leave(x))
        self.gyro_calibration_button.place(anchor='n', relx=0.25, rely=0.05, relwidth=0.31, relheight=0.1)


        self.magnetometer_calibration_button = tk.Button(self.settings_canvas, text='Start Magnetometer\nCalibration', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=self.magnetometer_calibration_button_func)
        self.magnetometer_calibration_button.bind('<Enter>', lambda event, x=self.magnetometer_calibration_button : self.on_hover(x))
        self.magnetometer_calibration_button.bind('<Leave>', lambda event, x=self.magnetometer_calibration_button : self.on_hover_leave(x))
        self.magnetometer_calibration_button.place(anchor='n', relx=0.25, rely=0.2, relwidth=0.31, relheight=0.1)


        self.format_button = tk.Button(self.settings_canvas, text='Start Formatting\nSD Card', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=self.format_button_func)
        self.format_button.bind('<Enter>', lambda event, x=self.format_button : self.on_hover(x))
        self.format_button.bind('<Leave>', lambda event, x=self.format_button : self.on_hover_leave(x))
        self.format_button.place(anchor='n', relx=0.25, rely=0.35, relwidth=0.31, relheight=0.1)


       

    def gyro_calibration_button_func(self):
        if self.myserial.connect_state == "Connected":
            yes_no_msg = tk.messagebox.askquestion(title='WARNING', message='You are about to calibrate the gyro sensor.\nAre you sure?')
            if yes_no_msg == 'yes':
                self.myserial.send_data('acccal\n')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')    
    

    def magnetometer_calibration_button_func(self):
        if self.myserial.connect_state == "Connected":
            yes_no_msg = tk.messagebox.askquestion(title='WARNING', message='You are about to calibrate the magnetometer sensor.\nAre you sure?')
            if yes_no_msg == 'yes':
                self.myserial.send_data('magcal\n')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')  
    

    def format_button_func(self):
        if self.myserial.connect_state == "Connected":
            yes_no_msg = tk.messagebox.askquestion(title='WARNING', message='You are about to format the SD card.\nAre you sure?')
            if yes_no_msg == 'yes':
                self.myserial.send_data('format\n')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')  




    #--------------------------------------------CREATING THE 'ABOUT' TAB COMPANY AND CREATOR INFORMATION--------------------------------------------
    def create_about_tab(self):
        self.about_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.about_tab, text='About')

        Helvetica_11 = tkFont.Font(family='Helvetica', size=11)
        Helvetica_12 = tkFont.Font(family='Helvetica', size=12)

        self.about_canvas = tk.Canvas(self.about_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        self.about_canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        image = Image.open('files\pictures-icon\invibit_logo.png')
        image = image.resize((250, 90), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(image)
        self.about_canvas.create_image(self.WIDTH/2, 30, anchor='n', image=image) 
        self.about_canvas.image = image

        # Text(master, height=1, borderwidth=0)

        self.url = tk.Text(self.about_canvas, height=1, font=Helvetica_12, bg=self.colors["white"], borderwidth=0, cursor="hand2")
        self.url.bind('<Button-1>', lambda event, x=self.url: self.open_link(x))
        self.url.insert('1.0', 'https://www.invibit.com/')
        self.url.configure(state='disabled')
        self.url.place(anchor='n', relx=0.5, rely=0.3, relwidth=0.35, relheight=0.05)

        contact_info_text = "phone: (+30) 210 4212380\nmail: info@invibit.com"

        self.contact_info_label = tk.Text(self.about_canvas, height=1, font=Helvetica_11, borderwidth=0, bg=self.colors["white"])
        self.contact_info_label.insert('1.0', contact_info_text)
        self.contact_info_label.configure(state='disabled')
        self.contact_info_label.place(anchor='n', relx=0.5, rely=0.38, relwidth=0.36, relheight=0.1)

        self.creator_label = tk.Text(self.about_canvas, font=Helvetica_12, bg=self.colors["white"], borderwidth=0)
        self.creator_label.insert('1.0', 'Tuning-GUI creator info:')
        self.creator_label.configure(state='disabled')
        self.creator_label.place(anchor='n', relx=0.5, rely=0.58, relwidth=0.35, relheight=0.1)

        self.creator_info_label = tk.Text(self.about_canvas, font=Helvetica_11, bg=self.colors["white"], borderwidth=0)
        self.creator_info_label.insert('1.0', 'Bill Brousalis\nbill.brousalis@gmail.com')
        self.creator_info_label.configure(state='disabled')
        self.creator_info_label.place(anchor='n', relx=0.5, rely=0.65, relwidth=0.35, relheight=0.1)

        
        # Firmware version at the bottom of the page
        self.firmware_version_label = tk.Label(self.about_canvas, text='version : (connect to view firmware version)', bg=self.colors["white"], font=self.font +'11')
        self.firmware_version_label.place(anchor='n', relx=0.65, rely=0.93)


    # small function to open url link provided in the 'about' tab
    def open_link(self, label):
        url = label.get('1.0', 'end')
        print('url = ', url)
        webbrowser.open_new(url)




    #----------------------------------------------------------------------------------------------------------------

    def on_hover(self, widget, highlight_color=colors["highlight"]):
        widget.configure(bg=highlight_color)


    def on_hover_leave(self, widget, init_color=colors["light grey"]):
        widget.configure(bg=init_color)


    #function creating a thread continuously reading data from the serial port
    def read_serial_thread(self):
        self.read_serial_t = threading.Thread(target=self.read_serial)
        self.read_serial_t.daemon = True
        self.read_serial_t.start()



    #function checking connection state and using serialComms module to receive data
    def read_serial(self):
        while self.myserial.connect_state == "Connected" and self.myserial.quat == False and self.current_tab in self.tabs_to_be_updated:
            self.myserial.receive_data()
            time.sleep(0.0001)
            self.reading_thread = True
        self.reading_thread = False
            


    def wait_for_thread_to_close(self):
        while self.reading_thread == True:
            time.sleep(0.0005)
            print('waiting for thread to close...')





    #generic update gui function running in a thread - calling individual update functions depending on current tab
    def update_gui(self):
        while True:
            self.myserial.COM = self.com_port_var.get()          
            self.myserial.BAUD = self.baud_rate_var.get()

            #current tab : 0 > vane/servo , 1 > monitor, 2 > graph  3 > 3D, 4 > about
            self.current_tab = self.tab_parent.index(self.tab_parent.select()) 
            if self.current_tab == 0:
                self.update_vane_gui()
                time.sleep(0.2)
            if self.current_tab == 1:
                self.update_monitor_gui()
                time.sleep(0.1)
            elif self.current_tab == 3:
                if self.myserial.connect_state == "Connected" and self.myserial.quat == True:
                    self.update_3D_gui()
                    time.sleep(0.1)
            else:
                time.sleep(0.05)
           
     


    """
    # function updating the gui when 'vane/servo' tab is currently open
    def update_vane_gui(self):
        try:
            for entry_wid in self.vane_entry_widgets_list:
                if ' ' in entry_wid.get():
                    tmp = entry_wid.get().replace(' ', '')
                    entry_wid.delete(0, 'end')
                    entry_wid.insert(0, tmp)
        except:
            print('update vane gui error...')
    """



    # function updating the gui when 'monitor' tab is currently open
    def update_monitor_gui(self):
        if self.myserial.connect_state == "Connected" and self.myserial.quat == False:
            try:             
                graph_data = self.myserial.return_graph_data()
                values = [item[len(item)-1] for item in graph_data]    
                for index, (val_label, value) in enumerate(zip(self.monitor_value_label_list, values)):
                    if index == 4:
                        if self.abs_rel_states_list[index] == 'Abs':
                            val_label['text'] = str(round(-value , 2))
                        elif self.abs_rel_states_list[index] == 'Rel':
                            val_label['text'] = str(round( (-value - self.rel_zero_values_list[index]) , 2))
                        continue
                    if self.abs_rel_states_list[index] == 'Abs':
                        val_label['text'] = str(round(value, 2))
                    elif self.abs_rel_states_list[index] == 'Rel':
                        val_label['text'] = str(round(value - self.rel_zero_values_list[index], 2))
            except:
                print('error on update_monitor_gui...')
        else:
            pass





    # function updating the gui when 'graph' tab is currently open
    def update_graph_gui(self, i): 
        self.ax.clear()
        try:
            # either plot or read serial, not both at the same time / avoid crashes
            while self.myserial.is_reading_serial == True:
                time.sleep(0.001)

            graph_data = self.myserial.return_graph_data()
            t_count_array = list(self.myserial.return_t_count_array())
            # plot the values
            for i, item in enumerate(graph_data):
                self.ax.plot(t_count_array, item, self.graph_color_list[i])
            self.ax.grid()

        except Exception as e:
            print(f'update_graph_gui exception : {e}')
 



    # function updating the gui when '3D' tab is currently open
    def update_3D_gui(self):
        try:
            # write roll pitch yaw values on screen
            self.tk_rpy_label['text'] = "Roll: {:.2f}  ||  Pitch: {:.2f}  ||  Yaw: {:.2f}".format(self.myobject.tk_roll,
                self.myobject.tk_pitch, self.myobject.tk_yaw)
        except Exception as e:
            print(f"update_3D_gui exception : {e}")
  
            




    # FUNCTION CALLED EVERY TIME THE USER SWITCHES TABS - KEEPS TRACK OF CURRENT AND PREVIOUS TAB,
    # SENDING APPROPRIATE VMON COMMAND TO DISPLAY CORRECT VALUES DEPENING ON THE CURRENT TAB 
    def on_tab_switch(self, event):
        try:
            self.current_tab = self.tab_parent.index(self.tab_parent.select())
            # THE 4TH (3RD COUNTING FROM 0) TAB IS THE '3D' TAB
            # IT REQUIRES SPECIAL ATTENTION, NEEDS TO SEND "VMON 7 100"  
            # UPON SWITCHING TO IT IN ORDER TO RECEIVE THE QUATERNION DATA IT EXPECTS

            # if previous tab is the 3D tab, switch to non quaternion data
            if self.previous_tab == 3:
                self.wait_for_thread_to_close()
                self.myserial.quat = False

            # Close graphing when switching to another tab / avoid crashes
            if self.previous_tab == 2 and self.current_tab != 2:
                if self.start_graph_button['text'] == 'Stop Graph':
                    self.start_graph_button_func()

            # if the current tab is the 3D tab, switch to quaternion data
            if self.current_tab == 3:
                self.wait_for_thread_to_close()
                self.myserial.send_data("vmon 7 100\n")
                self.myserial.quat = True

                #>>>> following not needed anymore (?)
                # for some reason, if current tab = 3, it doesn't reach the end of 
                # the function where we do the following assignment, so this is a quick and dirty fix:
                self.previous_tab = self.current_tab

                #call setup function to handle 3D
                self.setup3D()
            
            # arriving in an updating tab, coming from a non updating one > request data
            elif (self.current_tab in self.tabs_to_be_updated) and (self.previous_tab not in self.tabs_to_be_updated):
                self.myserial.send_data("vmon 8 100\n")
                time.sleep(0.05)
                self.read_serial_thread()

            # moving from and updating tab to another updating tab > change nothing                    
            # dont remove this, needed so it doesn't fall into the next <else>
            elif (self.current_tab in self.tabs_to_be_updated) and (self.previous_tab in self.tabs_to_be_updated):
                pass
            # arriving on the first tab, receive dump containing current values / variables
            elif self.current_tab == 0:
                self.wait_for_thread_to_close()
                self.myserial.quat = False
                self.myserial.receive_dump()
            # arriving on non updating-static tab
            else:
                self.wait_for_thread_to_close()
                self.myserial.send_data('vmon 0 0\n')
            # update previous tab to current tab on tab switch
            self.previous_tab = self.current_tab
        except:
            print("TAB_SWITCH ERROR")








    # write to the config file 
    # save the com port / baud rate last used inside the application
    # in order to retrieve them when re-opening the app
    def write_to_config(self):
        with open('files\config.txt', 'r+') as file:
            lines = file.readlines()
            lines = [line.replace('\n', '') for line in lines]
            file.seek(0)
            for line in lines:
                if "GRAPH_DISPLAY_LAST_X_SECONDS" in line:
                    file.write(line + '\n')
            file.truncate()
            strings = ["DEFAULT_COM=", self.com_port_var.get(), '\n', "DEFAULT_BAUD=", str(self.baud_rate_var.get()), '\n', "DEFAULT_SERVO_SPEED=", str(self.servo_speed_scale.get()), '\n']
            strings += [self.abs_rel_states_list[0].upper(), "/ZERO_ROLL=", str(self.rel_zero_values_list[0]), '\n', self.abs_rel_states_list[1].upper(), "/ZERO_PITCH=", str(self.rel_zero_values_list[1]), '\n', self.abs_rel_states_list[2].upper(), "/ZERO_YAW=", str(self.rel_zero_values_list[2]), '\n']
            strings += [self.abs_rel_states_list[3].upper(), "/ZERO_VANE=", str(self.rel_zero_values_list[3]), '\n', self.abs_rel_states_list[4].upper(), "/ZERO_WING=", str(self.rel_zero_values_list[4]), '\n']
            save = ''.join(strings)
            file.write(save)




    # run upon exiting the app - handle serial connection
    # run the write_to_config function to save
    def exit(self):
        self.myserial.send_data("vmon 0 0\n")
        self.myserial.close_csv()
        self.write_to_config()
        self.myserial.connect_state = "Not Connected"
        self.quit()
        self.destroy()





#-------------------------MAIN - RUN APP-------------------------
if __name__ == '__main__':
    app = Application()
    app.resizable(False, False)
    app.protocol("WM_DELETE_WINDOW", app.exit)
    app.mainloop()