#laboratorio No3
import re


# ============================================================
# ANALIZADOR 
# ============================================================

PATRONES = [
    ("ESPACIO", r"\s+"),
    ("NUMERO", r"\d+(?:\.\d+)?"),
    ("CADENA", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
    ("IDENTIFICADOR", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OPERADOR", r"==|!=|<=|>=|&&|\|\||\+\+|--|[+\-*/%<>=!]"),
    ("SIMBOLO", r"[(){};,]"),
]

PATRON_GENERAL = re.compile(
    "|".join(f"(?P<{nombre}>{patron})" for nombre, patron in PATRONES)
)


class ErrorSintactico(Exception):
    """Error producido cuando la entrada no cumple la gramÃ¡tica."""


def analizar_lexico(codigo):
    tokens = []
    posicion = 0

    while posicion < len(codigo):
        coincidencia = PATRON_GENERAL.match(codigo, posicion)

        if not coincidencia:
            raise ErrorSintactico(
                f"CarÃ¡cter no reconocido: {codigo[posicion]!r}"
            )

        tipo = coincidencia.lastgroup
        valor = coincidencia.group()

        if tipo != "ESPACIO":
            tokens.append((tipo, valor))

        posicion = coincidencia.end()

    tokens.append(("EOF", "EOF"))
    return tokens


# ============================================================
# ANALIZADOR SINTACTICO
# ============================================================

class AnalizadorSintactico:
    def __init__(self, codigo):
        self.tokens = analizar_lexico(codigo)
        self.posicion = 0

    def actual(self):
        return self.tokens[self.posicion]

    def valor_actual(self):
        return self.actual()[1]

    def tipo_actual(self):
        return self.actual()[0]

    def avanzar(self):
        token = self.actual()
        if self.tipo_actual() != "EOF":
            self.posicion += 1
        return token

    def aceptar(self, valor):
        if self.valor_actual() == valor:
            self.avanzar()
            return True
        return False

    def esperar(self, valor):
        if not self.aceptar(valor):
            raise ErrorSintactico(
                f"Se esperaba {valor!r}, pero se encontrÃ³ {self.valor_actual()!r}"
            )

    def esperar_identificador(self):
        if self.tipo_actual() != "IDENTIFICADOR":
            raise ErrorSintactico(
                f"Se esperaba un identificador, pero se encontrÃ³ {self.valor_actual()!r}"
            )
        return self.avanzar()[1]

    def esperar_fin(self):
        if self.tipo_actual() != "EOF":
            raise ErrorSintactico(
                f"Texto inesperado al final: {self.valor_actual()!r}"
            )

    # --------------------------------------------------------
    # Expresiones
    # --------------------------------------------------------

    def expresion_primaria(self):
        if self.aceptar("("):
            self.expresion_logica()
            self.esperar(")")
            return

        if self.tipo_actual() in ("IDENTIFICADOR", "NUMERO", "CADENA"):
            self.avanzar()
            return

        if self.valor_actual() in ("true", "false"):
            self.avanzar()
            return

        raise ErrorSintactico(
            f"Se esperaba un operando, pero se encontrÃ³ {self.valor_actual()!r}"
        )

    def expresion_unaria(self):
        if self.valor_actual() in ("!", "+", "-"):
            self.avanzar()
            self.expresion_unaria()
        else:
            self.expresion_primaria()

    def expresion_multiplicativa(self):
        self.expresion_unaria()
        while self.valor_actual() in ("*", "/", "%"):
            self.avanzar()
            self.expresion_unaria()

    def expresion_aditiva(self):
        self.expresion_multiplicativa()
        while self.valor_actual() in ("+", "-"):
            self.avanzar()
            self.expresion_multiplicativa()

    def expresion_relacional(self):
        self.expresion_aditiva()
        if self.valor_actual() in ("<", ">", "<=", ">="):
            self.avanzar()
            self.expresion_aditiva()

    def expresion_igualdad(self):
        self.expresion_relacional()
        while self.valor_actual() in ("==", "!="):
            self.avanzar()
            self.expresion_relacional()

    def expresion_and(self):
        self.expresion_igualdad()
        while self.valor_actual() == "&&":
            self.avanzar()
            self.expresion_igualdad()

    def expresion_logica(self):
        self.expresion_and()
        while self.valor_actual() == "||":
            self.avanzar()
            self.expresion_and()

    # --------------------------------------------------------
    # 1. EXPRESIONES LÃ“GICAS
    # --------------------------------------------------------

    def analizar_expresion_logica(self):
        self.expresion_logica()
        self.esperar_fin()
        return True

    # --------------------------------------------------------
    # Instrucciones auxiliares para for y funciones
    # --------------------------------------------------------

    def expresion_asignacion(self):
        self.esperar_identificador()

        if self.valor_actual() in ("=", "+=", "-=", "*=", "/="):
            self.avanzar()
            self.expresion_logica()
        elif self.valor_actual() in ("++", "--"):
            self.avanzar()
        else:
            raise ErrorSintactico(
                "Se esperaba un operador de asignaciÃ³n o incremento"
            )

    def instruccion_simple(self):
        if self.valor_actual() == ";":
            self.avanzar()
            return

        self.expresion_asignacion()
        self.esperar(";")

    def bloque(self):
        self.esperar("{")

        while self.valor_actual() != "}":
            if self.tipo_actual() == "EOF":
                raise ErrorSintactico("Falta cerrar el bloque con '}'")

            if self.valor_actual() == "for":
                self.sentencia_for()
            elif self.valor_actual() == "return":
                self.avanzar()
                if self.valor_actual() != ";":
                    self.expresion_logica()
                self.esperar(";")
            elif self.valor_actual() == "{":
                self.bloque()
            else:
                self.instruccion_simple()

        self.esperar("}")

    # --------------------------------------------------------
    # 2. SENTENCIA FOR
    # --------------------------------------------------------

    def sentencia_for(self):
        self.esperar("for")
        self.esperar("(")

        # InicializaciÃ³n: puede estar vacÃ­a.
        if self.valor_actual() != ";":
            self.expresion_asignacion()
        self.esperar(";")

        # CondiciÃ³n: puede estar vacÃ­a.
        if self.valor_actual() != ";":
            self.expresion_logica()
        self.esperar(";")

        # ActualizaciÃ³n: puede estar vacÃ­a.
        if self.valor_actual() != ")":
            self.expresion_asignacion()
        self.esperar(")")

        # Cuerpo del for.
        if self.valor_actual() == "{":
            self.bloque()
        else:
            self.instruccion_simple()

    def analizar_for(self):
        self.sentencia_for()
        self.esperar_fin()
        return True

    # --------------------------------------------------------
    # 3. DEFINICIÃ“N DE FUNCIONES
    # --------------------------------------------------------

    def definicion_funcion(self):
        # Tipo de retorno.
        if self.valor_actual() not in (
            "int", "float", "double", "char", "void", "bool", "string"
        ):
            raise ErrorSintactico("Se esperaba el tipo de retorno de la funciÃ³n")

        tipo_retorno = self.avanzar()[1]

        # Nombre de la funciÃ³n.
        nombre = self.esperar_identificador()

        self.esperar("(")

        # Lista de parÃ¡metros: tipo nombre, separados por comas.
        if self.valor_actual() != ")":
            self.parametro()

            while self.aceptar(","):
                self.parametro()

        self.esperar(")")

        # Cuerpo de la funciÃ³n.
        self.bloque()

        return tipo_retorno, nombre

    def parametro(self):
        tipos = ("int", "float", "double", "char", "bool", "string")

        if self.valor_actual() not in tipos:
            raise ErrorSintactico("Se esperaba el tipo del parÃ¡metro")

        self.avanzar()
        self.esperar_identificador()

    def analizar_funcion(self):
        self.definicion_funcion()
        self.esperar_fin()
        return True


# ============================================================
# FUNCIONES DE PRUEBA
# ============================================================

def ejecutar_analisis(titulo, codigo, metodo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)
    print("Entrada:", codigo)

    try:
        analizador = AnalizadorSintactico(codigo)
        metodo(analizador)
        print("RESULTADO: Sintaxis correcta.")
    except ErrorSintactico as error:
        print("RESULTADO: Error sintÃ¡ctico.")
        print("Detalle:", error)


def menu():
    while True:
        print("\n========== LABORATORIO N.Âº 3 ==========")
        print("1. Analizar expresiÃ³n lÃ³gica")
        print("2. Analizar sentencia for")
        print("3. Analizar definiciÃ³n de funciÃ³n")
        print("4. Ejecutar ejemplos")
        print("0. Salir")

        opcion = input("\nSeleccione una opciÃ³n: ").strip()

        if opcion == "1":
            codigo = input("\nIngrese una expresiÃ³n lÃ³gica: ")
            ejecutar_analisis(
                "ANÃLISIS DE EXPRESIÃ“N LÃ“GICA",
                codigo,
                AnalizadorSintactico.analizar_expresion_logica
            )

        elif opcion == "2":
            print("\nEjemplo: for (i = 0; i < 10; i++) { x = x + 1; }")
            codigo = input("Ingrese una sentencia for: ")
            ejecutar_analisis(
                "ANÃLISIS DE SENTENCIA FOR",
                codigo,
                AnalizadorSintactico.analizar_for
            )

        elif opcion == "3":
            print("\nEjemplo: int sumar(int a, int b) { return a + b; }")
            codigo = input("Ingrese una definiciÃ³n de funciÃ³n: ")
            ejecutar_analisis(
                "ANÃLISIS DE DEFINICIÃ“N DE FUNCIÃ“N",
                codigo,
                AnalizadorSintactico.analizar_funcion
            )

        elif opcion == "4":
            ejecutar_analisis(
                "EXPRESIÃ“N LÃ“GICA",
                "(a > 5 && b <= 10) || c == 0",
                AnalizadorSintactico.analizar_expresion_logica
            )
            ejecutar_analisis(
                "SENTENCIA FOR",
                "for (i = 0; i < 10; i++) { x = x + 1; }",
                AnalizadorSintactico.analizar_for
            )
            ejecutar_analisis(
                "DEFINICIÃ“N DE FUNCIÃ“N",
                "int sumar(int a, int b) { return a + b; }",
                AnalizadorSintactico.analizar_funcion
            )

        elif opcion == "0":
            print("\nPrograma finalizado.")
            break

        else:
            print("\nOpciÃ³n no vÃ¡lida. Intente nuevamente.")


if __name__ == "__main__":
    menu()
