# encoding: utf-8

from collections import defaultdict

import ply.lex as lex
import ply.yacc as yacc

import re

version = 1
section = ''
characters = defaultdict(list)
backgrounds = defaultdict(list)
macro_names = set()
blocks = []
line_number = 1

def parse_script(script):
    tokens = [
        # symbols
        'EQUAL', 'COLON', 'COMMENT',
        'SQUARE_OPEN', 'SQUARE_CLOSE',
        'CURLY_OPEN', 'CURLY_CLOSE',
        'NEWLINE',
        # data type
        'INTEGER', 'STRING',
    ]

    reserved = {
        'narr': 'NARRATOR',
    }

    literals = ['<', '>', '/', '@']

    tokens += reserved.values()

    t_EQUAL        = r'='
    t_COLON        = r':'

    t_SQUARE_OPEN  = r'\['
    t_SQUARE_CLOSE = r'\]'
    t_CURLY_OPEN   = r'\{'
    t_CURLY_CLOSE  = r'\}'

    # ignore space or tabs
    t_ignore       = ' \t'

    def t_INTEGER(t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(t):
    	r'[^\n\[\]\{\}\<\>\=\"@\/\;\:]+'
    	if t.value in reserved:
    	    t.type = reserved[t.value]
    	return t

    def t_NEWLINE(t):
        r'\n'
        t.lexer.lineno += 1
        return t

    def t_COMMENT(t):
        r'\/{2}.*'
        return t

    def t_error(e):
        raise ScriptImportParserError('ERR_IMPORT_SCRIPT_TOKENIZATION_ERROR', {
                  'message': str(e),
              })

    # Build the lexer
    lex.lex()

    def p_file(p):
        '''
        file :
             | file section_tag
             | file comment
             | file declaration
             | file script
             | file NEWLINE
        '''
        if len(p) == 1:
            p[0] = []
        elif p[2] != '\n':
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = p[1]     # newline
            global line_number
            line_number = line_number + 1

    def p_section_tag(p):
        '''
        section_tag : '<' expression '>'
                    | '<' '/' expression '>'
        '''
        global section
        p[0] = p[2].lower() if len(p) == 4 else p[3].lower()
        if p[0] not in ['declaration', 'script']:
            raise_syntax_error('ERR_IMPORT_SCRIPT_UNRECOGNIZED_SECTION_TAG')
        section = '' if section == p[0] else p[0]

    # scripts
    def p_script(p):
        '''
        script : character_script
               | background_script
               | aside_script
        '''
        if section != 'script':
            raise_syntax_error('ERR_IMPORT_SCRIPT_SHOULD_NOT_WRITE_SCRIPT_IN_DECLARATION')

    def p_script_character(p):
        '''character_script : character_tag COLON dialog'''
        p[3] = parse_dialog(p[3])

        character = characters[p[1]]
        attributes = {
            "character": character['id'],
            "dialog": p[3],
        }
        if 'name' in character:
            attributes['name'] = character['name']

        add_block('characterdialog', attributes)

    def p_script_aside(p):
        '''aside_script : aside_tag COLON dialog'''
        p[3] = parse_dialog(p[3])

        attributes = {
            'text': p[3],
        }

        add_block('aside', attributes)

    def p_dialog(p):
        '''
        dialog : expression
               | dialog NEWLINE
               | dialog NEWLINE expression
        '''
        p[0] = ''.join(str(s) if s else '' for s in p)
        if len(p) > 2:
            global line_number
            line_number = line_number + 1

    def p_script_background(p):
        '''background_script : background_tag'''
        background = backgrounds[p[1]]
        attributes = {
            'storage': background,
        }
        add_block('bg', attributes)

    def p_script_comment(p):
        '''comment : COMMENT'''
        p[0] = p[1][2:]
        if p[0] and section == 'script':
            add_block('comment', { 'text': p[0] })

    # declaration

    def p_declaration(p):
        '''
        declaration : character_declaration
                    | background_declaration
                    | version_declaration
        '''
        if section != 'declaration':
            raise_syntax_error('ERR_IMPORT_SCRIPT_SHOULD_NOT_WRITE_DECLARATION_IN_SCRIPT')

    def p_declaration_character(p):
        '''
        character_declaration : character_tag EQUAL INTEGER
                              | character_tag EQUAL INTEGER '@' expression
        '''
        asset_object = { 'id': p[3] }
        if len(p) == 6:
            asset_object['name'] = p[5]
        characters[p[1]] = asset_object

    def p_declaration_background(p):
        '''background_declaration : background_tag EQUAL INTEGER'''
        backgrounds[p[1]] = p[3]

    def p_declaration_version(p):
        '''version_declaration : expression EQUAL INTEGER'''
        if p[1] == 'version' and version != p[3]:
            print('version not match')

    # tags

    def p_character_tag(p):
        '''character_tag : SQUARE_OPEN expression SQUARE_CLOSE'''
        p[0] = p[2]
        if section == 'script' and not characters[p[0]]:
            raise_syntax_error('ERR_IMPORT_SCRIPT_USING_UNDECLARED_CHARACTER')

    def p_background_tag(p):
        '''background_tag : CURLY_OPEN expression CURLY_CLOSE'''
        p[0] = p[2]
        if section == 'script' and not backgrounds[p[0]]:
            raise_syntax_error('ERR_IMPORT_SCRIPT_USING_UNDECLARED_BACKGROUND')

    def p_aside_tag(p):
        '''aside_tag : SQUARE_OPEN NARRATOR SQUARE_CLOSE'''
        p[0] = p[2]

    # expression

    def p_expression_str(p):
        '''expression : STRING'''
        p[0] = p[1].strip()     # remove leading and trailing spaces

    def p_expression_int(p):
        '''expression : INTEGER'''
        p[0] = p[1]


    def p_error(p):
        if not p:
            raise_syntax_error('ERR_IMPORT_SCRIPT_SYNTAX_ERROR_UNEXPECTED_EOF')
        else:
            raise_syntax_error('ERR_IMPORT_SCRIPT_SYNTAX_ERROR', p.lineno)

    # helper function for script
    def parse_dialog(dialog):
        # remove newline at the end of dialog
        dialog = dialog.rstrip('\n')
        # handle **xxxx** => [keyword]xxxx[endkeyword]
        keywords = re.findall('\*{2}[^\*]+\*{2}', dialog)
        for keyword in keywords:
            dialog = dialog.replace(keyword, '[keyword]%s[endkeyword]' % keyword[2:-2])

        # handle !~ 2000~! => [wait time=2000]
        keywords = re.findall('!~[^~!]+~!', dialog)
        for keyword in keywords:
            wait_time = keyword[2:-2].strip()
            if not wait_time.isdigit():
                raise ScriptImportParserError('ERR_IMPORT_SCRIPT_WAIT_TIME_IS_NOT_AN_INTEGER')
            dialog = dialog.replace(keyword, '[wait time=%s]' % wait_time)

        return dialog

    yacc.yacc()

    def add_block(macro_name, attributes):
        macro_names.add(macro_name)
        blocks.append({
            "macro": macro_name,
            "attributes": attributes
        })

    def raise_syntax_error(key, line = None):
        if not line:
            line = line_number
        raise ScriptImportParserError(key, {
                  'line': line,
                  'content': script.split('\n')[line - 1],
              })

    result = yacc.parse(script)

    character_ids = set(character['id'] for character in characters.values())
    asset_ids = set(backgrounds.values())

    return [character_ids, asset_ids, macro_names, blocks]


class ScriptImportParserError(Exception):

    def __init__(self, key, interpolation={}):
        self.key = key
        self.interpolation = interpolation

    def __str__(self):
        return self.key
