import tkinter as tk
from tkinter import Menu, Text, Scrollbar, filedialog
from lexico import AnalizadorLexicoJS
from sintactico import AnalizadorSemanticoJS
from semantico import AnalizadorSintacticoJS
from ejecucion import EjecutorJavaScript


def on_menu_click(option):
    console.insert(tk.END, f"Seleccionaste: {option}\n")

def abrir_archivo():
    ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    if ruta_archivo:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, archivo.read())
        console.insert(tk.END, f"File opened: {ruta_archivo}\n")

def guardar_archivo():
    ruta_archivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    if ruta_archivo:
        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(text_area.get(1.0, tk.END))
        console.insert(tk.END, f"File saved: {ruta_archivo}\n")

def limpiar_pantalla():
    text_area.delete(1.0, tk.END)
    console.insert(tk.END, "Screen cleared\n")

def ejecutar_analizador(tipo):
    codigo = text_area.get(1.0, tk.END)
    if tipo == "Analizador Léxico":
        analizador = AnalizadorLexicoJS()
        resultados = analizador.analizar(codigo)
        console.delete(1.0, tk.END)
        console.insert(tk.END, "=== TOKENS ===\n")
        console.insert(tk.END, "\nTokens:\n")
        for token in resultados["tokens"]:
            console.insert(tk.END, f"{token[0]}: {token[1]}\n")
        console.delete(1.0, tk.END)
        for mensaje in resultados["consola"]:
            console.insert(tk.END, f">> {mensaje}\n")
        for warning in resultados["warnings"]:
            console.insert(tk.END, f"WARNING: {warning}\n", "warning")
        for error in resultados["errores"]:
            console.insert(tk.END, f"ERROR: {error}\n", "error")    
        

    elif tipo == "Analizador Sintáctico":
        codigo = text_area.get(1.0, tk.END)
        analizador = AnalizadorSintacticoJS()
        resultados = analizador.analizar(codigo)
        
        console.delete(1.0, tk.END)
        for mensaje in resultados["consola"]:
            console.insert(tk.END, f">> {mensaje}\n")
        for warning in resultados["warnings"]:
            console.insert(tk.END, f"WARNING: {warning}\n", "warning")
        for error in resultados["errores"]:
            console.insert(tk.END, f"ERROR: {error}\n", "error")

    elif tipo == "Ejecutar":
        codigo = text_area.get(1.0, tk.END)
        ejecutor = EjecutorJavaScript()
        ejecutor.ejecutar(codigo)
        resultados = ejecutor.obtener_resultados()
        
        console.delete(1.0, tk.END)
        # Mostrar salida
        console.insert(tk.END, "=== SALIDA ===\n", "output")
        for mensaje in resultados["salida"]:
            # Formatear arrays para mostrarlos como JS
            if isinstance(mensaje, list):
                elementos = []
                for elemento in mensaje:
                    if isinstance(elemento, bool):
                        elementos.append("true" if elemento else "false")
                    elif isinstance(elemento, str):
                        elementos.append(f'"{elemento}"')
                    else:
                        elementos.append(str(elemento))
                console.insert(tk.END, f"[{', '.join(elementos)}]\n", "output")
            else:
                console.insert(tk.END, f"{mensaje}\n", "output")
        
        # Mostrar errores
        console.insert(tk.END, "\n=== ERRORES ===\n", "error")
        for error in resultados["errores"]:
            console.insert(tk.END, f"{error}\n", "error")

        console.insert(tk.END, "\n=== ADVERTENCIAS ===\n", "warning")
        for warning in resultados.get("warnings", []):
            console.insert(tk.END, f"{warning}\n", "warning")


root = tk.Tk()
root.title("Interfaz con Tkinter")
root.geometry("600x400")

menu_bar = Menu(root)
root.config(menu=menu_bar)

archivo_menu = Menu(menu_bar, tearoff=0)
archivo_menu.add_command(label="Abrir", command=abrir_archivo)
archivo_menu.add_command(label="Guardar", command=guardar_archivo)
archivo_menu.add_command(label="Limpiar", command=limpiar_pantalla)
archivo_menu.add_separator()
archivo_menu.add_command(label="Salir", command=root.quit)
menu_bar.add_cascade(label="Archivo", menu=archivo_menu)
ejecutar_menu = Menu(menu_bar, tearoff=0)
ejecutar_menu.add_command(label="Ejecutar código", command=lambda: ejecutar_analizador("Ejecutar"))
menu_bar.add_cascade(label="Ejecutar", menu=ejecutar_menu)

compiladores_menu = Menu(menu_bar, tearoff=0)
compiladores_menu.add_command(label="Analizador Léxico", command=lambda: ejecutar_analizador("Analizador Léxico"))
compiladores_menu.add_command(label="Analizador Sintáctico", command=lambda: ejecutar_analizador("Analizador Sintáctico"))
menu_bar.add_cascade(label="Compiladores", menu=compiladores_menu)

menus = ["Editar", "Ejecutar", "Ayuda", "Variables"]
for menu_name in menus:
    menu = Menu(menu_bar, tearoff=0)
    menu.add_command(label=f"Opción 1 de {menu_name}", command=lambda m=menu_name: on_menu_click(m))
    menu_bar.add_cascade(label=menu_name, menu=menu)

text_area = Text(root, wrap=tk.WORD, height=15)
text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

console_frame = tk.Frame(root)
console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

console_label = tk.Label(console_frame, text="Console:")
console_label.pack(anchor="w")

console = Text(console_frame, wrap=tk.WORD, height=5, bg="black", fg="white")
console.pack(fill=tk.BOTH, expand=True)
console.tag_configure("output", foreground="green")
console.tag_configure("error", foreground="red")

root.mainloop()