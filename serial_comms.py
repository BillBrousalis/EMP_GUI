#------------------------------------------IMPORTS------------------------------------------
import time
import serial
import json
from collections import deque
from datetime import datetime

#------------------------------------------CREATING SERIAL CLASS------------------------------------------
class SerialClass():
    #------------------------------------------generic variables------------------------------------------
    default_servo_speed = 50
    x_limit = 50    # seconds to display in the X axis
    
    #------------------------------------------INITIALIZING------------------------------------------
    def __init__(self, com=None, baud=None):
        super().__init__()
        self.connected = False
        self.baud_rate_list = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 76800, 115200]
        if com is None:
            self.COM = 'COM16'
        if baud is None:
            self.BAUD = self.baud_rate_list[-1]

        self.time_start = time.time()

        self.csv_data_batch = deque()

        self.abs_rel_toggle_states = ['' for _ in range(5)]
        self.rel_zero_values_list = [0 for _ in range(5)]

        self.t_count = 0
        self.data = deque()
        self.t_count_array = deque()
        self.number_of_graph_values = 5
        self.graph_data = [[] for i in range(5)]
        self.is_reading_serial = False


    def set(self, com=None, baud=None):
        if com is not None:
            self.COM = com
        if baud is not None:
            self.BAUD = baud


    # handle the connect function of the serial connection
    # keep track and change the connection state
    def connect(self):
        if self.connected == False:
            try:
                self.ser = serial.Serial(self.COM, self.BAUD, timeout=2)
                self.ser.flush()
                self.connected = True
                print(f"Connected to {self.COM} successfully!")
            except Exception as e:
                print(f"Error connecting to port {self.COM} ... {e}")
        else:
            self.ser.close()
            self.connected = False
            print("Closing serial connection with port", self.COM)

    def disconnect(self):
        if self.connected:
            self.ser.close()
            self.connected = False
        else:
            print('not connected (disconnect func)')

        

    # used to send data through the serial port
    def send(self, dat, LF=True):
        if self.connected:
            if LF: 
                dat = f'{dat}\n'
            try:
                self.ser.write(dat.encode())
                print(f"SENDING... : '{dat}'")     
            except:
                print('error sending...')
        else:
            print("Connect to a serial port first...")



    def recv(self, isjson=True, collect=False):
        if self.connected:
            try:
                rec = self.ser.readline().decode()
                if isjson:
                    rec = json.loads(rec)
                if collect:
                    self.collect_data(rec)
                return rec
            except Exception as e:
                print(f'error in receive {e}')
        else:
            print('Not connected')

       

    '''
    # read data available to the serial port
    def receive(self): 
        if self.connected == True and self.ser != None:
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
    '''
                

    # if quat is false, collect data in an organized matter for 
    # use in the 'monitor' tab as well as the graph
    def collect_data(self, dat):
        if self.t_count >= 100:
            self.t_count = 0

        self.t_count += 0.1
        
        if len(self.data) >= self.x_limit:
            self.data.popleft()
            self.t_count_array.popleft()
         
        self.data.append(dat["md8"])
        self.t_count_array.append(self.t_count)

        item = self.data[-1]
        
        if item != None:
            for index, value in enumerate(item):
                if len(self.graph_data[index]) >= self.x_limit:
                    self.graph_data[index].pop(0)
                self.graph_data[index].append(value)
        self.is_reading_serial = False




    def toggle_record(self, state):
        if self.connected == True:
            if state == 'on':
                self.send("recstart")
            else:
                self.send("recstop")
    
             


    # flush the serial
    def serialFlush(self):
        if self.ser is not None:
            self.ser.flush()
            self.ser.reset_output_buffer()

    # return the graph data collected
    def return_graph_data(self):
        return (self.graph_data, self.t_count_array)
    
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
    def get_ports(self):
        avail_ports = []
        for i in range(1,32):
            com = f'COM{i}'
            try:
                s = serial.Serial(com)
                avail_ports.append(com)
                s.close()
            except:
                pass
        if len(avail_ports) == 0:
            avail_ports.append('---')
        return avail_ports


    def get_dump(self):
        if self.connected:
            while True:
                self.send("dump1")
                dump = self.recv(isjson=False)
                try:
                    dump = json.loads(dump)
                except:
                    print('not valid json in receive dump...')
                    time.sleep(0.05)
                if 'offs' in dump:
                    return dump


    # fix this shit
    def get_firmware_version(self):
        if self.connected:
            try:
                self.send('vers')
                time.sleep(0.05)
                self.serialFlush()
                version = self.ser.read_all().decode()
                print(f'version = {version}')
                if 'version' in version:
                    version = json.loads(version)
                    return version["version"]
                else:
                    while 'version' not in version:
                        print('retrying to get correct firmware version')
                        version = self.ser.readline().decode()
                        time.sleep(0.001)
                    version = json.loads(version)
                    return version["version"]
            except Exception as e:
                print(f"get_firmware_version error : {e}")
        else:
            return '*error in getting firmware version*'
