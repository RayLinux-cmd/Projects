import re

class AnalizadorSemanticoJS:
    def __init__(self): 
        self.errores = []
        self.warnings = []
        self.console_output = []
        self.variables = {}  # Se agregó para seguimiento de declaraciones

    def analizar(self, codigo):
        self.errores.clear()
        self.warnings.clear()
        self.console_output.clear()
        self.variables.clear()

        # Guardar las líneas para acceso desde otros métodos
        self.lineas = codigo.split('\n')

        # Verificar estructura general
        self._verificar_llaves_balanceadas(codigo)
        self._verificar_parentesis_balanceados(codigo)

        # Analizar declaraciones
        for num_linea, linea in enumerate(self.lineas, 1):
            linea = linea.strip()
            if linea:
                self._analizar_linea(linea, num_linea)

        return {
            "errores": self.errores,
            "warnings": self.warnings,
            "consola": self.console_output
        }

    def _analizar_linea(self, linea, num_linea):
        if linea.startswith("console.log"):
            self._procesar_console_log(linea, num_linea)
        
        if re.match(r'^\s*function\b', linea):
            self._verificar_funcion(linea, num_linea)

        elif re.match(r'\b(var|let|const|int|string|double|bool)\s', linea):
            self._verificar_declaracion(linea, num_linea)
        
        elif re.match(r'\b(switch|case|default)\b', linea):
            self._verificar_estructura_switch(linea, num_linea) 

        elif re.match(r'\b(if|for|while)\b', linea):
            self._verificar_estructura_control(linea, num_linea)

        if not linea.endswith(';') and not re.match(r'.*{\s*$', linea) and not linea.endswith('}') and not linea.endswith(':'):
            if not re.match(r'^\s*(if|for|while|switch|function|else)\b.*$', linea):
                self.errores.append(f"Línea {num_linea}: Falta ';' al final")

        if re.match(r'^\s*switch\s*\(', linea):
            self._verificar_estructura_switch(linea, num_linea)

        if re.match(r'^\s*(case|default)\b', linea):
            switch_encontrado = False
        # Buscar switch anterior
            for ln in reversed(self.lineas[:num_linea-1]):
                if 'switch' in ln:
                    switch_encontrado = True
                    break
            if not switch_encontrado:
                self.errores.append(f"Línea {num_linea}: '{linea}' fuera de bloque switch")

        elif re.match(r'^\s*(case|default)\b', linea):
            if not re.search(r'^\s*switch\s*\(', self.lineas[num_linea-2]):
                self.errores.append(f"Línea {num_linea}: '{linea}' fuera de switch")
        
        # Validar case con valor
        if linea.startswith('case'):
            if not re.match(r'case\s+.+?:', linea):
                self.errores.append(f"Línea {num_linea}: 'case' sin valor o ':'")
        
        # Validar default correcto
        if linea.startswith('default'):
            if not re.match(r'default\s*:', linea):
                self.errores.append(f"Línea {num_linea}: 'default' mal formado")

        else:
            if re.match(r'^\s*[a-zA-Z_]+\w*\s*;', linea):
                self.errores.append(f"Línea {num_linea}: Instrucción no válida: '{linea.strip()}'")

    def _verificar_llaves_balanceadas(self, codigo):
        balance = 0
        for i, c in enumerate(codigo):
            if c == '{': balance += 1
            elif c == '}': balance -= 1
            if balance < 0:
                self.errores.append(f"Llaves desbalanceadas en posición {i}")
                break
        if balance != 0:
            self.errores.append("Llaves desbalanceadas")
    
    def verificar_switch(self, codigo):
        bloques_switch = re.findall(r'switch\s*\([^)]+\)\s*\{(.*?)\}', codigo, re.DOTALL)
        for bloque in bloques_switch:
            casos = re.findall(r'case\s+([^:]+):', bloque)
            ya_vistos = set()
            for caso in casos:
                caso = caso.strip()
                if caso in ya_vistos:
                    self.errores.append(f"Error semántico: Caso duplicado 'case {caso}:'")
                else:
                    ya_vistos.add(caso)

    def _verificar_parentesis_balanceados(self, codigo):
        balance = 0
        for i, c in enumerate(codigo):
            if c == '(': balance += 1
            elif c == ')': balance -= 1
            if balance < 0:
                self.errores.append(f"Paréntesis desbalanceados en posición {i}")
                break
        if balance != 0:
            self.errores.append("Paréntesis desbalanceados")

    def _procesar_console_log(self, linea, num_linea):
        match = re.match(r'console\.log\((.*)\);?$', linea)
        if not match:
            self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en console.log")
            return

        contenido = match.group(1).strip()
        if contenido:
            self.console_output.append(f"[Análisis] Llamada válida a console.log en línea {num_linea}")
        else:
            self.errores.append(f"Línea {num_linea}: console.log vacío")
            
    def _verificar_declaracion(self, linea, num_linea):
        match = re.match(r'^\s*(int|double|string|bool)\s+([a-zA-Z_]\w*)\s*=\s*(.*?)\s*;?$', linea)
        if not match:
            self.errores.append(f"Línea {num_linea}: Declaración inválida o incompleta")
            return
        if re.match(r'^\s*(let|var|const)\s+[a-zA-Z_]\w*\s*=\s*\[.*?\]\s*;?', linea):
            self.estructuras_validas.append(f"Declaración de array válida en línea {num_linea}")
            return
        if nombre in self.variables:
            self.errores.append(f"Línea {num_linea}: Variable '{nombre}' ya declarada")
            return

        tipo, nombre, valor = match.groups()
        if nombre in self.variables:
            self.errores.append(f"Línea {num_linea}: Variable '{nombre}' ya declarada como {self.variables[nombre]}")
        else:
            self.variables[nombre] = tipo

        # Validaciones de tipo
        if tipo == 'double' and not re.match(r'^\d+\.\d+$', valor):
            self.warnings.append(f"Línea {num_linea}: Asignación incompatible (double = {valor})")
        elif tipo == 'int' and not valor.isdigit():
            self.warnings.append(f"Línea {num_linea}: Asignación incompatible (int = {valor})")
        elif tipo == 'string' and not ((valor.startswith('"') and valor.endswith('"')) or (valor.startswith("'") and valor.endswith("'"))):
            self.warnings.append(f"Línea {num_linea}: Valor no es una cadena válida")
        elif tipo == 'bool' and valor not in {'true', 'false'}:
            self.warnings.append(f"Línea {num_linea}: Valor booleano no válido")
    
    def _verificar_funcion(self, linea, num_linea):
        match = re.match(r'function\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*\{?', linea)
        if not match:
            self.errores.append(f"Línea {num_linea}: Sintaxis de función inválida")
            return
        
        nombre, parametros = match.groups()
        if nombre in self.variables:
            self.errores.append(f"Línea {num_linea}: Nombre de función '{nombre}' ya existe")
        
        # Verificar parámetros
        if parametros:
            params = [p.strip() for p in parametros.split(',')]
            if len(params) != len(set(params)):
                self.errores.append(f"Línea {num_linea}: Parámetros duplicados en función '{nombre}'")

    def _verificar_estructura_control(self, linea, num_linea):
        if re.match(r'^\s*if\s*\(', linea):
            if not re.search(r'\)\s*{?', linea):
                self.errores.append(f"Línea {num_linea}: Falta ')' o '{{' en if")
        if re.search(r'\w+\[\d+\]', linea):
            variable = re.search(r'(\w+)\[\d+\]', linea).group(1)
            if variable not in self.variables:
                self.errores.append(f"Línea {num_linea}: Variable '{variable}' no declarada")

        elif re.match(r'^\s*for\s*\(', linea):
            if not re.search(r'for\s*\([^;]*;[^;]*;[^)]*\)\s*{?', linea):
                self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en for. Debe tener formato: for(inicialización; condición; incremento)")
            
        # Extraer partes del for para validación semántica
        partes_match = re.match(r'for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)', linea)
        if partes_match:
            inicializacion, condicion, incremento = partes_match.groups()
            
            # Verificar si se está utilizando una variable no declarada en la condición
            if condicion.strip():
                variables_en_condicion = re.findall(r'\b([a-zA-Z_]\w*)\b', condicion)
                for var in variables_en_condicion:
                    if var not in self.variables and var not in ('true', 'false'):
                        self.warnings.append(f"Línea {num_linea}: Variable '{var}' posiblemente no declarada en la condición del for")
            else:
                # Verificar que haya else válido si existe
                if 'else' in linea and not re.search(r'else\s*{?', linea):
                    self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en else")

    # sintactico.py - Modificar el método _verificar_estructura_switch
    def _verificar_estructura_switch(self, linea, num_linea):
        if linea.startswith('switch'):
            # Corregir uso de 'expresion' por 'expr_match'
            expr_match = re.match(r'switch\s*\((.*?)\)\s*\{?', linea)  # <-- Corrección aquí
            if not expr_match:
                self.errores.append(f"Línea {num_linea}: Sintaxis incorrecta en switch. Use 'switch(expresión) {{ ... }}'")
                return
            
            # Validar expresión dentro del switch
            expresion_switch = expr_match.group(1).strip()
            if not expresion_switch:
                self.errores.append(f"Línea {num_linea}: Expresión vacía en switch")
            
            # Simular análisis de casos (requiere acceso a self.lineas)
            lineas = getattr(self, 'lineas', [])
            if not lineas:
                return
            
            # Capturar bloque del switch
            balance = 0
            bloque_switch = []
            for i in range(num_linea - 1, len(lineas)):
                ln = lineas[i]
                bloque_switch.append(ln)
                balance += ln.count('{') - ln.count('}')
                if balance == 0:
                    break
            
            # Verificar casos y default
            casos = []
            default_encontrado = False
            for idx, ln in enumerate(bloque_switch):
                ln = ln.strip()
                # Verificar case
                if ln.startswith('case'):
                    caso_match = re.match(r'case\s+(.+?):', ln)
                    if not caso_match:
                        self.errores.append(f"Línea {num_linea + idx}: 'case' mal formado")
                    else:
                        valor = caso_match.group(1)
                        if valor in casos:
                            self.errores.append(f"Línea {num_linea + idx}: Caso duplicado 'case {valor}'")
                        else:
                            casos.append(valor)
                # Verificar default
                elif ln.startswith('default:'):
                    if default_encontrado:
                        self.errores.append(f"Línea {num_linea + idx}: Múltiples 'default' en switch")
                    default_encontrado = True