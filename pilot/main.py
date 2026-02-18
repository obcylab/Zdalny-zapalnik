###### Uzupełnij tę sakcje ######
# Zmien ten klucz tak aby zawierał 16 znaków (tak dokładnie 16 znaków)
# klucz musi byc taki sam dla obu urzadzen
klucz = b"rakieta123456789"
# Adresy powinny byc takie same na obu urzadzeniach
# Jesli nie plnujesz brac udzialu w zlach "rakieciarzy" to zmien tylko jeden bajt czyli:
# masz "\xaa" zamien na "\x67" w obu adresach ("\x" to jest staly element tego nie mozesz ruszac
adresy = (b"\x55\xf0\xf0\xf0\xaa", b"\x44\xf0\xf0\xf0\xaa")
#################################


import utime
from machine import Pin, SPI
from nrf24l01 import NRF24L01
from micropython import const
import ucryptolib

_RX_POLL_DELAY = const(15)
_RESPONDER_SEND_DELAY = const(10)

power_led = Pin(15, Pin.OUT).high()
paired_led = Pin(16, Pin.OUT)
paired_led.low()
ignition_button = Pin(18, Pin.IN, Pin.PULL_UP)

cipher = ucryptolib.aes(klucz, 1)

CMD_RDY = cipher.encrypt(b"RDY-COMMAND-HASH")
CMD_IGN = cipher.encrypt(b"IGN-COMMAND-HASH")
CMD_DONE = cipher.encrypt(b"DON-COMMAND-HASH")

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
csn = Pin(5, Pin.OUT, value=1)
ce  = Pin(6, Pin.OUT, value=0)
nrf = NRF24L01(spi, csn, ce, payload_size=16)

nrf.open_tx_pipe(adresy[0])
nrf.open_rx_pipe(1, adresy[1])
nrf.start_listening()

num_failures = 0
rdy = False
msg = 0

while True:
    nrf.stop_listening()
    if rdy and ignition_button.value() == 0:
        payload = CMD_IGN
    else:
        payload = CMD_RDY

    try:
        nrf.send(payload)
    except OSError:
        print("Cant send (no ACK)")
        nrf.flush_tx()

    nrf.start_listening()
    utime.sleep_ms(5)
    start_time = utime.ticks_ms()
    timeout = False
    while not nrf.any() and not timeout:
        if utime.ticks_diff(utime.ticks_ms(), start_time) > 100:
            timeout = True

    if timeout:
        print("failed, response timed out")
        msg = 0
        paired_led.low()
        num_failures += 1
    else:
        msg = bytes(nrf.recv())
        cipher = ucryptolib.aes(klucz, 1)
        print("Recieved: ", cipher.decrypt(msg))
        if msg == CMD_RDY:
            rdy = True

            msg = 0
            paired_led.high()

    utime.sleep_ms(15)
