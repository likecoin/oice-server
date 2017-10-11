# pylama:ignore=C901,ignore=W612,ignore=E501
import ply.lex as lex
import ply.yacc as yacc

def parse(input_text):

    # we need this to close at_tag
    input_text = input_text+"\n"

    tokens = [
        'OPEN_TAG_SQUARE', 'CLOSE_TAG_SQUARE',
        'OPEN_TAG_AT',
        'IDENTIFIER', 'EQUAL', 'QUOTE',
        'SEMICOLON', 'ASTERISK', 'PIPE',
        'NEWLINE', 'TAB', 'SPACE', 'AND'
        ]
    reserved = {
        'iscript': 'ISCRIPT',
        'endscript': 'ENDSCRIPT'
    }

    tokens += reserved.values()

    t_OPEN_TAG_AT = r'@'
    t_OPEN_TAG_SQUARE = r'\['
    t_CLOSE_TAG_SQUARE = r'\]'
    t_EQUAL = r'[\s\t]*=[\s\t]*'
    t_SPACE = r'[^\S\n]+'
    t_TAB = r'\t+'
    t_QUOTE = r'\"'
    t_SEMICOLON = r';'
    t_AND = r'\&'
    t_ASTERISK = r'\*'
    t_PIPE = r'[\s\t]*\|[\s\t]*'

    def t_IDENTIFIER(t):
        r'[^\s\t\n\[\]\=\"@\;\*\|\&]+'
        if t.value in reserved:
            t.type = reserved[t.value]
        return t

    def t_NEWLINE(t):
        r'\n'
        t.lexer.lineno += 1
        return t

    def t_error(e):
        # TODO: error handling
        print('t error')

    # Build the lexer
    lex.lex()

    def p_file(p):
        '''file :
                | file tags
                | file comment_line
                | file NEWLINE'''
        if len(p) == 1:
            p[0] = []
        elif p[2] != '\n':
            # adding tag to file
            if type(p[2]) is list:
                for tag in p[2]:
                    p[1].append(tag)

            else:
                # only add tag, so ignore comment
                p[1].append(p[2])
            p[0] = p[1]
        else:
            # ignore new line
            p[0] = p[1]

    def p_tags(p):
        '''tags : square_tag
                | at_tag
                | text_tags
                | label_tag
                | iscript_tag'''
        p[0] = p[1]

    def p_square_tag(p):
        '''square_tag : OPEN_TAG_SQUARE in_tag_space IDENTIFIER in_tag_space CLOSE_TAG_SQUARE
                      | OPEN_TAG_SQUARE in_tag_space IDENTIFIER in_tag_space attributes in_tag_space CLOSE_TAG_SQUARE
                      | square_tag NEWLINE'''

        if len(p) == 6:
            p[0] = {
                'tagname': p[3],
                'attributes': {},
                'line': p.lineno(1)
            }
        elif len(p) == 8:
            p[0] = {
                'tagname': p[3],
                'attributes': p[5],
                'line': p.lineno(1)
            }
        elif len(p) == 3:
            p[0] = p[1]

    def p_at_tag(p):
        '''at_tag : OPEN_TAG_AT IDENTIFIER NEWLINE
                  | OPEN_TAG_AT IDENTIFIER in_tag_space attributes NEWLINE
                  | at_tag NEWLINE'''

        if len(p) == 4:
            p[0] = {
                'tagname': p[2],
                'attributes': {},
                'line': p.lineno(1)
            }
        elif len(p) == 6:
            p[0] = {
                'tagname': p[2],
                'attributes': p[4],
                'line': p.lineno(1)
            }
        elif len(p) == 3:
            p[0] = p[1]

    def p_text_tags(p):
        '''text_tags : text_tag
                     | text_tags NEWLINE
                     | text_tags NEWLINE text_tag'''

        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = p[1]
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]

    def p_text_tag(p):
        '''text_tag : IDENTIFIER
                    | SPACE
                    | EQUAL
                    | PIPE
                    | QUOTE
                    | AND
                    | text_tag ASTERISK
                    | text_tag SEMICOLON
                    | text_tag TAB
                    | text_tag OPEN_TAG_AT
                    | text_tag text_tag'''

        if len(p) == 2:
            p[0] = {
                'tagname': 'text',
                'attributes': {
                    'text': p[1]
                },
                'line': p.lineno(1)
            }
        elif 'tagname' in p[2]:
            # text_tag followed by text_tag
            p[1]['attributes']['text'] += p[2]['attributes']['text']
            p[0] = p[1]
        else:
            p[1]['attributes']['text'] += p[2]
            p[0] = p[1]

    def p_label_tag(p):
        '''label_tag : ASTERISK IDENTIFIER NEWLINE
                     | ASTERISK IDENTIFIER PIPE string_in_quote NEWLINE'''
        if len(p) == 4:
            p[0] = {
                'tagname': 'label',
                'attributes': {
                    'name': p[2]
                },
                'line': p.lineno(1)
            }
        else:
            p[0] = {
                'tagname': 'label',
                'attributes': {
                    'name': p[2],
                    'caption': p[4]
                },
                'line': p.lineno(1)
            }

    def p_iscript_tag(p):
        '''iscript_tag : open_iscript_tag iscript_content end_script_tag'''
        p[0] = {
            'tagname': 'iscript',
            'attributes': {
                'exp': p[2]
            },
            'line': p.lineno(1)
        }

    def p_open_iscript_tag(p):
        '''open_iscript_tag : OPEN_TAG_SQUARE in_tag_space ISCRIPT in_tag_space CLOSE_TAG_SQUARE
                            | OPEN_TAG_AT ISCRIPT NEWLINE
                            | open_iscript_tag NEWLINE'''

    def p_end_script_tag(p):
        '''end_script_tag : OPEN_TAG_SQUARE in_tag_space ENDSCRIPT in_tag_space CLOSE_TAG_SQUARE
                          | OPEN_TAG_AT ENDSCRIPT NEWLINE
                          | end_script_tag NEWLINE'''

    def p_iscript_content(p):
        '''iscript_content : 
                           | iscript_content IDENTIFIER
                           | iscript_content SPACE
                           | iscript_content TAB
                           | iscript_content EQUAL
                           | iscript_content QUOTE
                           | iscript_content AND
                           | iscript_content NEWLINE
                           | iscript_content OPEN_TAG_AT
                           | iscript_content OPEN_TAG_SQUARE
                           | iscript_content CLOSE_TAG_SQUARE
                           | iscript_content SEMICOLON
                           | iscript_content ASTERISK
                           | iscript_content PIPE'''
        if len(p) == 1:
            # create an empty string for later use
            p[0] = ""
        elif len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]

    def p_in_tag_space(p):
        '''in_tag_space :
                        | SPACE'''

    def p_attributes(p):
        '''attributes : attribute
                      | attributes attribute_separator attribute'''
        if len(p) == 2:
            p[0] = {
                p[1]['name']: p[1]['value']
            }
        else:
            p[1][p[3]['name']] = p[3]['value']
            p[0] = p[1]

    def p_attribute_separator(p):
        '''attribute_separator : TAB
                               | SPACE'''

    def p_attribute(p):
        '''attribute : IDENTIFIER
                     | ASTERISK 
                     | IDENTIFIER EQUAL attribute_value'''
        if len(p) == 2:
            if p[0] == '*':
                p[0] = {
                    'name': '*',
                    'value': 'true'
                }
            else:
                p[0] = {
                    'name': p[1],
                    'value': 'true'
                }
        if len(p) == 4:
            p[0] = {
                'name': p[1],
                'value': p[3]
            }

    def p_attribute_value(p):
        '''attribute_value : string_without_quote
                           | QUOTE string_in_quote QUOTE
                           | AND QUOTE string_in_quote QUOTE'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1] + p[2]
        elif len(p) == 4:
            p[0] = p[2]
        elif len(p) == 5:
            p[0] = p[1]+p[3]

    def p_attribute_string(p):
        '''string_without_quote : IDENTIFIER
                                | ASTERISK
                                | AND
                                | string_without_quote AND
                                | string_without_quote IDENTIFIER'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_string_in_quote(p):
        '''string_in_quote : 
                           | string_in_quote IDENTIFIER
                           | string_in_quote SPACE
                           | string_in_quote TAB
                           | string_in_quote AND
                           | string_in_quote EQUAL
                           | string_in_quote OPEN_TAG_AT
                           | string_in_quote OPEN_TAG_SQUARE
                           | string_in_quote CLOSE_TAG_SQUARE
                           | string_in_quote SEMICOLON
                           | string_in_quote ASTERISK
                           | string_in_quote PIPE'''
        if len(p) == 1:
            # create an empty string for later use
            p[0] = ""
        elif len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]

    def p_comment_line(p):
        '''comment_line : comment NEWLINE'''
        p[0] = {
            'tagname': 'comment',
            'attributes': {
                'text': p[1]
            },
            'line': p.lineno(1)
        }

    def p_comment(p):
        '''comment : SEMICOLON
                   | comment IDENTIFIER
                   | comment SPACE
                   | comment TAB
                   | comment EQUAL
                   | comment AND
                   | comment OPEN_TAG_AT
                   | comment OPEN_TAG_SQUARE
                   | comment CLOSE_TAG_SQUARE
                   | comment SEMICOLON
                   | comment ASTERISK
                   | comment PIPE
                   | comment QUOTE'''
        if len(p) == 2:
            p[0] = ""
        else:
            p[0] = p[1] + p[2]

    def p_error(p):
        if not p:
            raise KsParserError('Syntax error, unexpected EOF')
        else:
            raise KsParserError('Line %d, Syntax error, unexpected %s' % (p.lineno,p.type))

    yacc.yacc()

    result = yacc.parse(input_text)

    return result

class KsParserError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value