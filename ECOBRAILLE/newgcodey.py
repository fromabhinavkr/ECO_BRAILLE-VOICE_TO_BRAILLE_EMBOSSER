import os

class BrailleGCodeGenerator:
    def __init__(self):
        # Define braille dimensions
        #CODE WITH CORRECT Y VALUE
        self.BRAILLE = {
            "marginWidth": 3,
            "marginHeight": 5,
            "paperWidth": 180,
            "paperHeight": 260,
            "letterWidth": 2.5,
            "dotRadius": 1.2,
            "letterPadding": 3.7,
            "linePadding": 10,
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

    def gcode_print_dot_cached(self, X=None, Y=None):
        if X is None:
            X = self.xhead
        if Y is None:
            Y = self.yhead
        self.xhead = X
        self.yhead = Y
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
            code_str += self.gcode_print_dot_cached(position["x"], position["y"])

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

        max_row_length = 0
        rows = [[] for _ in range(4 if is_8dot else 3)]

        for i, char in enumerate(text_copy):
            char_is_capital_letter = is_8dot and char.isupper()
            char_is_line_break = char in ["\r", "\n"]

            if char_is_line_break:
                current_y += (2 if is_8dot else 3) * letter_width + self.BRAILLE["linePadding"]
                current_x = self.BRAILLE["marginWidth"]  # Reset current_x to the left margin

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

            row_indices = [[0, 0], [0, 0], [0, 0], [0, 0]]  # Initialize row indices
            for j, index in enumerate(indices):
                dot_map_value = self.LANGUAGES[self.BRAILLE["language"]]["dotMap"][j // 3][j % 3]
                if isinstance(dot_map_value, (list, tuple)):
                    row, col = dot_map_value
                else:
                    row = dot_map_value
                    col = 0
                row_indices[row - 1][col - 1] = 1

            rows[0].append(row_indices[0])
            rows[1].append(row_indices[1])
            rows[2].append(row_indices[2])
            if is_8dot:
                rows[3].append(row_indices[3])

            max_row_length = max(max_row_length, len(rows[0]))

            # Calculate the X-coordinate for the current character
            char_x = current_x

            current_x += self.BRAILLE["letterWidth"] + self.BRAILLE["letterPadding"]

            if current_x + self.BRAILLE["dotRadius"] > self.BRAILLE["paperWidth"] - self.BRAILLE["marginWidth"]:
                current_y += (2 if is_8dot else 3) * letter_width + self.BRAILLE["linePadding"]
                # current_x = self.BRAILLE["marginWidth"] + self.BRAILLE["letterWidth"] + self.BRAILLE["letterPadding"]
                current_x = self.BRAILLE["marginWidth"] + self.BRAILLE["paperWidth"] - (self.BRAILLE["marginWidth"] + letter_width)

            if current_y > self.BRAILLE["paperHeight"] - self.BRAILLE["marginHeight"]:
                break

            for row_index, row in enumerate(rows):
                current_col_index = 0
                for col_index, cell in enumerate(row):
                    if col_index >= len(rows[0]):
                        break

                    if any(cell):
                        if row_index == 0:
                            for dot in cell:
                                if dot:
                                    gcode += self.gcode_print_dot_cached(char_x, current_y)
                        else:
                            gcode += self.gcode_move_to_cached(char_x, current_y + row_index * self.BRAILLE["letterWidth"])
                            for dot_index, dot in enumerate(cell):
                                if dot:
                                    dot_x = char_x + dot_index * self.BRAILLE["dotRadius"] * 2
                                    gcode += self.gcode_print_dot_cached(dot_x, current_y + row_index * self.BRAILLE["letterWidth"])

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
        filename = os.path.join(directory, "y_code.txt")
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
