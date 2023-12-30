class color:
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    orange = '\033[93m'
    blue = '\033[34m'
    magenta = '\033[35m'
    cyan = '\033[36m'
    white = '\033[37m'
    grey = '\033[90m'
    light_red = '\033[91m'
    light_green = '\033[92m'
    light_yellow = '\033[93m'
    light_blue = '\033[94m'
    light_magenta = '\033[95m'
    light_cyan = '\033[96m'
    light_white = '\033[97m'
    purple = '\033[35m'  # Added purple color
    end = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

def black(string):
    return f"{color.black}{string}{color.end}"

def red(string):
    return f"{color.red}{string}{color.end}"

def green(string):
    return f"{color.green}{string}{color.end}"

def yellow(string):
    return f"{color.yellow}{string}{color.end}"

def orange(string):
    return f"{color.orange}{string}{color.end}"

def blue(string):
    return f"{color.blue}{string}{color.end}"

def purple(string):
    return f"{color.purple}{string}{color.end}"

def magenta(string):
    return f"{color.magenta}{string}{color.end}"

def cyan(string):
    return f"{color.cyan}{string}{color.end}"

def white(string):
    return f"{color.white}{string}{color.end}"

def grey(string):
    return f"{color.grey}{string}{color.end}"

def light_red(string):
    return f"{color.light_red}{string}{color.end}"

def light_green(string):
    return f"{color.light_green}{string}{color.end}"

def light_yellow(string):
    return f"{color.light_yellow}{string}{color.end}"

def light_blue(string):
    return f"{color.light_blue}{string}{color.end}"

def light_magenta(string):
    return f"{color.light_magenta}{string}{color.end}"

def light_cyan(string):
    return f"{color.light_cyan}{string}{color.end}"

def light_white(string):
    return f"{color.light_white}{string}{color.end}"

def bold(string):
    return f"{color.bold}{string}{color.end}"

def underline(string):
    return f"{color.underline}{string}{color.end}"
