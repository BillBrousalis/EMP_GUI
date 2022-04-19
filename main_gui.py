#--------------------------------------------IMPORTS--------------------------------------------
import serial
import tkinter as tk
import tkinter.font as tkFont
from tkinter import Toplevel, ttk
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

    #--------------------------------------------INITIALIZING CLASS--------------------------------------------
    def __init__(self):
        super().__init__()
        self.title("NAVI-TUNING")
        # add icon to the top left of the window
        self.iconbitmap(default='files\pictures-icon\\boat_icon.ico')

        self.min_max_defaults_list = []
        self.default_com, self.default_baud, self.default_servo_speed = None, None, 50

        self.s = serial_comms.SerialClass()
        self.create_GUI()
        self.read_last_config()
        self.s.set(com=self.default_com, baud=self.default_baud)
        self.set_defaults()
        self.reading_thread = False
 

    def set_defaults(self):
        self.com_port_var.set(self.s.COM)
        self.servo_speed_scale.set(self.default_servo_speed)
        for i in range(len(self.monitor_buttons)):
            self.monitor_buttons[i]["abs-rel"]["text"] = self.monitor_buttons[i]["toggle-state"]


    #--------------------------------------------CREATING GUI FRAME / TABS AND THREAD TO KEEP REFRESHING IT--------------------------------------------
    def create_GUI(self):
        self.mainFrame = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT)
        self.mainFrame.pack()
        self.create_serial_gui()

        self.tab_parent = ttk.Notebook(self.mainFrame)

        self.tabs = [{'name': 'Tuning', 'thread': False},
                     {'name': 'Monitor', 'thread': True},
                     {'name': 'Graphing', 'thread': True},
                     {'name': 'Advanced', 'thread': False},
                     {'name': 'About', 'thread': False}]

        self.create_tuning_tab()
        self.create_monitor_tab()                       
        self.create_graph_tab()
        self.create_calib_tab()
        self.create_about_tab()

        self.tab_parent.bind("<<NotebookTabChanged>>", self.on_tab_switch)
        self.previous_tab = 0
        self.tab_parent.place(anchor='n', relx=0.5, rely=0.07, relwidth=1, relheight=0.93)


        
    #--------------------------------------------TOP OF THE FRAME / WIDGETS TO HANDLE SERIAL CONNECTIONS--------------------------------------------
    def create_serial_gui(self):
        canvas = tk.Canvas(self.mainFrame, width=self.WIDTH, height=self.HEIGHT/6, bg=self.colors["light grey"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=0.08)

        Helvetica_10_bold = tkFont.Font(family='Helvetica', size=10, weight='bold')

        self.port_label = tk.Label(canvas, text='Com port:', font=Helvetica_10_bold, bg = self.colors["light grey"])
        self.port_label.place(anchor='n', relx=0.1, rely=0.15, relwidth=0.15, relheight=0.7)

        self.com_port_var = tk.StringVar(canvas)
        self.com_port_var.set(self.s.COM)

        avail_ports = self.s.get_ports()
        self.com_port_menu = tk.OptionMenu(canvas, self.com_port_var, *avail_ports)
        self.com_port_menu.config(font=Helvetica_10_bold, bg=self.colors["light grey"], relief='groove')
        self.com_port_menu.place(anchor='n', relx=0.25, rely=0.155, relwidth=0.17, relheight=0.7)

        self.refresh_com_ports_button = tk.Button(canvas, text='Refresh', bg=self.colors["light grey"], relief='groove',
            command=functools.partial(self.update_port_OptionMenu))
        self.refresh_com_ports_button.bind('<Enter>', lambda event, x=self.refresh_com_ports_button : self.on_hover(x))
        self.refresh_com_ports_button.bind('<Leave>', lambda event, x=self.refresh_com_ports_button : self.on_hover_leave(x))
        self.refresh_com_ports_button.place(anchor='n', relx=0.385, rely=0.205, relwidth=0.1, relheight=0.6)

        self.baud_rate_var = tk.StringVar(canvas) 
        self.baud_rate_var.set(str(self.s.BAUD))

        self.baud_label = tk.Label(canvas, text='Baud Rate:', font=Helvetica_10_bold, bg=self.colors["light grey"])
        self.baud_label.place(anchor='n', relx=0.52, rely=0.15, relwidth=0.15, relheight=0.7)

        self.baud_menu = tk.OptionMenu(canvas, self.baud_rate_var, *self.s.baud_rate_list)
        self.baud_menu.config(font=Helvetica_10_bold, bg=self.colors["light grey"], relief='groove')
        self.baud_menu.place(anchor='n', relx=0.68, rely=0.15, relwidth=0.17, relheight=0.7)

        self.connect_button = tk.Button(canvas, text='Connect', font=Helvetica_10_bold, relief='groove',
            bg=self.colors["black"], activebackground=self.colors["light grey"], fg='white', command=functools.partial(self.connect_button_func))
        self.connect_button.place(anchor='n', relx=0.875, rely=0.15, relwidth=0.17, relheight=0.7)


    #--------------------------------------------HANDLE SERIAL_GUI'S CONNECT BUTTON--------------------------------------------
    def connect_button_func(self):
        if self.connect_button['text'] == "Connect":
            self.s.COM = self.com_port_var.get()          
            self.s.BAUD = self.baud_rate_var.get()

            self.s.connect()
            self.connect_button['text'] = "Close"
            time.sleep(0.01)
            if self.s.connected:
                self.firmware_version_label['text'] = f'version : {self.s.get_firmware_version()}'
                self.update_tuning_values()
                self.handle_tabs()
            else:
                self.connect_button['text'] = "Connect"
                tkinter.messagebox.showinfo("Error", message="Error connecting to serial port")

        else:
            if self.s.connected:
                if self.start_graph_button['text'] == "Stop Graph":
                    self.start_graph_button_func()
                self.cleanup_serial()
            self.connect_button['text'] = "Connect"


    def cleanup_serial(self):
        if self.s.connected:
            self.s.send("vmon 0 0")
            self.s.serialFlush()
            time.sleep(0.01)
            self.s.disconnect()


    def handle_tabs(self):
        if self.tabs[self.current_tab]["thread"]:
            if self.s.connected:
                self.s.serialFlush()
                self.s.send("vmon 8 100")
                self.read_serial_thread()
                if self.current_tab == 1:
                    self.monitor_thread = threading.Thread(target=self.monitor_thread_loop)
                    self.monitor_thread.daemon = True
                    self.monitor_thread.start()
        else:
            self.s.send("vmon 0 0")
            self.wait_for_thread_to_close()
            self.s.serialFlush()


    # handling the refresh button for the available ports
    def update_port_OptionMenu(self):     
        avail_ports = self.s.get_ports()
        menu = self.com_port_menu.children['menu']
        menu.delete(0, 'end')
        for port in avail_ports:
            menu.add_command(label=port, command=lambda p=port: self.com_port_var.set(p))


    #--------------------------------------------CREATING THE 'VANE / SERVO' TAB - ADDING WIDGETS--------------------------------------------
    def create_tuning_tab(self):
        self.tuning_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.tuning_tab, text='Tuning')
        canvas = tk.Canvas(self.tuning_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        self.tuning_values = [{"text": "Offset :", "min": -20, "max": 20, "default": 0, "id": "voffs", "step": 0.01},
                              {"text": "Gain(Deg/Deg) :", "min": -5000, "max": 5000, "default": 0.00, "id": "vgain", "step": 0.01},
                              {"text": "Vane Scale(Deg/V) :", "min": -5000, "max": 5000, "default": 0.00, "id": "vscale", "step": 0.01},
                              {"text": "Delay(ms) :", "min": 0, "max": 2000, "default": 0, "id": "vdelay", "step": 1},
                              {"text": "Velocity :", "min": 0, "max": 5000000, "default": 0, "id": "vvel", "step": 1},
                              {"text": "Acceleration :", "min": 0, "max": 5000000, "default": 0, "id": "vacc", "step": 1}, 
                              {"text": "Kp :", "min": 0, "max": 32767, "default": 0, "id": "kp", "step": 1},
                              {"text": "Ki :", "min": 0, "max": 32767, "default": 0, "id": "ki", "step": 1},
                              {"text": "Kd :", "min": 0, "max": 32767, "default": 0, "id": "kd", "step": 1},
                              {"text": "Kv :", "min": 0, "max": 32767, "default": 0, "id": "kv", "step": 1},
                              {"text": "Power Limit(%) :", "min": 0, "max": 100, "default": 0, "id": "power", "step": 1}]


        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        for i, config in enumerate(self.tuning_values): 
            y = (0.03+i*0.08)
            self.mylabel = tk.Label(canvas, text=config["text"], font=Helvetica_11_bold, bg = self.colors["white"], anchor='e')
            self.mylabel.place(anchor='n', relx=0.17, rely=y, relwidth=0.3, relheight=0.065)  

            self.entry = tk.Entry(canvas, font=Helvetica_11_bold, bg=self.colors["light grey"], justify='center', relief='groove')
            self.entry.insert(0, config["default"])
            self.entry.bind('<Return>', lambda event, x=i: self.on_enter_press(x))
            self.entry.bind('<Enter>', lambda event, x=self.entry : self.on_hover(x))
            self.entry.bind('<Leave>', lambda event, x=self.entry : self.on_hover_leave(x))
            self.entry.place(anchor='n', relx=0.54, rely=y+0.005, relwidth=0.42, relheight=0.055)
            self.tuning_values[i]["entry"] = self.entry

            self.minus_but = tk.Button(canvas, text='-', font='Helvetica 14 bold', bg=self.colors["light grey"],
                relief='groove', command=functools.partial(self.adjust_value, '-', i))
            self.minus_but.bind('<Enter>', lambda event, x=self.minus_but : self.on_hover(x))
            self.minus_but.bind('<Leave>', lambda event, x=self.minus_but : self.on_hover_leave(x))    
            self.minus_but.place(anchor='n', relx=0.82, rely=y+0.005, relwidth=0.095, relheight=0.05)

            self.plus_but = tk.Button(canvas, text='+', font='Helvetica 13 bold', bg=self.colors["light grey"],
                relief='groove', command=functools.partial(self.adjust_value, '+', i))
            self.plus_but.bind('<Enter>', lambda event, x=self.plus_but : self.on_hover(x))
            self.plus_but.bind('<Leave>', lambda event, x=self.plus_but : self.on_hover_leave(x))
            self.plus_but.place(anchor='n', relx=0.92, rely=y+0.005, relwidth=0.095, relheight=0.05)


        # SAVE - RESET DEFAULT VALUES BUTTONS
        self.save_button = tk.Button(canvas, text='Save', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=functools.partial(self.save_values))
        self.save_button.bind('<Enter>', lambda event, x=self.save_button : self.on_hover(x))
        self.save_button.bind('<Leave>', lambda event, x=self.save_button : self.on_hover_leave(x))
        self.save_button.place(anchor='n', relx=0.844, rely=0.92, relwidth=0.25, relheight=0.06)



    #--------------------------------------------SEND VALUE (ON ENTER PRESS) OF THE ENTRY WIDGET IN FOCUS--------------------------------------------
    def on_enter_press(self, idx):
        widget = self.tuning_values[idx]["entry"]
        #check if text is numeric:
        if widget.get().replace('.', '').replace(' ', '').replace('-', '').isdigit():
            if self.check_bounds(): 
                id = self.tuning_values[idx]["id"]
                if self.tuning_values[idx]["step"] == 1:
                    try:
                        #check if given value is an integer
                        int(widget.get())
                    # show error message if value is not : integer / in bounds / numeric
                    except:
                        tk.messagebox.showinfo(title="Error", message="Value is not an integer.")
                        return None
                self.s.send(f'{id} {widget.get()}')
                time.sleep(0.05)
                self.update_tuning_values()
            else:
                tk.messagebox.showinfo(title="Error", message="Values are out of bounds.")    
        else:
            tk.messagebox.showinfo(title="Error", message="Values are not numeric.")


    # update tuning tab's values after using the 'dump1' command
    def update_tuning_values(self):
        try:
            if not self.s.connected: return None
            fresh_dump = self.s.get_dump()
            for idx, value_set in enumerate(fresh_dump.items()):
                val = str(value_set[1]).strip().replace(" ", "")
                self.tuning_values[idx]["entry"].delete(0, 'end')
                self.tuning_values[idx]["entry"].insert(0, val)
        except Exception as e:
            print(f'error in update_tuning_values : {e}')        


    # function handling the adjustment button of the 'vane/servo' tab
    def adjust_value(self, sign, idx):
        entry = self.tuning_values[idx]["entry"]
        min, max = self.tuning_values[idx]["min"], self.tuning_values[idx]["max"]
        step = self.tuning_values[idx]["step"]
        val = entry.get()
        # validate that input is a number
        try:
            assert val.replace('.', '').replace('-', '').isdigit()
        except:
            tkinter.messagebox.showinfo(title="Error", message="Input is not a number.")
            raise Exception("Boo! Not a number...")

        if step != 1: val = float(val)
        else: val = int(val)

        if sign == "+": 
            val += step
        else: 
            val -= step

        if val > max: val = max
        elif val < min: val = min
        
        if step != 1: val = '{:.2f}'.format(val)
        val = str(val)
        if self.s.connected:
            self.s.send(f'{self.tuning_values[idx]["id"]} {val.strip()}')
            self.update_tuning_values()
        else:
            print("not connected")


    # handling the 'save' button function
    def save_values(self):
        if self.s.connected:
            self.s.send("save")
        else:
            tkinter.messagebox.showinfo(title="Error", message="You are not connected to a serial port.")


    # determining if given values are inside their min/max bounds
    def check_bounds(self):
        for widget in self.tuning_values:
            val = float(widget["entry"].get())
            if val < widget["min"] or val > widget["max"]:
                return False
        return True



    #--------------------------------------------CREATING THE 'MONITOR' TAB - ADDING WIDGETS--------------------------------------------
    def create_monitor_tab(self):
        self.monitor_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.monitor_tab, text='Monitor')
        canvas = tk.Canvas(self.monitor_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        self.monitor_values = [{"text": "Roll :", "default": 0, "widget": None, "zero-rel-val": None, "color": "r"},
                               {"text": "Pitch :", "default": 0, "widget": None, "zero-rel-val": None, "color": "b"},
                               {"text": "Yaw :", "default": 0, "widget": None, "zero-rel-val": None, "color": "g"},
                               {"text": "Vane :", "default": 0, "widget": None, "zero-rel-val": None, "color": "m"},
                               {"text": "Wing :", "default": 0, "widget": None, "zero-rel-val": None, "color": "k"}]
        
        self.monitor_buttons = [{"abs-rel": None, "toggle-state": None, "zero": None}  for _ in range(5)]

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        #--------------------------------------------AGAIN USING A FOR LOOP TO AVOID BIG BLOCK OF REPEATING CODE--------------------------------------------
        for i, config in enumerate(self.monitor_values):
            y = (0.05+i*0.11)
            self.monitor_label = tk.Label(canvas, text=config["text"], font=Helvetica_11_bold, bg = self.colors["white"], anchor='e')
            self.monitor_label.place(anchor='n', relx=0.13, rely=y, relwidth=0.11, relheight=0.06)  

            self.monitor_value_label = tk.Label(canvas, text=str(config["default"]), font=Helvetica_11_bold, bg=self.colors["light grey"], justify='center', relief='groove')
            self.monitor_value_label.place(anchor='n', relx=0.45, rely=y, relwidth=0.45, relheight=0.06)
            self.monitor_values[i]["widget"] = self.monitor_value_label

            self.abs_rel_toggle_button = tk.Button(canvas, text='Abs', font=Helvetica_11_bold, bg=self.colors["light grey"])
            self.abs_rel_toggle_button.configure(relief='groove', command=lambda x=i : self.abs_rel_toggle_button_func(x))
            self.abs_rel_toggle_button.bind('<Enter>', lambda event, x=self.abs_rel_toggle_button : self.on_hover(x))
            self.abs_rel_toggle_button.bind('<Leave>', lambda event, x=self.abs_rel_toggle_button : self.on_hover_leave(x))
            self.abs_rel_toggle_button.place(anchor='n', relx=0.76, rely=y, relwidth=0.1, relheight=0.06)
            self.monitor_buttons[i]["abs-rel"] = self.abs_rel_toggle_button
        
            self.zero_button = tk.Button(canvas, text='Zero', font=Helvetica_11_bold, bg=self.colors["light grey"])
            self.zero_button.configure(relief='groove', command=lambda x=i: self.zero_button_func(x))
            self.zero_button.bind('<Enter>', lambda event, x=self.zero_button : self.on_hover(x))
            self.zero_button.bind('<Leave>', lambda event, x=self.zero_button : self.on_hover_leave(x))
            self.zero_button.place(anchor='n', relx=0.88, rely=y, relwidth=0.1, relheight=0.06)
            self.monitor_buttons[i]["zero"] = self.zero_button
            
            self.monitor_buttons[i]["toggle-state"] = self.monitor_buttons[i]["abs-rel"]["text"]
            self.monitor_values[i]["zero-rel-val"] = 0

        for i in range(5):
            y = (0.135+i*0.11)
            self.valSeparator = ttk.Separator(canvas)
            self.valSeparator.place(anchor='n', relx=0.5, rely=y, relwidth=0.8)

        self.start_stop_state = 'start'
        self.start_stop_button = tk.Button(canvas, text='Start', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=lambda: self.start_stop_button_func())
        self.start_stop_button.bind('<Enter>', lambda event, x=self.start_stop_button : self.on_hover(x))
        self.start_stop_button.bind('<Leave>', lambda event, x=self.start_stop_button : self.on_hover_leave(x))
        self.start_stop_button.place(anchor='n', relx=0.48, rely=0.73, relwidth=0.17, relheight=0.07)

        self.home_button = tk.Button(canvas, text='Home', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=lambda: self.home_button_func())
        self.home_button.bind('<Enter>', lambda event, x=self.home_button : self.on_hover(x))
        self.home_button.bind('<Leave>', lambda event, x=self.home_button : self.on_hover_leave(x))
        self.home_button.place(anchor='n', relx=0.68, rely=0.73, relwidth=0.17, relheight=0.07)

        self.servo_reset_button = tk.Button(canvas, text='Reset', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=self.servo_reset_button_func)
        self.servo_reset_button.bind('<Enter>', lambda event, x=self.servo_reset_button : self.on_hover(x))
        self.servo_reset_button.bind('<Leave>', lambda event, x=self.servo_reset_button : self.on_hover_leave(x))
        self.servo_reset_button.place(anchor='n', relx=0.88, rely=0.73, relwidth=0.17, relheight=0.07)

        self.jog_plus_button = tk.Button(canvas, text='Jog +', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.jog_plus_button.bind("<ButtonPress>", lambda event, parent=self.jog_plus_button: self.button_press(parent))
        self.jog_plus_button.bind("<ButtonRelease>", lambda event, parent=self.jog_plus_button: self.button_release(parent))
        self.jog_plus_button.bind('<Enter>', lambda event, x=self.jog_plus_button : self.on_hover(x))
        self.jog_plus_button.bind('<Leave>', lambda event, x=self.jog_plus_button : self.on_hover_leave(x))
        self.jog_plus_button.place(anchor='n', relx=0.28, rely=0.68, relwidth=0.17, relheight=0.07)

        self.jog_minus_button = tk.Button(canvas, text='Jog -', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.jog_minus_button.bind("<ButtonPress>", lambda event, parent=self.jog_minus_button: self.button_press(parent))
        self.jog_minus_button.bind("<ButtonRelease>", lambda event, parent=self.jog_minus_button: self.button_release(parent))
        self.jog_minus_button.bind('<Enter>', lambda event, x=self.jog_minus_button : self.on_hover(x))
        self.jog_minus_button.bind('<Leave>', lambda event, x=self.jog_minus_button : self.on_hover_leave(x))
        self.jog_minus_button.place(anchor='n', relx=0.28, rely=0.78, relwidth=0.17, relheight=0.07)

        self.servo_speed_label = tk.Label(canvas, text='speed', font='Helvetica 10 bold', bg=self.colors["white"], relief='groove')
        self.servo_speed_label.place(anchor='n', relx=0.08, rely=0.63, relwidth=0.1, relheight=0.05)  

        self.servo_speed_scale = tk.Scale(canvas, from_=0, to=100, tickinterval=100, orient='vertical', bg=self.colors["light grey"], relief='groove')
        self.servo_speed_scale.set(self.default_servo_speed)
        self.servo_speed_scale.bind('<Enter>', lambda event, x=self.servo_speed_scale : self.on_hover(x))
        self.servo_speed_scale.bind('<Leave>', lambda event, x=self.servo_speed_scale : self.on_hover_leave(x))
        self.servo_speed_scale.place(anchor='n', relx=0.1, rely=0.675, relwidth=0.15, relheight=0.18)

        self.record_toggle_but = tk.Button(canvas, text='Record', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.record_toggle_but.configure(command=self.record_toggle_but_func)
        self.record_toggle_but.bind('<Enter>', lambda event, x=self.record_toggle_but : self.on_hover(x))
        self.record_toggle_but.bind('<Leave>', lambda event, x=self.record_toggle_but : self.on_hover_leave(x))
        self.record_toggle_but.place(anchor='n', relx=0.84, rely=0.85, relwidth=0.25, relheight=0.07)

        self.default_servo_speed = self.s.return_default_servo_speed()
        self.servo_speed_scale.set(self.default_servo_speed)




    def button_press(self, parent):
        self.button_is_pressed = True
        if self.s.connected:
            if parent == self.jog_plus_button:
                self.jog_plus_button_func()
            elif parent == self.jog_minus_button:
                self.jog_minus_button_func()


    def button_release(self, parent):
        self.button_is_pressed = False
        if self.s.connected:
            if parent == self.jog_plus_button:
                self.jog_plus_button_func()
            elif parent == self.jog_minus_button:
                self.jog_minus_button_func()
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')


    def jog_plus_button_func(self):
        if self.button_is_pressed:
            speed = self.servo_speed_scale.get()
            self.s.send(f'jog 1 {speed}')
        else:
            self.s.send('srvstop')
        time.sleep(0.05)
        self.s.send('vmon 8 100')

    
    def jog_minus_button_func(self):
        if self.button_is_pressed:
            speed = self.servo_speed_scale.get()
            self.s.send(f'jog 0 {speed}')
        else:
            self.s.send('srvstop')
        time.sleep(0.05)
        self.s.send('vmon 8 100')


    def home_button_func(self):
        if self.s.connected:
            self.s.send('home')
            time.sleep(0.05)
            self.s.send('vmon 8 100')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    def start_stop_button_func(self):
        if self.s.connected:
            if self.start_stop_state == 'start':
                self.start_stop_state = 'stop'
                self.start_stop_button['text'] = 'Stop'
                self.s.send('start')
            else:
                self.start_stop_state = 'start'
                self.start_stop_button['text'] = 'Start'
                self.s.send('stop')
            time.sleep(0.05)
            self.s.send('vmon 8 100')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    def servo_reset_button_func(self):
        if self.s.connected:
            self.s.send('srvreset')
            time.sleep(0.05)
            self.s.send('vmon 8 100')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")

    
    def abs_rel_toggle_button_func(self, idx):
        if self.s.connected:
            current_state = self.monitor_buttons[idx]["abs-rel"]["text"]
            if current_state == 'Abs':
                self.monitor_buttons[idx]["abs-rel"]["text"] = 'Rel'
            elif current_state == 'Rel':
                self.monitor_buttons[idx]["abs-rel"]["text"] = 'Abs'
            self.monitor_buttons[idx]["toggle-state"] = self.monitor_buttons[idx]["abs-rel"]["text"]
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")


    def zero_button_func(self, idx):
        if self.s.connected:
            if self.monitor_buttons[idx]["toggle-state"] == "Abs":
                self.monitor_values[idx]["zero-rel-val"] = float('{:.2f}'.format(float(self.monitor_values[idx]["widget"]["text"])))
            else:
                tk.messagebox.showinfo(title='Warning', message='Need to be in "Abs" mode to use Zero.')
        else:
            tkinter.messagebox.showinfo(title='Error', message="You are not connected to a serial port.")

    
    def update_rel_abs_button_text(self):
        for x in self.monitor_buttons:
            x["abs-rel"]["text"] = x["toggle-state"]


    def record_toggle_but_func(self):
        if self.s.connected:
            if self.record_toggle_but['text'] == 'Record':
                self.record_toggle_but['text'] = 'Stop Recording'
                self.s.toggle_record('on')
            else:
                self.record_toggle_but['text'] = 'Record'
                self.s.toggle_record('off')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')



    #--------------------------------------------CREATING THE 'GRAPH' TAB USING MATPLOTLIB FIGURES--------------------------------------------
    def create_graph_tab(self):
        self.graph_data = self.s.data
        self.graph_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.graph_tab, text='Graph')

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        canvas = tk.Canvas(self.graph_tab, bg=self.colors["white"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)
        
        self.start_graph_button = tk.Button(canvas, text='Start Graph', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=functools.partial(self.start_graph_button_func))
        self.start_graph_button.bind('<Enter>', lambda event, x=self.start_graph_button : self.on_hover(x))
        self.start_graph_button.bind('<Leave>', lambda event, x=self.start_graph_button : self.on_hover_leave(x))
        self.start_graph_button.place(anchor='n', relx=0.77, rely=0.9, relwidth=0.22, relheight=0.07)
        
        self.clear_graph_button = tk.Button(canvas, text='Clear Data', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=functools.partial(self.s.clear_data))
        self.clear_graph_button.bind('<Enter>', lambda event, x=self.clear_graph_button : self.on_hover(x))
        self.clear_graph_button.bind('<Leave>', lambda event, x=self.clear_graph_button : self.on_hover_leave(x))
        self.clear_graph_button.place(anchor='n', relx=0.52, rely=0.9, relwidth=0.22, relheight=0.07)

        #USE PREFIXED COLORS FOR OUR VALUES SO NO LABELING IS NEEDING INSIDE THE GRAPH
        self.roll_color_label = tk.Label(canvas, text='Roll', fg='red', bg=self.colors["white"], font=Helvetica_11_bold)
        self.roll_color_label.place(anchor='n', relx=0.3, rely=0.01)

        self.pitch_color_label = tk.Label(canvas, text='Pitch', fg='blue', bg=self.colors["white"], font=Helvetica_11_bold)
        self.pitch_color_label.place(anchor='n', relx=0.4, rely=0.01)

        self.yaw_color_label = tk.Label(canvas, text='Yaw', fg='green', bg=self.colors["white"], font=Helvetica_11_bold)
        self.yaw_color_label.place(anchor='n', relx=0.5, rely=0.01)

        self.vane_color_label = tk.Label(canvas, text='Vane', fg='purple', bg=self.colors["white"], font=Helvetica_11_bold)
        self.vane_color_label.place(anchor='n', relx=0.6, rely=0.01)

        self.wing_color_label = tk.Label(canvas, text='Wing', fg='black', bg=self.colors["white"], font=Helvetica_11_bold)
        self.wing_color_label.place(anchor='n', relx=0.7, rely=0.01)

        self.graph_Separator = ttk.Separator(canvas)
        self.graph_Separator.place(anchor='n', relx=0.5, rely=0.058, relwidth=0.5)

        #CREATING MATPLOTLIB PLT FIGURE - DRAW INSIDE THE GRAPH CANVAS CREATED
        self.figure = plt.Figure()
        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=canvas)
        self.graph_canvas.get_tk_widget().place(anchor='n', relx=0.5, rely=0.06, relwidth=0.95, relheight=0.82)
        self.graph_canvas.draw()
        
        self.ax = self.figure.add_subplot(111)
        self.ax.grid()
        self.show_coords_event = self.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move_graph)
        self.figure.set_facecolor(self.colors["white"])

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(-40,40),textcoords="offset points",
                    bbox=dict(boxstyle='round', fc='white', ec='k', lw=1),
                    arrowprops=dict(arrowstyle='->'))
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
        if self.s.connected:
            if self.start_graph_button['text'] == 'Start Graph':
                self.start_graph_button['text'] = 'Stop Graph'
                try:
                    #restart animation without recreating animation obj
                    self.figure.canvas.mpl_disconnect(self.show_coords_event)
                    self.ani.event_source.start()
                except:
                    #create thread for graphing - avoiding laggy interface with threading
                    print('creating process for graph...')
                    self.graph_thread = threading.Thread(target=self.animation_thread)
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


#--------------------------------------------CREATING THE 'SETTINGS' TAB --------------------------------------------
    def create_calib_tab(self):
        self.settings_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.settings_tab, text='Calibrate')

        Helvetica_11_bold = tkFont.Font(family='Helvetica', size=11, weight='bold')

        canvas = tk.Canvas(self.settings_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        self.settings_info_label = tk.Label(canvas, text='< testing >', font=Helvetica_11_bold, justify='center', relief='groove')
        self.settings_info_label.place(anchor='n', relx=0.7, rely=0.02, relwidth=0.5, relheight=0.7)

        self.gyro_calibration_button = tk.Button(canvas, text='Start Gyro\nCalibration', font=Helvetica_11_bold, bg=self.colors["light grey"],
            relief='groove', command=self.gyro_calibration_button_func)
        self.gyro_calibration_button.bind('<Enter>', lambda event, x=self.gyro_calibration_button : self.on_hover(x))
        self.gyro_calibration_button.bind('<Leave>', lambda event, x=self.gyro_calibration_button : self.on_hover_leave(x))
        self.gyro_calibration_button.place(anchor='n', relx=0.25, rely=0.05, relwidth=0.31, relheight=0.1)

        self.magnetometer_calibration_button = tk.Button(canvas, text='Start Magnetometer\nCalibration', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=self.magnetometer_calibration_button_func)
        self.magnetometer_calibration_button.bind('<Enter>', lambda event, x=self.magnetometer_calibration_button : self.on_hover(x))
        self.magnetometer_calibration_button.bind('<Leave>', lambda event, x=self.magnetometer_calibration_button : self.on_hover_leave(x))
        self.magnetometer_calibration_button.place(anchor='n', relx=0.25, rely=0.2, relwidth=0.31, relheight=0.1)

        self.format_button = tk.Button(canvas, text='Start Formatting\nSD Card', font=Helvetica_11_bold,
            bg=self.colors["light grey"], relief='groove', command=self.format_button_func)
        self.format_button.bind('<Enter>', lambda event, x=self.format_button : self.on_hover(x))
        self.format_button.bind('<Leave>', lambda event, x=self.format_button : self.on_hover_leave(x))
        self.format_button.place(anchor='n', relx=0.25, rely=0.35, relwidth=0.31, relheight=0.1)

        self.get_logs_but = tk.Button(canvas, text='Access Log\nFiles', font=Helvetica_11_bold, bg=self.colors["light grey"], relief='groove')
        self.get_logs_but.configure(command=self.get_logs_but_func)
        self.get_logs_but.bind('<Enter>', lambda event, x=self.get_logs_but : self.on_hover(x))
        self.get_logs_but.bind('<Leave>', lambda event, x=self.get_logs_but : self.on_hover_leave(x))
        self.get_logs_but.place(anchor='n', relx=0.25, rely=0.5, relwidth=0.31, relheight=0.1)
        self.nw = None


    def get_logs_but_func(self):
        if self.nw is not None: return None
        if not self.s.connected:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')    
            return None
        self.s.serialFlush()
        self.s.send("getlist")
        list = self.s.read_all().split("\n")
        list = [x for x in list if x not in ["\n", ""]]
        print(f"LOGS:\n{list}")
        self.nw = Toplevel(self)
        self.nw.geometry("500x600")
        self.nw.minsize(500,600)
        self.nw.title("--Saved Log Files--")
        self.nw.protocol("WM_DELETE_WINDOW", self.nw_exit)
        self.fname_select = tk.StringVar(self.nw, "1")
        self.files = {key:val for (key,val) in zip([i for i in range(1,len(list)+1)], list)}
        row, col = 0, 0
        for (val, fname) in self.files.items():
            if (row+1) % 21 == 0:
                col += 1
                row = 0
            print(row, col)
            rb = tk.Radiobutton(self.nw, text=f'{fname}', variable=self.fname_select, value=val)
            rb.place(anchor='n', relx=(0.14+col*0.25), rely=(0.01+0.047*row), relwidth=0.25, relheight=0.05)
            row += 1
        self.dlbut = tk.Button(self.nw, text='Download', bg=self.colors["light grey"], relief='groove')
        self.dlbut.configure(command=self.downloadfile)
        self.dlbut.bind('<Enter>', lambda event, x=self.dlbut : self.on_hover(x))
        self.dlbut.bind('<Leave>', lambda event, x=self.dlbut : self.on_hover_leave(x))
        self.dlbut.place(anchor='n', relx=0.35, rely=0.95, relwidth=0.3, relheight=0.05)

        self.dlallbut = tk.Button(self.nw, text='Download ALL', bg=self.colors["light grey"], relief='groove')
        self.dlallbut.configure(command=self.downloadall)
        self.dlallbut.bind('<Enter>', lambda event, x=self.dlallbut : self.on_hover(x))
        self.dlallbut.bind('<Leave>', lambda event, x=self.dlallbut : self.on_hover_leave(x))
        self.dlallbut.place(anchor='n', relx=0.65, rely=0.95, relwidth=0.3, relheight=0.05)


    def downloadfile(self):
        if self.s.connected:
            fname = self.files[int(self.fname_select.get())]
            path = f"/logs/{fname}"
            print(f"Download: {path}")
            self.s.send(f"getfile {path}")
            try:
                dat = f"bytes: {self.s.read_all()}"
                with open(f"downloaded_logs\{fname}", 'w') as f:
                    f.write(dat)
                tk.messagebox.showinfo(title='Success', message='Download successful!\nFile is in /downloaded_logs.')    
            except Exception as e:
                tk.messagebox.showinfo(title='Error', message=f'Error: {e}')    
        else:
            print('Connection Error')


    def downloadall(self):
        if self.s.connected:
            for fname in self.files.values():
                path = f"/logs/{fname}"
                print(f"Download: {path}")
                self.s.send(f"getfile {path}")
                try:
                    dat = f"bytes: {self.s.read_all()}"
                    with open(f"downloaded_logs\{fname}", 'w') as f:
                        f.write(dat)
                except Exception as e:
                    tk.messagebox.showinfo(title='Error', message=f'Error: {e}')    
            tk.messagebox.showinfo(title='Success', message='Downloads successful!\nFiles are in downloaded_logs folder.')    
        else:
            print('Connection Error')


    def nw_exit(self):
        self.nw.destroy()
        self.nw = None


    def gyro_calibration_button_func(self):
        if self.s.connected:
            confirm = tk.messagebox.askquestion(title='WARNING', message='You are about to calibrate the gyro sensor.\nAre you sure?')
            if confirm == 'yes':
                self.s.send('acccal')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')    
    

    def magnetometer_calibration_button_func(self):
        if self.s.connected:
            confirm = tk.messagebox.askquestion(title='WARNING', message='You are about to calibrate the magnetometer sensor.\nAre you sure?')
            if confirm == 'yes':
                self.s.send('magcal')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')  
    

    def format_button_func(self):
        if self.s.connected:
            confirm = tk.messagebox.askquestion(title='WARNING', message='You are about to format the SD card.\nAre you sure?')
            if confirm == 'yes':
                self.s.send('format')
        else:
            tk.messagebox.showinfo(title='Error', message='You are not connected to a serial port.')  


    #--------------------------------------------CREATING THE 'ABOUT' TAB COMPANY AND CREATOR INFORMATION--------------------------------------------
    def create_about_tab(self):
        self.about_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.about_tab, text='About')

        Helvetica_11 = tkFont.Font(family='Helvetica', size=11)
        Helvetica_12 = tkFont.Font(family='Helvetica', size=12)

        canvas = tk.Canvas(self.about_tab, width=self.WIDTH, height=self.HEIGHT, bg=self.colors["white"], relief='groove')
        canvas.place(anchor='n', relx=0.5, rely=0, relwidth=1, relheight=1)

        image = Image.open('files\pictures-icon\invibit_logo.png')
        image = image.resize((250, 90), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(image)
        canvas.create_image(self.WIDTH/2, 30, anchor='n', image=image) 
        canvas.image = image

        # Text(master, height=1, borderwidth=0)

        self.url = tk.Text(canvas, height=1, font=Helvetica_12, bg=self.colors["white"], borderwidth=0, cursor="hand2")
        self.url.bind('<Button-1>', lambda event, x=self.url: self.open_link(x))
        self.url.insert('1.0', 'https://www.invibit.com/')
        self.url.configure(state='disabled')
        self.url.place(anchor='n', relx=0.5, rely=0.3, relwidth=0.35, relheight=0.05)

        contact_info_text = "phone: (+30) 210 4212380\nmail: info@invibit.com"

        self.contact_info_label = tk.Text(canvas, height=1, font=Helvetica_11, borderwidth=0, bg=self.colors["white"])
        self.contact_info_label.insert('1.0', contact_info_text)
        self.contact_info_label.configure(state='disabled')
        self.contact_info_label.place(anchor='n', relx=0.5, rely=0.38, relwidth=0.36, relheight=0.1)

        # Firmware version at the bottom of the page
        self.firmware_version_label = tk.Label(canvas, text='version : (connect to view firmware version)', bg=self.colors["white"], font=self.font +'11')
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


    #/////////////////////////////////////////////////////////////////////////////////
    # ///////////////////////////////// THREADING ////////////////////////////////////
    #/////////////////////////////////////////////////////////////////////////////////

    #function creating a thread continuously reading data from the serial port
    def read_serial_thread(self):
        if not self.reading_thread:
            self.read_serial_t = threading.Thread(target=self.read_serial_loop)
            self.read_serial_t.daemon = True
            self.read_serial_t.start()
        else:
            print("cant open thread when it is already in use")



    #function checking connection state and using serialComms module to receive data
    def read_serial_loop(self):
        while self.s.connected and self.current_tab in [1, 2]:
            self.s.recv(collect=True)
            time.sleep(0.0001)
            self.reading_thread = True
        self.reading_thread = False
        print("EXITING READ SERIAL THREAD")


    def wait_for_thread_to_close(self):
        while self.reading_thread == True:
            time.sleep(0.0005)
            print('waiting for thread to close...')


    # function updating the gui when 'monitor' tab is currently open
    def monitor_thread_loop(self):
        while self.s.connected and self.current_tab == 1:
            time.sleep(0.1)
            try:             
                dat, _ = self.s.return_graph_data()
                values = [item[len(item)-1] for item in dat]    
                for idx, (widget, value) in enumerate(zip(self.monitor_values, values)):
                    if idx == 4:
                        if self.monitor_buttons[idx]["toggle-state"] == "Abs":
                            widget["widget"]["text"] = str(round(-value, 2))
                        elif self.monitor_buttons[idx]["toggle-state"] == "Rel":
                            widget["widget"]["text"] = str(round( (-value - widget["zero-rel-val"]), 2))
                        continue
                    if self.monitor_buttons[idx]["toggle-state"] == "Abs":
                        widget["widget"]["text"] = str(round(value, 2))
                    elif self.monitor_buttons[idx]["toggle-state"] == "Rel":
                        widget["widget"]["text"] = str(round(value - widget["zero-rel-val"], 2))
            except Exception as e:
                print(f'error on update_monitor_gui: {e}')
        print("EXITING MONITOR THREAD...")


    # function updating the gui when 'graph' tab is currently open
    def update_graph_gui(self, i): 
        self.ax.clear()
        try:
            # either plot or read serial, not both at the same time / avoid crashes
            while self.s.is_reading_serial == True:
                time.sleep(0.001)
            dat, t_count_arr = self.s.return_graph_data()
            t_count_arr = list(t_count_arr)
            # plot the values
            for i, item in enumerate(dat):
                self.ax.plot(t_count_arr, item, self.monitor_values[i]["color"])
            self.ax.grid()
        except Exception as e:
            print(f'update_graph_gui exception : {e}')
 
    #/////////////////////////////////////////////////////////////////////////////////
    #////////////////////////////////// THREADING ////////////////////////////////////
    #/////////////////////////////////////////////////////////////////////////////////


    def on_tab_switch(self, event):
        try:
            self.current_tab = self.tab_parent.index(self.tab_parent.select())
            if self.current_tab != 2:
                if self.start_graph_button['text'] == "Stop Graph":
                    self.start_graph_button_func()
            # arriving in an updating tab, coming from a non updating one > request data
            if self.current_tab in [1, 2] and self.previous_tab not in [1, 2]:
                pass
            # arriving on non updating-static tab
            elif self.current_tab in [0, 3, 4]:
                self.wait_for_thread_to_close()
                if self.current_tab == 0:
                    self.update_tuning_values()

            self.previous_tab = self.current_tab
            self.handle_tabs()
            # update previous tab to current tab on tab switch
        except Exception as e:
            print(f"TAB_SWITCH ERROR: {e}")



    #/////////////////////////////////////////////////////////////////////////////////
    # ////////////////////////////// CONFIG READ-WRITE ///////////////////////////////
    #/////////////////////////////////////////////////////////////////////////////////


    # write to the config file 
    # save the com port / baud rate last used inside the application
    # in order to retrieve them when re-opening the app
    def write_to_config(self):
        with open('files\config.txt', 'r+') as file:
            lines = [x.strip() for x in file.readlines()]
            file.seek(0)
            for line in lines:
                if "GRAPH_DISPLAY_LAST_X_SECONDS" in line:
                    file.write(line + '\n')
            file.truncate()
            concat = ["DEFAULT_COM=", self.com_port_var.get(), "\nDEFAULT_BAUD=", str(self.baud_rate_var.get()), "\nDEFAULT_SERVO_SPEED=", str(self.servo_speed_scale.get()), '\n']
            x = ["/ZERO_ROLL=", "/ZERO_PITCH=", "/ZERO_YAW=", "/ZERO_VANE=", "/ZERO_WING="]
            for i in range(5):
                concat += [self.monitor_buttons[i]["toggle-state"].upper(), x[i], str(self.monitor_values[i]["zero-rel-val"]), "\n"]

            save = ''.join(concat)
            print("save:\n" + save)
            file.write(save)


    # ********** jesus christ re-write this
    def read_last_config(self):   
        with open('files\config.txt', 'r') as file:
            lines = [x.strip() for x in file.readlines()]
            for line in lines:
                if "DEFAULT_COM" in line:
                    self.default_com = line.split("=")[1].strip() #line.replace("DEFAULT_COM", '').replace(' ', '').replace('=', '')
                elif "DEFAULT_BAUD" in line:
                    self.default_baud = int(line.split("=")[1].strip()) #line.replace("DEFAULT_BAUD", '').replace(' ', '').replace('=', '')
            
                elif "GRAPH_DISPLAY_LAST_X_SECONDS" in line:
                    self.x_limit = 10 * float(line.split("=")[1].strip())
                elif "DEFAULT_SERVO_SPEED" in line:
                    self.default_servo_speed = int(line.split("=")[1].strip())
                elif "ZERO" in line:
                    print(line)
                    val = float(line.split('/')[1].split('=')[1])
                    abs_rel_state = 'Abs' if 'ABS' in line.split('/')[0] else 'Rel'

                    d = {"ROLL": 0, "PITCH": 1, "YAW": 2, "VANE": 3, "WING": 4}
                    for idx, name in enumerate(d.keys()):
                        if name in line:
                            self.monitor_buttons[idx]["toggle-state"] = abs_rel_state
                            self.monitor_values[idx]["zero-rel-val"] = val


    #/////////////////////////////////////////////////////////////////////////////////
    # ////////////////////////////// CONFIG READ-WRITE ///////////////////////////////
    #/////////////////////////////////////////////////////////////////////////////////



    # run upon exiting the app - handle serial connection
    # run the write_to_config function to save
    def exit(self):
        self.cleanup_serial()
        self.write_to_config()
        self.quit()
        self.destroy()


#-------------------------MAIN - RUN APP-------------------------
if __name__ == '__main__':
    app = Application()
    app.resizable(False, False)
    app.protocol("WM_DELETE_WINDOW", app.exit)
    app.mainloop()