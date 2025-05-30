# sintactico.py
import re

class AnalizadorSintacticoJS:
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.estructuras_validas = []
        self.nivel_llaves = 0
        self.lineas = [] 

    def analizar(self, codigo):
        self.errores.clear()
        self.warnings.clear()
        self.estructuras_validas = []
        self.nivel_llaves = 0
        self.lineas = [ln.strip() for ln in codigo.split('\n') if ln.strip()]

        i = 0
        while i < len(self.lineas):
            linea = self.lineas[i]
            
            # Verificar estructura if
            if re.match(r'^\s*if\s*\(', linea):
                resultado = self._validar_if(linea, i+1)
                if resultado:
                    i = resultado  # Saltar al final del bloque if-else
                    continue
            
            elif re.match(r'^\s*for\s*\(', linea):
                resultado = self._validar_for(linea, i+1)
                if resultado:
                    i = resultado  # Saltar al final del bloque for
                    continue
                
            # Verificar declaraciones
            elif re.match(r'^\s*(let|var|const)\s+', linea):
                self._validar_declaracion(linea, i+1)
                
            # Verificar console.log
            elif 'console.log' in linea:
                self._validar_console_log(linea, i+1)
                
            # Verificar balance de llaves
            self._verificar_llaves(linea, i+1)
            
            i += 1
            
        # Verificación final de llaves
        if self.nivel_llaves > 0:
            self.errores.append("Llaves abiertas sin cerrar al final del código")
        elif self.nivel_llaves < 0:
            self.errores.append("Llaves cerradas sin abrir al final del código")
            
        return {
            "errores": self.errores,
            "warnings": self.warnings,
            "estructuras": self.estructuras_validas
        }

    def _validar_if(self, linea, num_linea):
        # Check for common typos in the "if" keyword
        if not re.match(r'^\s*if\s*\(.*?\)', linea):
            self.errores.append(f"Línea {num_linea}: Falta '(' o ')' en if")

        if re.match(r'^\s*(fi|i[^\s])\s*\(', linea):
            palabra_incorrecta = re.match(r'^\s*([^\s]+)', linea).group(1)
            self.errores.append(f"Línea {num_linea}: Palabra reservada incorrecta '{palabra_incorrecta}'. Use 'if'")
            return None
            
        # Verificar estructura básica del if
        if not re.match(r'^\s*if\s*\(', linea):
            self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta al inicio del if. Use 'if ('")
            return None
            
        if not re.search(r'\)\s*{?', linea):
            self.errores.append(f"Línea {num_linea}: Falta ')' o '{{' en if")
            return None
                
        # Extraer la condición
        condicion_match = re.search(r'if\s*\((.*?)\)', linea)
        if not condicion_match:
            self.errores.append(f"Línea {num_linea}: Condición mal formada en if")
            return None
            
        condicion = condicion_match.group(1).strip()
        if not condicion:
            self.errores.append(f"Línea {num_linea}: Condición vacía en if")
        else:
            # Validate condition is a boolean expression
            self._validar_condicion_if(condicion, num_linea)
        
        # Check for missing open curly brace
        if not re.search(r'\)\s*{', linea) and not re.search(r'\)\s*$', linea):
            self.warnings.append(f"Línea {num_linea}: Recomendable usar llaves '{{}}' en el bloque if")
            
        # Determinar si hay else asociado
        bloque_if, final_line = self._extraer_bloque(linea, num_linea, 'if')
        self.estructuras_validas.append(f"If válido en línea {num_linea}")
        
        # Validar estructuras dentro del bloque if
        for ln in bloque_if:
            if 'switch' in ln:
                self._validar_switch(ln, num_linea)
        
        # Buscar else o else if
        if final_line < len(self.lineas):
            siguiente_linea = self.lineas[final_line].strip()
            if re.match(r'^\s*else\s+if\b', siguiente_linea):
                # Manejar else if recursivamente
                nuevo_final = self._validar_if(siguiente_linea.replace('else', '', 1).strip(), final_line+1)
                return nuevo_final if nuevo_final else final_line + 1
            elif re.match(r'^\s*else\b', siguiente_linea):
                # Check if else is properly connected to if (with } else {)
                if not re.search(r'\}\s*else', self.lineas[final_line-1] + siguiente_linea):
                    self.errores.append(f"Línea {final_line+1}: 'else' sin 'if' correspondiente o mal formado")
                
                bloque_else, final_line = self._extraer_bloque(siguiente_linea, final_line+1, 'else')
                self.estructuras_validas.append(f"Else válido en línea {final_line}")
                
        return final_line

    def _validar_switch(self, linea, num_linea):
        if not re.match(r'switch\s*\(.+?\)\s*\{?', linea):
            self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en switch")
        
        bloque_switch, _ = self._extraer_bloque(linea, num_linea, 'switch')

        case_values = set()
        for idx, ln in enumerate(bloque_switch):
            match_case = re.match(r'\s*case\s+(.*?):', ln)
            if match_case:
                valor = match_case.group(1).strip()
                if valor in case_values:
                    self.errores.append(f"Línea {num_linea + idx + 1}: Duplicado 'case {valor}' en switch")  # <--- Error crítico
                else:
                    case_values.add(valor)

    def _validar_for(self, linea, num_linea):
        # Verificar estructura básica del for
        match = re.match(r'^\s*for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)\s*\{?', linea)
        if not match:
            self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en for. Use 'for(inicialización; condición; incremento) {{ ... }}'")
            return None
        if not self._es_expresion_booleana(condicion):
            self.errores.append(f"Línea {num_linea}: Condición no booleana en for")
            
        inicializacion, condicion, incremento = match.groups()
        
        # Validar la parte de inicialización
        if inicializacion and not (
            re.match(r'^\s*(let|var|const)?\s*[a-zA-Z_]\w*\s*=\s*.+$', inicializacion) or
            re.match(r'^\s*[a-zA-Z_]\w*\s*=\s*.+$', inicializacion)
        ):
            self.errores.append(f"Línea {num_linea}: Inicialización inválida en for: '{inicializacion}'")
        
        # Validar la condición
        if condicion.strip() and not self._es_expresion_booleana(condicion):
            self.warnings.append(f"Línea {num_linea}: La condición del for podría no ser booleana: '{condicion}'")
        
        # Validar el incremento
        if incremento and not (
            re.match(r'^\s*[a-zA-Z_]\w*\s*(\+\+|--)\s*$', incremento) or
            re.match(r'^\s*[a-zA-Z_]\w*\s*[+\-*/]?=\s*.+$', incremento)
        ):
            self.errores.append(f"Línea {num_linea}: Incremento inválido en for: '{incremento}'")
        
        # Extraer y analizar el bloque
        bloque_for, final_line = self._extraer_bloque(linea, num_linea, 'for')
        self.estructuras_validas.append(f"For válido en línea {num_linea}")
        
        return final_line

    def _validar_condicion_if(self, condicion, num_linea):        
        # Check for assignment instead of comparison (= instead of ==)
        if re.search(r'[^=!<>]=[^=]', condicion):
            self.errores.append(f"Línea {num_linea}: Posible error en condición, uso de '=' (asignación) en lugar de '==' (comparación)")
        
        # Check for missing operands
        if re.search(r'(==|!=|>=|<=|>|<)\s*$', condicion) or re.search(r'^\s*(==|!=|>=|<=|>|<)', condicion):
            self.errores.append(f"Línea {num_linea}: Operando faltante en la condición")
            
        # Check if condition evaluates to boolean
        if not self._es_expresion_booleana(condicion):
            self.warnings.append(f"Línea {num_linea}: La condición '{condicion}' podría no ser booleana")
            
        # Check for unclosed strings in condition
        comillas = re.findall(r'["\'](.*?)["\']', condicion)
        if len(comillas) % 2 != 0 and re.search(r'["\']', condicion):
            self.errores.append(f"Línea {num_linea}: Comillas sin cerrar en la condición")

        if ' = ' in condicion and ' == ' not in condicion:
            self.errores.append(f"Línea {num_linea}: Uso de '=' en lugar de '=='")    
    
        if re.search(r'\b=\b', condicion) and not re.search(r'\b==\b', condicion):
            self.errores.append(f"Línea {num_linea}: Uso de '=' en lugar de '=='")

    def _es_expresion_booleana(self, expr):
        # Verificar si la expresión evalúa a bool
        return any(keyword in expr for keyword in ['==', '!=', '>', '<', 'true', 'false'])

    def _extraer_bloque(self, linea, num_linea, tipo):
        # Manejar bloques con llaves
        if '{' in linea:
            self.nivel_llaves += 1
            lineas_bloque = []
            nivel = 1
            i = num_linea
            while i < len(self.lineas) and nivel > 0:
                self.nivel_llaves += self.lineas[i].count('{')
                self.nivel_llaves -= self.lineas[i].count('}')
                nivel = self.nivel_llaves
                lineas_bloque.append(self.lineas[i])
                i += 1
            return lineas_bloque, i
        
        # Manejar bloques de una línea sin llaves
        else:
            return [linea.split(')')[-1].strip()], num_linea + 1
        
    def _verificar_parentesis_balanceados(self, codigo):
        balance = 0
        for c in codigo:
            if c == '(': balance += 1
            elif c == ')': balance -= 1
            if balance < 0: break
        if balance != 0:
            self.errores.append("Paréntesis desbalanceados")

    def _verificar_llaves(self, linea, num_linea):
        self.nivel_llaves += linea.count('{')
        self.nivel_llaves -= linea.count('}')
        if self.nivel_llaves < 0:
            self.errores.append(f"Línea {num_linea}: Llaves cerradas sin abrir")

    def _validar_declaracion(self, linea, num_linea):
        if not re.match(r'^\s*(let|var|const)\s+[a-zA-Z_]\w*\s*=\s*.+?\s*;?$', linea):
            self.errores.append(f"Línea {num_linea}: Declaración inválida")
        else:
            self.estructuras_validas.append(f"Declaración válida en línea {num_linea}")

    def _validar_console_log(self, linea, num_linea):
        if not re.match(r'^\s*console\.log\(.*?\)\s*;?$', linea):
            self.errores.append(f"Línea {num_linea}: console.log mal formado")
        else:
            self.estructuras_validas.append(f"Console.log válido en línea {num_linea}")