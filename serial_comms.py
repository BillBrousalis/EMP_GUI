
#------------------------------------------IMPORTS------------------------------------------
import time
import serial
import json
from collections import deque
from datetime import datetime
import timeit

#------------------------------------------CREATING SERIAL CLASS------------------------------------------
class SerialClass():
    #------------------------------------------generic variables------------------------------------------
    baud_rate_list = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 76800, 115200]
    available_ports_list = []
    
    default_com = 'COM16'
    default_baud = 115200
    
    default_servo_speed = 50

    x_limit = 50    # seconds to display in the X axis
    
    configFile = "files\\config.txt"


    #------------------------------------------INITIALIZING------------------------------------------
    def __init__(self):
        super().__init__()
        self.connect_state = "Not Connected"
        self.COM = self.default_com
        self.BAUD = self.default_baud
        #since app opens with a non-quaternion tab as its first tab, we have quat set to false by default
        self.quat = False

        self.write_batch_size = 10
        self.logging = False
        
        self.time_start = time.time()

        self.csv_data_batch = deque()

        self.abs_rel_toggle_states = ['' for _ in range(5)]
        self.rel_zero_values_list = [0 for _ in range(5)]
        self.read_last_config()

        self.t_count = 0
        #self.t_count_array = []
        self.data = deque()
        self.t_count_array = deque()
        self.number_of_graph_values = 5
        self.graph_data = [[] for i in range(self.number_of_graph_values)]
        self.is_reading_serial = False





    # read the config file to retrieve data for the last com port / baud rate used
    def read_last_config(self):   
        with open(self.configFile, 'r') as file:
            lines = file.readlines()
            lines = [line.replace('\n', '') for line in lines]
            for line in lines:
                if "DEFAULT_COM" in line:
                    self.default_com = line.replace("DEFAULT_COM", '').replace(' ', '').replace('=', '')
                elif "DEFAULT_BAUD" in line:
                    self.default_baud = line.replace("DEFAULT_BAUD", '').replace(' ', '').replace('=', '')
                    self.default_baud = int(self.default_baud)
            
                elif "GRAPH_DISPLAY_LAST_X_SECONDS" in line:
                    tmp = line.replace("GRAPH_DISPLAY_LAST_X_SECONDS", '').replace(' ', '').replace('=', '')
                    tmp = float(tmp)
                    self.x_limit = tmp * 10
                elif "DEFAULT_SERVO_SPEED" in line:
                    self.default_servo_speed = line.replace("DEFAULT_SERVO_SPEED", "").replace(' ', '').replace('=', '')
                    self.default_servo_speed = int(self.default_servo_speed)
                elif "ZERO" in line:
                    val = float(line.split('/')[1].split('=')[1])
                    abs_rel_state = 'Abs' if 'ABS' in line.split('/')[0] else 'Rel'
                    if "ROLL" in line:
                        self.abs_rel_toggle_states[0] = abs_rel_state
                        self.rel_zero_values_list[0] = val
                    elif "PITCH" in line:
                        self.abs_rel_toggle_states[1] = abs_rel_state
                        self.rel_zero_values_list[1] = val
                    elif "YAW" in line:
                        self.abs_rel_toggle_states[2] = abs_rel_state
                        self.rel_zero_values_list[2] = val
                    elif "VANE" in line:
                        self.abs_rel_toggle_states[3] = abs_rel_state
                        self.rel_zero_values_list[3] = val
                    elif "WING" in line:
                        self.abs_rel_toggle_states[4] = abs_rel_state
                        self.rel_zero_values_list[4] = val
            




    # handle the connect function of the serial connection
    # keep track and change the connection state
    def connect_func(self):
        if self.connect_state == "Not Connected":
            #print("COM PORT IS : ", self.COM)
            #print("BAUD RATE IS : ", self.BAUD)
            try:
                self.ser = serial.Serial(self.COM, self.BAUD, timeout=2)
                self.ser.flush()
                self.connect_state = "Connected"
                #self.get_firmware_version()
                print("Connected to", self.COM, "successfully!")
            except Exception as e:
                print("Error connecting to port ", self.COM, " ... ", e)
                self.connect_state = "Not Connected"
        elif self.connect_state == "Connected":
            self.ser.close()
            print("Closing serial connection with port", self.COM)
            self.connect_state = "Not Connected"


        

    # used to send data through the serial port
    def send_data(self, to_send):
        if self.connect_state == "Connected" and self.ser != None:
            try:
                self.ser.write(to_send.encode())
                print(f"SENDING... : '{to_send}'")     
            except:
                print('error sending...')
                
        else:
            print("Connect to a serial port first...")



    # read data available to the serial port
    def receive_data(self): 
        if self.ser != None and self.connect_state == "Connected":
            try:
                self.is_reading_serial = True
                self.received = self.ser.readline().decode()
                self.received = json.loads(self.received)
                if self.quat == False:
                    self.collect_data()
                else:
                    # check that we are not getting dump1 data
                    if "offs" not in self.received:
                        self.is_reading_serial = False
                        return self.received
                    else:
                        print(f'faulty json received... <receive_data> : {self.received}')
            except Exception as e:
                print(f"receive_data error : {e}")
                

    # if quat is false, collect data in an organized matter for 
    # use in the 'monitor' tab as well as the graph
    def collect_data(self):
            if self.t_count >= 100:
                self.t_count = 0

            self.t_count += 0.1
            
            if len(self.data) >= self.x_limit:
                self.data.popleft()
                self.t_count_array.popleft()
            
            self.data.append(self.received["md8"])
            self.t_count_array.append(self.t_count)

            item = self.data[-1]
            
            if item != None:
                for index, value in enumerate(item):
                    if len(self.graph_data[index]) >= self.x_limit:
                        self.graph_data[index].pop(0)
                    self.graph_data[index].append(value)
            
            '''
            if self.logging:
                csv_data = ','.join([str(val) for val in item])
                self.csv_data_batch.append(csv_data)
                if len(self.csv_data_batch) >= self.write_batch_size:
                    self.write_to_csv()
                    self.csv_data_batch.clear()
            '''

            self.is_reading_serial = False

            """
            # timing loop
            time_end = time.time()
            print(f'loop time : {time_end - self.time_start}')
            self.time_start = time_end
            """




    def toggle_logging(self, state):
        if self.connect_state == 'Connected':
            if state == 'on':
                self.send_data("recstart\n")
            else:
                self.send_data("recstop\n")
    '''
                self.logging = True
                # open csv file to prepare data writing
                timestamp = datetime.now()
                title_timestamp = timestamp.strftime("%d-%m-%Y--%H-%M-%S")
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                csv_start = f'~~~{timestamp}~~~\nRoll, Pitch, Yaw, Vane, Wing :'
                self.csv_logging = open(f'value_logging\\logging({title_timestamp}).csv', 'w+')
                self.csv_logging.write(f'{csv_start}')
            
            elif state == 'off':
                self.close_csv()
                self.logging = False
    '''



    # flush the serial
    def serialFlush(self):
        self.ser.flush()

    # return the graph data collected
    def return_graph_data(self):
        return self.graph_data
    
    def return_t_count_array(self):
        return self.t_count_array

    def return_default_servo_speed(self):
        return self.default_servo_speed





    # clear data collected
    def clear_data(self):
        self.t_count = 0
        self.t_count_array.clear() 
        self.graph_data = [[] for i in range(self.number_of_graph_values)]
        self.data.clear()




    # check for avaiable ports
    def refresh_ports(self):
        self.available_ports_list.clear()
        for i in range(1,32):
            com_str = 'COM'+str(i)
            try:
                s = serial.Serial(com_str)
                self.available_ports_list.append('COM'+str(i))
                s.close()
            except:
                pass
        if len(self.available_ports_list) == 0:
            self.available_ports_list.append('---')
        print("available ports:", self.available_ports_list)





    def receive_dump(self):
        if self.connect_state == "Connected":
            dump = ''
            while dump == '':
                self.send_data("dump1\n")
                dump = self.ser.readline().decode()
                try:
                    dump = json.loads(dump)
                except:
                    dump = ''
                    print('not valid json in receive dump...')
                    time.sleep(0.05)
                
                if 'offs' in dump:
                    return dump
                else:
                    dump = ''


    def write_to_csv(self):
        to_write = '\n' + '\n'.join(self.csv_data_batch)
        self.csv_logging.write(to_write)


    def close_csv(self):
        if self.logging:
            self.csv_logging.close()



    # get current firmware version
    def get_firmware_version(self):
        try:
            if self.connect_state == "Connected":
                self.send_data('vers\n')
                time.sleep(0.05)
                self.serialFlush()
                version = self.ser.read_all().decode()
                print(f'version = {version}')
                if 'version' in version:
                    version = json.loads(version)
                    return version['version']
                else:
                    while 'version' not in version:
                        print('retrying to get correct firmware version')
                        version = self.ser.readline().decode()
                        time.sleep(0.001)
                    version = json.loads(version)
            else:
                return '*error in getting firmware version*'
        except Exception as e:
            print(f"get_firmware_version error : {e}")



# create ser object to be used both by the mainGUI as well as the 3D graphics module
ser = SerialClass()