utils = {}

with open("utils.utils") as myfile:
    for line in myfile:
        if "##" not in line:
            key, value = line.partition("=")[::2]
            if value:
                utils[key.strip()] = value
            else:
                utils[key.strip()] = int(value)

