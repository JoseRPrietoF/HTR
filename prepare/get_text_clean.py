import re 

input_path = "/data2/jose/projects/HTR/prepare/text.txt"
output_text = "/data2/jose/projects/HTR/prepare/text_clean.txt"

def read_input(p):
    f = open(p, "r")
    lines = f.readlines()
    f.close()
    strings = []
    for line in lines:
        line = line.split(" ")[1:]
        line = "".join(line)
        line = line.replace("<space>", " ")
        line =  re.sub(r"[^a-zA-Z0-9 ]+", '', line)
        strings.append(line)
    return strings

strings = read_input(input_path)
f = open(output_text, "w")
for s in strings:
    f.write("{}\n".format(s))
f.close()