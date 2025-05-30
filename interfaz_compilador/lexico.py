# lexico.py (modificado)
import re

class AnalizadorLexicoJS:
    def __init__(self):
        self.warnings = []
        self.errores = []
        self.resultados_consola = []
        self.tokens = []

    def analizar(self, codigo):
        self.warnings.clear()
        self.errores.clear()
        self.resultados_consola.clear()
        self.tokens.clear()
        self.lineas = codigo.split('\n') 
        
        # Eliminar comentarios
        codigo = re.sub(r'//.*|/\*[\s\S]*?\*/', '', codigo)
        
        # Identificar tokens
        self._identificar_tokens(codigo)
        self._verificar_declaraciones(codigo)
        
        return {
            "errores": self.errores,
            "warnings": self.warnings,
            "consola": self.resultados_consola,
            "tokens": self.tokens
        }

    def _identificar_tokens(self, codigo):
        token_patterns = [
            ('PALABRA_RESERVADA', r'\b(break|switch|case|default|var|let|const|if|else|for|while)\b'),
            ('OPERADOR', r'[+\-*/=]'),
            ('NUMERO', r'\d+(\.\d+)?'),
            ('TIPO_DATO', r'\b(int|double|string|bool)\b'),
            ('COMENTARIO', r'//.*|/\*[\s\S]*?\*/'),
            ('CADENA', r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''),
            ('CADENA_INVALIDA', r'["\']'),  # Captura comillas sueltas
            ('IDENTIFICADOR', r'[a-zA-Z_]\w*'),
            ('CONSOLE_LOG', r'console\.log\b'),
            ('ERROR_CONSOLE', r'consolelog\b'),  # Detecta errores de escritura
            ('ERROR_CASE', r'\b(\w*case\b(?<!case))'),  # Detecta errores como xcase, 1case, etc.
            ('ERROR_NUMERIC_LABEL', r'^\s*(\d+)\s*:'),  # Detecta etiquetas numéricas sin case
            ('ERROR_FOR', r'\b(ffor|forr)\b'),  # Detectar errores comunes de escritura con 'for'
            ('CORCHETE_APERTURA', r'\['),
            ('CORCHETE_CIERRE', r'\]'),
            ('COMA', r','),
            ('ARRAY_LITERAL', r'\[.*?\]'),  # Captura literales como [1, "a", true]
            ('FUNCTION_KW', r'\bfunction\b'),
            ('RETURN_KW', r'\breturn\b'),
            ('PARAMETROS', r'\([^)]*\)'),  # Captura parámetros
            ('ERROR_PALABRA_RESERVADA', r'\b(functi0n|f0r|if0|etc)\b'),
            ('ERROR_PALABRA_NUMERO', r'\b[a-zA-Z]+\d+[a-zA-Z]*\b'),
            ('ERROR_IDENTIFICADOR', r'[^a-zA-Z0-9_]'),  # Detecta símbolos no permitidos
            ('ERROR_CONSOLE', r'console\.[^l][a-zA-Z]*\b'),
        ]
        
        for tipo, patron in token_patterns:
            for match in re.finditer(patron, codigo):
                if tipo == 'CADENA_INVALIDA':
                    self.errores.append(f"Error léxico: Cadena no cerrada en '{match.group()}'")
                elif tipo == 'ERROR_CONSOLE':
                    self.errores.append(f"Error léxico: 'consolelog' no existe. ¿Quisiste usar 'console.log'?")
                elif tipo == 'ERROR_CASE':
                    self.errores.append(f"Error léxico: '{match.group()}' no es válido. ¿Quisiste usar 'case'?")
                elif tipo == 'ERROR_NUMERIC_LABEL':
                    self.errores.append(f"Error léxico: '{match.group()}' no es válido. Debe usar 'case {match.group(1)}:'")
                elif tipo == 'ERROR_FOR':
                    self.errores.append(f"Error léxico: '{match.group()}' no es válido. ¿Quisiste usar 'for'?")
                else:
                    self.tokens.append((tipo, match.group()))

    def _buscar_console_log(self, codigo):
        patron = r'console\.log\s*\(\s*([^)]+)\s*\)\s*;?'
        matches = re.finditer(patron, codigo)
        for match in matches:
            expresion = match.group(1).strip()
            self._evaluar_expresion(expresion)

    def _evaluar_expresion(self, expresion):
        try:
            if expresion.startswith(("'", '"')) and expresion.endswith(("'", '"')):
                valor = expresion[1:-1]
                self.resultados_consola.append(valor)
            else:
                self.resultados_consola.append(f"Error: Expresión no válida -> {expresion}")
        except Exception as e:
            self.errores.append(f"Error al evaluar expresión: {str(e)}")

    def _verificar_declaraciones(self, codigo):
        patron = r'(int|string|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*?);'
        matches = re.finditer(patron, codigo)
        
        for match in matches:
            tipo_declarado = match.group(1)
            variable = match.group(2)
            valor = match.group(3).strip()
            
            if tipo_declarado == "int" and not valor.isdigit():
                self.warnings.append(f"Advertencia: Asignación incompatible - '{tipo_declarado}' a '{valor}' en variable {variable}")
            elif tipo_declarado == "string" and not (valor.startswith(('"', "'")) and valor.endswith(('"', "'"))):
                self.warnings.append(f"Advertencia: Valor no es cadena - '{valor}' en variable {variable}")
            elif tipo_declarado == "bool" and valor not in {"true", "false"}:
                self.warnings.append(f"Advertencia: Valor booleano no válido - '{valor}' en variable {variable}")