###### Uzupełnij tę sakcje ######
# Zmien ten klucz tak aby zawierał 16 znaków (tak dokładnie 16 znaków)
# klucz musi byc taki sam dla obu urzadzen
klucz = b"rakieta123456789"

# Adresy powinny byc takie same na obu urzadzeniach
# Jesli nie plnujesz brac udzialu w zlach "rakieciarzy" to zmien tylko jeden bajt czyli:
# Zmien "\xaa" na "\x67" w obu adresach ("\x" to jest staly element tego adresu nie mozesz zmieniać)
adresy = (b"\x55\xf0\xf0\xf0\xaa", b"\x44\xf0\xf0\xf0\xaa")

# Podaj ile ma czasu (sekundy) zostać podane napięcie na zapalnik!
czas_nagrzewania: float = 3
#################################



import utime
from machine import Pin, SPI
from nrf24l01 import NRF24L01
import ucryptolib


_RX_POLL_DELAY = 15

power_led = Pin(15, Pin.OUT)
ign_led = Pin(17, Pin.OUT)
power_led.high()
ign_led.low()
ignition_pin = Pin(16, Pin.OUT)
ignition_pin.low()

cipher = ucryptolib.aes(klucz, 1)

CMD_RDY = cipher.encrypt(b"RDY-COMMAND-HASH")
CMD_IGN = cipher.encrypt(b"IGN-COMMAND-HASH")
CMD_DONE = cipher.encrypt(b"DON-COMMAND-HASH")

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
csn = Pin(5, Pin.OUT, value=1)
ce  = Pin(6, Pin.OUT, value=0)


nrf = NRF24L01(spi, csn, ce, payload_size=16)
nrf.open_tx_pipe(adresy[1])
nrf.open_rx_pipe(1, adresy[0])
nrf.start_listening()



print("Responder: listening...")

while True:
    if nrf.any():
        msg = nrf.recv()
        if msg == CMD_RDY:
            print("Remote controller status: Ready Connected")

        nrf.stop_listening()
        utime.sleep_ms(2)

        if msg == CMD_IGN:
            try:
                print("Remote Controller: IGNITE Signal")
                nrf.send(CMD_DONE)
                ignition_pin.high()
                ign_led.high()
                utime.sleep(czas_nagrzewania)
                ignition_pin.low()
                ign_led.low()
            except OSError:
                pass
        else:
            try:
                nrf.send(CMD_RDY)
            except OSError:
                print("Sending RDY issue")
                nrf.flush_tx()
                pass

        nrf.start_listening()

    utime.sleep_ms(_RX_POLL_DELAY)