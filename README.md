# JavaScript Interpreter with GUI
## Interpreter GUI

This project is a JavaScript interpreter with a graphical interface that allows you to analyze and execute basic JavaScript code. It includes modules for lexical analysis, syntax analysis, semantic analysis, and code execution.

## Main Features
Lexical Analysis: Identifies tokens and detects basic errors

- **Syntax Analysis**: Verifies the structure of the code

- **Semantic Analysis**: Checks the program's consistency

- **Execution**: Interprets and runs JavaScript code

- **Graphical Interface**: Allows for easy code editing, saving, and execution

## System Requirements
Python 3.6 or higher

Required libraries:

- Tkinter (usually included with Python)

- No additional external libraries required

## Test code
Try adding these codes to test the compiler
### Nested structure
```bash
function procesarDatos(nombre) {
    var permitido = false;
    var nombre0 = "Ana";
    var nombre1 = "Luis";
    var nombre2 = "Carlos";
    var nombre3 = "Raymond";

    if (nombre === nombre0) permitido = true;
    if (nombre === nombre1) permitido = true;
    if (nombre === nombre2) permitido = true;
    if (nombre === nombre3) permitido = true;

    if (permitido) {
        console.log("Nombre permitido.");
    } else {
        console.log("Nombre NO permitido.");
        return;
    }

    switch (nombre) {
        case "Ana":
            console.log("Hola Ana");
            for (var i = 0; i < 2; i++) {
                console.log("Repetición " + i);
            }
            break;
        case "Luis":
            console.log("Hola Luis");
            for (var i = 0; i < 2; i++) {
                console.log("Repetición " + i);
            }
            break;
        case "Carlos":
            console.log("Hola Carlos");
            for (var i = 0; i < 2; i++) {
                console.log("Repetición " + i);
            }
            break;
        case "Raymond":
            console.log("Hola Raymond");
            for (var i = 0; i < 2; i++) {
                console.log("Repetición " + i);
            }
            break;
        default:
            console.log("Nombre no reconocido.");
    }
}

procesarDatos("Raymond");
   ```

### Arrays
```bash
var frutas = ["manzana", "banana", "naranja", "uva"];
var seleccion = frutas[2]; 

switch (seleccion) {
  case "manzana":
    console.log("Elegiste una manzana");
    break;
  case "banana":
    console.log("Elegiste una banana");
    break;
  case "naranja":
    console.log("Elegiste una naranja ");
    break;
  case "uva":
    console.log("Elegiste una uva");
    break;
  default:
    console.log("Fruta no reconocida");
}
```
```bash
var cosas = ["texto", 42, true, null, {nombre: "Ray"}, [1, 2, 3]];

console.log(cosas[0]); // "texto" (string)
console.log(cosas[1]); // 42 (number)
console.log(cosas[2]); // true (boolean)
console.log(cosas[3]); // null
console.log(cosas[4]); // {nombre: "Ray"} (objeto)
console.log(cosas[5]); // [1, 2, 3] (otro array)
```

### Switch
```bash
let color = "rojo";
switch (color) {
  case "rojo":
    console.log("El color es rojo");
    break;
  case "azul":
    console.log("El color es azul");
    break;
  default:
    console.log("Color no reconocido");
}
```
