import time
import os
class BrailleGCodeGenerator:
    def __init__(self):
        # Define braille dimensions
        self.BRAILLE = {
            "marginWidth": 3,
            "marginHeight": 5,
            "paperWidth": 180,
            "paperHeight": 260,
            "letterWidth": 2.5,
            "dotRadius": 1.2,
            "letterPadding": 3.7,
            "linePadding": 3,
            "headDownPosition": -2.0,
            "headUpPosition": 10,
            "speed": 5000,
            "delta": False,
            "goToZero": True,
            "invertX": True,
            "invertY": True,
            "mirrorX": False,
            "mirrorY": True,
            "language": "6 dots",
            "GCODEup": 'M3 S1',
            "GCODEdown": 'M3 S0',
            "usedotgrid": False
        }

        # Define dot map for different languages
        self.LANGUAGES = {
            "6 dots": 
                {
                "latinToBraille": {
                    "a": [1],
		            "b": [1,2],
		            "c": [1,4],
		            "d": [1,4,5],
		            "e": [1,5],
		            "f": [1,2,4],
		            "g": [1,2,4,5],
		            "h": [1,2,5],
		            "i": [2,4],
		            "j": [2,4,5],
		            "k": [1,3],
		            "l": [1,2,3],
		            "m": [1,3,4],
		            "n": [1,3,4,5],
		            "o": [1,3,5],
		            "p": [1,2,3,4],
		            "q": [1,2,3,4,5],
		            "r": [1,2,3,5],
		            "s": [2,3,4],
		            "t": [2,3,4,5],
		            "u": [1,3,6],
		            "v": [1,2,3,6],
		            "w": [2,4,5,6],
		            "x": [1,3,4,6],
		            "y": [1,3,4,5,6],
		            "z": [1,3,5,6],
		            " ": [],
		            ".": [2,5,6],
		            ",": [2],
		            "?": [2,6],
		            ";": [2,3],
		            ":": [2,4],
		            "!": [2,3,5],
		            "(": [2,3,6],
		            ")": [3,5,6],
		            "'": [3],
		            "-": [3,6],
		            "/": [3,4],
		            "*": [3,5],
		            "+": [2,3,5],
		            "=": [2,3,5,6],
		            "0": [3, 4, 5, 6],
		            "1": [1, 6],
		            "2": [1, 2, 6],
		            "3": [1, 4, 6],
		            "4": [1, 4, 5, 6],
		            "5": [1, 5, 6],
		            "6": [1, 2, 4, 6],
		            "7": [1, 2, 4, 5, 6],
		            "8": [1, 2, 5, 6],
		            "9": [2, 4, 6]
                },
                "dotMap": [[1, 2, 3], [4, 5, 6]],
                "numberPrefix": [3, 4, 5, 6]
            }
        }

        self.GCODEdotposition = []
        self.GCODEsvgdotposition = []
        self.xhead = 0
        self.yhead = 0
        self.generated_gcode = "" 

    def replace_at(self, s, n, t):
        return s[:n] + t + s[n+1:]

    def dot_position(self, x, y):
        return {"x": x, "y": y}

    def gcode_set_absolute_positioning(self):
        return "G90;\r\n"

    def gcode_motor_off(self):
        return "M84;\r\n"

    def gcode_home(self):
        return "G28 X;\r\n" + "G28 Y;\r\n"

    def gcode_reset_position(self, X, Y):
        return f"G92 X{X:.2f} Y{Y:.2f};\r\n"

    def gcode_set_speed(self, speed):
        return f"G1 F{speed};\r\n"

    def gcode_position(self, X, Y):
        code = ""
        has_values = False
        if X is not None:
            code += f" X{X:.2f}"
            has_values = True
        if Y is not None:
            code += f" Y{Y:.2f}"
            has_values = True
        if has_values:
            code += ";\r\n"
        return code

    def gcode_go_to(self, X, Y):
        return "G0" + self.gcode_position(X, Y)

    def gcode_move_to(self, X, Y, Z=None):
        code = "G1"
        code += self.gcode_position(X, Y)
        if Z is not None:
            code += f" Z{Z:.2f}"
        code += "\r"
        return code

    def gcode_move_to_cached(self, X=None, Y=None, comment=None):
        if X is not None:
            self.xhead = X
        if Y is not None:
            self.yhead = Y
        if comment is not None:
            code = f"G1 X{self.xhead:.2f} Y{self.yhead:.2f}; {comment}\r\n"
        else:
            code = f"G1 X{self.xhead:.2f} Y{self.yhead:.2f}\r\n"
        return code

    
    def gcode_print_dot(self):
        return f"{self.BRAILLE['GCODEdown']};\r\n{self.BRAILLE['GCODEup']};\r\n"

    def gcode_print_dot_cached(self):
        if self.xhead is not None and self.yhead is not None:
            self.GCODEdotposition.append(self.dot_position(self.xhead, self.yhead))
        return self.gcode_print_dot()

    def gcode_sort_zigzag(self, positions):
        sorted_positions = []
        s = 0
        e = 0
        direction = 1

        while e < len(positions):
            while e < len(positions) and positions[s]["y"] == positions[e]["y"]:
                e += 1

            tmp = positions[s:e]
            tmp.sort(key=lambda p: (p["y"], (p["x"] - p["x"]) * direction))
            sorted_positions.extend(tmp)
            direction *= -1
            s = e

        return sorted_positions

    def build_optimized_gcode(self):
        sorted_positions = self.gcode_sort_zigzag(self.GCODEdotposition)

        code_str = self.gcode_home()
        code_str += self.gcode_set_speed(self.BRAILLE["speed"])

        if self.BRAILLE["goToZero"]:
            code_str += self.gcode_move_to(0, 0)

        for position in sorted_positions:
            code_str += self.gcode_move_to_cached(position["x"], position["y"])
            code_str += self.gcode_print_dot_cached()

        code_str += self.gcode_move_to(0, 0)
        code_str += self.gcode_motor_off()
        return code_str

    def braille_to_gcode(self, text):
        self.GCODEdotposition = []
        self.GCODEsvgdotposition = []
        self.xhead = 0
        self.yhead = 0

        is_8dot = "8 dots" in self.BRAILLE["language"]
        current_x = self.BRAILLE["marginWidth"]
        current_y = self.BRAILLE["marginHeight"]
        letter_width = self.BRAILLE["letterWidth"]

        gcode = self.gcode_set_absolute_positioning()
        gcode += self.gcode_set_speed(self.BRAILLE["speed"])
        if self.BRAILLE["goToZero"]:
            gcode += self.gcode_move_to(0, 0, 0)
        gcode += self.gcode_move_to(0, 0, self.BRAILLE["headUpPosition"])

        is_writing_number = False
        is_special_char = False
        text_copy = list(text)

        for i, char in enumerate(text_copy):
            char_is_capital_letter = is_8dot and char.isupper()
            char_is_line_break = char in ["\r", "\n"]

            if char_is_line_break:
                current_y += (2 if is_8dot else 3) * letter_width + self.BRAILLE["linePadding"]
                current_x = self.BRAILLE["marginWidth"]

                if current_y > self.BRAILLE["paperHeight"] - self.BRAILLE["marginHeight"]:
                    break
                continue

            if char.lower() not in self.LANGUAGES[self.BRAILLE["language"]]["latinToBraille"]:
                print(f"Character '{char}' was not translated in braille.")
                continue

            indices = self.LANGUAGES[self.BRAILLE["language"]]["latinToBraille"][char.lower()]

            if not is_writing_number and char.isdigit():
                indices = self.LANGUAGES[self.BRAILLE["language"]]["numberPrefix"]
                text_copy[i] = char.lower()
                is_writing_number = True
            elif is_writing_number and char == " ":
                is_writing_number = False
            elif char_is_capital_letter:
                indices = self.LANGUAGES[self.BRAILLE["language"]]["numberPrefix"]
                text_copy[i] = char.lower()
            elif not is_special_char and self.get_prefix_for_special_character(char):
                indices = self.get_prefix_for_special_character(char)
                text_copy[i] = char.lower()
                is_special_char = True

            gx = self.BRAILLE["paperWidth"] - current_x if self.BRAILLE["invertX"] else current_x
            gy = -current_y

            if self.BRAILLE["delta"]:
                gx -= self.BRAILLE["paperWidth"] / 2
                gy += self.BRAILLE["paperHeight"] / 2
            elif not self.BRAILLE["invertY"]:
                gy += self.BRAILLE["paperHeight"]

            gcode += self.gcode_move_to_cached(self.BRAILLE["mirrorX"] and -gx or gx, self.BRAILLE["mirrorY"] and -gy or gy, None)

            for y in range(4 if is_8dot else 3):
                for x in range(2):
                    if x + y * 2 + 1 in indices:
                        # px = current_x + x * letter_width
                        # py = current_y + y * letter_width
                        # gx = self.BRAILLE["paperWidth"] - px if self.BRAILLE["invertX"] else px
                        # gy = -py
                        gx = self.BRAILLE["paperWidth"] - current_x if self.BRAILLE["invertX"] else current_x
                        gy = -current_y

                        if self.BRAILLE["delta"]:
                            gx -= self.BRAILLE["paperWidth"] / 2
                            gy += self.BRAILLE["paperHeight"] / 2
                        elif not self.BRAILLE["invertY"]:
                            gy += self.BRAILLE["paperHeight"]

                        gcode += self.gcode_move_to_cached(self.BRAILLE["mirrorX"] and -gx or gx, self.BRAILLE["mirrorY"] and -gy or gy, None)
                        gcode += self.gcode_print_dot_cached()

            current_x += self.BRAILLE["letterWidth"] + self.BRAILLE["letterPadding"]

            if current_x + self.BRAILLE["letterWidth"] + self.BRAILLE["dotRadius"] > self.BRAILLE["paperWidth"] - self.BRAILLE["marginWidth"]:
                current_y += (2 if is_8dot else 3) * letter_width + self.BRAILLE["linePadding"]
                current_x = self.BRAILLE["marginWidth"]

            if current_y > self.BRAILLE["paperHeight"] - self.BRAILLE["marginHeight"]:
                break

        gcode += self.gcode_move_to(0, 0, self.BRAILLE["headUpPosition"])
        if self.BRAILLE["goToZero"]:
            gcode += self.gcode_move_to(0, 0, 0)

        sorted_gcode = self.build_optimized_gcode()
        return sorted_gcode

    def get_prefix_for_special_character(self, char):
        # Implement logic to get prefix for special characters
        return []
    def save_gcode_to_memory(self, gcode):
        self.generated_gcode = gcode
        
    def save_gcode_to_file(self, gcode, directory):
        filename = os.path.join(directory, "newcode.txt")
        with open(filename, "w") as file:
            file.write(gcode)
        print("File saved succesfully")

# Example usage
generator = BrailleGCodeGenerator() 
input_file_path = "voice_input.txt"
with open(input_file_path, "r") as file:
    text = file.read()
gcode = generator.braille_to_gcode(text)
directory = "/home/nappu"
generator.save_gcode_to_memory(gcode)
print(generator.generated_gcode)
generator.save_gcode_to_file(gcode, directory)


#NOW THE BRAILLE GCODE FOR MOTOR########################################################

import RPi.GPIO as GPIO
import time

# Constants

solenoid_state = 0

STEPSPERMM = 100
MMPERSTEP = 1/STEPSPERMM
DIR_A = 20
STEP_A = 21
nENABLE_A = 27
STEP_DELAY = 0.9 # delay

DIR_B = 22
STEP_B = 23
nENABLE_B = 24

SOLENOID_PIN = 16

x_step_pos = 0
y_step_pos = 0

X_MIN = 0
X_MAX = 180

# Pin setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_A, GPIO.OUT)
GPIO.setup(STEP_A, GPIO.OUT)
GPIO.setup(nENABLE_A, GPIO.OUT)

GPIO.setup(DIR_B, GPIO.OUT)
GPIO.setup(STEP_B, GPIO.OUT)
GPIO.setup(nENABLE_B, GPIO.OUT)

GPIO.setup(SOLENOID_PIN, GPIO.OUT)


def EnableMotors():
    GPIO.output(nENABLE_A, GPIO.LOW)
    GPIO.output(nENABLE_B, GPIO.LOW)

def DisableMotors():
    GPIO.output(nENABLE_A, GPIO.HIGH)
    GPIO.output(nENABLE_B, GPIO.HIGH)

# a = 0 move A, a = 1 move B
def OneStep(a, direction):
    if a == 0:
        GPIO.output(DIR_A, direction)
        GPIO.output(STEP_A, GPIO.HIGH)
        time.sleep(STEP_DELAY/1000.0)
        GPIO.output(STEP_A, GPIO.LOW)
    elif a == 1:
        GPIO.output(DIR_B, direction)
        GPIO.output(STEP_B, GPIO.HIGH)
        time.sleep(STEP_DELAY/1000.0)
        GPIO.output(STEP_B, GPIO.LOW)

# To move to (X, Y) we need to calculate dA = dX + dY and dB = dX - dY
def MoveToPosition(x, y):
    global x_step_pos
    global y_step_pos
    global X_MIN, X_MAX

    # Limit the X-coordinate to the defined range
    x = max(X_MIN, min(X_MAX, x))
    y = y/MMPERSTEP

    x_steps_to_do = round(x) - x_step_pos
    y_steps_to_do = round(y) - y_step_pos
    a_steps_to_do = x_steps_to_do + y_steps_to_do
    b_steps_to_do = x_steps_to_do - y_steps_to_do
    x_step_pos = x
    y_step_pos = y
    # Decide on the direction based on the sign of x_steps_to_do
    directionA = 0 if x_steps_to_do >= 0 else 1
    directionB = 0 if x_steps_to_do >= 0 else 1

    # after obtaining the direction we can convert to absolute values for simplicity
    a_steps_to_do = abs(a_steps_to_do)
    b_steps_to_do = abs(b_steps_to_do)
    
    # here we will store the error for the axis with sliced movement
    if a_steps_to_do == b_steps_to_do:
        for i in range(int(a_steps_to_do)):
            OneStep(0, directionA)
            OneStep(1, directionB)
    else:
        sliced_axis_error = 0
        sliced_axis_increment = b_steps_to_do/a_steps_to_do if a_steps_to_do > b_steps_to_do else a_steps_to_do/b_steps_to_do

        if a_steps_to_do > b_steps_to_do:
            for i in range(int(a_steps_to_do)):
                OneStep(0, directionA)
                sliced_axis_error += sliced_axis_increment
                if sliced_axis_error >= 1:
                    OneStep(1, directionB)
                    sliced_axis_error -= 1
        elif a_steps_to_do < b_steps_to_do:
            for i in range(int(b_steps_to_do)):
                OneStep(1, directionB)
                sliced_axis_error += sliced_axis_increment
                if sliced_axis_error >= 1:
                    OneStep(0, directionA)
                    sliced_axis_error -= 1

def StepsDelay():
    time.sleep(STEP_DELAY/1000.0)

def SolenoidWrite(state):
    
    global solenoid_state
    solenoid_state = state
    GPIO.output(SOLENOID_PIN,state)
    print(state)   

def ExecuteGcode(commands):
    global x_step_pos
    global y_step_pos
    global STEP_DELAY
    print(commands)
    if 'F' in commands:
        STEP_DELAY = int(5000 - 5*int(commands['F']))
        if STEP_DELAY <0.9: STEP_DELAY = 0.9
        print("New step delay: " + str(STEP_DELAY))
        
    if 'M' in commands:  # Check for M3 command
        if int(commands['M']) == 3:
            if 'S' in commands:  # Check for S parameter
                if int(commands['S']) == 1 :  # If S parameter is 1, turn on solenoid
                    SolenoidWrite(1)
                    print("Solenoid turned on")
                    time.sleep(0.9)
                elif int(commands['S']) == 0:  # If S parameter is 0, turn off solenoid
                    SolenoidWrite(0)
                    print("Solenoid turned off")
                    time.sleep(0.9)
        if int(commands['M']) == 84:  # If M command is M84
            DisableMotors()  # Turn off the motors
            motors_enabled = False  # Update motor state variable
            print("Motors turned off")
            return  # Exit the function after handling M84
    if 'X' in commands or 'Y' in commands:
        MoveToPosition(float(commands['X']) if 'X' in commands else x_step_pos * MMPERSTEP, float(commands['Y']) if 'Y' in commands else y_step_pos * MMPERSTEP)
    if 'G' in commands:
        if commands['G'] == '28':
            x_step_pos = 0
            y_step_pos = 0
        elif commands['G'] == '29':
            # Emboss the Braille character
            for i in range(10):
                # Turn on the solenoid
                SolenoidWrite(1)
                print("Solenoid turned on")
                time.sleep(0.1)
                # Turn off the solenoid
                SolenoidWrite(0)
                print("Solenoid turned off")
                time.sleep(0.1)
    # if 'M' in commands:  # Check for M commands
    #     if int(commands['M']) == 84:  # If M command is M84
    #         DisableMotors()  # Turn off the motors
    #         motors_enabled = False  # Update motor state variable
    #         print("Motors turned off")
    #         return  # Exit the function after handling M84

def ProcessGcodeString(gcode_string):
    lines = gcode_string.split('\n')
    for line in lines:
        line = line.strip('\n\r')
        line = line.split(';', 1)[0]
        if len(line) > 0:
            gcode = line.split(' ')
            commands = {}
            for command in gcode:
                # print("command= ", command)
                if command[0] == 'X' and command[1:]:
                    commands['X'] = float(command[1:])
                elif command[0] == 'Y' and command[1:]:
                    commands['Y'] = float(command[1:])
                elif command[0] == 'Z' and command[1:]:
                    commands['Z'] = float(command[1:])
                elif command[0] == 'S' and command[1:]:
                    commands['S'] = float(command[1:])
                elif command[0] == 'G' and command[1:]:
                    commands['G'] = float(command[1:])
                elif command[0] == 'M' and command[1:]:  # Check for 'M' command
                     commands['M'] = float(command[1:])
            ExecuteGcode(commands)

def read_gcode_from_file(file_path):
    with open(file_path, 'r') as file:
        gcode_string = file.read()
    return gcode_string

def main():
    EnableMotors()
    # Assuming generator.generated_gcode contains the G-code string
    gcode_file_path = "newcode.txt"  # Replace with the actual file path
    gcode_string = read_gcode_from_file(gcode_file_path)
    ProcessGcodeString(gcode_string)

if __name__ == "__main__":
    main()