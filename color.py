class color:
    purple = '\033[95m'
    blue = '\033[94m'
    cyan = '\033[96m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    end = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

def purple(string):
    return f"{color.purple}{string}{color.end}"

def blue(string):
    return f"{color.blue}{string}{color.end}"

def cyan(string):
    return f"{color.cyan}{string}{color.end}"

def green(string):
    return f"{color.green}{string}{color.end}"

def yellow(string):
    return f"{color.yellow}{string}{color.end}"

def red(string):
    return f"{color.red}{string}{color.end}"

def bold(string):
    return f"{color.bold}{string}{color.end}"

def underline(string):
    return f"{color.underline}{string}{color.end}"