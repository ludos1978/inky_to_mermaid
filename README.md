# inky_to_mermaid

Converts a basic inky (https://www.inklestudios.com/ink/) file to a mermaid graph and creates a pdf out of it as well. Does help to get an overview how the structure of the ink story looks.

## not-features

- cannot handle subchoices
- does not render text by default (makes the graph to big)
- does not render choice text by default (makes the graph to big)
- does not handle default choices
- does not handle includes
- no advanced features such as variables etc.
- does not generate good large graphs

## running

- install python3 if you dont have it
- install the ply python library (pip install ply)
- install mmdc to convert the mmd file to a pdf directly (https://github.com/mermaid-js/mermaid-cli)

## ?

Why is it written in Python?
- Because i know Python and like the language. Rewriting it in Javascript using the inkjs would maybe make sense.

