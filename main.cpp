#include <iostream>
#include <string>
#include <list>
#include <algorithm>
#include <vector>

using namespace std;


template<typename T>
class Prenda{
public:

    T nombre;
    T estacion;
    T tipo;
    T color;
    T talla;
    T caracteristica;

    T obtenerNombre() const {
    return nombre;
}
    T obtenerCaracteristica() const {
    return caracteristica;
    }

     Prenda(T nombre, T estacion, T tipo, T color, T talla, T caracteristica)
        : nombre(nombre), estacion(estacion), tipo(tipo), color(color), talla(talla), caracteristica(caracteristica){}
};

template<typename T>
class Estacion{
public:
    T nombre;
    std::vector<Prenda<T>> prendas;

    Estacion(T nombre) : nombre(nombre){}
};
template<typename T>
class TipoPrenda{
public:
    T nombre;
    std::vector<Prenda<T>> prendas;

    TipoPrenda(T nombre) : nombre(nombre){}
};
template<typename T>
class Nodo{
public:
    T valor;
    Nodo<T>* next;
    Nodo<T>* anterior;

    Nodo(const T& v) : valor(v), next(nullptr), anterior(nullptr){}
};

template<typename T>
class ListaEnlazadaDoble{
private:
    Nodo<T>* head;
    Nodo<T>* tail;

public:
    Nodo<T>* buscarPorCaracteristica(const std::string& caracteristica) const {
        Nodo<T>* actualNode = head;

        while (actualNode != nullptr) {
            if (actualNode->valor.caracteristica == caracteristica) {
                return actualNode;
            }
            actualNode = actualNode->next;
        }

        return nullptr;
    }


    ListaEnlazadaDoble() : head(nullptr), tail(nullptr){}

    void push_back(const T& valor){
        Nodo<T>* nuevoNodo = new Nodo<T>(valor);

        if (head == nullptr){
            head = nuevoNodo;
            tail = nuevoNodo;
        } else {
            nuevoNodo->anterior = tail;
            tail->next = nuevoNodo;
            tail = nuevoNodo;
        }
    }

    void erase(Nodo<T>* nodo) {
        if (nodo == nullptr)
            return;

        if (nodo == head && nodo == tail){
            head = nullptr;
            tail = nullptr;
        } else if (nodo == head){
            head = head->next;
            head->anterior = nullptr;
        } else if (nodo == tail) {
            tail = tail->anterior;
            tail->next = nullptr;
        } else {
            nodo->anterior->next = nodo->next;
            nodo->next->anterior = nodo->anterior;
        }

        delete nodo;
    }
        void limpiar(){
        while (head != nullptr){
            Nodo<T>* nodoBorrar = head;
            head = head->next;
            delete nodoBorrar;
        }
        tail = nullptr;
    }

    Nodo<T>* begin() const{
        return head;
    }

    Nodo<T>* end() const{
        return nullptr;
    }
    Nodo<T>* obtenerhead() const{
        return head;
    }
};

template<typename T>
void intercambiar(Nodo<Prenda<T>>* nodo1, Nodo<Prenda<T>>* nodo2) {
    Prenda<T> temp = nodo1->valor;
    nodo1->valor = nodo2->valor;
    nodo2->valor = temp;
}

template<typename T>
Nodo<Prenda<T>>* particionar(Nodo<Prenda<T>>* head, Nodo<Prenda<T>>* tail) {
    Prenda<T> pivote = tail->valor;
    Nodo<Prenda<T>>* i = head->anterior;

    for (Nodo<Prenda<T>>* j = head; j != tail; j = j->next) {
        if (j->valor.obtenerNombre() <= pivote.obtenerNombre()) {
            i = (i == nullptr) ? head : i->next;
            intercambiar(i, j);
        }
    }

    i = (i == nullptr) ? head : i->next;
    intercambiar(i, tail);

    return i;
}

template<typename T>
void quicksort(Nodo<Prenda<T>>* head, Nodo<Prenda<T>>* tail) {
    if (head != nullptr && tail != nullptr && head != tail && head != tail->next) {
        Nodo<Prenda<T>>* pivote = particionar(head, tail);

        quicksort(head, pivote->anterior);
        quicksort(pivote->next, tail);
    }
}

template<typename T>
class Guardarropa{
public:
    ListaEnlazadaDoble<Prenda<T>> prendas;
    std::vector<Estacion<T>> estaciones;
    std::vector<TipoPrenda<T>> tiposPrenda;
    void agregarPrenda(const Prenda<T>& prenda){
        prendas.push_back(prenda);
        for (Estacion<T>& estacion : estaciones){
            if (estacion.nombre == prenda.estacion){
                estacion.prendas.push_back(prenda);
                break;
            }
        }
        for (TipoPrenda<T>& tipo : tiposPrenda){
            if (tipo.nombre == prenda.tipo){
                tipo.prendas.push_back(prenda);
                break;
            }
        }
    }

    void eliminarPrenda(const T& nombre){
        for (auto it = prendas.begin(); it != prendas.end(); ++it) {
            if (it->nombre == nombre){
                prendas.erase(it);
                break;
            }
        }
        for (Estacion<T>& estacion : estaciones){
            for (auto it = estacion.prendas.begin(); it != estacion.prendas.end(); ++it){
                if (it->nombre == nombre){
                    estacion.prendas.erase(it);
                    break;
                }
            }
        }
        for (TipoPrenda<T>& tipo : tiposPrenda){
            for (auto it = tipo.prendas.begin(); it != tipo.prendas.end(); ++it){
                if (it->nombre == nombre){
                    tipo.prendas.erase(it);
                    break;
                }
            }
        }

    }

void ordenar(){
    std::vector<Prenda<T>> prendasVector;
    Nodo<Prenda<T>>* actualNode = prendas.obtenerhead();
    while (actualNode != nullptr){
        prendasVector.push_back(actualNode->valor);
        actualNode = actualNode->next;
    }

    std::sort(prendasVector.begin(), prendasVector.end(), [](const Prenda<T>& a, const Prenda<T>& b){
        return a.talla < b.talla;
    });

    prendas.limpiar();

    for (const Prenda<T>& prenda : prendasVector){
        prendas.push_back(prenda);
    }
}

};

template<typename T>
int busquedaBinariaRecursiva(const ListaEnlazadaDoble<Prenda<T>>& prendas, const std::string& caracteristica, int inicio, int fin) {
    if (inicio > fin) {
        return -1;
    }
    int medio = inicio + (fin - inicio) / 2;
    const Prenda<T>& prenda = prendas.obtener(medio).valor;
    if (prenda.caracteristica == caracteristica) {
        return medio;
    }
    else if (prenda.caracteristica < caracteristica) {
        return busquedaBinariaRecursiva(prendas, caracteristica, medio + 1, fin);
    }
    else {
        return busquedaBinariaRecursiva(prendas, caracteristica, inicio, medio - 1);
    }
}

template<typename T>
void agregarPrenda(ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::cout << "----- AGREGAR PRENDA -----" << std::endl;
    std::cout << "Ingrese el nombre de la prenda: ";
    std::string nombre;
    std::getline(std::cin, nombre);

    std::cout << "Ingrese la estacion de la prenda: ";
    std::string estacion;
    std::getline(std::cin, estacion);

    std::cout << "Ingrese el tipo de la prenda: ";
    std::string tipo;
    std::getline(std::cin, tipo);

    std::cout << "Ingrese el color de la prenda: ";
    std::string color;
    std::getline(std::cin, color);

    std::cout << "Ingrese la talla de la prenda: ";
    std::string talla;
    std::getline(std::cin, talla);

    std::cout << "Ingrese la caracteristica de la prenda: ";
    std::string caracteristica;
    std::getline(std::cin, caracteristica);

    Prenda<T> nuevaPrenda(nombre, estacion, tipo, color, talla, caracteristica);
    prendas.push_back(nuevaPrenda);

    std::cout << "Prenda agregada correctamente." << std::endl;
}

template<typename T>
void buscarPrendaPorCaracteristica(const ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::cout << "----- BUSCAR PRENDA POR CARACTERISTICA -----" << std::endl;
    std::cout << "Ingrese la caracteristica para buscar la prenda: ";
    std::string caracteristica;
    std::getline(std::cin >> std::ws, caracteristica);

    Nodo<Prenda<T>>* nodoEncontrado = prendas.buscarPorCaracteristica(caracteristica);

    if (nodoEncontrado != nullptr) {
        Prenda<T>& prenda = nodoEncontrado->valor;
        std::cout << "Prenda encontrada:" << std::endl;
        std::cout << "Nombre: " << prenda.obtenerNombre() << std::endl;
        std::cout << "Estacion: " << prenda.estacion << std::endl;
        std::cout << "Tipo: " << prenda.tipo << std::endl;
        std::cout << "Color: " << prenda.color << std::endl;
        std::cout << "Talla: " << prenda.talla << std::endl;
    } else {
        std::cout << "No se encontro ninguna prenda con la caracteristica especificada." << std::endl;
    }
}

template<typename T>
void eliminarPrenda(ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::cout << "----- ELIMINAR PRENDA -----" << std::endl;
    std::cout << "Ingrese la posicion de la prenda a eliminar: ";
    int posicion;
    std::cin >> posicion;
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

    Nodo<Prenda<T>>* ridNode = prendas.obtenerhead();
    int contador = 0;
    while (ridNode != nullptr && contador < posicion) {
        ridNode = ridNode->next;
        contador++;
    }

    if (ridNode != nullptr) {
        Prenda<T>& prendaEliminada = ridNode->valor;
        std::cout << "Prenda eliminada:" << std::endl;
        std::cout << "Nombre: " << prendaEliminada.obtenerNombre() << std::endl;
        std::cout << "Estacion: " << prendaEliminada.estacion << std::endl;
        std::cout << "Tipo: " << prendaEliminada.tipo << std::endl;
        std::cout << "Color: " << prendaEliminada.color << std::endl;
        std::cout << "Talla: " << prendaEliminada.talla << std::endl;
        std::cout << "Caracteristica: " << prendaEliminada.caracteristica << std::endl;

        prendas.erase(ridNode);

        std::cout << "Prenda eliminada correctamente." << std::endl;
    } else {
        std::cout << "No se encontro ninguna prenda en la posicion especificada." << std::endl;
    }
}

template<typename T>
void editarPrenda(ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::string caracteristica;
    std::cout << "Ingrese la caracteristica para buscar la prenda a editar: ";
    std::getline(std::cin >> std::ws, caracteristica);

    Nodo<Prenda<T>>* nodoEncontrado = prendas.buscarPorCaracteristica(caracteristica);

    if (nodoEncontrado != nullptr) {
        Prenda<T>& prenda = nodoEncontrado->valor;
        std::cout << "Prenda encontrada:" << std::endl;
        std::cout << "Nombre: " << prenda.obtenerNombre() << std::endl;
        std::cout << "Estacion: " << prenda.estacion << std::endl;
        std::cout << "Tipo: " << prenda.tipo << std::endl;
        std::cout << "Color: " << prenda.color << std::endl;
        std::cout << "Talla: " << prenda.talla << std::endl;
        std::cout << "Caracteristica: " << prenda.caracteristica << std::endl;

        std::cout << "Ingrese el nuevo nombre de la prenda: ";
        std::getline(std::cin, prenda.nombre);

        std::cout << "Ingrese la nueva estacion de la prenda: ";
        std::getline(std::cin, prenda.estacion);

        std::cout << "Ingrese el nuevo tipo de la prenda: ";
        std::getline(std::cin, prenda.tipo);

        std::cout << "Ingrese el nuevo color de la prenda: ";
        std::getline(std::cin, prenda.color);

        std::cout << "Ingrese la nueva talla de la prenda: ";
        std::getline(std::cin, prenda.talla);

        std::cout << "Ingrese la nueva caracteristica de la prenda: ";
        std::getline(std::cin, prenda.caracteristica);

        std::cout << "Prenda editada correctamente." << std::endl;
    } else {
        std::cout << "No se encontro ninguna prenda con la caracteristica especificada." << std::endl;
    }
}


template<typename T>
void ordenarPrendas(ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::cout << "Ordenando prendas..." << std::endl;

    Nodo<Prenda<T>>* head = prendas.obtenerhead();
    Nodo<Prenda<T>>* tail = nullptr;

    while (head != nullptr && head->next != nullptr) {
        head = head->next;
    }

    tail = head;

    quicksort(prendas.obtenerhead(), tail);

    std::cout << "Las prendas han sido ordenadas correctamente." << std::endl;
}

template<typename T>
void mostrarPrendas(const ListaEnlazadaDoble<Prenda<T>>& prendas) {
    std::cout << "Mostrando todas las prendas:" << std::endl;

    Nodo<Prenda<T>>* actualNode = prendas.obtenerhead();

    while (actualNode != nullptr) {
        const Prenda<T>& prenda = actualNode->valor;
        std::cout << "Nombre: " << prenda.obtenerNombre() << std::endl;
        std::cout << "Estacion: " << prenda.estacion << std::endl;
        std::cout << "Tipo: " << prenda.tipo << std::endl;
        std::cout << "Color: " << prenda.color << std::endl;
        std::cout << "Talla: " << prenda.talla << std::endl;
        std::cout << "Caracteristica: " << prenda.caracteristica << std::endl;
        std::cout << "-------------------------" << std::endl;
        actualNode = actualNode->next;
    }
}

template<typename T>
void menu(ListaEnlazadaDoble<Prenda<T>>& prendas, ListaEnlazadaDoble<Estacion<T>>& estaciones, ListaEnlazadaDoble<TipoPrenda<T>>& tiposPrenda) {
    int opcion;
    do {
        std::cout << "----- MENU -----" << std::endl;
        std::cout << "1. Agregar prenda" << std::endl;
        std::cout << "2. Buscar prenda por caracteristica" << std::endl;
        std::cout << "3. Eliminar prenda" << std::endl;
        std::cout << "4. Editar prenda" << std::endl;
        std::cout << "5. Ordenar prendas (Quicksort)" << std::endl;
        std::cout << "6. Mostrar todas las prendas" << std::endl;
        std::cout << "7. Salir" << std::endl;
        std::cout << "Ingrese una opcion: ";
        std::cin >> opcion;
        std::cin.clear();
        std::cin.ignore(100, '\n');

        switch (opcion) {
            case 1: {
                agregarPrenda(prendas);
                break;
            }

            case 2: {
                buscarPrendaPorCaracteristica(prendas);
                break;
            }
            case 3: {
                eliminarPrenda(prendas);
                break;
            }
           case 4: {
                editarPrenda(prendas);
                break;
            }

            case 5: {
                ordenarPrendas(prendas);
                break;
            }

            case 6: {
                mostrarPrendas(prendas);
                break;
            }
            case 7: {
                std::cout << "Saliendo del programa..." << std::endl;
                break;
            }
            default: {
                std::cout << "Opcion invalida. Por favor, seleccione una opcion valida." << std::endl;

            }
        }
    } while (opcion != 7);
}


int main() {
    ListaEnlazadaDoble<Prenda<std::string>> prendas;
    ListaEnlazadaDoble<Estacion<std::string>> estaciones;
    ListaEnlazadaDoble<TipoPrenda<std::string>> tiposPrenda;
    menu(prendas, estaciones, tiposPrenda);
    return 0;
}
