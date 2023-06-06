import ply.lex as lex
import ply.yacc as yacc
import sys
import os
import subprocess
from collections import OrderedDict

insert_knot_text = False
insert_choice_text = False
render_mermaid = True

tokens = (
   'KNOT',
   'SUBKNOT',
   'CHOICE',
#    'SUBCHOICE',
   'REDIRECT',
   'TEXT',
)

t_ignore = ' \t\n'

def t_KNOT(t):
    r'=== .+ ==='
    t.value = t.value.strip().strip('=').strip()
    return t

def t_SUBKNOT(t):
    r'= .+'
    t.value = t.value.strip().lstrip('=').strip()
    return t

def t_CHOICE(t):
    r'\* .+'
    t.value = t.value.strip().lstrip('*').strip()
    return t

# def t_SUBCHOICE(t):
#     r'\* \* .+'
#     t.value = t.value.strip().lstrip('*').strip().lstrip('*').strip()
#     return t

def t_REDIRECT(t):
    r'-> .+'
    t.value = t.value.strip().lstrip('->').strip()
    return t

def t_TEXT(t):
    r'.+'
    return t

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

def p_script(p):
    '''script : block
              | script block'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_block(p):
    '''block : knot
             | subknot
             | choice
             | redirect
             | text'''
            #  | subchoice
    p[0] = p[1]

def p_knot(p):
    'knot : KNOT'
    p[0] = { 'type': 'knot', 'name': p[1] }

def p_subknot(p):
    'subknot : SUBKNOT'
    p[0] = { 'type': 'subknot', 'name': p[1] }

def p_choice(p):
    'choice : CHOICE'
    p[0] = { 'type': 'choice', 'name': p[1] }

# def p_subchoice(p):
#     'subchoice : SUBCHOICE'
#     p[0] = { 'type': 'subchoice', 'name': p[1] }

def p_redirect(p):
    'redirect : REDIRECT'
    p[0] = { 'type': 'redirect', 'destination': p[1] }

def p_text(p):
    'text : TEXT'
    p[0] = { 'type': 'text', 'content': p[1] }

def p_error(p):
    print("Syntax error in input!")

parser = yacc.yacc()


def split_text_with_words(text, chunk_size=40):
    words = text.split()
    chunks = []
    current_chunk = ""
    
    for word in words:
        if len(current_chunk) + len(word) <= chunk_size:
            current_chunk += word + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return '\n'.join(chunks)

def text_replace_doubledot (text):
    return text.replace(":", ";")

def close_previous(close_text=True, close_choice=True):
    global current_choice
    global current_text
    global mermaid_data
    if close_text:
        if current_text:
            if insert_knot_text:
                mermaid_data += f"\n    end note\n"
            current_text = False
    if close_choice:
        if current_choice:
            if insert_choice_text:
                mermaid_data += f"\n    end note\n"
            current_choice = False

def generate_mermaid(parsed_data):
    # First pass: gather all knots and subknots
    knots = {"[*]": OrderedDict(), "END": OrderedDict()}  # Add "END" as a default knot
    current_knot = "[*]"
    for block in parsed_data:
        if block['type'] == 'knot':
            current_knot = block['name']
            knots[current_knot] = OrderedDict()
        elif block['type'] == 'subknot':
            knots[current_knot][block['name']] = None

    # for knot in knots:
    #     print (f"{knot} {knots[knot].keys()}")

    # Second pass: generate Mermaid code
    global mermaid_data
    mermaid_data = "stateDiagram-v2\n"
    # mermaid_data = "stateDiagram\n"
    # mermaid_data = "graph TB\n"
    current_knot = "[*]"
    # mermaid_data += f"    {current_knot}: {current_knot}\n"
    mermaid_data += f"    {current_knot}: {current_knot}\n"
    current_subknot = ""
    global current_choice
    global current_text
    current_choice = False
    current_text = False
    for block in parsed_data:
        if block['type'] == 'knot':
            close_previous()
            current_knot = block['name']
            if (len(knots[current_knot]) > 0):
                current_subknot = next(iter(knots[current_knot]))
            else:
                current_subknot = ""
            # mermaid_data += f"    {current_knot}\n"
        elif block['type'] == 'subknot':
            close_previous()
            current_subknot = block['name']
            full_subknot_name = f"{current_knot}.{current_subknot}"
            mermaid_data += f"    {full_subknot_name}:{full_subknot_name}\n"
        elif block['type'] == 'redirect':
            close_previous()
            destination = block['destination']
            # it's not knot.subknot structure
            if '.' not in destination:
                # it's a knot
                if destination in knots:
                    # it has subknots
                    if len(knots[destination].keys()) > 0:
                        # use the first subknot
                        destination = f"{destination}.{list(knots[destination].keys())[0]}"
                else:
                    destination = f"{current_knot}.{destination}"
            mermaid_data += f"    {full_subknot_name if current_subknot else current_knot} --> {destination}\n"
        elif block['type'] == 'choice':
            close_previous(close_choice=False)
            # open choice
            if not current_choice:
                full_subknot_name = f"{current_knot}{'.' if current_subknot else ''}{current_subknot}"
                if insert_choice_text: 
                    mermaid_data += f"    note left of {full_subknot_name}\nCHOICE: "
                current_choice = True
            if insert_choice_text: 
                mermaid_data += f"{split_text_with_words(text_replace_doubledot(block['name']))}"
        # elif block['type'] == 'subchoice':
        #     close_previous(close_choice=False)
        #     # open choice
        #     if not current_choice:
        #         full_subknot_name = f"{current_knot}{'.' if current_subknot else ''}{current_subknot}"
        #         mermaid_data += f"    note left of {full_subknot_name}\nSUBCHOICE: "
        #         current_choice = True
        #     mermaid_data += f"{split_text_with_words(text_replace_doubledot(block['name']))}"
        elif block['type'] == 'text':
            close_previous(close_text=False)
            # open text
            if not current_text:
                full_subknot_name = f"{current_knot}{'.' if current_subknot else ''}{current_subknot}"
                if insert_knot_text:
                    mermaid_data += f"    note right of {full_subknot_name}\nTEXT: "
                current_text = True
            if insert_knot_text:
                mermaid_data += f"{split_text_with_words(text_replace_doubledot(block['content']))}"
            # print (block['content'])
    return mermaid_data

def modify_filename(filename, insert, new_extension):
    base_name, _ = os.path.splitext(filename)
    new_filename = f"{base_name}{insert}.{new_extension}"
    counter = 1

    while os.path.exists(new_filename):
        new_filename = f"{base_name}{insert}_{counter}.{new_extension}"
        counter += 1

    return new_filename

def convert_mermaid_to_pdf(mermaid_file, pdf_output):
    try:
        subprocess.run(['mmdc', '-i', mermaid_file, '-o', pdf_output], check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during conversion: {e}')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parser.py filename")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, 'r') as file:
        data = file.read()

    data = "\n->".join(data.split("->"))

    parsed_data = parser.parse(data)

    mermaid_data = generate_mermaid(parsed_data)

    mmd_filename = modify_filename(filename, "_mermaid", "mmd")
    
    with open(mmd_filename, 'w') as file:
        file.write(mermaid_data)
        # (f"```mermaid\n{mermaid_data}```") // .md file format

    pdf_filename = modify_filename(filename, "_mermaid", "pdf")
    convert_mermaid_to_pdf(mmd_filename, pdf_filename)
