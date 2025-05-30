import re 

class EjecutorJavaScript:
    def __init__(self, padre=None):
        self.variables = padre.variables if padre else {}
        self.console_output = []
        self.errores = []
        self.warnings = []
        self.padre = padre  # Contexto superior
        self.funciones = padre.funciones.copy() if padre else {}
        self.return_value = None  # Añadir esta línea


    def ejecutar(self, codigo):
        lineas = [ln.strip() for ln in codigo.split('\n') if ln.strip()]
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            try:
                if linea.startswith('function'):
                    i = self._procesar_funcion(lineas, i)
                elif linea.startswith(('let', 'var')):
                    self._procesar_declaracion(linea, i+1)
                    i += 1
                elif re.match(r'^\s*if\s*\(', linea):
                    i = self._procesar_if(lineas, i)
                elif re.match(r'^\s*switch\s*\(', linea):
                    i = self._procesar_switch(lineas, i)
                elif re.match(r'^\s*for\s*\(', linea):
                    i = self._procesar_for(lineas, i)
                elif re.match(r'^\s*console\.log', linea):
                    self._procesar_console_log(linea, i+1)
                    i += 1
                elif 'return' in linea:
                    expr = linea.split('return')[1].split(';')[0].strip()
                    valor = self._evaluar_expresion(expr, i+1)
                    self.return_value = valor
                    break  # Detener ejecución del bloque actual
                # CORRECCIÓN: Agregar manejo para llamadas a funciones en el nivel superior
                elif re.match(r'^\s*[a-zA-Z_]\w*\s*\(', linea):
                    # Detecta llamadas a funciones
                    nombre_funcion = re.match(r'^\s*([a-zA-Z_]\w*)\s*\(', linea).group(1)
                    args_match = re.search(r'\((.*?)\)', linea)
                    args = []
                    if args_match and args_match.group(1).strip():
                        args = [arg.strip() for arg in args_match.group(1).split(',')]
                    if nombre_funcion in self.funciones:
                        # CORRECCIÓN: Capturar el valor retornado y manejarlo adecuadamente
                        valor_retorno = self._llamar_funcion(nombre_funcion, args, i+1)
                        # Si la función retornó un valor, deberías manejarlo según corresponda
                        if valor_retorno is not None:
                            self.return_value = valor_retorno
                    else:
                        self.errores.append(f"Línea {i+1}: Función '{nombre_funcion}' no definida")
                    i += 1
                else:
                    # Manejar asignaciones de variables existentes
                    if re.match(r'^\s*[a-zA-Z_]\w*\s*=', linea):
                        self._procesar_asignacion(linea, i+1)
                    i += 1
            except Exception as e:
                self.errores.append(f"Línea {i+1}: {str(e)}")
                i += 1

    def _procesar_for(self, lineas, index):
        for_line = lineas[index]
        match = re.match(r'for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)\s*{?', for_line)
        
        if not match:
            self.errores.append(f"Línea {index+1}: Sintaxis incorrecta en for")
            return index + 1
        
        inicializacion, condicion, incremento = match.groups()
        
        # Crear un nuevo ámbito para el bucle for
        contexto_for = EjecutorJavaScript(padre=self)
        
        # Procesar inicialización
        if inicializacion:
            if re.match(r'^(let|var|const)\s+', inicializacion):
                contexto_for._procesar_declaracion(f"{inicializacion};", index+1)
            else:
                var_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', inicializacion)
                if var_match:
                    var_name, expr = var_match.groups()
                    if var_name in self.variables:
                        valor = self._evaluar_expresion(expr, index+1)
                        contexto_for.variables[var_name] = valor
                    else:
                        self.errores.append(f"Línea {index+1}: Variable '{var_name}' no declarada")
        
        # Capturar bloque del for
        bloque_for, next_line = self._capturar_bloque(lineas, index)
        
        # Límite de seguridad para evitar bucles infinitos
        max_iteraciones = 1000
        iteraciones = 0
        
        # Ejecutar el bucle
        while True:
            # Evaluar condición
            if condicion:
                resultado_condicion = contexto_for._evaluar_expresion(condicion, index+1)
                if not resultado_condicion:
                    break
            
            # Crear un nuevo contexto para cada iteración manteniendo el estado de las variables
            iteracion_contexto = EjecutorJavaScript(padre=contexto_for)
            iteracion_contexto.variables = contexto_for.variables.copy()
            
            # Ejecutar el bloque dentro del contexto de la iteración
            iteracion_contexto.ejecutar('\n'.join(bloque_for))
            
            # Actualizar el contexto del for con los cambios de esta iteración
            contexto_for.variables.update(iteracion_contexto.variables)
            contexto_for.console_output.extend(iteracion_contexto.console_output)
            contexto_for.errores.extend(iteracion_contexto.errores)
            contexto_for.warnings.extend(iteracion_contexto.warnings)
            
            # Procesar incremento
            if incremento:
                # Incremento ++/--
                inc_match = re.match(r'^([a-zA-Z_]\w*)\s*(\+\+|--)$', incremento)
                if inc_match:
                    var_name, operador = inc_match.groups()
                    if var_name in contexto_for.variables:
                        if operador == '++':
                            contexto_for.variables[var_name] += 1
                        else:  # --
                            contexto_for.variables[var_name] -= 1
                # Operación compuesta (+=, -=, etc.)
                else:
                    inc_match = re.match(r'^([a-zA-Z_]\w*)\s*([+\-*/])=\s*(.+)$', incremento)
                    if inc_match:
                        var_name, op, expr = inc_match.groups()
                        if var_name in contexto_for.variables:
                            valor = contexto_for._evaluar_expresion(expr, index+1)
                            if op == '+':
                                contexto_for.variables[var_name] += valor
                            elif op == '-':
                                contexto_for.variables[var_name] -= valor
                            elif op == '*':
                                contexto_for.variables[var_name] *= valor
                            elif op == '/':
                                contexto_for.variables[var_name] /= valor
                    # Asignación simple
                    else:
                        inc_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', incremento)
                        if inc_match:
                            var_name, expr = inc_match.groups()
                            if var_name in contexto_for.variables:
                                contexto_for.variables[var_name] = contexto_for._evaluar_expresion(expr, index+1)
            
            # Control de límite para evitar bucles infinitos
            iteraciones += 1
            if iteraciones >= max_iteraciones:
                self.errores.append(f"Línea {index+1}: Posible bucle infinito detectado en for (limitado a {max_iteraciones} iteraciones)")
                break
        
        # Actualizar el contexto padre con las variables modificadas
        self.variables.update(contexto_for.variables)
        self.console_output.extend(contexto_for.console_output)
        self.errores.extend(contexto_for.errores)
        self.warnings.extend(contexto_for.warnings)
        
        return next_line
    
    def _procesar_funcion(self, lineas, index):
        linea = lineas[index]
        match = re.match(r'function\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*\{?', linea)
        nombre = match.group(1)
        parametros = [p.strip() for p in match.group(2).split(',') if p.strip()]
        
        # Capturar cuerpo de la función
        bloque, next_line = self._capturar_bloque(lineas, index)
        self.funciones[nombre] = {
            'parametros': parametros,
            'bloque': bloque,
            'contexto': self  # Guardar contexto de declaración
        }
        return next_line
    
    def _procesar_declaracion(self, linea, num_linea):
        match = re.match(r'^(let|var|const)\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+?))?;?$', linea)
        if not match:
            self.errores.append(f"Línea {num_linea}: Declaración inválida: '{linea}'")
            return
        
        tipo_decl, nombre_var, expr = match.groups()
        if tipo_decl == 'const' and not expr:
            self.errores.append(f"Línea {num_linea}: 'const' debe inicializarse con un valor")
        
        # Solo verificar redeclaración para 'let' y 'const' en el mismo ámbito
        if nombre_var in self.variables and self is not self.padre and tipo_decl != 'var':
            if tipo_decl == 'const':
                self.errores.append(f"Línea {num_linea}: No se puede redeclarar 'const {nombre_var}'")
            else:
                self.warnings.append(f"Línea {num_linea}: Redeclaración de variable '{nombre_var}'")
        
        # Si hay una expresión, evaluar su valor
        if expr:
            valor = self._evaluar_expresion(expr, num_linea)
            self.variables[nombre_var] = valor
        else:
            # En JavaScript, variables no inicializadas son undefined
            self.variables[nombre_var] = None  # None equivale a undefined en nuestro contexto
            
    def _llamar_funcion(self, nombre, argumentos, num_linea):
        if nombre not in self.funciones:
            raise NameError(f"Función '{nombre}' no definida")
        
        func = self.funciones[nombre]
        # CORRECCIÓN: verificar que los argumentos sean suficientes pero permitir menos argumentos que parámetros
        # (comportamiento de JavaScript - los argumentos faltantes son 'undefined')
        if len(argumentos) > len(func['parametros']):
            self.warnings.append(f"Línea {num_linea}: Demasiados argumentos para '{nombre}'")
        
        # Crear nuevo contexto
        contexto_func = EjecutorJavaScript(padre=self)  # Usar self como padre permite acceder a variables globales
        
        # Asignar valores a los parámetros
        for i, param in enumerate(func['parametros']):
            if i < len(argumentos):
                contexto_func.variables[param] = self._evaluar_expresion(argumentos[i], num_linea)
            else:
                contexto_func.variables[param] = None  # undefined en JavaScript
        
        # Ejecutar bloque
        contexto_func.ejecutar('\n'.join(func['bloque']))
        
        # CORRECCIÓN: Propagar la salida de la consola y errores
        self.console_output.extend(contexto_func.console_output)
        self.errores.extend(contexto_func.errores)
        self.warnings.extend(contexto_func.warnings)
        
        # Obtener valor de retorno
        return contexto_func.return_value

    # Método _procesar_switch (modificado)

    def _procesar_switch(self, lineas, index):
        switch_line = lineas[index]
        expr_match = re.match(r'switch\s*\((.*?)\)\s*{?', switch_line)
        if not expr_match:
            self.errores.append(f"Línea {index+1}: Sintaxis incorrecta en switch")
            return index + 1

        # Evaluar la expresión del switch
        expresion = self._evaluar_expresion(expr_match.group(1), index+1)

        # Capturar bloque completo del switch
        bloque_switch, next_line = self._capturar_bloque(lineas, index)

        # Crear nuevo contexto para el switch
        contexto_switch = EjecutorJavaScript(padre=self)
        contexto_switch.variables = self.variables.copy()  

        # Variables para control de flujo
        ejecutando = False
        caso_ejecutado = False  # Nueva variable para rastrear sialgún caso coincidió
        i = 0
        salir_switch = False
        while i < len(bloque_switch) and not salir_switch:
            linea = bloque_switch[i].strip()

            if linea.startswith('case'):
                case_match = re.search(r'case\s+(.+?):', linea)
                if case_match:
                    valor_case = self._evaluar_expresion(case_match.group(1), index+i+1)
                    if valor_case == expresion and not caso_ejecutado:
                        ejecutando = True
                        caso_ejecutado = True  # Marcar que se encontró un caso coincidente
                    i += 1
                else:
                    i += 1
            elif linea.startswith('default:'):
                if not caso_ejecutado:  # Solo ejecutar default si ningún case coincidió
                    ejecutando = True
                i += 1
            elif 'break;' in linea and ejecutando:
                salir_switch = True  # Salir del switch en lugar de solo detener la ejecución
                i += 1
                continue  # Usar continue en lugar de break para permitir que se actualice el contexto
            elif ejecutando:
                # Procesar líneas dentro de un case activo
                if linea.startswith('console.log'):
                    contexto_switch._procesar_console_log(linea, index+i+1)
                    i += 1
                elif re.match(r'^(let|var|const)\s+', linea):
                    contexto_switch._procesar_declaracion(linea, index+i+1)
                    i += 1
                elif re.match(r'^[a-zA-Z_]\w*\s*=', linea):
                    contexto_switch._procesar_asignacion(linea, index+i+1)
                    i += 1
                elif re.match(r'^\s*for\s*\(', linea):
                    # Procesar for dentro del switch
                    sub_index = i
                    i = contexto_switch._procesar_for(bloque_switch, sub_index)
                elif not linea or linea.startswith('//'):
                    i += 1
                else:
                    i += 1
            else:
                i += 1

        # Actualizar el contexto padre con las variables y salidas (se mueve después del bucle)
        self.variables.update(contexto_switch.variables)
        self.console_output.extend(contexto_switch.console_output)
        self.errores.extend(contexto_switch.errores)
        self.warnings.extend(contexto_switch.warnings)

        return next_line

    def _procesar_for(self, lineas, index):
        for_line = lineas[index]
        match = re.match(r'for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)\s*{?', for_line)
        
        if not match:
            self.errores.append(f"Línea {index+1}: Sintaxis incorrecta en for")
            return index + 1
        
        inicializacion, condicion, incremento = match.groups()
        
        # Crear un nuevo contexto para el bucle for
        contexto_for = EjecutorJavaScript(padre=self)
        contexto_for.variables = self.variables.copy()  # Compartir variables con el contexto padre
        
        # Procesar inicialización
        if inicializacion:
            if re.match(r'^(let|var|const)\s+', inicializacion):
                contexto_for._procesar_declaracion(f"{inicializacion};", index+1)
            else:
                var_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', inicializacion)
                if var_match:
                    var_name, expr = var_match.groups()
                    valor = contexto_for._evaluar_expresion(expr, index+1)
                    contexto_for.variables[var_name] = valor
        
        # Capturar bloque del for
        bloque_for, next_line = self._capturar_bloque(lineas, index)
        
        # Límite de seguridad para evitar bucles infinitos
        max_iteraciones = 1000
        iteraciones = 0
        
        # Ejecutar el bucle
        while True:
            # Evaluar condición
            if condicion:
                resultado_condicion = contexto_for._evaluar_expresion(condicion, index+1)
                if not resultado_condicion:
                    break
            
            # Ejecutar bloque del for en un contexto temporal
            iteracion_contexto = EjecutorJavaScript(padre=contexto_for)
            iteracion_contexto.variables = contexto_for.variables.copy()
            iteracion_contexto.ejecutar('\n'.join(bloque_for))
            
            # Actualizar el contexto del for con los cambios de esta iteración
            contexto_for.variables.update(iteracion_contexto.variables)
            contexto_for.console_output.extend(iteracion_contexto.console_output)
            contexto_for.errores.extend(iteracion_contexto.errores)
            contexto_for.warnings.extend(iteracion_contexto.warnings)
            
            # Procesar incremento
            if incremento:
                # Incremento ++/--
                inc_match = re.match(r'^([a-zA-Z_]\w*)\s*(\+\+|--)$', incremento)
                if inc_match:
                    var_name, operador = inc_match.groups()
                    if operador == '++':
                        contexto_for.variables[var_name] += 1
                    else:  # --
                        contexto_for.variables[var_name] -= 1
                # Asignación simple
                else:
                    inc_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', incremento)
                    if inc_match:
                        var_name, expr = inc_match.groups()
                        contexto_for.variables[var_name] = contexto_for._evaluar_expresion(expr, index+1)
            
            # Control de límite para evitar bucles infinitos
            iteraciones += 1
            if iteraciones >= max_iteraciones:
                self.errores.append(f"Línea {index+1}: Posible bucle infinito detectado en for (limitado a {max_iteraciones} iteraciones)")
                break
        
        # Actualizar el contexto padre con las variables modificadas
        self.variables.update(contexto_for.variables)
        self.console_output.extend(contexto_for.console_output)
        self.errores.extend(contexto_for.errores)
        self.warnings.extend(contexto_for.warnings)
        
        return next_line
    
    def _procesar_if(self, lineas, index):
        if_line = lineas[index]
        cond_match = re.match(r'if\s*\((.*?)\)\s*', if_line)
        
        if not cond_match:
            self.errores.append(f"Línea {index+1}: Sintaxis incorrecta en if")
            return index + 1

        condicion = cond_match.group(1)
        resultado = self._evaluar_expresion(condicion, index+1)
        
        # Crear contexto para el if (pero manteniendo el mismo ámbito para variables)
        # IMPORTANTE: Usamos self como padre pero copiamos las variables actuales
        contexto_if = EjecutorJavaScript(padre=self)
        contexto_if.variables = self.variables.copy()  # Compartir las mismas variables
        
        # Capturar bloque del if
        bloque_if, next_line = self._capturar_bloque(lineas, index)
        
        # Ejecutar bloque si la condición es verdadera
        if resultado:
            contexto_if.ejecutar('\n'.join(bloque_if))
            # Actualizar las variables del ámbito actual con las del contexto if
            self.variables.update(contexto_if.variables)
            self.console_output.extend(contexto_if.console_output)
            
            # Propagar return_value si existe
            if contexto_if.return_value is not None:
                self.return_value = contexto_if.return_value
        
        # Determinar si hay else (solo si está inmediatamente después)
        has_else = False
        bloque_else = []
        if next_line < len(lineas) and re.match(r'^\s*else\b', lineas[next_line]):
            has_else = True
            # Comprobar si es un "else if"
            if re.search(r'else\s+if\s*\(', lineas[next_line]):
                # Procesar recursivamente el else if
                if not resultado:  # Solo si la condición del if original es falsa
                    next_line = self._procesar_if(lineas, next_line)
            else:
                # Es un else normal
                bloque_else, next_line = self._capturar_bloque(lineas, next_line)
                if not resultado:
                    contexto_else = EjecutorJavaScript(padre=self)
                    contexto_else.variables = self.variables.copy()  # Compartir variables
                    contexto_else.ejecutar('\n'.join(bloque_else))
                    # Actualizar variables y salidas
                    self.variables.update(contexto_else.variables)
                    self.console_output.extend(contexto_else.console_output)
                    
                    # Propagar return_value si existe
                    if contexto_else.return_value is not None:
                        self.return_value = contexto_else.return_value
        
        return next_line

    def _capturar_bloque(self, lineas, index):
        current_line = lineas[index]
        
        # Manejo especial para if statements de una sola línea
        if re.match(r'^\s*if\s*\(.*\)\s*\w', current_line) and '{' not in current_line:
            # Si el if tiene una instrucción en la misma línea
            statement = re.sub(r'^\s*if\s*\(.*?\)\s*', '', current_line).strip()
            if statement:
                return [statement], index + 1
        
        if '{' not in current_line:
            # Capturar toda la línea como bloque si termina en ;
            if ';' in current_line:
                return [current_line.split(';')[0].strip()], index + 1
            else:
                # Si es una estructura de control sin llaves, capturar la siguiente línea
                if index + 1 < len(lineas):
                    return [lineas[index + 1].strip()], index + 2
                else:
                    return [], index + 1
        
        # Resto del código original para bloques con llaves
        balance = current_line.count('{')
        start = index + 1
        end = start
        
        # Buscar el cierre del bloque
        while end < len(lineas) and balance > 0:
            balance += lineas[end].count('{')
            balance -= lineas[end].count('}')
            end += 1
            
            # Si ya procesamos toda la última línea y aún falta cerrar llaves
            if end == len(lineas) and balance > 0:
                self.errores.append(f"Línea {index+1}: Llaves sin cerrar al final del código")
                break
        
        # Si la última llave está en la misma línea que otra instrucción, incluirla
        if end > start and balance == 0 and end <= len(lineas):
            bloque = lineas[start:end-1]
            # Verificar si la última línea tiene código antes de la llave de cierre
            ultima_linea = lineas[end-1]
            ultima_sin_llave = ultima_linea.split('}')[0].strip()
            if ultima_sin_llave:
                bloque.append(ultima_sin_llave)
            return bloque, end
        
        return lineas[start:end], end

    def _capturar_bloque_desde_indice(self, lineas, index):
        # Similar a _capturar_bloque pero trabaja con índices dentro de un bloque ya capturado
        current_line = lineas[index]
        
        # Si no hay llave abierta, considera la siguiente línea como bloque (if sin llaves)
        if '{' not in current_line:
            # Para estructuras sin llaves, solo toma la siguiente línea
            if index + 1 < len(lineas):
                return [lineas[index + 1]], index + 2
            else:
                return [], index + 1
        
        # Calcular el balance de llaves
        balance = current_line.count('{')
        start = index + 1
        end = start
        
        # Buscar el cierre del bloque
        while end < len(lineas) and balance > 0:
            balance += lineas[end].count('{')
            balance -= lineas[end].count('}')
            end += 1
        
        return lineas[start:end], end
        
    def _evaluar_expresion(self, expr, num_linea):
        try:
            # Manejar valores especiales de JavaScript
            expr = expr.strip()
            if expr == 'undefined':
                return None  # Corregir evaluación de 'undefined'
            
            # Manejar acceso a la propiedad length de arrays y strings
            length_match = re.match(r'^(\w+)\.length$', expr)
            if length_match:
                var_name = length_match.group(1)
                if var_name in self.variables:
                    if isinstance(self.variables[var_name], list) or isinstance(self.variables[var_name], str):
                        return len(self.variables[var_name])
                    else:
                        self.errores.append(f"Línea {num_linea}: La propiedad 'length' solo es válida para arrays y strings")
                        return 0
                else:
                    # Variable no definida
                    self.errores.append(f"Línea {num_linea}: Variable '{var_name}' no definida")
                    return 0
                    
            # Manejar acceso a propiedades de objetos
            prop_match = re.match(r'^(\w+)\.(\w+)$', expr)
            if prop_match:
                var_name, prop_name = prop_match.groups()
                if var_name in self.variables:
                    if isinstance(self.variables[var_name], dict):
                        if prop_name in self.variables[var_name]:
                            return self.variables[var_name][prop_name]
                        else:
                            # Propiedad no existe
                            return None
                    else:
                        # No es un objeto, no tiene propiedades
                        self.errores.append(f"Línea {num_linea}: '{var_name}' no es un objeto")
                        return None
                else:
                    self.errores.append(f"Línea {num_linea}: Variable '{var_name}' no definida")
                    return None
                    
            # Manejar null
            if expr == 'null':
                return None
                
            # Manejar booleanos
            if expr.lower() == 'true':
                return True
            if expr.lower() == 'false':
                return False
            
            # Manejar cadenas vacías
            if expr == '""' or expr == "''":
                return ""

            # Manejar llamadas a funciones
            func_call = re.match(r'(\w+)\((.*)\)', expr)
            if func_call:
                nombre = func_call.group(1)
                # Dividir los argumentos correctamente
                args = []
                if func_call.group(2).strip():
                    args_raw = func_call.group(2)
                    nivel_parentesis = 0
                    nivel_corchetes = 0
                    comilla_actual = None
                    arg_actual = ""
                    
                    for c in args_raw:
                        if c == '(':
                            nivel_parentesis += 1
                            arg_actual += c
                        elif c == ')':
                            nivel_parentesis -= 1
                            arg_actual += c
                        elif c == '[':
                            nivel_corchetes += 1
                            arg_actual += c
                        elif c == ']':
                            nivel_corchetes -= 1
                            arg_actual += c
                        elif c in ("'", '"'):
                            if comilla_actual is None:
                                comilla_actual = c
                            elif c == comilla_actual:
                                comilla_actual = None
                            arg_actual += c
                        elif c == ',' and nivel_parentesis == 0 and nivel_corchetes == 0 and comilla_actual is None:
                            args.append(arg_actual.strip())
                            arg_actual = ""
                        else:
                            arg_actual += c
                    
                    if arg_actual.strip():
                        args.append(arg_actual.strip())
                
                return self._llamar_funcion(nombre, args, num_linea)

            # Manejar arrays
            if expr.startswith('[') and expr.endswith(']'):
                if len(expr) <= 2:  # Array vacío []
                    return []
                    
                elementos = []
                contenido_array = expr[1:-1].strip()
                
                nivel_corchetes = 0
                nivel_llaves = 0
                comilla_actual = None
                elemento_actual = ""
                
                for c in contenido_array:
                    if c == '[':
                        nivel_corchetes += 1
                        elemento_actual += c
                    elif c == ']':
                        nivel_corchetes -= 1
                        elemento_actual += c
                    elif c == '{':
                        nivel_llaves += 1
                        elemento_actual += c
                    elif c == '}':
                        nivel_llaves -= 1
                        elemento_actual += c
                    elif c in ("'", '"'):
                        if comilla_actual is None:
                            comilla_actual = c
                        elif c == comilla_actual:
                            comilla_actual = None
                        elemento_actual += c
                    elif c == ',' and nivel_corchetes == 0 and nivel_llaves == 0 and comilla_actual is None:
                        elementos.append(self._evaluar_expresion(elemento_actual.strip(), num_linea))
                        elemento_actual = ""
                    else:
                        elemento_actual += c
                        
                if elemento_actual.strip():
                    elementos.append(self._evaluar_expresion(elemento_actual.strip(), num_linea))
                    
                return elementos
            
            # Manejar acceso a arrays
            array_index_match = re.match(r'^(\w+)\[(\d+)\]', expr)
            if array_index_match:
                var_name, idx = array_index_match.groups()
                idx = int(idx)
                if var_name in self.variables:
                    if isinstance(self.variables[var_name], (list, str)):
                        if 0 <= idx < len(self.variables[var_name]):
                            return self.variables[var_name][idx]
                        else:
                            # Generar error por desbordamiento
                            self.errores.append(f"Línea {num_linea}: Índice {idx} fuera de rango para '{var_name}' (longitud {len(self.variables[var_name])})")
                            return None
                    else:
                        self.errores.append(f"Línea {num_linea}: '{var_name}' no es un array o cadena")
                        return None
                else:
                    self.errores.append(f"Línea {num_linea}: Variable '{var_name}' no definida")
                    return None
            
            # Manejar cadenas de texto literales
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                return expr[1:-1]  # Eliminar comillas y devolver contenido
            
            # Manejar objetos (simplificado)
            if expr.startswith('{') and expr.endswith('}'):
                # Para este ejemplo, simplemente creamos un diccionario Python
                # En una implementación más completa, analizaríamos la estructura del objeto
                try:
                    # Extraer pares clave:valor del objeto
                    contenido = expr[1:-1].strip()
                    objeto = {}
                    
                    # Análisis básico de objetos
                    if contenido:
                        # Dividir por comas
                        pares = re.split(r',(?![^{]*})', contenido)
                        for par in pares:
                            if ':' in par:
                                clave, valor = par.split(':', 1)
                                clave = clave.strip().strip('"').strip("'")
                                valor = valor.strip()
                                
                                # Evaluar el valor
                                if valor.startswith('"') and valor.endswith('"'):
                                    objeto[clave] = valor[1:-1]
                                elif valor.startswith("'") and valor.endswith("'"):
                                    objeto[clave] = valor[1:-1]
                                elif valor.isdigit():
                                    objeto[clave] = int(valor)
                                elif valor.replace('.', '', 1).isdigit():
                                    objeto[clave] = float(valor)
                                elif valor.lower() in ('true', 'false'):
                                    objeto[clave] = valor.lower() == 'true'
                                elif valor == 'null':
                                    objeto[clave] = None
                                else:
                                    # Para valores más complejos, dejar como string
                                    objeto[clave] = valor
                    
                    return objeto
                except Exception as e:
                    # Si falla el análisis, devolver el objeto como string
                    return expr
            
            # Manejar variables en la expresión
            expr_sin_cadenas = re.sub(r'"[^"]*"|\'[^\']*\'', '', expr)
            variables_en_expr = re.findall(r'\b([a-zA-Z_]\w*)\b', expr_sin_cadenas)
            
            expr_mod = expr
            for var in sorted(self.variables.keys(), key=len, reverse=True):
                # Solo reemplazar si es un nombre de variable completo, no parte de otra
                expr_mod = re.sub(rf'\b{var}\b', self._representar_valor(self.variables[var]), expr_mod)
            
            variables_en_expr = re.findall(r'\b([a-zA-Z_]\w*)\b', expr_sin_cadenas)
            for var in variables_en_expr:
                if var not in self.variables:
                    return None  # Tratar variables no declaradas como None (undefined
            # Comparación de igualdad == (manejo especial para null, undefined y cadenas vacías)
            if '==' in expr and '===' not in expr and '!==' not in expr:
                partes = expr.split('==')
                if len(partes) == 2:
                    parte1 = self._evaluar_expresion(partes[0].strip(), num_linea)
                    parte2 = self._evaluar_expresion(partes[1].strip(), num_linea)
                    
                    # Tratar null y undefined (None) como equivalentes en ==
                    if parte1 is None and (parte2 is None or parte2 == ""):
                        return True
                    if parte2 is None and (parte1 is None or parte1 == ""):
                        return True
                    
                    # Cadena vacía == null/undefined es true en JS
                    if parte1 == "" and parte2 is None:
                        return True
                    if parte2 == "" and parte1 is None:
                        return True
                    
                    # Comparación normal
                    return parte1 == parte2
            
            # Manejar otros operadores de comparación
            expr_mod = expr_mod.replace('===', '==').replace('!==', '!=')
            if '===' in expr:
                partes = expr.split('===')
                parte1 = self._evaluar_expresion(partes[0].strip(), num_linea)
                parte2 = self._evaluar_expresion(partes[1].strip(), num_linea)
                return parte1 == parte2 and type(parte1) == type(parte2)
            elif '!==' in expr:
                partes = expr.split('!==')
                parte1 = self._evaluar_expresion(partes[0].strip(), num_linea)
                parte2 = self._evaluar_expresion(partes[1].strip(), num_linea)
                return parte1 != parte2 or type(parte1) != type(parte2)
            
            # Manejar concatenación de strings con +
            if '+' in expr and not expr.startswith('+') and not expr.endswith('+'):
                try:
                    # Intentar evaluar normalmente
                    return eval(expr_mod)
                except:
                    # Si falla, puede ser una concatenación de strings
                    partes = expr.split('+')
                    resultado = ""
                    for parte in partes:
                        valor = self._evaluar_expresion(parte.strip(), num_linea)
                        resultado += str(valor) if valor is not None else "undefined"
                    return resultado
            
            # Intentar evaluar normalmente
            try:
                return eval(expr_mod)
            except Exception as e:
                self.errores.append(f"Línea {num_linea}: Error al evaluar expresión '{expr}' - {str(e)}")
                return None
                
        except TypeError as e:
            error_msg = str(e)
            # Manejar errores de concatenación str + int
            if 'unsupported operand type(s) for +' in error_msg or 'can only concatenate str' in error_msg:
                partes = expr.split('+')
                if len(partes) == 2:
                    parte1 = self._evaluar_expresion(partes[0].strip(), num_linea)
                    parte2 = self._evaluar_expresion(partes[1].strip(), num_linea)
                    return str(parte1) + str(parte2)
            self.errores.append(f"Línea {num_linea}: Error al evaluar expresión '{expr}' - {error_msg}")
            return None
        except Exception as e:
            self.errores.append(f"Línea {num_linea}: Error al evaluar expresión '{expr}' - {str(e)}")
            return None
            
            
    def _representar_valor(self, valor):
        """Convierte un valor a su representación en string para eval()"""
        if isinstance(valor, str):
            # Escapar comillas dentro de la cadena
            valor_escapado = valor.replace("'", "\\'").replace('"', '\\"')
            return f"'{valor_escapado}'"
        elif valor is None:
            return "None"
        elif isinstance(valor, list):
            elementos = [self._representar_valor(elem) for elem in valor]
            return f"[{', '.join(elementos)}]"
        elif isinstance(valor, dict):
            # Representar objetos como diccionarios
            pares = []
            for k, v in valor.items():
                clave_repr = self._representar_valor(k) if isinstance(k, str) else str(k)
                valor_repr = self._representar_valor(v)
                pares.append(f"{clave_repr}: {valor_repr}")
            return f"{{{', '.join(pares)}}}"
        else:
            return str(valor)

    def _procesar_asignacion(self, linea, num_linea):
        # Manejar asignación simple (x = y)
        match = re.match(r'([a-zA-Z_]\w*)\s*=\s*(.+?);?', linea)
        if match:
            var, expr = match.groups()
            if var in self.variables:
                valor = self._evaluar_expresion(expr, num_linea)
                if valor is not None:
                    self.variables[var] = valor
            else:
                self.errores.append(f"Línea {num_linea}: Variable '{var}' no declarada")
                
        # Manejar asignaciones compuestas (x += y, x -= y, etc.)
        elif re.match(r'([a-zA-Z_]\w*)\s*([+\-*/])=\s*(.+?);?', linea):
            match = re.match(r'([a-zA-Z_]\w*)\s*=\s*(.+?);?', linea)
            var, op, expr = match.groups()
            
            if var in self.variables:
                valor = self._evaluar_expresion(expr, num_linea)
                if valor is not None:
                    if op == '+':
                        self.variables[var] += valor
                    elif op == '-':
                        self.variables[var] -= valor
                    elif op == '*':
                        self.variables[var] *= valor
                    elif op == '/':
                        if valor == 0:
                            self.errores.append(f"Línea {num_linea}: División por cero")
                        else:
                            self.variables[var] /= valor
            else:
                self.errores.append(f"Línea {num_linea}: Variable '{var}' no declarada")
        else:
            self.errores.append(f"Línea {num_linea}: Asignación inválida: '{linea}'")

    def _procesar_console_log(self, linea, num_linea):
        if not re.search(r'console\.log\(', linea):
            self.errores.append(f"Línea {num_linea}: 'console.log' mal escrito o falta '.'")
            return
                
        match = re.search(r'console\.log\((.*?)\);?', linea)
        if match:
            contenido = match.group(1)
                
            # Manejar argumentos múltiples separados por coma
            args = []
            current_arg = []
            dentro_cadena = False
            comilla = None
            level = 0  # Para manejar paréntesis anidados
                
            for c in contenido:
                if c in ('"', "'") and (not dentro_cadena or comilla == c):
                    dentro_cadena = not dentro_cadena
                    if dentro_cadena:
                        comilla = c
                    current_arg.append(c)
                elif c == '(' and not dentro_cadena:
                    level += 1
                    current_arg.append(c)
                elif c == ')' and not dentro_cadena:
                    level -= 1
                    current_arg.append(c)
                elif c == ',' and not dentro_cadena and level == 0:
                    args.append(''.join(current_arg).strip())
                    current_arg = []
                else:
                    current_arg.append(c)
                
            if current_arg:
                args.append(''.join(current_arg).strip())
                
            # Procesar cada argumento
            resultados = []
            for arg in args:
                # Manejar concatenación con +
                if '+' in arg and not (arg.startswith('"') and arg.endswith('"')) and not (arg.startswith("'") and arg.endswith("'")):
                    partes = re.split(r'\s*\+\s*', arg)
                    valores_partes = []
                    for parte in partes:
                        parte = parte.strip()
                        try:
                            valor = self._evaluar_expresion(parte, num_linea)
                            valores_partes.append(str(valor) if valor is not None else "undefined")
                        except Exception as e:
                            valores_partes.append("undefined")
                    # Unir todas las partes evaluadas (concatenación)
                    resultados.append("".join(valores_partes))
                elif (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                    # Extraer cadena literal
                    resultados.append(arg[1:-1])
                else:
                    try: 
                        valor = self._evaluar_expresion(arg, num_linea)
                        if valor is None:
                            resultados.append("undefined")
                        elif isinstance(valor, dict):
                            # Formatear objetos para console.log
                            pares = []
                            for k, v in valor.items():
                                val_str = f'"{v}"' if isinstance(v, str) else str(v)
                                if isinstance(v, bool):
                                    val_str = "true" if v else "false"
                                pares.append(f'{k}: {val_str}')
                            resultados.append(f"{{{', '.join(pares)}}}")
                        else:
                            resultados.append(str(valor))
                    except Exception as e:
                        resultados.append("undefined")
                
            # Unir resultados con espacio (emulando el comportamiento de console.log)
            self.console_output.append(" ".join(resultados))
        else:
            self.errores.append(f"Línea {num_linea}: console.log mal formado")

    def _verificar_estructura_switch_ejecucion(self, lineas, index):
        """
        Verifica la estructura de un bloque switch para su correcta ejecución
        """
        switch_line = lineas[index]
        expr_match = re.match(r'switch\s*\((.*?)\)\s*{?', switch_line)
        
        if not expr_match:
            self.errores.append(f"Línea {index+1}: Sintaxis incorrecta en switch")
            return index + 1, []
            
        # Capturar bloque completo del switch
        bloque_switch, next_line = self._capturar_bloque(lineas, index)
        
        # Verificar que el bloque tenga al menos un caso
        tiene_casos = False
        for linea in bloque_switch:
            if re.match(r'^\s*case\s+', linea) or re.match(r'^\s*default\s*:', linea):
                tiene_casos = True
                break
                
        if not tiene_casos:
            self.errores.append(f"Línea {index+1}: El switch no contiene ningún caso")
            
        return next_line, bloque_switch

    def obtener_resultados(self):
        return {
            "salida": self.console_output,
            "errores": self.errores,
            "warnings": self.warnings,
            "variables": self.variables,
            "return_value": self.return_value  # Añadir esta línea
        }