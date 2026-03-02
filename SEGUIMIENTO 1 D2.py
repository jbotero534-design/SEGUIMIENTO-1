from machine import mem32, Pin
import time, urandom
from micropython import const

# REGISTROS ESP32

GPIO_ENABLE_REG   = const(0x3FF44020)
GPIO_OUT_W1TS_REG = const(0x3FF44008)
GPIO_OUT_W1TC_REG = const(0x3FF4400C)

# PINES

LED1   = 2
LED2   = 4
LED3   = 5
BUZZER = 18

J1 = [16, 17, 21, 22]
J2 = [23, 25, 26, 27]

BTN_MENU  = 13
BTN_RESET = 33
BTN_SIMON = 14

# CONFIGURAR SALIDAS

for pin in [LED1, LED2, LED3, BUZZER]:
    mem32[GPIO_ENABLE_REG] |= (1 << pin)

def on(pin):
    mem32[GPIO_OUT_W1TS_REG] = (1 << pin)

def off(pin):
    mem32[GPIO_OUT_W1TC_REG] = (1 << pin)

def apagar_todo():
    off(LED1)
    off(LED2)
    off(LED3)
    off(BUZZER)

# BOTONES

botones = {}
for pin in J1 + J2 + [BTN_MENU, BTN_RESET, BTN_SIMON]:
    botones[pin] = Pin(pin, Pin.IN, Pin.PULL_UP)

def leer(pin):
    return botones[pin].value() == 0

# SIMON DICE

def simon_dice():
    print("\n=== SIMON DICE ===")
    print("Jugador 2")

    apagar_todo()
    time.sleep(1.5)  

    secuencia = []
    nivel = 1

    while True:

        secuencia.append(urandom.randint(0,3))
        print("Nivel", nivel)

        for est in secuencia:
            activar_estimulo(est)
            time.sleep(0.6)
            apagar_todo()
            time.sleep(0.3)

        for esperado in secuencia:
            while True:

                if leer(BTN_RESET):
                    apagar_todo()
                    return

                for i in range(4):
                    if leer(J2[i]):
                        time.sleep_ms(200)

                        if i != esperado:
                            print("Perdiste")
                            apagar_todo()
                            time.sleep(1)
                            while any(leer(pin) for pin in J2 + [BTN_SIMON]):
                                time.sleep_ms(10)
                            return
                        break
                else:
                    continue
                break

        nivel += 1
        time.sleep(0.5)

# MENÚ

def seleccionar_valor(texto, minimo, maximo):
    valor = minimo
    print("\n" + texto)
    print("Valor actual:", valor)
    print("Pulsa para cambiar | Mantén 1.5s para confirmar")

    while True:
        if leer(BTN_MENU):
            inicio = time.ticks_ms()

            while leer(BTN_MENU):
                if time.ticks_diff(time.ticks_ms(), inicio) > 1500:
                    print("Confirmado:", valor)
                    time.sleep_ms(400)
                    return valor

            valor += 1
            if valor > maximo:
                valor = minimo

            print("Valor actual:", valor)
            time.sleep_ms(300)

# ACTIVAR ESTIMULO

def activar_estimulo(est):
    apagar_todo()
    if est == 0:
        on(LED1)
    elif est == 1:
        on(LED2)
    elif est == 2:
        on(LED3)
    elif est == 3:
        on(BUZZER)

# MEDIR REACCION

def medir(est, jugadores):
    inicio = time.ticks_ms()

    while True:

        if leer(BTN_SIMON):
            while leer(BTN_SIMON):
                time.sleep_ms(10)

            apagar_todo()
            time.sleep(0.5)  
            simon_dice()

            apagar_todo()
            time.sleep(0.3)
            activar_estimulo(est)
            inicio = time.ticks_ms()

        if leer(BTN_RESET):
            return "RESET", 0

        for i in range(4):
            if leer(J1[i]):
                tiempo = time.ticks_diff(time.ticks_ms(), inicio)
                time.sleep_ms(200)
                if i == est:
                    return "J1_OK", tiempo
                else:
                    return "J1_FAIL", tiempo

        if jugadores == 2:
            for i in range(4):
                if leer(J2[i]):
                    tiempo = time.ticks_diff(time.ticks_ms(), inicio)
                    time.sleep_ms(200)
                    if i == est:
                        return "J2_OK", tiempo
                    else:
                        return "J2_FAIL", tiempo

        time.sleep_ms(5)


# JUEGO PRINCIPAL

def juego():
    while True:
        print("\n===== SISTEMA DE REFLEJOS =====")

        jugadores = seleccionar_valor("Numero de jugadores (1-2)",1,2)
        rondas = seleccionar_valor("Numero de rondas (1-9)",1,9)

        score1 = 0
        score2 = 0

        for r in range(rondas):
            print("\n--- RONDA", r+1, "---")
            apagar_todo()

            time.sleep_ms(urandom.randint(400, 900))  

            est = urandom.randint(0, 3)
            activar_estimulo(est)

            resultado, tiempo = medir(est, jugadores)
            apagar_todo()

            if resultado == "RESET":
                print("Sistema reiniciado")
                break

            if resultado == "J1_OK":
                print("Jugador 1 reacciono en", tiempo, "ms")
                score1 += 1
            elif resultado == "J1_FAIL":
                print("Jugador 1 presiono boton incorrecto")
                score1 -= 1
            elif resultado == "J2_OK":
                print("Jugador 2 reacciono en", tiempo, "ms")
                score2 += 1
            elif resultado == "J2_FAIL":
                print("Jugador 2 presiono boton incorrecto")
                score2 -= 1

            print("P1:", score1, "P2:", score2)
            time.sleep(1)

        print("\n===== RESULTADOS =====")
        print("Jugador 1:", score1)

        if jugadores == 2:
            print("Jugador 2:", score2)
            if score1 > score2:
                print("GANADOR: JUGADOR 1")
            elif score2 > score1:
                print("GANADOR: JUGADOR 2")
            else:
                print("EMPATE")

        print("\nPresiona RESET para nuevo juego")
        while not leer(BTN_RESET):
            time.sleep_ms(10)

        print("Reiniciando...\n")
        time.sleep(1)

juego()