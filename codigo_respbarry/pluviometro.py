import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime

# CONFIGURAÇÕES
GPIO_PIN = 17
MM_POR_PULSO = 0.25
INTERVALO_LOG = 60  # segundos

# VARIÁVEIS
contador_pulsos = 0
chuva_acumulada = 0

# CONFIGURA GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def contar_pulso(channel):
    global contador_pulsos
    contador_pulsos += 1

# DETECTAR PULSOS
GPIO.add_event_detect(GPIO_PIN, GPIO.FALLING, callback=contar_pulso, bouncetime=300)

# CRIAR ARQUIVO CSV
arquivo_csv = "/home/enzo/Desktop/dados_pluviometro.csv"

with open(arquivo_csv, mode="a", newline="") as arquivo:
    writer = csv.writer(arquivo)

    print("Pluviômetro iniciado...")

    try:
        while True:
            time.sleep(INTERVALO_LOG)

            pulsos = contador_pulsos
            contador_pulsos = 0

            chuva_intervalo = pulsos * MM_POR_PULSO

            # global chuva_acumulada
            chuva_acumulada += chuva_intervalo

            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            writer.writerow([
                data_hora,
                pulsos,
                f"{chuva_intervalo:.2f}",
                f"{chuva_acumulada:.2f}"
            ])

            arquivo.flush()

            print(
                f"{data_hora} | Pulsos: {pulsos} | "
                f"Intervalo: {chuva_intervalo:.2f} mm | "
                f"Acumulado: {chuva_acumulada:.2f} mm"
            )

    except KeyboardInterrupt:
        print("Encerrando...")

    finally:
        GPIO.cleanup()